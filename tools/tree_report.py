#!/usr/bin/env python3
"""What each tree shape costs and what it gives, side by side with both ceilings.

Per arm: the realised width, diversity, the two selection rules, ROVER, and BOTH oracles --
the best whole candidate and the best path through the confusion network. The oracles are the
point of the comparison: a tree that keeps the composition ceiling while costing a third as
much is worth having even if the realised WER does not move.

Everything is contrasted against flat with a paired bootstrap over utterances, because a
second flat run with a different seed differed by 0.54 WER at 200 utterances, which is the
same size as the effects being claimed.

    PYTHONPATH=src python tools/tree_report.py results/trees/campaign [--norm whisper]
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import pandas as pd

import bootstrap

DEFAULT_K = 15          # src/decode.py pdd_decode, and the upstream README

ORDER = ["flat", "tree-early", "tree-late", "tree-deep", "flat-sched", "cond", "cond-tree",
         "adapt", "adapt-tree", "adapt-cond-tree"]


def load(root: Path) -> pd.DataFrame:
    parts = [pd.read_parquet(p) for p in glob.glob(str(root / "analysis" / "*.parquet"))
             if ".grid." not in p]
    if not parts:
        raise SystemExit(f"no analysis tables under {root}/analysis -- run campaign.analysis first")
    d = pd.concat(parts, ignore_index=True)
    return d[d.k == d.groupby(["set", "arm", "id"]).k.transform("max")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--norm", choices=["legacy", "whisper"], default="whisper")
    ap.add_argument("--n_boot", type=int, default=4000)
    args = ap.parse_args()

    d = load(Path(args.root))
    wn = args.norm == "whisper"
    ref = "ref_len_wn" if wn else "ref_len"
    col = {k: (f"wn_{k}" if wn else f"e_{k}") for k in
           ("mbr", "rover_cg", "oracle_cand")}
    col["oracle_comp"] = "e_oracle_comp"          # only computed on the legacy network
    if wn and d["wn_mbr"].isna().all():
        raise SystemExit("no Whisper-normalised columns; rerun analysis with whisper_normalizer")

    for s in sorted(d["set"].unique()):
        x = d[d["set"] == s]
        base = x[x.arm == "flat"].sort_values("id")
        print(f"\n{'=' * 104}\n{s}   ({args.norm} normalisation, n = {len(base)} utterances)"
              f"\n{'=' * 104}")
        print(f"{'arm':<16}{'K':>5}{'pair%':>7}{'dec s':>7}{'MBR':>8}{'ROVER':>8}{'gain':>7}"
              f"{'oracle cand':>13}{'oracle comp':>13}{'headroom':>10}")
        for a in [z for z in ORDER if z in set(x.arm)]:
            g = x[x.arm == a].sort_values("id")
            R = g[ref].sum()
            w = lambda c: 100.0 * g[c].sum() / R if R else float("nan")
            oc, ocomp = w(col["oracle_cand"]), w(col["oracle_comp"])
            print(f"{a:<16}{g.k.mean():>5.1f}{g.pairwise.mean():>7.1f}{g.decode_s.sum():>7.0f}"
                  f"{w(col['mbr']):>8.2f}{w(col['rover_cg']):>8.2f}"
                  f"{w(col['mbr']) - w(col['rover_cg']):>+7.2f}{oc:>13.2f}{ocomp:>13.2f}"
                  f"{oc - ocomp:>+10.2f}")

        print(f"\n{'-' * 104}\nagainst flat, paired bootstrap; positive means the arm is better"
              f"\n{'-' * 104}")
        for a in [z for z in ORDER if z in set(x.arm) and z != "flat"]:
            g = x[x.arm == a].sort_values("id")
            ids = set(base.id) & set(g.id)
            if len(ids) < 30:
                continue
            bb = base[base.id.isin(ids)].sort_values("id")
            gg = g[g.id.isin(ids)].sort_values("id")
            for label, c in (("ROVER", col["rover_cg"]), ("oracle comp", col["oracle_comp"])):
                st = bootstrap.paired_bootstrap(list(bb[c]), list(gg[c]), list(bb[ref]),
                                                n_boot=args.n_boot)
                flag = "" if st["ci_low"] > 0 or st["ci_high"] < 0 else "   spans zero"
                print(bootstrap.format_row(f"{a} vs flat, {label}", st) + flag)

    k_run = d.k.mean()
    print(f"\n{'-' * 104}\nflat here runs at K = {k_run:.0f}. Whisfusion's own default is "
          f"{DEFAULT_K}, so a saving measured against this flat is not a saving against the\n"
          f"model as it ships -- quote the K both numbers were taken at.\n{'-' * 104}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
