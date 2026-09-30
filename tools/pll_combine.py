#!/usr/bin/env python3
"""Does the decoder's own likelihood add anything to the vote?

tools/pll_rescore.py showed the pseudo-log-likelihood carries real ranking signal
(within-utterance Spearman +0.42 against edits) but loses to ROVER when used alone: 17.80
against 11.93 on ls-test-other. The two make different kinds of mistakes -- the likelihood
judges a whole transcript against the audio, ROVER counts agreement slot by slot -- so the
question is whether a combination beats both.

The vote has to be put on the same footing as the likelihood first: a score for a whole
transcript, not a word. The natural one is path-level agreement, the MBR quantity -- how close
this transcript is, on average, to each of the K candidates. ROVER's own output is in the menu
and gets an indicator, so "just keep ROVER" is always one of the options the tuner can take,
and a combination can only be reported as a gain if it beats that option on held-out data.

    score = z(pll) * a  +  z(agreement) * b  +  mu * [entry is ROVER's output]

z() standardises within the utterance: only the ranking inside one menu matters. a, b and mu
are tuned on one half of the utterances and scored on the other, both ways round, over several
random splits, so the interval carries the tuning noise as well as the test noise -- the
lesson of the Mangu and calibration retractions.

The menus are not stored in the results file, only their scores; they are rebuilt here from
the dumps with the same seed, in the same order, and checked entry for entry against the
stored menu sizes before anything is computed.

    PYTHONPATH=src:tools python3 tools/pll_combine.py \\
        --results results/pll_ls-test-other_fullmask_190.json \\
        --dumps <dir with main.jsonl.gz> --manifest <set>.jsonl
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np
from rapidfuzz.distance import Levenshtein

import scorers as S
from pll_rescore import build_menu


def z(x):
    x = np.asarray(x, float)
    s = x.std()
    return (x - x.mean()) / s if s > 1e-12 else x * 0.0


def replay(results, dumps, manifest, k, menu, seed):
    rows = {}
    with gzip.open(dumps, "rt", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            rows[d["id"]] = d
    want = {r["id"] for r in results}
    rng = random.Random(seed)
    out = {}
    for line in open(manifest, encoding="utf-8"):
        uid = json.loads(line)["id"]
        row = rows.get(uid)
        if row is None:
            continue
        m = build_menu(row, k, menu, rng)          # consumes the rng exactly as the run did
        ref = S.normalize(row["reference"]).split()
        if m is None or not ref or len(m["menu"]) < 3:
            continue
        if uid in want:
            cands = [S.normalize(c["text"]).split() for c in row["candidates"]][:k]
            out[uid] = (m, cands)
        if len(out) == len(want):
            break
    return out


def features(results, menus):
    """Per utterance: (edits, z-pll, z-agreement, is_rover, rover_edits, n_ref)."""
    utts = []
    for r in results:
        m, cands = menus[r["id"]]
        agree = []
        for w in m["menu"]:
            d = [Levenshtein.distance(w, c) / max(len(w), len(c), 1) for c in cands]
            agree.append(-float(np.mean(d)))
        utts.append(dict(
            e=np.asarray(r["edits"], float), p=z(r["pll"]), g=z(agree),
            # by TEXT, not by tag: when ROVER's output equals one of the candidates the menu
            # keeps it once, tagged "candidate", and a tag-based indicator then marks nothing
            # -- "always ROVER" silently stopped meaning always ROVER in the first version.
            rv=np.array([1.0 if w == m["rover"] else 0.0 for w in m["menu"]]),
            rover_e=float(r["rover_e"]), n=r["n_ref"]))
    return utts


def pick(u, a, b, mu):
    return float(u["e"][int(np.argmax(a * u["p"] + b * u["g"] + mu * u["rv"]))])


GRID_A = [0.0, 1.0]
GRID_B = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
GRID_MU = [0.0, 0.5, 1.0, 2.0, 4.0, 1e6]      # 1e6 = always ROVER


def tune(utts, arms):
    best = None
    for a, b, mu in arms:
        if a == 0 and b == 0 and mu < 1e5:
            continue
        v = sum(pick(u, a, b, mu) for u in utts)
        if best is None or v < best[0]:
            best = (v, (a, b, mu))
    return best[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--dumps", default="", help="the main.jsonl.gz the run read; not needed "
                    "when the results file stores its menus (every run since 29.9.)")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--menu", type=int, default=32)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--splits", type=int, default=50)
    a = ap.parse_args()

    results = json.loads(Path(a.results).read_text())
    if all("menu" in r and "cands" in r for r in results):
        menus = {r["id"]: (dict(menu=[t.split() for t in r["menu"]], rover=r["rover"].split()),
                           [c.split() for c in r["cands"]]) for r in results}
        print("menus read from the results file")
    elif a.dumps and a.manifest:
        menus = replay(results, a.dumps, a.manifest, a.k, a.menu, a.seed)
    else:
        print("this results file predates stored menus: pass --dumps and --manifest")
        return 2
    bad = [r["id"] for r in results
           if r["id"] not in menus or len(menus[r["id"]][0]["menu"]) != len(r["pll"])]
    print(f"{len(results)} scored utterances, {len(menus)} menus rebuilt, "
          f"{len(bad)} mismatched")
    if bad:
        print("the rebuilt menus do not match the run -- different seed, --menu or dumps?")
        return 1
    utts = features(results, menus)
    R = sum(u["n"] for u in utts)
    W = lambda tot: 100.0 * tot / R

    print(f"\n{'fixed rules, all utterances':<44}{'WER':>8}")
    rows = [("ROVER as shipped", sum(u["rover_e"] for u in utts)),
            ("likelihood alone", sum(pick(u, 1, 0, 0) for u in utts)),
            ("path-level vote alone (MBR agreement)", sum(pick(u, 0, 1, 0) for u in utts)),
            ("likelihood + vote, equal weight", sum(pick(u, 1, 1, 0) for u in utts)),
            ("oracle over the menu", sum(u["e"].min() for u in utts))]
    for lab, v in rows:
        print(f"  {lab:<42}{W(v):>8.2f}")

    arms = [(x, y, m) for x in GRID_A for y in GRID_B for m in GRID_MU]
    print(f"\n{'b (vote)':>10}" + "".join(f"{'mu=' + ('inf' if m > 1e5 else str(m)):>10}"
                                        for m in GRID_MU) + "   likelihood weight a=1")
    for y in GRID_B:
        print(f"{y:>10.2f}" + "".join(f"{W(sum(pick(u, 1, y, m) for u in utts)):>10.2f}"
                                      for m in GRID_MU))
    print("  (in-sample: for reading the shape, not for reporting)")

    # ---- held-out: tune on one half, score the other, both ways, many random splits
    rover_tot = sum(u["rover_e"] for u in utts)
    deltas, chosen = [], []
    per_utt_gain = np.zeros(len(utts))
    rng = np.random.default_rng(a.seed)
    for _ in range(a.splits):
        idx = rng.permutation(len(utts))
        h = len(idx) // 2
        folds = [idx[:h], idx[h:]]
        tot = 0.0
        for f in (0, 1):
            tr = [utts[i] for i in folds[f]]
            te = folds[1 - f]
            prm = tune(tr, arms)
            chosen.append(prm)
            for i in te:
                e = pick(utts[i], *prm)
                tot += e
                per_utt_gain[i] += (utts[i]["rover_e"] - e) / a.splits
        deltas.append(W(rover_tot - tot))
    deltas = np.sort(np.array(deltas))
    print(f"\nheld out, {a.splits} random 2-fold splits (tuned on one half, scored on the other)")
    print(f"  gain over ROVER: median {np.median(deltas):+.2f} WER, "
          f"split-to-split range [{deltas[0]:+.2f}, {deltas[-1]:+.2f}]")

    # test-set noise on top: bootstrap utterances on the averaged held-out gains
    n = np.array([u["n"] for u in utts], float)
    bs = []
    for _ in range(4000):
        i = rng.integers(0, len(utts), len(utts))
        bs.append(100.0 * per_utt_gain[i].sum() / n[i].sum())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    print(f"  bootstrap over utterances: {100.0 * per_utt_gain.sum() / n.sum():+.2f} WER, "
          f"95% CI [{lo:+.2f}, {hi:+.2f}]"
          + ("   spans zero" if lo <= 0 <= hi else ""))
    from collections import Counter
    c = Counter(chosen)
    print("  settings the tuner chose (a, b, mu):")
    for (x, y, m), k_ in c.most_common(5):
        print(f"    a={x:g} b={y:g} mu={'inf' if m > 1e5 else m:<5}  {k_} of {len(chosen)} folds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
