#!/usr/bin/env python3
"""Build the confusion network the way Mangu et al. (2000) §3 do, and vote on it.

compose.confusion_network aligns every candidate to ONE backbone, so the slot grid is
whatever word order that candidate happened to have, and every other candidate is bent to
fit. Mangu's construction has no backbone. It clusters word occurrences into equivalence
classes from the evidence of all the alignments at once, then orders the classes.

Their two stages, translated to our setting (we have K transcripts, not a timed lattice):

  intra-word (§3.2)  merge occurrences of the SAME word that correspond to each other.
                     They use temporal overlap; we have no timings, so correspondence comes
                     from every PAIRWISE alignment rather than from one backbone.
  inter-word (§3.3)  merge classes of DIFFERENT words that compete for the same position.
                     They use phonetic similarity from pronunciation base forms; we have no
                     pronunciation dictionary, so this uses character similarity, which is a
                     proxy and the weakest link in the translation.

Ordering: their classes are ordered by time. Ours are ordered by the precedence a candidate
imposes on its own words -- token p comes before p+1 -- which makes a DAG over classes, and
a topological sort turns it back into a slot sequence. A merge that would create a cycle is
refused, because a class cannot both precede and follow another.

Two checks run before any number is reported, because an unverified builder has produced a
false result in this project three times already:

  every candidate must be readable as a path through the network
  at K = 1 the network must be exactly that one candidate

    PYTHONPATH=src python tools/mangu_net.py results/campaign-2026-09-20 --max_utts 40
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import pickle
import random
import sys
from collections import defaultdict
from pathlib import Path

EPS = ""


# ------------------------------------------------------------------------------ the builder

def pairwise_links(cands: list[list[str]], w: list[float] | None = None):
    """(cand_i, pos_i) <-> (cand_j, pos_j) for every position two candidates align at.

    w is a per-candidate weight, so near-duplicate candidates can be stopped from voting
    many times for the same merge. m identical candidates otherwise produce m(m-1)/2 pairs
    that all reinforce each other, and the merge order ends up decided by which variant the
    decoder happened to repeat most -- which is not evidence about the words.
    """
    from rapidfuzz.distance import Levenshtein
    links = defaultdict(float)
    n = len(cands)
    w = w or [1.0] * n
    for i in range(n):
        for j in range(i + 1, n):
            ww = w[i] * w[j]
            if ww <= 0.0:
                continue
            for tag, i1, i2, j1, j2 in Levenshtein.opcodes(cands[i], cands[j]):
                if tag in ("equal", "replace"):
                    for d in range(min(i2 - i1, j2 - j1)):
                        links[((i, i1 + d), (j, j1 + d))] += ww
    return links


_PHON = {"loaded": False, "d": {}, "miss": 0, "hit": 0}


def phonemes(word: str):
    """CMUdict pronunciation with stress digits dropped, or None if the word is not in it.

    Mangu's inter-word clustering compares "the most likely phonetic base form"; characters
    are what we had instead. Characters miss exactly the confusions an ASR makes: to/two and
    their/there are one phoneme string each but look nothing alike.
    """
    if not _PHON["loaded"]:
        _PHON["loaded"] = True
        try:
            import cmudict
            _PHON["d"] = {w: [p.rstrip("012") for p in prons[0]]
                          for w, prons in cmudict.dict().items()}
        except Exception:
            _PHON["d"] = {}
    ph = _PHON["d"].get(word)
    if ph is None:
        _PHON["miss"] += 1
    else:
        _PHON["hit"] += 1
    return ph


def phon_available() -> bool:
    phonemes("the")
    return bool(_PHON["d"])


_SIM: dict = {}


def similarity(wa: str, wb: str, phon: bool) -> float:
    """1 - normalised edit distance, over phonemes when both words are known, else characters."""
    key = (wa, wb, phon)
    v = _SIM.get(key)
    if v is not None:
        return v
    from rapidfuzz.distance import Levenshtein
    if phon:
        pa, pb = phonemes(wa), phonemes(wb)
        if pa is not None and pb is not None:
            v = 1.0 - Levenshtein.distance(pa, pb) / max(len(pa), len(pb), 1)
            _SIM[key] = v
            return v
    v = 1.0 - Levenshtein.distance(wa, wb) / max(len(wa), len(wb), 1)
    _SIM[key] = v
    return v


class DSU:
    def __init__(self, items):
        self.p = {x: x for x in items}

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra
        return ra != rb


def reachable(adj: dict, src, dst, limit: int = 4000) -> bool:
    seen, stack, n = {src}, [src], 0
    while stack and n < limit:
        x = stack.pop(); n += 1
        if x == dst:
            return True
        for y in adj.get(x, ()):  # noqa: B007
            if y not in seen:
                seen.add(y); stack.append(y)
    return False


def build(cands: list[list[str]], confs: list[list[float]] | None,
          sim_threshold: float = 0.45, gamma: float = 1.0, phon: bool = False) -> list[dict]:
    """gamma weights the merge evidence by how duplicated a candidate is.

    1.0 leaves every candidate one full vote (and reproduces this function before the
    parameter existed, which --gamma-identity checks). 0.0 collapses each group of identical
    candidates to a single vote. Only the MERGE evidence is weighted; the slot vote counts
    stay as they are, so the comparison isolates the clustering.
    """
    import compose
    from rapidfuzz.distance import Levenshtein

    tokens = [(i, p) for i, c in enumerate(cands) for p in range(len(c))]
    if not tokens:
        return []
    word = {(i, p): cands[i][p] for i, p in tokens}
    dsu = DSU(tokens)
    owners = {t: {t[0]} for t in tokens}   # which candidates a cluster already contains
    w = None if gamma == 1.0 else compose.cluster_weights(cands, gamma)
    links = pairwise_links(cands, w)

    cached = {"adj": None}

    def cluster_adj(force: bool = False):
        """Precedence between clusters, from each candidate's own word order.

        Rebuilt only after a merge lands: it is the hot path, and between two refused
        merges nothing about the clustering has changed.
        """
        if cached["adj"] is not None and not force:
            return cached["adj"]
        adj = defaultdict(set)
        for i, c in enumerate(cands):
            for p in range(len(c) - 1):
                a, b = dsu.find((i, p)), dsu.find((i, p + 1))
                if a != b:
                    adj[a].add(b)
        cached["adj"] = adj
        return adj

    # ---- intra-word: same word, strongest correspondence first
    same = [(cnt, a, b) for (a, b), cnt in links.items() if word[a] == word[b]]
    same.sort(key=lambda t: -t[0])
    for _, a, b in same:
        ra, rb = dsu.find(a), dsu.find(b)
        if ra == rb:
            continue
        adj = cluster_adj()
        if reachable(adj, ra, rb) or reachable(adj, rb, ra):
            continue                       # merging would make a class precede itself
        if owners[ra] & owners[rb]:
            continue                       # one candidate cannot be twice in one slot
        dsu.union(ra, rb)
        r = dsu.find(ra)
        owners[r] = owners[ra] | owners[rb]
        cluster_adj(force=True)

    # ---- inter-word: different words that compete, by character similarity
    diff = [(cnt, a, b) for (a, b), cnt in links.items() if word[a] != word[b]]
    scored = []
    for cnt, a, b in diff:
        wa, wb = word[a], word[b]
        s = similarity(wa, wb, phon)
        if s >= sim_threshold:
            scored.append((cnt * s, a, b))
    scored.sort(key=lambda t: -t[0])
    for _, a, b in scored:
        ra, rb = dsu.find(a), dsu.find(b)
        if ra == rb:
            continue
        adj = cluster_adj()
        if reachable(adj, ra, rb) or reachable(adj, rb, ra):
            continue
        if owners[ra] & owners[rb]:
            continue
        dsu.union(ra, rb)
        r = dsu.find(ra)
        owners[r] = owners[ra] | owners[rb]
        cluster_adj(force=True)

    # ---- order the clusters, then emit slots
    groups = defaultdict(list)
    for t in tokens:
        groups[dsu.find(t)].append(t)
    adj = cluster_adj()
    order = toposort(list(groups), adj, key=lambda g: sum(p for _, p in groups[g]) / len(groups[g]))
    K = len(cands)
    slots = []
    for g in order:
        slot = defaultdict(lambda: [0.0, 0.0])
        for (i, p) in groups[g]:
            w = cands[i][p]
            slot[w][0] += 1.0
            slot[w][1] += (confs[i][p] if confs and p < len(confs[i]) else 1.0)
        present = len({i for i, _ in groups[g]})
        slot[EPS] = [float(K - present), float(K - present)]
        slots.append(dict(slot))
    return slots


def toposort(nodes: list, adj: dict, key) -> list:
    """Kahn, ties broken by mean position so the result reads left to right."""
    indeg = {n: 0 for n in nodes}
    for a, bs in adj.items():
        for b in bs:
            if b in indeg:
                indeg[b] += 1
    ready = sorted([n for n in nodes if indeg[n] == 0], key=key)
    out = []
    while ready:
        n = ready.pop(0)
        out.append(n)
        for b in sorted(adj.get(n, ()), key=key):
            if b in indeg:
                indeg[b] -= 1
                if indeg[b] == 0:
                    ready.append(b)
        ready.sort(key=key)
    left = [n for n in nodes if n not in set(out)]      # cycles survived: append by position
    return out + sorted(left, key=key)


# ------------------------------------------------------------------------------- the checks

def candidate_is_path(slots: list[dict], cand: list[str]) -> bool:
    """Can this candidate be read off the network, in order, taking EPS elsewhere?"""
    k = 0
    for s in slots:
        if k < len(cand) and cand[k] in s:
            k += 1
    return k == len(cand)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=16)
    ap.add_argument("--max_utts", type=int, default=40)
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--eps", type=float, default=0.7)
    ap.add_argument("--sim", type=float, default=0.45)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--phon", action="store_true", help="CMUdict phonemes instead of characters")
    ap.add_argument("--cache", default="results/mangu_cache.pkl")
    a = ap.parse_args()

    sys.path.insert(0, "src")
    import bootstrap
    import compose
    from rapidfuzz.distance import Levenshtein
    from scorers import normalize

    cache = Path(a.cache)
    if cache.exists():
        rows = pickle.loads(cache.read_bytes())
    else:
        rows = []
        per = defaultdict(int)
        for job in sorted(glob.glob(f"{a.root}/dumps/{a.model}__*")):
            parts = Path(job).name.split("__")
            if len(parts) < 4 or parts[3] != a.arm:
                continue
            s = parts[1]
            p = Path(job) / f"{a.arm}.jsonl.gz"
            if not p.exists() or per[s] >= a.max_utts:
                continue
            with gzip.open(p, "rt", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    raw = r["candidates"][:a.k]
                    cs = [normalize(c["text"]).split() for c in raw]
                    keep = [i for i, (w, c) in enumerate(zip(cs, raw))
                            if w and "word_conf" in c and len(c["word_conf"]) == len(w)]
                    if len(keep) < 2:
                        continue
                    ref = normalize(r["reference"]).split()
                    if not ref:
                        continue
                    rows.append(dict(set=s, id=r["id"], ref=ref,
                                     cands=[cs[i] for i in keep],
                                     confs=[list(raw[i]["word_conf"]) for i in keep]))
                    per[s] += 1
                    if per[s] >= a.max_utts:
                        break
        cache.write_bytes(pickle.dumps(rows))
    print(f"{len(rows)} utterances, {len(set(r['set'] for r in rows))} sets, K<= {a.k}")

    # ---------------------------------------------------------------- checks before numbers
    single = sum(1 for r in rows[:100]
                 if build([r["cands"][0]], None) and
                 [w for s in build([r["cands"][0]], None) for w in s if w != EPS] == r["cands"][0])
    print(f"check, K=1 reproduces the candidate: {single}/100")
    ok = tot = 0
    for r in rows[:60]:
        sl = build(r["cands"], r["confs"], a.sim, a.gamma, a.phon)
        for c in r["cands"]:
            tot += 1
            ok += candidate_is_path(sl, c)
    print(f"check, every candidate is a path:    {ok}/{tot}  ({100 * ok / max(tot, 1):.1f} %)")
    if single < 100 or ok < tot:
        print("\nthe builder does not contain its own inputs; not reporting WER from it")
        return 1

    # ------------------------------------------------------------------------- the numbers
    print(f"\n{'network':<14}{'slots':>7}{'slot size':>11}{'ROVER':>9}{'or.comp':>9}"
          f"{'control':>9}{'margin':>8}")
    print("-" * 67)
    pool = sorted({w for r in rows for c in r["cands"] for w in c})
    out = {}
    for name in ("backbone", "mangu"):
        ed = cp = ct = R = 0.0
        ns = sz = 0
        per_utt = []
        for r in rows:
            if name == "backbone":
                bb = compose.central_index(r["cands"])
                sl = compose.confusion_network(r["cands"], bb, r["confs"], None)
            else:
                sl = build(r["cands"], r["confs"], a.sim, a.gamma, a.phon)
            hyp = compose.rover(sl, float(len(r["cands"])), a.alpha, a.eps)
            e = Levenshtein.distance(r["ref"], hyp)
            per_utt.append(e); ed += e; R += len(r["ref"])
            rng = random.Random(hash(r["id"]) & 0xFFFFFFFF)
            cp += compose.oracle_path(sl, r["ref"])
            ct += compose.oracle_path(compose.shuffled_control(sl, pool, rng), r["ref"])
            ns += len(sl); sz += sum(len(s) for s in sl)
        w = lambda x: 100.0 * x / R
        print(f"{name:<14}{ns / len(rows):>7.1f}{sz / max(ns, 1):>11.2f}{w(ed):>9.2f}"
              f"{w(cp):>9.2f}{w(ct):>9.2f}{w(ct) - w(cp):>8.2f}")
        out[name] = per_utt
    rl = [len(r["ref"]) for r in rows]
    st = bootstrap.paired_bootstrap(out["backbone"], out["mangu"], rl, n_boot=4000)
    flag = "" if st["ci_low"] > 0 or st["ci_high"] < 0 else "   spans zero"
    print("\n" + bootstrap.format_row("mangu vs backbone, ROVER", st) + flag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
