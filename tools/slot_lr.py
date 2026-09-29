#!/usr/bin/env python3
"""Can any learned scorer beat alpha*freq + (1-alpha)*conf, slot by slot?

The A/R split says 6.1 % of reference words are sitting in their slot as an option and still
lose the vote. Recovering them is the cheapest part of the 10.92 WER gap, and it needs no
new topology, no language model and no second pass -- only a better rule for reading one
slot. So this asks the question in its simplest, convex form: multinomial logistic
regression over the words of a slot, gold = the reference word, argmax at test. Same
decision ROVER makes, better licence to make it.

Two things the structured perceptron in crf_rover.py got wrong and this fixes:

  Softmax over a slot is shift-invariant, so a feature with the same value for every word in
  the slot contributes exactly nothing. Half the CRF's emission features -- entropy, n_alt,
  uncontested, the bias -- were constant within a slot and could only ever act through the
  transition term. Here every such feature enters as a MULTIPLIER on the features that do
  vary, which is the thing worth learning: trust the confidence when the slot is contested,
  trust the count when it is not. That is a per-slot alpha, and a fixed alpha cannot be one.

  The perceptron took unit steps on features whose scales differ by an order of magnitude,
  never converged, and ended up liking long words. Features here are standardised on the
  training split and the objective is convex with an L2 penalty, so the fit is the fit.

If this cannot beat tuned ROVER, the per-slot statistics are exhausted: what is left has to
come from outside the slot.

    python3 tools/slot_lr.py --cache results/calib_cache.pkl --sizes 200,800,3200
"""

from __future__ import annotations

import argparse
import math
import pickle
import random
import sys
from pathlib import Path

sys.path.insert(0, "tools")
sys.path.insert(0, "src")

import numpy as np

import crf_rover as F

EPS = ""
EVAL_SETS = ("ls-test-clean", "ls-test-other", "gigaspeech", "ami", "common_voice")
GRID_ALPHA = [0.3, 0.4, 0.5, 0.6, 0.7, 0.85, 1.0]
GRID_EPS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

CTX_ALL = ("1", "entropy", "n_alt", "margin", "uncontested", "slot_conf")
VARY = ("freq", "conf", "conf_cal", "is_eps", "is_top", "log_votes", "word_len",
        "freq_share", "conf_gap")
CTX = list(CTX_ALL)          # narrowed by --ctx; "1" alone = no per-slot adaptivity


# ------------------------------------------------------------------------------- features

def slot_feats(slot: dict, total: float, power: float):
    """(words, X) with X[i] = outer(varying_i, context) flattened. Context is per slot."""
    words = list(slot.keys())
    if EPS not in words:
        words.append(EPS)
    votes = np.array([slot.get(w, [0.0, 0.0])[0] for w in words], float)
    csum = np.array([slot.get(w, [0.0, 0.0])[1] for w in words], float)
    real = np.array([w != EPS for w in words], float)
    freq = votes / total if total else votes * 0.0
    conf = np.where(votes > 0, csum / np.maximum(votes, 1e-9), 0.0) * real
    conf_cal = np.clip(conf, 0.0, 1.0) ** power

    p = freq / max(freq.sum(), 1e-9)
    ent = float(-(p[p > 0] * np.log(p[p > 0])).sum())
    srt = np.sort(freq)[::-1]
    margin = float(srt[0] - srt[1]) if len(srt) > 1 else float(srt[0])
    n_alt = float(real.sum())
    slot_conf = float((conf * real).sum() / max(real.sum(), 1.0))

    v = np.stack([
        freq,
        conf,
        conf_cal,
        1.0 - real,
        (votes == votes.max()).astype(float),
        np.log1p(votes) / math.log1p(max(total, 2.0)),
        np.array([min(len(w), 12) / 12.0 for w in words]),
        freq / max(freq.max(), 1e-9),
        conf - conf.max(),
    ], axis=1)                                            # (n_words, |VARY|)
    have = dict(zip(CTX_ALL, [1.0, ent, min(n_alt, 8.0) / 8.0, margin,
                              1.0 if n_alt <= 1 else 0.0, slot_conf]))
    c = np.array([have[k] for k in CTX])                   # (|CTX|,)
    return words, (v[:, :, None] * c[None, None, :]).reshape(len(words), -1)


