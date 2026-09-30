#!/usr/bin/env python3
"""The cost/quality table of the paper: upstream Whisfusion against the final pipeline, over K,
on flat and on tree-early decoding, with measured decode times.

Input is tools/cand_audio.py output over a treek campaign (arms flat-k{K}, tree-early-k{K}).
Per K, everything learned (ROVER alpha/eps, the final pipeline, the iROVER-style classifier)
is fitted on the FLAT candidates of the training sets and applied unchanged to both decodes of
the held-out sets; set-level cross-validation as in tools/final_compare.py. WER is reported
in the legacy normalisation and in Whisper's English normaliser.

    python3 tools/treek_eval.py --cand results/cand_audio_treek.pkl | tee results/treek_eval.txt
"""

from __future__ import annotations

import argparse
import pickle
import random
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np
from rapidfuzz.distance import Levenshtein

import crf_rover as F
import slot_lr as L
import slot_eval as S
import final_compare as FC
import k_curve as KC

UP = "Whisfusion upstream (mean conf)"
FIN = "final"
IRO = "iROVER-style"


def whisper_norm():
    try:
        from campaign.analysis import WhisperNorm
        w = WhisperNorm()
        return w if w.ok else None
    except Exception:
        return None


def evaluate(recs, k, a):
    flat = {(r["set"], r["id"]): r for r in recs if r["arm"] == f"flat-k{k}"}
    tree = {(r["set"], r["id"]): r for r in recs if r["arm"] == f"tree-early-k{k}"}
    B = {"flat": {}, "tree-early": {}}
    for name, src in (("flat", flat), ("tree-early", tree)):
        for key, r in src.items():
            b = KC.build(r, k)
            if b is not None:
                b.update(ref_text=r.get("ref_text", " ".join(r["ref"])), lang=r.get("lang", "en"),
                         decode_s=r.get("decode_s"))
                B[name][key] = b
    keys = sorted(set(B["flat"]) & set(B["tree-early"]))
    akey = "aslots_w2"
    hy = {name: {} for name in B}
    for fold in FC.FOLDS:
        pool = [B["flat"][kk] for kk in B["flat"] if kk[0] not in fold]
        random.Random(a.seed).shuffle(pool)
        n_lm = min(a.lm_utts, len(pool) // 3)
        lm = F.Bigram([d["ref"] for d in pool[:n_lm]])
        tr = pool[n_lm:]
        if not tr:
            continue
        al, ep, _ = min(((al, e, sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, e, S.POWER)
                                                  for s in d["slots"]], d["ref"]) for d in tr))
                         for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])
        fin = FC.fit_arm(tr, lm, akey, a)
        boost = KC.fit_boost(tr, lm, akey)
        for name in B:
            ev = [B[name][kk] for kk in keys if kk[0] in fold]
            if not ev:
                continue
            bh = KC.apply_boost(ev, boost, akey, lm)
            for d, hb in zip(ev, bh):
                tot = float(d["n_cand"])
                hy[name][(d["set"], d["id"])] = {
                    UP: d["toks"][FC.argmax(d["conf"])],
                    "MBR": d["toks"][FC.argmax(d["mbr"])],
                    "ROVER tuned": [F.rover_pick(s, tot, al, ep, S.POWER) for s in d["slots"]],
                    FIN: FC.apply_arm(d, fin, akey, lm),
                    IRO: hb,
                    "candidate oracle": min(d["toks"], key=lambda t: Levenshtein.distance(d["ref"], t)),
                }
    keys = [kk for kk in keys if kk in hy["flat"] and kk in hy["tree-early"]]
    return keys, B, hy


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    ap.add_argument("--ks", default="4,8,15,32")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lm_utts", type=int, default=1200)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    a = ap.parse_args()
    recs = pickle.loads(Path(a.cand).read_bytes())
    ks = [int(x) for x in a.ks.split(",")]
    wn = whisper_norm()
    res = {k: evaluate(recs, k, a) for k in ks}
    common = set.intersection(*[set(v[0]) for v in res.values()])
    common = sorted(kk for kk in common if any(kk[0] in f for f in FC.FOLDS))
    print(f"{len(common)} held-out utterances on {len({kk[0] for kk in common})} sets, present "
          f"in every arm; Whisper normaliser {'on' if wn else 'NOT available'}\n")

    rows = {}
    for k in ks:
        keys, B, hy = res[k]
        for dec in ("flat", "tree-early"):
            dsec = [B[dec][kk]["decode_s"] for kk in common if B[dec][kk]["decode_s"] is not None]
            for m in hy[dec][common[0]]:
                e = np.array([F.edits_of(hy[dec][kk][m], B[dec][kk]["ref"]) for kk in common], float)
                rl = np.array([len(B[dec][kk]["ref"]) for kk in common], float)
                ew = rw = None
                if wn:
                    ew, rw = [], []
                    for kk in common:
                        d = B[dec][kk]
                        r = wn(d["ref_text"], d["lang"])
                        h = wn(" ".join(w for w in hy[dec][kk][m] if w != S.EPS), d["lang"])
                        ew.append(Levenshtein.distance(r, h)); rw.append(len(r))
                    ew, rw = np.array(ew, float), np.array(rw, float)
                rows[(k, dec, m)] = (e, rl, ew, rw, float(np.mean(dsec)) if dsec else float("nan"))

    base = rows[(15, "flat", UP)] if 15 in ks else rows[(ks[0], "flat", UP)]
    print(f"{'K':>3} {'decode':<11}{'method':<34}{'WER':>7}{'WER wn':>8}{'s/utt':>7}{'cost':>6}")
    for (k, dec, m), (e, rl, ew, rw, sec) in rows.items():
        wv = f"{100 * ew.sum() / rw.sum():8.2f}" if ew is not None else f"{'-':>8}"
        print(f"{k:>3} {dec:<11}{m:<34}{100 * e.sum() / rl.sum():7.2f}{wv}{sec:7.3f}{sec / base[4]:6.2f}")

    print(f"\npaired bootstrap against upstream Whisfusion (flat K=15, mean conf); positive = better")
    for (k, dec, m), (e, rl, ew, rw, sec) in rows.items():
        if m in (FIN, IRO, "ROVER tuned", "MBR"):
            o, lo, hi = S.bootstrap(base[0], e, rl)
            line = f"  K={k:<3}{dec:<11}{m:<22}{o:+6.2f} [{lo:+.2f}, {hi:+.2f}]"
            if ew is not None:
                o, lo, hi = S.bootstrap(base[2], ew, rw)
                line += f"   whisper norm {o:+6.2f} [{lo:+.2f}, {hi:+.2f}]"
            print(line)

    print("\ntree-early minus flat, same K, same pipeline (positive = tree-early worse)")
    for k in ks:
        for m in (FIN, "ROVER tuned"):
            f, t = rows[(k, "flat", m)], rows[(k, "tree-early", m)]
            o, lo, hi = S.bootstrap(t[0], f[0], f[1])
            print(f"  K={k:<3}{m:<14}{o:+.2f} [{lo:+.2f}, {hi:+.2f}]   decode {t[4] / f[4]:.2f}x of flat")

    print("\nfinal vs iROVER-style, same K and decode (positive = final better)")
    for k in ks:
        for dec in ("flat", "tree-early"):
            o, lo, hi = S.bootstrap(rows[(k, dec, IRO)][0], rows[(k, dec, FIN)][0], rows[(k, dec, FIN)][1])
            print(f"  K={k:<3}{dec:<11}{o:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
