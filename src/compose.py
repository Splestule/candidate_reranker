"""Combining candidates word by word instead of picking one of them whole.

Candidates are aligned into a confusion network against the most central one; each slot
then holds the words the candidates propose at that position, plus an epsilon for the ones
that skip it. Voting over the slots is ROVER (Fiscus 1997); the oracle path through the
network is the ceiling that voting could reach.
"""

from __future__ import annotations

import random
from collections import defaultdict

from rapidfuzz.distance import Levenshtein

from scorers import normalize

EPS = ""


def central_index(cands: list[list[str]]) -> int:
    """Candidate with the smallest total distance to the others."""
    best, best_i = None, 0
    for i, a in enumerate(cands):
        tot = sum(Levenshtein.distance(b, a) / max(len(b), 1)
                  for j, b in enumerate(cands) if j != i)
        if best is None or tot < best:
            best, best_i = tot, i
    return best_i


def cluster_weights(cands: list[list[str]], gamma: float = 1.0,
                    threshold: float = 0.0) -> list[float]:
    """Vote weight per candidate, so a cluster of m near-identical candidates counts m**gamma.

    gamma=1 is one vote each, which is what ROVER does and assumes the candidates are
    independent. They are not: the decoder repeats itself. gamma=0 collapses each cluster
    to a single vote.
    """
    n = len(cands)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if cands[i] == cands[j]:
                close = True
            elif threshold > 0:
                span = max(len(cands[i]), len(cands[j]), 1)
                close = Levenshtein.distance(cands[i], cands[j]) / span <= threshold
            else:
                close = False
            if close:
                a, b = find(i), find(j)
                if a != b:
                    parent[b] = a

    size: dict[int, int] = defaultdict(int)
    for i in range(n):
        size[find(i)] += 1
    return [float(size[find(i)]) ** (gamma - 1.0) for i in range(n)]


def confusion_network(cands: list[list[str]], backbone: int,
                      confs: list[list[float]] | None = None,
                      weights: list[float] | None = None) -> list[dict]:
    """Align every candidate to the backbone. Returns one dict per slot mapping
    word -> [summed vote weight, summed weighted confidence]."""
    bb = cands[backbone]
    n = len(bb)
    w = weights if weights is not None else [1.0] * len(cands)
    k = sum(w)
    sub: list[dict] = [defaultdict(lambda: [0.0, 0.0]) for _ in range(n)]
    ins: list[dict] = [defaultdict(lambda: [0.0, 0.0]) for _ in range(n + 1)]
    ins_voters: list[set] = [set() for _ in range(n + 1)]

    def add(slot, word, cand_i, pos):
        e = slot[word]
        e[0] += w[cand_i]
        if confs is not None and word != EPS and pos is not None:
            c = confs[cand_i]
            e[1] += (c[pos] if pos < len(c) else 1.0) * w[cand_i]
        else:
            e[1] += w[cand_i]

    for ci, c in enumerate(cands):
        for tag, i1, i2, j1, j2 in Levenshtein.opcodes(bb, c):
            if tag == "equal":
                for d in range(i2 - i1):
                    add(sub[i1 + d], c[j1 + d], ci, j1 + d)
            elif tag == "replace":
                for pos in range(i1, i2):
                    off = j1 + (pos - i1)
                    if off < j2:
                        add(sub[pos], c[off], ci, off)
                    else:
                        add(sub[pos], EPS, ci, None)
                for off in range(j1 + (i2 - i1), j2):
                    add(ins[i2], c[off], ci, off)
                    ins_voters[i2].add(ci)
            elif tag == "delete":
                for pos in range(i1, i2):
                    add(sub[pos], EPS, ci, None)
            elif tag == "insert":
                for off in range(j1, j2):
                    add(ins[i1], c[off], ci, off)
                    ins_voters[i1].add(ci)

    # Candidates that inserted nothing at a point still vote there, for epsilon.
    for i in range(n + 1):
        if ins[i]:
            ins[i][EPS] = [k - sum(w[c] for c in ins_voters[i]), 0.0]

    slots = []
    for i in range(n):
        if ins[i]:
            slots.append(dict(ins[i]))
        slots.append(dict(sub[i]))
    if ins[n]:
        slots.append(dict(ins[n]))

    for s in slots:
        s.setdefault(EPS, [0.0, 0.0])
    return slots


def oracle_path(slots: list[dict], ref: list[str]) -> int:
    """Fewest edits any path through the network can achieve against ref."""
    INF = 10 ** 9
    R = len(ref)
    cur = list(range(R + 1))
    for slot in slots:
        nxt = [INF] * (R + 1)
        for j in range(R + 1):
            if cur[j] == INF:
                continue
            for w in slot:
                if w == EPS:
                    nxt[j] = min(nxt[j], cur[j])
                else:
                    nxt[j] = min(nxt[j], cur[j] + 1)          # spurious word
                    if j < R:
                        nxt[j + 1] = min(nxt[j + 1], cur[j] + (0 if w == ref[j] else 1))
        for j in range(R):                                    # skipped reference word
            nxt[j + 1] = min(nxt[j + 1], nxt[j] + 1)
        cur = nxt
    return cur[R]


def rover_slot_picks(slots: list[dict], total: float, alpha: float = 1.0,
                     eps_conf: float = 0.5) -> list[str]:
    """The winning word of every slot, epsilons included, one per slot."""
    out = []
    for slot in slots:
        best, best_w = None, EPS
        for w, (votes, conf_sum) in slot.items():
            freq = votes / total if total else 0.0
            conf = eps_conf if w == EPS else (conf_sum / votes if votes > 0 else 0.0)
            score = alpha * freq + (1.0 - alpha) * conf
            if best is None or score > best:
                best, best_w = score, w
        out.append(best_w)
    return out


def rover(slots: list[dict], total: float, alpha: float = 1.0,
          eps_conf: float = 0.5) -> list[str]:
    """Vote per slot. alpha=1 is pure frequency; below that, confidence weighs in.

    total is the summed vote weight of all candidates, so frequencies stay in [0, 1].
    """
    return [w for w in rover_slot_picks(slots, total, alpha, eps_conf) if w != EPS]


def shuffled_control(slots: list[dict], pool: list[str], rng: random.Random) -> list[dict]:
    """Same network shape, alternatives replaced by unrelated words.

    Isolates how much of the oracle's gain is free choice per slot rather than the
    candidates actually holding the right word.
    """
    out = []
    for slot in slots:
        words = [w for w in slot if w != EPS]
        if not words:
            out.append(dict(slot))
            continue
        keep = words[0]
        new = {keep: list(slot[keep]), EPS: list(slot[EPS])}
        for w in words[1:]:
            new[rng.choice(pool)] = list(slot[w])
        out.append(new)
    return out


def prepare(row: dict, norm=normalize) -> tuple[list[list[str]], list[list[float]] | None]:
    """Candidate word lists, and per-word confidences when the dump carries them.

    norm is the text normaliser the words are compared in, and it must be the same one the
    reference is scored with. Compose in the space you measure in: normalising ROVER's output
    a second time further downstream is not the same as normalising the candidates once, since
    a normaliser that expands contractions cannot expand what an earlier pass already stripped.
    """
    cands = [norm(c["text"]).split() for c in row["candidates"]]
    confs = None
    if all("word_conf" in c for c in row["candidates"]):
        confs = [c["word_conf"] for c in row["candidates"]]
        if any(len(w) != len(t) for w, t in zip(confs, cands)):
            confs = None
    return cands, confs
