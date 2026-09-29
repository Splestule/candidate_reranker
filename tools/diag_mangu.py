#!/usr/bin/env python3
"""Why does the backbone-free network lose on AMI when it wins on thirteen other sets?

The headline is +1.11 WER over 1507 held-out utterances, won on 13 of 14 sets, and lost on
AMI three times running (+0.13 at K=12, +3.79 and +1.46 at K=32). Three measurements in the
same direction is a property, not noise, and it belongs in the paper as a limitation --
but only once it is known whether "AMI" is the cause or merely the symptom.

Two things could be true and they need different sentences in the paper:

  the construction is worse on SHORT, DISAGREEING utterances, and AMI is simply made of
  those -- then the limitation is about utterance shape and applies everywhere;
  AMI loses even against matched utterances from other corpora -- then it is meeting speech
  itself (overlap, disfluency) and the limitation is about the domain.

So: bucket every scored utterance by properties that have nothing to do with which corpus it
came from, report the delta inside each bucket, and then ask whether AMI still loses once it
is compared only with utterances that look like it.

Reads what eval_mangu.py already wrote; nothing is rebuilt.

    PYTHONPATH=src python tools/diag_mangu.py \\
        --rows results/eval_mangu_k32_n200.pkl \\
        --res  results/eval_mangu_k32_n200__res_0.45-0.55-1.01.pkl
"""

from __future__ import annotations

import argparse
import pickle
import statistics
import sys
from collections import defaultdict
from pathlib import Path

DEV_SETS = ("ls-dev-clean", "ls-dev-other")


def quartile_edges(vals: list[float], n: int = 4) -> list[float]:
    s = sorted(vals)
    return [s[int(len(s) * i / n)] for i in range(1, n)]


