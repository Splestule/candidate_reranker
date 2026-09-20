#!/usr/bin/env python3
"""Everything the paper needs, from the per-utterance tables analysis.py wrote.

Outputs, under <root>/results/:

    per_utt_k.parquet, per_utt_k.csv.gz   one row per (model, set, arm, utterance, k): edits of
                                          every method; the source for any further statistics
    grid.parquet                          ROVER / selection parameter grid at the main k
    cells.csv                             corpus and mean-utterance WER of every method per
                                          (model, set, job kind, arm, k), with diversity
    contrasts.csv                         paired comparisons within an arm: delta, utterance and
                                          cluster bootstrap CIs, Wilcoxon p, wins / ties / losses
    cross_arm.csv                         composition against each model's standard decoding
                                          (Drax at low temperature, Whisper greedy / beam, CTC
                                          greedy, Whisfusion's own K=15 confidence pick)
    tuned.csv                             parameters picked on dev, reported on every test cell
    meta_analysis.csv                     random-effects pooling of the main contrast over sets
    timing.csv                            RTF, encoder / decoder split, ROVER CPU cost
    campaign_summary.json, REPORT.md

Deltas are WER(first) - WER(second) in points: positive means the second system is better.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from campaign import config as C  # noqa: E402

METHODS = ["first", "conf", "minconf", "logprob", "mbr", "cm05", "cm15", "rover_freq", "rover_c",
           "rover_cg", "oracle_cand", "oracle_comp", "control", "anti"]
WN_METHODS = ["first", "conf", "mbr", "cm05", "rover_freq", "rover_c", "rover_cg", "oracle_cand"]
CELL = ["model", "precision", "set", "kind", "arm", "k"]
WITHIN = [("conf", "rover_cg"), ("mbr", "rover_cg"), ("cm05", "rover_cg"), ("conf", "rover_c"),
          ("conf", "rover_freq"), ("first", "rover_cg"), ("conf", "mbr"), ("first", "conf"),
          ("rover_freq", "rover_cg")]
N_BOOT = 2000


# ---------------------------------------------------------------------------------- stats

def boot_delta(ea, eb, words, clusters=None, n_boot=N_BOOT, seed=0) -> dict:
    """Paired bootstrap of corpus WER(a) - WER(b), over utterances and over clusters."""
    ea, eb, w = (np.asarray(x, dtype=np.float64) for x in (ea, eb, words))
    n = len(w)
    if n == 0 or w.sum() == 0:
        return {}
    obs = 100.0 * (ea.sum() - eb.sum()) / w.sum()
    rng = np.random.default_rng(seed)
    d = np.empty(n_boot)
    step = max(1, min(n_boot, 4_000_000 // max(n, 1)))
    for s in range(0, n_boot, step):
        m = min(step, n_boot - s)
        idx = rng.integers(0, n, size=(m, n))
        d[s:s + m] = 100.0 * (ea[idx].sum(1) - eb[idx].sum(1)) / w[idx].sum(1)
    out = dict(delta=obs, ci_low=float(np.percentile(d, 2.5)), ci_high=float(np.percentile(d, 97.5)),
               se=float(d.std(ddof=1)), p_boot=float((d <= 0).mean()),
               n=n, n_better=int((eb < ea).sum()), n_worse=int((eb > ea).sum()), n_tied=int((ea == eb).sum()))
    if clusters is not None:
        cdf = pd.DataFrame({"c": clusters, "a": ea, "b": eb, "w": w}).groupby("c").sum()
        nc = len(cdf)
        out["n_clusters"] = nc
        if 5 <= nc < n:
            ca, cb, cw = cdf["a"].to_numpy(), cdf["b"].to_numpy(), cdf["w"].to_numpy()
            dc = np.empty(n_boot)
            step = max(1, min(n_boot, 4_000_000 // nc))
            for s in range(0, n_boot, step):
                m = min(step, n_boot - s)
                idx = rng.integers(0, nc, size=(m, nc))
                dc[s:s + m] = 100.0 * (ca[idx].sum(1) - cb[idx].sum(1)) / np.maximum(cw[idx].sum(1), 1)
            out.update(cl_ci_low=float(np.percentile(dc, 2.5)), cl_ci_high=float(np.percentile(dc, 97.5)))
    try:
        from scipy.stats import wilcoxon
        diff = ea - eb
        out["p_wilcoxon"] = float(wilcoxon(diff).pvalue) if np.any(diff != 0) else 1.0
    except Exception:
        out["p_wilcoxon"] = None
    return out


def random_effects(deltas: list[float], ses: list[float]) -> dict:
    """DerSimonian-Laird pooling of per-set deltas."""
    d, s = np.asarray(deltas, float), np.asarray(ses, float)
    ok = s > 0
    d, s = d[ok], s[ok]
    k = len(d)
    if k == 0:
        return {}
    w = 1.0 / s ** 2
    fixed = float((w * d).sum() / w.sum())
    q = float((w * (d - fixed) ** 2).sum())
    tau2 = max(0.0, (q - (k - 1)) / (w.sum() - (w ** 2).sum() / w.sum())) if k > 1 else 0.0
    wr = 1.0 / (s ** 2 + tau2)
    est = float((wr * d).sum() / wr.sum())
    se = float(math.sqrt(1.0 / wr.sum()))
    i2 = max(0.0, (q - (k - 1)) / q) if q > 0 and k > 1 else 0.0
    return dict(k_sets=k, pooled=est, ci_low=est - 1.96 * se, ci_high=est + 1.96 * se, tau2=tau2, I2=i2,
                n_positive=int((d > 0).sum()))


# ---------------------------------------------------------------------------------- tables

def load_tables(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    per, grid = [], []
    for p in sorted((root / "analysis").glob("*.parquet")):
        try:
            df = pd.read_parquet(p)
        except Exception as e:
            print(f"[aggregate] unreadable {p.name}: {e}", flush=True)
            continue
        (grid if p.name.endswith(".grid.parquet") else per).append(df)
    per_df = pd.concat(per, ignore_index=True) if per else pd.DataFrame()
    grid_df = pd.concat(grid, ignore_index=True) if grid else pd.DataFrame()
    if not per_df.empty:
        per_df["precision"] = per_df["precision"].fillna("")
        per_df = per_df.drop_duplicates(subset=CELL + ["id"], keep="last")
    if not grid_df.empty:
        grid_df["precision"] = grid_df["precision"].fillna("")
    return per_df, grid_df


def cells_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(CELL, sort=True):
        words = g["ref_len"].sum()
        r = dict(zip(CELL, key), n=len(g), words=int(words), audio_min=round(g["duration_s"].sum() / 60, 2),
                 n_clusters=g["cluster"].nunique(), mean_unique=g["n_unique"].mean(),
                 mean_pairwise=g["pairwise"].mean(), conf_frac=g["conf_frac"].mean(),
                 lang=g["lang"].iloc[0])
        for m in METHODS:
            col = f"e_{m}"
            if col in g and g[col].notna().all():
                r[f"wer_{m}"] = 100.0 * g[col].sum() / max(words, 1)
                r[f"mu_{m}"] = 100.0 * (g[col] / g["ref_len"].clip(lower=1)).mean()
        if "ref_len_wn" in g and g["ref_len_wn"].notna().all():
            wwn = g["ref_len_wn"].sum()
            for m in WN_METHODS:
                col = f"wn_{m}"
                if col in g and g[col].notna().all():
                    r[f"wn_wer_{m}"] = 100.0 * g[col].sum() / max(wwn, 1)
        if "e_oracle_cand" in g and g["e_oracle_comp"].notna().all():
            r["beats_best_pct"] = 100.0 * (g["e_oracle_comp"] < g["e_oracle_cand"]).mean()
        rows.append(r)
    return pd.DataFrame(rows)


def main_k(df_cell: pd.DataFrame) -> int:
    return int(df_cell["k"].max())


def contrasts_table(df: pd.DataFrame, k_extra=(16,)) -> pd.DataFrame:
    """Paired contrasts for the arms the paper reports. Sweeps and ablations are summarised by
    cells.csv; running every bootstrap for them too costs minutes and says nothing new."""
    rows = []
    df = df[df["kind"].isin(["main", "kscale", "lowT"])]
    for key, g in df.groupby(["model", "precision", "set", "kind", "arm"], sort=True):
        kmax = int(g["k"].max())
        for k in sorted({kmax, *[x for x in k_extra if x < kmax and (g["k"] == x).any()]}):
            gk = g[g["k"] == k]
            for a, b in WITHIN:
                for pre, words_col in (("e_", "ref_len"), ("wn_", "ref_len_wn")):
                    ca, cb = f"{pre}{a}", f"{pre}{b}"
                    if ca not in gk or cb not in gk or gk[ca].isna().any() or gk[cb].isna().any():
                        continue
                    if gk[words_col].isna().any():
                        continue
                    s = boot_delta(gk[ca], gk[cb], gk[words_col], gk["cluster"].to_numpy())
                    if s:
                        rows.append(dict(zip(["model", "precision", "set", "kind", "arm"], key), k=k,
                                         k_is_main=(k == kmax), norm="legacy" if pre == "e_" else "whisper",
                                         a=a, b=b, **s))
    return pd.DataFrame(rows)


def _paired(df_a: pd.DataFrame, col_a: str, df_b: pd.DataFrame, col_b: str):
    m = df_a[["id", "cluster", "ref_len", col_a]].merge(df_b[["id", col_b]], on="id", suffixes=("_a", "_b"))
    ca = col_a + "_a" if col_a == col_b else col_a
    cb = col_b + "_b" if col_a == col_b else col_b
    return m, ca, cb


def cross_arm_table(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Composition from a model's candidate pool against that model's standard decoding."""
    rows = []
    # (model, (kind, arm, k, method) for a, the same for b, label); a and b may live in
    # different job kinds, e.g. Drax's standard decode against its low-temperature pool
    specs = []
    kd = cfg["k_main"]["drax"]
    kw = cfg["k_main"]["whisfusion"]
    lo = cfg.get("drax_low_T", 0.4)
    ref_K = cfg["drax"]["ref_K"]
    specs += [("drax", ("main", "ref", 1, "first"), ("main", "main", kd, "rover_cg"), "Drax standard (T=0.1, 1 sample) vs ROVER@main"),
              ("drax", ("main", "ref", 1, "first"), ("main", "main", kd, "conf"), "Drax standard vs confidence pick@main"),
              ("drax", ("main", "ref", 1, "first"), ("main", "main", kd, "mbr"), "Drax standard vs MBR pick@main"),
              ("drax", ("main", "ref", ref_K, "rover_cg"), ("main", "main", kd, "rover_cg"), "ROVER@T=0.1 vs ROVER@main"),
              ("drax", ("main", "ref", 1, "first"), ("lowT", "lowT", kd, "rover_cg"), f"Drax standard vs ROVER@T={lo:g}"),
              ("drax", ("main", "ref", 1, "first"), ("lowT", "lowT", kd, "mbr"), f"Drax standard vs MBR@T={lo:g}"),
              ("drax", ("lowT", "lowT", kd, "mbr"), ("lowT", "lowT", kd, "rover_cg"), f"MBR vs ROVER, both @T={lo:g}"),
              ("drax", ("main", "main", kd, "rover_cg"), ("lowT", "lowT", kd, "rover_cg"), f"ROVER@main vs ROVER@T={lo:g}"),
              ("whisfusion", ("main", "main", 15, "conf"), ("main", "main", kw, "rover_cg"),
               "Whisfusion upstream (K=15 confidence) vs ROVER@main"),
              ("whisfusion", ("main", "main", 15, "conf"), ("main", "main", 15, "rover_cg"),
               "Whisfusion upstream vs ROVER at the same K=15")]
    for m in ("whisper-small", "whisper-turbo"):
        K = cfg["whisper_sample"]["K"]
        B = cfg["whisper_beams"]
        specs += [(m, ("main", "greedy", 1, "first"), ("main", "sample", K, "rover_cg"), "greedy vs ROVER over samples"),
                  (m, ("main", "greedy", 1, "first"), ("main", "beam", B, "rover_cg"), "greedy vs ROVER over beam n-best"),
                  (m, ("main", "beam", 1, "first"), ("main", "beam", B, "rover_cg"), "top beam vs ROVER over n-best"),
                  (m, ("main", "greedy", 1, "first"), ("main", "sample", K, "mbr"), "greedy vs MBR over samples")]
    specs += [("parakeet-ctc", ("main", "greedy", 1, "first"),
               ("main", "sample", cfg["ctc_sample"]["K"], "rover_cg"), "greedy vs ROVER over sampled CTC paths")]

    for model, (kind_a, arm_a, k_a, m_a), (kind_b, arm_b, k_b, m_b), label in specs:
        base = df[(df["model"] == model) & (df["precision"] == "")]
        for s, g in base.groupby("set"):
            ga = g[(g["kind"] == kind_a) & (g["arm"] == arm_a) & (g["k"] == k_a)]
            gb = g[(g["kind"] == kind_b) & (g["arm"] == arm_b) & (g["k"] == k_b)]
            if ga.empty or gb.empty:
                continue
            m, ca, cb = _paired(ga, f"e_{m_a}", gb, f"e_{m_b}")
            if m.empty:
                continue
            st = boot_delta(m[ca], m[cb], m["ref_len"], m["cluster"].to_numpy())
            if st:
                rows.append(dict(model=model, set=s, label=label, a=f"{m_a}@{arm_a}/k{k_a}",
                                 b=f"{m_b}@{arm_b}/k{k_b}",
                                 wer_a=100.0 * m[ca].sum() / m["ref_len"].sum(),
                                 wer_b=100.0 * m[cb].sum() / m["ref_len"].sum(), **st))
    return pd.DataFrame(rows)


