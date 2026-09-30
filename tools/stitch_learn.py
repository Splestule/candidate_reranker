#!/usr/bin/env python3
"""A learned scorer over stitchings: the first model shaped like the gap actually is.

tools/switch_oracle.py showed the composition gap is three or four contiguous segment
choices, not twenty-five word decisions -- one switch recovers 54 % of it, four recover
85 % -- and that the one-switch search space is about thirty thousand options, enumerable
in microseconds. tools/stitch_score.py then showed that nothing the decoder already emits
can rank those options: mean confidence, a bigram and a length bonus all land ten WER points
below ROVER, and equally far below with the switch turned off, so the failure is the ranking
and not the stitching.

So rank them with something trained for it. The score is linear in features that are
additive along the path, which is what makes exhaustive scoring possible:

    score(t, i, j) = w . [ (head_i(t) + tail_j(t)) / slots , g(i) , g(j) , junction , switch ]

Every per-slot feature is prefix-summed once per candidate, so a stitching costs a handful
of flops and the whole space is swept per utterance. Training is minimum risk -- softmax
over a sampled set of stitchings, loss = expected edit distance -- which optimises the thing
being reported rather than a proxy, and needs no oracle at test time.

Discipline, as everywhere else in this project: the dev sets fit the weights and the bigram,
the bigram is built from utterances the weight fit never sees, and the reported numbers come
from sets none of it ever saw.

    PYTHONPATH=src python3 tools/stitch_learn.py --max_utts 60
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
import compose
from crf_rover import Bigram
from switch_oracle import slot_matrix, switch_oracle

EPS = compose.EPS
# Split by SET, not by utterance, and make the training side cover several domains. The
# first version trained on LibriSpeech dev alone; the bigram feature is then the single most
# predictive thing in sight on clean read speech and worthless on meetings and noise, so the
# fit put a weight of +5 on it and the held-out number fell apart. A scorer meant for many
# domains has to be fitted on many.
EVAL_SETS = ("ls-test-clean", "ls-test-other", "gigaspeech", "ami", "common_voice")
SLOT_F = ("is_word", "conf", "freq", "gap_to_top", "is_rover", "bigram", "word_len", "log_votes")
CAND_F = ("mbr", "avg_conf", "rel_len")
D = len(SLOT_F) + 2 * len(CAND_F) + 2          # + junction bigram + switch indicator


def build(row, K, lm, with_rover: bool = True):
    """Everything a stitching score needs, precomputed once per utterance."""
    ref = A.S.normalize(row["reference"]).split()
    cands, confs, _ = A.prepare(row)
    k = min(K, len(cands))
    if k < 2 or not ref:
        return None
    sub, sub_c = cands[:k], (confs[:k] if confs else None)
    lens = [len(c) for c in sub]
    Lm = [[Levenshtein.distance(sub[i], sub[j]) for j in range(k)] for i in range(k)]
    mbr = np.array([-sum(Lm[i][j] / max(lens[j], 1) for j in range(k) if j != i) / (k - 1)
                    for i in range(k)])
    p = int(np.argmax(mbr))
    k0 = k
    slots = compose.confusion_network(sub, p, sub_c, None)
    M, owner = slot_matrix(sub, p, with_map=True)
    T = len(M)

    rover = compose.rover(slots, float(k), A.ROVER_DEFAULT["alpha"], A.ROVER_DEFAULT["eps"])
    picks = compose.rover_slot_picks(slots, float(k), A.ROVER_DEFAULT["alpha"],
                                     A.ROVER_DEFAULT["eps"])

    if with_rover:
        # ROVER's own output enters as one more candidate column. Then "no switch, take the
        # last column" IS ROVER, so the space the scorer searches contains its own baseline
        # and the oracle over it can only be better. It also gives the scorer a sane default
        # to fall back on, which a space of raw candidates does not have: every stitching of
        # two candidates throws away the votes of the other thirty.
        col = []
        seen = set()
        for t in range(len(M)):
            o = owner[t]
            if o in seen:
                col.append(EPS)
            else:
                seen.add(o)
                col.append(picks[o])
        M = [row + [col[t]] for t, row in enumerate(M)]
        lens = lens + [sum(1 for w in col if w != EPS)]
        k += 1

    g = np.zeros((T, k, len(SLOT_F)))
    last = [[EPS] * (T + 1) for _ in range(k)]
    first = [[EPS] * (T + 1) for _ in range(k)]
    for c in range(k):
        prev = EPS
        for t in range(T):
            w = M[t][c]
            sl = slots[owner[t]]
            top = max((v[0] for v in sl.values()), default=0.0)
            if w != EPS:
                votes, csum = sl.get(w, (0.0, 0.0))
                g[t, c] = (1.0,
                           csum / votes if votes > 0 else 0.0,
                           votes / k,
                           (top - votes) / k,
                           1.0 if w == picks[owner[t]] else 0.0,
                           lm(prev, w),
                           min(len(w), 12) / 12.0,
                           np.log1p(votes) / np.log1p(k))
                prev = w
            last[c][t + 1] = prev
        nxt = EPS
        for t in range(T, -1, -1):
            if t < T and M[t][c] != EPS:
                nxt = M[t][c]
            first[c][t] = nxt
    pre = np.concatenate([np.zeros((1, k, len(SLOT_F))), np.cumsum(g, axis=0)], axis=0)

    avgc = np.array([float(c.get("avg_conf", 0.0)) for c in row["candidates"][:k0]])
    rel = np.array(lens, dtype=float) / max(float(np.mean(lens[:k0])), 1e-9)
    if k > k0:                                   # the ROVER column: best of both by design
        mbr = np.append(mbr, mbr.max())
        avgc = np.append(avgc, avgc.mean())
    cand = np.stack([mbr, avgc, rel], axis=1)                      # (k, len(CAND_F))
    return dict(ref=ref, k=k, T=T, M=M, slots=slots, pre=pre, cand=cand,
                last=last, first=first, lm=lm,
                rover_e=Levenshtein.distance(ref, rover))


def feats(d, t, i, j):
    k, T, pre = d["k"], d["T"], d["pre"]
    path = (pre[t, i] + (pre[T, j] - pre[t, j])) / max(T, 1)
    w = d["first"][j][t]
    junc = 0.0
    if w != EPS and i != j:
        junc = d["lm"](d["last"][i][t], w) - d["lm"](d["last"][j][t], w)
    return np.concatenate([path, d["cand"][i], d["cand"][j],
                           [junc / max(T, 1), 1.0 if i != j else 0.0]])


def words(d, t, i, j):
    M, T = d["M"], d["T"]
    return [w for w in ([M[x][i] for x in range(t)] + [M[x][j] for x in range(t, T)])
            if w != EPS]


def sample(d, rng, n_rand: int):
    """All no-switch paths, plus random one-switch paths. Each with its true edit count."""
    out = []
    for c in range(d["k"]):
        out.append((0, c, c))
    for _ in range(n_rand):
        t = rng.randrange(d["T"] + 1)
        i, j = rng.randrange(d["k"]), rng.randrange(d["k"])
        out.append((t, i, j))
    X = np.stack([feats(d, *s) for s in out])
    e = np.array([Levenshtein.distance(d["ref"], words(d, *s)) for s in out], dtype=float)
    return X, e


def fit(rows, lam: float, iters: int, lr: float, temp: float):
    """Minimum risk: softmax over each utterance's sample, loss = expected edits."""
    w = np.zeros(D)
    m, v = np.zeros(D), np.zeros(D)
    n = len(rows)
    for it in range(1, iters + 1):
        grad = np.zeros(D)
        risk = 0.0
        for X, e in rows:
            s = temp * (X @ w)
            s -= s.max()
            p = np.exp(s)
            p /= p.sum()
            r = float(p @ e)
            risk += r
            grad += temp * ((p * (e - r)) @ X)          # d/dw of the expected cost
        grad = grad / n + 2.0 * lam * w
        m = 0.9 * m + 0.1 * grad
        v = 0.999 * v + 0.001 * (grad * grad)
        w -= lr * (m / (1 - 0.9 ** it)) / (np.sqrt(v / (1 - 0.999 ** it)) + 1e-8)
    return w, risk / n


