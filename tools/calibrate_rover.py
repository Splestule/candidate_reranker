#!/usr/bin/env python3
"""Does recalibrating the word confidences make ROVER's vote better?

ROVER scores a slot as alpha * vote_share + (1 - alpha) * mean_confidence. The vote share is
a proper fraction; the confidence is whatever the decoder reports. tools/calib.py showed that
what Whisfusion reports is monotone but badly scaled and saturated near 1.0 -- a third of all
words sit above 0.995, where they are right 89% of the time. No value of alpha fixes a signal
that is wrong rather than merely weighted wrongly, which is the standing explanation for why
the 45-point (alpha, eps, gamma) grid is flat at the optimum.

So: learn a monotone map from reported confidence to empirical correctness on dev, apply it on
test, and re-vote. Three things this has to get right or it measures nothing.

  eps_conf moves with it. Epsilon carries a fixed pseudo-confidence. Recalibration pushes real
  words down toward their true accuracy, so an unchanged eps_conf suddenly outvotes them and
  deletions explode. alpha and eps are therefore re-tuned on dev AFTER each calibration, and
  the as-is arm gets the same courtesy so the comparison is not rigged.

  freq-only is the control that matters. alpha = 1.0 ignores confidence altogether. If a
  recalibrated confidence cannot beat throwing the confidence away, the signal is worthless
  and the whole direction is closed -- which is a result, just not the hoped-for one.

  fit and score never share data. The map and (alpha, eps) come from the dev sets; every number
  reported for a test set comes from a set the fit never saw.

Pass 1 extracts each utterance's slots into a compact cache (per slot: every word with the
candidate indices and raw confidences that voted for it, plus the reference word for that
slot). Everything after that is arithmetic on the cache, so the sweeps cost nothing and the
dumps are read once.

    PYTHONPATH=src python tools/calibrate_rover.py results/campaign-2026-09-20 \
        --model whisfusion --max_utts 400
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np

DEV_SETS = ("ls-dev-clean", "ls-dev-other")
GRID_ALPHA = [0.3, 0.4, 0.5, 0.6, 0.7, 0.85, 1.0]
GRID_EPS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
SHIPPED = dict(alpha=0.5, eps=0.7)          # campaign.analysis.ROVER_DEFAULT
GAMMA = 0.5                                  # rover_cg clusters near-duplicates, as shipped


# ------------------------------------------------------------------ pass 1: dumps -> cache

def extract(root: Path, model: str, arm: str, k: int, max_utts: int,
            have: list[dict] | None = None, only: set[str] | None = None) -> list[dict]:
    """Append up to max_utts per set to what is already cached, so a big pull can be resumed.

    Extraction is the slow part and a shell may time out in the middle of it. Everything here
    is additive: rerun with the same arguments and it tops each set up to max_utts, skipping
    the sets that are already full.
    """
    if not (root / "dumps").is_dir():
        raise SystemExit(f"no dumps directory under {root} -- pass the campaign root, "
                         f"e.g. results/campaign-2026-09-20")
    out = list(have or [])
    seen = {(d["set"], d["id"]) for d in out}
    sys.path.insert(0, "src")
    import compose
    import decompose as D
    from scorers import normalize

    for job in sorted(glob.glob(f"{root}/dumps/{model}__*")):
        parts = Path(job).name.split("__")
        if len(parts) < 4 or parts[3] != arm:
            continue
        set_name = parts[1]
        if only and set_name not in only:
            continue
        p = Path(job) / f"{arm}.jsonl.gz"
        if not p.exists():
            continue
        n_here = sum(1 for r in out if r["set"] == set_name)
        if n_here >= max_utts:
            continue
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if (set_name, row["id"]) in seen:
                    continue
                raw = row["candidates"][:k]
                cands = [normalize(c["text"]).split() for c in raw]
                keep = [i for i, (w, c) in enumerate(zip(cands, raw))
                        if w and "word_conf" in c and len(c["word_conf"]) == len(w)]
                if len(keep) < 2:
                    continue
                cands = [cands[i] for i in keep]
                confs = [list(raw[i]["word_conf"]) for i in keep]
                ref = normalize(row["reference"]).split()
                if not ref:
                    continue
                bb = compose.central_index(cands)
                by_slot = D.reference_by_slot(cands, bb, ref)
                # rebuild the network keeping the individual votes rather than their sums
                slots = compose.confusion_network(cands, bb, confs, None)
                if len(by_slot) != len(slots):
                    continue
                per_slot = []
                for sl in slots:
                    per_slot.append({w: list(v) for w, v in sl.items()})
                seen.add((set_name, row["id"]))
                out.append(dict(set=set_name, id=row["id"],
                                cluster=row.get("cluster") or row["id"],
                                n_cand=len(cands), ref=ref, ref_by_slot=by_slot,
                                slots=per_slot, dup=dup_sizes(cands)))
                n_here += 1
                if n_here >= max_utts:
                    break
    return out


def dup_sizes(cands: list[list[str]]) -> list[int]:
    """Cluster size of each candidate, for the gamma reweighting rover_cg uses."""
    seen: dict[tuple, int] = {}
    for c in cands:
        t = tuple(c)
        seen[t] = seen.get(t, 0) + 1
    return [seen[tuple(c)] for c in cands]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max_utts", type=int, default=400)
    ap.add_argument("--cache", default="/tmp/calib_cache.pkl")
    ap.add_argument("--refresh", action="store_true", help="throw the cache away and start over")
    ap.add_argument("--extract", action="store_true",
                    help="top the cache up to --max_utts per set, then report")
    ap.add_argument("--sets", default="", help="limit extraction to these sets (comma separated)")
    args = ap.parse_args()

    cache = Path(args.cache)
    have = pickle.loads(cache.read_bytes()) if cache.exists() else []
    only = {x.strip() for x in args.sets.split(",") if x.strip()} or None
    if have and not args.refresh and not args.extract:
        data = have
        print(f"cache: {len(data)} utterances from {cache}  (--extract tops it up)")
    else:
        data = extract(Path(args.root), args.model, args.arm, args.k, args.max_utts,
                       have=[] if args.refresh else have, only=only)
        if len(data) < len(have) and not args.refresh:
            print(f"extracted {len(data)} but the cache already held {len(have)}; keeping the cache")
            data = have
        elif not data:
            print("extracted nothing: no utterance in those dumps carries usable word_conf")
            print("(the cache was left untouched)")
            return 2
        else:
            cache.write_bytes(pickle.dumps(data))
            per = {}
            for d in data:
                per[d["set"]] = per.get(d["set"], 0) + 1
            print(f"cache now {len(data)} utterances -> {cache}")
            print("  " + "  ".join(f"{k}:{v}" for k, v in sorted(per.items())))
    sets = sorted({d["set"] for d in data})
    dev = [d for d in data if d["set"] in DEV_SETS]
    test = [d for d in data if d["set"] not in DEV_SETS]
    print(f"sets {sets}\ndev {len(dev)} utts ({', '.join(DEV_SETS)}), test {len(test)} utts\n")
    if not dev:
        print("no dev utterances: this campaign has no ls-dev-* sets, so there is nothing")
        print("to fit on that is not also being scored. Refusing to report a tuned number.")
        return 2

    pairs = conf_label_pairs(dev)
    print(f"calibration pairs from dev: {len(pairs[0])} (word, correct) observations")
    iso = fit_isotonic(*pairs)
    pw = fit_power(*pairs)
    print(f"power fit: conf ** {pw:.3f}")
    show_reliability(*pairs, iso, pw)

    maps = {"as-is": None, "isotonic": iso, f"power {pw:.2f}": lambda c: c ** pw}
    print(f"\n{'arm':<16}{'alpha':>7}{'eps':>6}{'dev WER':>10}   tuned on dev")
    tuned = {}
    for name, m in maps.items():
        a, e, w = tune(dev, m)
        tuned[name] = (a, e, m)
        print(f"{name:<16}{a:>7.2f}{e:>6.2f}{w:>10.2f}")
    tuned["freq only"] = (1.0, 0.5, None)
    a, e, w = 1.0, 0.5, wer(dev, None, 1.0, 0.5)
    print(f"{'freq only':<16}{a:>7.2f}{e:>6.2f}{w:>10.2f}   (control: confidence ignored)")
    sa, se_ = SHIPPED["alpha"], SHIPPED["eps"]
    print(f"{'shipped':<16}{sa:>7.2f}{se_:>6.2f}{wer(dev, None, sa, se_):>10.2f}   (what runs today)")

    print(f"\n{'held-out set':<18}{'shipped':>9}{'as-is*':>9}{'isotonic':>10}{'power':>8}"
          f"{'freq':>8}{'best delta':>12}")
    print("-" * 76)
    names = ["as-is", "isotonic", f"power {pw:.2f}", "freq only"]
    pool = {n: [0.0, 0.0] for n in names + ["shipped"]}
    for s in sorted({d["set"] for d in test}):
        x = [d for d in test if d["set"] == s]
        vals = {}
        for n in names:
            a, e, m = tuned[n]
            vals[n] = wer(x, m, a, e)
            pool[n][0] += edits(x, m, a, e); pool[n][1] += reflen(x)
        base = wer(x, None, sa, se_)
        pool["shipped"][0] += edits(x, None, sa, se_); pool["shipped"][1] += reflen(x)
        best = min(vals.values())
        print(f"{s:<18}{base:>9.2f}{vals['as-is']:>9.2f}{vals['isotonic']:>10.2f}"
              f"{vals[f'power {pw:.2f}']:>8.2f}{vals['freq only']:>8.2f}{best - base:>+12.2f}")
    print("-" * 76)
    row = "".join(f"{100 * pool[n][0] / pool[n][1]:>9.2f}" if n == "shipped" else "" for n in ["shipped"])
    line = f"{'POOLED':<18}{100 * pool['shipped'][0] / pool['shipped'][1]:>9.2f}"
    for n, wdt in (("as-is", 9), ("isotonic", 10), (f"power {pw:.2f}", 8), ("freq only", 8)):
        line += f"{100 * pool[n][0] / pool[n][1]:>{wdt}.2f}"
    bestp = min(100 * pool[n][0] / pool[n][1] for n in names)
    line += f"{bestp - 100 * pool['shipped'][0] / pool['shipped'][1]:>+12.2f}"
    print(line)
    print("\n* as-is = today's confidences with (alpha, eps) re-tuned on dev, so the")
    print("  calibrated arms are not being credited for tuning the shipped arm never got.")
    print("  negative delta = better. If 'freq only' wins, the confidence signal is noise.")

    boot(test, tuned, pw, sa, se_)
    return 0


# ------------------------------------------------------------------------- calibration fits

def conf_label_pairs(data: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Every (reported confidence, is-this-the-reference-word) pair, over all slots."""
    c, y = [], []
    for d in data:
        for sl, r in zip(d["slots"], d["ref_by_slot"]):
            if r == "":
                continue
            n = sum(v[0] for w, v in sl.items() if w != "")
            for w, v in sl.items():
                if w == "" or v[0] <= 0:
                    continue
                c.append(v[1] / v[0])          # mean confidence of the votes for this word
                y.append(1.0 if w == r else 0.0)
        del n
    return np.asarray(c), np.asarray(y)


