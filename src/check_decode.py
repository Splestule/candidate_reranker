#!/usr/bin/env python3
"""Flat sampling must be bit-identical to the decoder before branching was added.

The tree parameters default to off, so the old code path has to survive untouched: same
seed, same masks, same text. Everything measured before the tree work was produced by the
old path, so a mismatch means those numbers stopped being comparable.

No dataset is needed. What is under test is the order of the random draws and the update,
not the audio, so a fixed pseudo-random encoder input exercises it exactly as speech would.
The reference decoder is imported as decode_old, which the notebook writes from git.
"""

from __future__ import annotations


def fake_condition(wf, seconds: float = 5.0, seed: int = 0):
    import numpy as np

    import wf_model
    rng = np.random.default_rng(seed)
    audio = (rng.standard_normal(int(16000 * seconds)) * 0.05).astype("float32")
    return wf_model.encode_audio(wf, audio)


def compare(wf, old, new, n_trials: int = 6, k: int = 16, n_steps: int = 4) -> int:
    """Returns the number of mismatching trials; prints one diff for the first."""
    bad = 0
    for t in range(n_trials):
        cond = fake_condition(wf, seconds=3.0 + t, seed=t)
        a = old.pdd_decode(wf, cond, n_candidates=k, n_steps=n_steps, seed=1000 + t)
        b = new.pdd_decode(wf, cond, n_candidates=k, n_steps=n_steps, seed=1000 + t)
        ta = [c.text for c in a.candidates]
        tb = [c.text for c in b.candidates]
        ok = ta == tb
        bad += not ok
        print(f"  trial {t}  {'ok' if ok else 'MISMATCH'}   unique {a.n_unique} -> {b.n_unique}")
        if not ok and bad == 1:
            for i, (x, y) in enumerate(zip(ta, tb)):
                if x != y:
                    print(f"      candidate {i}\n        old: {x[:100]}\n        new: {y[:100]}")
                    break
    print(f"\n{n_trials - bad}/{n_trials} identical"
          + ("  -- flat sampling is unchanged" if not bad else "  -- DO NOT RUN THE ABLATION"))
    return bad


def tree_sanity(wf, new, k: int = 16) -> int:
    """Every arm must decode, branch as told, size itself, and not fall apart.

    The previous run printed all of this and passed anyway, because nothing asserted. Five of
    nine arms were broken: adapt never changed width, and uncertainty masking pinned the hard
    positions to p = 1 so they never settled and WER came out four times worse. Each check
    below is one of those failures turned into a condition.
    """
    cond = fake_condition(wf, seconds=6.0, seed=99)
    q = max(k // 4, 1)
    low = [1.0, 0.5, 0.35, 0.25]
    ad = dict(base=max(k * 2 // 3, 4), u0=0.021, gamma=1.5, k_min=max(k // 6, 2), k_max=k)
    arms = [
        ("flat", dict(), None),
        ("tree-early", dict(branch_schedule=[1, q, k, k]), [1, q, k, k]),
        ("tree-late", dict(branch_schedule=[1, 1, q, k]), [1, 1, q, k]),
        ("flat-sched", dict(mask_ratio_schedule=low), None),
        ("cond", dict(mask_ratio_schedule=low, mask_mode="uncertain"), None),
        ("cond-tree", dict(mask_ratio_schedule=low, mask_mode="uncertain",
                           branch_schedule=[1, q, k, k]), [1, q, k, k]),
        ("adapt", dict(adaptive=ad), None),
        ("adapt-tree", dict(branch_schedule=[1, q, k, k], adaptive=ad), None),
    ]
    print(f"\n{'arm':<13}{'K':>5}{'unique':>8}{'mean len':>10}{'widths':>20}{'uncert.':>10}")
    res, bad = {}, []
    for name, kw, want in arms:
        r = new.pdd_decode(wf, cond, n_candidates=k, n_steps=4, seed=7, **kw)
        res[name] = r
        lens = [c.n_tokens for c in r.candidates]
        mean_len = sum(lens) / max(len(lens), 1)
        u = "" if r.uncertainty is None else f"{r.uncertainty:.4f}"
        print(f"{name:<13}{r.n_candidates_used:>5}{r.n_unique:>8}{mean_len:>10.1f}"
              f"{str(r.branch_widths):>20}{u:>10}")
        if want is not None and r.branch_widths != want:
            bad.append(f"{name}: branched {r.branch_widths}, asked for {want}")

    base_len = sum(c.n_tokens for c in res["flat"].candidates) / k
    for name in ("cond", "cond-tree", "flat-sched"):
        lens = [c.n_tokens for c in res[name].candidates]
        m = sum(lens) / max(len(lens), 1)
        if not 0.5 * base_len <= m <= 2.0 * base_len:   # divergence shows up as length first
            bad.append(f"{name}: mean length {m:.0f} against flat {base_len:.0f}, it is diverging")
    if res["adapt"].n_candidates_used == k:
        bad.append(f"adapt returned the full {k}: the width never adapted (u0 miscalibrated, "
                   f"or rows are not allowed to shrink)")
    if res["adapt"].uncertainty is None:
        bad.append("adapt reported no uncertainty: the probe step never ran")

    for line in bad:
        print(f"  FAIL  {line}")
    print("every arm behaves" if not bad else f"\n{len(bad)} arms misbehaving")
    return len(bad)


def main() -> int:
    import importlib
    import sys

    from campaign.families import Whisfusion
    new = importlib.import_module("decode")
    try:
        old = importlib.import_module("decode_old")
    except ImportError:
        print("decode_old not importable; the notebook writes it from git at build time")
        return 2
    wf = Whisfusion({}).wf
    bad = compare(wf, old, new)
    bad += tree_sanity(wf, new)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
