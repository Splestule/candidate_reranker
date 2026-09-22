#!/usr/bin/env python3
"""Predict how many candidates an utterance actually needs, before paying for them.

The k ladder in the per-utterance table is exactly what decoding with a smaller K would
have produced -- candidates are exchangeable draws, so the first k of them are a faithful
run at k. That makes both the label and the evaluation exact and free:

    label      the smallest k whose ROVER output is already as good as at k_max
    evaluation look the predicted k up in the same ladder

No GPU, and no oracle leakage at inference: every feature is read off the shared prefix
after step 1, which is one forward pass, plus the audio duration.

Regression to the mean is the trap here. Mean k_needed is 4.5 but the tail that needs 32 is
what costs WER, and a least-squares fit predicts 4.5 everywhere and quietly loses that tail.
So the score is only used for RANKING, then mapped onto the ladder by quantiles, which
reproduces the label distribution by construction and keeps the spread.
"""

from __future__ import annotations

import glob
import gzip
import json
import statistics
from pathlib import Path

import numpy as np
import pandas as pd

# Everything here is knowable after step 1, from the one shared prefix, plus the audio.
FEATURES = ["duration_s", "n_tokens", "tokens_per_s", "avg_conf", "min_conf", "median_conf",
            "mean_logprob", "mean_entropy", "conf_p10", "conf_p25", "frac_below_50",
            "frac_below_80", "conf_std"]


def utterance_features(row: dict) -> dict | None:
    """Read the features off the first candidate, which is the shared prefix."""
    c = row["candidates"][0]
    wc = c.get("word_conf")
    dur = float(row.get("duration_s") or 0.0) or 1e-6
    n = int(c.get("n_tokens") or 0)
    if not wc or n == 0:
        return None
    a = np.asarray(wc, dtype=float)
    return dict(
        id=row["id"], set=row.get("dataset") or row.get("set"),
        duration_s=dur, n_tokens=n, tokens_per_s=n / dur,
        avg_conf=float(c.get("avg_conf", a.mean())), min_conf=float(c.get("min_conf", a.min())),
        median_conf=float(c.get("median_conf", np.median(a))),
        mean_logprob=float(c.get("mean_logprob", 0.0)),
        mean_entropy=float(c.get("mean_entropy", 0.0)),
        conf_p10=float(np.percentile(a, 10)), conf_p25=float(np.percentile(a, 25)),
        frac_below_50=float((a < 0.5).mean()), frac_below_80=float((a < 0.8).mean()),
        conf_std=float(a.std()),
    )


def build(root: str, arm: str = "flat", metric: str = "e_rover_cg",
          tol: float = 0.5) -> pd.DataFrame:
    """Join features from the dumps onto labels from the k ladder."""
    root = Path(root)
    feats = []
    for p in glob.glob(str(root / "dumps" / "*" / f"{arm}.jsonl.gz")):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                r = utterance_features(json.loads(line))
                if r:
                    feats.append(r)
    F = pd.DataFrame(feats)

    parts = [pd.read_parquet(p) for p in glob.glob(str(root / "analysis" / "*.parquet"))
             if ".grid." not in p]
    d = pd.concat(parts, ignore_index=True)
    d = d[d.arm == arm]

    rows = []
    for (s, i), x in d.groupby(["set", "id"]):
        x = x.sort_values("k")
        R = max(int(x.ref_len.iloc[0]), 1)
        rov = x[metric].to_numpy(float)
        ks = x.k.to_numpy()
        # Saturation of the realised output is a jagged target: ROVER is NOT monotone in k,
        # 59 % of utterances get worse somewhere as k grows, so "the first k as good as k_max"
        # often fires on a fluke. The composition oracle is monotone to within 2 %, so its knee
        # -- the first k within tol points of the ceiling -- is the better behaved label.
        o = x[x.e_oracle_comp.notna()].sort_values("k")
        knee = None
        if len(o) > 1:
            ov = o.e_oracle_comp.to_numpy(float)
            knee = int(o.k.to_numpy()[int(np.argmax(100.0 * (ov - ov[-1]) / R <= tol))])
        rows.append(dict(set=s, id=i,
                         k_needed=int(ks[int(np.argmax(rov <= rov[-1]))]),
                         k_knee=knee,
                         ladder=list(x.k), edits=list(rov), ref_len=R))
    L = pd.DataFrame(rows)
    return F.drop(columns=["set"]).merge(L, on="id", how="inner")


def fit(train: pd.DataFrame, ridge: float = 1.0) -> dict:
    """Ridge on log k_needed. The coefficients are only ever used to rank."""
    X = train[FEATURES].to_numpy(float)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = np.c_[(X - mu) / sd, np.ones(len(X))]
    y = np.log(train.k_needed.to_numpy(float))
    A = Z.T @ Z + ridge * np.eye(Z.shape[1])
    A[-1, -1] -= ridge                                   # never shrink the intercept
    w = np.linalg.solve(A, Z.T @ y)
    return dict(mu=mu, sd=sd, w=w, quantiles=np.sort(train.k_needed.to_numpy(float)))


def predict_k(model: dict, df: pd.DataFrame, ladder: list[int], budget: float | None = None
              ) -> np.ndarray:
    """Rank by score, then map the ranks onto the label distribution, not onto the mean."""
    X = df[FEATURES].to_numpy(float)
    Z = np.c_[(X - model["mu"]) / model["sd"], np.ones(len(X))]
    score = Z @ model["w"]
    ranks = score.argsort().argsort() / max(len(score) - 1, 1)
    q = model["quantiles"]
    if budget is not None:                               # shift the distribution to a target mean
        q = q * (budget / q.mean())
    want = np.quantile(q, ranks)
    lad = np.asarray(sorted(ladder), dtype=float)
    return lad[np.abs(lad[None, :] - want[:, None]).argmin(1)].astype(int)


def evaluate(df: pd.DataFrame, ks: np.ndarray) -> dict:
    """Exact: read the chosen k straight out of each utterance's own ladder."""
    edits, tot = 0.0, 0
    for (_, row), k in zip(df.iterrows(), ks):
        lad, ed = list(row.ladder), list(row.edits)
        j = min(range(len(lad)), key=lambda t: abs(lad[t] - k))
        edits += ed[j]
        tot += row.ref_len
    return dict(wer=100.0 * edits / max(tot, 1), mean_k=float(np.mean(ks)))