def fit_isotonic(c: np.ndarray, y: np.ndarray, n_bins: int = 40):
    """Monotone map from reported confidence to empirical correctness, no sklearn.

    Quantile-binned means, then pool-adjacent-violators to force monotonicity, then linear
    interpolation between bin centres. Binning first is deliberate: raw PAVA on 11k points
    fits every wiggle, and the thing being corrected here is a smooth scale error.
    """
    order = np.argsort(c, kind="stable")
    c, y = c[order], y[order]
    edges = np.unique(np.quantile(c, np.linspace(0, 1, n_bins + 1)))
    idx = np.clip(np.searchsorted(edges, c, side="right") - 1, 0, len(edges) - 2)
    xs, ys, ws = [], [], []
    for b in range(len(edges) - 1):
        m = idx == b
        if m.sum() == 0:
            continue
        xs.append(float(c[m].mean())); ys.append(float(y[m].mean())); ws.append(float(m.sum()))

    # pool adjacent violators, weighted
    i = 0
    while i < len(ys) - 1:
        if ys[i] <= ys[i + 1] + 1e-12:
            i += 1
            continue
        w = ws[i] + ws[i + 1]
        ys[i] = (ys[i] * ws[i] + ys[i + 1] * ws[i + 1]) / w
        xs[i] = (xs[i] * ws[i] + xs[i + 1] * ws[i + 1]) / w
        ws[i] = w
        del ys[i + 1], xs[i + 1], ws[i + 1]
        if i:
            i -= 1
    gx, gy = np.asarray(xs), np.clip(np.asarray(ys), 0.0, 1.0)
    return lambda x: np.interp(np.atleast_1d(x), gx, gy)


