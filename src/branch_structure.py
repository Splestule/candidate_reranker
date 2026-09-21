#!/usr/bin/env python3
"""Do the candidates split into stable families, or does every slot disagree on its own?

ROVER counts every candidate as one independent vote. If the decoder really branches, the
same candidates should disagree together: the split at one slot would predict the split at
another, and a vote would be worth less than it looks. Cluster weighting tried to recover
that from surface similarity and bought nothing, which is either because the dependence is
not there or because similarity is a poor proxy for it. This measures it directly.

Each slot with disagreement partitions the candidates by the word they put there. The
agreement between two such partitions is the adjusted Rand index, which is zero in
expectation for independent partitions. The null shuffles each slot's labels among
candidates on its own, destroying any across-slot structure while keeping every slot's
shape, so the comparison isolates dependence rather than partition skew.

    PYTHONPATH=src python -m branch_structure <dump.jsonl.gz> [--n_utts 200]
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import statistics
from itertools import combinations

import compose
import decompose
from compose import EPS


def _pairs(counts: dict) -> float:
    return sum(n * (n - 1) / 2 for n in counts.values())


def adjusted_rand(a: list, b: list) -> float | None:
    """Chance-corrected agreement between two labellings of the same items."""
    n = len(a)
    if n < 3:
        return None
    joint, ca, cb = {}, {}, {}
    for x, y in zip(a, b):
        joint[(x, y)] = joint.get((x, y), 0) + 1
        ca[x] = ca.get(x, 0) + 1
        cb[y] = cb.get(y, 0) + 1
    if len(ca) < 2 or len(cb) < 2:          # a slot everyone agrees on carries no partition
        return None
    sij, sa, sb = _pairs(joint), _pairs(ca), _pairs(cb)
    exp = sa * sb / (n * (n - 1) / 2)
    denom = 0.5 * (sa + sb) - exp
    return (sij - exp) / denom if denom else None


def slot_labels(cands: list[list[str]], backbone: int) -> list[list[str]]:
    """What each candidate puts in each slot, one row per slot."""
    per_cand = [decompose.reference_by_slot(cands, backbone, c) for c in cands]
    n_slots = len(compose.confusion_network(cands, backbone, None, None))
    if any(len(p) != n_slots for p in per_cand):
        return []
    return [[p[s] for p in per_cand] for s in range(n_slots)]


def utterance(cands: list[list[str]], rng: random.Random, max_pairs: int = 400) -> tuple:
    rows = slot_labels(cands, compose.central_index(cands))
    live = [r for r in rows if len(set(r)) > 1]
    if len(live) < 2:
        return [], []
    pairs = list(combinations(range(len(live)), 2))
    if len(pairs) > max_pairs:
        pairs = rng.sample(pairs, max_pairs)

    obs = [v for i, j in pairs if (v := adjusted_rand(live[i], live[j])) is not None]
    shuf = [list(r) for r in live]
    for r in shuf:
        rng.shuffle(r)
    null = [v for i, j in pairs if (v := adjusted_rand(shuf[i], shuf[j])) is not None]
    return obs, null


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--n_utts", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    obs, null, n_used = [], [], 0
    with gzip.open(args.dump, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= args.n_utts:
                break
            row = json.loads(line)
            cands, _ = compose.prepare(row)
            if len(cands) < 3:
                continue
            o, z = utterance(cands, rng)
            if o:
                obs += o
                null += z
                n_used += 1

    if not obs:
        print(f"{args.dump}: no utterance had two disagreeing slots")
        return 0
    mo, mz = statistics.fmean(obs), statistics.fmean(null)
    print(f"{args.dump.split('/')[-2]:<42}{args.dump.split('/')[-1]:<14}"
          f"utts {n_used:>4}  pairs {len(obs):>7}  ARI {mo:>+7.4f}  null {mz:>+7.4f}  "
          f"rozdil {mo - mz:>+7.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
