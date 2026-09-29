#!/usr/bin/env python3
"""Is the CRF losing because it is the wrong model, or because 800 utterances is nothing?

crf_rover.py trains a linear-chain CRF on the 800 dev utterances and loses to calibrated
ROVER by 0.61 WER on held-out sets. That is a real negative, but it does not say which of two
very different things is true: the features carry no signal beyond the vote, or they do and
the perceptron has not seen enough slots to find it. The paper needs to know, because the
whole gap-closing programme rests on a learned word picker being possible at all.

So: train the same CRF on 200, 400, 800, 1600, 3200 utterances and watch the held-out delta.
A flat curve says the model is wrong. A curve still moving at 3200 says the experiment is
data-bound and a bigger training set is the next step, not a better architecture.

Everything that can be fitted is refitted at each size -- the bigram LM from the training
references, and the (alpha, eps) of the ROVER baseline it is compared against -- so the
baseline scales with the arm and never loses on a tuning technicality.

The eval sets are held out of every training subset, by set, not by utterance.

    python3 tools/crf_scale.py --cache results/calib_cache.pkl --workers 5
"""

from __future__ import annotations

import argparse
import pickle
import random
import sys
from pathlib import Path

sys.path.insert(0, "tools")
sys.path.insert(0, "src")

import numpy as np

import crf_rover as F

EVAL_SETS = ("ls-test-clean", "ls-test-other", "gigaspeech", "ami", "common_voice")
SIZES = (200, 400, 800, 1600, 3200)
GRID_ALPHA = [0.3, 0.4, 0.5, 0.6, 0.7, 0.85, 1.0]
GRID_EPS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def rover_edits(rows, alpha, eps, power):
    return sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), alpha, eps, power)
                           for s in d["slots"]], d["ref"]) for d in rows)


def tune_rover(rows, power):
    R = sum(len(d["ref"]) for d in rows) or 1
    best = None
    for a in GRID_ALPHA:
        for e in GRID_EPS:
            w = 100.0 * rover_edits(rows, a, e, power) / R
            if best is None or w < best[2]:
                best = (a, e, w)
    return best


def one_size(n: int):
    rng = random.Random(1234 + n)
    train = TRAIN[:]
    rng.shuffle(train)
    train = train[:n]

    lm = F.Bigram([d["ref"] for d in train])
    a_cal, e_cal, dev_w = tune_rover(train, POWER)

    we, wt = F.train(train, lm, POWER, EPOCHS,
                     init=F.rover_weights(a_cal, e_cal))

    R = sum(len(d["ref"]) for d in EVAL) or 1
    crf = sum(F.edits_of(F.decode(d, we, wt, lm, POWER), d["ref"]) for d in EVAL)
    rov = rover_edits(EVAL, a_cal, e_cal, POWER)
    ship = rover_edits(EVAL, 0.5, 0.7, None)
    per_utt_crf = [F.edits_of(F.decode(d, we, wt, lm, POWER), d["ref"]) for d in EVAL]
    per_utt_rov = [F.edits_of([F.rover_pick(s, float(d["n_cand"]), a_cal, e_cal, POWER)
                               for s in d["slots"]], d["ref"]) for d in EVAL]
    return dict(n=n, alpha=a_cal, eps=e_cal, train_wer=dev_w,
                crf=100.0 * crf / R, rover=100.0 * rov / R, shipped=100.0 * ship / R,
                types=len(lm.uni), per_utt_crf=per_utt_crf, per_utt_rov=per_utt_rov)


def _init(train, ev, power, epochs):
    global TRAIN, EVAL, POWER, EPOCHS
    TRAIN, EVAL, POWER, EPOCHS = train, ev, power, epochs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="results/calib_cache.pkl")
    ap.add_argument("--power", type=float, default=11.95)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--sizes", default="")
    ap.add_argument("--out", default="results/crf_scale.pkl")
    a = ap.parse_args()

    data = pickle.loads(Path(a.cache).read_bytes())
    ev = [d for d in data if d["set"] in EVAL_SETS]
    train = [d for d in data if d["set"] not in EVAL_SETS]
    sizes = [int(x) for x in a.sizes.split(",") if x.strip()] or list(SIZES)
    sizes = [n for n in sizes if n <= len(train)]
    print(f"{len(train)} training utterances available "
          f"({len(set(d['set'] for d in train))} sets), "
          f"{len(ev)} eval utterances ({len(EVAL_SETS)} sets)")
    print(f"sizes {sizes}, {a.epochs} epochs, power {a.power}\n", flush=True)

    _init(train, ev, a.power, a.epochs)
    if a.workers > 1:
        import multiprocessing as mp
        with mp.Pool(a.workers, initializer=_init,
                     initargs=(train, ev, a.power, a.epochs)) as p:
            rows = p.map(one_size, sizes)
    else:
        rows = [one_size(n) for n in sizes]

    import bootstrap
    rl = [len(d["ref"]) for d in ev]
    print(f"\n{'train utts':>11}{'LM types':>10}{'alpha':>7}{'eps':>6}{'train WER':>11}"
          f"{'shipped':>9}{'ROVER':>8}{'CRF':>8}{'CRF-ROVER':>11}{'95% CI':>18}")
    print("-" * 99)
    for r in sorted(rows, key=lambda x: x["n"]):
        st = bootstrap.paired_bootstrap(r["per_utt_rov"], r["per_utt_crf"], rl, n_boot=3000)
        ci = f"[{-st['ci_high']:+.2f}, {-st['ci_low']:+.2f}]"
        print(f"{r['n']:>11}{r['types']:>10}{r['alpha']:>7.2f}{r['eps']:>6.2f}"
              f"{r['train_wer']:>11.2f}{r['shipped']:>9.2f}{r['rover']:>8.2f}{r['crf']:>8.2f}"
              f"{r['crf'] - r['rover']:>+11.2f}{ci:>18}")
    print("-" * 99)
    print("CRF-ROVER negative = the learned picker wins. Watch the trend, not one row:")
    print("if it is still improving at the largest size, the experiment is data-bound.")

    Path(a.out).write_bytes(pickle.dumps(rows))
    print(f"\nrows -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
