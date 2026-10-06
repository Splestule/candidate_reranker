#!/usr/bin/env python3
"""Votes from distributions instead of argmax tokens (docs/rb_voting.md).

Same candidates, same confusion network; only the votes change. A row that holds word u in a
slot normally gives one vote to u. Here it gives each word v of the slot its probability
p(first token of v) under the distribution the row's token was last predicted from,
renormalised over the slot's words; deletions keep their hard vote. lambda mixes the two
(0 = hard votes, 1 = soft).

Methods per arm: upstream, ROVER tuned (hard), ROVER-RB (lambda tuned with alpha and eps),
final (slot model + neighbour bigram + acoustic, hard), final + RB (three soft-vote columns
added), slot oracle. Set-level CV as everywhere: train on s00 of the sets outside the fold,
test on s01 of the fold's sets.

    python3 tools/rb_eval.py --cand results/rb/cand_rb.pkl | tee results/rb/rb_eval.txt
"""

from __future__ import annotations

import argparse
import pickle
import random
import sys
from collections import Counter, defaultdict
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
import k_curve as KC

EPS = S.EPS
LAMBDAS = (0.25, 0.5, 0.75, 1.0)
TEMPS = (1.0, 2.0, 4.0)
UP, ROV, ROVRB, FIN, FINRB, SORA = ("upstream conf", "ROVER tuned", "ROVER-RB", "final", "final + RB",
                                    "slot oracle")


def holders(cands, bb):
    """Per slot (confusion_network's order): list of (candidate, word position or None)."""
    ref = cands[bb]
    n = len(ref)
    sub = [[] for _ in range(n)]
    ins = [[] for _ in range(n + 1)]
    for ci, c in enumerate(cands):
        for tag, i1, i2, j1, j2 in Levenshtein.opcodes(ref, c):
            if tag == "equal":
                for d in range(i2 - i1):
                    sub[i1 + d].append((ci, j1 + d))
            elif tag == "replace":
                for pos in range(i1, i2):
                    off = j1 + (pos - i1)
                    sub[pos].append((ci, off if off < j2 else None))
                for off in range(j1 + (i2 - i1), j2):
                    ins[i2].append((ci, off))
            elif tag == "delete":
                for pos in range(i1, i2):
                    sub[pos].append((ci, None))
            elif tag == "insert":
                for off in range(j1, j2):
                    ins[i1].append((ci, off))
    out = []
    for i in range(n):
        if ins[i]:
            out.append(ins[i] + [(ci, None) for ci in range(len(cands)) if ci not in {c for c, _ in ins[i]}])
        out.append(sub[i])
    if ins[n]:
        out.append(ins[n] + [(ci, None) for ci in range(len(cands)) if ci not in {c for c, _ in ins[n]}])
    return out


def soft_votes(cands, dists, bb, slots):
    """Per slot: word -> (soft vote at each of TEMPS, summed unnormalised probability).
    The decoder is sharp (most kept tokens near p = 1), so the votes are also taken from
    p ** (1 / T), renormalised over the slot's words."""
    ft = defaultdict(Counter)
    for c, ds in zip(cands, dists):
        if ds is not None:
            for w, d in zip(c, ds):
                ft[w][d[0]] += 1
    first = {w: cnt.most_common(1)[0][0] for w, cnt in ft.items()}
    out = []
    for slot, hs in zip(slots, holders(cands, bb)):
        real = [w for w in slot if w != EPS]
        sv = {w: [0.0] * len(TEMPS) for w in slot}
        mass = {w: 0.0 for w in slot}
        for ci, off in hs:
            own = EPS if off is None else cands[ci][off]
            ds = dists[ci]
            if off is None or ds is None or own not in first:
                sv.setdefault(own, [0.0] * len(TEMPS))
                sv[own] = [x + 1.0 for x in sv[own]]
                continue
            pm = dict(zip(ds[off][1], ds[off][2]))
            groups = defaultdict(list)
            for w in real:
                groups[first.get(w)].append(w)
            p = {}
            for t, ws in groups.items():
                pt = pm.get(t, 0.0) if t is not None else 0.0
                if own in ws:
                    p.update({w: (pt if w == own else 0.0) for w in ws})
                else:
                    p.update({w: pt / len(ws) for w in ws})
            if sum(p.values()) < 1e-6:
                sv[own] = [x + 1.0 for x in sv[own]]
                continue
            for ti, T in enumerate(TEMPS):
                q = {w: x ** (1.0 / T) for w, x in p.items()}
                z = sum(q.values())
                for w, x in q.items():
                    sv[w][ti] += x / z
            for w, x in p.items():
                mass[w] += x
        out.append({w: (sv.get(w, [0.0] * len(TEMPS)), mass.get(w, 0.0)) for w in slot})
    return out


