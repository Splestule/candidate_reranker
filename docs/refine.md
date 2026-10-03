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

## Evaluation (`tools/refine_eval.py`)
Candidates: explorer run 2's anchor-k8 and anchor-k4 arms (results/cand_audio.pkl), so the
baselines are the exact numbers of the explorer runs. Frozen final pipeline, set-level 3-fold CV,
train on s00, test on s01 (1068 utterances, 11 sets), seeds 0-2, paired bootstrap. Views: base,
+score (decoder readings as slot features), +words (+score and the proposed words offered in
their slots), +cands (refined whole candidates added to the network), and a training-free
window argmax.

Pipeline checks before the run, on these candidates with fabricated readings: readings that
favour the reference are detected (+4.6 / +8.0 for +score / +words at K=8), pure noise gives
-0.08 / -0.05 with the CI across 0, and the base numbers reproduce run 2 (final 24.21 seed 0,
ROVER tuned 24.70).

## What counts
- Primary: final +words against final at K=8, CI above 0 on every seed.
- Availability: slot oracle +words below slot oracle, i.e. the refill brings words that were
  in no candidate. Reported with the proposal hit rate and the share of holes filled.
- Secondary: +score and +cands at K=8 and K=4; anchor-k4 +words against anchor-k8 final (does
  refining four candidates beat decoding four more).
- This is development data (s01). If the primary holds, a confirmation on untouched rows 600-799
  (s03) with everything frozen comes next.
