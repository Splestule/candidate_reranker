"""Drax with the audio encoded once, K candidates in one batch, and per-token confidences.

The public Transcriber encodes the same file once per candidate, in fp32, and returns only text.
This keeps Drax's own modules and weights and replaces only the driver:

- the Whisper encoder and the cross-attention K/V cache run once per utterance and are expanded
  over the K candidates;
- the DiT blocks run under fp16 autocast on Turing (bf16 is emulated there), with the embeddings,
  time embedding, output layer and residual stream kept in fp32 so large activations cannot
  overflow;
- the sampler is DraxMixtureDiscreteEulerSolver with PolynomialConvexScheduler(n=1), written out
  so the one-hot velocity is never materialised: with kappa_t = t, a position jumps to its
  sampled x_1 with probability 1 - exp(-h / (1 - t)) unless it already holds it, which is what
  the reference solver's categorical over u reduces to.

The drax package is imported without running drax/__init__.py, which would pull in torchaudio and
flow_matching for the Transcriber this module does not use.
"""

from __future__ import annotations

import importlib
import json
import math
import sys
import types
from contextlib import nullcontext
from pathlib import Path

import torch
import torch.nn.functional as F

from campaign.tokwords import word_conf_from_ids


def import_drax(drax_root: str):
    """drax.model.* without drax/__init__.py."""
    pkg_dir = Path(drax_root) / "drax"
    if "drax" not in sys.modules:
        pkg = types.ModuleType("drax")
        pkg.__path__ = [str(pkg_dir)]
        sys.modules["drax"] = pkg
    return importlib.import_module("drax.model.transformer")


