#!/usr/bin/env python3
"""Is the explorer an error detector? CPU-only check on the candidates an explorer run decoded.

For every mixed arm (anchor + explorer candidates) the confusion network is built over all K
candidates as in evaluation, and each slot is read twice: the anchor block's majority word a and
the explorer block's majority word e. Against the reference word r of the slot:

  q   correction rate    P(e == r | a != r)
  f   false-alarm rate   P(e != a | a == r)

Taking the explorer's word wherever it disagrees changes the slot errors by
f * #right - q' * #wrong (q' counting only disagreeing corrections); it helps only if
q / f > (1 - p) / p, p the anchor block's slot error rate. The script also sweeps a threshold
on the explorer's confidence for its word (best rule, chosen on the same data, so an optimistic
bound on what any switch rule could get) and reports how often the explorer fills a hole, a
slot whose reference word no anchor candidate has.

Control: the anchor-only arm at the same K, its last n candidates relabelled as the "explorer".
That is what a block of plain anchor samples does in the same position; an explorer is worth
something only where it beats this row.

    python3 tools/explorer_qf.py run1=results/explorer/cand_audio.pkl run2=results/explorer2/cand_audio.pkl
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np

import compose
import decompose as D

EPS = compose.EPS


def pick(slot):
    """Majority word of a block; ties broken by summed confidence. None if the block cast no vote."""
    best = max(slot.items(), key=lambda kv: (kv[1][0], kv[1][1]))
    return best[0] if best[1][0] > 0 else None


def read_utt(r, k, n_x, relabel):
    raw = r["cands"][:k]
    ok = [c for c in raw if c["conf"] is not None]
    if len(ok) < 2:
        return None
    if relabel:
        src = ["anchor"] * (len(raw) - n_x) + ["explorer"] * n_x
        src = [s for s, c in zip(src, raw) if c["conf"] is not None]
    else:
        src = [c.get("source", "anchor") for c in ok]
    if "explorer" not in src or "anchor" not in src:
        return None
    cands = [c["words"] for c in ok]
    confs = [c["conf"] for c in ok]
    bb = compose.central_index(cands)
    wa = [1.0 if s == "anchor" else 0.0 for s in src]
    wx = [1.0 - w for w in wa]
    A = compose.confusion_network(cands, bb, confs, wa)
    X = compose.confusion_network(cands, bb, confs, wx)
    ref = D.reference_by_slot(cands, bb, r["ref"])
    if not (len(A) == len(X) == len(ref)):
        return None
    nx = sum(wx)
    out = []
    for sa, sx, rw in zip(A, X, ref):
        a, e = pick(sa), pick(sx)
        if a is None or e is None:
            continue
        ev, ec = sx[e]
        # explorer's confidence in its own word: vote share times mean word confidence
        score = (ev / nx) * (ec / ev if ev > 0 else 0.0)
        in_anchor = rw in sa and sa[rw][0] > 0
        out.append((a == rw, e == rw, e != a, score, in_anchor, rw in sx and sx[rw][0] > 0))
    return out, len(r["ref"])


def auc(pos, neg):
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    s = np.concatenate([pos, neg])
    ranks = s.argsort().argsort() + 1.0
    return (ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def report(name, rows, ref_words):
    R = np.array([x[:3] + (x[4], x[5]) for x in rows], bool)
    sc = np.array([x[3] for x in rows], float)
    a_ok, e_ok, dis, in_a, in_x = R.T
    n_ok, n_bad = a_ok.sum(), (~a_ok).sum()
    p = n_bad / len(rows)
    q = (e_ok & ~a_ok).sum() / max(n_bad, 1)
    f = (dis & a_ok).sum() / max(n_ok, 1)
    corr, dam = dis & e_ok, dis & a_ok
    # best threshold on the explorer's confidence among disagreeing slots (in-sample bound)
    d_idx = np.where(dis)[0]
    order = d_idx[np.argsort(-sc[d_idx])]
    gain = np.cumsum(corr[order].astype(int) - dam[order].astype(int))
    best = max(0, gain.max()) if len(gain) else 0
    holes = ~in_a
    fill = (holes & in_x).sum() / max(holes.sum(), 1)
    print(f"  {name:<34} p {100 * p:5.1f}  q {100 * q:5.1f}  f {100 * f:5.1f}  "
          f"q/f {q / max(f, 1e-9):5.2f} (need {(1 - p) / max(p, 1e-9):4.2f})  "
          f"always-switch {100 * (dam.sum() - corr.sum()) / ref_words:+6.2f}  "
          f"best-rule {-100 * best / ref_words:+6.2f}  "
          f"AUC {auc(sc[corr], sc[dam]):.3f}  hole-fill {100 * fill:4.1f}% of {holes.sum()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="name=path/to/cand_audio.pkl")
    ap.add_argument("--test_shard", type=int, default=1)
    ap.add_argument("--all_shards", action="store_true")
    a = ap.parse_args()
    print("slot-level, WER points relative to the anchor block's majority (negative = explorer helps)\n")
    for spec in a.runs:
        name, path = spec.split("=", 1)
        recs = pickle.loads(Path(path).read_bytes())
        recs = [r for r in recs if a.all_shards or r.get("shard") == a.test_shard]
        arms = sorted({r["arm"] for r in recs}, key=lambda x: (int(x.rsplit("-k", 1)[1]), x))
        print(f"{name}: {len(recs)} records, arms {arms}")
        for arm in arms:
            if arm.startswith("anchor"):
                continue
            k = int(arm.rsplit("-k", 1)[1])
            sub = [r for r in recs if r["arm"] == arm]
            n_x = max(sum(c.get("source") == "explorer" for c in r["cands"][:k]) for r in sub)
            for label, src_arm, relabel in ((arm, arm, False),
                                            (f"  control anchor-k{k} last {n_x}", f"anchor-k{k}", True)):
                rows, words = [], 0
                for r in recs:
                    if r["arm"] != src_arm:
                        continue
                    got = read_utt(r, k, n_x, relabel)
                    if got:
                        rows += got[0]
                        words += got[1]
                if rows:
                    report(label, rows, words)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
