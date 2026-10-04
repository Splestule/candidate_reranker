#!/usr/bin/env python3
"""What peer conditioning does to the candidates themselves, before any combiner: mean candidate
WER, the best candidate (oracle), how much the K candidates still disagree, and how many are
distinct. Peer conditioning could improve candidates by pulling them together; if it does, the
combiner has less to work with, and this table shows it.

    python3 tools/pcd_report.py results/cand_audio.pkl results/pcd/dec_0.pkl results/pcd/dec_1.pkl
"""

from __future__ import annotations

import pickle
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

from rapidfuzz.distance import Levenshtein

import confirm_eval as CE


def main() -> int:
    recs = [r for p in sys.argv[1:] if Path(p).exists() for r in pickle.loads(Path(p).read_bytes())]
    by = defaultdict(dict)
    for r in recs:
        if r.get("shard") == 1 and r["set"] in CE.TEST_SETS and r["arm"].endswith("-k8"):
            by[r["arm"]][(r["set"], r["id"])] = r
    keys = set.intersection(*[set(v) for v in by.values()]) if by else set()
    print(f"{len(keys)} test utterances in every arm\n")
    print("| arm | mean candidate WER | candidate oracle | pairwise disagreement | distinct / 8 |")
    print("|---|---|---|---|---|")
    for arm in sorted(by):
        e = o = refw = 0.0
        dis = pairs = uniq = 0.0
        for k in keys:
            r = by[arm][k]
            c = [x["words"] for x in r["cands"][:8]]
            ed = [Levenshtein.distance(r["ref"], w) for w in c]
            e += sum(ed) / len(c)
            o += min(ed)
            refw += len(r["ref"])
            for a, b in combinations(c, 2):
                dis += Levenshtein.distance(a, b) / max(len(a), len(b), 1)
                pairs += 1
            uniq += len({" ".join(w) for w in c})
        print(f"| {arm} | {100 * e / refw:.2f} | {100 * o / refw:.2f} | {100 * dis / max(pairs, 1):.1f} % | "
              f"{uniq / max(len(keys), 1):.2f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
