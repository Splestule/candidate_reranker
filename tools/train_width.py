#!/usr/bin/env python3
"""Train and evaluate the width predictor, held out by dataset so nothing leaks.

Everything is exact and offline: the k ladder is what decoding at k would have produced, so
the evaluation is a lookup, not a simulation. Reported against three references -- the full
flat run, the heuristic we shipped, and the oracle -- because the question is not whether
the model beats nothing, it is how much of the gap between the heuristic and the ceiling it
closes.

    PYTHONPATH=src python tools/train_width.py results/trees2/campaign
"""

from __future__ import annotations

import argparse

import numpy as np

import width_model as W


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--arm", default="flat")
    ap.add_argument("--budgets", default="4,6,8,12,16")
    args = ap.parse_args()

    df = W.build(args.root, arm=args.arm)
    sets = sorted(df["set"].dropna().unique()) if df["set"].notna().any() else []
    if not sets:
        df["set"] = df.id.str.split("-").str[0]
        sets = sorted(df["set"].unique())
    print(f"{len(df)} utterances, {len(W.FEATURES)} features, sets: {', '.join(map(str, sets))}")
    print(f"k_needed: mean {df.k_needed.mean():.1f}, median {df.k_needed.median():.0f}, "
          f"{100 * (df.k_needed == 1).mean():.0f} % need only one candidate\n")

    ladder = sorted(df.ladder.iloc[0])
    kmax = max(ladder)

    for held in sets:
        tr, te = df[df["set"] != held], df[df["set"] == held]
        if len(tr) < 100 or len(te) < 50:
            continue
        model = W.fit(tr)
        full = W.evaluate(te, np.full(len(te), kmax))
        orac = W.evaluate(te, te.k_needed.to_numpy())
        print(f"held out: {held}   ({len(te)} utts, trained on {len(tr)})")
        print(f"  {'policy':<22}{'mean K':>8}{'WER':>8}{'vs full':>9}{'saving':>9}")
        print(f"  {'full K=' + str(kmax):<22}{kmax:>8.1f}{full['wer']:>8.2f}"
              f"{0.0:>+9.2f}{1.0:>8.2f}x")
        print(f"  {'oracle width':<22}{orac['mean_k']:>8.1f}{orac['wer']:>8.2f}"
              f"{full['wer'] - orac['wer']:>+9.2f}{kmax / orac['mean_k']:>8.2f}x")
        for b in [float(x) for x in args.budgets.split(",")]:
            ks = W.predict_k(model, te, ladder, budget=b)
            r = W.evaluate(te, ks)
            rnd = W.evaluate(te, np.full(len(te), int(round(r["mean_k"]))))   # same budget, flat
            print(f"  {'learned, budget ' + str(int(b)):<22}{r['mean_k']:>8.1f}{r['wer']:>8.2f}"
                  f"{full['wer'] - r['wer']:>+9.2f}{kmax / max(r['mean_k'], 1e-9):>8.2f}x"
                  f"    flat at the same K: {rnd['wer']:.2f}")
        print()

    model = W.fit(df)
    order = np.argsort(-np.abs(model["w"][:-1]))
    print("feature weights, largest first (ranking only, the sign says more candidates needed):")
    for i in order:
        print(f"  {W.FEATURES[i]:<16}{model['w'][i]:+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