def best(d, w, switch: bool):
    """Exhaustive argmax over the stitching space, prefix sums doing the work."""
    k, T, pre = d["k"], d["T"], d["pre"]
    ws, wc = w[:len(SLOT_F)], w[len(SLOT_F):]
    wi = wc[:len(CAND_F)]
    wj = wc[len(CAND_F):2 * len(CAND_F)]
    w_junc, w_sw = wc[2 * len(CAND_F)], wc[2 * len(CAND_F) + 1]

    ps = pre @ ws                                       # (T+1, k) path-feature score
    ci, cj = d["cand"] @ wi, d["cand"] @ wj
    tot = ps[T]
    bestv, arg = -1e18, (0, 0, 0)
    ts = range(T + 1) if switch else [0]
    for t in ts:
        head = ps[t] + ci                               # (k,)
        tail = (tot - ps[t]) + cj                       # (k,)
        if not switch:
            v = head + tail
            c = int(np.argmax(v))
            if v[c] > bestv:
                bestv, arg = float(v[c]), (0, c, c)
            continue
        jn = np.zeros(k)
        for j in range(k):
            wd = d["first"][j][t]
            if wd != EPS:
                jn[j] = -d["lm"](d["last"][j][t], wd)
        for i in range(k):
            wd_i = d["last"][i][t]
            add = np.zeros(k)
            for j in range(k):
                wd = d["first"][j][t]
                if wd != EPS and j != i:
                    add[j] = (d["lm"](wd_i, wd) + jn[j]) * w_junc / max(T, 1)
            v = head[i] + tail + add + w_sw * (np.arange(k) != i)
            j = int(np.argmax(v))
            if v[j] > bestv:
                bestv, arg = float(v[j]), (t, i, j)
    return arg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/campaign-2026-09-20/dumps")
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max_utts", type=int, default=60)
    ap.add_argument("--n_rand", type=int, default=160)
    ap.add_argument("--train_utts", type=int, default=400)
    ap.add_argument("--iters", type=int, default=600)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--temp", type=float, default=4.0)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/stitch_learn.json")
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
    devall = [r for s in by_set if s not in EVAL_SETS for r in by_set[s]]
    if not devall:
        print("no training sets in these dumps")
        return 2
    rng0 = random.Random(7)
    rng0.shuffle(devall)
    half = max(len(devall) // 3, 1)
    lm = Bigram([A.S.normalize(r["reference"]).split() for r in devall[:half]])
    train_rows = devall[half:][:a.train_utts]
    test_rows = [(s, r) for s in EVAL_SETS for r in by_set.get(s, [])]
    print(f"bigram from {half} training utterances; weights fit on {len(train_rows)} other "
          f"training utterances across {len({s for s in by_set if s not in EVAL_SETS})} sets; "
          f"{len(test_rows)} test utterances on {len({s for s, _ in test_rows})} held-out "
          f"sets", flush=True)

    rng = random.Random(a.seed)
    train = []
    for r in train_rows:
        d = build(r, a.k, lm)
        if d:
            train.append(sample(d, rng, a.n_rand))
    mu = np.concatenate([X for X, _ in train]).mean(0)
    sd = np.concatenate([X for X, _ in train]).std(0) + 1e-9
    train = [((X - mu) / sd, e) for X, e in train]
    w, risk = fit(train, a.lam, a.iters, a.lr, a.temp)
    print(f"trained on {len(train)} utterances x {len(train[0][1])} sampled stitchings, "
          f"expected edits {risk:.2f}\n", flush=True)

    names = list(SLOT_F) + [f"i.{x}" for x in CAND_F] + [f"j.{x}" for x in CAND_F] \
        + ["junction", "switch"]
    order = np.argsort(-np.abs(w))[:10]
    print("largest weights (standardised)")
    for i in order:
        print(f"  {names[i]:<16}{w[i]:+8.3f}")

    # the scorer reads standardised features, so fold the standardisation into the weights
    wz = w / sd
    shift = float(-(w * mu / sd).sum())          # constant: cannot change an argmax

    tot = dict(R=0, rov=0, s0=0, s1=0, cand=0, or0=0, or1=0, or2=0, moved=0, n=0)
    for _, r in test_rows:
        d = build(r, a.k, lm)
        if not d:
            continue
        tot["R"] += len(d["ref"])
        tot["n"] += 1
        tot["rov"] += d["rover_e"]
        tot["cand"] += min(Levenshtein.distance(d["ref"], words(d, 0, c, c))
                           for c in range(d["k"]))
        o = switch_oracle(d["M"], d["ref"], [0, 1, 2])
        tot["or0"] += o[0]
        tot["or1"] += o[1]
        tot["or2"] += o[2]
        for key, sw in (("s0", False), ("s1", True)):
            t, i, j = best(d, wz, sw)
            tot[key] += Levenshtein.distance(d["ref"], words(d, t, i, j))
            if sw:
                tot["moved"] += i != j
    del shift

    R = tot["R"]
    print(f"\n{'on the held-out sets':<38}{'WER':>8}")
    for key, lab in (("rov", "ROVER as shipped"),
                     ("cand", "best whole candidate (oracle)"),
                     ("s0", "learned scorer, no switch"),
                     ("s1", "learned scorer, one switch"),
                     ("or0", "ORACLE over this space, no switch"),
                     ("or1", "ORACLE over this space, one switch"),
                     ("or2", "ORACLE over this space, two switches")):
        print(f"  {lab:<36}{100.0 * tot[key] / R:>8.2f}")
    print(f"\n  it switched on {100.0 * tot['moved'] / max(tot['n'], 1):.0f}% of "
          f"{tot['n']} utterances")
    d1 = 100.0 * (tot["rov"] - tot["s1"]) / R
    print(f"  learned one-switch against ROVER: {d1:+.2f} WER")
    if a.out:
        Path(a.out).write_text(json.dumps(
            dict(model=a.model, arm=a.arm, k=a.k, n=tot["n"],
                 rover=100.0 * tot["rov"] / R, cand=100.0 * tot["cand"] / R,
                 s0=100.0 * tot["s0"] / R, s1=100.0 * tot["s1"] / R,
                 or0=100.0 * tot["or0"] / R, or1=100.0 * tot["or1"] / R,
                 or2=100.0 * tot["or2"] / R,
                 weights=dict(zip(names, w.tolist()))), indent=1))
        print(f"\n-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
