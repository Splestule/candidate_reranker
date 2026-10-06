#!/usr/bin/env python3
"""The composition pipeline on a second parallel decoder: Drax (flow matching, K=16 samples).

Offline, from the campaign dumps; nothing is decoded again. Same pipeline as for Whisfusion
minus the step-zero acoustic features, which are Whisfusion-specific: confusion network ->
slot model with the neighbour bigram. Baselines from the same K candidates: upstream (mean
confidence), MBR, ROVER tuned, iROVER-style (boosted stumps, same features), oracles.

English: set-level 3-fold CV over the 11 test sets (dev sets always train), trained on s00,
tested on s01 + s02. Multilingual FLEURS (en de fr es it pt): leave one language out; the
slot model and ROVER are fitted on the other languages (s01/s02), the bigram of the held-out
language comes from its own s00, and its s01/s02 are tested.

    python3 tools/drax_eval.py --dumps_root results/campaign-2026-09-20/dumps | tee results/drax_eval.txt
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

import compose
import decompose as D
import crf_rover as F
import slot_lr as L
import slot_eval as S
import final_compare as FC
from scorers import normalize

UP, MBR, ROV, IRO, SLOT, FIN, ORA, SORA = ("upstream conf", "MBR", "ROVER tuned", "iROVER-style",
                                           "slot model", "final (no acoustic)", "candidate oracle",
                                           "slot oracle")
DEV = ("ls-dev-clean", "ls-dev-other")
TEST = [s for f in FC.FOLDS for s in f]
FLEURS = ("fleurs-en", "fleurs-de", "fleurs-fr", "fleurs-es", "fleurs-it", "fleurs-pt")


def load(root, sets):
    out = []
    for s in sets:
        for p in sorted(Path(root).glob(f"drax__{s}__s*__main/main.jsonl.gz")):
            shard = int(p.parent.name.split("__")[2][1:])
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                for line in fh:
                    r = json.loads(line)
                    out.append(dict(set=s, id=r["id"], shard=shard, lang=r.get("lang", "en"),
                                    ref=normalize(r["reference"]).split(), cands=r["candidates"]))
    return out


def build(r, k):
    raw = r["cands"][:k]
    toks = [normalize(c["text"]).split() for c in raw]
    n = len(toks)
    Dm = [[Levenshtein.distance(toks[j], toks[i]) / max(len(toks[j]), 1) for j in range(n)] for i in range(n)]
    mbr = [-sum(Dm[i][j] for j in range(n) if j != i) / max(n - 1, 1) for i in range(n)] if n > 1 else [0.0]
    ok = [(t, c["word_conf"]) for t, c in zip(toks, raw)
          if c.get("word_conf") is not None and len(c["word_conf"]) == len(t)]
    if not ok or not r["ref"]:
        return None
    cands = [t for t, _ in ok]
    bb = compose.central_index(cands)
    by_slot = D.reference_by_slot(cands, bb, r["ref"])
    slots = compose.confusion_network(cands, bb, [c for _, c in ok], None)
    if len(by_slot) != len(slots):
        return None
    return dict(set=r["set"], id=r["id"], shard=r["shard"], lang=r["lang"], ref=r["ref"],
                n_cand=len(ok), ref_by_slot=by_slot, slots=[{w: list(v) for w, v in s.items()} for s in slots],
                toks=toks, conf=[c["avg_conf"] for c in raw], mbr=mbr)


def fit_slot(tr, lmf, a):
    pre = [S.prepare(d, "", lmf(d)) for d in tr]
    Xs = [X for sl in pre for (_, X, g) in sl if g is not None]
    gs = [g for sl in pre for (_, _, g) in sl if g is not None]
    A = np.concatenate(Xs)
    mu, sd = A.mean(0), A.std(0) + 1e-9
    w, _ = L.fit([(X - mu) / sd for X in Xs], gs, a.lam, a.iters, a.lr)
    return w, mu, sd


def apply_slot(d, m, lm):
    w, mu, sd = m
    return [words[int(np.argmax(((X - mu) / sd) @ w))] for words, X, _ in S.prepare(d, "", lm)]


def fit_boost(tr, lmf):
    from sklearn.ensemble import HistGradientBoostingClassifier
    Xs, y = [], []
    for d in tr:
        for words, X, g in S.prepare(d, "", lmf(d)):
            if g is None:
                continue
            Xs.append(X)
            y += [1 if i == g else 0 for i in range(len(words))]
    clf = HistGradientBoostingClassifier(max_depth=1, max_iter=400, learning_rate=0.1, random_state=0)
    clf.fit(np.concatenate(Xs), np.array(y))
    return clf


def apply_boost(d, clf, lm):
    sl = S.prepare(d, "", lm)
    p = clf.predict_proba(np.concatenate([X for _, X, _ in sl]))[:, 1]
    out, at = [], 0
    for words, X, _ in sl:
        out.append(words[int(np.argmax(p[at:at + len(words)]))])
        at += len(words)
    return out


def tune_rover(tr):
    return min(((al, e, sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, e, S.POWER)
                                         for s in d["slots"]], d["ref"]) for d in tr))
                for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])[:2]


def fit_all(tr, lmf, a):
    return dict(rover=tune_rover(tr), slot=fit_slot(tr, lambda d: None, a), fin=fit_slot(tr, lmf, a),
                boost=fit_boost(tr, lmf))


def apply_all(d, m, lm):
    al, ep = m["rover"]
    tot = float(d["n_cand"])
    return {UP: d["toks"][FC.argmax(d["conf"])], MBR: d["toks"][FC.argmax(d["mbr"])],
            ROV: [F.rover_pick(s, tot, al, ep, S.POWER) for s in d["slots"]],
            IRO: apply_boost(d, m["boost"], lm), SLOT: apply_slot(d, m["slot"], None),
            FIN: apply_slot(d, m["fin"], lm),
            ORA: min(d["toks"], key=lambda t: Levenshtein.distance(d["ref"], t)),
            SORA: [r if (r in s or r == S.EPS) else F.rover_pick(s, tot, al, ep, S.POWER)
                   for s, r in zip(d["slots"], d["ref_by_slot"])]}


def english(recs, k, seed, a):
    B = [b for b in (build(r, k) for r in recs) if b is not None]
    test = [d for d in B if d["set"] in TEST and d["shard"] >= 1]
    H = {}
    for fold in FC.FOLDS:
        pool = [d for d in B if d["shard"] == 0 and d["set"] not in fold] + \
               [d for d in B if d["set"] in DEV]
        random.Random(seed).shuffle(pool)
        n_lm = min(a.lm_utts, len(pool) // 3)
        lm = F.Bigram([d["ref"] for d in pool[:n_lm]])
        m = fit_all(pool[n_lm:], lambda d: lm, a)
        for d in test:
            if d["set"] in fold:
                H[(d["set"], d["id"])] = apply_all(d, m, lm)
    return test, H


def multilingual(recs, k, a):
    B = [b for b in (build(r, k) for r in recs) if b is not None]
    lms = {s: F.Bigram([d["ref"] for d in B if d["set"] == s and d["shard"] == 0]) for s in FLEURS}
    ev = [d for d in B if d["shard"] >= 1]
    H = {}
    for held in FLEURS:
        m = fit_all([d for d in ev if d["set"] != held], lambda d: lms[d["set"]], a)
        for d in ev:
            if d["set"] == held:
                H[(d["set"], d["id"])] = apply_all(d, m, lms[held])
    return ev, H


def report(title, test, Hs, a):
    rl = np.array([len(d["ref"]) for d in test], float)
    R = rl.sum()
    keys = [(d["set"], d["id"]) for d in test]
    E = [{m: np.array([F.edits_of(H[kk][m], d["ref"]) for kk, d in zip(keys, test)], float)
          for m in H[keys[0]]} for H in Hs]
    print(f"\n== {title}: {len(test)} utterances, {int(R)} words, {len({d['set'] for d in test})} sets")
    up = np.mean([100 * e[UP].sum() / R for e in E])
    print(f"  {'method':<22}{'WER':>7}{'sd':>6}{'rel. vs upstream':>18}")
    for m in E[0]:
        ws = [100 * e[m].sum() / R for e in E]
        print(f"  {m:<22}{np.mean(ws):7.2f}{np.std(ws):6.2f}{100 * (up - np.mean(ws)) / up:17.1f}%")
    print("  paired bootstrap, final minus baseline (positive = final better), per seed")
    for b in (UP, MBR, ROV, IRO, SLOT):
        cells = []
        for i, e in enumerate(E):
            o, lo, hi = S.bootstrap(e[b], e[FIN], rl, seed=i)
            cells.append(f"{o:+.2f} [{lo:+.2f},{hi:+.2f}]{'*' if lo > 0 else ('-' if hi < 0 else ' ')}")
        print(f"    vs {b:<18}" + "  ".join(cells))
    print(f"  per set (seed 0){'':<4}" + "".join(f"{m[:12]:>14}" for m in (UP, MBR, ROV, IRO, FIN, SORA))
          + f"{'final vs ROVER':>24}")
    for s in sorted({d["set"] for d in test}, key=lambda s: (s not in TEST, s)):
        ix = np.array([i for i, d in enumerate(test) if d["set"] == s])
        Rs = rl[ix].sum()
        row = "".join(f"{100 * E[0][m][ix].sum() / Rs:14.2f}" for m in (UP, MBR, ROV, IRO, FIN, SORA))
        o, lo, hi = S.bootstrap(E[0][ROV][ix], E[0][FIN][ix], rl[ix])
        print(f"  {s:<16}{len(ix):>4}{row}{f'{o:+.2f} [{lo:+.2f},{hi:+.2f}]':>24}")
    return E


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps_root", required=True)
    ap.add_argument("--ks", default="4,8,16")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--lm_utts", type=int, default=1200)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--skip", default="", help="'en' or 'ml' to skip a part")
    a = ap.parse_args()
    seeds = [int(x) for x in a.seeds.split(",")]
    ks = [int(x) for x in a.ks.split(",")]
    if a.skip != "en":
        recs = load(a.dumps_root, TEST + list(DEV))
        for k in ks:
            runs = [english(recs, k, s, a) for s in seeds]
            report(f"Drax K={k}, English, set-level CV, test s01+s02", runs[0][0], [h for _, h in runs], a)
            sys.stdout.flush()
    if a.skip != "ml":
        recs = load(a.dumps_root, FLEURS)
        for k in ks:
            test, H = multilingual(recs, k, a)
            report(f"Drax K={k}, FLEURS 6 languages, leave one language out, test s01+s02", test, [H], a)
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
