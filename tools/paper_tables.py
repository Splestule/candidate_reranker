#!/usr/bin/env python3
"""The tables and figures-worth-of-numbers the paper needs, from a campaign root.

    PYTHONPATH=src python tools/paper_tables.py <campaign_root> [--out results/paper]

Everything here is derived from results/per_utt_k.parquet, so it can be rerun offline on the
merged output of several sessions without touching a GPU.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

NOISE = {"ls-test-clean": ("clean", 99), "ls-tc-babble10": ("babble 10 dB", 10),
         "ls-tc-babble5": ("babble 5 dB", 5), "ls-tc-babble0": ("babble 0 dB", 0),
         "ls-tc-white5": ("white 5 dB", 5)}
MULTI = ["fleurs-de", "fleurs-fr", "fleurs-es", "fleurs-it", "fleurs-pt"]


def wer(g: pd.DataFrame, col: str) -> float:
    return 100.0 * g[col].sum() / max(g["ref_len"].sum(), 1)


def main_arms(df: pd.DataFrame) -> pd.DataFrame:
    """Each model's headline arm at its largest k."""
    m = df[(df["precision"] == "") & (df["kind"].isin(["main", "lowT"]))]
    keep = ((m["model"] == "drax") & (m["arm"].isin(["main", "lowT"]))) | \
           ((m["model"] == "whisfusion") & (m["arm"] == "main")) | \
           (m["model"].isin(["whisper-small", "whisper-turbo", "parakeet-ctc"]) & (m["arm"] == "sample"))
    m = m[keep]
    return m[m["k"] == m.groupby(["model", "arm"])["k"].transform("max")]


def t_noise(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (mod, arm), gm in m.groupby(["model", "arm"]):
        for s, (lab, snr) in NOISE.items():
            g = gm[gm["set"] == s]
            if g.empty:
                continue
            rows.append(dict(model=mod, arm=arm, condition=lab, snr_db=snr, n=len(g),
                             pairwise=g["pairwise"].mean(), first=wer(g, "e_first"),
                             conf=wer(g, "e_conf"), mbr=wer(g, "e_mbr"), rover=wer(g, "e_rover_cg"),
                             gain_vs_mbr=wer(g, "e_mbr") - wer(g, "e_rover_cg"),
                             gain_vs_conf=wer(g, "e_conf") - wer(g, "e_rover_cg"),
                             oracle_cand=wer(g, "e_oracle_cand"), oracle_comp=wer(g, "e_oracle_comp"),
                             control=wer(g, "e_control")))
    return pd.DataFrame(rows)


def t_cells(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (mod, arm, s), g in m.groupby(["model", "arm", "set"]):
        rows.append(dict(model=mod, arm=arm, set=s, lang=g["lang"].iloc[0], n=len(g), k=g["k"].iloc[0],
                         pairwise=g["pairwise"].mean(), unique=g["n_unique"].mean(),
                         first=wer(g, "e_first"), conf=wer(g, "e_conf"), mbr=wer(g, "e_mbr"),
                         rover_freq=wer(g, "e_rover_freq"), rover=wer(g, "e_rover_cg"),
                         gain_vs_mbr=wer(g, "e_mbr") - wer(g, "e_rover_cg"),
                         gain_vs_conf=wer(g, "e_conf") - wer(g, "e_rover_cg"),
                         oracle_cand=wer(g, "e_oracle_cand"), oracle_comp=wer(g, "e_oracle_comp"),
                         control=wer(g, "e_control")))
    return pd.DataFrame(rows)


def t_length(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (mod, arm), g in m.groupby(["model", "arm"]):
        g = g[~g["set"].isin(MULTI)]
        b = pd.cut(g["ref_len"], [0, 5, 10, 20, 10 ** 6], labels=["1-5", "6-10", "11-20", "21+"])
        for lab, gg in g.groupby(b, observed=True):
            rows.append(dict(model=mod, arm=arm, words=lab, n=len(gg), mbr=wer(gg, "e_mbr"),
                             rover=wer(gg, "e_rover_cg"),
                             gain=wer(gg, "e_mbr") - wer(gg, "e_rover_cg")))
    return pd.DataFrame(rows)


def t_headroom(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (mod, arm), g in m.groupby(["model", "arm"]):
        g = g[g["e_oracle_comp"].notna()]
        if g.empty:
            continue
        oc, cp, ct = wer(g, "e_oracle_cand"), wer(g, "e_oracle_comp"), wer(g, "e_control")
        rows.append(dict(model=mod, arm=arm, n=len(g), oracle_cand=oc, oracle_comp=cp, control=ct,
                         real_headroom=oc - cp, luck=oc - ct,
                         signal_to_luck=(oc - cp) / max(oc - ct, 1e-9),
                         beats_best_pct=100.0 * (g["e_oracle_comp"] < g["e_oracle_cand"]).mean()))
    return pd.DataFrame(rows)


def t_kscale(df: pd.DataFrame) -> pd.DataFrame:
    k = df[df["kind"] == "kscale"]
    rows = []
    for (mod, s, kk), g in k.groupby(["model", "set", "k"]):
        rows.append(dict(model=mod, set=s, k=kk, n=len(g), conf=wer(g, "e_conf"), mbr=wer(g, "e_mbr"),
                         rover=wer(g, "e_rover_cg"), oracle_cand=wer(g, "e_oracle_cand"),
                         oracle_comp=wer(g, "e_oracle_comp") if g["e_oracle_comp"].notna().all() else None))
    return pd.DataFrame(rows).sort_values(["model", "k"])


def t_sweep(df: pd.DataFrame) -> pd.DataFrame:
    s = df[df["kind"] == "sweepT"]
    s = s[s["k"] == s["k"].max()]
    rows = []
    for (mod, st, arm), g in s.groupby(["model", "set", "arm"]):
        rows.append(dict(model=mod, set=st, arm=arm, T=g["arm_T"].iloc[0], n=len(g),
                         unique=g["n_unique"].mean(), pairwise=g["pairwise"].mean(),
                         first=wer(g, "e_first"), conf=wer(g, "e_conf"), mbr=wer(g, "e_mbr"),
                         rover_freq=wer(g, "e_rover_freq"), rover=wer(g, "e_rover_cg"),
                         oracle_cand=wer(g, "e_oracle_cand"), oracle_comp=wer(g, "e_oracle_comp")))
    return pd.DataFrame(rows).sort_values(["model", "set", "T"])


def t_correlations(cells: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (mod, arm), g in cells.groupby(["model", "arm"]):
        if len(g) < 4:
            continue
        rows.append(dict(model=mod, arm=arm, n_cells=len(g),
                         r_gain_pairwise=g["gain_vs_mbr"].corr(g["pairwise"]),
                         r_gain_baseline=g["gain_vs_mbr"].corr(g["mbr"]),
                         r_gain_conf_pairwise=g["gain_vs_conf"].corr(g["pairwise"])))
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    root = Path(args.root)
    out = Path(args.out) if args.out else root / "results" / "paper"
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(root / "results" / "per_utt_k.parquet")
    m = main_arms(df)
    tables = {"noise_ladder": t_noise(m), "cells": t_cells(m), "by_length": t_length(m),
              "headroom": t_headroom(m), "k_scaling": t_kscale(df), "temperature_sweep": t_sweep(df)}
    tables["correlations"] = t_correlations(tables["cells"])
    for name, t in tables.items():
        if t is None or t.empty:
            continue
        t.round(3).to_csv(out / f"{name}.csv", index=False)
        print(f"\n=== {name}")
        print(t.round(2).to_string(index=False))
    print(f"\nwritten to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
