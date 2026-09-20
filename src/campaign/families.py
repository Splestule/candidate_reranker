"""One adapter per model family, all with the same two calls.

    enc = fam.encode(audio, lang)            # once per utterance
    cands, extra = fam.decode(enc, arm, seed, lang)

Candidates are dicts in the dump_candidates.py schema (text, avg_conf, min_conf, median_conf,
mean_logprob, mean_entropy, n_tokens, optional word_conf), so scorers.py and compose.py work on
every family unchanged. `extra` is per-row metadata such as identical_after_step1.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import torch

from campaign.tokwords import token_stats, word_conf_from_ids


def _from_pretrained(cls, name, dtype, **kw):
    try:
        return cls.from_pretrained(name, dtype=dtype, **kw)
    except TypeError:
        return cls.from_pretrained(name, torch_dtype=dtype, **kw)


def _device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


# ---------------------------------------------------------------------------------------------

class Whisfusion:
    """Masked diffusion (Whisfusion v1): PDD with K parallel candidates, as decode.py does it."""

    def __init__(self, spec: dict, precision: str | None = None):
        from huggingface_hub import hf_hub_download

        import wf_model

        base = hf_hub_download("nieshen/SMDM", "mdm_safetensors/mdm-170M-100e18-rsl-0.01.safetensors")
        adapter = hf_hub_download("taeyoun811/whisfusion", "whisfusion_stage2_decoder.pt")
        self.wf = wf_model.load(base, adapter, device=_device(), dtype=precision or "auto")

    def encode(self, audio, lang):
        import wf_model
        return wf_model.encode_audio(self.wf, audio)

    def decode(self, enc, arm, seed, lang):
        import decode as dec

        r = dec.pdd_decode(self.wf, enc, n_candidates=arm["K"], n_steps=arm.get("steps", 4),
                           mask_ratio_schedule=arm.get("schedule"), seq_len=arm.get("seq_len", 256),
                           first_step_sampling=arm.get("first_step_sampling", False),
                           temperature=arm.get("temperature", 1.0), seed=seed)
        return ([dec.candidate_to_dict(c) for c in r.candidates],
                {"identical_after_step1": r.identical_after_step1})


# ---------------------------------------------------------------------------------------------

class Drax:
    """Discrete flow matching (Drax-v1) through campaign.drax_fast."""

    def __init__(self, spec: dict, precision: str | None = None):
        from campaign.drax_fast import DraxFast

        root = os.environ.get("DRAX_ROOT", "/kaggle/working/drax_repo")
        self.m = DraxFast(spec["hf"], root, device=_device(), precision=precision or "fp16")

    def encode(self, audio, lang):
        return self.m.encode(audio, lang)

    def decode(self, enc, arm, seed, lang):
        chunk = int(os.environ.get("DRAX_CHUNK", "32"))
        return self.m.sample(enc, lang, K=arm["K"], temperature=arm["T"], steps=arm["steps"],
                             seed=seed, chunk=chunk), {}


# ---------------------------------------------------------------------------------------------

class Whisper:
    """Autoregressive control: greedy, beam n-best, or K temperature samples from one model.

    Calls GenerationMixin.generate directly. Whisper's own generate() turns
    num_return_sequences into repeated inputs, so beam search would return B copies of the best
    beam instead of an n-best list. Token probabilities come from one teacher-forced pass over
    the finished sequences, which works the same for every mode and transformers version.
    """

    def __init__(self, spec: dict, precision: str | None = None):
        import copy

        from transformers import WhisperForConditionalGeneration, WhisperProcessor

        self.dev = _device()
        self.dtype = torch.float16 if self.dev == "cuda" else torch.float32
        self.proc = WhisperProcessor.from_pretrained(spec["hf"])
        self.model = _from_pretrained(WhisperForConditionalGeneration, spec["hf"], self.dtype)
        self.model = self.model.to(self.dev).train(False).requires_grad_(False)
        self.tok = self.proc.tokenizer
        self.eot = self.tok.convert_tokens_to_ids("<|endoftext|>")
        self.gen_cfg = copy.deepcopy(self.model.generation_config)
        for k in ("forced_decoder_ids", "max_length"):
            if hasattr(self.gen_cfg, k):
                setattr(self.gen_cfg, k, None)

    def encode(self, audio, lang):
        f = self.proc.feature_extractor(audio, sampling_rate=16000, return_tensors="pt").input_features
        return f.to(self.dev, dtype=self.dtype)

    def _prompt(self, lang):
        ids = [self.tok.convert_tokens_to_ids(t) for t in
               ("<|startoftranscript|>", f"<|{lang}|>", "<|transcribe|>", "<|notimestamps|>")]
        return torch.tensor([ids], device=self.dev)

    @torch.no_grad()
    def decode(self, enc, arm, seed, lang):
        from transformers.generation.utils import GenerationMixin

        torch.manual_seed(int(seed) & 0x7FFFFFFF)
        prompt = self._prompt(lang)
        P = prompt.shape[1]
        kw = dict(input_features=enc, decoder_input_ids=prompt, generation_config=self.gen_cfg,
                  max_new_tokens=200)
        mode = arm["mode"]
        if mode == "greedy":
            seqs = GenerationMixin.generate(self.model, **kw, do_sample=False, num_beams=1)
        elif mode == "beam":
            B = arm["beams"]
            seqs = GenerationMixin.generate(self.model, **kw, do_sample=False, num_beams=B,
                                            num_return_sequences=B)
        else:
            seqs = GenerationMixin.generate(self.model, **kw, do_sample=True, temperature=arm["T"],
                                            top_k=0, top_p=1.0, num_return_sequences=arm["K"])
        if not torch.is_tensor(seqs):
            seqs = seqs.sequences
        N = seqs.shape[0]

        # teacher-forced pass for the probability of every emitted token; timed apart, since a
        # production decoder would get these from generate() for free
        import time
        if self.dev == "cuda":
            torch.cuda.synchronize()
        t_score = time.time()
        enc_h = self.model.model.encoder(enc).last_hidden_state
        logits = self.model(encoder_outputs=(enc_h.expand(N, -1, -1),), decoder_input_ids=seqs).logits
        lps = torch.log_softmax(logits.float(), dim=-1)[:, :-1]                   # predicts seqs[:, 1:]
        tgt = seqs[:, 1:]
        tok_lp = lps.gather(-1, tgt.unsqueeze(-1)).squeeze(-1).cpu()
        tok_ent = (-(lps.exp() * lps).sum(-1)).cpu()
        seqs = seqs.cpu()
        score_s = time.time() - t_score

        cands = []
        for i in range(N):
            gen = seqs[i, P:].tolist()
            if self.eot in gen:
                gen = gen[:gen.index(self.eot)]
            ids = [t for t in gen if t < self.eot]
            pos = [P - 1 + j for j, t in enumerate(gen) if t < self.eot]
            text = self.tok.decode(ids, skip_special_tokens=True).strip()
            lp = [float(tok_lp[i, p]) for p in pos]
            pr = [float(np.exp(x)) for x in lp]
            ent = [float(tok_ent[i, p]) for p in pos]
            wc = word_conf_from_ids(self.tok, ids, pr, text) if ids else None
            cands.append(token_stats(text, pr, lp, ent, wc, {"rank": i}))
        return cands, {"score_s": round(score_s, 4)}


# ---------------------------------------------------------------------------------------------

class CTC:
    """Parallel one-step control: greedy or K paths sampled from the CTC frame posteriors."""

    def __init__(self, spec: dict, precision: str | None = None):
        from transformers import AutoModelForCTC, AutoProcessor

        self.dev = _device()
        self.dtype = torch.float16 if self.dev == "cuda" else torch.float32
        self.proc = AutoProcessor.from_pretrained(spec["hf"])
        self.model = _from_pretrained(AutoModelForCTC, spec["hf"], self.dtype)
        self.model = self.model.to(self.dev).train(False).requires_grad_(False)
        self.tok = getattr(self.proc, "tokenizer", self.proc)
        pad = getattr(self.model.config, "pad_token_id", None)
        self.blank = int(pad) if pad is not None else None

    @torch.no_grad()
    def encode(self, audio, lang):
        inputs = self.proc(audio, sampling_rate=16000, return_tensors="pt")
        inputs = {k: (v.to(self.dev, dtype=self.dtype) if torch.is_floating_point(v) else v.to(self.dev))
                  for k, v in inputs.items() if hasattr(v, "to")}
        logits = self.model(**inputs).logits[0].float()
        if self.blank is None:
            self.blank = logits.shape[-1] - 1
        return torch.log_softmax(logits, dim=-1)                           # (T, V)

    def _collapse(self, path: torch.Tensor, lp: torch.Tensor):
        ids, confs, prev = [], [], None
        run: list[float] = []
        for t, tok in enumerate(path.tolist()):
            if tok != prev:
                if run:
                    confs.append(sum(run) / len(run))
                run = []
                if tok != self.blank:
                    ids.append(tok)
                prev = tok
            if tok != self.blank:
                run.append(float(lp[t, tok].exp()))
        if run:
            confs.append(sum(run) / len(run))
        return ids, confs

    @torch.no_grad()
    def decode(self, enc, arm, seed, lang):
        lp = enc
        if arm["mode"] == "greedy":
            paths = lp.argmax(-1, keepdim=True).T                           # (1, T)
        else:
            g = torch.Generator(device=lp.device)
            g.manual_seed(int(seed) & 0x7FFFFFFF)
            K = arm["K"]
            u = torch.rand((K,) + tuple(lp.shape), device=lp.device, generator=g).clamp_(min=1e-12)
            paths = (lp.unsqueeze(0) / arm["T"] - torch.log(-torch.log(u))).argmax(-1)   # (K, T)
        lp_cpu = lp.cpu()
        cands = []
        for p in paths.cpu():
            ids, confs = self._collapse(p, lp_cpu)
            try:
                text = self.tok.decode(ids, skip_special_tokens=True, group_tokens=False)
            except TypeError:
                text = self.tok.decode(ids, skip_special_tokens=True)
            text = text.strip()
            logp = [float(np.log(max(c, 1e-12))) for c in confs]
            wc = word_conf_from_ids(self.tok, ids, confs, text) if ids else None
            cands.append(token_stats(text, confs, logp, None, wc))
        return cands, {}


FAMILIES = {"wf": Whisfusion, "drax": Drax, "whisper": Whisper, "ctc": CTC}


def load(model_name: str, precision: str | None = None):
    from campaign.config import MODELS

    spec = MODELS[model_name]
    return FAMILIES[spec["family"]](spec, precision)
