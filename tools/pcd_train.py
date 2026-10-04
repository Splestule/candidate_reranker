#!/usr/bin/env python3
"""Train the last PDD step with peer conditioning (tools/pcd.py), one variant per call.

Each example is one row k of one training utterance in the state the decoder reaches before
its last step (tools/pcd_states.py): the row's tokens with a fresh 80 % mask -- the last step's
ratio -- plus the variant's extra input, and the reference tokens as targets at the masked
positions (padding included, as in Whisfusion's own training, so the step still decides
length). Every variant gets the same utterances, the same rows and masks (same seed), the same
steps and the same trainable parameters: LoRA rank 16 on every decoder linear plus the two
zero-initialised projections, which the plain variant carries but never uses.

Held out: 5 % of the utterances; every 100 steps, token accuracy on their non-padding targets
with the adapter on against the base model.

    PYTHONPATH=src:Whisfusion/src:tools python3 tools/pcd_train.py --states results/pcd/states_0.pkl,... \\
        --mode peer --out results/pcd/peer.pt
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", required=True, help="comma separated pcd_states.py outputs")
    ap.add_argument("--mode", choices=["peer", "self", "shuf", "plain"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=1200)
    ap.add_argument("--utts", type=int, default=8, help="utterances per batch")
    ap.add_argument("--rows", type=int, default=2, help="rows per utterance per batch")
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    import torch
    import torch.nn.functional as Fn
    import data as dataio
    import lora
    import pcd
    import wf_model
    from campaign.families import Whisfusion

    S = [s for p in a.states.split(",") if p and Path(p).exists() for s in pickle.loads(Path(p).read_bytes())]
    rng = random.Random(a.seed)
    order = list(range(len(S)))
    rng.shuffle(order)
    n_val = max(8, len(S) // 20)
    val, tr = order[:n_val], order[n_val:]
    print(f"{len(S)} utterances with states: {len(tr)} train, {len(val)} held out; mode {a.mode}", flush=True)

    torch.manual_seed(a.seed)
    wf = Whisfusion({}).wf
    import lit_gpt.diffmodel as DM            # out-of-place rotary under autograd, as train_explorer
    _rot = DM.apply_rotary_emb_func
    DM.apply_rotary_emb_func = lambda x, c, s_, il=False, ip=False: _rot(x, c, s_, il, ip and not torch.is_grad_enabled())
    model, dev = wf.model, wf.device
    L, pad, mask_id = 256, wf.pad_token_id, wf.mask_token_id
    params = lora.inject(model, a.rank, 2.0 * a.rank)
    inj = pcd.PeerInjector(model, a.mode).to(dev)
    model.to(dev)
    params += list(inj.proj.parameters()) + list(inj.agree.parameters())
    print(f"embedding at {inj.emb_name}; trainable {sum(p.numel() for p in params) / 1e6:.2f}M", flush=True)
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 50) * max(0.0, 1 - s / max(a.steps, 1)))
    scaler = torch.amp.GradScaler(enabled=dev == "cuda")
    ccache = {}

    def cond_of(i):
        if i not in ccache:
            with torch.no_grad():
                ccache[i] = wf_model.encode_audio(wf, dataio.load_audio(S[i]["audio"])).cpu()
            if len(ccache) > 1500:
                ccache.pop(next(iter(ccache)))
        return ccache[i]

    def batch(utts, gen):
        """Inputs, conditions, targets and the extra input for rows of the given utterances."""
        own, peers, cond, tgt = [], [], [], []
        for j, i in enumerate(utts):
            cur = torch.as_tensor(S[i]["cur"], device=dev).long()
            other = None
            if a.mode == "shuf":                  # another utterance of the same batch
                other = torch.as_tensor(S[utts[(j + 1) % len(utts)]]["cur"], device=dev).long()
            pt = pcd.peer_tokens(cur, other)
            t = torch.full((L,), pad, dtype=torch.long)
            t[:len(S[i]["tgt"])] = torch.tensor(S[i]["tgt"])
            c = cond_of(i)
            for k in rng.sample(range(cur.shape[0]), a.rows):
                own.append(cur[k])
                peers.append(pt[k])
                cond.append(c)
                tgt.append(t)
        own, peers = torch.stack(own), torch.stack(peers)
        cond, tgt = torch.cat(cond).to(dev), torch.stack(tgt).to(dev)
        m = torch.rand(own.shape, device=dev, generator=gen) < pcd.SCHEDULE[-1]
        m[:, 0] = False
        x = torch.where(m, torch.full_like(own, mask_id), own)
        return x, own, peers, cond, tgt, m

    @torch.no_grad()
    def val_acc():
        gen = torch.Generator(device=dev)
        gen.manual_seed(1234)
        hit = {"on": 0, "off": 0}
        tot = 0
        for b in range(0, len(val), a.utts):
            x, own, peers, cond, tgt, m = batch(val[b:b + a.utts], gen)
            sel = m & (tgt != pad)
            for key, on in (("off", False), ("on", True)):
                lora.set_enabled(model, on)
                inj.add = inj.features(None, own, peers) if on else None
                logits = model(idx=x, condition=cond)
                inj.add = None
                hit[key] += int((logits.argmax(-1)[sel] == tgt[sel]).sum())
            tot += int(sel.sum())
        lora.set_enabled(model, True)
        return {k: v / max(tot, 1) for k, v in hit.items()}

    with torch.no_grad():                     # the hook must reach the decoder, or every variant is plain
        c0 = cond_of(tr[0]).to(dev)
        x0 = torch.as_tensor(S[tr[0]]["cur"][:1], device=dev).long()
        base_logits = model(idx=x0, condition=c0).float()
        inj.add = torch.randn(1, x0.shape[1], inj.emb.embedding_dim, device=dev)
        hooked = model(idx=x0, condition=c0).float()
        inj.add = None
        assert not torch.allclose(base_logits, hooked), f"injection at {inj.emb_name} does not reach the decoder"
        print(f"injection at {inj.emb_name} reaches the decoder: max logit change "
              f"{(hooked - base_logits).abs().max().item():.3f}", flush=True)
    log = [dict(step=0, **val_acc())]
    print("held-out token accuracy:", json.dumps(log[-1]), flush=True)
    gen = torch.Generator(device=dev)
    gen.manual_seed(a.seed)
    model.train()
    lora.set_enabled(model, True)
    t0, losses = time.time(), []
    for step in range(1, a.steps + 1):
        x, own, peers, cond, tgt, m = batch(rng.sample(tr, a.utts), gen)
        with torch.autocast("cuda", dtype=torch.float16, enabled=dev == "cuda"):
            inj.add = inj.features(None, own, peers)
            logits = model(idx=x, condition=cond)
            inj.add = None
            loss = Fn.cross_entropy(logits[m].float(), tgt[m])
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        scaler.step(opt)
        scaler.update()
        sched.step()
        losses.append(loss.item())
        if step % 100 == 0 or step == a.steps:
            model.eval()
            d = dict(step=step, loss=sum(losses[-100:]) / len(losses[-100:]), **val_acc())
            model.train()
            log.append(d)
            print(f"step {step}: {json.dumps(d)}  {(time.time() - t0) / step:.2f} s/step", flush=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(dict(state=lora.lora_state(model), r=a.rank, alpha=2.0 * a.rank, inj=inj.state(),
                    mode=a.mode, emb=inj.emb_name, args=vars(a), log=log), out)
    print(f"saved {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
