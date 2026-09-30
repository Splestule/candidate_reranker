#!/usr/bin/env python3
"""Quality against cost: Whisfusion's own recipe against the final pipeline, over K.

Upstream Whisfusion samples K=15 candidates and keeps the one with the highest mean
confidence. For every K the network is rebuilt from the first K candidates of the dump
(flat sampling draws them independently, so the first K are a valid K-sample), the final
pipeline is refitted at that K, and everything is scored with the set-level cross-validation
of tools/final_compare.py. At K=32 an iROVER-style arm is added: the same features, but a
boosted-stump classifier (Hillard et al. 2007 use AdaBoost over stumps) instead of the
convex model.

Cost is the measured T4 decode time per candidate from run 6 (bench a4de8c4), relative to
upstream K=15; tree-early at K=32 is 1.69x cheaper than flat K=32 (run 8).

    python3 tools/k_curve.py --cand results/cand_audio.pkl --ks 1,2,4,8,15,32
"""

from __future__ import annotations

import argparse
import pickle
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

# T4 decode seconds for 200 test-clean utterances at K (run 6); linear beyond K=5
BENCH = {1: 26.0, 3: 36.2, 5: 60.4, 10: 119.7, 15: 180.5, 20: 236.5, 30: 357.8}


def cost(k):
    ks = sorted(BENCH)
    if k in BENCH:
        return BENCH[k]
    if k > ks[-1]:
        return BENCH[30] + (k - 30) * (BENCH[30] - BENCH[20]) / 10
    lo = max(x for x in ks if x < k)
    hi = min(x for x in ks if x > k)
    return BENCH[lo] + (k - lo) * (BENCH[hi] - BENCH[lo]) / (hi - lo)


def build(r, k):
    """Network record at K plus the whole-candidate views of the same K candidates."""
    raw = r["cands"][:k]
    toks = [c["words"] for c in raw]
    n = len(toks)
    Dm = [[Levenshtein.distance(toks[j], toks[i]) / max(len(toks[j]), 1) for j in range(n)] for i in range(n)]
    mbr = [-sum(Dm[i][j] for j in range(n) if j != i) / max(n - 1, 1) for i in range(n)] if n > 1 else [0.0]
    conf = [c["avg_conf"] for c in raw]
    ok = [c for c in raw if c["conf"] is not None]
    if not ok:
        return None
    cands = [c["words"] for c in ok]
    bb = compose.central_index(cands)
    by_slot = D.reference_by_slot(cands, bb, r["ref"])
    slots = compose.confusion_network(cands, bb, [c["conf"] for c in ok], None)
    aslots = compose.confusion_network(cands, bb, [c["aud"] for c in ok], None)
    if len(by_slot) != len(slots):
        return None
    return dict(set=r["set"], id=r["id"], ref=r["ref"], n_cand=len(ok), ref_by_slot=by_slot,
                slots=[{w: list(v) for w, v in s.items()} for s in slots],
                aslots_w2=[{w: list(v) for w, v in s.items()} for s in aslots],
                toks=toks, conf=conf, mbr=mbr)


def fit_boost(tr, lm, akey):
    from sklearn.ensemble import HistGradientBoostingClassifier
    X, y = [], []
    for d in tr:
        for words, Xs, g in S.prepare(d, akey, lm):
            if g is None:
                continue
            X.append(Xs)
            y += [1 if i == g else 0 for i in range(len(words))]
    clf = HistGradientBoostingClassifier(max_depth=1, max_iter=400, learning_rate=0.1, random_state=0)
    clf.fit(np.concatenate(X), np.array(y))
    return clf


def apply_boost(ds, clf, akey, lm):
    """One predict call for a whole fold; per-slot calls cost 400 tree walks each."""
    pre = [S.prepare(d, akey, lm) for d in ds]
    p = clf.predict_proba(np.concatenate([X for sl in pre for (_, X, _) in sl]))[:, 1]
    out, at = [], 0
    for sl in pre:
        h = []
        for words, X, _ in sl:
            h.append(words[int(np.argmax(p[at:at + len(words)]))])
            at += len(words)
        out.append(h)
    return out


