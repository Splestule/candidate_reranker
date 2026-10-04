# Peer-conditioned denoising

Written before the run; the criteria below do not change after results are seen.

## Idea
PDD decodes K rows in parallel, and every step fills all masked positions, so before the last
step each row is a complete sentence and so are its siblings. Their disagreement carries
information: 2.8x the shuffled control for Whisfusion (SKELETON 4.2), and the gain of composition
tracks disagreement at r = 0.87. Every method so far read that disagreement only after decoding
(ROVER, final, refinement, LM features). Here the denoiser reads it during decoding: in the last
step, each row's input embeddings get a learned projection of its siblings' tokens at every
position (their mean embedding, the share agreeing with the row, the share of the majority).
The rows then go to the same final pipeline as always.

Training-free interaction between parallel diffusion paths exists for text (Self-Repulsive
Sampling 2026: peers' commitments push a path away, for diversity; self-rewarding SMC: paths are
reweighted and resampled). Self-conditioning feeds a model its own previous prediction. Trained
conditioning on the joint state of the sibling paths, aimed at combining them, for ASR, we did not
find; the search was a handful of web queries without the full texts, so that claim needs a proper
literature review before it goes into a paper.

## Run (`tools/run_pcd.sh`)
- Training audio disjoint from evaluation (`tools/pcd_data.py`): for each Open ASR Leaderboard
  set one shard the evaluation never took, dropping utterances whose meeting / call / speaker
  appears in that set's evaluation manifest; plus a LibriSpeech train-clean-100 shard. Up to 700
  utterances per source.
- States: tree-early [1, 2, 8], the 8 rows before the last step (`tools/pcd_states.py`).
- Four variants, identical in data, rows, masks, steps (1200 x 16 rows), LoRA rank 16 and the
  two zero-initialised projections (`tools/pcd_train.py`):
  `peer` the method; `self` the row's own previous tokens (classic self-conditioning);
  `shuf` siblings from a different utterance (information or capacity?); `plain` no extra input
  (in-domain fine-tuning of the last step).
- Evaluation decodes (`tools/pcd_decode.py`): s00 + s01 of the 13 sets, tree-early to the last
  step once, the last step five ways with the same mask. `pcdbase-k8` is the untrained model and
  is checked to reproduce tree-early PDD exactly; a 0-step adapter is checked to change nothing.
- Final pipeline, set-level 3-fold CV, train s00, test s01 (1067 utterances, 11 sets), seeds 0-2,
  paired bootstrap (`tools/refine_eval.py`); candidate quality and diversity (`tools/pcd_report.py`);
  GPT-2 stacked on top, reported separately.

Cost: tree-early K=8 is 19 decoder passes (312 ms on a T4) against 32 (480 ms) for flat K=8; peer
conditioning adds a gather of sibling embeddings and two small projections to the last step.

## What counts
- **H1 (the method)**: pcd-peer final beats pcd-plain final, pcd-self final and pcd-shuf final,
  CI above 0 on every seed. Without all three, a gain is fine-tuning, self-conditioning or extra
  capacity, not reading the siblings.
- **H2 (worth it)**: pcd-peer final beats pcdbase final (tree-early, same compute), CI above 0 on
  every seed.
- **H3 (the efficiency claim)**: pcd-peer final is not worse than flat K=8 final: upper CI of
  (flat - peer) below 0.3 on every seed, at 0.65x the decode.
- Reported without a hypothesis: candidate WER, oracle and disagreement per arm (does peer
  conditioning pull the rows together?); ROVER tuned per arm; + GPT-2 on top.

Development data (s01). If H1 and H2 hold, a frozen confirmation on untouched rows 600-799 (s03)
follows.
