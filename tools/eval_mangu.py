#!/usr/bin/env python3
"""Settle the backbone-free network properly: tuned on dev, measured on test, and timed.

tools/mangu_net.py showed +0.63 at K=12 and +0.41 at K=24 with every hyper-parameter left
at whatever I first typed. This does the version the result has to survive:

  sim, alpha and eps are chosen on the DEV sets and applied unchanged to the test sets,
  separately for each network, so neither arm is credited with tuning the other never got;
  the sweep covers K up to the real operating point;
  both constructions are TIMED, because "composing is free" (1.2 ms, a thousandth of the
  decode) is part of what this project claims, and the backbone-free build is O(K^2)
  pairwise alignments plus a merge loop. If it costs 200 ms the claim changes.

Per-utterance work is independent, so --workers spreads it over cores; this is CPU-only
and needs no GPU at any K.

    PYTHONPATH=src python tools/eval_mangu.py results/campaign-2026-09-20 \\
        --k 32 --max_utts 200 --workers 8
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import pickle
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

DEV_SETS = ("ls-dev-clean", "ls-dev-other")
GRID_SIM = [0.30, 0.40, 0.45, 0.55, 0.65, 0.80, 1.01]   # 1.01 = no inter-word merging at all
GRID_ALPHA = [0.3, 0.5, 0.7, 0.85, 1.0]
GRID_EPS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
EPS = ""


def load(root: str, model: str, arm: str, k: int, max_utts: int, cache: Path):
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    sys.path.insert(0, "src")
    from scorers import normalize
    rows, per = [], defaultdict(int)
    for job in sorted(glob.glob(f"{root}/dumps/{model}__*")):
        parts = Path(job).name.split("__")
        if len(parts) < 4 or parts[3] != arm:
            continue
        s = parts[1]
        p = Path(job) / f"{arm}.jsonl.gz"
        if not p.exists() or per[s] >= max_utts:
            continue
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                raw = r["candidates"][:k]
                cs = [normalize(c["text"]).split() for c in raw]
                keep = [i for i, (w, c) in enumerate(zip(cs, raw))
                        if w and "word_conf" in c and len(c["word_conf"]) == len(w)]
                ref = normalize(r["reference"]).split()
                if len(keep) < 2 or not ref:
                    continue
                rows.append(dict(set=s, id=r["id"], ref=ref,
                                 cands=[cs[i] for i in keep],
                                 confs=[list(raw[i]["word_conf"]) for i in keep]))
                per[s] += 1
                if per[s] >= max_utts:
                    break
    cache.write_bytes(pickle.dumps(rows))
    return rows


def nets_for(row: dict, sims: list[tuple[float, float]]):
    """Both networks for one utterance, plus the wall clock each construction took."""
    sys.path.insert(0, "src")
    sys.path.insert(0, "tools")
    import compose
    import mangu_net

    t0 = time.perf_counter()
    bb = compose.central_index(row["cands"])
    base = compose.confusion_network(row["cands"], bb, row["confs"], None)
    t_base = (time.perf_counter() - t0) * 1000.0

    out = {"backbone": base}
    t_mangu = {}
    for sim, g, ph in sims:
        t0 = time.perf_counter()
        out[f"mangu{sim:g}g{g:g}{'p' if ph else 'c'}"] = mangu_net.build(
            row["cands"], row["confs"], sim, g, ph)
        t_mangu[(sim, g, ph)] = (time.perf_counter() - t0) * 1000.0
    return out, t_base, t_mangu


def score(slots: list[dict], total: float, ref: list[str], alpha: float, eps: float) -> int:
    sys.path.insert(0, "src")
    import compose
    from rapidfuzz.distance import Levenshtein
    return Levenshtein.distance(ref, compose.rover(slots, total, alpha, eps))


def work(row: dict, sims: list[float]):
    nets, t_base, t_mangu = nets_for(row, sims)
    total = float(len(row["cands"]))
    edits = {}
    for name, sl in nets.items():
        for a in GRID_ALPHA:
            for e in GRID_EPS:
                edits[(name, a, e)] = score(sl, total, row["ref"], a, e)
    shape = {name: (len(sl), sum(len(x) for x in sl)) for name, sl in nets.items()}
    return dict(set=row["set"], id=row["id"], n_ref=len(row["ref"]), edits=edits,
                shape=shape, t_base=t_base, t_mangu=t_mangu)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max_utts", type=int, default=100)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--sims", default="", help="comma-separated sim thresholds; the full grid "
                    "rebuilds every utterance once per value, so narrow it at high K")
    ap.add_argument("--gammas", default="1.0", help="merge-evidence weighting; 1.0 is "
                    "unweighted, 0.0 collapses identical candidates to one vote")
    ap.add_argument("--phon", action="store_true",
                    help="also build a variant using CMUdict phonemes for inter-word merging")
    ap.add_argument("--budget", type=int, default=0,
                    help="score at most this many NEW utterances, then save and report on "
                         "whatever is done. 0 means all of them.")
    ap.add_argument("--cache", default=None)
    a = ap.parse_args()

    sys.path.insert(0, "src")
    sys.path.insert(0, "tools")
    import bootstrap

    global GRID_SIM
    sims = [float(x) for x in a.sims.split(",") if x.strip()] or [0.45]
    gammas = [float(x) for x in a.gammas.split(",") if x.strip()] or [1.0]
    phons = [False, True] if a.phon else [False]
    GRID_SIM = [(s_, g_, p_) for s_ in sims for g_ in gammas for p_ in phons]
    cache = Path(a.cache or f"results/eval_mangu_k{a.k}_n{a.max_utts}.pkl")
    rows = load(a.root, a.model, a.arm, a.k, a.max_utts, cache)
    dev = [r for r in rows if r["set"] in DEV_SETS]
    test = [r for r in rows if r["set"] not in DEV_SETS]
    print(f"K<={a.k}: {len(rows)} utterances, dev {len(dev)}, test {len(test)}, "
          f"{len(set(r['set'] for r in test))} held-out sets")
    if not dev or not test:
        print("need both dev and test sets in this campaign")
        return 2

    # results are saved as they are produced: a long run used to print to a terminal and
    # leave nothing behind, so an interrupted or unattended run lost everything it computed
    tag = "-".join(f"{x:g}x{y:g}{'p' if z else 'c'}" for x, y, z in GRID_SIM)
    rpath = cache.with_name(cache.stem + f"__res_{tag}.pkl")
    done = pickle.loads(rpath.read_bytes()) if rpath.exists() else []
    have = {(r["set"], r["id"]) for r in done}
    todo = [r for r in rows if (r["set"], r["id"]) not in have]
    # round-robin across sets, so a partial run is balanced rather than all of one corpus
    rank = defaultdict(int)
    keyed = []
    for r in todo:
        keyed.append((rank[r["set"]], r["set"], r))
        rank[r["set"]] += 1
    todo = [r for _, _, r in sorted(keyed, key=lambda t: (t[0], t[1]))]
    if a.budget:
        todo = todo[: a.budget]
    if todo:
        t0 = time.time()
        if a.workers > 1:
            from multiprocessing import Pool
            with Pool(a.workers) as pool:
                new = pool.starmap(work, [(r, GRID_SIM) for r in todo], chunksize=4)
        else:
            new = [work(r, GRID_SIM) for r in todo]
        done += new
        rpath.write_bytes(pickle.dumps(done))
        print(f"scored {len(new)} new in {time.time() - t0:.0f} s on {a.workers} worker(s)")
    res = done
    have = {(r["set"], r["id"]) for r in res}
    rows = [r for r in rows if (r["set"], r["id"]) in have]
    dev = [r for r in rows if r["set"] in DEV_SETS]
    test = [r for r in rows if r["set"] not in DEV_SETS]
    print(f"reporting on {len(res)} scored utterances "
          f"({len(todo) and len(rows)} of the cache); results in {rpath.name}\n")
    if not dev or not test:
        print("not enough scored yet on both sides of the split; run again to add more")
        return 0

    by_id = {(r["set"], r["id"]): r for r in res}
    names = ["backbone"] + [f"mangu{s_:g}g{g_:g}{'p' if p_ else 'c'}" for s_, g_, p_ in GRID_SIM]

    def wer(rs, name, al, e):
        num = sum(by_id[(r["set"], r["id"])]["edits"][(name, al, e)] for r in rs)
        den = sum(len(r["ref"]) for r in rs)
        return 100.0 * num / den if den else float("nan")

    # ---- tune each network on dev, separately, so neither arm is favoured
    print(f"{'network':<12}{'sim/gamma':>12}{'alpha':>7}{'eps':>6}{'dev WER':>10}")
    best = {}
    for name in names:
        b = min(((al, e, wer(dev, name, al, e)) for al in GRID_ALPHA for e in GRID_EPS),
                key=lambda t: t[2])
        best[name] = b
    bb_best = best["backbone"]
    print(f"{'backbone':<12}{'-':>12}{bb_best[0]:>7.2f}{bb_best[1]:>6.2f}{bb_best[2]:>10.2f}")
    mg_name = min((n for n in names if n != "backbone"), key=lambda n: best[n][2])
    for n in names:
        if n == "backbone":
            continue
        mark = "  <- chosen" if n == mg_name else ""
        print(f"{'mangu':<12}{n[5:]:>12}{best[n][0]:>7.2f}{best[n][1]:>6.2f}"
              f"{best[n][2]:>10.2f}{mark}")

    # ---- apply to test
    al_b, e_b, _ = best["backbone"]
    al_m, e_m, _ = best[mg_name]
    print(f"\n{'held-out set':<18}{'n':>5}{'backbone':>10}{'mangu':>9}{'delta':>8}")
    print("-" * 50)
    for s in sorted({r["set"] for r in test}):
        x = [r for r in test if r["set"] == s]
        b, m = wer(x, "backbone", al_b, e_b), wer(x, mg_name, al_m, e_m)
        print(f"{s:<18}{len(x):>5}{b:>10.2f}{m:>9.2f}{m - b:>+8.2f}")
    b, m = wer(test, "backbone", al_b, e_b), wer(test, mg_name, al_m, e_m)
    print("-" * 50)
    print(f"{'POOLED':<18}{len(test):>5}{b:>10.2f}{m:>9.2f}{m - b:>+8.2f}")

    pb = [by_id[(r["set"], r["id"])]["edits"][("backbone", al_b, e_b)] for r in test]
    pm = [by_id[(r["set"], r["id"])]["edits"][(mg_name, al_m, e_m)] for r in test]
    rl = [len(r["ref"]) for r in test]
    st = bootstrap.paired_bootstrap(pb, pm, rl, n_boot=8000)
    flag = "" if st["ci_low"] > 0 or st["ci_high"] < 0 else "   spans zero"
    print("\n" + bootstrap.format_row("mangu vs backbone (held out)", st) + flag)

    # ---- shape and cost
    sim_g = next(k for k in GRID_SIM
                 if f"mangu{k[0]:g}g{k[1]:g}{'p' if k[2] else 'c'}" == mg_name)
    tb = sum(r["t_base"] for r in res) / len(res)
    tm = sum(r["t_mangu"][sim_g] for r in res) / len(res)
    sb = sum(r["shape"]["backbone"][0] for r in res) / len(res)
    sm = sum(r["shape"][mg_name][0] for r in res) / len(res)
    zb = sum(r["shape"]["backbone"][1] for r in res) / sum(r["shape"]["backbone"][0] for r in res)
    zm = sum(r["shape"][mg_name][1] for r in res) / sum(r["shape"][mg_name][0] for r in res)
    print(f"\n{'':<12}{'slots':>8}{'slot size':>11}{'build ms':>10}{'% of a 2117 ms decode':>24}")
    print(f"{'backbone':<12}{sb:>8.1f}{zb:>11.2f}{tb:>10.2f}{100 * tb / 2117.0:>23.3f}%")
    print(f"{'mangu':<12}{sm:>8.1f}{zm:>11.2f}{tm:>10.2f}{100 * tm / 2117.0:>23.3f}%")
    print("\n(2117 ms is the measured Whisfusion decode at K=32, run 8. If the mangu build")
    print(" is a large fraction of it, 'composing is free' stops being true and the paper")
    print(" has to say so.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
