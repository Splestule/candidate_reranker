#!/usr/bin/env python3
"""Does consensus re-denoising (tools/refine.py) give the composition something new?

Same candidates, same frozen pipeline, same set-level 3-fold CV and seeds as
tools/explorer_eval.py: train on shard 0 of the sets outside the fold, test on shard 1 of the
fold's sets. Per arm (K) four views of every utterance:

  base     the network over the K candidates, the final pipeline as frozen
  +score   the same slots; every word of a contested slot gets the decoder's reading of it in
           the consensus context (lp_self, lp_nb, their window sum, each also relative to the
           slot's best) as extra columns of the slot model
  +words   +score, and the slot also offers the words the refill proposed (zero votes); the
           slot oracle of this view is the availability the refill bought
  +cands   the refined whole candidates appended to the K, network rebuilt, final as frozen

plus a training-free rule, "window argmax": in contested slots the alternative with the best
lp_self (summed) + lp_nb, elsewhere ROVER as shipped. Bootstrap: every view against base at the
same K, and anchor-k4 +cands against anchor-k8 base (refining costs a fraction of four more
candidates).

    python3 tools/refine_eval.py --cand results/cand_audio.pkl \\
        --refine results/refine/refine_k8.pkl,results/refine/refine_k4.pkl
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

import crf_rover as F
import slot_lr as L
import slot_eval as S
import final_compare as FC
import k_curve as KC
import confirm_eval as CE

AKEY = "aslots_w2"
EPS = S.EPS
NCOL = 11


def refine_cols(words, i, R):
    """Decoder readings in the consensus context for the words of slot i (zeros if not read)."""
    f = R["feats"].get(i, {})
    props = set(R["props"].get(i, ()))
    has = 1.0 if i in R["contested"] else 0.0
    ls = np.array([f[w][0] if w in f and f[w][0] is not None else np.nan for w in words])
    ln = np.array([f[w][1] if w in f and f[w][1] is not None else np.nan for w in words])
    lsum = np.array([f[w][2] if w in f and f[w][2] is not None else (0.0 if w == EPS else np.nan) for w in words])
    win = lsum + ln

    def rel(v):
        ok = ~np.isnan(v)
        return np.where(ok, v - (v[ok].max() if ok.any() else 0.0), 0.0)

    cols = [np.full(len(words), has), (~np.isnan(ls)).astype(float), np.nan_to_num(ls), rel(ls),
            (~np.isnan(ln)).astype(float), np.nan_to_num(ln), rel(ln),
            np.nan_to_num(win), rel(win), np.array([1.0 if w in props else 0.0 for w in words]),
            np.array([1.0 if (w in f and not np.isnan(win[j])) and win[j] == np.nanmax(win) else 0.0
                      for j, w in enumerate(words)]) if (~np.isnan(win)).any() else np.zeros(len(words))]
    return np.stack(cols, 1)


def with_refine(d, R, lm):
    return [(words, np.hstack([X, refine_cols(words, i, R)]), g)
            for i, (words, X, g) in enumerate(S.prepare(d, AKEY, lm))]


def add_props(d, R):
    """The same record with the refill's words offered in their slots, at zero votes."""
    d2 = dict(d)
    d2["slots"] = [dict(s) for s in d["slots"]]
    d2[AKEY] = [dict(s) for s in d[AKEY]]
    for i, ws in R["props"].items():
        for w in ws:
            d2["slots"][i].setdefault(w, [0.0, 0.0])
            d2[AKEY][i].setdefault(w, [0.0, 0.0])
    return d2


def fit_ref(tr, lm, a):
    pre = [with_refine(d, R, lm) for d, R in tr]
    Xs = [X for sl in pre for (_, X, g) in sl if g is not None]
    gs = [g for sl in pre for (_, _, g) in sl if g is not None]
    A = np.concatenate(Xs)
    mu, sd = A.mean(0), A.std(0) + 1e-9
    w, loss = L.fit([(X - mu) / sd for X in Xs], gs, a.lam, a.iters, a.lr)
    return w, mu, sd, loss


