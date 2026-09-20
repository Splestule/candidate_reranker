#!/usr/bin/env python3
"""Accuracy against decoding cost: composing K candidates vs selecting one of them.

    PYTHONPATH=src python tools/fig_cost_quality.py <campaign_root> --out results/paper/fig_cost_quality

One figure, one axis: WER on the y, measured decode+encode seconds per utterance on the x
(log, because cost spans two orders of magnitude). Each line walks the same K ladder from one
candidate to the largest pool; the vertical gap between a solid and a dashed line of the same
colour is what composition buys at equal compute, and the horizontal gap is the compute it
saves at equal accuracy.

Costs are measured on one T4 in the campaign itself (timing.csv): a candidate is 72.8 ms for
Whisfusion at 4 steps and 222 ms for Drax at 16 steps, plus a K-independent encoder pass.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

# dataviz reference palette, slots 1 and 2; validated for all pairs in light mode
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8983"
SURFACE = "#ffffff"

MODELS = [
    # label, model, job kind, arm, encoder s, per-candidate s, colour, and the hand-placed
    # annotation slots: the curves converge differently, so no rule puts these automatically
    ("Whisfusion", "whisfusion", "main", "main", 0.038, 0.0728, BLUE,
     dict(name_xy=(0.098, 22.3), k_below=(1, 4), k_right=(32,),
          note_xy=(2.75, 13.47), note_ha="left", note_va="center")),
    ("Drax", "drax", "kscale", "K64", 0.186, 0.2222, ORANGE,
     dict(name_xy=(0.37, 11.4), k_below=(1, 4), k_right=(64,),
          note_xy=(7.0, 6.15), note_ha="center", note_va="bottom", arrow_y=4.35)),
]
SET = "ls-test-other"
MARK_K = (1, 2, 4, 8, 16, 32, 64)


def resolve(root: Path, default_out: str) -> tuple[Path, Path]:
    """Accept a campaign root as the orchestrator leaves it, with everything under
    <root>/results/, or as the results directory is checked into the repo, with the parquet at
    the top and the derived files beside it."""
    if (root / "results" / "per_utt_k.parquet").exists():
        return root / "results" / "per_utt_k.parquet", root / "results" / default_out
    return root / "per_utt_k.parquet", root / default_out


def ladder(df: pd.DataFrame, model: str, kind: str, arm: str, enc: float, per: float) -> pd.DataFrame:
    g = df[(df["set"] == SET) & (df["model"] == model) & (df["kind"] == kind) & (df["arm"] == arm)]
    rows = []
    for k, gk in g.groupby("k"):
        w = gk["ref_len"].sum()
        rows.append(dict(k=int(k), cost=enc + per * int(k),
                         mbr=100 * gk["e_mbr"].sum() / w,
                         rover=100 * gk["e_rover_cg"].sum() / w))
    return pd.DataFrame(rows).sort_values("k")


def iso_arrow(ax, lad: pd.DataFrame, colour: str, st: dict):
    """Where composition reaches the best WER selection ever reaches, and at what saving."""
    best_sel = lad["mbr"].min()
    hit = lad[lad["rover"] <= best_sel]
    if hit.empty:
        return
    x0 = float(hit["cost"].iloc[0])
    x1 = float(lad.loc[lad["mbr"].idxmin(), "cost"])
    # where the curves are nearly flat the arrow would disappear into them: drop it below and
    # tie each end back to the point it refers to
    y = st.get("arrow_y", best_sel)
    if y != best_sel:
        for x in (x0, x1):
            ax.plot([x, x], [y, best_sel], color=colour, lw=0.9, ls=(0, (1.5, 1.5)), zorder=2)
    ax.annotate("", xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.3, shrinkA=1, shrinkB=1,
                                mutation_scale=11))
    ax.text(*st["note_xy"], f"{x1 / x0:.0f}× less compute\nfor the same WER", color=colour,
            fontsize=8.5, ha=st["note_ha"], va=st["note_va"], linespacing=1.35, zorder=6)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    src, default_out = resolve(Path(args.root), "figures")
    out = Path(args.out) if args.out else default_out / "fig_cost_quality"
    out.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(src)

    fig, ax = plt.subplots(figsize=(7.6, 5.0), dpi=220)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    for label, model, kind, arm, enc, per, colour, st in MODELS:
        lad = ladder(df, model, kind, arm, enc, per)
        if lad.empty:
            continue
        marks = lad[lad["k"].isin(MARK_K)]
        ax.plot(lad["cost"], lad["mbr"], color=colour, lw=1.9, ls=(0, (5, 2.2)), zorder=3)
        ax.plot(marks["cost"], marks["mbr"], ls="none", marker="o", ms=5, color=colour,
                mfc=SURFACE, mew=1.6, zorder=3)
        ax.plot(lad["cost"], lad["rover"], color=colour, lw=2.2, zorder=4)
        ax.plot(marks["cost"], marks["rover"], ls="none", marker="o", ms=5.5, color=colour,
                mec=SURFACE, mew=1.2, zorder=4)
        # the model is named once, where its two curves meet at K = 1; solid vs dashed is the
        # legend's job, so nothing has to be written twice
        ax.text(*st["name_xy"], label, color=colour, fontsize=11, fontweight="bold", ha="left",
                va="bottom")
        for k in st["k_below"]:
            r = lad[lad["k"] == k]
            if not r.empty:
                ax.annotate(f"K={k}", (r["cost"].iloc[0], r["rover"].iloc[0]),
                            textcoords="offset points", xytext=(0, -14), ha="center",
                            fontsize=7.5, color=INK3)
        for k in st["k_right"]:
            r = lad[lad["k"] == k]
            if not r.empty:
                ax.annotate(f"K={k}", (r["cost"].iloc[0], r["rover"].iloc[0]),
                            textcoords="offset points", xytext=(9, -3), ha="left",
                            fontsize=7.5, color=INK3)
        iso_arrow(ax, lad, colour, st)

    ax.set_xscale("log")
    ax.set_xlim(0.085, 22)
    ax.set_ylim(3.2, 23.5)
    ax.set_xticks([0.1, 0.25, 0.5, 1, 2, 4, 8, 16])
    ax.set_xticklabels(["0.1", "0.25", "0.5", "1", "2", "4", "8", "16"])
    ax.set_xlabel("decoding cost per utterance (seconds on one T4, log scale)", fontsize=10, color=INK2)
    ax.set_ylabel("word error rate (%)", fontsize=10, color=INK2)
    ax.grid(True, which="major", axis="both", color="#e8e8e4", lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#d8d8d2")
    ax.tick_params(colors=INK2, labelsize=9, length=3)

    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], color=INK2, lw=1.9, ls=(0, (5, 2.2)), marker="o", ms=5,
                              mfc=SURFACE, mew=1.6, label="select one candidate (MBR)"),
                       Line2D([], [], color=INK2, lw=2.2, marker="o", ms=5.5, mec=SURFACE,
                              mew=1.2, label="compose the candidates (ROVER)")],
              loc="upper right", frameon=False, fontsize=9.5, labelcolor=INK2,
              handlelength=2.8, borderpad=0.2, labelspacing=0.5)

    ax.set_title("Composing candidates buys more accuracy per second than selecting one",
                 fontsize=13, color=INK, loc="left", pad=34, fontweight="bold")
    ax.text(0, 1.075, "LibriSpeech test-other. Each curve walks the candidate pool from K = 1 to 32 "
                      "(Whisfusion) or 64 (Drax);",
            transform=ax.transAxes, fontsize=9, color=INK2)
    ax.text(0, 1.028, "cost is the measured decode plus encode time per utterance on one T4.",
            transform=ax.transAxes, fontsize=9, color=INK2)

    fig.tight_layout()
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out.with_suffix(f".{ext}"), facecolor=SURFACE, bbox_inches="tight")
    print(f"written: {out.with_suffix('.png')} (+ pdf, svg)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
