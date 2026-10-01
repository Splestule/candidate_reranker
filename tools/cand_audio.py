#!/usr/bin/env python3
"""Per-candidate word confidences and step-zero acoustic scores, kept per candidate.

tools/audio_slots.py folds the acoustic scores straight into the K=32 network, so a network
over any other K cannot be rebuilt from its cache. This keeps them per candidate (in the
dump's order), which is what tools/k_curve.py needs to build the network for K = 1..32.

    PYTHONPATH=src:Whisfusion/src:tools python3 tools/cand_audio.py --data data \\
        --dumps_root results/campaign-2026-09-20/dumps --like results/audio_cache.pkl \\
        --out results/cand_audio.pkl
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import pickle
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--dumps_root", required=True)
    ap.add_argument("--like", default="", help="cache whose (set, id) pairs to cover")
    ap.add_argument("--sets", default="", help="without --like: these sets, --per_set each")
    ap.add_argument("--per_set", type=int, default=400)
    ap.add_argument("--arm", default="main", help="comma separated; one step-zero pass serves all")
    ap.add_argument("--pattern", default="whisfusion__{set}__s*__{arm}/{arm}.jsonl.gz",
                    help="dump path under --dumps_root; {set} and {arm} are filled in")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--window", type=int, default=2)
    ap.add_argument("--seq_len", type=int, default=256)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import data as dataio
    import wf_model
    from audio_slots import acoustic_reading, word_scores
    from campaign.families import Whisfusion
    from scorers import normalize

    want = {}
    if a.like:
        for d in pickle.loads(Path(a.like).read_bytes()):
            want.setdefault(d["set"], set()).add(d["id"])
    else:
        want = {s: None for s in a.sets.split(",") if s}
    arms = [x for x in a.arm.split(",") if x]
    out_p = Path(a.out)
    out = pickle.loads(out_p.read_bytes()) if out_p.exists() else []
    seen = {(r["set"], r["id"], r.get("arm", arms[0])) for r in out}
    wf = Whisfusion({}).wf
    t0, n = time.time(), 0
    for s, ids in sorted(want.items()):
        rows = {arm: {} for arm in arms}          # arm -> id -> dump row
        for arm in arms:
            for p in sorted(Path(a.dumps_root).glob(a.pattern.format(set=s, arm=arm))):
                opener = gzip.open if p.suffix == ".gz" else open
                with opener(p, "rt", encoding="utf-8") as fh:
                    m = re.search(r"__s(\d+)__", str(p))
                    for line in fh:
                        r = json.loads(line)
                        if ids is None or r["id"] in ids:
                            r["_shard"] = int(m.group(1)) if m else None
                            rows[arm][r["id"]] = r
        order = [u for u in rows[arms[0]] if all(u in rows[x] for x in arms)]
        if ids is None:
            order = order[: a.per_set]
        audio = {u.id: u.audio_path for u in dataio.iter_manifest(str(Path(a.data) / "manifests" / f"{s}.jsonl"))}
        for uid in order:
            todo = [arm for arm in arms if (s, uid, arm) not in seen]
            if not todo or uid not in audio:
                continue
            # the step-zero reading depends on the audio only, so one pass serves every arm
            cond = wf_model.encode_audio(wf, dataio.load_audio(audio[uid]))
            lp = acoustic_reading(wf, cond, a.seq_len)
            for arm in todo:
                row = rows[arm][uid]
                cands = []
                for c in row["candidates"][: a.k]:
                    words = normalize(c["text"]).split()
                    wc = c.get("word_conf")
                    sc = word_scores(wf, lp, c["text"], a.window) if words else None
                    ok = (words and wc is not None and len(wc) == len(words)
                          and sc is not None and len(sc) == len(words))
                    cands.append(dict(words=words, avg_conf=c["avg_conf"], conf=list(wc) if ok else None,
                                      aud=[math.exp(x) for x in sc] if ok else None))
                out.append(dict(set=s, id=uid, cluster=row.get("cluster") or uid,
                                lang=row.get("lang", "en"), ref=normalize(row["reference"]).split(),
                                ref_text=row["reference"], decode_s=row.get("decode_s"),
                                encode_s=row.get("encode_s"), shard=row.get("_shard"), arm=arm,
                                cands=cands))
            n += 1
            if n % 100 == 0:
                out_p.write_bytes(pickle.dumps(out))
            if n in (1, 10) or n % 50 == 0:
                print(f"  {n} utterances ({len(out)} records), {(time.time() - t0) / n:.1f} s each",
                      flush=True)
    out_p.write_bytes(pickle.dumps(out))
    print(f"done: {len(out)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
