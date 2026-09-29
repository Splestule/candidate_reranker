#!/usr/bin/env python3
"""Are the per-word confidences ROVER votes with actually calibrated?

ROVER mixes vote share with word confidence (alpha). If the confidences are miscalibrated,
no value of alpha helps: the signal being mixed in is wrong, not just weighted wrongly.
This bins the backbone candidate's words by their reported confidence and reports how often
the word is the reference word at that position -- a reliability diagram in text.

    PYTHONPATH=src python tools/calib.py results/campaign-2026-09-20 --model whisfusion
"""
from __future__ import annotations
import argparse, glob, gzip, json, sys
from pathlib import Path
from collections import defaultdict

BINS = [0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 0.98, 0.995, 1.0001]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main"); ap.add_argument("--max_utts", type=int, default=1200)
    a = ap.parse_args()
    sys.path.insert(0, "src")
    import compose
    from scorers import normalize
    from rapidfuzz.distance import Levenshtein

    hit = defaultdict(int); tot = defaultdict(int); conf_sum = defaultdict(float)
    n_utt = 0
    for j in sorted(glob.glob(f"{a.root}/dumps/{a.model}__*")):
        p = Path(j) / f"{a.arm}.jsonl.gz"
        if not p.exists():
            continue
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                cs = row["candidates"]
                if not all("word_conf" in c for c in cs):
                    continue
                words = [normalize(c["text"]).split() for c in cs]
                ok = [i for i, (w, c) in enumerate(zip(words, cs))
                      if len(w) == len(c["word_conf"]) and w]
                if not ok:
                    continue
                bb = ok[compose.central_index([words[i] for i in ok])]
                w, cf = words[bb], cs[bb]["word_conf"]
                ref = normalize(row["reference"]).split()
                correct = [False] * len(w)
                for tag, i1, i2, j1, j2 in Levenshtein.opcodes(w, ref):
                    if tag == "equal":
                        for d in range(i2 - i1):
                            correct[i1 + d] = True
                for x, c in zip(w, cf):
                    b = next(k for k in range(len(BINS) - 1) if BINS[k] <= c < BINS[k + 1])
                    tot[b] += 1; conf_sum[b] += c
                for i, c in enumerate(cf):
                    if correct[i]:
                        b = next(k for k in range(len(BINS) - 1) if BINS[k] <= c < BINS[k + 1])
                        hit[b] += 1
                n_utt += 1
                if n_utt >= a.max_utts:
                    break
        if n_utt >= a.max_utts:
            break

    print(f"{n_utt} utterances, backbone candidate only\n")
    print(f"{'conf bin':<16}{'n words':>10}{'mean conf':>11}{'actually right':>16}{'gap':>8}")
    print("-" * 61)
    T = H = 0; se = 0.0
    for b in sorted(tot):
        mc = conf_sum[b] / tot[b]; acc = hit[b] / tot[b]
        print(f"{f'{BINS[b]:.3f}-{BINS[b+1]:.3f}':<16}{tot[b]:>10}{mc:>11.3f}"
              f"{acc:>15.3f}{mc - acc:>+8.3f}")
        T += tot[b]; H += hit[b]; se += abs(mc - acc) * tot[b]
    if T:
        print("-" * 61)
        print(f"{'ALL':<16}{T:>10}{conf_sum and sum(conf_sum.values())/T:>11.3f}{H/T:>15.3f}"
              f"{sum(conf_sum.values())/T - H/T:>+8.3f}")
        print(f"\nECE (expected calibration error) = {se/T:.3f}")
        print("positive gap = overconfident: the model claims more certainty than it earns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
