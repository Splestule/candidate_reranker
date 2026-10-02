#!/usr/bin/env python3
"""Train a LoRA explorer next to the frozen Whisfusion decoder (the anchor).

Both modes run Whisfusion's own masked-diffusion loss on LibriSpeech train-clean-100 (data the
base model was already trained on, so any gain cannot come from new data):

  plain     the usual loss: cross-entropy on the masked positions. The control: fine-tuning
            alone, nothing about composition.
  explorer  the anchor's step-zero reading of the fully masked sequence marks the positions it
            gets wrong. There the loss is up-weighted (alpha) and an unlikelihood term (beta)
            pushes the explorer away from the anchor's wrong token, so that the explorer's
            candidates disagree with the anchor where the anchor errs, and only there, which is
            what the confusion network can use.

    python3 tools/train_explorer.py --mode explorer --out results/explorer/explorer.pt
"""

from __future__ import annotations

import argparse
import io
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")


def batches(files, bs, skip, seed):
    """(audio arrays, transcripts) from LibriSpeech parquet shards, shuffled within a buffer."""
    import pyarrow.parquet as pq
    import soundfile as sf
    rng = random.Random(seed)
    buf = []
    for f in files:
        t = pq.read_table(f, columns=["audio", "text", "id"])
        for r in t.to_pylist():
            if r["id"] in skip:
                continue
            buf.append(r)
        rng.shuffle(buf)
        while len(buf) >= bs:
            chunk, buf = buf[:bs], buf[bs:]
            yield [sf.read(io.BytesIO(r["audio"]["bytes"]), dtype="float32")[0] for r in chunk], \
                [r["text"] for r in chunk]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["plain", "explorer"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shards", type=int, default=8, help="train-clean-100 parquet files (~2k utts each)")
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--alpha_err", type=float, default=4.0, help="extra weight on anchor-error positions")
    ap.add_argument("--beta_ul", type=float, default=1.0, help="unlikelihood of the anchor's wrong token")
    ap.add_argument("--mask_min", type=float, default=0.5)
    ap.add_argument("--mask_max", type=float, default=1.0)
    ap.add_argument("--val_utts", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    if a.mode == "plain":
        a.alpha_err = a.beta_ul = 0.0

    import torch
    import torch.nn.functional as Fn
    from huggingface_hub import hf_hub_download
    from campaign.families import Whisfusion
    import lora

    torch.manual_seed(a.seed)
    wf = Whisfusion({}).wf
    # lit_gpt rotates k in place, which autograd refuses on a split view; out of place is the
    # same arithmetic
    import lit_gpt.diffmodel as DM
    _rot = DM.apply_rotary_emb_func
    DM.apply_rotary_emb_func = lambda x, c, s_, il=False, ip=False: _rot(x, c, s_, il, ip and not torch.is_grad_enabled())
    dev = wf.device
    model = wf.model
    params = lora.inject(model, a.rank, 2.0 * a.rank)
    print(f"LoRA: {sum(p.numel() for p in params) / 1e6:.2f}M trainable parameters", flush=True)
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / 50) * max(0.0, 1 - s / a.steps))
    scaler = torch.amp.GradScaler(enabled=dev == "cuda")
    mask_id = wf.mask_token_id

    files = [hf_hub_download("openslr/librispeech_asr", f"all/train.clean.100/{i:04d}.parquet",
                             repo_type="dataset") for i in range(a.shards)]
    # the first val_utts of the last shard are held out for the diagnostics
    import pyarrow.parquet as pq
    val_rows = pq.read_table(files[-1], columns=["audio", "text", "id"]).slice(0, a.val_utts).to_pylist()
    val_ids = {r["id"] for r in val_rows}

    def prep(audios, texts):
        feats = wf.whisper_processor(audios, sampling_rate=16000, return_tensors="pt").input_features
        with torch.no_grad():
            cond = wf.whisper_encoder(feats.to(dev, wf.dtype)).last_hidden_state.to(wf.dtype)
        tgt = wf.tokenizer(texts, return_tensors="pt", padding="max_length", truncation=True,
                           max_length=256).input_ids.to(dev)
        lora.set_enabled(model, False)
        with torch.no_grad():
            anchor = model(idx=probe(tgt), condition=cond).argmax(-1)
        return cond, tgt, anchor

    def probe(tgt):
        """The fully masked step-zero input; position 0 keeps BOS, as in decode.py."""
        x = torch.full_like(tgt, mask_id)
        x[:, 0] = tgt[:, 0]
        return x

    def step_loss(cond, tgt, anchor):
        b, l = tgt.shape
        p = a.mask_min + (a.mask_max - a.mask_min) * torch.rand((b, 1), device=dev)
        m = torch.rand((b, l), device=dev) < p
        m[:, 0] = False
        noisy = torch.where(m, mask_id, tgt)
        lora.set_enabled(model, True)
        logits = model(idx=noisy, condition=cond).float()
        err = (anchor != tgt) & m
        w = 1.0 + a.alpha_err * err.float()
        ce = Fn.cross_entropy(logits[m], tgt[m], reduction="none")
        loss = (ce * w[m]).sum() / w[m].sum()
        ul = torch.zeros((), device=dev)
        if a.beta_ul > 0 and err.any():
            pw = torch.softmax(logits[err], -1).gather(1, anchor[err][:, None]).squeeze(1)
            ul = -torch.log1p(-pw.clamp(max=1 - 1e-4)).mean()
            loss = loss + a.beta_ul * ul
        return loss, ce.mean().item(), ul.item(), err.sum().item() / max(m.sum().item(), 1)

    @torch.no_grad()
    def diagnose():
        """Step-zero reading on held-out utterances: where the anchor errs, how often the
        explorer is right, and how often it repeats the anchor's wrong token."""
        tot = dict(err=0, exp_right_on_err=0, exp_same_wrong=0, ok=0, exp_right_on_ok=0)
        for i in range(0, len(val_rows), a.bs):
            rows = val_rows[i:i + a.bs]
            import soundfile as sf
            cond, tgt, anchor = prep([sf.read(io.BytesIO(r["audio"]["bytes"]), dtype="float32")[0]
                                      for r in rows], [r["text"] for r in rows])
            real = tgt != wf.tokenizer.pad_token_id
            real[:, 0] = False
            lora.set_enabled(model, True)
            ex = model(idx=probe(tgt), condition=cond).argmax(-1)
            err = (anchor != tgt) & real
            ok = (anchor == tgt) & real
            tot["err"] += err.sum().item()
            tot["ok"] += ok.sum().item()
            tot["exp_right_on_err"] += ((ex == tgt) & err).sum().item()
            tot["exp_same_wrong"] += ((ex == anchor) & err).sum().item()
            tot["exp_right_on_ok"] += ((ex == tgt) & ok).sum().item()
        e, o = max(tot["err"], 1), max(tot["ok"], 1)
        return dict(anchor_err_rate=tot["err"] / (e + o), explorer_right_where_anchor_wrong=tot["exp_right_on_err"] / e,
                    explorer_repeats_anchor_error=tot["exp_same_wrong"] / e,
                    explorer_right_where_anchor_right=tot["exp_right_on_ok"] / o)

    def save(log):
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        torch.save(dict(state=lora.lora_state(model), r=a.rank, alpha=2.0 * a.rank, args=vars(a),
                        log=log), out)

    model.train()
    log = []
    print("before training:", json.dumps(diagnose()), flush=True)
    t0, s = time.time(), 0
    while s < a.steps:
        for audios, texts in batches(files, a.bs, val_ids, a.seed + s):
            cond, tgt, anchor = prep(audios, texts)
            with torch.autocast("cuda", dtype=torch.float16, enabled=dev == "cuda"):
                loss, ce, ul, er = step_loss(cond, tgt, anchor)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            scaler.step(opt)
            scaler.update()
            sched.step()
            s += 1
            if s % 50 == 0:
                print(f"step {s}: loss {loss.item():.3f} ce {ce:.3f} ul {ul:.3f} "
                      f"anchor-error share {er:.3f}  {(time.time() - t0) / s:.2f} s/step", flush=True)
            if s % 250 == 0 or s == a.steps:
                d = diagnose()
                d["step"] = s
                log.append(d)
                print("diagnostics:", json.dumps(d), flush=True)
                save(log)
            if s >= a.steps:
                break
    save(log)
    print(f"saved {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
