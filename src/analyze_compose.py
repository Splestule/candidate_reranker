#!/usr/bin/env python3
"""Phase A: is the candidate set worth more than its best member?

Compares picking one candidate whole against combining them word by word, with a
control that replaces the alternatives with unrelated words to show how much of the
oracle is free choice rather than information.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

from rapidfuzz.distance import Levenshtein

import bootstrap
import compose
import scorers as S


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--json", default=None)
    ap.add_argument("--alpha", type=float, default=1.0,
                    help="ROVER: 1.0 is pure vote frequency, lower mixes in confidence")
    ap.add_argument("--eps_conf", type=float, default=0.5)
    ap.add_argument("--gamma", type=float, default=1.0,
                    help="cluster vote weighting: 1.0 one vote each, 0.0 one vote per cluster")
    ap.add_argument("--cluster_threshold", type=float, default=0.0)
    ap.add_argument("--n_boot", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rows = load(args.dump)
    if not rows:
        print("empty dump")
        return 1

    rng = random.Random(args.seed)
    pool = [w for r in rows[: min(200, len(rows))]
            for w in S.normalize(r["candidates"][0]["text"]).split()]

    tot_ref = 0
    keys = ["baseline", "mbr", "rover", "oracle_cand", "oracle_comp", "control"]
    edits = {k: 0 for k in keys}
    per_utt = {k: [] for k in keys}
    raw = {k: [] for k in keys}
    ref_lens: list[int] = []
    beats_best = 0
    have_conf = 0

    for row in rows:
        ref = S.normalize(row["reference"]).split()
        cands, confs = compose.prepare(row)
        have_conf += confs is not None
        k = len(cands)

        wers = [Levenshtein.distance(ref, c) for c in cands]
        conf_scores = S.s_mean_conf(row["candidates"])
        mbr_scores = S.s_conf_plus_mbr(row["candidates"])

        picks = {
            "baseline": cands[max(range(k), key=lambda i: conf_scores[i])],
            "mbr": cands[max(range(k), key=lambda i: mbr_scores[i])],
            "oracle_cand": cands[min(range(k), key=lambda i: wers[i])],
        }

        backbone = compose.central_index(cands)
        weights = compose.cluster_weights(cands, args.gamma, args.cluster_threshold)
        slots = compose.confusion_network(cands, backbone, confs, weights)
        picks["rover"] = compose.rover(slots, sum(weights), args.alpha, args.eps_conf)

        best_single = min(wers)
        comp = min(compose.oracle_path(slots, ref), best_single)
        ctrl = min(compose.oracle_path(
            compose.shuffled_control(slots, pool, rng), ref), best_single)
        beats_best += comp < best_single

        tot_ref += len(ref)
        ref_lens.append(len(ref))
        for key, hyp in picks.items():
            e = Levenshtein.distance(ref, hyp)
            edits[key] += e
            raw[key].append(e)
            per_utt[key].append(100.0 * e / max(len(ref), 1))
        for key, e in [("oracle_comp", comp), ("control", ctrl)]:
            edits[key] += e
            raw[key].append(e)
            per_utt[key].append(100.0 * e / max(len(ref), 1))

    print("=" * 70)
    print(f"COMPOSITION  ·  {args.dump}")
    print("=" * 70)
    print(f"utterances: {len(rows)}   per-word confidences: "
          f"{'yes' if have_conf == len(rows) else 'no, ROVER votes by frequency only'}")
    print(f"ROVER alpha {args.alpha}  eps_conf {args.eps_conf}  gamma {args.gamma}\n")

    print(f"{'':<34}{'corpus WER':>12}{'mean-utt':>11}")
    labels = [
        ("baseline", "pick by confidence"),
        ("mbr", "pick by conf + 0.5*mbr"),
        ("rover", "ROVER, word-level vote"),
        ("oracle_cand", "oracle over whole candidates"),
        ("oracle_comp", "oracle over word combinations"),
        ("control", "  same, unrelated alternatives"),
    ]
    out = {"dump": args.dump, "n_utts": len(rows), "alpha": args.alpha,
           "eps_conf": args.eps_conf, "gamma": args.gamma, "methods": {}}
    for key, label in labels:
        cw = 100.0 * edits[key] / tot_ref
        mu = statistics.fmean(per_utt[key])
        out["methods"][key] = {"corpus_wer": cw, "mean_utt_wer": mu}
        print(f"{label:<34}{cw:>12.2f}{mu:>11.2f}")

    m = out["methods"]
    real = m["oracle_cand"]["corpus_wer"] - m["oracle_comp"]["corpus_wer"]
    luck = m["oracle_cand"]["corpus_wer"] - m["control"]["corpus_wer"]
    out["headroom_real"] = real
    out["headroom_control"] = luck
    out["beats_best_candidate_pct"] = 100.0 * beats_best / len(rows)
    out["rover_gain"] = m["baseline"]["corpus_wer"] - m["rover"]["corpus_wer"]

    print(f"\ncombining beats the best single candidate on "
          f"{out['beats_best_candidate_pct']:.1f} % of utterances")
    print(f"headroom beyond the candidate oracle: {real:.2f} points")
    print(f"same for the control: {luck:.2f} points")
    if luck > 0:
        print(f"signal-to-luck ratio: {real / luck:.1f}x")
    print(f"ROVER vs baseline: {out['rover_gain']:+.2f} points")

    print(f"\n{'-' * 74}\nPAIRED BOOTSTRAP  ·  {args.n_boot} resamples, positive favours the "
          f"second system\n{'-' * 74}")
    out["bootstrap"] = {}
    for a_key, b_key, label in [("baseline", "rover", "ROVER over pick by confidence"),
                                ("mbr", "rover", "ROVER over conf + 0.5*mbr"),
                                ("baseline", "mbr", "conf + 0.5*mbr over confidence")]:
        s = bootstrap.paired_bootstrap(raw[a_key], raw[b_key], ref_lens,
                                       n_boot=args.n_boot, seed=args.seed)
        out["bootstrap"][f"{b_key}_vs_{a_key}"] = s
        print(bootstrap.format_row(label, s))
        if s and s["ci_low"] <= 0 <= s["ci_high"]:
            print(f"{'':<34}interval spans zero: not distinguishable")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"\nstats written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
