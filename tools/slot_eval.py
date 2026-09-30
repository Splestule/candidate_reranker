#!/usr/bin/env python3
"""The learned slot combiner, evaluated the way the paper needs it.

tools/slot_lr.py established that a convex per-slot model beats tuned ROVER on held-out sets
(+0.25 WER alone, +0.51 with a neighbour bigram). This is the reporting version of the same
model, plus the one feature family it never had:

  * every arm on the same held-out sets, with a paired bootstrap against TUNED ROVER, pooled
    and per set -- a gain that only lives on one domain is not a gain;
  * the gain broken down into substitutions, insertions and deletions, next to the slot
    oracle's, so it is visible WHICH errors the model fixes and which it cannot reach;
  * optionally, acoustic features: the decoder's step-zero reading of the audio, scored per
    word and folded into the same network (tools/audio_slots.py). At the level of whole
    transcripts that signal was redundant with the vote; a slot is a different decision.

Split by SET, as always: the bigram is built from training utterances the weight fit never
sees, alpha/eps of the ROVER baseline are tuned on the training sets, and nothing that is
reported has been looked at during fitting.

    python3 tools/slot_eval.py --cache results/calib_cache.pkl
    python3 tools/slot_eval.py --cache results/audio_cache.pkl --audio w2
"""

from __future__ import annotations

import argparse
import math
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

EPS = ""
EVAL_SETS = ("ls-test-clean", "ls-test-other", "gigaspeech", "ami", "common_voice")
POWER = 11.95
CTX = ("1", "entropy", "n_alt", "margin", "uncontested", "slot_conf")


def slot_rows(slot, aslot, total, lmctx):
    """(words, X) for one slot. X = outer(varying, context) [+ neighbour columns]."""
    words = list(slot.keys())
    if EPS not in words:
        words.append(EPS)
    votes = np.array([slot.get(w, [0.0, 0.0])[0] for w in words], float)
    csum = np.array([slot.get(w, [0.0, 0.0])[1] for w in words], float)
    real = np.array([w != EPS for w in words], float)
    freq = votes / total if total else votes * 0.0
    conf = np.where(votes > 0, csum / np.maximum(votes, 1e-9), 0.0) * real
    conf_cal = np.clip(conf, 0.0, 1.0) ** POWER
    vary = [freq, conf, conf_cal, 1.0 - real, (votes == votes.max()).astype(float),
            np.log1p(votes) / math.log1p(max(total, 2.0)),
            np.array([min(len(w), 12) / 12.0 for w in words]),
            freq / max(freq.max(), 1e-9), conf - conf.max()]
    if aslot is not None:
        av = np.array([aslot.get(w, [0.0, 0.0])[0] for w in words], float)
        asum = np.array([aslot.get(w, [0.0, 0.0])[1] for w in words], float)
        aud = np.where(av > 0, asum / np.maximum(av, 1e-9), 0.0) * real
        lg = np.log(np.clip(aud, 1e-6, 1.0)) * real
        vary += [aud, lg, lg - (lg[real > 0].max() if real.any() else 0.0) * real]
    v = np.stack(vary, axis=1)
    p = freq / max(freq.sum(), 1e-9)
    ent = float(-(p[p > 0] * np.log(p[p > 0])).sum())
    srt = np.sort(freq)[::-1]
    margin = float(srt[0] - srt[1]) if len(srt) > 1 else float(srt[0])
    n_alt = float(real.sum())
    c = np.array([1.0, ent, min(n_alt, 8.0) / 8.0, margin, 1.0 if n_alt <= 1 else 0.0,
                  float(conf.sum() / max(n_alt, 1.0))])
    X = (v[:, :, None] * c[None, None, :]).reshape(len(words), -1)
    if lmctx is not None:
        lm, prev, nxt, top = lmctx
        X = np.hstack([X, np.array([[lm(prev, w), lm(w, nxt), 1.0 if w == top else 0.0,
                                     1.0 if w == EPS else 0.0] for w in words])])
    return words, X


def top_word(slot):
    return max(slot.items(), key=lambda kv: kv[1][0])[0] if slot else EPS


def prepare(d, audio_key, lm):
    total = float(d["n_cand"])
    tops = [top_word(s) for s in d["slots"]]
    aslots = d.get(audio_key) if audio_key else None
    out = []
    for i, (slot, ref) in enumerate(zip(d["slots"], d["ref_by_slot"])):
        lmctx = None
        if lm is not None:
            prev = next((tops[j] for j in range(i - 1, -1, -1) if tops[j] != EPS), EPS)
            nxt = next((tops[j] for j in range(i + 1, len(tops)) if tops[j] != EPS), EPS)
            lmctx = (lm, prev, nxt, tops[i])
        words, X = slot_rows(slot, aslots[i] if aslots else None, total, lmctx)
        out.append((words, X, words.index(ref) if ref in words else None))
    return out


