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
