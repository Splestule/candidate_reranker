#!/usr/bin/env python3
"""Does the confidence calibration survive someone else's dev set?

calibrate_rover.py fits the calibration on dev, tunes alpha/eps on dev, and scores on
held-out sets. That is the right split, but the reported delta still treats one particular
dev set as given. The Mangu retraction on 29.9.2026 showed what that hides: when an arm's
parameter spread is tens of WER points, which parameters the tuner happens to land on is a
bigger effect than anything being measured.

So: resample the dev utterances with replacement, refit the calibration on that resample,
re-tune alpha/eps on it, and score on the fixed test sets. Everything that was fitted gets
refitted every round, so the interval carries the fitting noise as well as the test noise.

The comparison is always against "as-is" -- today's confidences with alpha/eps tuned on the
same resample -- so a calibrated arm never gets credit for tuning the baseline lacked.

    python3 tools/audit_calib.py --cache results/calib_cache.pkl --rounds 300 --workers 8
"""

from __future__ import annotations

import argparse
import pickle
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, "tools")
sys.path.insert(0, "src")

import numpy as np

import calibrate_rover as C

ARMS = ("as-is", "isotonic", "power", "freq only")


def tune(rows, m, alphas=None):
    best = None
    for a in (alphas or C.GRID_ALPHA):
        for e in C.GRID_EPS:
            w = C.wer(rows, m, a, e)
            if best is None or w < best[2]:
                best = (a, e, w)
    return best


def one_round(seed: int):
    """Refit and re-tune on a dev resample; return each arm's WER on the fixed test set."""
    rng = random.Random(seed)
    samp = [DEV[rng.randrange(len(DEV))] for _ in range(len(DEV))]
    c, y = C.conf_label_pairs(samp)
    if len(c) < 100:
        return None
    pw = C.fit_power(c, y)
    iso = C.fit_isotonic(c, y)
    maps = {"as-is": None, "isotonic": iso, "power": (lambda x, t=pw: x ** t)}

    out = {"power_t": pw, "seed": seed}
    for name, m in maps.items():
        a, e, _ = tune(samp, m)
        out[name] = (C.wer(TEST, m, a, e), a, e)
    a, e, _ = tune(samp, None, alphas=[1.0])          # confidence ignored: the control
    out["freq only"] = (C.wer(TEST, None, a, e), a, e)
    return out


def _init(dev, test):
    global DEV, TEST
    DEV, TEST = dev, test


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="results/calib_cache.pkl")
    ap.add_argument("--rounds", type=int, default=60,
                    help="rounds to add this run; the device shell is capped at three "
                         "minutes, so this is meant to be called repeatedly")
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--report", action="store_true", help="read --out and print, adding nothing")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    data = pickle.loads(Path(a.cache).read_bytes())
    dev = [d for d in data if d["set"] in C.DEV_SETS]
    test = [d for d in data if d["set"] not in C.DEV_SETS]
    print(f"{len(dev)} dev / {len(test)} test utterances from {a.cache}", flush=True)

    _init(dev, test)
    store = Path(a.out) if a.out else None
    rounds = pickle.loads(store.read_bytes()) if store and store.exists() else []
    if rounds:
        print(f"resuming: {len(rounds)} rounds already in {store}")

    # ---- how much do alpha and eps matter at all, on the full dev set?
    print(f"\n{'arm':<12}{'best':>8}{'worst':>9}{'spread':>9}   alpha/eps on the full dev set",
          flush=True)
    c, y = C.conf_label_pairs(dev)
    pw_full = C.fit_power(c, y)
    iso_full = C.fit_isotonic(c, y)
    for name, m in (("as-is", None), ("isotonic", iso_full),
                    ("power", lambda x: x ** pw_full)):
        vals = [C.wer(dev, m, al, e) for al in C.GRID_ALPHA for e in C.GRID_EPS]
        print(f"{name:<12}{min(vals):>8.2f}{max(vals):>9.2f}{max(vals) - min(vals):>9.2f}",
              flush=True)
    print(f"\nfull-dev power exponent: conf ** {pw_full:.2f}", flush=True)

    # ---- the refit-and-retune bootstrap
    if not a.report:
        done = {r["seed"] for r in rounds}
        seeds = [s for s in range(a.seed0, a.seed0 + 100000) if s not in done][:a.rounds]
        if a.workers > 1:
            import multiprocessing as mp
            with mp.Pool(a.workers, initializer=_init, initargs=(dev, test)) as p:
                new = [r for r in p.map(one_round, seeds, chunksize=2) if r]
        else:
            new = [r for r in map(one_round, seeds) if r]
        rounds += new
        if store:
            store.write_bytes(pickle.dumps(rounds))
            print(f"+{len(new)} rounds, {len(rounds)} total -> {store}", flush=True)
    if not rounds:
        print("no rounds yet")
        return 2
    print(f"\n{len(rounds)} rounds, each refitting the calibration and re-tuning "
          f"alpha/eps on a dev resample", flush=True)

    ts = [r["power_t"] for r in rounds]
    ts.sort()
    print(f"power exponent across rounds: median {statistics.median(ts):.2f}, "
          f"2.5% {ts[int(.025 * len(ts))]:.2f}, 97.5% {ts[int(.975 * len(ts)) - 1]:.2f}")

    base = [r["as-is"][0] for r in rounds]
    print(f"\n{'arm':<12}{'test WER':>10}{'vs as-is':>10}{'2.5%':>9}{'97.5%':>9}{'better':>8}"
          f"   (minus = better)")
    for n in ARMS:
        w = [r[n][0] for r in rounds]
        d = sorted(x - b for x, b in zip(w, base))
        lo, hi = d[int(.025 * len(d))], d[int(.975 * len(d)) - 1]
        frac = 100.0 * sum(1 for x in d if x < 0) / len(d)
        span = "" if (lo > 0 or hi < 0) else "   spans zero"
        print(f"{n:<12}{statistics.median(w):>10.2f}{statistics.median(d):>+10.2f}"
              f"{lo:>+9.2f}{hi:>+9.2f}{frac:>7.0f}%{span}")

    sa, se = C.SHIPPED["alpha"], C.SHIPPED["eps"]
    print(f"\nshipped (alpha {sa}, eps {se}, no calibration) on the same test set: "
          f"{C.wer(test, None, sa, se):.2f}")
    print("'freq only' is the control: alpha forced to 1, so the confidence never votes.")
    print("If the calibrated arms cannot beat as-is by more than the interval, the")
    print("calibration is not a result.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