def build(r, k):
    b = KC.build(r, k)
    if b is None:
        return None
    ok = [c for c in r["cands"][:k] if c["conf"] is not None]
    cands = [c["words"] for c in ok]
    bb = compose.central_index(cands)
    b["soft"] = soft_votes(cands, [c.get("dist") for c in ok], bb, b["slots"])
    b.update(shard=r["shard"])
    return b


def mixed(d, lam, ti):
    out = []
    for s, sv in zip(d["slots"], d["soft"]):
        m = {}
        for w, (v, cs) in s.items():
            nv = (1 - lam) * v + lam * sv[w][0][ti]
            m[w] = [nv, cs * nv / v if v > 0 else 0.0]
        out.append(m)
    return out


def tune_rover_rb(tr, al, e):
    """lambda and T on top of the hard ROVER's alpha and eps (the full grid is 50x slower)."""
    best = None
    for lam in LAMBDAS:
        for ti in range(len(TEMPS)):
            ed = sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, e, S.POWER)
                                 for s in mixed(d, lam, ti)], d["ref"]) for d in tr)
            if best is None or ed < best[0]:
                best = (ed, lam, ti)
    return best[1:]


def prepare_rb(d, akey, lm):
    out = []
    tot = float(d["n_cand"])
    for (words, X, g), sv in zip(S.prepare(d, akey, lm), d["soft"]):
        zero = ([0.0] * len(TEMPS), 0.0)
        f = np.array([sv.get(w, zero)[0] for w in words]) / tot
        mass = np.array([sv.get(w, zero)[1] / tot for w in words])
        out.append((words, np.hstack([X, f, f - f.max(0, keepdims=True), mass[:, None]]), g))
    return out


def fit(tr, akey, lm, a, prep):
    pre = [prep(d, akey, lm) for d in tr]
    Xs = [X for sl in pre for (_, X, g) in sl if g is not None]
    gs = [g for sl in pre for (_, _, g) in sl if g is not None]
    A = np.concatenate(Xs)
    mu, sd = A.mean(0), A.std(0) + 1e-9
    w, _ = L.fit([(X - mu) / sd for X in Xs], gs, a.lam, a.iters, a.lr)
    return w, mu, sd


def apply(d, m, akey, lm, prep):
    w, mu, sd = m
    return [words[int(np.argmax(((X - mu) / sd) @ w))] for words, X, _ in prep(d, akey, lm)]