def fit_power(c: np.ndarray, y: np.ndarray) -> float:
    """conf ** t, t chosen to minimise squared calibration error. One parameter, hard to overfit."""
    best, best_t = None, 1.0
    for t in np.arange(0.5, 12.01, 0.05):
        e = float(np.mean((c ** t - y) ** 2))
        if best is None or e < best:
            best, best_t = e, float(t)
    return best_t


def show_reliability(c, y, iso, pw):
    edges = [0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 0.98, 0.995, 1.0001]
    print(f"\n{'dev conf bin':<16}{'n':>9}{'reported':>10}{'true':>8}{'isotonic':>10}{'power':>8}")
    for i in range(len(edges) - 1):
        m = (c >= edges[i]) & (c < edges[i + 1])
        if m.sum() == 0:
            continue
        print(f"{f'{edges[i]:.3f}-{edges[i+1]:.3f}':<16}{int(m.sum()):>9}{c[m].mean():>10.3f}"
              f"{y[m].mean():>8.3f}{float(np.mean(iso(c[m]))):>10.3f}"
              f"{float(np.mean(c[m] ** pw)):>8.3f}")


# ------------------------------------------------------------------------------ re-voting

def pick(slot: dict, total: float, alpha: float, eps: float, m) -> str:
    best, bw = None, ""
    for w, (votes, conf_sum) in slot.items():
        if votes <= 0 and w != "":
            continue
        freq = votes / total if total else 0.0
        if w == "":
            conf = eps
        else:
            conf = conf_sum / votes if votes > 0 else 0.0
            if m is not None:
                conf = float(np.atleast_1d(m(conf))[0])
        s = alpha * freq + (1.0 - alpha) * conf
        if best is None or s > best:
            best, bw = s, w
    return bw


