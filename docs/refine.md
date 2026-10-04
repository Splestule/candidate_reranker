# Consensus re-denoising

Written before the run.

## Why
Every combiner so far reads what the decoder exported for K candidates generated
independently of each other, and all of them stop at a few percent of the headroom
(paper/SKELETON.md 5-7). Two things were measured to be missing: a score that is comparable
across the alternatives of a slot, and the words no candidate proposed (12 % of reference
words). Training the decoder to produce complementary candidates (docs/explorer_poc.md) did not
work: the explorers were no better error detectors than plain extra samples.

A masked diffusion decoder can be asked a question an autoregressive one cannot: fill these
positions, given this audio and these words around them. The confusion network says which
question to ask -- where the candidates disagree, and what they agree on around it. So the
composition is written back into the decoder's input instead of being its last step.

## What `tools/refine.py` does (no training, no reference)
For each contested slot (candidates disagree, or the consensus word's confidence < 0.7; at most
10 per utterance) the consensus (ROVER as shipped) is the decoder's input with that slot masked:

- refill: the slot, or a run of up to 4 adjacent contested slots (the gap is segment-shaped,
  SKELETON 5b), masked at the token lengths its readings have and filled by argmax. A single
  word no candidate had becomes a new alternative of the slot; the refilled groups stitched into
  the consensus give one or two new whole candidates.
- score: every alternative of the slot, new ones included, in the SAME consensus context:
  lp_self (its own tokens masked) and lp_nb (the neighbouring consensus words masked, the
  alternative visible). Epsilon gets lp_nb only. Previously tried and different: the step-zero
  acoustic reading (no context at all) and the whole-transcript PLL (every transcript in its own
  context, compared across transcripts).

Cost: about 40 decoder sequence passes per utterance, against 32 for decoding K=8 (4 steps).

## Trained (`tools/train_refiner.py`)
Zero-shot the decoder has never been asked this: in training its unmasked context is always
the reference, never a consensus that is partly wrong, and the masked span is never where K
candidates disagree. The refiner LoRA (rank 16, 600 steps of 16) is trained on exactly the
inference input: consensus written out, one contested group masked at the length of the
reference's words for it, cross-entropy on those tokens (plus one uncontested slot in 30 % of
utterances, so "masked" does not mean "must change"). Control: the plain LoRA, same
utterances, steps and rank, trained with Whisfusion's own objective on the reference. If the
refiner beats it, the input is what matters, not in-domain fine-tuning.

Data and leakage: shard 0 of the test sets, from results/cand_audio.pkl. One adapter per fold of
the evaluation's set-level CV, trained on the other folds' sets and applied only to its own
fold's sets (dev sets, never trained on, use fold 0's). No adapter ever refines an utterance of a
set it was trained on; the combiner of fold f trains on shard-0 features that came from adapters
which saw fold f's shard 0 (not its shard 1, the test).

## Prior work this has to be positioned against
- Single-hypothesis refinement: Mask-CTC (Higuchi et al. 2020), PC-MLM error correction for CTC
  (Futami et al., Interspeech 2022), Align-Refine (Chi et al. 2021): mask the low-confidence
  tokens of ONE hypothesis and re-predict them.
- Audio-conditioned diffusion deliberation: Whisper-LLaDA (Liu et al., ICASSP 2026,
  arXiv:2509.16622): a diffusion LLM with Whisper features refines a first-pass autoregressive
  transcript by random or low-confidence remasking; text-only LLaDA does not help. The closest
  paper. Single hypothesis, a second model.
- Deliberation (Hu et al. 2020, Transformer deliberation 2021): a second-pass decoder attends to
  audio and first-pass hypotheses through an extra encoder; autoregressive.
- N-best correction over multiple hypotheses, text only: N-best T5, HyPoradise / GER, and NAR
  correctors that align and jointly encode the hypotheses.
- DiffLM rescoring of CTC n-best lists (arXiv:2604.14001).
What would be new: the confusion network over one parallel decoder's own K candidates choosing
both WHERE to re-read (disagreement) and WHAT the context is (the consensus), the same decoder
doing the re-reading, and its output feeding back into the composition (new alternatives, new
candidates, comparable scores). The run carries the deciding ablation: "single refined" is the
Whisper-LLaDA/Mask-CTC recipe applied to Whisfusion's upstream pick, with as many words masked
as there are contested slots. Composition-guided refinement has to beat it.

