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

plus a training-free rule, "window argmax": ROVER as shipped decides word or nothing, and in
contested slots the decoder picks among the real words by lp_self (summed) + lp_nb. Bootstrap: every view against base at the
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


def gpt_cols(words, g):
    """GPT-2 log p(word | left context) and its gap to the slot's best (tools/ext_lm.py)."""
    v = np.array([g.get(w, 0.0) if w != EPS else 0.0 for w in words])
    real = np.array([w != EPS for w in words])
    return np.stack([v, (v - (v[real].max() if real.any() else 0.0)) * real], 1)


def with_refine(d, R, lm, G=None):
    G = G[(d["set"], d["id"])] if G is not None else None
    out = []
    for i, (words, X, g) in enumerate(S.prepare(d, AKEY, lm)):
        parts = [X]
        if R is not None:
            parts.append(refine_cols(words, i, R))
        if G is not None:
            parts.append(gpt_cols(words, G[i]))
        out.append((words, np.hstack(parts), g))
    return out


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


def fit_ref(tr, lm, a, G=None):
    pre = [with_refine(d, R, lm, G) for d, R in tr]
    Xs = [X for sl in pre for (_, X, g) in sl if g is not None]
    gs = [g for sl in pre for (_, _, g) in sl if g is not None]
    A = np.concatenate(Xs)
    mu, sd = A.mean(0), A.std(0) + 1e-9
    w, loss = L.fit([(X - mu) / sd for X in Xs], gs, a.lam, a.iters, a.lr)
    return w, mu, sd, loss


def apply_ref(d, R, m, lm, G=None):
    w, mu, sd, _ = m
    return [words[int(np.argmax(((X - mu) / sd) @ w))] for words, X, _ in with_refine(d, R, lm, G)]


def window_argmax(d, R):
    """Training-free: ROVER decides word or nothing (an empty slot has no tokens of its own to
    pay for, so a summed log-prob always favours it); among real words the decoder decides, by
    lp_self (summed) + lp_nb where measured, in the context the variant used."""
    n = float(d["n_cand"])
    out = []
    for i, s in enumerate(d["slots"]):
        rov = F.rover_pick(s, n, 0.5, 0.7, None)
        f = R["feats"].get(i, {})
        sc = {w: v[2] + (v[1] or 0.0) for w, v in f.items() if w != EPS and v[2] is not None}
        out.append(max(sc, key=sc.get) if i in R["contested"] and sc and rov != EPS else rov)
    return out


