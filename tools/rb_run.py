#!/usr/bin/env python3
"""Decode with the per-word predictive distributions kept, for voting from distributions.

For every utterance: Whisfusion PDD at each arm with track_topk (tokens identical to a normal
decode), the step-zero acoustic scores per candidate (as tools/cand_audio.py), all in the
cand_audio record format plus `dist` per candidate: [first token id, top ids, top probs] per
word. Utterances come from the campaign manifests, shard = rows [200 s, 200 s + 200).

    PYTHONPATH=src:Whisfusion/src:tools python3 tools/rb_run.py --data /tmp/campaign_data \\
        --jobs ls-test-clean:1,ami:0 --out results/rb/cand_rb.pkl
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

ARMS = {"flat-k4": dict(K=4, steps=4), "flat-k8": dict(K=8, steps=4),
        "tree-early-k8": dict(K=8, steps=4, branch_schedule=[1, 2, 8, 8])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--jobs", required=True, help="set:shard,set:shard,...")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--shard_size", type=int, default=200)
    ap.add_argument("--limit", type=int, default=0, help="utterances per job (smoke test)")
    ap.add_argument("--topk", type=int, default=8)
    ap.add_argument("--window", type=int, default=2)
    ap.add_argument("--minutes", type=float, default=0, help="stop after this long (0 = no cap)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import data as dataio
    from audio_slots import acoustic_reading, word_scores
    from campaign.families import Whisfusion
    from scorers import normalize

    arms = a.arms.split(",")
    out_p = Path(a.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out = pickle.loads(out_p.read_bytes()) if out_p.exists() else []
    seen = {(r["set"], r["id"], r["arm"]) for r in out}
    fam = Whisfusion({})
    wf = fam.wf
    t0, n, dec_s = time.time(), 0, {x: 0.0 for x in arms}
    stop = t0 + 60 * a.minutes if a.minutes else float("inf")
    for job in a.jobs.split(","):
        s, shard = job.split(":")
        shard = int(shard)
        man = [json.loads(l) for l in open(Path(a.data) / "manifests" / f"{s}.jsonl", encoding="utf-8") if l.strip()]
        rows = man[shard * a.shard_size:(shard + 1) * a.shard_size]
        if a.limit:
            rows = rows[:a.limit]
        for row in rows:
            uid = str(row.get("id", Path(row["audio"]).stem))
            todo = [x for x in arms if (s, uid, x) not in seen]
            if not todo:
                continue
            if time.time() > stop:
                break
            te = time.time()
            enc = fam.encode(dataio.load_audio(row["audio"]), row.get("lang", "en"))
            enc_s = time.time() - te
            lp = acoustic_reading(wf, enc, 256)
            for arm in todo:
                seed = (zlib.crc32(f"{uid}|{arm}".encode()) & 0x7FFFFFFF)
                td = time.time()
                cands, _ = fam.decode(enc, dict(ARMS[arm], track_topk=a.topk), seed, "en")
                t_arm = time.time() - td
                dec_s[arm] += t_arm
                cs = []
                for c in cands:
                    words = normalize(c["text"]).split()
                    wc, wd = c.get("word_conf"), c.get("word_dist")
                    sc = word_scores(wf, lp, c["text"], a.window) if words else None
                    ok = (words and wc is not None and len(wc) == len(words)
                          and sc is not None and len(sc) == len(words))
                    cs.append(dict(words=words, avg_conf=c["avg_conf"], conf=list(wc) if ok else None,
                                   aud=[math.exp(x) for x in sc] if ok else None,
                                   dist=wd if (ok and wd is not None and len(wd) == len(words)) else None))
                out.append(dict(set=s, id=uid, cluster=row.get("cluster") or uid, lang=row.get("lang", "en"),
                                ref=normalize(row["text"]).split(), ref_text=row["text"], shard=shard, arm=arm,
                                encode_s=enc_s, decode_s=t_arm, cands=cs))
                seen.add((s, uid, arm))
            n += 1
            if n % 100 == 0:
                out_p.write_bytes(pickle.dumps(out))
            if n in (1, 10) or n % 100 == 0:
                print(f"  {job}: {n} utterances, {(time.time() - t0) / n:.2f} s each; decode s/utt "
                      + ", ".join(f"{x} {dec_s[x] / n:.3f}" for x in arms), flush=True)
        out_p.write_bytes(pickle.dumps(out))
        if time.time() > stop:
            print("time cap reached", flush=True)
            break
    out_p.write_bytes(pickle.dumps(out))
    ok = sum(c["dist"] is not None for r in out for c in r["cands"])
    tot = sum(len(r["cands"]) for r in out)
    print(f"done: {len(out)} records, word distributions on {ok}/{tot} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