def run_k(recs, k, a, with_boost):
    data = [x for x in (build(r, k) for r in recs) if x is not None]
    test = [d for d in data if any(d["set"] in f for f in FC.FOLDS)]
    akey = "aslots_w2"
    hy = {}
    for fold in FC.FOLDS:
        ev = [d for d in data if d["set"] in fold]
        pool = [d for d in data if d["set"] not in fold]
        random.Random(a.seed).shuffle(pool)
        n_lm = min(a.lm_utts, len(pool) // 3)
        lm = F.Bigram([d["ref"] for d in pool[:n_lm]])
        tr = pool[n_lm:]
        al, ep, _ = min(((al, e, sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, e, S.POWER)
                                                  for s in d["slots"]], d["ref"]) for d in tr))
                         for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])
        fin = FC.fit_arm(tr, lm, akey, a)
        boost = fit_boost(tr, lm, akey) if with_boost else None
        bh = apply_boost(ev, boost, akey, lm) if with_boost else None
        for n_d, d in enumerate(ev):
            tot = float(d["n_cand"])
            h = {"Whisfusion upstream (mean conf)": d["toks"][FC.argmax(d["conf"])],
                 "MBR": d["toks"][FC.argmax(d["mbr"])],
                 "ROVER tuned": [F.rover_pick(s, tot, al, ep, S.POWER) for s in d["slots"]],
                 "final": FC.apply_arm(d, fin, akey, lm),
                 "candidate oracle": min(d["toks"], key=lambda t: Levenshtein.distance(d["ref"], t)),
                 "slot oracle": [r if (r in s or r == S.EPS) else F.rover_pick(s, tot, al, ep, S.POWER)
                                 for s, r in zip(d["slots"], d["ref_by_slot"])]}
            if boost is not None:
                h["iROVER-style (boosted stumps)"] = bh[n_d]
            hy[(d["set"], d["id"])] = h
    keys = sorted(hy)
    refs = {(d["set"], d["id"]): d["ref"] for d in test}
    E = {m: np.array([F.edits_of(hy[kk][m], refs[kk]) for kk in keys], float) for m in hy[keys[0]]}
    rl = np.array([len(refs[kk]) for kk in keys], float)
    return keys, E, rl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    ap.add_argument("--ks", default="1,2,4,8,15,32")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lm_utts", type=int, default=1200)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    a = ap.parse_args()
    recs = pickle.loads(Path(a.cand).read_bytes())
    ks = [int(x) for x in a.ks.split(",")]
    res = {}
    for k in ks:
        res[k] = run_k(recs, k, a, with_boost=(k == max(ks)))
        print(f"K={k}: {len(res[k][0])} scored utterances", flush=True)

    # same utterances at every K, so rows are comparable
    common = set.intersection(*[set(v[0]) for v in res.values()])
    ref_k = 15 if 15 in res else ks[0]
    base_cost = cost(15)
    print(f"\n{len(common)} utterances scored at every K; cost = T4 decode time relative to "
          f"upstream Whisfusion (K=15), from run 6; tree-early = flat K=32 / 1.69\n")
    rows = []
    for k in ks:
        keys, E, rl = res[k]
        ix = np.array([i for i, kk in enumerate(keys) if kk in common])
        R = rl[ix].sum()
        for m, e in E.items():
            rows.append((k, m, 100 * e[ix].sum() / R, e[ix], rl[ix]))
    print(f"{'K':>3}  {'method':<34}{'WER':>7}{'cost':>7}")
    for k, m, w, _, _ in rows:
        c = cost(k) / base_cost
        print(f"{k:>3}  {m:<34}{w:>7.2f}{c:>7.2f}")
    if 32 in res:
        print(f"{32:>3}  {'final, tree-early decode':<34}{'(see tree_compare)':>7}{cost(32) / 1.69 / base_cost:>7.2f}")

    up = next(r for r in rows if r[0] == ref_k and r[1].startswith("Whisfusion"))
    print(f"\npaired bootstrap against upstream Whisfusion (K={ref_k}, mean conf), positive = better")
    for k, m, w, e, rlx in rows:
        if m in ("final", "MBR", "ROVER tuned") or m.startswith("iROVER"):
            o, lo, hi = S.bootstrap(up[3], e, rlx)
            print(f"  K={k:<3}{m:<34}{o:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    if 32 in res:
        keys, E, rl = res[32]
        ix = np.array([i for i, kk in enumerate(keys) if kk in common])
        for m in [x for x in E if x.startswith("iROVER")]:
            o, lo, hi = S.bootstrap(E[m][ix], E["final"][ix], rl[ix])
            print(f"\nK=32 final vs {m}: {o:+.2f} [{lo:+.2f}, {hi:+.2f}]  (positive = final better)")
            o, lo, hi = S.bootstrap(E["ROVER tuned"][ix], E[m][ix], rl[ix])
            print(f"K=32 {m} vs ROVER tuned: {o:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