def diagnostics(B):
    """Slots where the reference word is in the network with at least two real words: how often
    the top of each vote picks it, and the vote share it gets."""
    n = hit_h = hit_s = ties = ties_s = 0
    sh_h, sh_s = [], []
    for d in B:
        for s, sv, r in zip(d["slots"], d["soft"], d["ref_by_slot"]):
            if r not in s or sum(w != EPS for w in s) < 2:
                continue
            n += 1
            hv = {w: v[0] for w, v in s.items()}
            top = max(hv.values())
            tie = sum(v == top for v in hv.values()) > 1
            hit_h += max(hv, key=hv.get) == r
            hit_s += max(sv, key=lambda w: sv[w][0][0]) == r
            ties += tie
            ties_s += tie and max(sv, key=lambda w: sv[w][0][0]) == r
            sh_h.append(hv[r] / d["n_cand"])
            sh_s.append(sv[r][0][0] / d["n_cand"])
    if n:
        print(f"  contested slots with the reference inside: {n}; top vote is the reference: hard "
              f"{100 * hit_h / n:.1f}%, soft {100 * hit_s / n:.1f}%; hard ties {100 * ties / n:.1f}% "
              f"(soft right on {100 * ties_s / max(ties, 1):.1f}% of them); mean share of the reference "
              f"hard {np.mean(sh_h):.3f}, soft {np.mean(sh_s):.3f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    ap.add_argument("--test_shard", type=int, default=1)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--lm_utts", type=int, default=1200)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    a = ap.parse_args()
    recs = pickle.loads(Path(a.cand).read_bytes())
    seeds = [int(x) for x in a.seeds.split(",")]
    akey = "aslots_w2"
    tests = [s for f in FC.FOLDS for s in f]
    arms = [x for x in ("flat-k4", "flat-k8", "tree-early-k8") if any(r["arm"] == x for r in recs)]
    E = {}
    for arm in arms:
        k = int(arm.split("-k")[-1])
        B = [b for b in (build(r, k) for r in recs if r["arm"] == arm) if b is not None]
        test = [d for d in B if d["shard"] == a.test_shard and d["set"] in tests]
        train = [d for d in B if d["shard"] != a.test_shard]
        print(f"\n== {arm}: test {len(test)} utterances (s{a.test_shard:02d}), train {len(train)}", flush=True)
        diagnostics(test)
        rl = np.array([len(d["ref"]) for d in test], float)
        for seed in seeds:
            H = {}
            for fold in FC.FOLDS:
                pool = [d for d in train if d["set"] not in fold]
                random.Random(seed).shuffle(pool)
                n_lm = min(a.lm_utts, len(pool) // 3)
                lm = F.Bigram([d["ref"] for d in pool[:n_lm]])
                tr = pool[n_lm:]
                al, ep = min(((al, e, sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, e, S.POWER)
                                                      for s in d["slots"]], d["ref"]) for d in tr))
                              for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])[:2]
                lam, ti = tune_rover_rb(tr, al, ep)
                mf = fit(tr, akey, lm, a, S.prepare)
                mr = fit(tr, akey, lm, a, prepare_rb)
                if seed == seeds[0]:
                    print(f"  fold {'/'.join(fold)}: ROVER alpha {al} eps {ep}; ROVER-RB lambda {lam} "
                          f"T {TEMPS[ti]}", flush=True)
                for d in test:
                    if d["set"] not in fold:
                        continue
                    tot = float(d["n_cand"])
                    H[(d["set"], d["id"])] = {
                        UP: d["toks"][FC.argmax(d["conf"])],
                        ROV: [F.rover_pick(s, tot, al, ep, S.POWER) for s in d["slots"]],
                        ROVRB: [F.rover_pick(s, tot, al, ep, S.POWER) for s in mixed(d, lam, ti)],
                        FIN: apply(d, mf, akey, lm, S.prepare),
                        FINRB: apply(d, mr, akey, lm, prepare_rb),
                        SORA: [r if (r in s or r == EPS) else F.rover_pick(s, tot, al, ep, S.POWER)
                               for s, r in zip(d["slots"], d["ref_by_slot"])]}
            for m in (UP, ROV, ROVRB, FIN, FINRB, SORA):
                E[(arm, seed, m)] = np.array([F.edits_of(H[(d["set"], d["id"])][m], d["ref"]) for d in test], float)
        R = rl.sum()
        for m in (UP, ROV, ROVRB, FIN, FINRB, SORA):
            ws = [100 * E[(arm, s, m)].sum() / R for s in seeds]
            print(f"  {m:<16}{np.mean(ws):7.2f}  (sd {np.std(ws):.2f})")
        for base, arm_m in ((ROV, ROVRB), (FIN, FINRB)):
            cells = []
            for s in seeds:
                o, lo, hi = S.bootstrap(E[(arm, s, base)], E[(arm, s, arm_m)], rl, seed=s)
                cells.append(f"{o:+.2f} [{lo:+.2f},{hi:+.2f}]{'*' if lo > 0 else ('-' if hi < 0 else ' ')}")
            print(f"  {arm_m} vs {base}: " + "  ".join(cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
