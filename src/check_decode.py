#!/usr/bin/env python3
"""Flat sampling must be bit-identical to the decoder before branching was added.

The tree parameters default to off, so the old code path has to survive untouched: same
seed, same masks, same text. Everything measured before the tree work was produced by the
old path, so a mismatch means those numbers stopped being comparable.

The probe has to be speech. Pseudo-random audio decodes to a single token, which makes
every assertion here trivially true: "6/6 identical" and "every arm behaves" were, twice,
statements about an empty output. Pass a manifest and the checks run on real utterances;
without one they fall back to noise and say, loudly, that they tested nothing.
"""

from __future__ import annotations


def fake_condition(wf, seconds: float = 5.0, seed: int = 0):
    import numpy as np

    import wf_model
    rng = np.random.default_rng(seed)
    audio = (rng.standard_normal(int(16000 * seconds)) * 0.05).astype("float32")
    return wf_model.encode_audio(wf, audio)


def real_conditions(wf, manifest: str, n: int = 6) -> list[tuple[str, object]]:
    """Encoder states for the first n utterances of a prepared manifest."""
    import data as dataio
    import wf_model

    out = []
    for u in dataio.iter_manifest(manifest):
        out.append((u.id, wf_model.encode_audio(wf, dataio.load_audio(u.audio_path))))
        if len(out) >= n:
            break
    return out


def probe_conditions(wf, manifest: str | None, n: int = 6) -> tuple[list[tuple[str, object]], bool]:
    """(labelled conditions, real). Falls back to noise if the manifest is missing."""
    import os

    if manifest and os.path.exists(manifest):
        conds = real_conditions(wf, manifest, n)
        if conds:
            print(f"probe: {len(conds)} real utterances from {os.path.basename(manifest)}")
            return conds, True
    print("probe: pseudo-random audio -- no manifest given")
    return [(f"noise-{t}", fake_condition(wf, seconds=3.0 + t, seed=t)) for t in range(n)], False


def compare(wf, old, new, conds, k: int = 16, n_steps: int = 4) -> int:
    """Returns the number of mismatching trials; prints one diff for the first."""
    bad = 0
    for t, (label, cond) in enumerate(conds):
        a = old.pdd_decode(wf, cond, n_candidates=k, n_steps=n_steps, seed=1000 + t)
        b = new.pdd_decode(wf, cond, n_candidates=k, n_steps=n_steps, seed=1000 + t)
        ta = [c.text for c in a.candidates]
        tb = [c.text for c in b.candidates]
        ok = ta == tb
        bad += not ok
        mean_len = sum(c.n_tokens for c in a.candidates) / max(k, 1)
        print(f"  {label:<26}{'ok' if ok else 'MISMATCH'}   unique {a.n_unique} -> {b.n_unique}"
              f"   mean len {mean_len:.0f}")
        if not ok and bad == 1:
            for i, (x, y) in enumerate(zip(ta, tb)):
                if x != y:
                    print(f"      candidate {i}\n        old: {x[:100]}\n        new: {y[:100]}")
                    break
    n = len(conds)
    print(f"\n{n - bad}/{n} identical"
          + ("  -- flat sampling is unchanged" if not bad else "  -- DO NOT RUN THE ABLATION"))
    return bad


def tree_sanity(wf, new, cond, k: int = 16) -> int:
    """Every arm must decode, branch as told, size itself, and not fall apart.

    The first tree run printed all of this and passed anyway, because nothing asserted. Five
    of nine arms were broken: adapt never changed width, and uncertainty masking pinned the
    hard positions to p = 1 so they never settled and WER came out four times worse. Each
    check below is one of those failures turned into a condition.
    """
    probe = new.pdd_decode(wf, cond, n_candidates=k, n_steps=4, seed=7)
    probe_len = sum(c.n_tokens for c in probe.candidates) / max(k, 1)
    vacuous = probe.n_unique <= 1 and probe_len <= 2.0
    if vacuous:
        print("\n  !! VACUOUS: the probe decodes to nothing (unique "
              f"{probe.n_unique}, mean length {probe_len:.1f}).")
        print("  !! Nothing below is actually being tested. Give the check a manifest.\n")

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
    if res["flat"].n_unique <= 1:
        bad.append("flat gave one distinct candidate: there is no diversity to branch on")
    if res["adapt"].n_candidates_used == k:
        bad.append(f"adapt returned the full {k}: the width never adapted (u0 miscalibrated, "
                   f"or rows are not allowed to shrink)")
    if res["adapt"].uncertainty is None:
        bad.append("adapt reported no uncertainty: the probe step never ran")

    for line in bad:
        print(f"  FAIL  {line}")
    if vacuous:
        print("checks did not run: the probe was degenerate")
        return 0                      # do not block the run, but never claim a pass either
    print("every arm behaves" if not bad else f"\n{len(bad)} arms misbehaving")
    return len(bad)


def main(manifest: str | None = None, n_utts: int = 6, k: int = 16) -> int:
    import importlib

    from campaign.families import Whisfusion
    new = importlib.import_module("decode")
    try:
        old = importlib.import_module("decode_old")
    except ImportError:
        print("decode_old not importable; the notebook writes it from git at build time")
        return 2
    wf = Whisfusion({}).wf
    conds, real = probe_conditions(wf, manifest, n_utts)
    bad = compare(wf, old, new, conds, k=k)
    bad += tree_sanity(wf, new, conds[-1][1], k=k)
    if not real:
        print("\nthis was noise, not speech: a pass here means nothing")
    return 1 if bad else 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=None, help="prepared <set>.jsonl to probe with")
    ap.add_argument("--n_utts", type=int, default=6)
    ap.add_argument("--k", type=int, default=16)
    a = ap.parse_args()
    raise SystemExit(main(a.manifest, a.n_utts, a.k))
