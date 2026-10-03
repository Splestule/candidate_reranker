#!/usr/bin/env python3
"""Train the decoder for the question tools/refine.py asks it: fill these positions, given the
audio and the candidates' consensus around them.

Zero-shot the decoder was never trained on that input -- in training the unmasked context is
always the reference, never a consensus that is itself partly wrong, and the span is never
chosen by where K candidates disagree. Mode `refine` trains a LoRA on exactly the inference
input: for an utterance's K candidates (shard 0 of --sets, results/cand_audio.pkl) the
consensus is written out, one contested group (same selection and grouping as refine.py) is
masked at the length of the reference's words for it, and the loss is cross-entropy on those
reference tokens. 30 % of utterances also contribute one uncontested slot, so "masked" does
not come to mean "must change".

Mode `plain` is the control: the same utterances, steps and adapter, trained with Whisfusion's
own objective on the reference (mask ratio 0.5-1.0). A refine adapter that beats it shows the
input matters, not only in-domain fine-tuning.

Held out: 5 % of the utterances; every 100 steps the token accuracy on their refine examples
with the adapter on and off.

    PYTHONPATH=src:Whisfusion/src:tools python3 tools/train_refiner.py --mode refine \\
        --cand results/cand_audio.pkl --data /tmp/campaign_data --sets ami,earnings22 --out r.pt
"""

from __future__ import annotations

import argparse
import json
import pickle
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

