#!/usr/bin/env python3
"""Tune ROVER's voting parameters on the grid the analysis already wrote.

Nothing is decoded and nothing is re-composed: analysis.py evaluated every (alpha, eps,
gamma) combination per utterance at the main k and stored the edit counts, so tuning is a
groupby. What it answers is how much of the gap to the composition oracle the existing
voting rule leaves on the table before any learned model exists.

Tuning and reporting must not touch the same data. Two splits are reported:

  leave-one-set-out  tune on the other sets, apply to the held-out one. The honest number
                     when the question is "will this transfer to a corpus I did not tune on".
  cluster split      within each set, tune on half the speakers/recordings and apply to the
                     other half. Bounds what tuning is worth on a corpus of the same kind.

    PYTHONPATH=src python tools/tune_rover.py results/branch/campaign --arm flat
"""

from __future__ import annotations

import argparse
import glob
import sys
import zlib
from pathlib import Path

import pandas as pd

DEFAULT = dict(alpha=0.5, eps=0.7, gamma=0.5)      # analysis.ROVER_DEFAULT, what we run today
KEYS = ["alpha", "eps", "gamma"]


def load(root: Path, arm: str | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    grid = [p for p in glob.glob(str(root / "analysis" / "*.grid.parquet"))]
    flat = [p for p in glob.glob(str(root / "analysis" / "*.parquet")) if ".grid." not in p]
    if not grid:
        raise SystemExit(f"no *.grid.parquet under {root}/analysis")
    g = pd.concat([pd.read_parquet(p) for p in grid], ignore_index=True)
    d = pd.concat([pd.read_parquet(p) for p in flat], ignore_index=True)
    g = g[g.param == "rover"]
    if arm:
        g, d = g[g.arm == arm], d[d.arm == arm]
    d = d[d.k == d.groupby(["set", "arm", "id"]).k.transform("max")]
    return g, d


def wer(df: pd.DataFrame) -> float:
    r = df.ref_len.sum()
    return 100.0 * df.e.sum() / r if r else float("nan")


def best_params(df: pd.DataFrame) -> tuple[dict, float]:
    s = df.groupby(KEYS).apply(wer, include_groups=False)
    p = s.idxmin()
    return dict(zip(KEYS, p)), float(s.min())


def pick(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    m = pd.Series(True, index=df.index)
    for k in KEYS:
        m &= df[k] == p[k]
    return df[m]


def half(cluster: str) -> int:
    return zlib.crc32(str(cluster).encode("utf-8")) & 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--arm", default="flat", help="which decode arm to tune on ('' = all)")
    args = ap.parse_args()

    g, d = load(Path(args.root), args.arm or None)
    sets = sorted(g["set"].unique())
    print(f"{len(g)} grid rows, {g.id.nunique()} utterances, sets {sets}, arm {args.arm or 'all'}")
    print(f"current setting: alpha={DEFAULT['alpha']} eps={DEFAULT['eps']} gamma={DEFAULT['gamma']}\n")

    # ------------------------------------------------------------------ whole-grid picture
    print("best and worst of the 45 combinations, scored on everything (NOT a held-out number)")
    s = g.groupby(KEYS).apply(wer, include_groups=False).sort_values()
    cur = wer(pick(g, DEFAULT))
    print(f"  current                          {cur:6.2f}")
    for (a, e, ga), v in list(s.items())[:3]:
        print(f"  best    alpha {a:<5} eps {e:<5} gamma {ga:<5} {v:6.2f}   ({v - cur:+.2f})")
    for (a, e, ga), v in list(s.items())[-2:]:
        print(f"  worst   alpha {a:<5} eps {e:<5} gamma {ga:<5} {v:6.2f}   ({v - cur:+.2f})")

    # ------------------------------------------------------------------- leave one set out
    print("\nleave-one-set-out: parameters chosen on the other sets, applied to this one")
    print(f"  {'held-out set':<18}{'tuned on others':<28}{'current':>9}{'tuned':>9}{'delta':>8}")
    tot_cur = tot_new = tot_ref = 0.0
    for s_out in sets:
        tr, te = g[g["set"] != s_out], g[g["set"] == s_out]
        if tr.empty:
            continue
        p, _ = best_params(tr)
        a, b = pick(te, DEFAULT), pick(te, p)
        tot_cur += a.e.sum(); tot_new += b.e.sum(); tot_ref += a.ref_len.sum()
        lbl = f"a {p['alpha']} e {p['eps']} g {p['gamma']}"
        print(f"  {s_out:<18}{lbl:<28}{wer(a):>9.2f}{wer(b):>9.2f}{wer(b) - wer(a):>+8.2f}")
    if tot_ref:
        print(f"  {'POOLED':<18}{'':<28}{100*tot_cur/tot_ref:>9.2f}{100*tot_new/tot_ref:>9.2f}"
              f"{100*(tot_new - tot_cur)/tot_ref:>+8.2f}")

    # --------------------------------------------------------------- cluster split per set
    print("\ncluster split: half the speakers/recordings tune, the other half is scored")
    print(f"  {'set':<18}{'tuned on half A':<28}{'current':>9}{'tuned':>9}{'delta':>8}")
    for s_ in sets:
        x = g[g["set"] == s_].copy()
        x["h"] = x.cluster.map(half)
        tr, te = x[x.h == 0], x[x.h == 1]
        if tr.empty or te.empty:
            continue
        p, _ = best_params(tr)
        a, b = pick(te, DEFAULT), pick(te, p)
        lbl = f"a {p['alpha']} e {p['eps']} g {p['gamma']}"
        print(f"  {s_:<18}{lbl:<28}{wer(a):>9.2f}{wer(b):>9.2f}{wer(b) - wer(a):>+8.2f}")

    # ------------------------------------------------------- what is left for a real model
    print("\nwhere tuning leaves us against the ceiling (same utterances, legacy space)")
    print(f"  {'set':<18}{'current':>9}{'best tuned':>12}{'oracle comp':>13}{'gap left':>10}{'capt%':>7}")
    for s_ in sets + [None]:
        gg = g if s_ is None else g[g["set"] == s_]
        dd = d if s_ is None else d[d["set"] == s_]
        dd = dd[dd.e_oracle_comp.notna()]
        if dd.empty:
            continue
        p, tuned = best_params(gg)
        cur_ = wer(pick(gg, DEFAULT))
        R = dd.ref_len.sum()
        ocp = 100.0 * dd.e_oracle_comp.sum() / R
        mbr = 100.0 * dd.e_mbr.sum() / R
        print(f"  {(s_ or 'ALL'):<18}{cur_:>9.2f}{tuned:>12.2f}{ocp:>13.2f}{tuned - ocp:>10.2f}"
              f"{100*(mbr - tuned)/(mbr - ocp):>7.1f}")
    print("\n  (best tuned is fitted on the same data it is scored on -- an upper bound on")
    print("   what tuning can do, not a result. The held-out tables above are the result.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
