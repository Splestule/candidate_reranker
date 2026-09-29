#!/usr/bin/env python3
"""Every number the paper is allowed to contain, printed from the data, in one run.

The rule this enforces: if a figure is not in this output, it does not go in the paper. Two
results in this project were written up before they were measured properly and had to be
retracted -- a confusion-network construction worth "+1.11" that was one badly-tuned
baseline parameter, and a confidence calibration worth "+0.17" that was the alpha/eps
re-tuning that came with it. Both survived as long as they did because the number lived in
a document and the code that produced it lived somewhere else.

So each block below prints the number, its interval, and the file it came from, and says
loudly when a source is missing instead of quietly leaving a row out. Retracted results are
printed too, with what they actually are, because a paper that drops them silently is
making the same mistake again.

    PYTHONPATH=src python3 tools/paper_numbers.py
    PYTHONPATH=src python3 tools/paper_numbers.py --only gap,slot
"""

from __future__ import annotations

import argparse
import pickle
import statistics
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

CAMPAIGN = "results/campaign-2026-09-20/results/per_utt_k.parquet"
TREES = "results/campaign/results/per_utt_k.parquet"
CALIB = "results/calib_cache.pkl"
AUDIT = "results/audit_calib_rounds.pkl"
SLOT = "results/slot_lr.pkl"
SLOT_NB = "results/slot_lr_nb_curve.pkl"
SLOT_OC = "results/slot_lr_oracle_ctx.pkl"
MANGU = "results/eval_mangu_k32_n200__res_0.45x1c.pkl"
CONTROLS = "results/controls.json"
SWITCH = "results/switch_oracle.json"

HEAD_MODEL, HEAD_ARM, HEAD_K = "whisfusion", "main", 32
MISSING: list[str] = []


def need(path: str):
    p = Path(path)
    if not p.exists():
        MISSING.append(path)
        print(f"  !! missing: {path}")
        return None
    return p


def rule(title: str, src: str):
    print(f"\n{'=' * 78}\n{title}\n  source: {src}\n{'-' * 78}")


# ------------------------------------------------------------------------------- the gap

def load_campaign():
    import pandas as pd
    p = need(CAMPAIGN)
    if p is None:
        return None
    df = pd.read_parquet(p)
    return df[(df["precision"] == "") & (df["kind"] == "main")
              & df["e_oracle_comp"].notna()]


def block_gap(df):
    """ROVER against the two oracles and the shuffled control, on the legacy normalisation.

    e_oracle_comp and e_control exist only in legacy space, so every number here is legacy
    and must not be mixed with the wn_* columns.
    """
    import bootstrap
    rule("1. THE GAP -- what word-level composition leaves on the table",
         f"{CAMPAIGN}, model={HEAD_MODEL} arm={HEAD_ARM} k={HEAD_K}, legacy normalisation")
    g = df[(df["model"] == HEAD_MODEL) & (df["arm"] == HEAD_ARM) & (df["k"] == HEAD_K)]
    R = g["ref_len"].sum()
    w = lambda c: 100.0 * g[c].sum() / R
    rover, comp, cand, ctl = (w("e_rover_cg"), w("e_oracle_comp"),
                              w("e_oracle_cand"), w("e_control"))
    first = w("e_first")
    print(f"{len(g)} utterances over {g['set'].nunique()} sets, {int(R)} reference words")
    print(f"sets: {', '.join(sorted(g['set'].unique()))}\n")
    for name, v in (("single candidate (e_first)", first), ("ROVER, as shipped", rover),
                    ("best candidate oracle", cand), ("composition oracle", comp),
                    ("shuffled control", ctl)):
        print(f"  {name:<32}{v:>7.2f}")
    st = bootstrap.paired_bootstrap(g["e_rover_cg"].tolist(), g["e_oracle_comp"].tolist(),
                                    g["ref_len"].tolist())
    print(f"\n  gap ROVER -> composition oracle   {rover - comp:>7.2f} WER, "
          f"{100 * (rover - comp) / rover:.0f}% of ROVER's error")
    print("  " + bootstrap.format_row("ROVER vs composition oracle", st))
    print(f"\n  the real ceiling is {cand / comp:.2f}x lower than the candidate oracle "
          f"({cand:.2f} vs {comp:.2f})")
    print(f"  composition beats the best whole candidate on "
          f"{100.0 * (g['e_oracle_comp'] < g['e_oracle_cand']).mean():.0f}% of utterances")
    sl = (rover - comp) / max(rover - ctl, 1e-9)
    print(f"  signal to luck: real gap / shuffled-control gap = {sl:.1f}x")

    # the same quantity on the branching campaign, which covers only three hard sets.
    # An earlier write-up quoted 24.88 -> 13.95 as the headline; that was this narrower
    # slice, not the 16-set measurement above, and it must not be reported as the headline.
    t = need(TREES)
    if t is not None:
        import pandas as pd
        d2 = pd.read_parquet(t)
        d2 = d2[(d2["precision"] == "") & (d2["arm"] == "flat") & (d2["k"] == HEAD_K)
                & d2["e_oracle_comp"].notna()]
        if len(d2):
            R2 = d2["ref_len"].sum()
            r2 = 100.0 * d2["e_rover_cg"].sum() / R2
            c2 = 100.0 * d2["e_oracle_comp"].sum() / R2
            print(f"\n  cross-check, branching campaign, flat arm, "
                  f"{d2['set'].nunique()} hard sets only ({', '.join(sorted(d2['set'].unique()))}):")
            print(f"    ROVER {r2:.2f} -> composition oracle {c2:.2f}, gap {r2 - c2:.2f}")
            print("    harder sets, bigger gap. The headline is the 16-set figure above.")
    return dict(rover=rover, comp=comp, cand=cand, control=ctl, gap=rover - comp)