def slot_oracle(d, al, ep):
    n = float(d["n_cand"])
    return [r if (r in s or r == EPS) else F.rover_pick(s, n, al, ep, S.POWER)
            for s, r in zip(d["slots"], d["ref_by_slot"])]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True, help="comma separated cand_audio-format pickles")
    ap.add_argument("--refine", required=True,
                    help="variants as name=a.pkl,b.pkl;name2=... (one name: name= may be left out); "
                         "a variant may cover only some arms")
    ap.add_argument("--arms", default="anchor-k8,anchor-k4")
    ap.add_argument("--lm", default="", help="external-LM slot scores (tools/gpt_slots.py) as "
                    "name:arm=path,arm2=path;name2:... -- every LM is a separate view")
    ap.add_argument("--lm_variants", default="", help="variants stacked with each LM (default all)")
    ap.add_argument("--pairs", default="", help="extra bootstrap pairs: armA@method>armB@method;...")
    ap.add_argument("--test_shard", type=int, default=1)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--lm_utts", type=int, default=600)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    a = ap.parse_args()

    VAR = {}
    for spec in a.refine.split(";"):
        if not spec:
            continue
        name, paths = spec.split("=", 1) if "=" in spec else ("zs", spec)
        VAR[name] = {}
        for p in paths.split(","):
            if p and Path(p).exists():
                VAR[name].update(pickle.loads(Path(p).read_bytes()))
    VAR = {k: v for k, v in VAR.items() if v}
    LMS = {}                     # name -> arm -> (set, id) -> per-slot {word: log p}
    for spec in a.lm.split(";"):
        if ":" not in spec:
            continue
        name, rest = spec.split(":", 1)
        for part in rest.split(","):
            if "=" in part and Path(part.split("=", 1)[1]).exists():
                arm, p = part.split("=", 1)
                LMS.setdefault(name, {})[arm] = pickle.loads(Path(p).read_bytes())
    lmv = {x for x in a.lm_variants.split(",") if x}
    recs = [r for p in a.cand.split(",") if p and Path(p).exists() for r in pickle.loads(Path(p).read_bytes())]
    arms = [x for x in a.arms.split(",") if any(r["arm"] == x for r in recs)]
    names = {x: [v for v in VAR if any(k[0] == x for k in VAR[v])] for x in arms}
    full = {v: any(R["props"] or R["refined"] for R in VAR[v].values()) for v in VAR}
    print("variants per arm: " + "; ".join(f"{x}: {names[x]}" for x in arms)
          + "".join(f"; LM {n} for {sorted(v)}" for n, v in LMS.items()))

    B, C, RR = {}, {}, {}    # arm -> key -> base record / {variant: +cands record} / {variant: refine}
    bad = 0
    for arm in arms:
        k = int(arm.rsplit("-k", 1)[1])
        B[arm], C[arm], RR[arm] = {}, {}, {}
        for r in recs:
            if r["arm"] != arm or any((arm, r["set"], r["id"]) not in VAR[v] for v in names[arm]):
                continue
            if any(arm in v and (r["set"], r["id"]) not in v[arm] for v in LMS.values()):
                continue
            b = KC.build(r, k)
            if b is None:
                continue
            Rs = {v: VAR[v][(arm, r["set"], r["id"])] for v in names[arm]}
            if any(len(b["slots"]) != R["n_slots"] for R in Rs.values()):
                bad += 1
                continue
            if any(arm in v and len(v[arm][(r["set"], r["id"])]) != len(b["slots"]) for v in LMS.values()):
                bad += 1
                continue
            cs = {}
            for v, R in Rs.items():
                if full[v]:
                    b2 = KC.build(dict(r, cands=r["cands"][:k] + R["refined"]), k + len(R["refined"]))
                    if b2 is None:
                        break
                    b2["shard"] = r.get("shard")
                    cs[v] = b2
            if len(cs) != sum(full[v] for v in names[arm]):
                continue
            b["shard"] = r.get("shard")
            key = (b["set"], b["id"])
            B[arm][key], C[arm][key], RR[arm][key] = b, cs, Rs
    if bad:
        print(f"!! {bad} records whose network differs from the one their features were read on: skipped")

    keys = sorted(set.intersection(*[{kk for kk, d in B[x].items() if d["shard"] == a.test_shard
                                      and kk[0] in CE.TEST_SETS} for x in arms]))
    rl = np.array([len(B[arms[0]][kk]["ref"]) for kk in keys], float)
    print(f"test: {len(keys)} utterances on {len({k[0] for k in keys})} sets; arms {arms}\n")

    for arm in arms:
        for v in names[arm]:
            cont = sum(len(RR[arm][kk][v]["contested"]) for kk in keys)
            slots = sum(len(B[arm][kk]["slots"]) for kk in keys)
            line = f"{arm} [{v}]: contested {100 * cont / max(slots, 1):.1f}% of slots"
            if full[v]:
                n_prop = hit = holes = filled = 0
                for kk in keys:
                    d, R = B[arm][kk], RR[arm][kk][v]
                    for i, (sl, r) in enumerate(zip(d["slots"], d["ref_by_slot"])):
                        ps = R["props"].get(i, [])
                        n_prop += len(ps)
                        hit += int(r in ps)
                        if r != EPS and r not in sl:
                            holes += 1
                            filled += int(r in ps)
                line += (f"; {n_prop} new words, {100 * hit / max(n_prop, 1):.1f}% of them the reference; "
                         f"holes filled {filled} of {holes}; refined candidates per utt "
                         f"{np.mean([len(RR[arm][kk][v]['refined']) for kk in keys]):.2f}")
            print(line)

    # standalone transcripts, no model fitted: refining the composition against refining one candidate
    stand = [(arm, v) for arm in arms for v in names[arm] if RR[arm][keys[0]][v].get("single")]
    if stand:
        print("\nstandalone transcripts (WER), no combiner")
    for arm, v in stand:
        row = {}
        for m, f in (("upstream pick", lambda R: R["single"]["base"]),
                     ("single refined", lambda R: R["single"]["refined"]),
                     ("consensus", lambda R: R["consensus"]),
                     ("consensus refined", lambda R: R["cons_refined"])):
            row[m] = np.array([F.edits_of(f(RR[arm][kk][v]), B[arm][kk]["ref"]) for kk in keys], float)
        print(f"  {arm} [{v}]  " + "  ".join(f"{m} {100 * e.sum() / rl.sum():.2f}" for m, e in row.items()))
        for x, y in (("upstream pick", "single refined"), ("consensus", "consensus refined"),
                     ("single refined", "consensus refined")):
            o, lo, hi = S.bootstrap(row[x], row[y], rl)
            print(f"      {x} -> {y}: {o:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    print()

    seeds = [int(x) for x in a.seeds.split(",")]
    E, methods = {}, {}
    for seed in seeds:
        for arm in arms:
            GS = {n: v[arm] for n, v in LMS.items() if arm in v}
            H = {}
            for fold in FC.FOLDS:
                pool = [kk for kk, d in B[arm].items() if d["shard"] != a.test_shard and kk[0] not in fold]
                random.Random(seed).shuffle(pool)
                n_lm = min(a.lm_utts, len(pool) // 3)
                lm = F.Bigram([B[arm][kk]["ref"] for kk in pool[:n_lm]])
                tr = pool[n_lm:]
                al, ep, _ = min(((al, e, sum(F.edits_of([F.rover_pick(s_, float(B[arm][kk]["n_cand"]), al, e, S.POWER)
                                                          for s_ in B[arm][kk]["slots"]], B[arm][kk]["ref"]) for kk in tr))
                                 for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])
                m_base = FC.fit_arm([B[arm][kk] for kk in tr], lm, AKEY, a)
                m_lm = {n: fit_ref([(B[arm][kk], None) for kk in tr], lm, a, G) for n, G in GS.items()}
                M = {}
                for v in names[arm]:
                    M[v] = dict(sc=fit_ref([(B[arm][kk], RR[arm][kk][v]) for kk in tr], lm, a))
                    for n, G in GS.items():
                        if not lmv or v in lmv:
                            M[v]["lm " + n] = fit_ref([(B[arm][kk], RR[arm][kk][v]) for kk in tr], lm, a, G)
                    if full[v]:
                        M[v]["cand"] = FC.fit_arm([C[arm][kk][v] for kk in tr], lm, AKEY, a)
                        M[v]["wd"] = fit_ref([(add_props(B[arm][kk], RR[arm][kk][v]), RR[arm][kk][v])
                                              for kk in tr], lm, a)
                    if M[v]["sc"][3] > m_base[3] + 1e-3:
                        print(f"  !! seed {seed} {arm} [{v}] +score: train loss {M[v]['sc'][3]:.4f} > base {m_base[3]:.4f}")
                for kk in keys:
                    if kk[0] not in fold:
                        continue
                    d = B[arm][kk]
                    h = {"ROVER tuned": [F.rover_pick(s_, float(d["n_cand"]), al, ep, S.POWER) for s_ in d["slots"]],
                         "final": FC.apply_arm(d, m_base, AKEY, lm),
                         "slot oracle": slot_oracle(d, al, ep)}
                    for n, G in GS.items():
                        h[f"final +{n}"] = apply_ref(d, None, m_lm[n], lm, G)
                    for v in names[arm]:
                        R = RR[arm][kk][v]
                        h[f"window argmax [{v}]"] = window_argmax(d, R)
                        h[f"final +score [{v}]"] = apply_ref(d, R, M[v]["sc"], lm)
                        for n, G in GS.items():
                            if "lm " + n in M[v]:
                                h[f"final +score +{n} [{v}]"] = apply_ref(d, R, M[v]["lm " + n], lm, G)
                        if full[v]:
                            c, dw = C[arm][kk][v], add_props(d, R)
                            h[f"final +words [{v}]"] = apply_ref(dw, R, M[v]["wd"], lm)
                            h[f"final +cands [{v}]"] = FC.apply_arm(c, M[v]["cand"], AKEY, lm)
                            h[f"slot oracle +words [{v}]"] = slot_oracle(dw, al, ep)
                    H[kk] = h
            for m in H[keys[0]]:
                methods.setdefault(m, None)
                E[(seed, arm, m)] = np.array([F.edits_of(H[kk][m], B[arm][kk]["ref"]) for kk in keys], float)
        print(f"seed {seed} done", flush=True)

    print(f"\n{'':<34}" + "".join(f"{x:>11}" for x in arms))
    for m in methods:
        print(f"{m:<34}" + "".join(f"{np.mean([100 * E[(s_, x, m)].sum() / rl.sum() for s_ in seeds]):11.2f}"
                                    if (seeds[0], x, m) in E else f"{'':>11}" for x in arms))

    print("\npaired bootstrap, positive = second better")
    pairs = []
    for x in arms:
        for v in names[x]:
            pairs += [((x, "final"), (x, f"{m} [{v}]")) for m in ("final +score", "final +words", "final +cands")]
        lms = [n for n in LMS if x in LMS[n]]
        for n in lms:
            pairs.append(((x, "final"), (x, f"final +{n}")))
            pairs += [((x, f"final +{n}"), (x, f"final +score +{n} [{v}]")) for v in names[x]]
        pairs += [((x, f"final +{n1}"), (x, f"final +{n2}")) for i, n1 in enumerate(lms) for n2 in lms[i + 1:]]
        pairs += [((x, f"final +score [{v1}]"), (x, f"final +score [{v2}]"))
                  for i, v1 in enumerate(names[x]) for v2 in names[x][i + 1:]]
    for spec in a.pairs.split(";"):
        if ">" in spec:
            l, r = spec.split(">")
            pairs.append((tuple(l.split("@", 1)), tuple(r.split("@", 1))))
    for (xa, ma), (xb, mb) in pairs:
        if (seeds[0], xa, ma) not in E or (seeds[0], xb, mb) not in E:
            continue
        for s_ in seeds:
            o, lo, hi = S.bootstrap(E[(s_, xa, ma)], E[(s_, xb, mb)], rl, seed=s_)
            print(f"  {xa} {ma:<28} -> {xb} {mb:<30} seed {s_}: {o:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