def top_word(slot: dict) -> str:
    return max(slot.items(), key=lambda kv: kv[1][0])[0] if slot else EPS


def utt_slots(d: dict, power: float, lm=None, oracle_ctx: bool = False):
    """Per-slot (words, features, gold index). With an LM, four context features are added.

    The context features are deliberately decode-free: they look at the MOST-VOTED word of
    the slot before and after, which is fixed whatever this slot decides. That keeps the
    objective convex and the argmax independent per slot, so the comparison against ROVER
    stays like for like. A Viterbi pass over a learned transition would be the next step,
    and crf_rover.py is what happened when that was tried first.
    """
    total = float(d["n_cand"])
    base = []
    for slot, ref in zip(d["slots"], d["ref_by_slot"]):
        words, X = slot_feats(slot, total, power)
        base.append((words, X, words.index(ref) if ref in words else None, slot))
    if lm is None:
        return [(w, X, g) for w, X, g, _ in base]

    tops = [top_word(sl) for _, _, _, sl in base]
    # The oracle variant replaces the neighbours' most-voted words with the reference's own
    # neighbours. It does not reveal this slot's answer -- a bigram score against a known
    # previous word still has to be weighed against the votes -- but it removes every error
    # the context itself makes. What the model then wins is an upper bound on what any
    # amount of context modelling could be worth here.
    ctx_src = [r for _, _, _, _ in base] if False else (
        list(d["ref_by_slot"]) if oracle_ctx else tops)
    out = []
    for i, (words, X, g, _) in enumerate(base):
        prev = next((ctx_src[j] for j in range(i - 1, -1, -1) if ctx_src[j] != EPS), EPS)
        nxt = next((ctx_src[j] for j in range(i + 1, len(ctx_src)) if ctx_src[j] != EPS), EPS)
        ctx = np.array([[lm(prev, w), lm(w, nxt),
                         1.0 if w == tops[i] else 0.0,
                         1.0 if w == EPS else 0.0] for w in words])
        out.append((words, np.hstack([X, ctx]), g))
    return out


# --------------------------------------------------------------------------------- model

def buckets(Xs, golds):
    """Group slots by their word count so each group is one dense (n, w, d) tensor.

    The loop version spends all its time in Python for a few hundred flops per slot. Slots
    come in a handful of sizes -- two to five words, mostly -- so bucketing by size gives
    full vectorisation without padding a 20-word slot's worth of zeros onto every 2-word one.
    """
    by = {}
    for X, g in zip(Xs, golds):
        by.setdefault(X.shape[0], ([], []))[0].append(X)
        by[X.shape[0]][1].append(g)
    return [(np.stack(xs), np.asarray(gs)) for xs, gs in by.values()]


def fit(Xs, golds, lam: float, iters: int = 400, lr: float = 0.15):
    """Softmax over each slot's rows, gold = the reference word. Adam, L2, convex."""
    d = Xs[0].shape[1]
    bk = buckets(Xs, golds)
    n = float(len(Xs))
    w = np.zeros(d)
    m, v = np.zeros(d), np.zeros(d)
    loss = 0.0
    for t in range(1, iters + 1):
        g = np.zeros(d)
        loss = 0.0
        for X, gi in bk:                                  # X (n_b, n_w, d)
            s = X @ w
            s -= s.max(axis=1, keepdims=True)
            e = np.exp(s)
            p = e / e.sum(axis=1, keepdims=True)
            loss -= float(np.log(np.maximum(p[np.arange(len(gi)), gi], 1e-12)).sum())
            p[np.arange(len(gi)), gi] -= 1.0
            g += np.einsum("bw,bwd->d", p, X)
        g = g / n + 2.0 * lam * w
        m = 0.9 * m + 0.1 * g
        v = 0.999 * v + 0.001 * (g * g)
        w -= lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
    return w, loss / n


