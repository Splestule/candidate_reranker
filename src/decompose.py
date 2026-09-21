#!/usr/bin/env python3
"""Why composition wins or loses, split into two numbers that pull against each other.

A slot of the confusion network is a decision. Voting can only get it right if the right
word is among the options at all, so the gain factors into

    availability  A  how often the reference word is an option in its slot
    recoverability R  how often the vote picks it, given that it is there

and ROVER's slot accuracy is their product. Selection's slot accuracy is the backbone's,
B. More disagreement raises A (more distinct words per slot) and lowers R (the votes
scatter), so A*R has a maximum and the temperature that maximises it need not be the one
that minimises WER. Reported next to B, this says whether a configuration fails because
the words are missing or because the vote cannot find them.

The reference is aligned to the same backbone the candidates are aligned to, so its word
lands in the slot the network would have to get right.
"""

from __future__ import annotations

import statistics

from rapidfuzz.distance import Levenshtein

import compose
from compose import EPS


def _insertion_points(cands: list[list[str]], bb: list[str]) -> set[int]:
    """The insertion slots confusion_network() will emit, by the same rule it uses."""
    pts = set()
    for c in cands:
        for tag, i1, i2, j1, j2 in Levenshtein.opcodes(bb, c):
            if tag == "insert" and j2 > j1:
                pts.add(i1)
            elif tag == "replace" and j2 > j1 + (i2 - i1):
                pts.add(i2)
    return pts


def reference_by_slot(cands: list[list[str]], backbone: int, ref: list[str]) -> list[str]:
    """The reference word belonging to each slot, EPS where the reference skips it."""
    bb = cands[backbone]
    ins_pts = _insertion_points(cands, bb)
    sub = [EPS] * len(bb)
    ins: dict[int, list[str]] = {i: [] for i in range(len(bb) + 1)}
    for tag, i1, i2, j1, j2 in Levenshtein.opcodes(bb, ref):
        if tag == "equal":
            for d in range(i2 - i1):
                sub[i1 + d] = ref[j1 + d]
        elif tag == "replace":
            for pos in range(i1, i2):
                off = j1 + (pos - i1)
                sub[pos] = ref[off] if off < j2 else EPS
            ins[i2].extend(ref[j1 + (i2 - i1):j2])
        elif tag == "delete":
            for pos in range(i1, i2):
                sub[pos] = EPS
        elif tag == "insert":
            ins[i1].extend(ref[j1:j2])

    out = []
    for i in range(len(bb)):
        if i in ins_pts:
            out.append(ins[i][0] if ins[i] else EPS)
        out.append(sub[i])
    if len(bb) in ins_pts:
        out.append(ins[len(bb)][0] if ins[len(bb)] else EPS)
    return out


def decompose(cands: list[list[str]], backbone: int, ref: list[str],
              alpha: float = 1.0, eps_conf: float = 0.5) -> dict:
    """Slot counts for one utterance."""
    slots = compose.confusion_network(cands, backbone, None, None)
    by_slot = reference_by_slot(cands, backbone, ref)
    if len(by_slot) != len(slots):          # layouts disagree: skip rather than misreport
        return {}

    bb = cands[backbone]
    picks = compose.rover_slot_picks(slots, float(len(cands)), alpha, eps_conf)
    bb_by_slot, j = [], 0
    ins_pts = _insertion_points(cands, bb)
    for i in range(len(bb)):
        if i in ins_pts:
            bb_by_slot.append(EPS)
        bb_by_slot.append(bb[i])
    if len(bb) in ins_pts:
        bb_by_slot.append(EPS)

    n = avail = picked = base = damage = rescue = 0
    for s, r, p, b in zip(slots, by_slot, picks, bb_by_slot):
        if r == EPS:
            continue
        n += 1
        a = r in s
        avail += a
        picked += p == r
        base += b == r
        damage += (b == r) and (p != r)
        rescue += (b != r) and (p == r)
    return dict(n=n, avail=avail, picked=picked, base=base, damage=damage, rescue=rescue)


def summarise(per_utt: list[dict]) -> dict:
    """Pool slot counts over utterances."""
    keep = [d for d in per_utt if d and d["n"]]
    if not keep:
        return {}
    tot = {k: sum(d[k] for d in keep) for k in ("n", "avail", "picked", "base", "damage", "rescue")}
    A = tot["avail"] / tot["n"]
    R = tot["picked"] / tot["avail"] if tot["avail"] else 0.0
    return dict(n_slots=tot["n"], A=100 * A, R=100 * R, AR=100 * A * R,
                B=100 * tot["base"] / tot["n"],
                damage=100 * tot["damage"] / tot["n"],
                rescue=100 * tot["rescue"] / tot["n"],
                n_utts=len(keep))
