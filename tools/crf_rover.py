#!/usr/bin/env python3
"""A learned path scorer over the confusion network, in place of voting slot by slot.

ROVER decides each slot on its own. The composition oracle picks a path. That difference is
most of the 10.92 WER between them, because whether "time is leisure" beats "times leisure"
is not a property of either slot alone. So: score whole paths and take the best one.

Finding the path is not the problem. The network is a linear chain, so the best path under
any additive score is one Viterbi pass -- microseconds. The work is the scoring function,
and the model class that fits "score a path through a chain, learn from the true path" is a
linear-chain CRF. Trained here with an averaged structured perceptron: Viterbi, compare to
the gold path, move the weights on the difference. No optimiser library, no GPU, minutes on
a laptop, a few hundred parameters.

The transition term carries a bigram score, which is the one thing the network genuinely
does not contain (word order). It is a feature the model weighs against the votes, not a
language model replacing them -- a general LM cannot see the votes at all, and a neural one
would cost more than the decode it is correcting.

Discipline, same as tools/calibrate_rover.py: the calibration map, the bigram, the CRF
weights and every hyper-parameter come from the dev sets; the reported numbers come from
sets none of that ever saw. The baseline to beat is CALIBRATED ROVER, not the shipped one.

    PYTHONPATH=src python tools/crf_rover.py --cache /tmp/calib_cache.pkl
"""

from __future__ import annotations

import argparse
import math
import pickle
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

EPS = ""
DEV_SETS = ("ls-dev-clean", "ls-dev-other")
SHIPPED = dict(alpha=0.5, eps=0.7)
N_EMIT, N_TRANS = 12, 4


# ------------------------------------------------------------------------------- features

def slot_rows(slot: dict, total: float, power: float) -> tuple[list[str], np.ndarray]:
    """Words of one slot and their emission features, in a fixed order."""
    words = list(slot.keys())
    if EPS not in words:
        words.append(EPS)
    votes = np.array([slot.get(w, [0.0, 0.0])[0] for w in words], dtype=np.float64)
    csum = np.array([slot.get(w, [0.0, 0.0])[1] for w in words], dtype=np.float64)
    freq = votes / total if total else votes * 0.0
    with np.errstate(invalid="ignore", divide="ignore"):
        conf = np.where(votes > 0, csum / np.maximum(votes, 1e-9), 0.0)
    conf_cal = np.clip(conf, 0.0, 1.0) ** power
    real = np.array([w != EPS for w in words], dtype=np.float64)
    n_alt = float(real.sum())
    p = freq / max(freq.sum(), 1e-9)
    ent = float(-(p[p > 0] * np.log(p[p > 0])).sum())
    top = (votes == votes.max()).astype(np.float64)
    srt = np.sort(freq)[::-1]
    margin = float(srt[0] - srt[1]) if len(srt) > 1 else float(srt[0])

    f = np.zeros((len(words), N_EMIT))
    f[:, 0] = 1.0                                     # bias: how much a slot costs at all
    f[:, 1] = freq
    f[:, 2] = conf_cal * real          # epsilon has no confidence of its own; see f[:, 4]
    f[:, 3] = conf * real
    f[:, 4] = 1.0 - real                              # epsilon, i.e. drop the slot
    f[:, 5] = min(n_alt, 8.0) / 8.0
    f[:, 6] = top
    f[:, 7] = margin
    f[:, 8] = np.log1p(votes) / math.log1p(max(total, 2.0))
    f[:, 9] = np.array([min(len(w), 12) / 12.0 for w in words])
    f[:, 10] = ent
    f[:, 11] = 1.0 if n_alt <= 1 else 0.0             # uncontested: nothing to decide
    return words, f


def trans_feats(prev: str, cur: str, lm) -> np.ndarray:
    t = np.zeros(N_TRANS)
    t[0] = lm(prev, cur)
    t[1] = 1.0 if (prev == EPS and cur == EPS) else 0.0
    t[2] = 1.0 if prev == EPS else 0.0
    t[3] = 1.0 if cur == EPS else 0.0
    return t