def rover_edits(rows, alpha, eps, power):
    return sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), alpha, eps, power)
                           for s in d["slots"]], d["ref"]) for d in rows)


def tune_rover(rows, power):
    R = sum(len(d["ref"]) for d in rows) or 1
    return min(((a, e, 100.0 * rover_edits(rows, a, e, power) / R)
                for a in GRID_ALPHA for e in GRID_EPS), key=lambda t: t[2])


def slot_acc(pre, w, mu, sd):
    """(picked correctly, reachable slots) over prepared utterances."""
    ok = n = 0
    for slots in pre:
        for words, X, gi in slots:
            if gi is None:
                continue
            n += 1
            ok += int(np.argmax(((X - mu) / sd) @ w) == gi)
    return ok, n


def decode_wer(data, pre, w, mu, sd):
    tot = R = 0
    for d, slots in zip(data, pre):
        h = [words[int(np.argmax(((X - mu) / sd) @ w))] for words, X, _ in slots]
        tot += F.edits_of(h, d["ref"])
        R += len(d["ref"])
    return 100.0 * tot / max(R, 1), tot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="results/calib_cache.pkl")
    ap.add_argument("--power", type=float, default=11.95)
    ap.add_argument("--sizes", default="200,400,800,1600,3200")
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--iters", type=int, default=400)
    ap.add_argument("--ctx", default="",
                    help="comma-separated subset of " + ",".join(CTX_ALL) + "; '1' alone "
                         "turns off per-slot adaptivity and leaves a plain linear scorer")
    ap.add_argument("--neighbour", action="store_true",
                    help="add decode-free context: bigram against the neighbouring slots' "
                         "most-voted words")
    ap.add_argument("--lm_utts", type=int, default=1200,
                    help="training utterances reserved for the context bigram alone")
    ap.add_argument("--oracle_ctx", action="store_true",
                    help="use the reference's own neighbours instead of the neighbouring "
                         "slots' most-voted words: an upper bound on what context is worth")
    ap.add_argument("--seeds", default="1234", help="one training draw per seed, per size")
    ap.add_argument("--out", default="results/slot_lr.pkl")
    a = ap.parse_args()

    global CTX
    if a.ctx:
        CTX = [x.strip() for x in a.ctx.split(",") if x.strip()]
        bad = [x for x in CTX if x not in CTX_ALL]
        if bad:
            print(f"unknown context feature(s): {bad}")
            return 2
    data = pickle.loads(Path(a.cache).read_bytes())
    ev = [d for d in data if d["set"] in EVAL_SETS]
    pool = [d for d in data if d["set"] not in EVAL_SETS]
    print(f"{len(pool)} training utterances, {len(ev)} eval utterances "
          f"({len(EVAL_SETS)} held-out sets)", flush=True)

    # The bigram must not be built from the same references the weights are fitted on.
    # It memorises them -- lm(prev, gold) goes to one on the training slots -- and the
    # model then puts all its weight on a feature that carries nothing at test time. That
    # mistake cost a run: with oracle context it turned a 0.39 gain into a 1.2 loss.
    lm = None
    if a.neighbour:
        rng0 = random.Random(9999)
        shuf = pool[:]
        rng0.shuffle(shuf)
        lm_pool, pool = shuf[:a.lm_utts], shuf[a.lm_utts:]
        lm = F.Bigram([d["ref"] for d in lm_pool])
        print(f"bigram from {len(lm_pool)} held-out references; weights fit on the "
              f"remaining {len(pool)}")
        if a.oracle_ctx:
            print("ORACLE CONTEXT: the neighbours are the reference's own words")
        print(f"context bigram over {len(pool)} training references, {len(lm.uni)} types")
    pre_ev = [utt_slots(d, a.power, lm, a.oracle_ctx) for d in ev]
    names = [f"{x}*{c}" for x in VARY for c in CTX]
    if a.neighbour:
        names += ["lm(prev,w)", "lm(w,next)", "is_slot_top", "is_eps_ctx"]
    print(f"context features: {CTX}")

    # ---- ROVER's own slot accuracy, as the thing to beat
    print(f"\n{'train utts':>11}{'slots':>9}{'ROVER acc':>11}{'LR acc':>9}{'ROVER WER':>11}"
          f"{'LR WER':>9}{'LR-ROVER':>10}{'95% CI':>18}", flush=True)
    print("-" * 88)
    import bootstrap
    rl = [len(d["ref"]) for d in ev]
    rows = []
    jobs = [(n, sd) for n in (int(x) for x in a.sizes.split(",") if x.strip())
            for sd in (int(x) for x in a.seeds.split(",") if x.strip())]
    for n, seed in jobs:
        rng = random.Random(seed + n)
        tr = pool[:]
        rng.shuffle(tr)
        tr = tr[:n]
        al, ep, _ = tune_rover(tr, a.power)

        pre_tr = [utt_slots(d, a.power, lm, a.oracle_ctx) for d in tr]
        Xs = [X for slots in pre_tr for (_, X, gi) in slots if gi is not None]
        gs = [gi for slots in pre_tr for (_, _, gi) in slots if gi is not None]
        A = np.concatenate(Xs, axis=0)
        mu, sd = A.mean(0), A.std(0) + 1e-9
        Xz = [(X - mu) / sd for X in Xs]
        w, loss = fit(Xz, gs, a.lam, a.iters)

        ok, tot_slots = slot_acc(pre_ev, w, mu, sd)
        rok = rn = 0
        for d, slots in zip(ev, pre_ev):
            picks = [F.rover_pick(s, float(d["n_cand"]), al, ep, a.power) for s in d["slots"]]
            for (words, _, gi), pick in zip(slots, picks):
                if gi is None:
                    continue
                rn += 1
                rok += int(words[gi] == pick)
        lw, _ = decode_wer(ev, pre_ev, w, mu, sd)
        rw = 100.0 * rover_edits(ev, al, ep, a.power) / sum(rl)

        pu_lr = [F.edits_of([wd[int(np.argmax(((X - mu) / sd) @ w))] for wd, X, _ in slots],
                            d["ref"]) for d, slots in zip(ev, pre_ev)]
        pu_rv = [F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, ep, a.power)
                             for s in d["slots"]], d["ref"]) for d in ev]
        st = bootstrap.paired_bootstrap(pu_rv, pu_lr, rl, n_boot=3000)
        ci = f"[{-st['ci_high']:+.2f}, {-st['ci_low']:+.2f}]"
        tag = f"{n}" if len(a.seeds.split(",")) < 2 else f"{n}/s{seed}"
        print(f"{tag:>11}{len(gs):>9}{100 * rok / max(rn, 1):>10.1f}%"
              f"{100 * ok / max(tot_slots, 1):>8.1f}%{rw:>11.2f}{lw:>9.2f}"
              f"{lw - rw:>+10.2f}{ci:>18}", flush=True)
        rows.append(dict(n=n, seed=seed, w=w, mu=mu, sd=sd, names=names, loss=loss,
                         alpha=al, eps=ep, rover_wer=rw, lr_wer=lw,
                         rover_acc=rok / max(rn, 1), lr_acc=ok / max(tot_slots, 1)))
    print("-" * 88)
    print("LR-ROVER negative = the learned picker wins.\n")

    w, mu, sd = rows[-1]["w"], rows[-1]["mu"], rows[-1]["sd"]
    order = np.argsort(-np.abs(w))[:18]
    print(f"largest weights at {rows[-1]['n']} utterances (standardised features)")
    for i in order:
        print(f"  {names[i]:<22}{w[i]:+8.3f}")

    Path(a.out).write_bytes(pickle.dumps(rows))
    print(f"\nrows -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
