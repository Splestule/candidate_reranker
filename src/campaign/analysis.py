#!/usr/bin/env python3
"""Per-utterance metrics for one dump (one job x arm), along a ladder of candidate counts.

Candidates in a dump are exchangeable draws, so the first k of them are a faithful simulation of
having decoded only k (see allocate.py). For every utterance and every k on the ladder this
records the edit count of each method, so any corpus WER, paired test or regression can be
computed later from integers without touching the candidates again:

    first          candidate 0: one decode, no selection at all
    conf, minconf, logprob     pick the candidate with the best model score
    mbr            pick the most central candidate (minimum Bayes risk under WER)
    cm05, cm15     conf + lambda * mbr, lambda 0.5 and 1.5
    rover_freq     ROVER, one vote per candidate
    rover_c        ROVER mixing vote share and word confidence (alpha 0.5, eps 0.7)
    rover_cg       the same with near-duplicate candidates sharing a vote (gamma 0.5)
    oracle_cand    best single candidate (needs the reference)
    oracle_comp    best path through the confusion network (needs the reference)
    control        oracle_comp with every alternative replaced by an unrelated word
    anti           worst single candidate

wn_* are the same edits after Whisper's text normaliser (the Open ASR Leaderboard convention),
for the main methods. A second table holds a parameter grid at the main k, for tuning on dev
and applying on test without re-running anything.
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import statistics
import sys
import time
import zlib
from pathlib import Path

from rapidfuzz.distance import Levenshtein

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import compose  # noqa: E402
import scorers as S  # noqa: E402

LADDER = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20, 24, 32, 48, 64]
ORACLE_KS = {2, 4, 8, 15, 16, 32, 64}
WN_KS = {1, 15, 16}
GRID_ALPHA = [0.3, 0.5, 0.7, 0.85, 1.0]
GRID_EPS = [0.3, 0.5, 0.7]
GRID_GAMMA = [0.0, 0.5, 1.0]
LAMBDAS = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
ROVER_DEFAULT = dict(alpha=0.5, eps=0.7, gamma=0.5)


# ------------------------------------------------------------------------------ normalisers

class WhisperNorm:
    """Whisper's English normaliser for en, the basic one otherwise; None if unavailable."""

    def __init__(self):
        self.en = self.basic = None
        try:
            from whisper_normalizer.basic import BasicTextNormalizer
            from whisper_normalizer.english import EnglishTextNormalizer
            self.en, self.basic = EnglishTextNormalizer(), BasicTextNormalizer()
            return
        except Exception:
            pass
        try:  # the same code ships inside transformers; it needs the spelling map of a tokenizer
            from transformers import WhisperTokenizer
            from transformers.models.whisper.english_normalizer import (BasicTextNormalizer,
                                                                        EnglishTextNormalizer)
            tok = WhisperTokenizer.from_pretrained("openai/whisper-small")
            self.en = EnglishTextNormalizer(tok.english_spelling_normalizer)
            self.basic = BasicTextNormalizer()
        except Exception:
            pass

    @property
    def ok(self) -> bool:
        return self.en is not None

    def __call__(self, text: str, lang: str) -> list[str]:
        f = self.en if lang == "en" else self.basic
        return f(text).split()


# ---------------------------------------------------------------------------------- loading