def block_models(df):
    rule("2. THE GAP ACROSS MODELS -- is this a diffusion phenomenon or a general one",
         f"{CAMPAIGN}, each arm at its own largest k, legacy normalisation")
    print(f"{'model / arm':<26}{'k':>4}{'sets':>6}{'ROVER':>8}{'comp.or':>9}{'cand.or':>9}"
          f"{'control':>9}{'gap':>7}{'% err':>7}{'s/luck':>8}")
    for (m, arm), g0 in df.groupby(["model", "arm"]):
        if len(g0) < 400:
            continue
        g = g0[g0["k"] == g0["k"].max()]
        if len(g) < 200:
            continue
        R = g["ref_len"].sum()
        w = lambda c: 100.0 * g[c].sum() / R
        rov, comp, cand, ctl = (w("e_rover_cg"), w("e_oracle_comp"),
                                w("e_oracle_cand"), w("e_control"))
        print(f"{m + ' / ' + arm:<26}{int(g['k'].max()):>4}{g['set'].nunique():>6}"
              f"{rov:>8.2f}{comp:>9.2f}{cand:>9.2f}{ctl:>9.2f}"
              f"{rov - comp:>7.2f}{100 * (rov - comp) / rov:>6.0f}%"
              f"{(rov - comp) / max(rov - ctl, 1e-9):>8.1f}")
    print("\n  k and the set list differ by model, so compare the gap share and the")
    print("  signal-to-luck column, not the absolute WERs.")


def block_controls():
    """How much of each model's oracle gap is information and how much is K free guesses.

    Two controls, both keeping the network shape, the epsilon arcs and the vote counts:
    LEXICAL replaces the alternatives with corpus words, PERMUTED moves the alternative sets
    between slots of the same utterance, so every word on every arc is still one the decoder
    really proposed for this utterance. Permuted is the stricter control and the one to
    report. Both are clamped to the best whole candidate, the fallback any system has -- see
    tools/control_check.py for why that clamp has to be stated.
    """
    rule("2b. THE CONTROLS -- how much of the oracle gap is not luck", CONTROLS)
    p = need(CONTROLS)
    if p is None:
        return
    import json
    rows = json.loads(p.read_text())
    print(f"{'model / arm':<26}{'k':>4}{'n':>6}{'ROVER':>8}{'oracle':>8}{'lex*':>8}"
          f"{'perm*':>8}{'gap':>7}{'lex s/l':>9}{'perm s/l':>10}")
    for r in sorted(rows, key=lambda r: -(r["rover"] - r["perm_clamped"]) and 0
                    or -(r["rover"] - r["oracle"]) / max(r["rover"] - r["perm_clamped"], 1e-9)):
        gap = r["rover"] - r["oracle"]
        print(f"{r['model'] + ' / ' + r['arm']:<26}{r['k']:>4}{r['n']:>6}{r['rover']:>8.2f}"
              f"{r['oracle']:>8.2f}{r['lex_clamped']:>8.2f}{r['perm_clamped']:>8.2f}"
              f"{gap:>7.2f}"
              f"{gap / max(r['rover'] - r['lex_clamped'], 1e-9):>9.1f}"
              f"{gap / max(r['rover'] - r['perm_clamped'], 1e-9):>10.1f}")
    print("\n  1.0 means the whole gap is the oracle's freedom to guess: the network carries")
    print("  no information a shuffled one does not. Autoregressive beam search sits there.")
    print("  Masked diffusion does not, and that is the finding.")


