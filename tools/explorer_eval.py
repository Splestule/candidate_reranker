#!/usr/bin/env python3
"""Does a composition-aware explorer help? Anchor-only K candidates against K/2 anchor + K/2
LoRA explorer candidates (tools/train_explorer.py), and against K/2 anchor + K/2 from a LoRA
trained with the plain loss on the same data (the control for fine-tuning alone).

Same frozen composition pipeline and set-level cross-validation as tools/confirm_eval.py:
train on shard 0 of the sets outside the fold, test on the fold's sets at --test_shard.

    python3 tools/explorer_eval.py --cand results/explorer/cand_audio.pkl | tee results/explorer/eval.txt
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np

import crf_rover as F
import slot_eval as S
import final_compare as FC
import k_curve as KC
import confirm_eval as CE


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    ap.add_argument("--ks", default="4,8")
    ap.add_argument("--test_shard", type=int, default=1)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--lm_utts", type=int, default=600)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    a = ap.parse_args()
    recs = pickle.loads(Path(a.cand).read_bytes())
    ks = [int(x) for x in a.ks.split(",")]
    arms = [f"{p}-k{k}" for k in ks for p in ("anchor", "mix-plain", "mix-expl")]
    arms = [x for x in arms if any(r["arm"] == x for r in recs)]
    B = {}
    for arm in arms:
        k = int(arm.rsplit("-k", 1)[1])
        B[arm] = {}
        for r in recs:
            if r["arm"] != arm:
                continue
            b = KC.build(r, k)
            if b is None:
                continue
            b.update(shard=r.get("shard"), src=[c.get("source", "anchor") for c in r["cands"][:k]])
            B[arm][(b["set"], b["id"])] = b
    test = set.intersection(*[{kk for kk, d in B[x].items() if d["shard"] == a.test_shard
                               and kk[0] in CE.TEST_SETS} for x in arms])
    keys = sorted(test)
    print(f"test: {len(keys)} utterances on {len({k[0] for k in keys})} sets; arms {arms}\n", flush=True)
    akey = "aslots_w2"
    seeds = [int(x) for x in a.seeds.split(",")]
    E = {}
    for seed in seeds:
        for arm in arms:
            H = {}
            for fold in FC.FOLDS:
                tr = [d for d in B[arm].values() if d["shard"] != a.test_shard and d["set"] not in fold]
                ev = [B[arm][kk] for kk in keys if kk[0] in fold]
                H.update(CE.apply_all(ev, CE.fit_all(tr, akey, seed, a, None, None), akey, None, None))
            for m in H[keys[0]]:
                E[(seed, arm, m)] = np.array([F.edits_of(H[kk][m], B[arm][kk]["ref"]) for kk in keys], float)
            # slot oracle: the reference word wherever the network has it
            E[(seed, arm, "slot oracle")] = np.array([F.edits_of(
                [r if (r in s or r == S.EPS) else S.top_word(s) for s, r in zip(B[arm][kk]["slots"], B[arm][kk]["ref_by_slot"])],
                B[arm][kk]["ref"]) for kk in keys], float)
        print(f"seed {seed} done", flush=True)
    rl = np.array([len(B[arms[0]][kk]["ref"]) for kk in keys], float)

    methods = [CE.UP, CE.MBR, CE.ROV, CE.IRO, CE.FIN, CE.ORA, "slot oracle"]
    print(f"{'arm':<14}" + "".join(f"{m[:16]:>18}" for m in methods))
    for arm in arms:
        print(f"{arm:<14}" + "".join(f"{np.mean([100 * E[(s, arm, m)].sum() / rl.sum() for s in seeds]):18.2f}"
                                     for m in methods))

    print("\nper-candidate WER by source (mean over candidates)")
    for arm in arms:
        by = {"anchor": [], "explorer": []}
        for kk in keys:
            d = B[arm][kk]
            for t, s in zip(d["toks"], d["src"]):
                by[s].append(F.edits_of(t, d["ref"]) / max(len(d["ref"]), 1))
        print(f"  {arm:<14}" + "  ".join(f"{s} {100 * np.mean(v):.2f}" for s, v in by.items() if v))

    print("\npaired bootstrap, positive = second arm better")
    for k in ks:
        for m in (CE.FIN, CE.ROV, "slot oracle"):
            for base, arm in ((f"anchor-k{k}", f"mix-expl-k{k}"), (f"mix-plain-k{k}", f"mix-expl-k{k}"),
                              (f"anchor-k{k}", f"mix-plain-k{k}")):
                if base not in arms or arm not in arms:
                    continue
                for s in seeds[:1] if m == "slot oracle" else seeds:
                    o, lo, hi = S.bootstrap(E[(s, base, m)], E[(s, arm, m)], rl, seed=s)
                    print(f"  K={k:<2} {m:<12} {base:<13} -> {arm:<13} seed {s}: {o:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