def read_dump(path: Path) -> list[dict]:
    rows = []
    opener = gzip.open if str(path).endswith(".gz") else open
    try:
        with opener(path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except (EOFError, OSError):
        pass
    return rows


def prepare(row: dict) -> tuple[list[list[str]], list[list[float]], float]:
    """Word lists and per-word confidences. A candidate without usable word confidences gets
    its own mean confidence on every word, so confidence-weighted voting stays defined."""
    cands, confs, exact = [], [], 0
    for c in row["candidates"]:
        words = S.normalize(c["text"]).split()
        wc = c.get("word_conf")
        if wc is not None and len(wc) == len(words):
            confs.append([float(x) for x in wc])
            exact += 1
        else:
            a = float(c.get("avg_conf", 0.5))
            a = min(max(a, 0.0), 1.0)
            confs.append([a] * len(words))
        cands.append(words)
    return cands, confs, exact / max(len(cands), 1)


# --------------------------------------------------------------------------------- analysis

def argbest(values: list[float]) -> int:
    best, bi = None, 0
    for i, v in enumerate(values):
        if best is None or v > best:
            best, bi = v, i
    return bi


def analyze_row(row: dict, k_main: int, pool: list[str], wn: WhisperNorm, meta: dict):
    ref = S.normalize(row["reference"]).split()
    R = len(ref)
    lang = row.get("lang", "en")
    cands, confs, conf_frac = prepare(row)
    K = len(cands)
    if K == 0:
        return [], []
    raw = row["candidates"]
    ed = [Levenshtein.distance(ref, c) for c in cands]
    lens = [len(c) for c in cands]
    Lm = [[0] * K for _ in range(K)]
    for i in range(K):
        for j in range(i + 1, K):
            d = Levenshtein.distance(cands[i], cands[j])
            Lm[i][j] = Lm[j][i] = d
    avg = [float(c.get("avg_conf", 0.0)) for c in raw]
    mnc = [float(c.get("min_conf", 0.0)) for c in raw]
    mlp = [float(c.get("mean_logprob", 0.0)) for c in raw]

    use_wn = wn.ok
    if use_wn:
        ref_wn = wn(row["reference"], lang)
        cand_wn = [wn(c["text"], lang) for c in raw]
        ed_wn = [Levenshtein.distance(ref_wn, c) for c in cand_wn]
    rng = random.Random(zlib.crc32(row["id"].encode("utf-8")))

    base = dict(meta, id=row["id"], cluster=row.get("cluster") or row["id"],
                duration_s=row.get("duration_s"), ref_len=R, ref_len_wn=len(ref_wn) if use_wn else None,
                K_avail=K, conf_frac=round(conf_frac, 3), encode_s=row.get("encode_s"),
                decode_s=row.get("decode_s"), n_unique_all=row.get("n_unique"),
                identical_after_step1=row.get("identical_after_step1"))

    out, grid = [], []
    ks = [k for k in LADDER if k <= K]
    if K not in ks:
        ks.append(K)
    for k in ks:
        idx = range(k)
        if k > 1:
            mbr = [-sum(Lm[i][j] / max(lens[j], 1) for j in idx if j != i) / (k - 1) for i in idx]
        else:
            mbr = [0.0]
        p_conf = argbest(avg[:k])
        p_min = argbest(mnc[:k])
        p_lp = argbest(mlp[:k])
        p_mbr = argbest(mbr)
        p_cm05 = argbest([avg[i] + 0.5 * mbr[i] for i in idx])
        p_cm15 = argbest([avg[i] + 1.5 * mbr[i] for i in idx])
        sub, sub_c = cands[:k], confs[:k]

        t0 = time.perf_counter()
        slots1 = compose.confusion_network(sub, p_mbr, sub_c, None)
        w05 = compose.cluster_weights(sub, 0.5)
        slots05 = compose.confusion_network(sub, p_mbr, sub_c, w05)
        h_cg = compose.rover(slots05, sum(w05), ROVER_DEFAULT["alpha"], ROVER_DEFAULT["eps"])
        rover_ms = (time.perf_counter() - t0) * 1000.0
        h_freq = compose.rover(slots1, float(k), 1.0, 0.5)
        h_c = compose.rover(slots1, float(k), ROVER_DEFAULT["alpha"], ROVER_DEFAULT["eps"])

        rec = dict(base, k=k,
                   n_unique=len({" ".join(c) for c in sub}),
                   pairwise=round(100.0 * statistics.fmean(
                       Lm[i][j] / max(lens[i], lens[j], 1) for i in idx for j in idx if i < j), 3)
                   if k > 1 else 0.0,
                   e_first=ed[0], e_conf=ed[p_conf], e_minconf=ed[p_min], e_logprob=ed[p_lp],
                   e_mbr=ed[p_mbr], e_cm05=ed[p_cm05], e_cm15=ed[p_cm15],
                   e_rover_freq=Levenshtein.distance(ref, h_freq),
                   e_rover_c=Levenshtein.distance(ref, h_c),
                   e_rover_cg=Levenshtein.distance(ref, h_cg),
                   e_oracle_cand=min(ed[:k]), e_anti=max(ed[:k]),
                   e_oracle_comp=None, e_control=None, rover_ms=round(rover_ms, 3),
                   len_rover_cg=len(h_cg), len_conf=lens[p_conf])
        if k >= 2 and (k in ORACLE_KS or k == K):
            oc = compose.oracle_path(slots1, ref)
            ctrl = compose.oracle_path(compose.shuffled_control(slots1, pool, rng), ref)
            rec["e_oracle_comp"] = min(oc, rec["e_oracle_cand"])
            rec["e_control"] = min(ctrl, rec["e_oracle_cand"])
        if use_wn and (k in WN_KS or k == k_main or k == K):
            # Build the network from Whisper-normalised candidates rather than normalising
            # ROVER's legacy-normalised output a second time. That second pass cost 2-7 points
            # of pure artifact: legacy strips the apostrophe, so "time\'s leisure" becomes
            # "times leisure" and stays that way, while the reference becomes "time is leisure".
            # Per-word confidences cannot come along -- they index the model\'s own tokens and
            # this normaliser changes the word count -- so wn_rover_freq is the clean metric
            # here and wn_rover_c / _cg fall back to frequency with a flat confidence.
            sub_wn = cand_wn[:k]
            n1 = compose.confusion_network(sub_wn, p_mbr, None, None)
            w5 = compose.cluster_weights(sub_wn, 0.5)
            n5 = compose.confusion_network(sub_wn, p_mbr, None, w5)
            rec.update(wn_first=ed_wn[0], wn_conf=ed_wn[p_conf], wn_mbr=ed_wn[p_mbr],
                       wn_cm05=ed_wn[p_cm05],
                       wn_rover_freq=Levenshtein.distance(
                           ref_wn, compose.rover(n1, float(k), 1.0, 0.5)),
                       wn_rover_c=Levenshtein.distance(
                           ref_wn, compose.rover(n1, float(k), ROVER_DEFAULT["alpha"],
                                                 ROVER_DEFAULT["eps"])),
                       wn_rover_cg=Levenshtein.distance(
                           ref_wn, compose.rover(n5, sum(w5), ROVER_DEFAULT["alpha"],
                                                 ROVER_DEFAULT["eps"])),
                       wn_oracle_cand=min(ed_wn[:k]))
        out.append(rec)

        if k == min(k_main, K):
            gbase = dict(meta, id=row["id"], cluster=base["cluster"], ref_len=R, k=k)
            nets = {1.0: (slots1, float(k)), 0.5: (slots05, sum(w05))}
            for g in GRID_GAMMA:
                if g not in nets:
                    w = compose.cluster_weights(sub, g)
                    nets[g] = (compose.confusion_network(sub, p_mbr, sub_c, w), sum(w))
                slots, tot = nets[g]
                for a in GRID_ALPHA:
                    for e in (GRID_EPS if a < 1.0 else [0.5]):
                        h = compose.rover(slots, tot, a, e)
                        grid.append(dict(gbase, param="rover", alpha=a, eps=e, gamma=g, lam=None,
                                         e=Levenshtein.distance(ref, h)))
            for lam in LAMBDAS:
                p = argbest([avg[i] + lam * mbr[i] for i in idx])
                grid.append(dict(gbase, param="select", alpha=None, eps=None, gamma=None, lam=lam, e=ed[p]))
    return out, grid


def analyze_dump(path: Path, out_dir: Path, meta: dict, k_main: int) -> dict:
    import pandas as pd

    rows = read_dump(path)
    tag = meta["tag"]
    if not rows:
        return {"tag": tag, "n": 0}
    pool = [w for r in rows[:200] for w in S.normalize(r["candidates"][0]["text"]).split()] if rows[0]["candidates"] else []
    if not pool:
        pool = ["the"]
    wn = WhisperNorm()
    recs, grid = [], []
    t0 = time.time()
    for r in rows:
        try:
            a, g = analyze_row(r, k_main, pool, wn, meta)
        except Exception as e:  # one malformed row must not lose the dump
            print(f"[analysis] {tag}/{r.get('id')}: {type(e).__name__}: {e}", flush=True)
            continue
        recs += a
        grid += g
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(recs).to_parquet(out_dir / f"{tag}.parquet", index=False)
    if grid:
        pd.DataFrame(grid).to_parquet(out_dir / f"{tag}.grid.parquet", index=False)
    return {"tag": tag, "n": len(rows), "n_rec": len(recs), "seconds": round(time.time() - t0, 1),
            "wn": wn.ok}


def analyze_job(root: Path, job: dict, k_main: int) -> list[dict]:
    """Every arm of a finished job."""
    res = []
    for arm in job["arms"]:
        p = root / "dumps" / job["id"] / f"{arm['name']}.jsonl.gz"
        if not p.exists():
            p = p.with_suffix("")
            if not p.exists():
                continue
        meta = dict(tag=f"{job['id']}__{arm['name']}", job=job["id"], model=job["model"],
                    precision=job.get("precision") or "", set=job["set"], lang=job["lang"],
                    kind=job["kind"], arm=arm["name"], shard=job["shard"],
                    arm_K=arm.get("K", arm.get("beams", 1)), arm_T=arm.get("T", arm.get("temperature")),
                    arm_steps=arm.get("steps"), arm_mode=arm.get("mode"))
        km = min(k_main, arm.get("K", arm.get("beams", 1)))
        res.append(analyze_dump(p, root / "analysis", meta, km))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--job", default=None, help="one job id; default: every finished job")
    ap.add_argument("--k_main", type=int, default=32)
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)
    with open(root / "plan.json", encoding="utf-8") as f:
        plan = {j["id"]: j for j in json.load(f)}
    jobs = [plan[args.job]] if args.job else [plan[p.stem] for p in (root / "state" / "done").glob("*.json")
                                                 if p.stem in plan]
    for job in jobs:
        if not args.redo and all((root / "analysis" / f"{job['id']}__{a['name']}.parquet").exists()
                                 for a in job["arms"]):
            continue
        for r in analyze_job(root, job, args.k_main):
            print(r, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