def block_switch():
    """Is the gap a few segment choices or hundreds of word decisions?

    An oracle allowed at most S candidate switches stitches the transcript from S+1
    contiguous segments. S=0 is the n-best oracle, S unlimited is the composition oracle,
    and where the curve saturates says what shape of model could reach it.
    """
    rule("3b. THE SHAPE OF THE GAP -- how many decisions is it really", SWITCH)
    p = need(SWITCH)
    if p is None:
        return
    import json
    rows = json.loads(p.read_text())
    keys = sorted({int(k) for r in rows for k in r["budgets"]})
    print(f"{'model / arm':<24}{'ROVER':>7}{'comp':>7}" +
          "".join(f"{('S=' + str(k)):>8}" for k in keys))
    print(f"{'':<24}{'':>7}{'':>7}" + "".join(f"{'':>8}" for k in keys)
          + "   share of the gap closed")
    for r in rows:
        gap = r["rover"] - r["comp"]
        line = f"{r['model'] + ' / ' + r['arm']:<24}{r['rover']:>7.2f}{r['comp']:>7.2f}"
        for k in keys:
            v = r["budgets"].get(str(k))
            line += f"{'':>8}" if v is None else f"{100 * (r['rover'] - v) / max(gap, 1e-9):>7.0f}%"
        print(line)
    print("\n  Masked diffusion: one switch recovers over half the gap, four recover most of")
    print("  it. The gap is a handful of contiguous segment choices, not a word-by-word")
    print("  problem -- which is why per-slot models ceiling out at a few percent.")
    print("  Beam search is the opposite: switches buy it almost nothing, so the rest of its")
    print("  gap really is the oracle picking lucky individual words. Same reading as 2b.")
    print("\n  The one-switch search space is (slots+1) x K^2, about 30k options at K=32, and")
    print("  prefix sums enumerate all of them in microseconds. The search is not the")
    print("  problem: see tools/stitch_score.py for what is.")


# ------------------------------------------------------------ where the gap actually lives

def block_ar():
    """A = the reference word is an option in its slot. R = given that, the vote picks it.

    Counted over slots whose reference is a real word. Slots whose reference is epsilon --
    the network offered a word where the reference has none -- are a different question and
    are reported separately; folding them in inflates A, because epsilon is always on offer.
    """
    rule("3. A / R -- availability against recoverability", CALIB)
    if need(CALIB) is None:
        return
    import crf_rover as F
    data = pickle.loads(Path(CALIB).read_bytes())
    n = avail = picked = 0
    eps_n = eps_ok = 0
    for d in data:
        total = float(d["n_cand"])
        for sl, r in zip(d["slots"], d["ref_by_slot"]):
            pick = F.rover_pick(sl, total, 0.5, 0.7, None)
            if r == "":
                eps_n += 1
                eps_ok += pick == ""
                continue
            n += 1
            here = r in sl
            avail += here
            picked += here and pick == r
    A, R_ = avail / n, picked / max(avail, 1)
    print(f"{n} slots with a real reference word, over {len(data)} utterances\n")
    print(f"  A  reference word is an option        {100 * A:>6.1f}%")
    print(f"  R  and the vote picks it              {100 * R_:>6.1f}%")
    print(f"  A*R = ROVER's slot accuracy           {100 * A * R_:>6.1f}%")
    print(f"\n  not available  {100 * (1 - A):>5.1f}%   -- no candidate proposed it; only a "
          f"different decoder helps")
    print(f"  not picked     {100 * A * (1 - R_):>5.1f}%   -- it was there and lost the vote; "
          f"this is what a better rule could win")
    print(f"\n  {eps_n} slots where the reference is epsilon (the network invented a "
          f"position): dropped correctly {100 * eps_ok / max(eps_n, 1):.1f}%")


