#!/usr/bin/env python3
"""Everything that survived, in one pipeline, against Whisfusion's own selectors.

Pipeline: K=32 PDD candidates -> confusion network -> per-slot convex model with the
neighbour bigram and the step-zero acoustic features (tools/slot_eval.py). Baselines from the
same 32 candidates: the first candidate, upstream Whisfusion's pick (mean confidence), MBR,
conf + lambda*MBR (lambda tuned), ROVER shipped and ROVER tuned.

Set-level cross-validation so every non-dev utterance is scored exactly once by a model that
never saw its set: the 11 test sets are split into folds, dev sets always train. Per fold the
bigram, the weights, ROVER's alpha/eps and lambda are all fitted on the training sets only.

    python3 tools/final_compare.py --cache results/audio_cache.pkl \\
        --dumps_root results/campaign-2026-09-20/dumps --seeds 0,1,2
"""

from __future__ import annotations

import argparse
import gzip
import json
import pickle
import random
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np
from rapidfuzz.distance import Levenshtein

import crf_rover as F
import slot_lr as L
import slot_eval as S
from scorers import normalize

FOLDS = (("ls-test-clean", "ami", "earnings22", "ls-tc-babble0"),
         ("ls-test-other", "common_voice", "spgispeech", "ls-tc-white5"),
         ("gigaspeech", "voxpopuli", "ls-tc-babble5"))
LAMBDAS = (0.25, 0.5, 1.0, 1.5, 3.0)
EPS = S.EPS


def load_candidates(root, data, k):
    out = {}
    for s in {d["set"] for d in data}:
        for p in sorted(Path(root).glob(f"whisfusion__{s}__s*__main/main.jsonl.gz")):
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                for line in fh:
                    r = json.loads(line)
                    out[(s, r["id"])] = r["candidates"][:k]
    return out


def whole(cands):
    """Word lists and per-candidate scores for the whole-candidate selectors."""
    toks = [normalize(c["text"]).split() for c in cands]
    n = len(toks)
    D = [[Levenshtein.distance(toks[j], toks[i]) / max(len(toks[j]), 1) for j in range(n)]
         for i in range(n)]
    mbr = [-sum(D[i][j] for j in range(n) if j != i) / max(n - 1, 1) for i in range(n)]
    conf = [c["avg_conf"] for c in cands]
    return toks, conf, mbr


def argmax(x):
    return max(range(len(x)), key=lambda i: x[i])


def fit_arm(tr, lm, akey, a):
    pre = [S.prepare(d, akey, lm) for d in tr]
    Xs = [X for sl in pre for (_, X, g) in sl if g is not None]
    gs = [g for sl in pre for (_, _, g) in sl if g is not None]
    A = np.concatenate(Xs)
    mu, sd = A.mean(0), A.std(0) + 1e-9
    w, loss = L.fit([(X - mu) / sd for X in Xs], gs, a.lam, a.iters, a.lr)
    return (w, mu, sd, loss)


def apply_arm(d, model, akey, lm):
    w, mu, sd, _ = model
    return [words[int(np.argmax(((X - mu) / sd) @ w))] for words, X, _ in S.prepare(d, akey, lm)]


