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
- Training audio disjoint from evaluation utterances (`tools/pcd_data.py`): for each Open ASR
  Leaderboard set one shard the evaluation never took, plus a LibriSpeech train-clean-100 shard,
  up to 700 utterances per source. Recordings and speakers can be shared with the evaluation
  (counted per set in train_data.json).
  *Amended before any result, after the first Kaggle attempt crashed in the smoke test:* the
  original plan also dropped every utterance sharing a meeting / call / speaker with the
  evaluation. That left 0 AMI, 0 Earnings22, 2 GigaSpeech, 89 VoxPopuli and 178 SPGISpeech
  utterances (1669 in total, almost all Common Voice and LibriSpeech), because AMI's 16 test
  meetings and Earnings22's 6 calls are all in the evaluation. All variants train on the same data,
  so sharing cannot favour one variant over another (H1); it can make every trained variant better
  than the untrained base, so H2 and H3 are read against the plain control as well.
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

## Run 1 result: invalid (training bug)
Every trained variant broke decoding, the plain control included: final WER 61-64 against 24.67
for the untrained base, candidate WER 71-81 against 36. The targets were the reference tokens
on the hypothesis' positions without alignment, so after the first word shift the last step
learned to write the reference shifted against the tokens it keeps ("walking past a pink hotel"
-> "walingk pa thestinininotot"). Token accuracy on held-out rows, measured in the same unaligned
setup, rose slightly and did not show it. The peer variant was also unstable (held-out accuracy
fell to 0.02 at step 500 before recovering). H1-H3 were not tested.

## Run 2 (results/pcd2), changes before any run-2 result
- Targets aligned to each row's own tokens (`pcd.align_targets`): equal tokens and same-length
  substitutions get the reference token, insertions / deletions / length-changing substitutions
  are ignored, positions after both sequences end keep padding.
- Peer and self inputs layer-normalised before the zero-initialised projection.
- After training, each variant decodes 100 held-out training utterances with the real last step
  (base vs adapter WER over all 8 rows); the run stops before the evaluation decodes if every
  adapter is worse than the base by more than 1 point.
Everything else (data, states, steps, arms, hypotheses H1-H3, evaluation) is unchanged.