# ------------------------------------------------------------------------------- bigram LM

class Bigram:
    """Add-k bigram over the training references, skipping epsilon. The weak link here.

    240 dev utterances is not a language model. It is enough to test whether the transition
    term earns a weight at all; a real one needs external text (the LibriSpeech LM corpus is
    the convention) and --lm_text takes it.
    """

    def __init__(self, sents: list[list[str]], k: float = 0.5):
        self.uni: dict[str, int] = defaultdict(int)
        self.bi: dict[tuple, int] = defaultdict(int)
        self.k, self.V = k, 1
        for s in sents:
            prev = "<s>"
            for w in s:
                self.uni[prev] += 1
                self.bi[(prev, w)] += 1
                prev = w
        self.V = max(len(self.uni), 1)

    def __call__(self, prev: str, cur: str) -> float:
        if cur == EPS:
            return 0.0                        # epsilon is handled by its own features
        prev = prev if prev != EPS else "<s>"
        num = self.bi.get((prev, cur), 0) + self.k
        den = self.uni.get(prev, 0) + self.k * self.V
        return math.log(num / den) / 12.0      # scaled so one weight covers a sane range


# --------------------------------------------------------------------------------- Viterbi

def decode(d: dict, we: np.ndarray, wt: np.ndarray, lm, power: float) -> list[str]:
    total = float(d["n_cand"])
    prev_words, prev_score, prev_back = [EPS], np.zeros(1), []
    slots = []
    for slot in d["slots"]:
        words, f = slot_rows(slot, total, power)
        em = f @ we
        slots.append(words)
        sc = np.full(len(words), -1e18)
        bk = np.zeros(len(words), dtype=int)
        for j, w in enumerate(words):
            best, arg = None, 0
            for i, pw in enumerate(prev_words):
                v = prev_score[i] + float(trans_feats(pw, w, lm) @ wt)
                if best is None or v > best:
                    best, arg = v, i
            sc[j], bk[j] = best + em[j], arg
        prev_words, prev_score = words, sc
        prev_back.append(bk)

    out, j = [], int(np.argmax(prev_score))
    for i in range(len(slots) - 1, -1, -1):
        out.append(slots[i][j])
        j = int(prev_back[i][j])
    return out[::-1]


def gold_path(d: dict) -> list[str | None]:
    """The reference word per slot, or None where it is not on offer and nothing is learnable."""
    out = []
    for slot, r in zip(d["slots"], d["ref_by_slot"]):
        if r == EPS:
            out.append(EPS)
        elif r in slot:
            out.append(r)
        else:
            out.append(None)
    return out


# -------------------------------------------------------------------------------- training

def rover_weights(alpha: float, eps_conf: float) -> np.ndarray:
    """The weights at which the CRF IS calibrated ROVER. Verified by --identity."""
    we = np.zeros(N_EMIT)
    we[1] = alpha
    we[2] = 1.0 - alpha
    we[4] = (1.0 - alpha) * eps_conf
    return we