def block_slot_ceiling():
    """What a perfect per-slot decision would be worth, against what a learned one is worth."""
    rule("4. THE SLOT CEILING -- everything a per-slot model could ever win",
         f"{CALIB}, {SLOT}, {SLOT_NB}")
    if need(CALIB) is None:
        return
    import crf_rover as F
    import slot_lr as L
    data = pickle.loads(Path(CALIB).read_bytes())
    ev = [d for d in data if d["set"] in L.EVAL_SETS]
    R = sum(len(d["ref"]) for d in ev)
    tot = avail = n = 0
    for d in ev:
        total = float(d["n_cand"])
        h = []
        for sl, r in zip(d["slots"], d["ref_by_slot"]):
            n += 1
            if r in sl or r == "":
                avail += 1
                h.append(r)
            else:
                h.append(F.rover_pick(sl, total, 0.6, 0.4, 11.95))
        tot += F.edits_of(h, d["ref"])
    oracle = 100.0 * tot / R
    ship = 100.0 * L.rover_edits(ev, 0.5, 0.7, None) / R
    tuned = 100.0 * L.rover_edits(ev, 0.6, 0.4, 11.95) / R
    print(f"{len(ev)} utterances on {len(L.EVAL_SETS)} held-out sets, {n} slots, "
          f"reference available in {100 * avail / n:.1f}%\n")
    print(f"  {'ROVER as shipped':<40}{ship:>7.2f}")
    print(f"  {'ROVER with alpha/eps tuned on train':<40}{tuned:>7.2f}")
    best = {}
    for tag, path in (("learned per-slot pick", SLOT),
                      ("+ neighbour bigram", SLOT_NB),
                      ("+ ORACLE neighbour words", SLOT_OC)):
        p = need(path)
        if p is None:
            continue
        rows = pickle.loads(p.read_bytes())
        by = {}
        for r in rows:
            by.setdefault(r["n"], []).append(r["lr_wer"] - r["rover_wer"])
        n_best = min(by, key=lambda k: statistics.mean(by[k]))
        best[tag] = (n_best, statistics.mean(by[n_best]),
                     100.0 * statistics.mean([r["lr_wer"] for r in rows if r["n"] == n_best]) / 100)
        print(f"  {tag:<40}{best[tag][2]:>7.2f}   ({best[tag][1]:+.2f} vs tuned ROVER, "
              f"best at {n_best} training utterances)")
    print(f"  {'per-slot oracle (right word when present)':<40}{oracle:>7.2f}")
    head = tuned - oracle
    print(f"\n  headroom inside the slots          {head:>6.2f} WER")
    for tag, (_, d, _) in best.items():
        print(f"  {tag:<34}{-d:>6.2f} WER = {100 * -d / head:.0f}% of it")
    print("\n  The oracle row hands the model the reference's own neighbouring words. It is")
    print("  worth 0.2 more than guessing them from the votes, so local context is not")
    print("  under-estimated -- a bigram over one neighbour is simply not enough signal.")
    print("\n  a flat learning curve says this is a ceiling, not a data problem.")
    for tag, path in (("no context", SLOT), ("with neighbour bigram", SLOT_NB),
                      ("with oracle neighbours", SLOT_OC)):
        p = Path(path)
        if not p.exists():
            continue
        rows = pickle.loads(p.read_bytes())
        by = {}
        for r in rows:
            by.setdefault(r["n"], []).append(r["lr_wer"] - r["rover_wer"])
        print(f"    {tag:<24}" + "  ".join(f"{k}:{statistics.mean(v):+.2f}"
                                           for k, v in sorted(by.items())))


# --------------------------------------------------------------------- what did not work

