#!/usr/bin/env python3
"""Is the information in these features, or is it the model that is too weak?

tools/stitch_learn.py trains a linear scorer over stitchings and captures 0.3 % of the 6.07
WER sitting in its own search space. That has two possible readings and they lead to
completely different next steps: either the features carry the answer and a linear model
cannot extract it -- in which case build a bigger model -- or the features do not carry it,
in which case a bigger model is wasted compute and the fix belongs in the decoder.

Two measurements, neither of which assumes a model class:

  NEAREST NEIGHBOUR CEILING. k-NN regression on the same features estimates E[edits | x]
  directly, and converges to the Bayes-optimal predictor as the sample grows. If the best
  possible function of these features still cannot rank, no architecture over them can.
  Scored on a fixed sampled subset of the space so the linear scorer, the k-NN and the
  oracle are all choosing from exactly the same menu.

  COLLISION TEST. Within one utterance, take pairs of stitchings whose standardised feature
  vectors are nearly identical and look at how far apart their true edit counts are. Any
  scorer gives near-identical inputs near-identical scores, so a large spread here is a hard
  limit that no amount of capacity removes. The reference distribution is the spread over
  random pairs from the same utterance: if collisions are as spread out as random pairs, the
  features have told us nothing.

    PYTHONPATH=src python3 tools/stitch_signal.py --max_utts 40
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np
from rapidfuzz.distance import Levenshtein

import campaign.analysis as A
from crf_rover import Bigram
from stitch_learn import CAND_F, SLOT_F, EVAL_SETS, build, feats, words


def menu(d, rng, n):
    """A fixed sampled subset of the stitching space: every no-switch path plus n random.

    Features are standardised INSIDE the utterance. The decision is a ranking among this
    utterance's own options, so what matters is how a stitching compares to its siblings, not
    its absolute confidence -- and a neighbour search over absolute features just retrieves
    utterances of similar difficulty. Centring here is what makes a nearest-neighbour
    estimate of E[edits | features] mean anything.
    """
    out = [(0, c, c) for c in range(d["k"])]
    for _ in range(n):
        out.append((rng.randrange(d["T"] + 1), rng.randrange(d["k"]), rng.randrange(d["k"])))
    X = np.stack([feats(d, *s) for s in out])
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    e = np.array([Levenshtein.distance(d["ref"], words(d, *s)) for s in out], float)
    txt = [" ".join(words(d, *st)) for st in out]
    return X, e, len(d["ref"]), txt


def load(root, model, arm, max_utts):
    by_set: dict[str, list] = {}
    for dd in sorted(glob.glob(f"{root}/{model}__*")):
        s = Path(dd).name.split("__")[1]
        got = by_set.setdefault(s, [])
        for f in sorted(glob.glob(f"{dd}/{arm}.jsonl.gz")):
            if len(got) >= max_utts:
                break
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    got.append(json.loads(line))
                    if len(got) >= max_utts:
                        break
    return by_set


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/campaign-2026-09-20/dumps")
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max_utts", type=int, default=40)
    ap.add_argument("--train_utts", type=int, default=250)
    ap.add_argument("--test_utts", type=int, default=120)
    ap.add_argument("--menu", type=int, default=200, help="random stitchings per utterance")
    ap.add_argument("--knn", default="1,5,20,80")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    by_set = load(a.root, a.model, a.arm, a.max_utts)
    pool = [r for s in by_set if s not in EVAL_SETS for r in by_set[s]]
    rng0 = random.Random(7)
    rng0.shuffle(pool)
    third = max(len(pool) // 3, 1)
    lm = Bigram([A.S.normalize(r["reference"]).split() for r in pool[:third]])
    train_rows = pool[third:][:a.train_utts]
    # round-robin across the held-out sets: taking them in order fills the quota from
    # ls-test-clean alone and the "held-out" number is then one easy domain.
    buckets = [list(by_set.get(s, [])) for s in EVAL_SETS]
    test_rows = []
    while len(test_rows) < a.test_utts and any(buckets):
        for b in buckets:
            if b and len(test_rows) < a.test_utts:
                test_rows.append(b.pop(0))
    print(f"{len(train_rows)} training / {len(test_rows)} held-out utterances, "
          f"{a.k + a.menu} stitchings scored per utterance", flush=True)

    rng = random.Random(a.seed)
    tr, te = [], []
    for rows, dst in ((train_rows, tr), (test_rows, te)):
        for r in rows:
            d = build(r, a.k, lm)
            if d:
                dst.append(menu(d, rng, a.menu) + (d["rover_e"],))
    if not tr or not te:
        print("not enough data")
        return 2

    # centre the target inside each utterance: only the within-utterance ranking matters,
    # and edit counts are not comparable between utterances of different lengths.
    Xtr = np.concatenate([X for X, _, _, _, _ in tr])
    ytr = np.concatenate([(e - e.mean()) / max(R, 1) for _, e, R, _, _ in tr])
    Ztr = Xtr                                   # already standardised within each utterance
    print(f"{len(Ztr)} training stitchings, {Ztr.shape[1]} features\n", flush=True)

    R_tot = sum(R for _, _, R, _, _ in te)
    rov = 100.0 * sum(r for _, _, _, _, r in te) / R_tot
    best_in_menu = 100.0 * sum(e.min() for _, e, _, _, _ in te) / R_tot
    no_switch = 100.0 * sum(e[:a.k].min() for _, e, _, _, _ in te) / R_tot

    print(f"{'on the held-out utterances':<44}{'WER':>8}")
    print(f"  {'ROVER as shipped':<42}{rov:>8.2f}")
    print(f"  {'oracle over the MENU (no switch only)':<42}{no_switch:>8.2f}")
    print(f"  {'oracle over the MENU (with switches)':<42}{best_in_menu:>8.2f}")

    ks = [int(x) for x in a.knn.split(",") if x.strip()]
    sq_tr = (Ztr * Ztr).sum(1)
    for kk in ks:
        picked = 0.0
        for Z, e, R, _, _ in te:
            d2 = sq_tr[None, :] - 2.0 * (Z @ Ztr.T) + (Z * Z).sum(1)[:, None]
            idx = np.argpartition(d2, kk, axis=1)[:, :kk]
            yhat = ytr[idx].mean(1)
            picked += e[int(np.argmin(yhat))]
        w = 100.0 * picked / R_tot
        print(f"  {f'k-NN over the same features, k={kk}':<42}{w:>8.2f}"
              f"   {100 * (rov - w) / max(rov - best_in_menu, 1e-9):>5.1f}% of the menu's gap")

    # ---- collision test
    # The threshold is a percentile of the observed pair distances, not a fixed number:
    # after within-utterance standardisation the scale depends on how varied an utterance's
    # options are, and a fixed epsilon collected eight pairs in the whole test set.
    rngc = random.Random(1)
    pairs = []
    for Z, e, R, txt, _ in te:
        n = len(Z)
        per = max(R / max(len(te), 1), 1.0)
        for _ in range(600):
            i, j = rngc.randrange(n), rngc.randrange(n)
            if i == j or txt[i] == txt[j]:
                continue
            pairs.append((float(np.linalg.norm(Z[i] - Z[j]) / np.sqrt(Z.shape[1])),
                          abs(e[i] - e[j]) / per))
    pairs.sort(key=lambda x: x[0])
    n = len(pairs)
    print(f"\n{'pairs of DIFFERENT transcripts':<34}{'n':>8}{'median |edits|':>16}"
          f"{'mean':>8}")
    for lab, lo, hi in (("nearest 1 % by feature distance", 0, 0.01),
                        ("nearest 5 %", 0, 0.05),
                        ("all pairs (reference)", 0.0, 1.0)):
        sl = [d for _, d in pairs[int(lo * n):max(int(hi * n), 1)]]
        print(f"{lab:<34}{len(sl):>8}{np.median(sl):>16.2f}{np.mean(sl):>8.2f}")
    print(f"\nfeature distance at the 1st percentile: {pairs[max(int(0.01 * n) - 1, 0)][0]:.3f}"
          f"   (median over all pairs {pairs[n // 2][0]:.3f})")
    print("\nIf the near rows match the reference row, stitchings that look the same to the")
    print("features really are as different in quality as any two, and no model over these")
    print("features -- of any size -- can separate them. k-NN is the same statement from the")
    print("other side: it estimates E[edits | features] directly, so if it cannot rank, the")
    print("Bayes-optimal function of these features cannot either.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