def tuned_table(df: pd.DataFrame, grid: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Pick lambda and (alpha, eps, gamma) on dev, per model; report tuned systems on test."""
    if grid.empty:
        return pd.DataFrame(), {}
    rows, chosen = [], {}
    main_arms = {"drax": "main", "whisfusion": "main", "whisper-small": "sample",
                 "whisper-turbo": "sample", "parakeet-ctc": "sample"}
    for model, arm in main_arms.items():
        g = grid[(grid["model"] == model) & (grid["arm"] == arm) & (grid["kind"] == "main") &
                 (grid["precision"] == "")]
        if g.empty:
            continue
        dev = g[g["set"].isin(C.DEV_SETS)]
        if dev.empty:
            continue
        rv = dev[dev["param"] == "rover"]
        sl = dev[dev["param"] == "select"]
        w = dev.drop_duplicates(["set", "id"])["ref_len"].sum()
        rv_w = rv.groupby(["alpha", "eps", "gamma"])["e"].sum() / max(w, 1) * 100
        sl_w = sl.groupby("lam")["e"].sum() / max(w, 1) * 100
        (a, e, gm), lam = rv_w.idxmin(), sl_w.idxmin()
        chosen[model] = dict(alpha=a, eps=e, gamma=gm, lam=lam, dev_rover=float(rv_w.min()),
                             dev_select=float(sl_w.min()), n_dev=int(len(dev.drop_duplicates(["set", "id"]))))
        test = g[~g["set"].isin(C.DEV_SETS)]
        for s, gs in test.groupby("set"):
            r = gs[(gs["param"] == "rover") & (gs["alpha"] == a) & (gs["eps"] == e) &
                   (gs["gamma"] == gm)].set_index("id")
            q = gs[(gs["param"] == "select") & (gs["lam"] == lam)].set_index("id")
            ids = r.index.intersection(q.index)
            if len(ids) == 0:
                continue
            r, q = r.loc[ids], q.loc[ids]
            st = boot_delta(q["e"], r["e"], q["ref_len"], q["cluster"].to_numpy())
            rows.append(dict(model=model, set=s, k=int(gs["k"].iloc[0]), alpha=a, eps=e, gamma=gm, lam=lam,
                             wer_select_tuned=100 * q["e"].sum() / q["ref_len"].sum(),
                             wer_rover_tuned=100 * r["e"].sum() / q["ref_len"].sum(), **st))
    return pd.DataFrame(rows), chosen


def timing_table(root: Path, df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    plan = {j["id"]: j for j in json.load(open(root / "plan.json", encoding="utf-8"))}
    stats = []
    for p in (root / "state" / "done").glob("*.json"):
        s = json.load(open(p, encoding="utf-8"))
        j = plan.get(p.stem)
        if not j or "decode_s" not in s:
            continue
        stats.append((j, s))
    by: dict[tuple, dict] = {}
    for j, s in stats:
        for a in j["arms"]:
            key = (j["model"], j.get("precision") or "", j["kind"], a["name"])
            d = by.setdefault(key, dict(n=0, audio_s=0.0, encode_s=0.0, decode_s=0.0, wall_s=0.0, peak_mb=0.0,
                                        K=a.get("K", a.get("beams", 1)), T=a.get("T"), steps=a.get("steps")))
            d["n"] += s.get("n_ok", 0)
            d["audio_s"] += s.get("audio_s", 0.0)
            d["encode_s"] += s.get("encode_s", 0.0) / max(len(j["arms"]), 1)
            d["decode_s"] += s["decode_s"].get(a["name"], 0.0)
            d["peak_mb"] = max(d["peak_mb"], s.get("peak_mem_mb", 0.0) or 0.0)
    for (model, prec, kind, arm), d in by.items():
        if d["n"] == 0:
            continue
        rms = df[(df["model"] == model) & (df["arm"] == arm) & (df["kind"] == kind)]
        rms = rms[rms["k"] == rms["k"].max()]["rover_ms"].mean() if not rms.empty else None
        rows.append(dict(model=model, precision=prec, kind=kind, arm=arm, K=d["K"], T=d["T"], steps=d["steps"],
                         n=d["n"], audio_h=d["audio_s"] / 3600, s_per_utt=(d["encode_s"] + d["decode_s"]) / d["n"],
                         encode_s_per_utt=d["encode_s"] / d["n"], decode_s_per_utt=d["decode_s"] / d["n"],
                         rtf=(d["encode_s"] + d["decode_s"]) / max(d["audio_s"], 1e-9),
                         rtf_decode=d["decode_s"] / max(d["audio_s"], 1e-9),
                         ms_per_candidate=1000 * d["decode_s"] / d["n"] / max(d["K"] or 1, 1),
                         rover_ms_per_utt=rms, peak_mem_mb=d["peak_mb"]))
    return pd.DataFrame(rows)


def meta_table(contr: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if contr.empty:
        return pd.DataFrame()
    c = contr[(contr["k_is_main"]) & (contr["kind"] == "main") & (~contr["set"].isin(C.DEV_SETS))]
    for (model, prec, arm, norm, a, b), g in c.groupby(["model", "precision", "arm", "norm", "a", "b"]):
        re_ = random_effects(g["delta"].tolist(), g["se"].tolist())
        if re_:
            sig = int(((g["ci_low"] > 0)).sum())
            rows.append(dict(model=model, precision=prec, arm=arm, norm=norm, a=a, b=b, n_sig_positive=sig,
                             n_sig_negative=int((g["ci_high"] < 0).sum()), **re_))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------- report

def fmt(x, nd=2):
    return "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def write_report(out: Path, cells: pd.DataFrame, contr: pd.DataFrame, cross: pd.DataFrame,
                 tuned: pd.DataFrame, chosen: dict, meta: pd.DataFrame, timing: pd.DataFrame,
                 summary: dict) -> None:
    L = [f"# Campaign report\n", f"generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}\n",
         f"utterance decodes analysed: {summary.get('n_rows', 0)}; cells: {len(cells)}\n"]
    if not cells.empty:
        L.append("\n## Main arm at the largest K, corpus WER (legacy normalisation)\n")
        L.append("| model | set | n | K | first | conf | MBR | ROVER | ROVER-cg | oracle | oracle-comp | control | pairwise % |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        main = cells[(cells["kind"] == "main") & (cells["precision"] == "")]
        for (model, s, arm), g in main.groupby(["model", "set", "arm"]):
            r = g[g["k"] == g["k"].max()].iloc[0]
            L.append(f"| {model}/{arm} | {s} | {r['n']} | {r['k']} | {fmt(r.get('wer_first'))} | "
                     f"{fmt(r.get('wer_conf'))} | {fmt(r.get('wer_mbr'))} | {fmt(r.get('wer_rover_c'))} | "
                     f"{fmt(r.get('wer_rover_cg'))} | {fmt(r.get('wer_oracle_cand'))} | "
                     f"{fmt(r.get('wer_oracle_comp'))} | {fmt(r.get('wer_control'))} | {fmt(r.get('mean_pairwise'), 1)} |")
    if not contr.empty:
        L.append("\n## ROVER-cg against the best selection, paired bootstrap (main arm, largest K)\n")
        L.append("| model | set | vs | delta | 95% CI | cluster CI | Wilcoxon p | better/worse/tied |")
        L.append("|---|---|---|---|---|---|---|---|")
        c = contr[(contr["k_is_main"]) & (contr["norm"] == "legacy") & (contr["kind"] == "main") &
                  (contr["b"] == "rover_cg") & (contr["a"].isin(["conf", "mbr"]))]
        for _, r in c.iterrows():
            L.append(f"| {r['model']}/{r['arm']} | {r['set']} | {r['a']} | {r['delta']:+.2f} | "
                     f"[{r['ci_low']:+.2f}, {r['ci_high']:+.2f}] | "
                     f"[{fmt(r.get('cl_ci_low'))}, {fmt(r.get('cl_ci_high'))}] | "
                     f"{fmt(r.get('p_wilcoxon'), 4)} | {r['n_better']}/{r['n_worse']}/{r['n_tied']} |")
    if not meta.empty:
        L.append("\n## Pooled over test sets (random effects)\n")
        L.append("| model | arm | norm | a -> b | sets | pooled delta | 95% CI | I2 | sets sig + / - |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for _, r in meta.iterrows():
            L.append(f"| {r['model']} | {r['arm']} | {r['norm']} | {r['a']} -> {r['b']} | {r['k_sets']} | "
                     f"{r['pooled']:+.2f} | [{r['ci_low']:+.2f}, {r['ci_high']:+.2f}] | {r['I2']:.2f} | "
                     f"{r['n_sig_positive']} / {r['n_sig_negative']} |")
    if not cross.empty:
        L.append("\n## Against each model's standard decoding\n")
        L.append("| model | set | comparison | WER a | WER b | delta | 95% CI |")
        L.append("|---|---|---|---|---|---|---|")
        for _, r in cross.iterrows():
            L.append(f"| {r['model']} | {r['set']} | {r['label']} | {r['wer_a']:.2f} | {r['wer_b']:.2f} | "
                     f"{r['delta']:+.2f} | [{r['ci_low']:+.2f}, {r['ci_high']:+.2f}] |")
    if chosen:
        L.append("\n## Tuned on dev (ls-dev-clean + ls-dev-other), reported on test\n")
        for m, c in chosen.items():
            L.append(f"- **{m}**: alpha={c['alpha']}, eps={c['eps']}, gamma={c['gamma']}, lambda={c['lam']} "
                     f"(dev: select {c['dev_select']:.2f}, ROVER {c['dev_rover']:.2f}, n={c['n_dev']})")
        if not tuned.empty:
            L.append("\n| model | set | tuned select | tuned ROVER | delta | 95% CI |")
            L.append("|---|---|---|---|---|---|")
            for _, r in tuned.iterrows():
                L.append(f"| {r['model']} | {r['set']} | {r['wer_select_tuned']:.2f} | {r['wer_rover_tuned']:.2f} | "
                         f"{r['delta']:+.2f} | [{r['ci_low']:+.2f}, {r['ci_high']:+.2f}] |")
    if not timing.empty:
        L.append("\n## Cost\n")
        L.append("| model | kind | arm | K | T | steps | n | s/utt | encode s | decode s | RTF | ms/candidate | ROVER ms | peak MB |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for _, r in timing.sort_values(["model", "kind", "arm"]).iterrows():
            L.append(f"| {r['model']}{'@' + r['precision'] if r['precision'] else ''} | {r['kind']} | {r['arm']} | "
                     f"{r['K']} | {fmt(r['T'], 2)} | {r['steps'] or ''} | {r['n']} | {r['s_per_utt']:.3f} | "
                     f"{r['encode_s_per_utt']:.3f} | {r['decode_s_per_utt']:.3f} | {r['rtf']:.4f} | "
                     f"{r['ms_per_candidate']:.1f} | {fmt(r['rover_ms_per_utt'])} | {r['peak_mem_mb']:.0f} |")
    (out / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--no_csv", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)
    out = root / "results"
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.load(open(root / "run_config.json", encoding="utf-8"))
    t0 = time.time()

    df, grid = load_tables(root)
    summary: dict = {"generated_unix": time.time(), "n_rows": int(len(df)), "config": cfg}
    if df.empty:
        print("[aggregate] nothing to aggregate", flush=True)
        (out / "campaign_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return 0
    df.to_parquet(out / "per_utt_k.parquet", index=False)
    if not grid.empty:
        grid.to_parquet(out / "grid.parquet", index=False)
    if not args.no_csv:
        df.to_csv(out / "per_utt_k.csv.gz", index=False, compression="gzip")

    cells = cells_table(df)
    cells.to_csv(out / "cells.csv", index=False)
    print(f"[aggregate] cells {len(cells)} ({time.time() - t0:.0f} s)", flush=True)
    contr = contrasts_table(df)
    contr.to_csv(out / "contrasts.csv", index=False)
    print(f"[aggregate] contrasts {len(contr)} ({time.time() - t0:.0f} s)", flush=True)
    cross = cross_arm_table(df, cfg)
    cross.to_csv(out / "cross_arm.csv", index=False)
    tuned, chosen = tuned_table(df, grid)
    tuned.to_csv(out / "tuned.csv", index=False)
    meta = meta_table(contr)
    meta.to_csv(out / "meta_analysis.csv", index=False)
    timing = timing_table(root, df)
    timing.to_csv(out / "timing.csv", index=False)

    datasets = {}
    for p in sorted((root / "manifests").glob("*.meta.json")):
        datasets[p.name.split(".meta")[0]] = json.load(open(p, encoding="utf-8"))
    summary.update(
        datasets=datasets,
        models={m: C.MODELS[m] for m in df["model"].unique() if m in C.MODELS},
        tuned_on_dev=chosen,
        cells=cells.replace({np.nan: None}).to_dict(orient="records"),
        contrasts_main=contr[contr["k_is_main"]].replace({np.nan: None}).to_dict(orient="records") if not contr.empty else [],
        cross_arm=cross.replace({np.nan: None}).to_dict(orient="records"),
        tuned=tuned.replace({np.nan: None}).to_dict(orient="records"),
        meta_analysis=meta.replace({np.nan: None}).to_dict(orient="records"),
        timing=timing.replace({np.nan: None}).to_dict(orient="records"),
    )
    with open(out / "campaign_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    write_report(out, cells, contr, cross, tuned, chosen, meta, timing, summary)
    print(f"[aggregate] done in {time.time() - t0:.0f} s -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
