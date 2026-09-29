#!/usr/bin/env python3
"""Is the composition gap a few decisive segment choices, or hundreds of word decisions?

This is the question that picks the next direction. The composition oracle is allowed to
change its mind at every slot; a system that had to be built would much rather change its
mind a handful of times per utterance. If most of the 9.35 WER survives a budget of two or
three candidate switches, the learnable object is a SEGMENT chooser -- "take candidate 7 up
to here, candidate 3 after" -- which is a far smaller and better-posed problem than picking
a word in every slot, and one where a sequence model has something to hold on to. If the gap
collapses the moment switches are limited, then it really is spread over many independent
word decisions, and the slot-ceiling result says those are not learnable.

Construction: align every candidate to the backbone exactly as compose.confusion_network
does, but keep WHICH candidate contributed each word instead of only the vote counts. A slot
where a candidate inserted several words becomes that many micro-slots, so a multi-word
insertion is attributed to one candidate and cannot be split for free.

The oracle is then a DP over (reference position, candidate in use, switches spent). A
budget of zero is exactly the n-best oracle; an unlimited budget is the composition oracle.
Everything in between is new.

    PYTHONPATH=src python3 tools/switch_oracle.py --model whisfusion --k 32 --max_utts 100
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

import numpy as np
from rapidfuzz.distance import Levenshtein

import campaign.analysis as A
import compose

EPS = compose.EPS
INF = 1e9


def slot_matrix(cands: list[list[str]], backbone: int) -> list[list[str]]:
    """One row per micro-slot, one column per candidate: the word that candidate puts there.

    Same alignment as compose.confusion_network -- substitutions land on the backbone
    position, insertions collect at the gap before it -- so the slot sequence matches the
    network ROVER votes over, and the two oracles are computed on the same object.
    """
    bb = cands[backbone]
    n = len(bb)
    K = len(cands)
    sub = [[EPS] * K for _ in range(n)]
    ins: list[list[list[str]]] = [[[] for _ in range(K)] for _ in range(n + 1)]

    for ci, c in enumerate(cands):
        for tag, i1, i2, j1, j2 in Levenshtein.opcodes(bb, c):
            if tag == "equal":
                for d in range(i2 - i1):
                    sub[i1 + d][ci] = c[j1 + d]
            elif tag == "replace":
                for pos in range(i1, i2):
                    off = j1 + (pos - i1)
                    sub[pos][ci] = c[off] if off < j2 else EPS
                for off in range(j1 + (i2 - i1), j2):
                    ins[i2][ci].append(c[off])
            elif tag == "delete":
                for pos in range(i1, i2):
                    sub[pos][ci] = EPS
            elif tag == "insert":
                for off in range(j1, j2):
                    ins[i1][ci].append(c[off])

    rows: list[list[str]] = []

    def push_ins(i):
        width = max((len(x) for x in ins[i]), default=0)
        for m in range(width):
            rows.append([(ins[i][c][m] if m < len(ins[i][c]) else EPS) for c in range(K)])

    for i in range(n):
        push_ins(i)
        rows.append(sub[i])
    push_ins(n)
    return rows


def switch_oracle(rows: list[list[str]], ref: list[str], budgets: list[int]) -> dict[int, int]:
    """Fewest edits reachable with at most S candidate switches, for each S in budgets.

    dp[s, c, j] = best cost having spent s switches, currently taking from candidate c, with
    j reference words consumed. Staying on c is free; moving to any other candidate costs one
    switch, which is why only the per-s minimum over candidates has to be carried forward.
    """
    if not rows:
        return {s: len(ref) for s in budgets}
    K = len(rows[0])
    R = len(ref)
    S = max(budgets)
    dp = np.full((S + 1, K, R + 1), INF)
    dp[0, :, 0] = 0.0                                  # any candidate may start a path

    ref_arr = np.asarray(ref, dtype=object)
    for row in rows:
        prev_min = dp.min(axis=1)                      # (S+1, R+1)
        nxt = np.full_like(dp, INF)
        for c in range(K):
            src = dp[:, c, :].copy()
            if S:
                src[1:] = np.minimum(src[1:], prev_min[:-1])
            w = row[c]
            if w == EPS:
                out = src
            else:
                out = src + 1.0                        # keep the word, consume no reference
                if R:
                    cost = np.where(ref_arr == w, 0.0, 1.0)
                    out[:, 1:] = np.minimum(out[:, 1:], src[:, :-1] + cost)
            nxt[:, c, :] = out
        for j in range(R):                             # a reference word skipped entirely
            nxt[:, :, j + 1] = np.minimum(nxt[:, :, j + 1], nxt[:, :, j] + 1.0)
        dp = nxt

    best = dp[:, :, R].min(axis=1)                     # (S+1,), per exact switch count
    run = np.minimum.accumulate(best)                  # at MOST s switches
    return {s: int(round(float(run[min(s, S)]))) for s in budgets}


def best_stitch(rows, slots, K, total, alpha, eps, max_switch=1):
    """The highest-scoring stitching under ROVER's own slot score, with at most one switch.

    No oracle, no training: score every word by exactly what ROVER scores it by, and ask
    which contiguous two-segment stitching maximises the sum. With prefix sums over the
    per-candidate scores this is O(slots * K^2) with a tiny constant -- about thirty
    thousand options for K=32, all of them enumerated, still microseconds.

    It is the cheapest possible test of the segment hypothesis: if even this beats ROVER,
    then choosing WHERE to switch is worth more than choosing better inside each slot, and a
    learned segment chooser is the thing to build.
    """
    T = len(rows)
    sc = np.zeros((T, K))
    for t, (row, slot) in enumerate(zip(rows, slots)):
        for c in range(K):
            w = row[c]
            votes, csum = slot.get(w, (0.0, 0.0))
            freq = votes / total if total else 0.0
            conf = eps if w == EPS else (csum / votes if votes > 0 else 0.0)
            v = alpha * freq + (1.0 - alpha) * conf
            # Along a path, a raw slot score is not comparable between slots: epsilon carries
            # the constant eps_conf, which beats most real words, so the highest-scoring
            # stitching is the empty one. Scoring each word against its own slot's best
            # removes the per-slot offset and leaves "what this choice gives up".
            sc[t, c] = np.log(max(v, 1e-6))
    sc -= sc.max(axis=1, keepdims=True)
    pre = np.vstack([np.zeros(K), np.cumsum(sc, axis=0)])        # (T+1, K)
    tot = pre[T]
    best, arg = -INF, (0, 0, 0)
    for t in range(T + 1):
        head = pre[t]                                            # candidate c1 up to t
        tail = tot - pre[t]                                      # candidate c2 from t
        i = int(np.argmax(head)); j = int(np.argmax(tail))
        v = head[i] + tail[j]
        if v > best:
            best, arg = v, (t, i, j)
    t, i, j = arg
    out = [rows[x][i] for x in range(t)] + [rows[x][j] for x in range(t, T)]
    return [w for w in out if w != EPS], (i != j)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/campaign-2026-09-20/dumps")
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max_utts", type=int, default=100, help="per set")
    ap.add_argument("--budgets", default="0,1,2,3,4,6,8,12,20")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    budgets = [int(x) for x in a.budgets.split(",") if x.strip()]
    dirs = sorted(glob.glob(f"{a.root}/{a.model}__*"))
    per: dict[str, list] = {}
    for d in dirs:
        s = Path(d).name.split("__")[1]
        rows = per.setdefault(s, [])
        for f in sorted(glob.glob(f"{d}/{a.arm}.jsonl.gz")):
            if len(rows) >= a.max_utts:
                break
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    rows.append(json.loads(line))
                    if len(rows) >= a.max_utts:
                        break
    per = {k: v for k, v in per.items() if v}
    if not per:
        print(f"no {a.arm}.jsonl.gz under {a.root} for {a.model}")
        return 2

    tot = dict(R=0, rover=0, comp=0, n=0, switches=0.0, slots=0, stitch=0, moved=0)
    bud = {s: 0 for s in budgets}
    for s in sorted(per):
        for row in per[s]:
            ref = A.S.normalize(row["reference"]).split()
            cands, confs, _ = A.prepare(row)
            k = min(a.k, len(cands))
            if k < 2 or not ref:
                continue
            sub, sub_c = cands[:k], (confs[:k] if confs else None)
            lens = [len(c) for c in sub]
            Lm = [[Levenshtein.distance(sub[i], sub[j]) for j in range(k)] for i in range(k)]
            mbr = [-sum(Lm[i][j] / max(lens[j], 1) for j in range(k) if j != i) / (k - 1)
                   for i in range(k)]
            p = max(range(k), key=lambda i: mbr[i])
            slots = compose.confusion_network(sub, p, sub_c, None)
            rows_m = slot_matrix(sub, p)
            res = switch_oracle(rows_m, ref, budgets)
            tot["R"] += len(ref)
            tot["n"] += 1
            tot["slots"] += len(rows_m)
            tot["rover"] += Levenshtein.distance(
                ref, compose.rover(slots, float(k), A.ROVER_DEFAULT["alpha"],
                                   A.ROVER_DEFAULT["eps"]))
            tot["comp"] += min(compose.oracle_path(slots, ref), min(res.values()))
            h, moved = best_stitch(rows_m, slots, k, float(k),
                                   A.ROVER_DEFAULT["alpha"], A.ROVER_DEFAULT["eps"])
            tot["stitch"] += Levenshtein.distance(ref, h)
            tot["moved"] += moved
            for b in budgets:
                bud[b] += res[b]

    R = tot["R"]
    rov = 100.0 * tot["rover"] / R
    comp = 100.0 * tot["comp"] / R
    gap = rov - comp
    print(f"{a.model} / {a.arm}, k={a.k}: {tot['n']} utterances, {R} reference words, "
          f"{tot['slots'] / max(tot['n'], 1):.1f} slots per utterance\n")
    print(f"  ROVER as shipped            {rov:>7.2f}")
    st = 100.0 * tot["stitch"] / R
    print(f"  composition oracle          {comp:>7.2f}   (gap {gap:.2f})")
    print(f"  best 1-switch stitching     {st:>7.2f}   ({rov - st:+.2f} against ROVER, "
          f"no oracle, no training; it moved on {100.0 * tot['moved'] / max(tot['n'], 1):.0f}% "
          f"of utterances)\n")
    print(f"{'switch budget':<16}{'oracle WER':>12}{'gap closed':>12}{'% of gap':>10}")
    print("-" * 50)
    for b in budgets:
        w = 100.0 * bud[b] / R
        print(f"{('0 = n-best' if b == 0 else str(b)):<16}{w:>12.2f}{rov - w:>12.2f}"
              f"{100.0 * (rov - w) / max(gap, 1e-9):>9.0f}%")
    print("-" * 50)
    print("A budget of S stitches the transcript from S+1 contiguous candidate segments.")
    print("Read where the curve flattens: that is how many decisions a segment-level model")
    print("would actually have to get right.")
    if a.json:
        f = Path(a.json)
        got = json.loads(f.read_text()) if f.exists() else []
        got = [r for r in got if (r["model"], r["arm"], r["k"]) != (a.model, a.arm, a.k)]
        got.append(dict(model=a.model, arm=a.arm, k=a.k, n=tot["n"], rover=rov, comp=comp,
                        budgets={str(b): 100.0 * bud[b] / R for b in budgets}))
        f.write_text(json.dumps(got, indent=1))
        print(f"\n-> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