def bucket_of(v: float, edges: list[float]) -> int:
    for i, e in enumerate(edges):
        if v < e:
            return i
    return len(edges)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--res", required=True)
    ap.add_argument("--focus", default="ami")
    a = ap.parse_args()

    sys.path.insert(0, "src")
    import bootstrap
    from rapidfuzz.distance import Levenshtein

    rows = {(r["set"], r["id"]): r for r in pickle.loads(Path(a.rows).read_bytes())}
    res = pickle.loads(Path(a.res).read_bytes())
    res = [r for r in res if (r["set"], r["id"]) in rows]
    names = sorted({n for r in res for (n, _, _) in r["edits"]})
    mangu_names = [n for n in names if n != "backbone"]

    # same tuning rule as eval_mangu: pick (alpha, eps) per network on dev only
    dev = [r for r in res if r["set"] in DEV_SETS]
    test = [r for r in res if r["set"] not in DEV_SETS]
    if not dev or not test:
        print("need dev and test utterances in the results file")
        return 2

    def dev_wer(name, al, e):
        num = sum(r["edits"][(name, al, e)] for r in dev)
        den = sum(r["n_ref"] for r in dev)
        return 100.0 * num / den

    keys = sorted({(al, e) for (_, al, e) in res[0]["edits"]})
    best = {n: min(keys, key=lambda k: dev_wer(n, *k)) for n in names}
    mg = min(mangu_names, key=lambda n: dev_wer(n, *best[n]))
    bb_k, mg_k = best["backbone"], best[mg]
    print(f"tuned on dev: backbone alpha/eps {bb_k}, mangu {mg} alpha/eps {mg_k}")
    print(f"{len(test)} held-out utterances, {len(set(r['set'] for r in test))} sets\n")

    # ---- per-utterance properties that say nothing about which corpus it is
    feat = {}
    for r in test:
        row = rows[(r["set"], r["id"])]
        cs = row["cands"]
        lens = [len(c) for c in cs]
        pw = []
        for i in range(min(len(cs), 8)):
            for j in range(i + 1, min(len(cs), 8)):
                pw.append(Levenshtein.distance(cs[i], cs[j]) / max(lens[i], lens[j], 1))
        feat[(r["set"], r["id"])] = dict(
            ref_len=float(r["n_ref"]),
            pairwise=100.0 * statistics.fmean(pw) if pw else 0.0,
            n_unique=float(len({" ".join(c) for c in cs})),
            slot_ratio=r["shape"][mg][0] / max(r["shape"]["backbone"][0], 1),
        )

    def delta(rs):
        b = [r["edits"][("backbone",) + bb_k] for r in rs]
        m = [r["edits"][(mg,) + mg_k] for r in rs]
        R = sum(r["n_ref"] for r in rs)
        return (100.0 * (sum(b) - sum(m)) / R) if R else float("nan"), b, m

    print("delta = backbone - mangu in WER points; positive means mangu is better\n")
    labels = dict(ref_len="reference words", pairwise="pairwise disagreement %",
                  n_unique="distinct candidates", slot_ratio="mangu slots / backbone slots")
    for f in ("ref_len", "pairwise", "n_unique", "slot_ratio"):
        vals = [feat[(r["set"], r["id"])][f] for r in test]
        edges = quartile_edges(vals)
        print(f"{labels[f]:<32}{'range':>16}{'n':>7}{'backbone':>10}{'mangu':>8}{'delta':>8}")
        for b in range(4):
            rs = [r for r in test if bucket_of(feat[(r['set'], r['id'])][f], edges) == b]
            if not rs:
                continue
            lo = "-inf" if b == 0 else f"{edges[b-1]:.2f}"
            hi = "inf" if b == 3 else f"{edges[b]:.2f}"
            d, bb, mm = delta(rs)
            R = sum(r["n_ref"] for r in rs)
            print(f"{'':<32}{f'{lo}..{hi}':>16}{len(rs):>7}"
                  f"{100 * sum(bb) / R:>10.2f}{100 * sum(mm) / R:>8.2f}{d:>+8.2f}")
        print()

    # ---- is the focus set losing beyond what its shape explains?
    foc = [r for r in test if r["set"] == a.focus]
    oth = [r for r in test if r["set"] != a.focus]
    if not foc:
        print(f"no {a.focus} utterances in this results file")
        return 0
    print(f"{a.focus} against everything else\n")
    print(f"{'':<26}{'n':>7}{'ref len':>9}{'pairwise':>10}{'uniq':>7}{'slot ratio':>12}{'delta':>8}")
    for nm, rs in ((a.focus, foc), ("other sets", oth)):
        fs = [feat[(r["set"], r["id"])] for r in rs]
        d, _, _ = delta(rs)
        print(f"{nm:<26}{len(rs):>7}{statistics.fmean(f['ref_len'] for f in fs):>9.1f}"
              f"{statistics.fmean(f['pairwise'] for f in fs):>10.1f}"
              f"{statistics.fmean(f['n_unique'] for f in fs):>7.1f}"
              f"{statistics.fmean(f['slot_ratio'] for f in fs):>12.2f}{d:>+8.2f}")

    # matched comparison: only other-set utterances that look like the focus set
    fs = [feat[(r["set"], r["id"])] for r in foc]
    lo_len = min(f["ref_len"] for f in fs), max(f["ref_len"] for f in fs)
    med_pw = statistics.median(f["pairwise"] for f in fs)
    matched = [r for r in oth
               if lo_len[0] <= feat[(r["set"], r["id"])]["ref_len"] <= lo_len[1]
               and abs(feat[(r["set"], r["id"])]["pairwise"] - med_pw) <= 10.0]
    if len(matched) >= 50:
        d_f, bf, mf = delta(foc)
        d_m, bm, mm = delta(matched)
        print(f"\nmatched on length and disagreement ({len(matched)} utterances from other sets):")
        print(f"  {a.focus:<22}{d_f:>+8.2f}")
        print(f"  {'matched others':<22}{d_m:>+8.2f}")
        st = bootstrap.paired_bootstrap(bf, mf, [r["n_ref"] for r in foc], n_boot=4000)
        flag = "" if st["ci_low"] > 0 or st["ci_high"] < 0 else "   spans zero"
        print("\n  " + bootstrap.format_row(f"mangu vs backbone on {a.focus}", st) + flag)
        print(f"\n  if {a.focus} still loses while matched others win, the limitation is the")
        print("  domain; if both look alike, it is utterance shape and AMI is only a symptom.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
