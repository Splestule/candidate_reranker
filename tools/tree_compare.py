#!/usr/bin/env python3
"""Does the final pipeline survive the cheaper tree-early decode?

tree-early shares the early denoising steps between candidates and costs 1.69x less than flat
sampling (run 8: 1.253 vs 2.115 s/utt, same K=32). On ROVER it lost 0.18 WER. The question
here is whether the learned combiner loses more or less than that.

Training is the same as in tools/final_compare.py (flat campaign candidates, every set except
the three the tree run covers). The fitted pipeline is then applied, unchanged, to the flat
and the tree-early candidates of the same utterances from the tree run.

    python3 tools/tree_compare.py --train results/audio_cache.pkl \\
        --flat results/tree_cache_flat.pkl --tree results/tree_cache_tree-early.pkl \\
        --dumps_root tdumps
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
from rapidfuzz.distance import Levenshtein

import crf_rover as F
import slot_lr as L
import slot_eval as S
import final_compare as FC

TREE_SETS = ("ls-test-other", "ami", "earnings22")
FIN = "+ neighbour + acoustic (final)"


def load(root, arm, sets, k):
    import gzip, json
    out = {}
    for s in sets:
        p = Path(root) / f"whisfusion__{s}__s00__{arm}" / f"{arm}.jsonl.gz"
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                out[(s, r["id"])] = (r["candidates"][:k], r.get("decode_s"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--flat", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--dumps_root", required=True)
    ap.add_argument("--audio", default="w2")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--lm_utts", type=int, default=1200)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    a = ap.parse_args()
    akey = f"aslots_{a.audio}"

    pool0 = [d for d in pickle.loads(Path(a.train).read_bytes()) if d["set"] not in TREE_SETS]
    arms = {"flat": pickle.loads(Path(a.flat).read_bytes()),
            "tree-early": pickle.loads(Path(a.tree).read_bytes())}
    keys = set.intersection(*[{(d["set"], d["id"]) for d in v} for v in arms.values()])
    for n in arms:
        arms[n] = sorted([d for d in arms[n] if (d["set"], d["id"]) in keys],
                         key=lambda d: (d["set"], d["id"]))
    cands = {n: load(a.dumps_root, n, TREE_SETS, a.k) for n in arms}
    test = arms["flat"]
    rl = np.array([len(d["ref"]) for d in test], float)
    R = rl.sum()
    print(f"training: {len(pool0)} flat campaign utterances on {len({d['set'] for d in pool0})} "
          f"sets; test: {len(test)} utterances on {', '.join(TREE_SETS)} ({int(R)} words), "
          f"both arms on the same utterances\n")
    for n in arms:
        ds = [cands[n][(d["set"], d["id"])][1] for d in arms[n]]
        ds = [x for x in ds if x is not None]
        if ds:
            print(f"  {n:<11} decode {np.mean(ds):.3f} s/utt (as logged by the tree run)")

    E = {}   # (arm, method) -> list over seeds of edit arrays
    for seed in [int(x) for x in a.seeds.split(",")]:
        pool = list(pool0)
        random.Random(seed).shuffle(pool)
        n_lm = min(a.lm_utts, len(pool) // 3)
        lm = F.Bigram([d["ref"] for d in pool[:n_lm]])
        tr = pool[n_lm:]
        al, ep, _ = min(((al, e, sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, e, S.POWER)
                                                  for s in d["slots"]], d["ref"]) for d in tr))
                         for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])
        models = {"slot model": (FC.fit_arm(tr, None, "", a), "", None),
                  "+ neighbour": (FC.fit_arm(tr, lm, "", a), "", lm),
                  FIN: (FC.fit_arm(tr, lm, akey, a), akey, lm)}
        print(f"seed {seed}: ROVER alpha {al} eps {ep}")
        for n, recs in arms.items():
            out = {}
            for d in recs:
                toks, conf, mbr = FC.whole(cands[n][(d["set"], d["id"])][0])
                tot = float(d["n_cand"])
                h = {"Whisfusion upstream (mean conf)": toks[FC.argmax(conf)],
                     "MBR": toks[FC.argmax(mbr)],
                     "ROVER tuned": [F.rover_pick(s, tot, al, ep, S.POWER) for s in d["slots"]]}
                for m, (mod, ak, l) in models.items():
                    h[m] = FC.apply_arm(d, mod, ak, l)
                h["candidate oracle"] = min(toks, key=lambda t: Levenshtein.distance(d["ref"], t))
                h["slot oracle"] = [r if (r in s or r == S.EPS) else F.rover_pick(s, tot, al, ep, S.POWER)
                                    for s, r in zip(d["slots"], d["ref_by_slot"])]
                for m, hy in h.items():
                    out.setdefault(m, []).append(F.edits_of(hy, d["ref"]))
            for m, v in out.items():
                E.setdefault((n, m), []).append(np.array(v, float))

    methods = [m for (n, m) in E if n == "flat"]
    print(f"\n{'method (seed-mean WER)':<34}{'flat':>8}{'tree-early':>12}{'tree - flat':>13}{'95% CI (seed 0)':>22}")
    for m in methods:
        f = np.mean([100 * x.sum() / R for x in E[("flat", m)]])
        t = np.mean([100 * x.sum() / R for x in E[("tree-early", m)]])
        o, lo, hi = S.bootstrap(E[("tree-early", m)][0], E[("flat", m)][0], rl)
        print(f"{m:<34}{f:>8.2f}{t:>12.2f}{t - f:>+13.2f}{f'[{lo:+.2f}, {hi:+.2f}]':>22}")
    print("  (tree - flat > 0 means tree-early is worse)")

    print("\nfinal pipeline vs baselines, within each arm (paired, per seed)")
    for n in arms:
        for base in ("MBR", "ROVER tuned"):
            cells = []
            for i in range(len(E[(n, FIN)])):
                o, lo, hi = S.bootstrap(E[(n, base)][min(i, len(E[(n, base)]) - 1)], E[(n, FIN)][i], rl, seed=i)
                cells.append(f"{o:+.2f} [{lo:+.2f},{hi:+.2f}]")
            print(f"  {n:<11} vs {base:<12}" + "   ".join(cells))

    print("\ncross-arm: tree-early + final pipeline vs flat + MBR / flat + ROVER tuned (seed 0)")
    for base in ("MBR", "ROVER tuned"):
        o, lo, hi = S.bootstrap(E[("flat", base)][0], E[("tree-early", FIN)][0], rl)
        print(f"  vs flat {base:<12}{o:+.2f} [{lo:+.2f}, {hi:+.2f}]")

    print("\nper set, seed 0: final pipeline WER flat / tree-early")
    for s in TREE_SETS:
        ix = np.array([i for i, d in enumerate(test) if d["set"] == s])
        if len(ix):
            f = 100 * E[("flat", FIN)][0][ix].sum() / rl[ix].sum()
            t = 100 * E[("tree-early", FIN)][0][ix].sum() / rl[ix].sum()
            print(f"  {s:<16}{f:>7.2f}{t:>9.2f}{t - f:>+8.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
