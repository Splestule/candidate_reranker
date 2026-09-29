#!/usr/bin/env python3
"""Can anything cheap rank stitchings, or is that exactly what the decoder fails to give us?

tools/switch_oracle.py shows the composition gap is segment-shaped: one contiguous switch
between two candidates recovers 55 % of it and four recover 85 %, and the one-switch search
space is about thirty thousand options -- enumerable in microseconds with prefix sums. So
the missing piece is not the search. It is a score that can rank one whole path against
another.

The per-slot ROVER score cannot: summed along a path it lands at 30.6 WER when the best
whole candidate is 20.4 and ROVER itself is 21.6. That is not a switching failure, because
the no-switch version of the same score is just as bad. A slot score was built to be
argmaxed inside its slot, never to be compared across slots or across candidates.

This tries the two cheapest things that could fix that, on a dev/test split by SET:

    mean word confidence of the path      (the decoder's own signal, per word)
    add-k bigram over the emitted words   (fluency, from references the fit never sees)

with one weight tuned on dev. If a combination of those gets near ROVER, a learned segment
scorer is a short step and the direction is open. If it does not, then the decoder emits
nothing that ranks paths, and that is the finding: the fix has to be in training.

    PYTHONPATH=src python3 tools/stitch_score.py --max_utts 40
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np
from rapidfuzz.distance import Levenshtein

import campaign.analysis as A
import compose
from crf_rover import Bigram
from switch_oracle import slot_matrix

EPS = compose.EPS
DEV_SETS = ("ls-dev-clean", "ls-dev-other")


def prep(row, K):
    ref = A.S.normalize(row["reference"]).split()
    cands, confs, _ = A.prepare(row)
    k = min(K, len(cands))
    if k < 2 or not ref:
        return None
    sub, sub_c = cands[:k], (confs[:k] if confs else None)
    lens = [len(c) for c in sub]
    Lm = [[Levenshtein.distance(sub[i], sub[j]) for j in range(k)] for i in range(k)]
    mbr = [-sum(Lm[i][j] / max(lens[j], 1) for j in range(k) if j != i) / (k - 1)
           for i in range(k)]
    p = max(range(k), key=lambda i: mbr[i])
    slots = compose.confusion_network(sub, p, sub_c, None)
    M = slot_matrix(sub, p)
    conf = np.zeros((len(M), k))
    real = np.zeros((len(M), k))
    for t, (r, sl) in enumerate(zip(M, slots)):
        for c in range(k):
            w = r[c]
            if w == EPS:
                continue
            v, cs = sl.get(w, (0.0, 0.0))
            conf[t, c] = cs / v if v > 0 else 0.0
            real[t, c] = 1.0
    return dict(ref=ref, k=k, M=M, slots=slots, conf=conf, real=real)


def path_words(M, t, i, j):
    return [w for w in ([M[x][i] for x in range(t)] + [M[x][j] for x in range(t, len(M))])
            if w != EPS]


def lm_tables(M, k, lm):
    """Per-candidate prefix sums of the bigram score, plus what is needed to rejoin them.

    Scoring every (t, i, j) by re-walking the path is O(T^2 K^2) and takes a minute for
    fifteen utterances. But a stitched path's bigram score is candidate i's prefix plus
    candidate j's suffix, with exactly ONE bond different: the word j contributes first after
    t now follows i's last word before t instead of its own. So keep, per candidate and per
    slot, the prefix sum, the last word before t, the first word from t, and that word's own
    predecessor, and every stitch is four lookups.
    """
    T = len(M)
    bpre = np.zeros((k, T + 1))
    last = [[EPS] * (T + 1) for _ in range(k)]
    for c in range(k):
        prev = EPS
        for t in range(T):
            w = M[t][c]
            bpre[c, t + 1] = bpre[c, t] + (lm(prev, w) if w != EPS else 0.0)
            if w != EPS:
                prev = w
            last[c][t + 1] = prev
    first = [[EPS] * (T + 1) for _ in range(k)]      # first real word at or after t
    fprev = [[EPS] * (T + 1) for _ in range(k)]      # the word it currently follows
    for c in range(k):
        nxt = EPS
        for t in range(T, -1, -1):
            first[c][t] = nxt
            if t < T and M[t][c] != EPS:
                nxt = M[t][c]
                first[c][t] = nxt
        for t in range(T + 1):
            fprev[c][t] = last[c][t]
    return bpre, last, first, fprev


def score_paths(d, lm, mu, switch: bool, lam: float = 0.0):
    """Best path under mean confidence + mu * mean bigram + lam * words-per-slot.

    The length term is not optional. A mean over the words a path emits rewards dropping
    words: a path that says nothing has no low-confidence words in it. Every length-normalised
    decoder score carries a word-insertion bonus for the same reason, so the comparison is
    only fair with one, tuned like the rest.
    """
    M, k = d["M"], d["k"]
    T = len(M)
    cpre = np.vstack([np.zeros(k), np.cumsum(d["conf"], axis=0)])
    npre = np.vstack([np.zeros(k), np.cumsum(d["real"], axis=0)])
    bpre, last, first, fprev = lm_tables(M, k, lm) if mu else (None,) * 4

    best, arg = -1e18, (0, 0, 0)
    if not switch:
        for c in range(k):
            n = npre[T, c]
            if n <= 0:
                continue
            v = cpre[T, c] / n + (mu * bpre[c, T] / n if mu else 0.0) + lam * n / max(T, 1)
            if v > best:
                best, arg = v, (0, c, c)
        return path_words(M, *arg), arg

    for t in range(T + 1):
        for i in range(k):
            hc, hn = cpre[t, i], npre[t, i]
            for j in range(k):
                n = hn + (npre[T, j] - npre[t, j])
                if n <= 0:
                    continue
                v = (hc + (cpre[T, j] - cpre[t, j])) / n + lam * n / max(T, 1)
                if mu:
                    b = bpre[i, t] + (bpre[j, T] - bpre[j, t])
                    w = first[j][t]
                    if w != EPS:
                        b += lm(last[i][t], w) - lm(fprev[j][t], w)
                    v += mu * b / n
                if v > best:
                    best, arg = v, (t, i, j)
    return path_words(M, *arg), arg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/campaign-2026-09-20/dumps")
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max_utts", type=int, default=40)
    ap.add_argument("--mus", default="0,0.25,0.5,1")
    ap.add_argument("--lams", default="0,0.5,1,2,4")
    a = ap.parse_args()

    by_set: dict[str, list] = {}
    for dd in sorted(glob.glob(f"{a.root}/{a.model}__*")):
        s = Path(dd).name.split("__")[1]
        got = by_set.setdefault(s, [])
        for f in sorted(glob.glob(f"{dd}/{a.arm}.jsonl.gz")):
            if len(got) >= a.max_utts:
                break
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    got.append(json.loads(line))
                    if len(got) >= a.max_utts:
                        break
    devall = [r for s in DEV_SETS for r in by_set.get(s, [])]
    half = max(len(devall) // 2, 1)
    lm_rows, tune_rows = devall[:half], devall[half:]       # the bigram never sees the tuner
    dev = [prep(r, a.k) for r in tune_rows]
    test = [prep(r, a.k) for s in by_set if s not in DEV_SETS for r in by_set[s]]
    dev = [d for d in dev if d]
    test = [d for d in test if d]
    if not dev or not test:
        print("need both dev and test sets in the dumps")
        return 2
    lm = Bigram([A.S.normalize(r["reference"]).split() for r in lm_rows])
    print(f"{len(dev)} tuning / {len(test)} test utterances; bigram from {len(lm_rows)} "
          f"other dev utterances ({len(lm.uni)} types), so the tuner never scores text the "
          f"bigram memorised\n")

    def wer(rows, mu, switch, lam):
        e = sum(Levenshtein.distance(d["ref"], score_paths(d, lm, mu, switch, lam)[0])
                for d in rows)
        return 100.0 * e / sum(len(d["ref"]) for d in rows)

    mus = [float(x) for x in a.mus.split(",") if x.strip()]
    lams = [float(x) for x in a.lams.split(",") if x.strip()]
    print(f"{'mu':>6}{'lam':>7}{'dev 0-switch':>15}{'dev 1-switch':>15}")
    best = None
    for mu in mus:
        for lam in lams:
            w0, w1 = wer(dev, mu, False, lam), wer(dev, mu, True, lam)
            print(f"{mu:>6.2f}{lam:>7.2f}{w0:>15.2f}{w1:>15.2f}")
            if best is None or w1 < best[2]:
                best = (mu, lam, w1)
    mu, lam = best[0], best[1]
    print(f"\nbest on dev: mu {mu}, lam {lam}\n")

    R = sum(len(d["ref"]) for d in test)
    rov = 100.0 * sum(Levenshtein.distance(
        d["ref"], compose.rover(d["slots"], float(d["k"]), A.ROVER_DEFAULT["alpha"],
                                A.ROVER_DEFAULT["eps"])) for d in test) / R
    cand = 100.0 * sum(min(Levenshtein.distance(d["ref"], [w for w in (d["M"][t][c]
                       for t in range(len(d["M"]))) if w != EPS]) for c in range(d["k"]))
                       for d in test) / R
    print(f"{'on the held-out sets':<34}{'WER':>8}")
    print(f"  {'ROVER as shipped':<32}{rov:>8.2f}")
    print(f"  {'best whole candidate (oracle)':<32}{cand:>8.2f}")
    print(f"  {'scored 0-switch, conf only':<32}{wer(test, 0.0, False, 0.0):>8.2f}")
    print(f"  {'scored 0-switch, tuned':<32}{wer(test, mu, False, lam):>8.2f}")
    print(f"  {'scored 1-switch, tuned':<32}{wer(test, mu, True, lam):>8.2f}")
    print("\nIf the scored rows cannot get near ROVER, the decoder emits nothing that ranks")
    print("whole paths, and the one-switch oracle stays out of reach whatever searches it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