## Evaluation (`tools/refine_eval.py`)
Candidates: explorer run 2's anchor-k8 and anchor-k4 arms (results/cand_audio.pkl), so the
baselines are the exact numbers of the explorer runs. Frozen final pipeline, set-level 3-fold CV,
train on s00, test on s01 (1068 utterances, 11 sets), seeds 0-2, paired bootstrap. Views: base,
+score (decoder readings as slot features), +words (+score and the proposed words offered in
their slots), +cands (refined whole candidates added to the network), and a training-free
window argmax (ROVER decides word or nothing, the decoder picks among the real words).

Pipeline checks before the run: the whole Kaggle runner end to end on a mock model (smoke test,
both GPU chains, six adapters, evaluation of three variants); and on these candidates with
fabricated readings: readings that
favour the reference are detected (+4.6 / +8.0 for +score / +words at K=8), pure noise gives
-0.08 / -0.05 with the CI across 0, and the base numbers reproduce run 2 (final 24.21 seed 0,
ROVER tuned 24.70).

Also reported, with no combiner: WER of the upstream pick, the single-hypothesis refinement of
it, the consensus, and the refined consensus.

## What counts
- Primary: final +words against final at K=8, CI above 0 on every seed.
- Availability: slot oracle +words below slot oracle, i.e. the refill brings words that were
  in no candidate. Reported with the proposal hit rate and the share of holes filled.
- Composition is the lever: consensus refined beats single refined (standalone transcripts).
- Training: final +words [refiner] beats final +words [plain] and [zs] at K=8.
- Secondary: +score and +cands at K=8 and K=4; anchor-k4 +words against anchor-k8 final (does
  refining four candidates beat decoding four more).
- This is development data (s01). If the primary holds, a confirmation on untouched rows 600-799
  (s03) with everything frozen comes next.

## Run 1 result: zero-shot (Kaggle, 4 Oct 2026)
This run was the first version of the pipeline: zero-shot only, no single-hypothesis baseline,
no training (those were pushed after the kernel started). 2332 / 2331 records refined at
K=8 / K=4 in 37 / 34 min on one T4 each, no failures, tokeniser round trip 100 %. Test: 1067
utterances, 11 sets, seeds 0-2.

| | K=8 | K=4 |
|---|---|---|
| ROVER tuned | 24.73 | 26.03 |
| final | 24.30 | 25.55 |
| final +score | 24.01 | 25.18 |
| final +words | 24.05 | 25.20 |
| final +cands | 24.43 | 25.81 |
| window argmax (no training) | 28.83 | 28.69 |
| slot oracle | 17.48 | 19.82 |
| slot oracle +words | 17.37 | 19.67 |

Paired bootstrap against final, per seed:
- K=8 +words +0.18 [0.03, 0.33], +0.32 [0.16, 0.48], +0.24 [0.08, 0.40]: **primary criterion
  met** (CI above 0 on every seed). +score +0.19 / +0.36 / +0.31, all CI above 0.
- K=4 +words +0.34 / +0.32 / +0.40, +score +0.41 / +0.32 / +0.39, all CI above 0.
- +cands -0.09 to -0.33 (K=4 seed 1 CI below 0); ROVER +cands -0.65 at K=4.
- anchor-k4 +words against anchor-k8 final: -0.84 to -1.01; refining does not replace four
  more candidates.

Reading:
- The gain is the score, not new words. The refill proposes 1.5 new words per utterance at
  K=8, 1.3 % of them right; it fills 21 of 2821 holes (0.7 %), and the slot oracle moves by
  0.11. +words is no better than +score.
- The decoder's reading of an alternative in the consensus context is a useful feature
  (+0.2-0.4 on top of the frozen pipeline, which already has the step-zero acoustic reading and
  the neighbour bigram) and a bad picker on its own (window argmax -4.5).
- Cost: 61 decoder sequence passes per utterance at K=8 against 32 for decoding the candidates
  (4 steps x 8), so about 1.9x the decode for +0.25. Between K=8 and K=15 the confirmation run
  had final 23.33 -> 22.64 (tree-early K=8 vs flat K=15), so more candidates is at least as
  good a use of the compute. The scoring passes are most of it and can be cut.
- Not yet measured: the single-hypothesis baseline and the trained refiner (the current
  run_refine.sh), and a matched-compute control.
