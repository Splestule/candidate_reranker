#!/usr/bin/env python3
"""Re-measure the oracle's controls from the dumps, with the clamping made explicit.

The campaign stores e_control as min(shuffled-network oracle, best whole candidate). That
clamp is not cosmetic: on a network whose alternatives have been replaced by noise, the
oracle path can be WORSE than any single candidate, because the noisy arcs crowd out the
real word, and the clamp then silently substitutes the candidate oracle. The published
signal-to-luck ratio depends on which convention is used, so this prints both, next to a
second and stricter control.

  lexical    alternatives after the first replaced by corpus words (what the campaign does)
  permuted   the alternative SETS moved between slots of the same utterance. The words, the
             counts and the confidences are all real and all the decoder's own; only the
             correspondence between a slot and its alternatives is destroyed.

A control system is allowed the same fallback the real one has -- it can always output its
best whole candidate -- so the clamped column is the fair comparison. The unclamped column
is reported so nobody has to take that on trust.

    PYTHONPATH=src python3 tools/control_check.py --model whisfusion --k 32 --max_utts 200
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import random
import sys
import zlib
from pathlib import Path

sys.path.insert(0, "src")

import compose
from rapidfuzz.distance import Levenshtein

import campaign.analysis as A

EPS = compose.EPS


def permuted(slots, rng):
    alts = []
    for sl in slots:
        words = [w for w in sl if w != EPS]
        alts.append([(w, list(sl[w])) for w in words[1:]])
    if len(alts) > 1:
        order = list(range(len(alts)))
        for _ in range(8):
            rng.shuffle(order)
            if all(i != j for i, j in enumerate(order)):
                break
        alts = [alts[j] for j in order]
    out = []
    for sl, extra in zip(slots, alts):
        words = [w for w in sl if w != EPS]
        new = {}
        if words:
            new[words[0]] = list(sl[words[0]])
        if EPS in sl:
            new[EPS] = list(sl[EPS])
        for w, v in extra:
            new.setdefault(w, list(v))
        out.append(new)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/campaign-2026-09-20/dumps")
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max_utts", type=int, default=200, help="per set")
    ap.add_argument("--json", default="", help="append the pooled row to this JSON file")
    a = ap.parse_args()

    # The dump layout puts the SET in the directory name and the ARM in the file name for
    # the baselines (beam.jsonl.gz, sample.jsonl.gz beside each other), while whisfusion and
    # drax carry the arm in both. Match on the file, so one flag works for every model.
    dirs = sorted(glob.glob(f"{a.root}/{a.model}__*"))
    if not dirs:
        print(f"no dumps under {a.root} for {a.model}")
        return 2
    per = {}
    for d in dirs:
        s = Path(d).name.split("__")[1]
        rows = per.setdefault(s, [])
        for f in sorted(glob.glob(f"{d}/{a.arm}.jsonl.gz")):
            if len(rows) >= a.max_utts:
                break
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    rows.append(json.loads(line))
                    if len(rows) >= a.max_utts:
                        break

    per = {k: v for k, v in per.items() if v}
    if not per:
        print(f"no {a.arm}.jsonl.gz under {a.root} for {a.model}")
        return 2
    print(f"{'set':<18}{'n':>5}{'ROVER':>8}{'oracle':>8}{'cand.or':>9}"
          f"{'lex':>8}{'lex*':>8}{'perm':>8}{'perm*':>8}{'s/luck':>8}{'s/luck*':>9}")
    print("-" * 99)
    tot = {k: 0.0 for k in ("R", "rov", "orac", "cand", "lex", "lexc", "perm", "permc")}
    n_tot = 0
    for s in sorted(per):
        acc = {k: 0.0 for k in tot}
        n = 0
        for row in per[s]:
            ref = A.S.normalize(row["reference"]).split()
            cands, confs, _ = A.prepare(row)
            k = min(a.k, len(cands))
            if k < 2 or not ref:
                continue
            sub, sub_c = cands[:k], (confs[:k] if confs else None)
            ed = [Levenshtein.distance(ref, c) for c in sub]
            lens = [len(c) for c in sub]
            Lm = [[Levenshtein.distance(sub[i], sub[j]) for j in range(k)] for i in range(k)]
            mbr = [-sum(Lm[i][j] / max(lens[j], 1) for j in range(k) if j != i) / (k - 1)
                   for i in range(k)]
            p_mbr = max(range(k), key=lambda i: mbr[i])
            slots = compose.confusion_network(sub, p_mbr, sub_c, None)
            rng = random.Random(zlib.crc32(row["id"].encode("utf-8")))
            cand = min(ed)
            acc["R"] += len(ref)
            acc["rov"] += Levenshtein.distance(
                ref, compose.rover(slots, float(k), A.ROVER_DEFAULT["alpha"],
                                   A.ROVER_DEFAULT["eps"]))
            acc["orac"] += min(compose.oracle_path(slots, ref), cand)
            acc["cand"] += cand
            pool = [w for c in sub for w in c] or ["the"]
            lx = compose.oracle_path(compose.shuffled_control(slots, pool, rng), ref)
            pm = compose.oracle_path(permuted(slots, rng), ref)
            acc["lex"] += lx
            acc["lexc"] += min(lx, cand)
            acc["perm"] += pm
            acc["permc"] += min(pm, cand)
            n += 1
        if not n:
            continue
        for k_ in tot:
            tot[k_] += acc[k_]
        n_tot += n
        w = lambda k_: 100.0 * acc[k_] / acc["R"]
        gap = w("rov") - w("orac")
        print(f"{s:<18}{n:>5}{w('rov'):>8.2f}{w('orac'):>8.2f}{w('cand'):>9.2f}"
              f"{w('lex'):>8.2f}{w('lexc'):>8.2f}{w('perm'):>8.2f}{w('permc'):>8.2f}"
              f"{gap / max(w('rov') - w('lexc'), 1e-9):>8.1f}"
              f"{gap / max(w('rov') - w('permc'), 1e-9):>9.1f}")
    print("-" * 99)
    w = lambda k_: 100.0 * tot[k_] / tot["R"]
    gap = w("rov") - w("orac")
    print(f"{'POOLED':<18}{n_tot:>5}{w('rov'):>8.2f}{w('orac'):>8.2f}{w('cand'):>9.2f}"
          f"{w('lex'):>8.2f}{w('lexc'):>8.2f}{w('perm'):>8.2f}{w('permc'):>8.2f}"
          f"{gap / max(w('rov') - w('lexc'), 1e-9):>8.1f}"
          f"{gap / max(w('rov') - w('permc'), 1e-9):>9.1f}")
    if a.json:
        f = Path(a.json)
        rows = json.loads(f.read_text()) if f.exists() else []
        rows = [r for r in rows if (r["model"], r["arm"], r["k"]) != (a.model, a.arm, a.k)]
        rows.append(dict(model=a.model, arm=a.arm, k=a.k, n=n_tot,
                         rover=w("rov"), oracle=w("orac"), cand=w("cand"),
                         lex=w("lex"), lex_clamped=w("lexc"),
                         perm=w("perm"), perm_clamped=w("permc")))
        f.write_text(json.dumps(rows, indent=1))
        print(f"\npooled row -> {a.json}")

    print("\n* = clamped to the best whole candidate, the fallback any system has.")
    print("Unclamped, a control oracle can be worse than ROVER: the noise arcs crowd the")
    print("real word out of its own slot. That is a fact about the control, not about the")
    print("network, and it is why the clamp has to be stated rather than assumed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
