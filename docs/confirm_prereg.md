# Confirmation run: pre-registration

Written and committed before the run. Nothing below changes after results are seen; any
deviation is listed at the end with its reason.

## Data
- Test: shard s02 (manifest rows 400-599) of the 11 test sets. These utterances were never
  decoded during development (development used s00/s01).
- Train: s00 of all 13 sets (the 11 test sets plus ls-dev-clean, ls-dev-other).
- Decoding: Whisfusion, flat and tree-early (branch schedule [1, K/4, K, K]) at K = 4, 8, 15.
  Decode time measured per utterance on the run's GPU.

## Frozen
Every feature, grid and hyperparameter of `tools/confirm_eval.py` as committed: slot model
(lam 1e-4, lr 0.05, 800 iters), neighbour bigram on 1200 held-out training references,
acoustic step-0 features (window 2), ROVER grid, iROVER-style boosted stumps (depth 1, 400
iterations), GPT-2 (124M) slot features with 12 words of left context, candidate LM
rescoring grid. Seeds 0, 1, 2.

## Primary protocol
Set-level 3-fold CV exactly as in development (folds of `tools/final_compare.py`): train on s00
of the sets outside the fold, test on s02 of the fold's sets. Paired bootstrap (3000
resamples, 95% CI) on word errors. A hypothesis PASSES only if its condition holds for every
listed comparison on every seed.

| | hypothesis | condition | development value |
|---|---|---|---|
| H1 | final, tree-early K=8 beats upstream Whisfusion (flat K=15, mean confidence) | CI > 0 | +5.44 [5.04, 5.87] |
| H2 | tree-early is non-inferior to flat for final, K = 4, 8, 15 | upper CI of (tree - flat) < 0.5 | +0.22, +0.23, +0.14 |
| H3 | final beats iROVER-style, same K and decode, K = 4, 8 | CI > 0 | +0.18 to +0.55 |
| H4 | final beats tuned ROVER, all six configurations | CI > 0 | +0.6 to +0.9 |
| H5 | final + GPT-2 beats upstream + GPT-2 and MBR + GPT-2 (same LM, tuned rescoring) | CI > 0 | not measured |
| H6 | GPT-2 features improve final | CI > 0 | +1.69 [1.55, 1.82] (K=32 flat) |

H3 at K=4 flat had the narrowest development margin (+0.18 [0.03, 0.32]); a FAIL there is
plausible and will be reported as such.

## Reported without a hypothesis
- In-domain protocol (train on s00 of all sets, test on s02 of all test sets).
- Whisper-small, autoregressive, greedy, batch 1, on the same s02 utterances.
- final + GPT-2 against iROVER-style with the same GPT-2 features.
- Per-set WER at the headline configurations; Whisper-normalised WER.

## Deviations
(none yet)