def edits(data: list[dict], m, alpha: float, eps: float) -> float:
    from rapidfuzz.distance import Levenshtein
    tot = 0
    for d in data:
        h = [pick(sl, float(d["n_cand"]), alpha, eps, m) for sl in d["slots"]]
        tot += Levenshtein.distance(d["ref"], [w for w in h if w != ""])
    return float(tot)


def reflen(data: list[dict]) -> float:
    return float(sum(len(d["ref"]) for d in data))


def wer(data: list[dict], m, alpha: float, eps: float) -> float:
    r = reflen(data)
    return 100.0 * edits(data, m, alpha, eps) / r if r else float("nan")


def tune(dev: list[dict], m) -> tuple[float, float, float]:
    best = None
    for a in GRID_ALPHA:
        for e in GRID_EPS:
            w = wer(dev, m, a, e)
            if best is None or w < best[2]:
                best = (a, e, w)
    return best


def boot(test, tuned, pw, sa, se_):
    sys.path.insert(0, "src")
    import bootstrap
    from rapidfuzz.distance import Levenshtein

    def per_utt(m, a, e):
        return [Levenshtein.distance(d["ref"],
                [w for w in (pick(sl, float(d["n_cand"]), a, e, m) for sl in d["slots"]) if w != ""])
                for d in test]

    base = per_utt(None, sa, se_)
    rl = [len(d["ref"]) for d in test]
    print(f"\npaired bootstrap over {len(test)} held-out utterances, vs what runs today")
    for n in ["as-is", "isotonic", f"power {pw:.2f}", "freq only"]:
        a, e, m = tuned[n]
        st = bootstrap.paired_bootstrap(base, per_utt(m, a, e), rl, n_boot=4000)
        flag = "" if st["ci_low"] > 0 or st["ci_high"] < 0 else "   spans zero"
        print("  " + bootstrap.format_row(n, st) + flag)


if __name__ == "__main__":
    raise SystemExit(main())