def apply_ref(d, R, m, lm):
    w, mu, sd, _ = m
    return [words[int(np.argmax(((X - mu) / sd) @ w))] for words, X, _ in with_refine(d, R, lm)]


def window_argmax(d, R):
    n = float(d["n_cand"])
    out = []
    for i, s in enumerate(d["slots"]):
        f = R["feats"].get(i, {})
        sc = {w: (v[2] if v[2] is not None else 0.0) + v[1] for w, v in f.items()
              if v[1] is not None and (w == EPS or v[2] is not None)}
        out.append(max(sc, key=sc.get) if i in R["contested"] and sc else F.rover_pick(s, n, 0.5, 0.7, None))
    return out


def slot_oracle(d, al, ep):
    n = float(d["n_cand"])
    return [r if (r in s or r == EPS) else F.rover_pick(s, n, al, ep, S.POWER)
            for s, r in zip(d["slots"], d["ref_by_slot"])]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    ap.add_argument("--refine", required=True, help="comma separated refine.py outputs")
    ap.add_argument("--arms", default="anchor-k8,anchor-k4")
    ap.add_argument("--test_shard", type=int, default=1)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--lm_utts", type=int, default=600)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    a = ap.parse_args()

    REF = {}
    for p in a.refine.split(","):
        if p and Path(p).exists():
            REF.update(pickle.loads(Path(p).read_bytes()))
    arms = [x for x in a.arms.split(",") if any(k[0] == x for k in REF)]
    recs = [r for r in pickle.loads(Path(a.cand).read_bytes()) if r["arm"] in arms]

    V = {}            # arm -> view -> (set, id) -> record ; plus "R" -> refine record
    bad = 0
    for arm in arms:
        k = int(arm.rsplit("-k", 1)[1])
        V[arm] = {"base": {}, "cands": {}, "R": {}, "n_ref": {}}
        for r in recs:
            if r["arm"] != arm or (arm, r["set"], r["id"]) not in REF:
                continue
            R = REF[(arm, r["set"], r["id"])]
            b = KC.build(r, k)
            if b is None:
                continue
            if len(b["slots"]) != R["n_slots"]:
                bad += 1
                continue
            b["shard"] = r.get("shard")
            key = (b["set"], b["id"])
            V[arm]["base"][key] = b
            V[arm]["R"][key] = R
            V[arm]["n_ref"][key] = len(R["refined"])
            r2 = dict(r, cands=r["cands"][:k] + R["refined"])
            b2 = KC.build(r2, k + len(R["refined"]))
            if b2 is not None:
                b2["shard"] = r.get("shard")
                V[arm]["cands"][key] = b2
    if bad:
        print(f"!! {bad} records whose network differs from the one refine.py read: skipped")

    keys = sorted(set.intersection(*[{kk for kk, d in V[x]["base"].items() if d["shard"] == a.test_shard
                                      and kk[0] in CE.TEST_SETS and kk in V[x]["cands"]} for x in arms]))
    rl = np.array([len(V[arms[0]]["base"][kk]["ref"]) for kk in keys], float)
    print(f"test: {len(keys)} utterances on {len({k[0] for k in keys})} sets; arms {arms}\n")

    # what the refill bought, before any model: proposals and availability
    for arm in arms:
        B, RR = V[arm]["base"], V[arm]["R"]
        n_prop = hit = holes = filled = cont = slots = 0
        for kk in keys:
            d, R = B[kk], RR[kk]
            slots += len(d["slots"])
            cont += len(R["contested"])
            for i, (s, r) in enumerate(zip(d["slots"], d["ref_by_slot"])):
                ps = R["props"].get(i, [])
                n_prop += len(ps)
                hit += int(r in ps)
                if r != EPS and r not in s:
                    holes += 1
                    filled += int(r in ps)
        print(f"{arm}: contested {100 * cont / max(slots, 1):.1f}% of slots; {n_prop} new words proposed, "
              f"{100 * hit / max(n_prop, 1):.1f}% of them the reference; holes filled {filled} of {holes} "
              f"({100 * filled / max(holes, 1):.1f}%); refined candidates per utt "
              f"{np.mean([V[arm]['n_ref'][kk] for kk in keys]):.2f}")
    print()

    seeds = [int(x) for x in a.seeds.split(",")]
    E = {}
    for seed in seeds:
        for arm in arms:
            B, C, RR = V[arm]["base"], V[arm]["cands"], V[arm]["R"]
            H = {}
            for fold in FC.FOLDS:
                pool = [kk for kk, d in B.items() if d["shard"] != a.test_shard and kk[0] not in fold
                        and kk in C]
                random.Random(seed).shuffle(pool)
                n_lm = min(a.lm_utts, len(pool) // 3)
                lm = F.Bigram([B[kk]["ref"] for kk in pool[:n_lm]])
                tr = pool[n_lm:]
                al, ep, _ = min(((al, e, sum(F.edits_of([F.rover_pick(s, float(B[kk]["n_cand"]), al, e, S.POWER)
                                                          for s in B[kk]["slots"]], B[kk]["ref"]) for kk in tr))
                                 for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])
                m_base = FC.fit_arm([B[kk] for kk in tr], lm, AKEY, a)
                m_cand = FC.fit_arm([C[kk] for kk in tr], lm, AKEY, a)
                m_sc = fit_ref([(B[kk], RR[kk]) for kk in tr], lm, a)
                m_wd = fit_ref([(add_props(B[kk], RR[kk]), RR[kk]) for kk in tr], lm, a)
                for name, m in (("+score", m_sc), ("+words", m_wd)):
                    if m[3] > m_base[3] + 1e-3 and name == "+score":
                        print(f"  !! seed {seed} {arm} {name}: train loss {m[3]:.4f} > base {m_base[3]:.4f}")
                for kk in keys:
                    if kk[0] not in fold:
                        continue
                    d, c, R = B[kk], C[kk], RR[kk]
                    dw = add_props(d, R)
                    H[kk] = {
                        "ROVER tuned": [F.rover_pick(s, float(d["n_cand"]), al, ep, S.POWER) for s in d["slots"]],
                        "final": FC.apply_arm(d, m_base, AKEY, lm),
                        "window argmax": window_argmax(d, R),
                        "final +score": apply_ref(d, R, m_sc, lm),
                        "final +words": apply_ref(dw, R, m_wd, lm),
                        "ROVER +cands": [F.rover_pick(s, float(c["n_cand"]), al, ep, S.POWER) for s in c["slots"]],
                        "final +cands": FC.apply_arm(c, m_cand, AKEY, lm),
                        "slot oracle": slot_oracle(d, al, ep),
                        "slot oracle +words": slot_oracle(dw, al, ep),
                        "slot oracle +cands": slot_oracle(c, al, ep),
                    }
            for m in H[keys[0]]:
                E[(seed, arm, m)] = np.array([F.edits_of(H[kk][m], V[arm]["base"][kk]["ref"]) for kk in keys], float)
        print(f"seed {seed} done", flush=True)

    methods = list(H[keys[0]])
    print(f"\n{'':<22}" + "".join(f"{x:>12}" for x in arms))
    for m in methods:
        print(f"{m:<22}" + "".join(f"{np.mean([100 * E[(s, x, m)].sum() / rl.sum() for s in seeds]):12.2f}"
                                    for x in arms))

    print("\npaired bootstrap, positive = second better")
    pairs = [((x, "final"), (x, m)) for x in arms
             for m in ("window argmax", "final +score", "final +words", "final +cands")]
    pairs += [((x, "ROVER tuned"), (x, "ROVER +cands")) for x in arms]
    if "anchor-k8" in arms and "anchor-k4" in arms:
        pairs += [(("anchor-k8", "final"), ("anchor-k4", "final +cands")),
                  (("anchor-k8", "final"), ("anchor-k4", "final +words"))]
    for (xa, ma), (xb, mb) in pairs:
        for s in seeds:
            o, lo, hi = S.bootstrap(E[(s, xa, ma)], E[(s, xb, mb)], rl, seed=s)
            print(f"  {xa} {ma:<14} -> {xb} {mb:<14} seed {s}: {o:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
