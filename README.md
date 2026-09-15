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
