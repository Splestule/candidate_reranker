"""Training-free ways to pick one of the K candidates. mean_conf is what upstream does."""

from __future__ import annotations

import math
import re

_PUNCT = re.compile(r"[^\w\s]")


def normalize(text: str) -> str:
    """Must match upstream evaluate_whisfusion.py or our WER is not comparable."""
    return " ".join(_PUNCT.sub("", text.lower()).split())


def edit_distance(a: list, b: list) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def wer_pair(ref: str, hyp: str) -> float:
    r, h = normalize(ref).split(), normalize(hyp).split()
    if not r:
        return 0.0 if not h else 1.0
    return edit_distance(r, h) / len(r)


def corpus_wer(refs: list[str], hyps: list[str]) -> float:
    """Total edits over total reference words."""
    e = w = 0
    for ref, hyp in zip(refs, hyps):
        r = normalize(ref).split()
        e += edit_distance(r, normalize(hyp).split())
        w += len(r)
    return 100.0 * e / max(w, 1)


def mean_utt_wer(refs: list[str], hyps: list[str]) -> float:
    """Mean per-utterance WER; upstream reports this, so compare 8.3% against it."""
    if not refs:
        return 0.0
    return 100.0 * sum(wer_pair(r, h) for r, h in zip(refs, hyps)) / len(refs)


# Scorers take the candidate dicts written by dump_candidates.py and return a
# score per candidate; higher is better.

def s_mean_conf(cands):
    return [c["avg_conf"] for c in cands]


def s_min_conf(cands):
    return [c["min_conf"] for c in cands]


def s_median_conf(cands):
    return [c["median_conf"] for c in cands]


def s_mean_logprob(cands):
    return [c["mean_logprob"] for c in cands]


def s_neg_entropy(cands):
    return [-c["mean_entropy"] for c in cands]


def s_len_norm_conf(cands):
    return [c["avg_conf"] * math.log(1 + c["n_tokens"]) for c in cands]


def s_mbr_wer(cands):
    """MBR within the candidate set: negative mean WER against the others."""
    toks = [normalize(c["text"]).split() for c in cands]
    n = len(toks)
    out = []
    for i in range(n):
        tot = sum(edit_distance(toks[j], toks[i]) / max(len(toks[j]), 1)
                  for j in range(n) if j != i)
        out.append(-tot / max(n - 1, 1))
    return out


def s_conf_plus_mbr(cands, lam: float = 0.5):
    return [a + lam * b for a, b in zip(s_mean_conf(cands), s_mbr_wer(cands))]


SCORERS = {
    "mean_conf (upstream)": s_mean_conf,
    "min_conf": s_min_conf,
    "median_conf": s_median_conf,
    "mean_logprob": s_mean_logprob,
    "neg_entropy": s_neg_entropy,
    "len_norm_conf": s_len_norm_conf,
    "mbr_wer": s_mbr_wer,
    "conf+0.5*mbr": s_conf_plus_mbr,
}


def diversity(cands) -> dict:
    """Low diversity caps what any selection method can achieve."""
    toks = [normalize(c["text"]).split() for c in cands]
    n = len(toks)
    if n < 2:
        return {"mean_pairwise_wer": 0.0, "n_unique": 1}
    tot = cnt = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            tot += edit_distance(toks[i], toks[j]) / max(len(toks[j]), 1)
            cnt += 1
    return {
        "mean_pairwise_wer": 100.0 * tot / cnt,
        "n_unique": len({" ".join(t) for t in toks}),
    }
