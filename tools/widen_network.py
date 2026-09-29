#!/usr/bin/env python3
"""Let a word be an option in neighbouring slots too, and see whether anything is gained.

The confusion network is a chain of slots, already fully connected between neighbours: any
word in slot i may be followed by any word in slot i+1. What is NOT free is which slot a
word landed in. compose.confusion_network aligns every candidate to one backbone, so if one
candidate put "leisure" at position 5 and another at 6, the backbone picks one and the other
placement is gone -- along with every path that needed it.

Widening here means exactly that and nothing more: each slot also offers the words of the
slots within `dist`, carried over with their votes scaled by `decay` because borrowed
evidence is weaker evidence. No word enters that no candidate proposed, so the property that
makes this different from LLM correction survives.

Reading the output, in this order and no other:

  oracle_comp WILL improve. More paths means more chances to match the reference by
  accident, so on its own that number means nothing at all.
  control is the same widening measured on a network whose alternatives were replaced by
  unrelated words. Whatever the control gains is what shape alone buys.
  signal/luck = (oracle_cand - oracle_comp) / (oracle_cand - control) is the read. If it
  falls while oracle_comp improves, the widening bought luck.
  ROVER is whether any decision rule we have can actually use the extra room.

    PYTHONPATH=src python tools/widen_network.py --cache results/calib_cache.pkl
"""

from __future__ import annotations

import argparse
import pickle
import random
import sys
from collections import defaultdict
from pathlib import Path

EPS = ""
DEV_SETS = ("ls-dev-clean", "ls-dev-other")
SHIPPED = dict(alpha=0.5, eps=0.7)


def widen(slots: list[dict], dist: int, decay: float) -> list[dict]:
    """Each slot also offers its neighbours' words, with votes scaled by decay ** offset."""
    if dist <= 0:
        return [dict(s) for s in slots]
    out = []
    for i, s in enumerate(slots):
        merged = {w: list(v) for w, v in s.items()}
        for off in range(1, dist + 1):
            for j in (i - off, i + off):
                if not (0 <= j < len(slots)):
                    continue
                f = decay ** off
                for w, v in slots[j].items():
                    if w == EPS:
                        continue                  # epsilon is already in every slot
                    if w in merged:
                        continue                  # never inflate a word already voted here
                    merged[w] = [v[0] * f, v[1] * f]
        merged.setdefault(EPS, [0.0, 0.0])
        out.append(merged)
    return out


def rover_pick(slot: dict, total: float, alpha: float, eps: float, power: float | None) -> str:
    best, bw = None, EPS
    for w, (votes, csum) in slot.items():
        freq = votes / total if total else 0.0
        if w == EPS:
            conf = eps
        else:
            conf = csum / votes if votes > 0 else 0.0
            if power is not None:
                conf = min(max(conf, 0.0), 1.0) ** power
        s = alpha * freq + (1.0 - alpha) * conf
        if best is None or s > best:
            best, bw = s, w
    return bw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="results/calib_cache.pkl")
    ap.add_argument("--power", type=float, default=11.95)
    ap.add_argument("--alpha", type=float, default=0.7)
    ap.add_argument("--eps", type=float, default=0.4)
    ap.add_argument("--max_utts", type=int, default=120, help="per set; oracle_path is the slow part")
    a = ap.parse_args()

    sys.path.insert(0, "src")
    import bootstrap
    import compose
    from rapidfuzz.distance import Levenshtein

    data = pickle.loads(Path(a.cache).read_bytes())
    by_set: dict[str, list] = defaultdict(list)
    for d in data:
        if len(by_set[d["set"]]) < a.max_utts:
            by_set[d["set"]].append(d)
    pool_of = {s: sorted({w for d in v for sl in d["slots"] for w in sl if w != EPS})
               for s, v in by_set.items()}

    # the widening must be a no-op at dist 0, or nothing below is about widening
    bad = 0
    for d in data[:200]:
        if widen(d["slots"], 0, 0.5) != [dict(s) for s in d["slots"]]:
            bad += 1
    print(f"identity check at dist=0: {200 - bad}/200 networks unchanged")
    if bad:
        print("widen() is not a no-op at dist 0; fix that first")
        return 1

    grid = [(0, 1.0), (1, 0.25), (1, 0.5), (1, 1.0), (2, 0.5)]
    print(f"\n{len(data)} utterances cached, scoring "
          f"{sum(len(v) for v in by_set.values())} (up to {a.max_utts} per set)\n")
    print(f"{'dist':>5}{'decay':>7}{'slot':>7}{'ROVER':>9}{'or.comp':>9}{'control':>9}"
          f"{'margin':>8}{'d ROVER':>9}{'d comp':>8}{'d ctrl':>8}{'d margin':>10}")
    print("-" * 91)

    per_utt, res = {}, {}
    for dist, decay in grid:
        ed_r = ed_cp = ed_ct = R = 0.0
        sizes = n_slots = 0
        rows = []
        for s, utts in sorted(by_set.items()):
            pool = pool_of[s]
            for d in utts:
                sl = widen(d["slots"], dist, decay)
                total = float(d["n_cand"])
                hyp = [rover_pick(x, total, a.alpha, a.eps, a.power) for x in sl]
                rows.append(Levenshtein.distance(d["ref"], [w for w in hyp if w != EPS]))
                ed_r += rows[-1]
                rng = random.Random(hash(d["id"]) & 0xFFFFFFFF)
                ed_cp += compose.oracle_path(sl, d["ref"])
                ed_ct += compose.oracle_path(compose.shuffled_control(sl, pool, rng), d["ref"])
                R += len(d["ref"])
                sizes += sum(len(x) for x in sl); n_slots += len(sl)
        w = lambda x: 100.0 * x / R
        cur = dict(rover=w(ed_r), comp=w(ed_cp), ctrl=w(ed_ct), slot=sizes / max(n_slots, 1))
        cur["margin"] = cur["ctrl"] - cur["comp"]      # how much the real words beat a fake net
        b = res.get((0, 1.0), cur)
        print(f"{dist:>5}{decay:>7.2f}{cur['slot']:>7.2f}{cur['rover']:>9.2f}"
              f"{cur['comp']:>9.2f}{cur['ctrl']:>9.2f}{cur['margin']:>8.2f}"
              f"{cur['rover'] - b['rover']:>+9.2f}{cur['comp'] - b['comp']:>+8.2f}"
              f"{cur['ctrl'] - b['ctrl']:>+8.2f}{cur['margin'] - b['margin']:>+10.2f}")
        res[(dist, decay)] = cur
        per_utt[(dist, decay)] = rows

    base = per_utt[(0, 1.0)]
    rl = [len(d["ref"]) for s, v in sorted(by_set.items()) for d in v]
    print("\nROVER against the unwidened network, paired bootstrap (positive = better)")
    for key in grid[1:]:
        st = bootstrap.paired_bootstrap(base, per_utt[key], rl, n_boot=4000)
        flag = "" if st["ci_low"] > 0 or st["ci_high"] < 0 else "   spans zero"
        print("  " + bootstrap.format_row(f"dist {key[0]}, decay {key[1]}", st) + flag)
    print("\nmargin = control - oracle_comp, i.e. how far the real words beat a same-shaped")
    print("fake network. d comp improving while d margin does not is luck, not information.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
