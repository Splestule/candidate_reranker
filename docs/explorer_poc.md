# Explorer proof of concept

Written before the run. One question: does a decoder trained to be useful *for composition*
give the composition pipeline more to work with than the same compute spent on plain
sampling?

## Setup
- Anchor: Whisfusion as released, frozen.
- Explorer: LoRA (rank 16, every linear layer of the 18 decoder blocks, 6.2M parameters) on top
  of the anchor; one set of weights, switched on and off at decode time.
- Training data: LibriSpeech train-clean-100 (8 parquet shards, ~16k utterances, 1000 steps of
  16). The base model was trained on all of LibriSpeech 960h, so a gain cannot come from data
  the anchor never saw.
- Loss (`tools/train_explorer.py`): Whisfusion's masked-diffusion cross-entropy (mask ratio
  0.5-1.0). The anchor's step-zero reading of the fully masked sequence marks the positions it
  gets wrong. There the explorer's cross-entropy is weighted 1 + alpha (alpha = 4) and an
  unlikelihood term, beta * -log(1 - p(anchor's wrong token)) with beta = 1, pushes it off the
  anchor's mistake.
- Control: the same LoRA, same data and steps, plain loss (alpha = beta = 0). It separates
  "trained for composition" from "fine-tuned a little more".

## Decoding and evaluation
- Arms at K = 4 and 8, flat PDD, 4 steps: `anchor-kK` (K anchor candidates),
  `mix-plain-kK` and `mix-expl-kK` (K/2 anchor + K/2 LoRA candidates). Same number of decoder
  passes in every arm.
- Data: rows 100-199 (shard s01 at shard size 100) of the 11 test sets to test, rows 0-99 of
  all 13 sets to train the composer. Development data; the untouched s02 stays reserved for a
  confirmation if this works.
- `tools/explorer_eval.py`: the frozen composition pipeline of the confirmation run (final,
  ROVER tuned, iROVER-style, upstream, MBR, oracles), set-level CV, seeds 0-2, paired
  bootstrap.

## What counts as a result
- Primary: final WER, `mix-expl-k8` against `anchor-k8` and against `mix-plain-k8`; worth
  pursuing if both differences are > 0 with the CI above 0 on every seed.
- Secondary: the same at K = 4; slot oracle (does the network contain the right word more
  often); per-candidate WER of explorer candidates (they may be individually worse and still
  help the composition).
- Training diagnostics on 256 held-out utterances: where the anchor errs at step zero, how
  often the explorer is right and how often it repeats the anchor's error; accuracy where the
  anchor is right should barely move.

## Prior art to cite
Generating systems that are complementary for combination is an old idea for HMM ASR
(e.g. Breslin & Gales, directed decision trees and boosting for complementary systems
feeding ROVER / confusion network combination), and diversity-by-training appears as
negative correlation learning and multiple-choice learning (Lee et al., stochastic MCL). What
would be new: doing it inside one parallel diffusion decoder, with a cheap switchable adapter,
aimed at the anchor's step-zero errors, and measured with a learned composition at equal
decoding compute.

## Cost
~20 min per LoRA on a T4 (estimate), ~2 h of decoding, ~1 h acoustic scores, ~30 min
evaluation. Caps in `tools/run_explorer.sh` keep the worst case under 10 h.

## Run 1 result
No gain: final WER at K=8, anchor 24.30, anchor + plain 24.17, anchor + explorer 24.38; the
explorer loss added nothing over the plain control. Diagnostics: the anchor's step-zero
reading is "wrong" at 48% of positions, mostly word shifts, and the explorer bought its
diversity by getting worse where the anchor was right (candidate WER 40.6 vs 38.2).

## Run 2: vote explorer (`tools/run_explorer2.sh`)
Three changes, inference unchanged (same K, same four steps, the adapter switched on for
some candidates):
1. Real errors. `tools/explorer_prep.py` decodes ~6000 training utterances with the anchor as
   at inference (K=4), builds the confusion network and aligns the reference: every reference
   word is `maj` (wins the anchor's vote), `min` (in the network, loses) or `hole` (missing).
2. Keep what works. KL(anchor || explorer) on every masked position except the `min`/`hole`
   words.
3. A differentiable stand-in for the composition. With s the explorer's share of K,
   V(w) = (1 - s) anchor share(w) + s p_explorer(w), read at the word's first token; the loss is
   relu(margin + max_competitor V - V(reference)) on `min` and `hole` words. Plus 0.2 x CE.
Arms: anchor-k4, mix-vote-k4 (2+2), anchor-k8, mix-plain-k8 (6+2), mix-vote-k8 (6+2),
mix-vote44-k8 (4+4). Same data, composer and evaluation as run 1. A smoke test (step 0) runs
first on Kaggle and stops the run if any new piece fails.