def _sinusoids(length: int, channels: int, max_timescale: float = 10000) -> torch.Tensor:
    log_inc = math.log(max_timescale) / (channels // 2 - 1)
    inv = torch.exp(-log_inc * torch.arange(channels // 2))
    t = torch.arange(length)[:, None] * inv[None, :]
    return torch.cat([t.sin(), t.cos()], dim=1)


def _build_encoder(wcfg: dict):
    from transformers import WhisperConfig
    from transformers.models.whisper.modeling_whisper import WhisperEncoder

    conf = WhisperConfig(**{k: v for k, v in wcfg.items() if k not in ("torch_dtype", "transformers_version")})
    try:
        with torch.device("meta"):
            enc = WhisperEncoder(conf)
        return enc.to_empty(device="cpu")
    except Exception:
        return WhisperEncoder(conf)


class DraxFast:
    def __init__(self, model_id: str, drax_root: str, device: str = "cuda", precision: str = "fp16",
                 verbose: bool = True):
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file
        from transformers import WhisperFeatureExtractor, WhisperTokenizer

        tr = import_drax(drax_root)
        self.device = device
        self.precision = precision if device == "cuda" else "fp32"
        self.block_dtype = {"fp16": torch.float16, "bf16": torch.bfloat16, "fp32": torch.float32}[self.precision]

        with open(hf_hub_download(model_id, "config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        dcfg, wcfg = cfg["decoder_config"], cfg["whisper_config"]

        enc = _build_encoder(wcfg)
        enc_state = load_file(hf_hub_download(model_id, "encoder.safetensors"))
        res = enc.load_state_dict(enc_state, strict=False)
        missing = [k for k in res.missing_keys if "embed_positions" not in k]
        if missing or res.unexpected_keys:
            raise RuntimeError(f"Drax encoder keys: missing {missing[:5]} unexpected {res.unexpected_keys[:5]}")
        if not any(k.endswith("embed_positions.weight") for k in enc_state):
            with torch.no_grad():
                enc.embed_positions.weight.copy_(_sinusoids(*enc.embed_positions.weight.shape))
        del enc_state
        enc_dtype = torch.float16 if device == "cuda" else torch.float32
        self.encoder = enc.to(device=device, dtype=enc_dtype).train(False).requires_grad_(False)

        dec = tr.Transformer(vocab_size=dcfg["vocab_size"], masked=dcfg.get("masked", False), config=dcfg)
        dec_state = load_file(hf_hub_download(model_id, "decoder.safetensors"))
        res = dec.load_state_dict(dec_state, strict=False)
        missing = [k for k in res.missing_keys if "inv_freq" not in k]
        if missing or res.unexpected_keys:
            raise RuntimeError(f"Drax decoder keys: missing {missing[:5]} unexpected {res.unexpected_keys[:5]}")
        del dec_state
        dec = dec.to(device).train(False).requires_grad_(False)
        if self.block_dtype != torch.float32:
            for blk in dec.blocks:
                blk.to(self.block_dtype)
        self.dec = dec
        self.vocab = dcfg["vocab_size"]
        self.length = dcfg["length"]

        self.fe = WhisperFeatureExtractor.from_pretrained("openai/whisper-large-v3")
        self.tok = WhisperTokenizer.from_pretrained("openai/whisper-large-v3")
        self.eot = self.tok.convert_tokens_to_ids("<|endoftext|>")
        self.sot = self.tok.convert_tokens_to_ids("<|startoftranscript|>")
        self.transcribe_id = self.tok.convert_tokens_to_ids("<|transcribe|>")
        self.notimestamps = self.tok.convert_tokens_to_ids("<|notimestamps|>")
        self.langs = dcfg.get("support_language_codes", ["en"])
        if verbose:
            n_dec = sum(p.numel() for p in dec.parameters()) / 1e6
            n_enc = sum(p.numel() for p in self.encoder.parameters()) / 1e6
            print(f"[drax] decoder {n_dec:.0f}M ({self.precision} blocks), encoder {n_enc:.0f}M, "
                  f"canvas {self.length}, vocab {self.vocab}", flush=True)

    # -----------------------------------------------------------------------------------------

    def _ac(self, dtype):
        if self.device != "cuda" or dtype == torch.float32:
            return nullcontext()
        return torch.autocast("cuda", dtype=dtype)

    @torch.no_grad()
    def encode(self, audio, lang: str = "en") -> dict:
        feats = self.fe(audio, sampling_rate=16000, return_tensors="pt").input_features
        feats = feats.to(self.device, dtype=next(self.encoder.parameters()).dtype)
        h = self.encoder(feats).last_hidden_state                                # (1, 1500, 1280)
        if self.block_dtype == torch.float32:
            h = h.float()
        with self._ac(self.block_dtype):
            proj = self.dec.audio_proj(h)
            ks, vs = [], []
            for blk in self.dec.blocks:
                na = blk.norm_audio(proj)
                ks.append(blk.k_cross(na))
                vs.append(blk.v_cross(na))
        dt = self.block_dtype
        return {"k": [k.to(dt) for k in ks], "v": [v.to(dt) for v in vs]}

    def _prompt(self, lang: str) -> list[int]:
        return [self.sot, self.tok.convert_tokens_to_ids(f"<|{lang}|>"), self.transcribe_id,
                self.notimestamps]

    def _logits(self, x_t, t, preserve, cache) -> torch.Tensor:
        K = x_t.shape[0]
        d = self.dec
        x = d.vocab_embed(x_t) + d.preserve_embeddings(preserve.long())          # fp32 residual
        c = F.silu(d.time_embedding(time=t))
        rot = d.rotary_emb(x=x)
        with self._ac(self.block_dtype):
            for i, blk in enumerate(d.blocks):
                x = blk(x=x, rotary_cos_sin=rot, c=c, audio=None,
                        audio_k=cache["k"][i].expand(K, -1, -1), audio_v=cache["v"][i].expand(K, -1, -1))
        head = torch.float16 if self.block_dtype != torch.float32 else torch.float32
        with self._ac(head):
            out = d.output_layer(x=x.float(), c=c)
        return out.float()

    @torch.no_grad()
    def sample(self, cache: dict, lang: str, K: int, temperature: float, steps: int, seed: int,
               chunk: int = 32) -> list[dict]:
        """K candidates in the dump schema. Chunks bound memory at large K."""
        cands: list[dict] = []
        for start in range(0, K, chunk):
            cands += self._sample(cache, lang, min(chunk, K - start), temperature, steps,
                                  seed + 7919 * start)
        return cands

    def _sample(self, cache, lang, K, temperature, steps, seed) -> list[dict]:
        dev = self.device
        g = torch.Generator(device=dev)
        g.manual_seed(int(seed) & 0x7FFFFFFF)
        L, V = self.length, self.vocab
        prompt = torch.tensor(self._prompt(lang), device=dev)
        P = len(prompt)

        x_init = torch.randint(0, V, (K, L), device=dev, generator=g)
        x_init[:, :P] = prompt
        preserve = torch.zeros((K, L), dtype=torch.bool, device=dev)
        preserve[:, :P] = True

        h = 1.0 / steps if steps > 1 else 1.0 - 1e-8
        n_steps = math.ceil(1.0 / h - 1e-9)
        grid = [h * i for i in range(n_steps)] + [1.0]
        x_t = x_init.clone()
        final_logits = None
        inv_T = 1.0 / max(float(temperature), 1e-6)
        for i in range(n_steps):
            t, dt = grid[i], grid[i + 1] - grid[i]
            logits = self._logits(x_t, torch.full((K,), t, device=dev), preserve, cache)
            # Gumbel-max is categorical(softmax(logits / T)) with an explicit generator
            gum = torch.rand(logits.shape, device=dev, generator=g)
            gum.clamp_(min=1e-12).log_().neg_().log_().neg_()
            gum.add_(logits, alpha=inv_T)
            x_1 = gum.argmax(dim=-1)
            del gum
            x_1 = torch.where(preserve, x_init, x_1)
            x_t = torch.where(preserve, x_init, x_t)
            if i == n_steps - 1:
                x_t = x_1
                final_logits = logits
            else:
                p_jump = 1.0 - math.exp(-dt / (1.0 - t))
                jump = (torch.rand((K, L), device=dev, generator=g) < p_jump) & (x_1 != x_t)
                x_t = torch.where(jump, x_1, x_t)
                del logits

        if not bool(torch.isfinite(final_logits).all()):
            raise FloatingPointError(f"non-finite Drax logits under {self.precision}")
        logp = torch.log_softmax(final_logits, dim=-1)
        del final_logits
        chosen_lp = logp.gather(-1, x_t.unsqueeze(-1)).squeeze(-1)                 # (K, L)
        ent = -(logp.exp() * logp).sum(-1)
        del logp

        toks = x_t.cpu()
        chosen_lp, ent = chosen_lp.float().cpu(), ent.float().cpu()
        texts = self.tok.batch_decode(toks[:, P:], skip_special_tokens=True)
        out = []
        for i in range(K):
            ids = toks[i, P:]
            text_pos = (ids < self.eot).nonzero().squeeze(-1)
            text = texts[i].strip()
            if text_pos.numel() == 0:
                out.append(dict(text=text, avg_conf=0.0, min_conf=0.0, median_conf=0.0,
                                mean_logprob=-20.0, mean_entropy=0.0, n_tokens=0))
                continue
            lp = chosen_lp[i, P:][text_pos]
            pr = lp.exp()
            tid = ids[text_pos].tolist()
            d = dict(text=text,
                     avg_conf=float(pr.mean()),          # probability of the token actually emitted
                     min_conf=float(pr.min()),
                     median_conf=float(pr.median()),
                     mean_logprob=float(lp.mean()),
                     mean_entropy=float(ent[i, P:][text_pos].mean()),
                     n_tokens=len(tid))
            wc = word_conf_from_ids(self.tok, tid, pr.tolist(), text)
            if wc is not None:
                d["word_conf"] = wc
            out.append(d)
        return out
