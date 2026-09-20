# candidate_reranker

How much accuracy [Whisfusion](https://github.com/taeyoun811/Whisfusion) loses when it picks
one of its K parallel candidates, and what closes the gap.

LibriSpeech test-clean, 2620 utterances, K = 15, free Kaggle T4 (fp16 + SDPA instead of
bf16 + FlashAttention). Reproduction matches the paper: 8.24 vs 8.3 mean-utterance WER,
69.7 vs 68.7 % hit rate, 5.75 vs 5.9 oracle.

| selection | corpus WER | mean-utt | hit % | gap |
|---|---|---|---|---|
| `mean_conf`, upstream v1 | 9.10 | 8.24 | 69.7 | 2.49 |
| `mbr_wer` | 8.30 | 7.70 | 76.8 | 1.95 |
| `conf + 0.5·mbr` | 8.29 | 7.61 | 77.6 | 1.86 |
| ROVER, word-level vote | **6.76** | **6.91** | — | — |
| oracle over whole candidates | 6.66 | 5.75 | 100.0 | — |
| oracle over word-level combinations | **3.27** | **3.40** | — | — |

Paired bootstrap for `conf+0.5·mbr` over the baseline: +0.63 points, 95 % CI [+0.47, +0.79].
Whisfusion v2 makes MBR its default selection, so those rows are a reproduction, not a result.

Three things not in the paper:

- Candidates are identical after step 1 on 100 % of utterances. Step 0 masks everything, so
  all K inputs are the same sequence and the update is argmax.
- Sampling in step 0 raises pairwise distance from 14.3 to 16.7 %, but the oracle gets worse
  (5.21 → 5.31 on a matched subset). Mask ratios of 0.8–1.0 overwrite injected differences.
- Picking the best word at each aligned position beats the best whole candidate on 34 % of
  utterances, and voting over those positions gets there without a reference: ROVER reaches
  6.76 against a 6.66 whole-candidate oracle. Replacing the alternatives with unrelated words
  leaves only 0.37 of the 3.40 points of headroom, so the gain is information, not free choice.

## The campaign: two model families, 21 datasets

An 11-hour Kaggle T4 x2 session extends all of the above to a second model family and far more
data: 18,400 utterance decodes, about 447,000 candidate transcripts, zero failed jobs. Design,
outputs and how to rerun: [docs/campaign.md](docs/campaign.md). Findings, tables and the
per-utterance data: [results/campaign-2026-09-20](results/campaign-2026-09-20)
([REPORT.md](results/campaign-2026-09-20/REPORT.md)).

Models: Whisfusion (masked diffusion, K = 32) and Drax (discrete flow matching, K = 16 at
T = 1.3, plus its own T = 0.1 decode). Data: LibriSpeech dev/test, the Open ASR Leaderboard test
sets (AMI, Earnings22, VoxPopuli, GigaSpeech, SPGISpeech, Common Voice), FLEURS in six
languages, SLR83 accents, and a babble/white-noise ladder on test-clean.

Pooled over datasets (random-effects, WER points, positive favours ROVER):

| contrast | Whisfusion (14 sets) | Drax (19 sets) |
|---|---|---|
| ROVER vs pick by confidence | **+4.43** [3.60, 5.26] | **+1.73** [1.37, 2.08] |
| ROVER vs pick by MBR | **+2.77** [2.17, 3.37] | +0.52 [0.30, 0.74] |
| ROVER vs one sample | +11.98 [10.63, 13.33] | +6.00 [5.17, 6.82] |

Against Whisfusion's own upstream decoding (K = 15, mean confidence) ROVER wins on 16 of 16
datasets, mean +4.9 points. Against Drax's standard decode it averages only +0.34: better on
10 of 21 sets, worse on 2. Composition beats *selection* everywhere; beating a strong model's
default decode is a narrower claim.

Four things the scale buys:

- **It pays when candidates disagree.** Across 37 model x dataset cells the gain tracks
  candidate diversity at r = 0.87. The noise ladder is the controlled version: Whisfusion's
  gain over MBR goes +1.40 (clean) -> +3.04 (10 dB) -> +4.73 (5 dB) -> +7.99 (0 dB).
- **The headroom is information.** Pooled over all sets the composition oracle is 11.15
  (Whisfusion) and 5.03 (Drax) against candidate oracles of 19.46 and 8.20; the shuffled
  control recovers only a fifth of that, a signal-to-luck ratio of 4.2x and 3.9x.
- **It saturates, the oracle does not.** To K = 64 on test-other, Drax's ROVER flattens at
  ~5.0 while the composition oracle keeps falling to 1.43.
- **Candidates cost K x the decoder; combining is free.** ROVER is 0.2-2.9 ms of CPU per
  utterance. At matched compute, more candidates roughly ties with more denoising steps, but
  composition at half the compute beats selection at full compute
  ([figure](results/campaign-2026-09-20/figures/fig_cost_quality.png)).

```bash
bash setup.sh /work
export PYTHONPATH=$PWD/src:/work/Whisfusion/src
python src/selftest.py --work /work
python src/dump_candidates.py --source librispeech --path /work/data/LibriSpeech/test-clean \
    --base_model /work/ckpt/mdm_safetensors/mdm-170M-100e18-rsl-0.01.safetensors \
    --adapter /work/ckpt/whisfusion_stage2_decoder.pt \
    --out results/test-clean.jsonl --resume
python src/analyze.py results/test-clean.jsonl --json results/test-clean.stats.json
```

`src/wf_compat.py` replaces the CUDA extensions Whisfusion imports; FlashAttention 2 needs
Ampere and Kaggle serves T4 or P100. Kaggle notes in [docs/kaggle.md](docs/kaggle.md).
