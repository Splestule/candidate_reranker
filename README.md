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

## The campaign: four decoder families, 25 datasets

Three Kaggle T4 x2 sessions (11 h + 3.3 h + 11 h) extend all of the above to more models and far
more data: 297 jobs, 55,481 utterance decodes, ~1.59 million candidate transcripts, zero failed
jobs. Design, outputs and how to rerun: [docs/campaign.md](docs/campaign.md). Everything the
sessions produced is in [results/campaign-2026-09-20](results/campaign-2026-09-20) — the raw
candidate dumps, the per-utterance table, the dataset manifests, the Kaggle and per-worker logs, a
record of every job, and the tables and figures derived from them
([REPORT.md](results/campaign-2026-09-20/REPORT.md)).

Models: Whisfusion (masked diffusion, K = 32), Drax (discrete flow matching, K = 16 at T = 1.3
and at its dev-tuned T = 0.4, plus its own T = 0.1 decode), and as controls Whisper-small and
Whisper-large-v3-turbo (autoregressive: greedy, beam-8 n-best, 16 samples) and Parakeet-CTC-1.1B
(32 sampled frame paths). Data: LibriSpeech dev/test, the Open ASR Leaderboard test sets (AMI,
Earnings22, VoxPopuli, GigaSpeech, SPGISpeech, Common Voice), FLEURS in six languages, SLR83
accents, and a noise ladder on test-clean (babble at 15, 10, 5, 0 and −5 dB; white at 10, 5 and
0 dB). The third session also sweeps the temperature of every family on the same three sets.

**One normalisation.** Every WER is under Whisper's text normaliser (the Open ASR Leaderboard
convention), applied to the reference and to each candidate *before* anything is combined, so the
words that are voted on are the words that are scored. The first two sessions were analysed with
the legacy lowercase-and-strip-punctuation normaliser, and their Whisper-normalised columns built
ROVER on legacy tokens, which understated it by 1.5–2.7 points. Everything has been re-scored;
the legacy numbers survive only as `lg_*` columns, to reproduce the Whisfusion paper, and on the
same data the pooled contrasts below move by at most 0.1 point between the two.

Pooled over datasets (random-effects, WER points, positive favours ROVER):

| contrast | Whisfusion (18 sets) | Drax (23 sets) |
|---|---|---|
| ROVER vs pick by confidence | **+4.62** [3.96, 5.29] | **+1.81** [1.50, 2.12] |
| ROVER vs pick by MBR | **+2.84** [2.36, 3.32] | +0.55 [0.37, 0.73] |
| ROVER vs one sample | +11.86 [10.76, 12.96] | +6.25 [5.46, 7.04] |

Against Whisfusion's own upstream decoding (K = 15, mean confidence) ROVER wins on 20 of 20
datasets, mean +5.2 points. Drax at its dev-tuned T = 0.4 beats its own standard decode by
+0.67 (better on 16 of 23 sets, worse on none) — but there MBR selection does just as well (+0.08
between them).

**The controls decide the framing.** The same composition over autoregressive and CTC pools does
nothing against a greedy decode: Whisper-turbo 16 samples +0.06, Whisper-small −0.28,
Parakeet-CTC 32 sampled paths +0.00 (without babble at −5 dB, where Whisper-turbo's greedy decode
loops to 161 % WER and dominates any pooled number). Voting over a beam n-best list is worse than
greedy (−3.1 for Whisper-small, −2.0 for turbo), but that is beam search failing on AMI and heavy
noise: against the top beam, the vote over its own n-best list is slightly better (+0.5, +0.1).

**Inside each decoder, the gain follows disagreement.** Raising the sampling temperature on the
same three sets (ls-test-other, AMI, babble 5 dB; 600 utterances per point):

| decoder | disagreement between candidates | ROVER gain over MBR | r | best ROVER vs its best single decode |
|---|---|---|---|---|
| Drax, T 0.4 → 1.6 | 6.8 → 53 % | −0.13 → +4.32 | 0.99 | 7.56 vs 7.43 (MBR) |
| Parakeet-CTC, T 0.5 → 2.0 | 6.3 → 77 % | −0.07 → +21.3 | 0.97 | 8.76 vs 8.65 (greedy) |
| Whisper-turbo, T 0.3 → 1.2 | 3.5 → 59 % | +0.02 → +3.61 | 0.99 | 7.09 vs 7.19 (greedy) |
| Whisfusion, first-step T 0 → 1.5 | 34 → 38 % | +2.94 → +3.55 | 0.90 | 21.07 vs 24.01 (MBR) |

At matched disagreement the gains are the same size in every family (Whisfusion +3.1 at 34 %,
CTC +4.4 at 39 %, turbo +3.6 at 59 %), so composition is variance reduction and nothing specific
to diffusion. What differs is the price of the disagreement: an autoregressive or CTC pool only
disagrees once every candidate is worse, and composition then wins back part of what the
temperature cost — never more than 0.1 point past greedy. Whisfusion's pool disagrees at its
native operating point, so there composition is a net win. (Whisfusion's first-step temperature
barely moves its disagreement, so its own row covers a narrow range.)

Five more things the scale buys:

- **It pays when candidates disagree.** Across 92 model x dataset cells (all but babble at −5 dB) the gain
  over MBR tracks candidate diversity at r = 0.87. The noise ladder is the controlled version: Whisfusion's gain
  over MBR goes +1.2 (clean) -> +1.9 (15 dB) -> +3.2 (10 dB) -> +4.5 (5 dB) -> +7.8 (0 dB), and
  then stops rising (+7.3 at −5 dB). Drax peaks at 0 dB (+3.6) and falls at −5 dB (+1.6), where its
  candidates disagree on 94 % of words: past a point the pool is mostly noise.
- **The headroom is information.** Pooled over all sets the composition oracle is 13.40
  (Whisfusion) and 6.88 (Drax) against candidate oracles of 21.60 and 10.24; replacing every
  alternative with an unrelated word recovers only 2.5 and 1.2 points of that, a signal-to-luck
  ratio of 3.3x and 2.8x.
- **It saturates, the oracle does not.** To K = 64 on test-other, Drax's ROVER flattens at 4.6
  (and MBR catches it, 4.55) while the composition oracle keeps falling to 1.28.
- **Candidates cost K x the decoder; combining is free.** ROVER is 0.1–7 ms of CPU per utterance.
  On test-other, Whisfusion's ROVER reaches the best WER selection ever reaches at a fifth of the
  compute; Drax's two curves meet from K = 16 on
  ([figure](results/campaign-2026-09-20/figures/fig_cost_quality.png)).
- **MOVER is not a better combiner here.** MOVER ([Kamo et al., 2025](https://arxiv.org/abs/2508.05055))
  extends ROVER to multi-speaker meetings; on one utterance its speaker, segment and ordering
  stages are no-ops and its time constraint changed nothing, which leaves incremental alignment
  with a plain majority vote. Against our ROVER, on the first shard of every test set, it is worse on Whisfusion (+0.71 WER
  [0.57, 0.85]), better on Drax (−0.29) and on Whisper samples (−1.08 small, −0.45 turbo), and ties
  on CTC. Its alignment helps pools whose candidates differ in length; our confidence and
  near-duplicate weighting is what Whisfusion needs
  ([results](results/campaign-2026-09-20/mover/mover_summary.csv),
  [script](tools/mover_experiment.py)).

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