def train(dev: list[dict], lm, power: float, epochs: int, seed: int = 0, masks=None,
          init: np.ndarray | None = None):
    me, mt = masks if masks is not None else (np.ones(N_EMIT), np.ones(N_TRANS))
    we = np.zeros(N_EMIT) if init is None else init.copy()
    wt = np.zeros(N_TRANS)                     # start AT the baseline, so training can only help
    acc_e, acc_t, n_acc = np.zeros(N_EMIT), np.zeros(N_TRANS), 0
    rng = random.Random(seed)
    order = list(range(len(dev)))
    skipped = learn = 0
    for ep in range(epochs):
        rng.shuffle(order)
        wrong = 0
        for idx in order:
            d = dev[idx]
            gold = gold_path(d)
            pred = decode(d, we * me, wt * mt, lm, power)
            total = float(d["n_cand"])
            prev_g = prev_p = EPS
            for slot, g, p in zip(d["slots"], gold, pred):
                if g is None:
                    if ep == 0:
                        skipped += 1
                    prev_g, prev_p = p, p      # stay on the predicted path where gold is absent
                    continue
                if ep == 0:
                    learn += 1
                if g != p:
                    wrong += 1
                    words, f = slot_rows(slot, total, power)
                    we += (f[words.index(g)] - f[words.index(p)]) * me
                    wt += (trans_feats(prev_g, g, lm) - trans_feats(prev_p, p, lm)) * mt
                prev_g, prev_p = g, p
            acc_e += we; acc_t += wt; n_acc += 1
        print(f"  epoch {ep}: {wrong} slot corrections")
    if ep == 0 or True:
        print(f"  slots used {learn}, skipped as unreachable {skipped} "
              f"({100 * skipped / max(learn + skipped, 1):.1f} %)")
    return (acc_e / max(n_acc, 1)) * me, (acc_t / max(n_acc, 1)) * mt


# ---------------------------------------------------------------------------------- scoring

def rover_pick(slot: dict, total: float, alpha: float, eps: float, power: float | None) -> str:
    best, bw = None, EPS
    for w, (votes, csum) in slot.items():
        freq = votes / total if total else 0.0
        if w == EPS:
            conf = eps
        else:
            conf = csum / votes if votes > 0 else 0.0
            if power is not None:
                conf = min(max(conf, 0.0), 1.0) ** power
        s = alpha * freq + (1.0 - alpha) * conf
        if best is None or s > best:
            best, bw = s, w
    return bw


