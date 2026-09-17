#!/usr/bin/env python3
"""Spend a fixed candidate budget unevenly across utterances.

Candidates in a dump are exchangeable draws, so taking the first k of them is a faithful
simulation of having decoded only k. That makes every allocation policy measurable on an
existing dump at no decoding cost, as long as the mean k is held to the same budget.

Policies may only use what is knowable before decoding the rest: duration, and the length
and confidence of the first candidate.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from rapidfuzz.distance import Levenshtein

import bootstrap
import compose
import scorers as S


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def scores(rows: list[dict], policy: str) -> list[float]:
    out = []
    for r in rows:
        first = r["candidates"][0]
        n_words = max(len(S.normalize(first["text"]).split()), 1)
        unconf = max(1.0 - float(first["avg_conf"]), 1e-3)
        out.append({
            "const": 1.0,
            "duration": max(float(r.get("duration_s", 1.0)), 0.1),
            "words": float(n_words),
            "unconf": unconf,
            "words_unconf": n_words * unconf,
        }[policy])
    return out


def allocate(s: list[float], budget: float, k_min: int, k_max: int) -> list[int]:
    """Scale the scores until the mean allocation hits the budget."""
    lo, hi = 1e-9, 1e9
    for _ in range(80):
        a = (lo + hi) / 2
        k = [min(max(int(round(a * x)), k_min), k_max) for x in s]
        if statistics.fmean(k) < budget:
            lo = a
        else:
            hi = a
    return [min(max(int(round(hi * x)), k_min), k_max) for x in s]


def rover_edits(rows: list[dict], ks: list[int], alpha: float, eps_conf: float):
    edits, ref_lens = [], []
    for r, k in zip(rows, ks):
        row = dict(r, candidates=r["candidates"][:k])
        ref = S.normalize(r["reference"]).split()
        cands, confs = compose.prepare(row)
        slots = compose.confusion_network(cands, compose.central_index(cands), confs)
        hyp = compose.rover(slots, float(len(cands)), alpha, eps_conf)
        edits.append(Levenshtein.distance(ref, hyp))
        ref_lens.append(len(ref))
    return edits, ref_lens


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--budget", type=float, default=15.0, help="mean candidates per utterance")
    ap.add_argument("--k_min", type=int, default=2)
    ap.add_argument("--k_max", type=int, default=30)
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--eps_conf", type=float, default=0.7)
    ap.add_argument("--n_boot", type=int, default=2000)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    rows = load(args.dump)
    K = min(len(r["candidates"]) for r in rows)
    if args.k_max > K:
        args.k_max = K
    print(f"{len(rows)} utterances, dump holds K = {K}, "
          f"budget {args.budget} mean candidates, k in [{args.k_min}, {args.k_max}]\n")

    policies = ["const", "duration", "words", "unconf", "words_unconf"]
    results = {}
    for p in policies:
        ks = allocate(scores(rows, p), args.budget, args.k_min, args.k_max)
        e, ref = rover_edits(rows, ks, args.alpha, args.eps_conf)
        results[p] = {"edits": e, "k": ks,
                      "wer": 100.0 * sum(e) / max(sum(ref), 1),
                      "mean_k": statistics.fmean(ks),
                      "min_k": min(ks), "max_k": max(ks)}
    ref_lens = ref

    print(f"{'policy':<16}{'corpus WER':>12}{'mean k':>9}{'k range':>12}")
    for p in policies:
        r = results[p]
        span = f"{r['min_k']}-{r['max_k']}"
        print(f"{p:<16}{r['wer']:>12.2f}{r['mean_k']:>9.2f}{span:>12}")

    print(f"\n{'-' * 62}\nPAIRED BOOTSTRAP against the flat budget\n{'-' * 62}")
    out = {"dump": args.dump, "budget": args.budget, "K": K,
           "policies": {p: {k: v for k, v in results[p].items() if k not in ("edits", "k")}
                        for p in policies}}
    for p in policies[1:]:
        s = bootstrap.paired_bootstrap(results["const"]["edits"], results[p]["edits"],
                                       ref_lens, n_boot=args.n_boot)
        out["policies"][p]["vs_const"] = s
        print(bootstrap.format_row(f"{p} over const", s))
        if s and s["ci_low"] <= 0 <= s["ci_high"]:
            print(f"{'':<34}interval spans zero: not distinguishable")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"\nwritten: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
