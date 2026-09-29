#!/usr/bin/env python3
"""A / R decomposition on finished dumps, with the voting parameters we actually ship.

Splits ROVER's slot accuracy into the two things that can go wrong:

    A  availability    the reference word is an option in its slot at all
    R  recoverability  the vote picks it, given that it is there

A*R is ROVER's slot accuracy, B is the backbone's (i.e. selection's). The point of the
split is that A is a property of the candidates and R is a property of the decision rule,
so it says whether a configuration fails because the words are missing or because the vote
cannot find them. Unlike src/decompose.py's own default this passes the per-word
confidences and the shipped alpha/eps, so the R reported here is the R of the real system.

    PYTHONPATH=src python tools/ar_report.py results/campaign-2026-09-20 --model whisfusion
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import sys
from pathlib import Path

ALPHA, EPS_CONF = 0.5, 0.7          # campaign.analysis.ROVER_DEFAULT


def rows(path: str):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max_shards", type=int, default=3)
    ap.add_argument("--max_utts", type=int, default=250)
    args = ap.parse_args()

    sys.path.insert(0, str(Path(args.root).resolve().parent.parent / "src"))
    sys.path.insert(0, "src")
    import compose
    import decompose as D
    from scorers import normalize

    jobs = sorted(glob.glob(f"{args.root}/dumps/{args.model}__*"))
    by_set: dict[str, list[str]] = {}
    for j in jobs:
        name = Path(j).name
        parts = name.split("__")
        if len(parts) < 4 or parts[3] != args.arm:
            continue
        by_set.setdefault(parts[1], []).append(j)

    print(f"{'set':<18}{'utts':>6}{'slots':>8}{'A':>8}{'R':>8}{'A*R':>8}{'B':>8}"
          f"{'rescue':>8}{'damage':>8}")
    print("-" * 82)
    grand = []
    for s, js in sorted(by_set.items()):
        per = []
        for j in js[: args.max_shards]:
            p = Path(j) / f"{args.arm}.jsonl.gz"
            if not p.exists():
                continue
            for row in rows(str(p)):
                cands = [normalize(c["text"]).split() for c in row["candidates"]][: args.k]
                if len(cands) < 2:
                    continue
                confs = None
                if all("word_conf" in c for c in row["candidates"][: args.k]):
                    cc = [c["word_conf"] for c in row["candidates"][: args.k]]
                    if all(len(w) == len(t) for w, t in zip(cc, cands)):
                        confs = cc
                ref = normalize(row["reference"]).split()
                if not ref:
                    continue
                bb = compose.central_index(cands)
                slots = compose.confusion_network(cands, bb, confs, None)
                by_slot = D.reference_by_slot(cands, bb, ref)
                if len(by_slot) != len(slots):
                    continue
                picks = compose.rover_slot_picks(slots, float(len(cands)), ALPHA, EPS_CONF)
                bbs, ins = [], D._insertion_points(cands, cands[bb])
                for i, w in enumerate(cands[bb]):
                    if i in ins:
                        bbs.append(compose.EPS)
                    bbs.append(w)
                if len(cands[bb]) in ins:
                    bbs.append(compose.EPS)
                d = dict(n=0, avail=0, picked=0, base=0, damage=0, rescue=0)
                for sl, r, pk, b in zip(slots, by_slot, picks, bbs):
                    if r == compose.EPS:
                        continue
                    d["n"] += 1
                    d["avail"] += r in sl
                    d["picked"] += pk == r
                    d["base"] += b == r
                    d["damage"] += (b == r) and (pk != r)
                    d["rescue"] += (b != r) and (pk == r)
                per.append(d)
                if len(per) >= args.max_utts:
                    break
            if len(per) >= args.max_utts:
                break
        if not per:
            continue
        grand += per
        t = D.summarise(per)
        print(f"{s:<18}{t['n_utts']:>6}{t['n_slots']:>8}{t['A']:>8.1f}{t['R']:>8.1f}"
              f"{t['AR']:>8.1f}{t['B']:>8.1f}{t['rescue']:>8.1f}{t['damage']:>8.1f}")
    if grand:
        t = D.summarise(grand)
        print("-" * 82)
        print(f"{'ALL':<18}{t['n_utts']:>6}{t['n_slots']:>8}{t['A']:>8.1f}{t['R']:>8.1f}"
              f"{t['AR']:>8.1f}{t['B']:>8.1f}{t['rescue']:>8.1f}{t['damage']:>8.1f}")
        print(f"\nA = {t['A']:.1f} %  of reference words are somewhere in their slot")
        print(f"R = {t['R']:.1f} %  of those the vote actually picks")
        print(f"unavailable slots            {100 - t['A']:.1f} %   fixable only by changing the model")
        print(f"available but not picked     {t['A'] * (100 - t['R']) / 100:.1f} %   "
              f"fixable by a better decision rule, no retraining")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
