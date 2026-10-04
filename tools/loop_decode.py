#!/usr/bin/env python3
"""Tree-early decoding with a snapshot before the last step: two arms from one decode.

Every PDD step fills all masked positions, so after any step each row is a complete sentence.
One tree-early decode (branch schedule [1, 2, 8, 8], 4 steps) gives

  tree-k8   the 8 rows after all four steps, the tree-early control (1 + 2 + 8 + 8 = 19
            decoder sequence passes)
  loop-k8   the same 8 rows as they stood after step 3 (1 + 2 + 8 = 11 passes): the input of
            in-loop composition, where the last step is spent on the candidates' consensus
            instead of on 8 independent rows (tools/refine.py --mode joint, one more pass)

Records are written in tools/cand_audio.py's format (normalised words, word confidences from
the logits of the step that produced them, the step-zero acoustic reading per word), for the
same utterances and shards as the arms already in --like, so everything downstream
(refine.py, refine_eval.py) reads them unchanged.

    PYTHONPATH=src:Whisfusion/src:tools python3 tools/loop_decode.py --like results/cand_audio.pkl \\
        --data /tmp/campaign_data --out results/refine/loop_cand.pkl
"""

from __future__ import annotations

import argparse
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
    ap.add_argument("--like", required=True, help="cand_audio.pkl whose utterances to decode")
    ap.add_argument("--like_arm", default="anchor-k8")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--branch", default="1,2,8,8")
    ap.add_argument("--snapshot_step", type=int, default=2)
    ap.add_argument("--sets", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--window", type=int, default=2)
    ap.add_argument("--time_check", type=int, default=300,
                    help="on the first N utterances also time flat K and the tree up to the snapshot "
                         "on their own, so every arm's decode cost is measured, not inferred")
    a = ap.parse_args()

    import data as dataio
    import decode as dec
    import wf_model
    from audio_slots import acoustic_reading, word_scores
    from campaign.families import Whisfusion
    from scorers import normalize

    sets = {x for x in a.sets.split(",") if x}
    like = [r for r in pickle.loads(Path(a.like).read_bytes())
            if r["arm"] == a.like_arm and (not sets or r["set"] in sets)]
    if a.limit:
        like = like[:a.limit]
    branch = [int(x) for x in a.branch.split(",")]
    tag = f"k{a.k}"
    out_p = Path(a.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out = pickle.loads(out_p.read_bytes()) if out_p.exists() else []
    seen = {(r["set"], r["id"]) for r in out}
    audio = {}
    for s in sorted({r["set"] for r in like}):
        audio[s] = {u.id: u.audio_path for u in dataio.iter_manifest(str(Path(a.data) / "manifests" / f"{s}.jsonl"))}
    wf = Whisfusion({}).wf
    print(f"{len(like)} utterances, branch {branch}, snapshot after step {a.snapshot_step}; {len(seen)} done",
          flush=True)

    def record(src, cands, arm, lp):
        rows = []
        for c in cands:
            words = normalize(c.text).split()
            wc = c.word_conf
            sc = word_scores(wf, lp, c.text, a.window) if words else None
            ok = (words and wc is not None and len(wc) == len(words)
                  and sc is not None and len(sc) == len(words))
            rows.append(dict(words=words, avg_conf=c.avg_conf, conf=list(wc) if ok else None,
                             aud=[math.exp(x) for x in sc] if ok else None, source="anchor"))
        return dict(set=src["set"], id=src["id"], cluster=src.get("cluster"), lang=src.get("lang", "en"),
                    ref=src["ref"], ref_text=src.get("ref_text"), shard=src.get("shard"), arm=arm, cands=rows)

    import json
    import torch

    def timed(fn):
        if wf.device == "cuda":
            torch.cuda.synchronize()
        t1 = time.perf_counter()
        r_ = fn()
        if wf.device == "cuda":
            torch.cuda.synchronize()
        return r_, 1000 * (time.perf_counter() - t1)

    tm = {"tree": [], "encode": [], "acoustic": [], "flat": [], "loop_only": [], "tree_plain": [],
          "passes": {"tree": sum(branch), "loop_only": sum(branch[:a.snapshot_step + 1]), "flat": a.k * len(branch)}}
    warm = next((x for x in like if x["id"] in audio.get(x["set"], {})), None)
    if warm is not None:                 # first CUDA calls are slow; keep them out of the timings
        c0 = wf_model.encode_audio(wf, dataio.load_audio(audio[warm["set"]][warm["id"]]))
        for _ in range(2):
            dec.pdd_decode(wf, c0, n_candidates=a.k, n_steps=len(branch), branch_schedule=branch, seed=0)
            dec.pdd_decode(wf, c0, n_candidates=a.k, n_steps=len(branch), seed=0)
    t0, n, fails = time.time(), 0, 0
    for src in like:
        if (src["set"], src["id"]) in seen or src["id"] not in audio.get(src["set"], {}):
            continue
        try:
            wav = dataio.load_audio(audio[src["set"]][src["id"]])
            cond, ms_enc = timed(lambda: wf_model.encode_audio(wf, wav))
            seed = zlib.crc32(f"{src['set']}/{src['id']}".encode()) % (2 ** 31)
            r, ms = timed(lambda: dec.pdd_decode(wf, cond, n_candidates=a.k, n_steps=len(branch),
                                                 branch_schedule=branch, seed=seed,
                                                 snapshot_step=a.snapshot_step))
            lp, ms_ac = timed(lambda: acoustic_reading(wf, cond, 256))
            tm["tree"].append(ms)
            tm["encode"].append(ms_enc)
            tm["acoustic"].append(ms_ac)
            if len(tm["flat"]) < a.time_check:
                # the snapshot builds extra candidate records: analysis, not decoding, so the tree's
                # cost is timed again without it
                tm["tree_plain"].append(timed(lambda: dec.pdd_decode(wf, cond, n_candidates=a.k, n_steps=len(branch),
                                                                     branch_schedule=branch, seed=seed))[1])
                tm["flat"].append(timed(lambda: dec.pdd_decode(wf, cond, n_candidates=a.k, n_steps=len(branch),
                                                               seed=seed))[1])
                tm["loop_only"].append(timed(lambda: dec.pdd_decode(
                    wf, cond, n_candidates=a.k, n_steps=a.snapshot_step + 1,
                    branch_schedule=branch[:a.snapshot_step + 1], seed=seed))[1])
            out.append(record(src, r.candidates, f"tree-{tag}", lp))
            out.append(record(src, r.snapshot, f"loop-{tag}", lp))
        except Exception as e:          # one bad utterance must not end the run
            fails += 1
            print(f"  !! {src['set']}/{src['id']}: {type(e).__name__}: {e}", flush=True)
            if fails > 50:
                raise
            continue
        n += 1
        if n % 100 == 0:
            out_p.write_bytes(pickle.dumps(out))
            print(f"  {n} utterances, {(time.time() - t0) / n:.2f} s each", flush=True)
    out_p.write_bytes(pickle.dumps(out))
    Path(str(out_p) + ".timing.json").write_text(json.dumps(tm))

    def mean(v):
        return sum(v) / max(len(v), 1)
    print(f"timing (ms per utterance): encoder {mean(tm['encode']):.1f}, step-zero acoustic reading "
          f"{mean(tm['acoustic']):.1f}, tree-early {mean(tm['tree']):.1f} ({tm['passes']['tree']} passes); on "
          f"{len(tm['flat'])} utterances flat K={a.k} {mean(tm['flat']):.1f} ({tm['passes']['flat']} passes), "
          f"tree-early without snapshot {mean(tm['tree_plain']):.1f}, "
          f"tree up to the snapshot {mean(tm['loop_only']):.1f} ({tm['passes']['loop_only']} passes)", flush=True)
    print(f"done: {n} utterances in {(time.time() - t0) / 60:.1f} min, {fails} failed", flush=True)
    return 0 if n or seen else 1


if __name__ == "__main__":
    raise SystemExit(main())
