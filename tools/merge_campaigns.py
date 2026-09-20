#!/usr/bin/env python3
"""Combine the output of several campaign sessions into one root, then aggregate it as a whole.

Sessions are paired by construction: a set's shard k holds the same utterances in every session,
because the order is a hash of the utterance id. So the per-utterance tables of two runs can
simply be pooled, and contrasts that cross sessions (Drax's standard decode from session 1
against its low-temperature pool from session 2) work like any other.

    python tools/merge_campaigns.py out/run1/campaign out/run2/campaign --out out/merged
    PYTHONPATH=src python -m campaign.aggregate --root out/merged
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--aggregate", action="store_true", help="run campaign.aggregate afterwards")
    args = ap.parse_args()

    out = Path(args.out)
    for sub in ("analysis", "state/done", "manifests", "dumps"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    plan: list[dict] = []
    seen_jobs: set[str] = set()
    counts = {}
    for i, r in enumerate(map(Path, args.roots)):
        tag = f"r{i + 1}"
        n_an = n_done = 0
        for p in (r / "analysis").glob("*.parquet"):
            # tags are unique per job x arm, and job ids repeat across sessions only if the
            # same job really was rerun; keep the newer file in that case
            shutil.copy(p, out / "analysis" / p.name)
            n_an += 1
        for p in (r / "state" / "done").glob("*.json"):
            shutil.copy(p, out / "state" / "done" / p.name)
            n_done += 1
        for p in (r / "manifests").glob("*"):
            if not (out / "manifests" / p.name).exists():
                shutil.copy(p, out / "manifests" / p.name)
        d = r / "dumps"
        if d.is_dir():
            for job_dir in d.iterdir():
                dst = out / "dumps" / job_dir.name
                if not dst.exists() and job_dir.is_dir():
                    shutil.copytree(job_dir, dst)
        pf = r / "plan.json"
        if pf.exists():
            for j in json.load(open(pf, encoding="utf-8")):
                if j["id"] not in seen_jobs:
                    seen_jobs.add(j["id"])
                    plan.append(j)
        cf = r / "run_config.json"
        if cf.exists() and not (out / "run_config.json").exists():
            shutil.copy(cf, out / "run_config.json")
        counts[tag] = dict(root=str(r), analysis=n_an, done=n_done)

    with open(out / "plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=1)
    with open(out / "merged_from.json", "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)
    print(json.dumps(counts, indent=2))
    print(f"merged plan: {len(plan)} jobs -> {out}")

    if args.aggregate:
        import subprocess
        import sys
        src = Path(__file__).resolve().parent.parent / "src"
        env = dict(**__import__("os").environ, PYTHONPATH=str(src))
        subprocess.run([sys.executable, "-m", "campaign.aggregate", "--root", str(out)], env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