def run_seed(data, cand, a, seed):
    akey = f"aslots_{a.audio}"
    hyps = {}   # (set, id) -> {arm: word list}
    log = []
    for fold in FOLDS:
        ev = [d for d in data if d["set"] in fold]
        pool = [d for d in data if d["set"] not in fold]
        rng = random.Random(seed)
        rng.shuffle(pool)
        n_lm = min(a.lm_utts, len(pool) // 3)
        lm = F.Bigram([d["ref"] for d in pool[:n_lm]])
        tr = pool[n_lm:]

        best = min(((al, e, sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, e, S.POWER)
                                            for s in d["slots"]], d["ref"]) for d in tr))
                    for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])
        al, ep = best[0], best[1]
        W = {}
        for d in pool:
            W[(d["set"], d["id"])] = whole(cand[(d["set"], d["id"])])

        def cm_edits(lam):
            tot = 0
            for d in pool:
                toks, conf, mbr = W[(d["set"], d["id"])]
                i = argmax([c + lam * m for c, m in zip(conf, mbr)])
                tot += Levenshtein.distance(d["ref"], toks[i])
            return tot
        lam = min(LAMBDAS, key=cm_edits)

        models = {"slot model": fit_arm(tr, None, "", a),
                  "+ neighbour": fit_arm(tr, lm, "", a),
                  "+ neighbour + acoustic (final)": fit_arm(tr, lm, akey, a)}
        losses = {k: m[3] for k, m in models.items()}
        warn = [k for k, v in losses.items() if k != "slot model" and v > losses["slot model"] + 1e-3]
        log.append(f"  fold {'/'.join(fold)}: ROVER alpha {al} eps {ep}, lambda {lam}, "
                   f"train loss " + ", ".join(f"{v:.4f}" for v in losses.values())
                   + (f"  !! not converged: {warn}" if warn else ""))

        for d in ev:
            toks, conf, mbr = whole(cand[(d["set"], d["id"])])
            tot = float(d["n_cand"])
            h = {
                "first candidate": toks[0],
                "Whisfusion upstream (mean conf)": toks[argmax(conf)],
                "MBR": toks[argmax(mbr)],
                f"conf + lambda*MBR": toks[argmax([c + lam * m for c, m in zip(conf, mbr)])],
                "ROVER shipped": [F.rover_pick(s, tot, 0.5, 0.7, None) for s in d["slots"]],
                "ROVER tuned": [F.rover_pick(s, tot, al, ep, S.POWER) for s in d["slots"]],
            }
            h["slot model"] = apply_arm(d, models["slot model"], "", None)
            h["+ neighbour"] = apply_arm(d, models["+ neighbour"], "", lm)
            h["+ neighbour + acoustic (final)"] = apply_arm(d, models["+ neighbour + acoustic (final)"], akey, lm)
            h["candidate oracle"] = min(toks, key=lambda t: Levenshtein.distance(d["ref"], t))
            h["slot oracle"] = [r if (r in s or r == EPS) else F.rover_pick(s, tot, al, ep, S.POWER)
                                for s, r in zip(d["slots"], d["ref_by_slot"])]
            hyps[(d["set"], d["id"])] = h
    return hyps, log


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--dumps_root", required=True)
    ap.add_argument("--audio", default="w2")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--lm_utts", type=int, default=1200)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    a = ap.parse_args()

    data = pickle.loads(Path(a.cache).read_bytes())
    cand = load_candidates(a.dumps_root, data, a.k)
    data = [d for d in data if (d["set"], d["id"]) in cand]
    test = [d for d in data if any(d["set"] in f for f in FOLDS)]
    refs = [d["ref"] for d in test]
    rl = np.array([len(r) for r in refs], float)
    R = rl.sum()
    print(f"{len(test)} scored utterances on {len({d['set'] for d in test})} sets "
          f"({int(R)} words), {len(data) - len(test)} dev-only; K={a.k}; "
          f"set-level {len(FOLDS)}-fold CV; seeds {a.seeds}\n", flush=True)

    per_seed = []
    for seed in [int(x) for x in a.seeds.split(",")]:
        hyps, log = run_seed(data, cand, a, seed)
        print(f"seed {seed}"); print("\n".join(log), flush=True)
        E = {k: np.array([F.edits_of(hyps[(d['set'], d['id'])][k], d["ref"]) for d in test], float)
             for k in hyps[(test[0]["set"], test[0]["id"])]}
        per_seed.append(E)
        if len(per_seed) == 1:
            hyps0 = hyps

    arms = list(per_seed[0].keys())
    fin = "+ neighbour + acoustic (final)"
    print(f"\npooled WER over all {len(test)} scored utterances (mean over seeds; the "
          f"baselines without training do not depend on the seed)\n")
    print(f"{'method':<34}{'WER':>7}{'rel. vs MBR':>13}{'rel. vs ROVER t.':>18}")
    mbr = np.mean([100 * E["MBR"].sum() / R for E in per_seed])
    rt = np.mean([100 * E["ROVER tuned"].sum() / R for E in per_seed])
    for k in arms:
        w = np.mean([100 * E[k].sum() / R for E in per_seed])
        print(f"{k:<34}{w:>7.2f}{100 * (mbr - w) / mbr:>12.1f}%{100 * (rt - w) / rt:>17.1f}%")

    print(f"\npaired bootstrap of the final pipeline, per seed (positive = final is better)")
    for base in ("Whisfusion upstream (mean conf)", "MBR", "conf + lambda*MBR", "ROVER shipped",
                 "ROVER tuned", "+ neighbour"):
        cells = []
        for i, E in enumerate(per_seed):
            o, lo, hi = S.bootstrap(E[base], E[fin], rl, seed=i)
            cells.append(f"{o:+.2f} [{lo:+.2f},{hi:+.2f}]")
        print(f"  vs {base:<32}" + "   ".join(cells))

    sets = [s for f in FOLDS for s in f]
    show = ["Whisfusion upstream (mean conf)", "MBR", "ROVER tuned", fin, "slot oracle"]
    print(f"\nper set, WER (seed-mean)   {'':>0}" + "".join(f"{k[:14]:>16}" for k in show)
          + f"{'final vs ROVER t.':>26}")
    for s in sets:
        ix = np.array([i for i, d in enumerate(test) if d["set"] == s])
        if not len(ix):
            continue
        line = f"{s:<16}{len(ix):>5} utts "
        for k in show:
            line += f"{np.mean([100 * E[k][ix].sum() / rl[ix].sum() for E in per_seed]):>16.2f}"
        o, lo, hi = S.bootstrap(per_seed[0]["ROVER tuned"][ix], per_seed[0][fin][ix], rl[ix])
        flag = "*" if lo > 0 else (" " if hi >= 0 else "-")
        line += f"{f'{o:+.2f} [{lo:+.2f},{hi:+.2f}]{flag}':>26}"
        print(line)
    print("  (last column: seed 0; * = interval above zero, - = below zero)")

    print("\nsubstitutions / insertions / deletions, WER points (seed 0)")
    for k in ("Whisfusion upstream (mean conf)", "MBR", "ROVER tuned", fin, "slot oracle"):
        sid = np.sum([S.sid(d["ref"], [w for w in hyps0[(d["set"], d["id"])][k] if w != EPS])
                      for d in test], axis=0) * 100.0 / R
        print(f"  {k:<34}" + "  ".join(f"{n} {v:5.2f}" for n, v in zip(("sub", "ins", "del"), sid)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
