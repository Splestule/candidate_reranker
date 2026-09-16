"""Paired bootstrap over utterances, for comparing two systems measured on the same data."""

from __future__ import annotations

import numpy as np


def paired_bootstrap(edits_a: list[int], edits_b: list[int], ref_len: list[int],
                     n_boot: int = 4000, seed: int = 0) -> dict:
    """Confidence interval for corpus WER(a) - WER(b). Positive means b is better.

    Both systems are scored on the same resampled utterances, so the interval covers the
    difference between them and not the spread of the test set, which is much larger.
    """
    a = np.asarray(edits_a, dtype=np.float64)
    b = np.asarray(edits_b, dtype=np.float64)
    r = np.asarray(ref_len, dtype=np.float64)
    n = len(r)
    if n == 0 or r.sum() == 0:
        return {}

    observed = 100.0 * (a.sum() - b.sum()) / r.sum()

    rng = np.random.default_rng(seed)
    deltas = np.empty(n_boot, dtype=np.float64)
    step = 500
    for start in range(0, n_boot, step):
        idx = rng.integers(0, n, size=(min(step, n_boot - start), n))
        sr = r[idx].sum(axis=1)
        deltas[start:start + idx.shape[0]] = 100.0 * (a[idx].sum(axis=1) - b[idx].sum(axis=1)) / sr

    return {
        "delta": observed,
        "ci_low": float(np.percentile(deltas, 2.5)),
        "ci_high": float(np.percentile(deltas, 97.5)),
        "p_no_gain": float((deltas <= 0).mean()),
        "n_better": int((b < a).sum()),
        "n_worse": int((b > a).sum()),
        "n_tied": int((a == b).sum()),
        "n_boot": n_boot,
    }


def format_row(label: str, s: dict) -> str:
    if not s:
        return f"{label:<34} (empty)"
    return (f"{label:<34}{s['delta']:+7.2f}  95% CI [{s['ci_low']:+.2f}, {s['ci_high']:+.2f}]"
            f"   better {s['n_better']} / worse {s['n_worse']} / tied {s['n_tied']}")
