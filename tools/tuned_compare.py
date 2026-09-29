#!/usr/bin/env python3
"""Compare two arms when both have to be tuned, with the tuning's own noise in the interval.

The usual recipe -- tune each arm on dev, apply to test, bootstrap the test utterances --
hides a whole source of variance, and on 29.9.2026 it produced a +1.11 WER result in this
project that was entirely one badly-tuned baseline parameter. With a small dev set the tuner
is a lottery, and whichever arm draws the worse ticket loses; the test-set bootstrap knows
nothing about that, so it reports a tight interval around an artefact.

What this does instead, B times:

  resample the DEV utterances with replacement,
  tune every arm on that resample,
  score the arms on the fixed TEST set with the parameters that resample chose.

The spread of the resulting deltas is the interval that matters: it answers "would this
result survive someone else's dev set", which is the question a reader actually has.

It also prints, for each arm, how far its best and worst parameter settings are apart. When
that spread is larger than the effect, no amount of test data rescues the comparison -- the
honest report is that the experiment cannot resolve it.

Reads the per-utterance results eval_mangu.py writes.

    PYTHONPATH=src python tools/tuned_compare.py \\
        results/eval_mangu_k32_n200__res_0.45x1c.pkl --rounds 400
"""

from __future__ import annotations

import argparse
import pickle
import random
import statistics
from pathlib import Path

DEV_SETS = ("ls-dev-clean", "ls-dev-other")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("res")
    ap.add_argument("--rounds", type=int, default=400)
    ap.add_argument("--baseline", default="backbone")
    ap.add_argument("--dev_frac", type=float, default=1.0,
                    help="use this fraction of dev per round, to show how the interval "
                         "widens when the dev set is small")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    res = pickle.loads(Path(a.res).read_bytes())
    dev = [r for r in res if r["set"] in DEV_SETS]
    test = [r for r in res if r["set"] not in DEV_SETS]
    if not dev or not test:
        print("need dev and test utterances in that results file")
        return 2
    params = sorted({(al, e) for (_, al, e) in res[0]["edits"]})
    arms = sorted({n for (n, _, _) in res[0]["edits"]})
    others = [n for n in arms if n != a.baseline]
    if not others:
        print(f"no arm to compare against {a.baseline}")
        return 2
    R_test = sum(r["n_ref"] for r in test)
    print(f"{len(dev)} dev / {len(test)} test utterances, {len(params)} parameter settings, "
          f"arms {arms}\n")

    # ---- how much do the parameters matter at all?
    print(f"{'arm':<16}{'best':>8}{'worst':>9}{'spread':>9}   on the full dev set")
    for n in arms:
        vals = []
        for (al, e) in params:
            num = sum(r["edits"][(n, al, e)] for r in dev)
            vals.append(100.0 * num / sum(r["n_ref"] for r in dev))
        print(f"{n:<16}{min(vals):>8.2f}{max(vals):>9.2f}{max(vals) - min(vals):>9.2f}")

    # ---- the tuning-aware bootstrap
    rng = random.Random(a.seed)
    n_dev = max(int(len(dev) * a.dev_frac), 10)
    print(f"\ntuning-aware bootstrap: {a.rounds} rounds, each re-tuning on {n_dev} "
          f"resampled dev utterances")
    print(f"\n{'arm vs ' + a.baseline:<24}{'median':>9}{'2.5%':>9}{'97.5%':>9}"
          f"{'>0':>7}   parameters chosen")
    for n in others:
        deltas, picks_b, picks_n = [], [], []
        for _ in range(a.rounds):
            samp = [dev[rng.randrange(len(dev))] for _ in range(n_dev)]
            Rd = sum(r["n_ref"] for r in samp)

            def tuned(arm):
                return min(params,
                           key=lambda p: sum(r["edits"][(arm,) + p] for r in samp) / max(Rd, 1))

            pb, pn = tuned(a.baseline), tuned(n)
            picks_b.append(pb); picks_n.append(pn)
            eb = sum(r["edits"][(a.baseline,) + pb] for r in test)
            en = sum(r["edits"][(n,) + pn] for r in test)
            deltas.append(100.0 * (eb - en) / R_test)
        deltas.sort()
        lo = deltas[int(0.025 * len(deltas))]
        hi = deltas[int(0.975 * len(deltas)) - 1]
        pos = 100.0 * sum(1 for d in deltas if d > 0) / len(deltas)
        mb = statistics.mode(picks_b); mn = statistics.mode(picks_n)
        print(f"{n:<24}{statistics.median(deltas):>+9.2f}{lo:>+9.2f}{hi:>+9.2f}{pos:>6.0f}%"
              f"   {a.baseline} {mb} mostly, {n} {mn} mostly")

    print("\nread the interval, not the median: it spans what a different dev set would have")
    print("given you. If it contains zero, the experiment does not resolve the question,")
    print("however many test utterances there are.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