def edits_of(hyp: list[str], ref: list[str]) -> int:
    from rapidfuzz.distance import Levenshtein
    return Levenshtein.distance(ref, [w for w in hyp if w != EPS])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/calib_cache.pkl")
    ap.add_argument("--power", type=float, default=11.65, help="calibration exponent from calibrate_rover")
    ap.add_argument("--cal_alpha", type=float, default=0.7)
    ap.add_argument("--cal_eps", type=float, default=0.4)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--lm_text", default=None, help="one sentence per line; dev references if unset")
    ap.add_argument("--identity", action="store_true",
                    help="check the CRF reproduces calibrated ROVER, then stop")
    ap.add_argument("--mask", default="", help="comma-separated feature names to zero out, for ablation")
    a = ap.parse_args()

    sys.path.insert(0, "src")
    import bootstrap

    data = pickle.loads(Path(a.cache).read_bytes())
    dev = [d for d in data if d["set"] in DEV_SETS]
    test = [d for d in data if d["set"] not in DEV_SETS]
    if not dev or not test:
        print("need both dev and test utterances in the cache")
        return 2
    print(f"dev {len(dev)} utts, test {len(test)} utts, {len(set(d['set'] for d in test))} held-out sets")

    if a.lm_text:
        sents = [l.split() for l in Path(a.lm_text).read_text(encoding="utf-8").splitlines() if l.strip()]
    else:
        sents = [d["ref"] for d in dev]
    lm = Bigram(sents)
    print(f"bigram: {len(sents)} sentences, {len(lm.uni)} types\n")

    names = ["bias", "freq", "conf_cal", "conf_raw", "is_eps", "n_alt", "top_vote",
             "margin", "log_votes", "word_len", "entropy", "uncontested"]
    tnames = ["bigram", "eps->eps", "from_eps", "to_eps"]
    mask = [x.strip() for x in a.mask.split(",") if x.strip()]
    bad = [m for m in mask if m not in names + tnames]
    if bad:
        print(f"unknown feature(s) to mask: {bad}")
        return 2
    me = np.array([0.0 if n in mask else 1.0 for n in names])
    mt = np.array([0.0 if n in tnames_ else 1.0 for n, tnames_ in ((t, mask) for t in tnames)])
    if mask:
        print(f"ablation: masking {mask}\n")

    if a.identity:
        base = rover_weights(a.cal_alpha, a.cal_eps)
        zero = np.zeros(N_TRANS)
        flat = lambda x, y: 0.0
        same = bad = 0
        for d in dev + test:
            v = decode(d, base, zero, flat, a.power)
            r = [rover_pick(s, float(d["n_cand"]), a.cal_alpha, a.cal_eps, a.power)
                 for s in d["slots"]]
            same += v == r
            bad += v != r
        print(f"identity check: {same}/{same + bad} utterances decode identically to "
              f"calibrated ROVER")
        if bad:
            print("the CRF cannot express its own baseline -- fix that before training")
            return 1
        return 0

    print("training the CRF on dev, starting from the weights that reproduce ROVER")
    we, wt = train(dev, lm, a.power, a.epochs, masks=(me, mt),
                   init=rover_weights(a.cal_alpha, a.cal_eps))
    np.set_printoptions(precision=3, suppress=True)
    print("\nemission weights")
    for n, v in zip(names, we):
        print(f"  {n:<13}{v:+8.3f}")
    print("transition weights")
    for n, v in zip(tnames, wt):
        print(f"  {n:<13}{v:+8.3f}")

    arms = {
        "shipped ROVER": lambda d: [rover_pick(s, float(d["n_cand"]), SHIPPED["alpha"],
                                               SHIPPED["eps"], None) for s in d["slots"]],
        "calibrated ROVER": lambda d: [rover_pick(s, float(d["n_cand"]), a.cal_alpha,
                                                  a.cal_eps, a.power) for s in d["slots"]],
        "CRF path": lambda d: decode(d, we, wt, lm, a.power),
    }
    print(f"\n{'held-out set':<18}{'n':>5}{'shipped':>9}{'calibr.':>9}{'CRF':>8}"
          f"{'oracle':>8}{'vs calibr.':>12}")
    print("-" * 69)
    ed = {k: defaultdict(float) for k in arms}
    R = defaultdict(float)
    per_utt = {k: [] for k in arms}
    rl = []
    for d in test:
        for k, fn in arms.items():
            e = edits_of(fn(d), d["ref"])
            ed[k][d["set"]] += e
            per_utt[k].append(e)
        R[d["set"]] += len(d["ref"])
        rl.append(len(d["ref"]))
    for s in sorted(R):
        n = sum(1 for d in test if d["set"] == s)
        row = f"{s:<18}{n:>5}"
        for k in arms:
            row += f"{100 * ed[k][s] / R[s]:>9.2f}" if k != "CRF path" else f"{100 * ed[k][s] / R[s]:>8.2f}"
        row += f"{'':>8}{100 * (ed['CRF path'][s] - ed['calibrated ROVER'][s]) / R[s]:>+12.2f}"
        print(row)
    print("-" * 69)
    tot = sum(R.values())
    line = f"{'POOLED':<18}{len(test):>5}"
    for k in arms:
        v = 100 * sum(ed[k].values()) / tot
        line += f"{v:>9.2f}" if k != "CRF path" else f"{v:>8.2f}"
    line += f"{'':>8}{100 * (sum(ed['CRF path'].values()) - sum(ed['calibrated ROVER'].values())) / tot:>+12.2f}"
    print(line)

    print("\npaired bootstrap over held-out utterances (positive = the arm is better)")
    for base_name in ("shipped ROVER", "calibrated ROVER"):
        st = bootstrap.paired_bootstrap(per_utt[base_name], per_utt["CRF path"], rl, n_boot=4000)
        flag = "" if st["ci_low"] > 0 or st["ci_high"] < 0 else "   spans zero"
        print("  " + bootstrap.format_row(f"CRF vs {base_name}", st) + flag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