EPS = ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["refine", "plain"], required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--sets", required=True, help="comma separated training sets (shard 0)")
    ap.add_argument("--arms", default="anchor-k8,anchor-k4")
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--max_slots", type=int, default=10)
    ap.add_argument("--conf_thr", type=float, default=0.7)
    ap.add_argument("--max_run", type=int, default=4)
    ap.add_argument("--seq_len", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    import torch
    import torch.nn.functional as Fn
    import data as dataio
    import decompose as D
    import lora
    import refine as RF
    import wf_model
    from campaign.families import Whisfusion

    rng = random.Random(a.seed)
    torch.manual_seed(a.seed)
    sets = set(a.sets.split(","))
    arms = set(a.arms.split(","))
    recs = [r for r in pickle.loads(Path(a.cand).read_bytes())
            if r["arm"] in arms and r["set"] in sets and r.get("shard") == 0]
    audio = {}
    for s in sets:
        for u in dataio.iter_manifest(str(Path(a.data) / "manifests" / f"{s}.jsonl")):
            audio[(s, u.id)] = u.audio_path

    wf = Whisfusion({}).wf
    import lit_gpt.diffmodel as DM            # out-of-place rotary under autograd, as train_explorer
    _rot = DM.apply_rotary_emb_func
    DM.apply_rotary_emb_func = lambda x, c, s_, il=False, ip=False: _rot(x, c, s_, il, ip and not torch.is_grad_enabled())
    tok, model, dev = wf.tokenizer, wf.model, wf.device
    mask_id, pad_id = wf.mask_token_id, wf.pad_token_id
    bos = tok.bos_token_id if tok.bos_token_id is not None else 0
    L = a.seq_len
    wc = {}

    def wtoks(w):
        if w not in wc:
            wc[w] = tok(w.upper(), add_special_tokens=False)["input_ids"] if w else []
        return wc[w]

    def seq(words, span_at=None, span=()):
        """BOS + words, the slot span_at replaced by the token list span; positions of span."""
        ids, pos = [bos], []
        for i, w in enumerate(words):
            if i == span_at:
                pos = list(range(len(ids), len(ids) + len(span)))
                ids += list(span)
            elif w != EPS:
                ids += wtoks(w)
        return (ids + [pad_id] * (L - len(ids)), pos) if len(ids) <= L else (None, None)

    # ---- examples: (utterance key, input ids with the span masked, positions, target tokens)
    utts = sorted({(r["set"], r["id"]) for r in recs if (r["set"], r["id"]) in audio})
    rng.shuffle(utts)
    held = set(utts[:max(1, len(utts) // 20)])
    ex_tr, ex_val, refs = [], [], {}
    for r in recs:
        key = (r["set"], r["id"])
        if key not in audio:
            continue
        refs[key] = r["ref"]
        net = RF.network(r, int(r["arm"].rsplit("-k", 1)[1]))
        if net is None:
            continue
        ok, cands, bb, slots, n, top = net
        ref = D.reference_by_slot(cands, bb, r["ref"])
        if len(ref) != len(slots):
            continue
        cidx = RF.contested(slots, top, n, a.max_slots, a.conf_thr)
        gs = RF.groups(cidx, a.max_run)
        free = [i for i in range(len(slots)) if i not in cidx and ref[i] != EPS]
        if free and rng.random() < 0.3:
            gs.append([rng.choice(free)])
        for g in gs:
            tgt = [t for i in g if ref[i] != EPS for t in wtoks(ref[i])]
            if not tgt:
                continue
            words = list(top)
            for i in g[1:]:
                words[i] = EPS
            ids, pos = seq(words, g[0], [mask_id] * len(tgt))
            if ids is None:
                continue
            (ex_val if key in held else ex_tr).append((key, ids, pos, tgt))
    print(f"{len(utts)} utterances on {len(sets)} sets; refine examples: {len(ex_tr)} train, "
          f"{len(ex_val)} held out", flush=True)
    if not ex_tr:
        return 1
    plain = [k for k in sorted(refs) if k not in held]

    params = lora.inject(model, a.rank, 2.0 * a.rank)
    model.to(dev)
    print(f"LoRA: {sum(p.numel() for p in params) / 1e6:.2f}M trainable parameters, mode {a.mode}", flush=True)
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 50) * max(0.0, 1 - s / a.steps))
    scaler = torch.amp.GradScaler(enabled=dev == "cuda")

    ccache = {}

    def cond_of(keys):
        out = []
        for k in keys:
            if k not in ccache:
                with torch.no_grad():
                    ccache[k] = wf_model.encode_audio(wf, dataio.load_audio(audio[k])).cpu()
                if len(ccache) > 1200:
                    ccache.pop(next(iter(ccache)))
            out.append(ccache[k])
        return torch.cat(out).to(dev)

    def refine_batch(exs):
        x = torch.tensor([e[1] for e in exs], device=dev)
        rows = torch.tensor([j for j, e in enumerate(exs) for _ in e[2]], device=dev)
        cols = torch.tensor([p for e in exs for p in e[2]], device=dev)
        y = torch.tensor([t for e in exs for t in e[3]], device=dev)
        return x, rows, cols, y

    def plain_batch(keys):
        x = torch.full((len(keys), L), pad_id, dtype=torch.long)
        for j, k in enumerate(keys):
            ids = [bos] + [t for w in refs[k] for t in wtoks(w)]
            x[j, :min(len(ids), L)] = torch.tensor(ids[:L])
        x = x.to(dev)
        p = 0.5 + 0.5 * torch.rand((len(keys), 1), device=dev)
        m = torch.rand(x.shape, device=dev) < p
        m[:, 0] = False
        rows, cols = m.nonzero(as_tuple=True)
        return torch.where(m, mask_id, x), rows, cols, x[rows, cols]

    @torch.no_grad()
    def val_acc():
        res = {}
        for on in (False, True):
            lora.set_enabled(model, on)
            hit = tot = 0
            for b in range(0, len(ex_val), a.bs):
                exs = ex_val[b:b + a.bs]
                x, rows, cols, y = refine_batch(exs)
                logits = model(idx=x, condition=cond_of([e[0] for e in exs]))
                hit += int((logits[rows, cols].argmax(-1) == y).sum())
                tot += len(y)
            res["on" if on else "off"] = hit / max(tot, 1)
        lora.set_enabled(model, True)
        return res

    log = [dict(step=0, **val_acc())]
    print("held-out refine token accuracy:", json.dumps(log[-1]), flush=True)
    model.train()
    lora.set_enabled(model, True)
    t0, step, run_loss = time.time(), 0, []
    while step < a.steps:
        if a.mode == "refine":
            exs = rng.sample(ex_tr, min(a.bs, len(ex_tr)))
            keys = [e[0] for e in exs]
            x, rows, cols, y = refine_batch(exs)
        else:
            keys = rng.sample(plain, min(a.bs, len(plain)))
            x, rows, cols, y = plain_batch(keys)
        cond = cond_of(keys)
        with torch.autocast("cuda", dtype=torch.float16, enabled=dev == "cuda"):
            logits = model(idx=x, condition=cond)
            loss = Fn.cross_entropy(logits[rows, cols].float(), y)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        scaler.step(opt)
        scaler.update()
        sched.step()
        step += 1
        run_loss.append(loss.item())
        if step % 100 == 0 or step == a.steps:
            model.eval()
            d = dict(step=step, loss=sum(run_loss[-100:]) / len(run_loss[-100:]), **val_acc())
            model.train()
            log.append(d)
            print(f"step {step}: {json.dumps(d)}  {(time.time() - t0) / step:.2f} s/step", flush=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(dict(state=lora.lora_state(model), r=a.rank, alpha=2.0 * a.rank, args=vars(a), log=log), out)
    print(f"saved {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
