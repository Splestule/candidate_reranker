#!/usr/bin/env python3
"""MOVER against our ROVER on the candidate dumps, CPU only.

    PYTHONPATH=src python tools/mover_experiment.py --dumps D1 [D2 ...] --out results/mover

MOVER (Kamo et al., Interspeech 2025, arXiv:2508.05055) is ROVER extended to meeting outputs:
1) speaker label mapping, 2) segment grouping, 3) pseudo word timings in proportion to character
count, 4) ROVER whose DP only lets two words match or substitute when their timings overlap
within a collar (TC-DP, 5 s in the paper), with most-frequent-word voting and nulls dropped,
5) order consistency resolution, which only moves timings. On one utterance from one speaker,
stages 1, 2 and 5 do nothing, so what is left to test is stage 4 with stage 3's timings:
incremental alignment of each hypothesis to the growing network, in system order, under a time
constraint. That is implemented here as written; the ROVER it is compared with is ours, which
aligns every candidate to the MBR candidate and votes with confidences and near-duplicate
down-weighting.

Everything is scored under one normalisation: Whisper's (English normaliser for en, the basic
one otherwise), applied to the raw reference and to the raw candidates before any combination,
so the words that are voted on are the words that are scored.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd
from rapidfuzz.distance import Levenshtein

import compose
import scorers as S

ALPHA, EPS_C, GAMMA = 0.5, 0.7, 0.5          # ROVER_DEFAULT in campaign.analysis
TEST_KINDS = {"main", "lowT", "sweepT"}
MAIN_ARMS = {("whisfusion", "main"), ("drax", "main"), ("drax", "lowT"), ("whisper-small", "sample"),
             ("whisper-turbo", "sample"), ("parakeet-ctc", "sample")}

_norm = {}


def wn(text: str, lang: str) -> list[str]:
    if not _norm:
        from whisper_normalizer.basic import BasicTextNormalizer
        from whisper_normalizer.english import EnglishTextNormalizer
        _norm["en"], _norm["basic"] = EnglishTextNormalizer(), BasicTextNormalizer()
    return (_norm["en"] if lang == "en" else _norm["basic"])(text).split()


# ------------------------------------------------------------------------------------ MOVER

def pseudo_times(words: list[str], dur: float) -> list[tuple[float, float]]:
    """Stage 3, character-based: each word gets time in proportion to its length."""
    L = sum(len(w) for w in words)
    t, out = 0.0, []
    for w in words:
        d = dur * len(w) / L if L else 0.0
        out.append((t, t + d))
        t += d
    return out


def mover(cands: list[list[str]], dur: float, collar: float, order: list[int]) -> list[str]:
    """Stage 4: incremental alignment to the network with a time constraint, then majority."""
    if not order:
        return []
    h0 = order[0]
    slots = [dict(cnt={w: 1}, rank={w: 0}, b=b, e=e)
             for w, (b, e) in zip(cands[h0], pseudo_times(cands[h0], dur))]

    def vote(s, w, r):
        s["cnt"][w] = s["cnt"].get(w, 0) + 1
        s["rank"].setdefault(w, r)

    for r, h in enumerate(order[1:], start=1):
        hw = cands[h]
        ht = pseudo_times(hw, dur)
        n, m = len(slots), len(hw)
        D = [[0] * (m + 1) for _ in range(n + 1)]
        B = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            D[i][0] = D[i - 1][0] + (0 if None in slots[i - 1]["cnt"] else 1)
            B[i][0] = 1
        for j in range(1, m + 1):
            D[0][j] = j
            B[0][j] = 2
        for i in range(1, n + 1):
            s = slots[i - 1]
            cnt, sb, se = s["cnt"], s["b"] - collar, s["e"] + collar
            dcost = 0 if None in cnt else 1
            Di, Dp = D[i], D[i - 1]
            for j in range(1, m + 1):
                b, e = ht[j - 1]
                best, bt = Dp[j] + dcost, 1                      # hypothesis has null here
                c = Di[j - 1] + 1                                # new slot for this word
                if c < best:
                    best, bt = c, 2
                if b < se and sb < e:                            # TC-DP: only if timings overlap
                    c = Dp[j - 1] + (0 if hw[j - 1] in cnt else 1)
                    if c <= best:
                        best, bt = c, 0
                Di[j] = best
                B[i][j] = bt
        i, j, ops = n, m, []
        while i > 0 or j > 0:
            bt = B[i][j]
            if bt == 0:
                ops.append((0, i - 1, j - 1)); i -= 1; j -= 1
            elif bt == 1:
                ops.append((1, i - 1, None)); i -= 1
            else:
                ops.append((2, None, j - 1)); j -= 1
        new = []
        for op, si, wj in reversed(ops):
            if op == 0:
                s = slots[si]
                vote(s, hw[wj], r)
                s["b"], s["e"] = min(s["b"], ht[wj][0]), max(s["e"], ht[wj][1])
            elif op == 1:
                s = slots[si]
                vote(s, None, r)
            else:
                s = dict(cnt={None: r}, rank={None: 0}, b=ht[wj][0], e=ht[wj][1])
                vote(s, hw[wj], r)
            new.append(s)
        slots = new
    out = []
    for s in slots:
        w = max(s["cnt"], key=lambda x: (s["cnt"][x], -s["rank"][x]))
        if w is not None:
            out.append(w)
    return out


# ---------------------------------------------------------------------------------- per file

def confs_for(c: dict, n: int) -> list[float]:
    wc = c.get("word_conf")
    if wc is not None and len(wc) == n:
        return [float(x) for x in wc]
    a = min(max(float(c.get("avg_conf", 0.5)), 0.0), 1.0)
    return [a] * n


def mbr_pick(cands: list[list[str]]) -> int:
    k = len(cands)
    if k == 1:
        return 0
    lens = [max(len(c), 1) for c in cands]
    sc = [sum(Levenshtein.distance(cands[i], cands[j]) / lens[j] for j in range(k) if j != i)
          for i in range(k)]
    return min(range(k), key=lambda i: sc[i])


def run_file(task: tuple) -> list[dict]:
    path, model, set_name, kind, arm, shard = task
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    out = []
    for row in rows:
        raw = row.get("candidates") or []
        if len(raw) < 2:
            continue
        lang = row.get("lang", "en")
        ref = wn(row["reference"], lang)
        if not ref:
            continue
        cands = [wn(c["text"], lang) for c in raw]
        confs = [confs_for(c, len(t)) for c, t in zip(raw, cands)]
        dur = float(row.get("duration_s") or 0.07 * len(row["reference"]))
        k = len(cands)
        p = mbr_pick(cands)
        slots1 = compose.confusion_network(cands, p, confs, None)
        w05 = compose.cluster_weights(cands, GAMMA)
        slots05 = compose.confusion_network(cands, p, confs, w05)
        h = dict(
            mbr=cands[p],
            rover_freq=compose.rover(slots1, float(k), 1.0, 0.5),
            rover_cg=compose.rover(slots05, sum(w05), ALPHA, EPS_C),
            mover=mover(cands, dur, 5.0, list(range(k))),
            mover_c1=mover(cands, dur, 1.0, list(range(k))),
            mover_nc=mover(cands, dur, math.inf, list(range(k))),
            mover_mbrfirst=mover(cands, dur, 5.0, [p] + [i for i in range(k) if i != p]),
        )
        # what the earlier wn_* columns scored: ROVER on legacy tokens, then Whisper-normalised
        lg = [S.normalize(c["text"]).split() for c in raw]
        lconf = [confs_for(c, len(t)) for c, t in zip(raw, lg)]
        lw = compose.cluster_weights(lg, GAMMA)
        lslots = compose.confusion_network(lg, mbr_pick(lg), lconf, lw)
        old_cg = wn(" ".join(compose.rover(lslots, sum(lw), ALPHA, EPS_C)), lang)
        rec = dict(model=model, set=set_name, kind=kind, arm=arm, shard=shard, id=row["id"],
                   cluster=row.get("cluster") or row["id"], k=k, ref_len=len(ref),
                   pairwise=100.0 * sum(Levenshtein.distance(cands[i], cands[j]) /
                                        max(len(cands[i]), len(cands[j]), 1)
                                        for i in range(k) for j in range(i + 1, k)) / (k * (k - 1) / 2),
                   e_first=Levenshtein.distance(ref, cands[0]),
                   e_oracle=min(Levenshtein.distance(ref, c) for c in cands),
                   e_rover_cg_oldwn=Levenshtein.distance(ref, old_cg))
        for name, hyp in h.items():
            rec[f"e_{name}"] = Levenshtein.distance(ref, hyp)
        out.append(rec)
    return out


def tasks_from(dump_dirs: list[Path]) -> list[tuple]:
    out = []
    for d in dump_dirs:
        for jd in sorted(p for p in d.iterdir() if p.is_dir()):
            model, set_name, shard, kind = jd.name.split("__")
            if kind not in TEST_KINDS or set_name.startswith("ls-dev"):
                continue
            for f in sorted(jd.glob("*.jsonl.gz")):
                arm = f.name[: -len(".jsonl.gz")]
                if kind == "sweepT":
                    if arm == "greedy":
                        continue
                elif (model, arm) not in MAIN_ARMS or shard != "s00":
                    continue
                out.append((str(f), model, set_name, kind, arm, int(shard[1:])))
    return out


def boot(delta: pd.Series, ref_len: pd.Series, n: int = 1000, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    d, w = delta.to_numpy(), ref_len.to_numpy()
    idx = range(len(d))
    vals = []
    for _ in range(n):
        s = rng.choices(idx, k=len(d))
        vals.append(100.0 * sum(d[i] for i in s) / max(sum(w[i] for i in s), 1))
    vals.sort()
    return vals[int(0.025 * n)], vals[int(0.975 * n)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tasks = tasks_from([Path(d) for d in args.dumps])
    print(f"{len(tasks)} dump files", flush=True)
    recs = []
    with ProcessPoolExecutor(args.workers) as ex:
        for i, r in enumerate(ex.map(run_file, tasks, chunksize=1)):
            recs.extend(r)
            if (i + 1) % 25 == 0:
                print(f"  {i + 1}/{len(tasks)} files, {len(recs)} utterances", flush=True)
    df = pd.DataFrame(recs)
    df.to_parquet(out / "mover_per_utt.parquet", index=False)

    meths = ["first", "mbr", "rover_freq", "rover_cg", "mover", "mover_c1", "mover_nc",
             "mover_mbrfirst", "oracle", "rover_cg_oldwn"]
    rows = []
    for (m, kind, arm), g in df.groupby(["model", "kind", "arm"]):
        w = g["ref_len"].sum()
        r = dict(model=m, kind=kind, arm=arm, n=len(g), sets=g["set"].nunique(), K=int(g["k"].max()),
                 pairwise=g["pairwise"].mean())
        for me in meths:
            r[me] = 100.0 * g[f"e_{me}"].sum() / w
        d = g["e_mover"] - g["e_rover_cg"]
        r["mover_minus_rover"] = 100.0 * d.sum() / w
        r["ci_lo"], r["ci_hi"] = boot(d, g["ref_len"])
        rows.append(r)
    t = pd.DataFrame(rows).sort_values(["kind", "model", "pairwise"])
    t.round(3).to_csv(out / "mover_summary.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(t.round(2).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
