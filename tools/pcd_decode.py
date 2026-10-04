#!/usr/bin/env python3
"""Evaluation decodes for peer-conditioned denoising: five last steps from one shared state.

Per utterance (the same utterances and shards as --like_arm in --like): tree-early PDD to the
last step once (11 decoder passes), then the last step (8 rows) five ways, all with the same
mask:
  pcdbase-k8         the base model: exactly tree-early K=8 (checked against decode.pdd_decode
                     on the first --check utterances)
  pcd-<mode>-k8      the adapter of each trained variant (tools/pcd_train.py), with its extra input
The shuffled control reads the previous utterance's rows. Records in cand_audio format.

    PYTHONPATH=src:Whisfusion/src:tools python3 tools/pcd_decode.py --like results/cand_audio.pkl \\
        --data /tmp/campaign_data --adapters peer=results/pcd/peer.pt,... --out results/pcd/dec_0.pkl
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--like", required=True)
    ap.add_argument("--like_arm", default="anchor-k8")
    ap.add_argument("--data", required=True)
    ap.add_argument("--adapters", default="", help="mode=path,... from tools/pcd_train.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--part", default="0/1")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--check", type=int, default=20)
    a = ap.parse_args()

    import torch
    import data as dataio
    import decode as dec
    import lora
    import pcd
    import wf_model
    from audio_slots import acoustic_reading, word_scores
    from campaign.families import Whisfusion
    from scorers import normalize

    pi, pn = (int(x) for x in a.part.split("/"))
    like = [r for r in pickle.loads(Path(a.like).read_bytes()) if r["arm"] == a.like_arm][pi::pn]
    if a.limit:
        like = like[:a.limit]
    audio = {}
    for s in sorted({r["set"] for r in like}):
        audio[s] = {u.id: u.audio_path for u in dataio.iter_manifest(str(Path(a.data) / "manifests" / f"{s}.jsonl"))}
    wf = Whisfusion({}).wf
    model, dev = wf.model, wf.device

    ads = {}
    for spec in a.adapters.split(","):
        if "=" in spec:
            mode, p = spec.split("=", 1)
            ads[mode] = torch.load(p, map_location="cpu", weights_only=False)
    inj = {}
    if ads:
        first = next(iter(ads.values()))
        lora.inject(model, first["r"], first["alpha"])
        for mode, ck in ads.items():
            inj[mode] = pcd.PeerInjector(model, ck["mode"]).to(dev)
            inj[mode].load(ck["inj"])
            ck["state"] = {k: v.to(dev) for k, v in ck["state"].items()}
        model.to(dev)
    print(f"{len(like)} utterances; adapters {sorted(ads)}", flush=True)

    def sync():
        if dev == "cuda":
            torch.cuda.synchronize()

    def record(src, cands, arm, lp):
        rows = []
        for c in cands:
            words = normalize(c.text).split()
            wc = c.word_conf
            sc = word_scores(wf, lp, c.text, 2) if words else None
            ok = (words and wc is not None and len(wc) == len(words)
                  and sc is not None and len(sc) == len(words))
            rows.append(dict(words=words, avg_conf=c.avg_conf, conf=list(wc) if ok else None,
                             aud=[math.exp(x) for x in sc] if ok else None, source="anchor"))
        return dict(set=src["set"], id=src["id"], cluster=src.get("cluster"), lang=src.get("lang", "en"),
                    ref=src["ref"], ref_text=src.get("ref_text"), shard=src.get("shard"), arm=arm, cands=rows)

    @torch.no_grad()
    def last_step(cur, m, mode, other):
        x = torch.where(m, torch.full_like(cur, wf.mask_token_id), cur)
        if mode is None:
            if ads:
                lora.set_enabled(model, False)
        else:
            lora.set_enabled(model, True)
            inj[mode].add = inj[mode].features(None, cur, pcd.peer_tokens(cur, other if mode == "shuf" else None))
        logits = model(idx=x, condition=cond.expand(cur.shape[0], -1, -1))
        if mode is not None:
            inj[mode].add = None
            lora.set_enabled(model, False)
        final = torch.where(m, logits.argmax(-1), x)
        return dec._candidates(wf, final, logits)

    out_p = Path(a.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    tm = {"first": [], "last": {}, "checked": 0, "mismatch": 0}
    out, prev, t0, n = [], None, time.time(), 0
    # warm-up, and a first "previous utterance" for the shuffled control
    w = next(r for r in like if r["id"] in audio.get(r["set"], {}))
    cond = wf_model.encode_audio(wf, dataio.load_audio(audio[w["set"]][w["id"]]))
    prev, _ = pcd.first_steps(wf, cond, 1)
    for src in like:
        if src["id"] not in audio.get(src["set"], {}):
            continue
        try:
            cond = wf_model.encode_audio(wf, dataio.load_audio(audio[src["set"]][src["id"]]))
            seed = zlib.crc32(f"{src['set']}/{src['id']}".encode()) % (2 ** 31)
            sync()
            t1 = time.perf_counter()
            cur, gen = pcd.first_steps(wf, cond, seed)
            m = pcd.last_mask(cur, gen)
            sync()
            tm["first"].append(1000 * (time.perf_counter() - t1))
            lp = acoustic_reading(wf, cond, 256)
            for mode in [None] + sorted(ads):
                if mode is not None:            # swapping adapters is bookkeeping, not decoding
                    model.load_state_dict(ads[mode]["state"], strict=False)
                sync()
                t1 = time.perf_counter()
                cands = last_step(cur, m, mode, prev)
                sync()
                arm = "pcdbase-k8" if mode is None else f"pcd-{mode}-k8"
                tm["last"].setdefault(arm, []).append(1000 * (time.perf_counter() - t1))
                out.append(record(src, cands, arm, lp))
                if mode is None and tm["checked"] < a.check:
                    if ads:
                        lora.set_enabled(model, False)
                    ref = dec.pdd_decode(wf, cond, n_candidates=8, n_steps=4, branch_schedule=pcd.BRANCH, seed=seed)
                    tm["checked"] += 1
                    tm["mismatch"] += int([c.text for c in ref.candidates] != [c.text for c in cands])
            prev = cur
        except Exception as e:
            print(f"  !! {src['set']}/{src['id']}: {type(e).__name__}: {e}", flush=True)
            continue
        n += 1
        if n % 100 == 0:
            out_p.write_bytes(pickle.dumps(out))
            print(f"  {n} utterances, {(time.time() - t0) / n:.2f} s each", flush=True)
    out_p.write_bytes(pickle.dumps(out))
    Path(str(out_p) + ".timing.json").write_text(json.dumps(tm))
    mean = lambda v: sum(v) / max(len(v), 1)
    print(f"base reproduces tree-early PDD on {tm['checked'] - tm['mismatch']} of {tm['checked']} checked utterances",
          flush=True)
    print("timing (ms per utterance): first 3 steps " + f"{mean(tm['first']):.1f}; last step "
          + ", ".join(f"{k} {mean(v):.1f}" for k, v in tm["last"].items()), flush=True)
    print(f"done: {n} utterances in {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0 if n else 1


if __name__ == "__main__":
    raise SystemExit(main())
