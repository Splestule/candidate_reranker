#!/usr/bin/env python3
"""Training audio for peer-conditioned denoising, disjoint from every utterance we evaluate on.

For each Open ASR Leaderboard set, one shard the evaluation does NOT take (campaign/config.py
spreads `take` of `n_shards` evenly; any other index is unseen by every run so far), built with
the campaign's own prep code (same filtering and selection order). Utterances whose cluster
(meeting, call, speaker) also occurs in that set's evaluation manifest are dropped, so no
training speaker or recording is a test speaker or recording where the data says which is which.
Plus one LibriSpeech train-clean-100 shard (its speakers are disjoint from test by design).

    PYTHONPATH=src:tools python3 tools/pcd_data.py --data /tmp/campaign_data --out /tmp/pcd_data
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="evaluation data dir (its manifests define what to avoid)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--per_set", type=int, default=700)
    ap.add_argument("--sets", default="ami,earnings22,voxpopuli,gigaspeech,spgispeech,common_voice,ls-train")
    a = ap.parse_args()

    from campaign import config as C
    from campaign import prep_data as P

    out = Path(a.out)
    raw, audio = out / "raw", out / "audio"
    rows_all, report = [], {}
    for s in a.sets.split(","):
        try:
            if s == "ls-train":
                f = P.hf_file(C.LS_REPO, "all/train.clean.100/0000.parquet", raw)
                rows, _ = P.build_parquet("ls-train", dict(lang="en", n_max=a.per_set, repo=C.LS_REPO), [f], audio)
                dropped, shard = 0, "train.clean.100/0000"
            else:
                spec = C.SETS[s]
                n, take = spec["n_shards"], spec["take"]
                used = {min(n - 1, int((i + 0.5) * n / take)) for i in range(take)}
                free = [i for i in range(n) if i not in used]
                shard = free[len(free) // 2]
                f = P.hf_file(C.ESB_REPO, f"{spec['config']}/test-{shard:05d}-of-{n:05d}.parquet", raw)
                rows, _ = P.build_parquet(s, dict(spec, n_max=a.per_set * 2), [f], audio)
                f.unlink(missing_ok=True)
                ev = Path(a.data) / "manifests" / f"{s}.jsonl"
                eval_ids, eval_clusters = set(), set()
                if ev.exists():
                    for line in open(ev):
                        r = json.loads(line)
                        eval_ids.add(r["id"])
                        eval_clusters.add(r.get("cluster"))
                keep = [r for r in rows if r["id"] not in eval_ids and
                        (r["cluster"] == r["id"] or r["cluster"] not in eval_clusters)]
                dropped = len(rows) - len(keep)
                rows = keep[:a.per_set]
            for r in rows:
                r["set"] = s
            rows_all += rows
            report[s] = dict(shard=shard, kept=len(rows), dropped_overlap=dropped)
            print(f"[pcd_data] {s}: shard {shard}, {len(rows)} utterances, {dropped} dropped for "
                  f"sharing a cluster with the evaluation", flush=True)
        except Exception as e:                 # a missing set costs data, not the run
            report[s] = dict(error=f"{type(e).__name__}: {e}")
            print(f"[pcd_data] {s} FAILED: {type(e).__name__}: {e}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "train.jsonl", "w") as fh:
        for r in rows_all:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out / "train.meta.json").write_text(json.dumps(report, indent=2))
    print(f"[pcd_data] {len(rows_all)} training utterances on {sum('kept' in v for v in report.values())} sets")
    return 0 if rows_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
