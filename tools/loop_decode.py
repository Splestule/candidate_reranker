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

    t0, n, fails = time.time(), 0, 0
    for src in like:
        if (src["set"], src["id"]) in seen or src["id"] not in audio.get(src["set"], {}):
            continue
        try:
            cond = wf_model.encode_audio(wf, dataio.load_audio(audio[src["set"]][src["id"]]))
            seed = zlib.crc32(f"{src['set']}/{src['id']}".encode()) % (2 ** 31)
            r = dec.pdd_decode(wf, cond, n_candidates=a.k, n_steps=len(branch), branch_schedule=branch,
                               seed=seed, snapshot_step=a.snapshot_step)
            lp = acoustic_reading(wf, cond, 256)
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
    print(f"done: {n} utterances in {(time.time() - t0) / 60:.1f} min, {fails} failed", flush=True)
    return 0 if n or seen else 1


if __name__ == "__main__":
    raise SystemExit(main())