def block_calib():
    rule("5. CONFIDENCE CALIBRATION -- RETRACTED, it is the alpha/eps tuning", AUDIT)
    p = need(AUDIT)
    if p is None:
        return
    rounds = pickle.loads(p.read_bytes())
    base = [r["as-is"][0] for r in rounds]
    print(f"{len(rounds)} rounds, each refitting the calibration and re-tuning alpha/eps "
          f"on a dev resample\n")
    print(f"  {'arm':<14}{'test WER':>10}{'vs as-is':>10}{'2.5%':>9}{'97.5%':>9}")
    for n in ("as-is", "isotonic", "power", "freq only"):
        w = [r[n][0] for r in rounds]
        d = sorted(x - b for x, b in zip(w, base))
        lo, hi = d[int(.025 * len(d))], d[int(.975 * len(d)) - 1]
        flag = "   spans zero" if lo <= 0 <= hi else ""
        print(f"  {n:<14}{statistics.median(w):>10.2f}{statistics.median(d):>+10.2f}"
              f"{lo:>+9.2f}{hi:>+9.2f}{flag}")
    print("\n  as-is = today's confidences with alpha/eps tuned on the same resample.")
    print("  Monotone recalibration is absorbed by alpha and eps, because ROVER's decision")
    print("  is a comparison inside one slot. 'freq only' shows the signal is worth ~1.0.")


def block_mangu():
    rule("6. MANGU-STYLE CONSTRUCTION -- RETRACTED, the effect spans zero", MANGU)
    p = need(MANGU)
    if p is None:
        return
    res = pickle.loads(p.read_bytes())
    dev = [r for r in res if r["set"] in ("ls-dev-clean", "ls-dev-other")]
    test = [r for r in res if r["set"] not in ("ls-dev-clean", "ls-dev-other")]
    params = sorted({(a, e) for (_, a, e) in res[0]["edits"]})
    arms = sorted({n for (n, _, _) in res[0]["edits"]})
    Rd = sum(r["n_ref"] for r in dev)
    Rt = sum(r["n_ref"] for r in test)
    print(f"{len(dev)} dev / {len(test)} test utterances, {len(params)} parameter settings\n")
    print(f"  {'arm':<16}{'dev best':>10}{'dev worst':>11}{'spread':>9}{'test at dev best':>19}")
    for a in arms:
        vals = {p_: 100.0 * sum(r["edits"][(a,) + p_] for r in dev) / Rd for p_ in params}
        bp = min(vals, key=vals.get)
        tw = 100.0 * sum(r["edits"][(a,) + bp] for r in test) / Rt
        print(f"  {a:<16}{min(vals.values()):>10.2f}{max(vals.values()):>11.2f}"
              f"{max(vals.values()) - min(vals.values()):>9.2f}{tw:>19.2f}")
    print("\n  A parameter spread of 14 to 22 WER points on arms whose difference is 0.03")
    print("  means the tuner, not the construction, decides who wins. Run")
    print("  tools/tuned_compare.py for the interval that includes the tuning noise.")


def block_cost(df):
    rule("7. COST -- what the combination actually costs next to the decode",
         f"{CAMPAIGN}, k={HEAD_K}")
    g = df[(df["model"] == HEAD_MODEL) & (df["arm"] == HEAD_ARM) & (df["k"] == HEAD_K)]
    print(f"  {'decode (encode + PDD)':<32}{1000 * (g['encode_s'] + g['decode_s']).mean():>8.1f} ms")
    print(f"  {'ROVER over the network':<32}{g['rover_ms'].mean():>8.2f} ms")
    print(f"  {'ratio':<32}{1000 * (g['encode_s'] + g['decode_s']).mean() / max(g['rover_ms'].mean(), 1e-9):>8.0f}x")


BLOCKS = ("gap", "models", "controls", "switch", "ar", "slot", "calib", "mangu", "cost")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated subset of " + ",".join(BLOCKS))
    a = ap.parse_args()
    want = {x.strip() for x in a.only.split(",") if x.strip()} or set(BLOCKS)
    bad = want - set(BLOCKS)
    if bad:
        print(f"unknown block(s): {sorted(bad)}")
        return 2

    df = load_campaign() if want & {"gap", "models", "cost"} else None
    print("PAPER NUMBERS -- nothing goes in the paper that is not printed here")
    if df is not None:
        block_gap(df) if "gap" in want else None
        block_models(df) if "models" in want else None
    if "controls" in want:
        block_controls()
    if "switch" in want:
        block_switch()
    if "ar" in want:
        block_ar()
    if "slot" in want:
        block_slot_ceiling()
    if "calib" in want:
        block_calib()
    if "mangu" in want:
        block_mangu()
    if df is not None and "cost" in want:
        block_cost(df)

    print(f"\n{'=' * 78}")
    if MISSING:
        print(f"{len(MISSING)} source(s) missing -- those numbers are NOT current:")
        for m in MISSING:
            print(f"  {m}")
        return 1
    print("every source present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
