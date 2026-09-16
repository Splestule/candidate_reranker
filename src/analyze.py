#!/usr/bin/env python3
"""Oracle gap analysis over a candidate dump."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import scorers as S

BUCKETS = [(0, 10, "0-10s"), (10, 20, "10-20s"), (20, 30, "20-30s"), (30, 1e9, "30s+")]


def bucket_of(d: float) -> str:
    for lo, hi, name in BUCKETS:
        if lo <= d < hi:
            return name
    return "30s+"


def spearman(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n < 3:
        return None

    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return None if dx == 0 or dy == 0 else num / (dx * dy)


def pct(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * p
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--json", default=None)
    ap.add_argument("--min_gap", type=float, default=1.5)
    ap.add_argument("--min_coverage", type=float, default=20.0)
    args = ap.parse_args()

    rows = load(args.dump)
    if not rows:
        print("empty dump")
        return 1

    refs = [r["reference"] for r in rows]
    K = len(rows[0]["candidates"])
    rng = random.Random(0)

    all_wers = [[100.0 * S.wer_pair(r["reference"], c["text"]) for c in r["candidates"]]
                for r in rows]

    def pick_by(score_fn):
        out = []
        for r in rows:
            sc = score_fn(r["candidates"])
            out.append(max(range(len(sc)), key=lambda i: sc[i]))
        return out

    oracle_idx = [min(range(K), key=lambda j: w[j]) for w in all_wers]
    anti_idx = [max(range(K), key=lambda j: w[j]) for w in all_wers]
    rand_idx = [rng.randrange(K) for _ in rows]
    base_idx = pick_by(S.s_mean_conf)

    out: dict = {
        "dump": args.dump,
        "n_utts": len(rows),
        "k": K,
        "total_audio_min": sum(r["duration_s"] for r in rows) / 60.0,
        "identical_after_step1_frac":
            100.0 * sum(1 for r in rows if r.get("identical_after_step1")) / len(rows),
    }

    print("=" * 74)
    print(f"ORACLE GAP  ·  {args.dump}")
    print("=" * 74)
    print(f"utterances: {len(rows)}   K: {K}   audio: {out['total_audio_min']:.1f} min")
    print(f"identical candidates after step 1: {out['identical_after_step1_frac']:.1f} % of utts")

    print("\n" + "-" * 74)
    print(f"{'scorer':<28}{'corpus WER':>12}{'mean-utt':>11}{'hit %':>10}{'gap':>10}")
    print("-" * 74)

    scorer_stats = {}

    def line(name, idx):
        hyps = [rows[i]["candidates"][j]["text"] for i, j in enumerate(idx)]
        cw = S.corpus_wer(refs, hyps)
        mu = S.mean_utt_wer(refs, hyps)
        hit = 100.0 * sum(1 for i, j in enumerate(idx)
                          if all_wers[i][j] <= min(all_wers[i]) + 1e-9) / len(rows)
        gap = sum(all_wers[i][j] - min(all_wers[i]) for i, j in enumerate(idx)) / len(rows)
        scorer_stats[name] = {"corpus_wer": cw, "mean_utt_wer": mu,
                              "hit_rate": hit, "mean_gap": gap}
        print(f"{name:<28}{cw:>12.2f}{mu:>11.2f}{hit:>10.1f}{gap:>10.2f}")

    for name, fn in S.SCORERS.items():
        line(name, pick_by(fn))
    print("-" * 74)
    line("ORACLE (best of K)", oracle_idx)
    line("RANDOM", rand_idx)
    line("ANTI-ORACLE (worst)", anti_idx)
    print("-" * 74)
    print("corpus WER = total edits / total reference words")
    print("mean-utt   = mean of per-utterance WER, as upstream reports it;")
    print("             compare the paper's 8.3% against this column")

    out["scorers"] = scorer_stats
    base = scorer_stats["mean_conf (upstream)"]
    orac = scorer_stats["ORACLE (best of K)"]

    per_utt_gap = [all_wers[i][j] - min(all_wers[i]) for i, j in enumerate(base_idx)]
    coverage = 100.0 * sum(1 for g in per_utt_gap if g > 1e-9) / len(rows)
    flat = 100.0 * sum(1 for w in all_wers if max(w) - min(w) < 1e-9) / len(rows)

    print("\n" + "-" * 74)
    print("COVERAGE -- where there is anything to choose")
    print("-" * 74)
    print(f"utterances where the baseline missed the best candidate: {coverage:.1f} %")
    print(f"utterances where all candidates are equally good: {flat:.1f} %")
    print(f"gap (mean-utt): {base['mean_utt_wer'] - orac['mean_utt_wer']:.2f}   "
          f"gap (corpus): {base['corpus_wer'] - orac['corpus_wer']:.2f}")
    print(f"per-utterance gap  p50={pct(per_utt_gap,.5):.1f}  p90={pct(per_utt_gap,.9):.1f}  "
          f"p99={pct(per_utt_gap,.99):.1f}  max={max(per_utt_gap):.1f}")

    out["coverage_pct"] = coverage
    out["all_candidates_equal_pct"] = flat
    out["gap_corpus"] = base["corpus_wer"] - orac["corpus_wer"]
    out["gap_mean_utt"] = base["mean_utt_wer"] - orac["mean_utt_wer"]

    divs = [S.diversity(r["candidates"]) for r in rows]
    mean_pair = sum(d["mean_pairwise_wer"] for d in divs) / len(divs)
    mean_uniq = sum(d["n_unique"] for d in divs) / len(divs)
    single = 100.0 * sum(1 for d in divs if d["n_unique"] == 1) / len(divs)

    print("\n" + "-" * 74)
    print("CANDIDATE DIVERSITY")
    print("-" * 74)
    print(f"mean pairwise distance between candidates: {mean_pair:.1f} % WER")
    print(f"mean unique texts out of {K}: {mean_uniq:.1f}")
    print(f"utterances where all {K} candidates are identical: {single:.1f} %")

    out["diversity"] = {"mean_pairwise_wer": mean_pair, "mean_unique": mean_uniq,
                        "all_identical_pct": single}

    rhos = [r for r in (spearman([c["avg_conf"] for c in row["candidates"]], all_wers[i])
                        for i, row in enumerate(rows)) if r is not None]
    if rhos:
        out["spearman_conf_wer"] = sum(rhos) / len(rhos)
        print(f"\nSpearman rho(confidence, WER) within an utterance: "
              f"{out['spearman_conf_wer']:+.3f} over {len(rhos)} utts "
              f"(more negative = better ranking)")

    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[bucket_of(r["duration_s"])].append(i)

    print("\n" + "-" * 74)
    print(f"{'duration':<12}{'n':>7}{'baseline':>11}{'oracle':>10}{'gap':>9}{'coverage':>11}")
    print("-" * 74)
    bucket_out = {}
    for _, _, name in BUCKETS:
        ii = by.get(name)
        if not ii:
            continue
        br = [refs[i] for i in ii]
        b = S.mean_utt_wer(br, [rows[i]["candidates"][base_idx[i]]["text"] for i in ii])
        o = S.mean_utt_wer(br, [rows[i]["candidates"][oracle_idx[i]]["text"] for i in ii])
        cov = 100.0 * sum(1 for i in ii if per_utt_gap[i] > 1e-9) / len(ii)
        bucket_out[name] = {"n": len(ii), "baseline": b, "oracle": o,
                            "gap": b - o, "coverage": cov}
        print(f"{name:<12}{len(ii):>7}{b:>11.2f}{o:>10.2f}{b-o:>9.2f}{cov:>10.1f}%")
    out["by_duration"] = bucket_out

    print("\n" + "-" * 74)
    print(f"{'k':<6}{'baseline':>11}{'oracle':>10}{'gap':>9}")
    print("-" * 74)
    k_out = {}
    for k in sorted({min(x, K) for x in [1, 3, 5, 10, 15, 20, 25, 30, K]}):
        if k > K:
            continue
        bi, oi = [], []
        for i, r in enumerate(rows):
            sc = S.s_mean_conf(r["candidates"][:k])
            bi.append(max(range(k), key=lambda j: sc[j]))
            oi.append(min(range(k), key=lambda j: all_wers[i][j]))
        b = S.mean_utt_wer(refs, [rows[i]["candidates"][j]["text"] for i, j in enumerate(bi)])
        o = S.mean_utt_wer(refs, [rows[i]["candidates"][j]["text"] for i, j in enumerate(oi)])
        k_out[k] = {"baseline": b, "oracle": o}
        print(f"{k:<6}{b:>11.2f}{o:>10.2f}{b-o:>9.2f}")
    out["by_k"] = k_out

    print("\n" + "=" * 74)
    print("VERDICT against the pre-registered criterion")
    print("=" * 74)
    c1 = out["gap_mean_utt"] >= args.min_gap
    c2 = coverage >= args.min_coverage
    c3 = mean_pair > 0.0
    print(f"  gap >= {args.min_gap} ................. {out['gap_mean_utt']:6.2f}   {'OK' if c1 else 'NO'}")
    print(f"  coverage >= {args.min_coverage} % ............ {coverage:6.1f}   {'OK' if c2 else 'NO'}")
    print(f"  non-zero diversity ............ {mean_pair:6.1f}   {'OK' if c3 else 'NO'}")
    print(f"\n  -> {'GO' if (c1 and c2 and c3) else 'STOP'}")
    out["verdict"] = {"gap_ok": c1, "coverage_ok": c2, "diversity_ok": c3,
                      "go": c1 and c2 and c3}

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"\nstats written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