def sid(ref, hyp):
    s = i = dl = 0
    for op in Levenshtein.editops(ref, hyp):
        if op.tag == "replace":
            s += 1
        elif op.tag == "insert":
            i += 1
        else:
            dl += 1
    return s, i, dl


def bootstrap(base, arm, rl, n=3000, seed=0):
    base, arm, rl = map(lambda x: np.asarray(x, float), (base, arm, rl))
    rng = np.random.default_rng(seed)
    obs = 100.0 * (base.sum() - arm.sum()) / rl.sum()
    idx = rng.integers(0, len(rl), (n, len(rl)))
    d = 100.0 * (base[idx].sum(1) - arm[idx].sum(1)) / rl[idx].sum(1)
    return obs, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--audio", default="", help="w0 / w2 ... : use aslots_<key> from the cache")
    ap.add_argument("--lm_utts", type=int, default=1200)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    # 0.15 (slot_lr's default) diverged on one of three seeds once the acoustic and the
    # neighbour features were combined: train loss 0.45 against 0.24 for the same arm at 0.05,
    # and a -1.05 WER swing. 0.05 converges on every arm and seed tried.
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    data = pickle.loads(Path(a.cache).read_bytes())
    akey = f"aslots_{a.audio}" if a.audio else ""
    if akey and not all(akey in d for d in data):
        print(f"{akey} missing from some records of {a.cache}")
        return 2
    ev = [d for d in data if d["set"] in EVAL_SETS]
    pool = [d for d in data if d["set"] not in EVAL_SETS]
    rng = random.Random(a.seed)
    rng.shuffle(pool)
    n_lm = min(a.lm_utts, len(pool) // 3)
    lm = F.Bigram([d["ref"] for d in pool[:n_lm]])
    tr = pool[n_lm:]
    print(f"{len(tr)} training utterances ({len({d['set'] for d in tr})} sets), bigram from "
          f"{n_lm} others, {len(ev)} held-out on {len({d['set'] for d in ev})} sets"
          + (f", acoustic features from {akey}" if akey else ""), flush=True)

    # ---- tuned ROVER: the baseline every arm is measured against
    R_tr = sum(len(d["ref"]) for d in tr)
    best = min(((al, e, sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, e, POWER)
                                        for s in d["slots"]], d["ref"]) for d in tr))
                for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])
    al, ep = best[0], best[1]
    print(f"tuned ROVER on the training sets: alpha {al}, eps {ep}, "
          f"train WER {100.0 * best[2] / R_tr:.2f}\n", flush=True)

    arms = {"slot model": (False, False), "+ neighbour bigram": (True, False)}
    if akey:
        arms["+ acoustic"] = (False, True)
        arms["+ neighbour + acoustic"] = (True, True)

    hyps = {"ROVER shipped": [], "ROVER tuned": [], "slot oracle": []}
    for d in ev:
        tot = float(d["n_cand"])
        hyps["ROVER shipped"].append([F.rover_pick(s, tot, 0.5, 0.7, None) for s in d["slots"]])
        hyps["ROVER tuned"].append([F.rover_pick(s, tot, al, ep, POWER) for s in d["slots"]])
        hyps["slot oracle"].append([r if (r in s or r == EPS) else F.rover_pick(s, tot, al, ep, POWER)
                                    for s, r in zip(d["slots"], d["ref_by_slot"])])
    losses = {}
    for name, (use_lm, use_aud) in arms.items():
        lmx = lm if use_lm else None
        ak = akey if use_aud else ""
        pre_tr = [prepare(d, ak, lmx) for d in tr]
        Xs = [X for sl in pre_tr for (_, X, g) in sl if g is not None]
        gs = [g for sl in pre_tr for (_, _, g) in sl if g is not None]
        A = np.concatenate(Xs)
        mu, sd = A.mean(0), A.std(0) + 1e-9
        w, loss = L.fit([(X - mu) / sd for X in Xs], gs, a.lam, a.iters, a.lr)
        hs = []
        for d in ev:
            hs.append([words[int(np.argmax(((X - mu) / sd) @ w))]
                       for words, X, _ in prepare(d, ak, lmx)])
        hyps[name] = hs
        print(f"  fitted {name}: {len(gs)} slots, {A.shape[1]} features, "
              f"train loss {loss:.4f}", flush=True)
        losses[name] = loss
        # every arm's features contain the plain slot model's, so at convergence its training
        # loss cannot be higher. If it is, the optimiser did not converge and the arm's
        # numbers below describe a failed fit, not the features.
        if name != "slot model" and loss > losses["slot model"] + 1e-3:
            print(f"  !! {name} did not converge (train loss {loss:.4f} > "
                  f"{losses['slot model']:.4f} of the nested model): lower --lr", flush=True)
        # The breakdown on the 400-per-set cache showed the whole gain is epsilon decisions --
        # the model keeps words ROVER drops -- while its word CHOICE is worse than ROVER's
        # (substitutions go up). So split the two decisions: the model says whether a slot
        # emits a word, ROVER says which word. No parameters, so nothing to tune.
        hyb = []
        for hm, hr in zip(hs, hyps["ROVER tuned"]):
            hyb.append([m if (m == EPS or r == EPS) else r for m, r in zip(hm, hr)])
        hyps[name + " | ROVER words"] = hyb

    refs = [d["ref"] for d in ev]
    rl = [len(r) for r in refs]
    R = sum(rl)
    E = {k: [F.edits_of(h, r) for h, r in zip(v, refs)] for k, v in hyps.items()}
    SID = {k: np.sum([sid(r, [w for w in h if w != EPS]) for h, r in zip(v, refs)], axis=0)
           for k, v in hyps.items()}

    base = E["ROVER tuned"]
    print(f"\n{'held-out, pooled':<26}{'WER':>7}{'sub':>7}{'ins':>7}{'del':>7}"
          f"{'vs tuned ROVER':>17}{'95% CI':>18}")
    for k in hyps:
        s, i, dl = 100.0 * SID[k] / R
        line = f"{k:<26}{100.0 * sum(E[k]) / R:>7.2f}{s:>7.2f}{i:>7.2f}{dl:>7.2f}"
        if k not in ("ROVER tuned",):
            o, lo, hi = bootstrap(base, E[k], rl)
            line += f"{o:>+17.2f}{f'[{lo:+.2f}, {hi:+.2f}]':>18}"
        print(line)
    print("  (positive = better than tuned ROVER; sub/ins/del in WER points)")

    print(f"\n{'per held-out set':<16}" + "".join(f"{k[:22]:>24}" for k in hyps if k != "ROVER tuned"))
    for s in EVAL_SETS:
        ix = [i for i, d in enumerate(ev) if d["set"] == s]
        if not ix:
            continue
        line = f"{s:<16}"
        for k in hyps:
            if k == "ROVER tuned":
                continue
            o, lo, hi = bootstrap([base[i] for i in ix], [E[k][i] for i in ix], [rl[i] for i in ix])
            flag = "*" if lo > 0 else (" " if hi >= 0 else "-")
            line += f"{f'{o:+.2f} [{lo:+.2f},{hi:+.2f}]{flag}':>24}"
        print(line)
    print("  * = interval above zero, - = below zero. Tuned ROVER WER per set:",
          ", ".join(f"{s} {100.0 * sum(base[i] for i, d in enumerate(ev) if d['set'] == s) / max(sum(rl[i] for i, d in enumerate(ev) if d['set'] == s), 1):.2f}"
                    for s in EVAL_SETS if any(d["set"] == s for d in ev)))

    pairs = [("+ acoustic", "slot model"), ("+ neighbour + acoustic", "+ neighbour bigram")]
    pairs = [(x, y) for x, y in pairs if x in E and y in E]
    if pairs:
        print("\nwhat the acoustic features add on their own (paired, same utterances):")
        for x, y in pairs:
            o, lo, hi = bootstrap(E[y], E[x], rl)
            print(f"  {x:<26} vs {y:<22}{o:+.2f}  [{lo:+.2f}, {hi:+.2f}]"
                  + ("" if lo > 0 else ("   BELOW zero" if hi < 0 else "   spans zero")))

    gap = sum(base) - sum(E["slot oracle"])
    print("\nshare of the slot oracle's gain each arm recovers, by error type:")
    for k in hyps:
        if k in ("ROVER tuned", "ROVER shipped", "slot oracle"):
            continue
        d_all = SID["ROVER tuned"] - SID[k]
        d_orc = SID["ROVER tuned"] - SID["slot oracle"]
        parts = ", ".join(f"{n} {100 * x / max(y, 1):.0f}%" for n, x, y in zip(("sub", "ins", "del"), d_all, d_orc))
        print(f"  {k:<26} total {100.0 * (sum(base) - sum(E[k])) / max(gap, 1):.1f}%   ({parts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
