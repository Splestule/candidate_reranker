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


def tree_sanity(wf, new, k: int = 16) -> None:
    """The tree arms must at least decode, branch when told to, and size themselves."""
    cond = fake_condition(wf, seconds=6.0, seed=99)
    q = max(k // 4, 1)
    arms = [
        ("flat", dict()),
        ("tree-early", dict(branch_schedule=[1, q, k, k])),
        ("tree-late", dict(branch_schedule=[1, 1, q, k])),
        ("cond", dict(mask_mode="uncertain")),
        ("adapt", dict(adaptive=dict(base=k, u0=0.15, gamma=1.0, k_min=2, k_max=k))),
        ("adapt-tree", dict(branch_schedule=[1, q, k, k],
                            adaptive=dict(base=k, u0=0.15, gamma=1.0, k_min=2, k_max=k))),
    ]
    print(f"\n{'arm':<14}{'K used':>8}{'unique':>8}{'widths':>22}{'uncertainty':>13}")
    for name, kw in arms:
        r = new.pdd_decode(wf, cond, n_candidates=k, n_steps=4, seed=7, **kw)
        u = "" if r.uncertainty is None else f"{r.uncertainty:.4f}"
        print(f"{name:<14}{r.n_candidates_used:>8}{r.n_unique:>8}"
              f"{str(r.branch_widths):>22}{u:>13}")


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
    tree_sanity(wf, new)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
