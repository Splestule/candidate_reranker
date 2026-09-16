#!/usr/bin/env python3
"""Pick selection parameters on a dev dump, report them on a test dump.

Tuning and reporting on the same set is the mistake this exists to prevent.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from rapidfuzz.distance import Levenshtein

import compose
import scorers as S


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def prep(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        cands, confs = compose.prepare(row)
        out.append({
            "ref": S.normalize(row["reference"]).split(),
            "cands": cands,
            "confs": confs,
            "backbone": compose.central_index(cands),
            "raw": row["candidates"],
            "net": {},
            "conf": S.s_mean_conf(row["candidates"]),
            "mbr": S.s_mbr_wer(row["candidates"]),
        })
    return out


def network(it: dict, gamma: float, threshold: float = 0.0):
    """Confusion network for one gamma, built once per utterance and kept."""
    if gamma not in it["net"]:
        w = compose.cluster_weights(it["cands"], gamma, threshold)
        it["net"][gamma] = (
            compose.confusion_network(it["cands"], it["backbone"], it["confs"], w),
            sum(w),
        )
    return it["net"][gamma]


def wer_of(items, hyp_fn) -> float:
    e = w = 0
    for it in items:
        e += Levenshtein.distance(it["ref"], hyp_fn(it))
        w += len(it["ref"])
    return 100.0 * e / max(w, 1)


def select_lambda(items, lam):
    def f(it):
        sc = [a + lam * b for a, b in zip(it["conf"], it["mbr"])]
        return it["cands"][max(range(len(sc)), key=lambda i: sc[i])]
    return f


def rover_params(alpha, eps_conf, gamma):
    def f(it):
        slots, total = network(it, gamma)
        return compose.rover(slots, total, alpha, eps_conf)
    return f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", required=True, nargs="+")
    ap.add_argument("--test", default=None)
    ap.add_argument("--gammas", default="0.0,0.25,0.5,0.75,1.0")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    dev = prep([r for p in args.dev for r in load(p)])
    print(f"dev: {len(dev)} utterances from {len(args.dev)} dump(s)")

    print("\nlambda for conf + lambda*mbr")
    lambdas = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
    lam_wer = {lam: wer_of(dev, select_lambda(dev, lam)) for lam in lambdas}
    for lam in lambdas:
        print(f"  {lam:>4}  {lam_wer[lam]:6.2f}")
    best_lam = min(lam_wer, key=lam_wer.get)

    print("\nROVER: alpha (1.0 = votes only), epsilon confidence, gamma (1.0 = one vote each)")
    alphas = [0.3, 0.5, 0.7, 0.85, 1.0]
    eps_list = [0.3, 0.5, 0.7]
    gammas = [float(g) for g in args.gammas.split(",")]
    have_conf = any("word_conf" in c for it in dev for c in it["raw"])
    if not have_conf:
        alphas, eps_list = [1.0], [0.5]
        print("  dump has no per-word confidences, votes only")
    rover_wer = {(a, e, g): wer_of(dev, rover_params(a, e, g))
                 for g in gammas for a in alphas for e in eps_list}
    for (a, e, g), v in sorted(rover_wer.items(), key=lambda kv: kv[1]):
        print(f"  alpha {a:<5} eps {e:<5} gamma {g:<5} {v:6.2f}")
    best_alpha, best_eps, best_gamma = min(rover_wer, key=rover_wer.get)

    # What the cluster weighting is worth on its own, at the best alpha/eps.
    at_one = rover_wer.get((best_alpha, best_eps, 1.0))
    if at_one is not None and best_gamma != 1.0:
        print(f"\n  gamma {best_gamma} vs gamma 1.0 at the same alpha/eps: "
              f"{at_one - rover_wer[(best_alpha, best_eps, best_gamma)]:+.2f} points on dev")

    print(f"\nchosen on dev: lambda={best_lam}  alpha={best_alpha}  "
          f"eps_conf={best_eps}  gamma={best_gamma}")
    out = {"dev": args.dev, "n_dev": len(dev), "lambda": best_lam,
           "alpha": best_alpha, "eps_conf": best_eps, "gamma": best_gamma,
           "dev_wer": {"select": lam_wer[best_lam],
                       "rover": rover_wer[(best_alpha, best_eps, best_gamma)],
                       "rover_gamma1": at_one}}

    if args.test:
        test = prep(load(args.test))
        base = wer_of(test, lambda it: it["cands"][
            max(range(len(it["conf"])), key=lambda i: it["conf"][i])])
        sel = wer_of(test, select_lambda(test, best_lam))
        rov = wer_of(test, rover_params(best_alpha, best_eps, best_gamma))
        rov1 = wer_of(test, rover_params(best_alpha, best_eps, 1.0))
        print(f"\ntest: {len(test)} utterances from {args.test}")
        print(f"  pick by confidence      {base:6.2f}")
        print(f"  pick with tuned lambda  {sel:6.2f}")
        print(f"  ROVER, gamma 1.0        {rov1:6.2f}")
        print(f"  ROVER with tuned params {rov:6.2f}")
        out["test"] = {"path": args.test, "n": len(test), "baseline": base,
                       "select": sel, "rover": rov, "rover_gamma1": rov1}

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"\nwritten: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
