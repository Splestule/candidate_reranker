# The ceiling of post-hoc candidate combination in parallel ASR decoding

Working skeleton. Every figure below is printed by `tools/paper_numbers.py`; the header of
each section names the block it comes from. A number that this script does not print does
not belong in the paper.

Status of the argument: the headline measurement stands, three of the four ways we tried to
exploit it do not, and the negative results are what make the positive one worth reporting.

---

## 1. Claim

**Read this first: the composition ceiling is not ours to discover.** HyPoradise (NeurIPS
2023) already defines, names and tabulates it -- their *compositional oracle* o_cp against
the *n-best oracle* o_nb -- and the SLT 2024 GenSEC challenge adopted both as benchmark
metrics. Their ratios across ten test sets run from 1.4x to 4.7x, which brackets our 1.75x.
Any draft that opens with "the field measures against the wrong ceiling" will be desk
rejected by anyone who has read either paper. The gap measurement is a *replication on a new
class of decoder*, and it should be presented as one, in the first paragraph.

What is ours is narrower, and it is enough for a short paper:

1. **A ceiling that is defined and reachable.** o_cp is "achievable WER using all tokens in
   the N-best list" -- a bag of tokens, with no alignment, no positional constraint and no
   algorithm. That is not a bound any combiner can approach; it is not even clear it is
   well defined. Ours is the best path through a confusion network over the K candidates:
   a strictly tighter bound, constructively defined, and one that an actual combination
   algorithm could in principle attain.

2. **Separating the oracle's structure from the oracle's freedom.** An oracle over K
   hypotheses is partly information and partly the licence to guess K times. We measure the
   split with a **shuffled control**: keep the network's shape, replace the alternatives with
   unrelated words, take the oracle again. We found no prior work that does this for an ASR
   oracle, and it changes the reading of every published oracle number. In our data the
   real gap is **2.8x** the control's for masked diffusion and **1.8x** for flow matching,
   but **1.0x** for autoregressive beam search -- meaning a Whisper beam's entire
   composition-oracle gap, the largest in our table at 9.42 WER, is the oracle's freedom to
   guess and not information in the hypotheses. This is the result we would lead with, and
   it says the n-best correction literature is spending its effort on the wrong decoders.

3. **A ceiling on what post-hoc combination can reach, for a single parallel decoder.**
   Prior work says this for *multi-system* combination: iROVER (NAACL 2007) recovers about
   9 % of the ROVER-to-oracle gap on a network built from four systems' 1-best outputs, and
   Hoffmeister's thesis (2011) concludes that none of the sophisticated combiners beat plain
   confidence-weighted ROVER. We reproduce that verdict in the setting where the candidates
   are free -- one decoder, one pass -- and add what those papers do not have: an
   availability/recoverability decomposition, a learning curve showing it is a ceiling and
   not a sample-size problem, and an oracle-context bound on what local context is worth.

4. **Tuning-aware intervals.** No ASR paper we could find reports a confidence interval that
   includes hyperparameter-tuning noise; ASR significance testing resamples the test set only
   (Bisani and Ney 2004; Liu et al. 2019). We import the argument from Dodge et al. (EMNLP
   2019) and show it matters here: over the (alpha, eps) grid a ROVER arm spans 14 to 22 WER
   points, and two of our own results had to be retracted because of it.

The conclusion the paper argues to: **for parallel decoders the gap is real and not luck, and
it cannot be closed from outside the decoder.** Diffusion and flow-matching decoders emit K
candidates for free, which is what makes the question worth asking here and not on a beam.

## 2. Setup (block 1, block 7)

Whisfusion v1: frozen Whisper-small encoder, SMDM-170M masked-diffusion decoder, parallel
diffusion decoding, K = 32, 4 steps. 16 evaluation sets: LibriSpeech dev/test clean and
other, a babble and white-noise ladder over test-clean, AMI, Earnings22, GigaSpeech,
SPGISpeech, VoxPopuli, Common Voice, FLEURS-en, SLR83. 6296 utterances, 113 563 reference
words, legacy normalisation throughout (the composition oracle and the control are defined
only in that space).

Combination is ROVER over a confusion network built from all-pairwise alignments of the K
candidates: **0.35 ms against a 2365 ms decode, a factor of 6800**. Cost is not the story;
the ceiling is.

## 3. The gap (block 1)

| | WER |
|---|---|
| one candidate | 31.91 |
| ROVER over all K | 20.50 |
| best whole candidate (candidate oracle) | 19.46 |
| best word-by-word composition (composition oracle) | **11.15** |
| shuffled control | 17.47 |

- ROVER to composition oracle: **9.35 WER, 95 % CI [9.10, 9.60]**, better on 4192 utterances,
  worse on none.
- Composition beats the best whole candidate on **56 %** of utterances.
- Signal to luck against the lexical control: **3.1x** on these 16 sets. Section 4.2 repeats
  it against a stricter permuted control on the dumps (2.8x) and across every model.

## 4. The gap is general, the information in it is not (block 2, block 2b)

### 4.1 The gap itself

Each arm at its own largest K; K and the set list differ, so read the share, not the WERs.

| model / arm | K | sets | ROVER | comp. oracle | gap | % of error |
|---|---|---|---|---|---|---|
| whisfusion / main | 32 | 16 | 20.50 | 11.15 | 9.35 | 46 % |
| drax / main | 16 | 21 | 10.06 | 5.03 | 5.03 | 50 % |
| parakeet-ctc / sample | 32 | 8 | 9.60 | 4.86 | 4.75 | 49 % |
| whisper-small / sample | 16 | 8 | 10.35 | 4.99 | 5.36 | 52 % |
| whisper-small / beam | 8 | 8 | 13.35 | 5.69 | 7.66 | 57 % |
| whisper-turbo / sample | 16 | 8 | 7.71 | 4.44 | 3.27 | 42 % |
| whisper-turbo / beam | 8 | 8 | 8.57 | 4.24 | 4.33 | 51 % |

42 to 57 % everywhere. A combination oracle beats a selection oracle by about half the
remaining error for any system with K hypotheses; that is close to arithmetic, and on its own
it says nothing about whether the gap is usable.

### 4.2 The controls -- the result to lead with

Two controls, both preserving the network's shape, its epsilon arcs and its vote counts:

- **lexical** -- every alternative after the first is replaced by a word drawn from the
  corpus. Destroys the acoustics and the alignment, keeps the word statistics.
- **permuted** -- the alternative *sets* are moved between slots of the same utterance. The
  words, their counts and their confidences all survive; only the correspondence between a
  slot and its alternatives is destroyed. Every word on every arc is still a word this
  decoder really proposed for this utterance, so no one can object that the noise was
  obviously wrong. This is the stricter control and the one to report.

Both are clamped to the best whole candidate, the fallback any system has. The clamp must be
stated: **unclamped, a control oracle is often worse than ROVER itself**, because the shuffled
arcs crowd the right word out of its own slot. Both conventions are printed by
`tools/control_check.py`.

| model / arm | K | ROVER | comp. oracle | lexical | permuted | gap | signal / luck |
|---|---|---|---|---|---|---|---|
| whisfusion / main | 32 | 21.80 | 12.23 | 17.84 | 18.42 | 9.57 | **2.8** |
| drax / main | 16 | 10.70 | 5.56 | 7.74 | 7.90 | 5.13 | **1.8** |
| parakeet-ctc / sample | 32 | 11.35 | 6.42 | 7.73 | 7.89 | 4.93 | 1.4 |
| whisper-small / sample | 16 | 13.32 | 7.03 | 8.07 | 8.08 | 6.29 | 1.2 |
| whisper-turbo / sample | 16 | 9.65 | 6.17 | 6.47 | 6.49 | 3.48 | 1.1 |
| whisper-turbo / beam | 8 | 10.69 | 6.09 | 6.31 | 6.30 | 4.60 | **1.0** |
| whisper-small / beam | 8 | 17.33 | 7.91 | 8.28 | 8.28 | 9.42 | **1.0** |

Signal to luck = (ROVER - composition oracle) / (ROVER - permuted control). At 1.0 the
network carries nothing a shuffled network does not.

**Autoregressive beam search sits at exactly 1.0.** Its whole composition-oracle gap --
9.42 WER for whisper-small, the largest in the table -- is the oracle's freedom to guess,
not information in the hypotheses. Sampling is barely better, 1.1 to 1.2. CTC sampling 1.4.
Flow matching 1.8. Masked diffusion 2.8.

The ordering is monotone in how independently the candidates are generated, which is the
mechanism we would argue for: beam hypotheses share a prefix and differ where the search
happened to fork, while parallel-decoder candidates are drawn from a joint distribution over
the whole sequence and disagree where the model is genuinely uncertain.

Two consequences:

1. **Composition is worth pursuing for parallel decoders and not for beams.** That is the
   opposite of where the n-best correction literature spends its effort.
2. **Every published oracle number should carry a control.** The same headline gap means two
   entirely different things at 1.0 and at 2.8, and no paper in the sweep reports the split.

## 5. Where the gap lives (block 3)

Decompose ROVER's slot accuracy as A x R over the 89 729 slots whose reference is a real word:

- **A = 88.0 %** -- the reference word is an option in its slot at all.
- **R = 92.9 %** -- given that it is, the vote picks it.
- A x R = 81.7 %, which is ROVER's slot accuracy.

So **12.0 % is unavailable** -- no candidate proposed the word, and no combination rule can
invent it -- and **6.2 % is available and loses the vote**. Only the second is addressable
from outside the decoder. 83 % of the unavailability is true absence: the word appears in no
candidate at all, at any position.

## 5b. The shape of the gap -- the result that picks the next direction (block 3b)

An oracle allowed at most S candidate switches stitches its transcript from S+1 contiguous
segments. S = 0 is the n-best oracle; S unlimited is the composition oracle. Nothing in the
literature reports what is in between, and it turns out to be the whole story.

Share of the ROVER-to-composition gap closed at each budget:

| model / arm | ROVER | comp. | S=0 | S=1 | S=2 | S=4 | S=8 |
|---|---|---|---|---|---|---|---|
| whisfusion / main | 21.61 | 11.97 | 11 % | **54 %** | 72 % | **85 %** | 90 % |
| drax / main | 10.73 | 5.47 | 35 % | 68 % | 79 % | 85 % | 87 % |
| parakeet-ctc / sample | 11.36 | 6.41 | 42 % | 64 % | 72 % | 76 % | 76 % |
| whisper-small / sample | 13.38 | 6.91 | 71 % | 84 % | 87 % | 88 % | 89 % |
| whisper-small / beam | 16.81 | 7.85 | 34 % | 37 % | 37 % | 37 % | 37 % |
| whisper-turbo / beam | 10.86 | 6.05 | 54 % | 58 % | 58 % | 58 % | 58 % |

**One switch recovers 54 % of the gap for masked diffusion, four recover 85 %**, over roughly
25 slots per utterance. The gap is three or four contiguous segment choices, not twenty-five
independent word decisions -- which is exactly why the per-slot models of section 6.3 ceiling
out at a few percent: the problem was the wrong shape. It also agrees with the block
structure we measured independently, disagreement arriving in runs of two to four adjacent
words.

Beam search is the mirror image. Switches buy it nothing (34 % to 37 %), so the remaining
two thirds of its gap is only reachable by unconstrained word-level switching -- the oracle
picking lucky individual words. That is the same verdict the shuffled control gives in
section 4.2, from an entirely different measurement.

**And the search is free.** The one-switch space is (slots + 1) x K^2, about 30 000 options
at K = 32, and prefix sums enumerate all of them in microseconds against a 2365 ms decode.

### What is missing is a score, not a search

Every cheap way of ranking a whole path fails, and fails in a way that identifies the
problem:

| on held-out sets | WER |
|---|---|
| ROVER as shipped | 25.01 |
| best whole candidate (oracle) | 23.64 |
| best 0-switch path by mean confidence | 36.03 |
| + bigram + word-insertion bonus, both tuned on dev | 36.04 |
| best 1-switch path, tuned | 37.72 |

Summing ROVER's own per-slot score along a path is no better, and crucially it is **equally
bad without switching** (30.6 against 30.8), so this is not a failure of stitching. A slot
score was built to be argmaxed inside its slot; it was never calibrated to compare across
slots or across candidates. The decoder's confidences are not much better -- confidence-based
selection of a whole candidate reaches 24.81 where ROVER, which never compares paths at all,
reaches 20.50.

So: **the structure is there, the search is free, and the decoder emits nothing that ranks
one path against another.** That is the sharpest statement of the problem this paper can
make, and it says where the next work goes -- a learned scorer over stitchings first,
because it needs no retraining and bounds what is reachable without it, and then a decoder
whose confidences are comparable across candidates because the training objective made them
so.

## 6. What does not close it

### 6.1 Topology: RETRACTED (block 6)

We built the network the way Mangu, Brill and Stolcke (2000) do -- intra-word clustering on
correspondence strength, inter-word clustering on orthographic or phonetic similarity, with
acyclicity and one-candidate-per-slot as hard constraints -- instead of aligning everything
to a backbone. On 1500 utterances with a ~50-utterance dev set it looked worth **+1.11 WER**.

It is worth **+0.01, 95 % CI [-0.15, +0.18]**, on 2800 balanced held-out utterances.

The first number was one badly-tuned baseline parameter. Over the (alpha, eps) grid the
backbone arm spans **14.36 WER points** and the Mangu arm **22.50**; an effect of 0.03 cannot
be resolved against that with a dev set of fifty. `tools/tuned_compare.py` re-tunes both arms
on each bootstrap resample of the dev set, so the interval carries the tuning noise. **Method
note worth stating in the paper: any ROVER baseline reported without its tuning protocol and
its parameter sensitivity is uninterpretable.**

What survives: the construction is insensitive to the merge threshold, to the vote decay and
to phonetic versus orthographic similarity. The hard constraints do the work, not the
similarity measure.

### 6.2 Confidence calibration: RETRACTED (block 5)

Word confidences are monotone but badly scaled (ECE 0.205, saturated near 1). Fitting
`conf^t` on dev looked worth +0.17.

With the calibration refitted and alpha/eps re-tuned on every dev resample, against a
baseline that gets the same re-tuning:

| arm | test WER | vs as-is | 95 % CI |
|---|---|---|---|
| as-is (alpha/eps tuned) | 24.23 | -- | -- |
| isotonic | 24.49 | +0.19 | [-0.16, +0.52] |
| power ^11.9 | 24.35 | +0.12 | [-0.21, +0.46] |
| freq only (confidence discarded) | 25.23 | +1.00 | [+0.70, +1.16] |
| shipped (alpha 0.5, eps 0.7) | 24.51 | | |

The +0.17 was the alpha/eps re-tuning that came with the calibration (24.51 to 24.23);
calibration itself contributes nothing. The mechanism is worth a paragraph: ROVER's decision
is a comparison **inside one slot**, a monotone map barely changes the order inside a slot,
and the one thing it does change -- the trade-off between the confidence term, the frequency
term and epsilon -- is exactly what alpha and eps already set. **Monotone recalibration is
absorbed by the voting parameters.**

The control matters: discarding confidence costs 1.00 WER, so the signal is real. Its
*scale* is not what is wrong.

### 6.3 A learned picker: it works, and that is the bad news (block 4)

Multinomial logistic regression over the words of a slot; gold is the reference word; argmax
at test. Nine features that vary across words in a slot (vote share, confidence, calibrated
confidence, epsilon, is-top, log votes, word length, share of the top word, gap to the best
confidence) times six per-slot context features (1, entropy, alternatives, margin,
uncontested, mean slot confidence) as **multipliers**, 54 parameters, L2, convex.

The multiplier structure is the point: softmax over a slot is shift-invariant, so a feature
constant within the slot contributes nothing on its own. As a multiplier it gives the model a
**per-slot alpha** -- trust confidence where the slot is contested, trust counts where it is
not -- which fixed-alpha ROVER cannot express.

Trained on 8 sets, evaluated on 5 held-out sets (1877 utterances, 36 754 slots):

| | WER |
|---|---|
| ROVER as shipped | 19.29 |
| ROVER, alpha/eps tuned on the training sets | 19.29 |
| learned per-slot pick | 19.06 (-0.25, CI excludes zero) |
| + bigram against the neighbouring slots' most-voted words | 18.78 (-0.51) |
| + bigram against the reference's **own** neighbouring words (oracle) | 18.60 (-0.69) |
| **per-slot oracle** (reference word whenever it is present) | **12.27** |

The reference word is present in 92.0 % of these slots, so a perfect per-slot decision is
worth **7.02 WER**. The best learnable one is worth **0.51 -- 7 % of it**, and handing the
model the true neighbouring words raises that only to **0.69 -- 10 %**.

And none of it scales:

| train utts | no context | neighbour bigram | oracle neighbours |
|---|---|---|---|
| 200 | -0.19 | -0.48 | |
| 400 | -0.21 | -0.43 | |
| 800 | -0.25 | -0.48 | -0.69 |
| 1600 | -0.20 | -0.48 | -0.67 |
| 2000-3200 | -0.20 | -0.51 | |

Flat from 200 onward; stable to +-0.02 across independent training draws. **This is a
ceiling, not a sample-size problem.**

Ablation, at 800 utterances: plain linear reweighting of the nine varying features is worth
-0.17, per-slot adaptivity adds 0.04, and the neighbour bigram adds another 0.26 -- more
than everything inside the slot combined. The largest weight in the model is `lm(prev, w)`,
an order above the rest.

**Read together: the slot is exhausted, and local context nearly so.** Everything learnable
from the statistics of one slot is worth a quarter of a WER point. Adding one neighbouring
word doubles that, and knowing that neighbour *perfectly* adds only 0.18 more -- so the
limit is not the difficulty of estimating context, it is that one adjacent word does not
carry the missing information either.

**Methods trap, worth one paragraph in the paper.** The first version of this experiment
built the context bigram from the same references the weights were fitted on. The bigram
memorises them, `lm(prev, gold)` goes to one on every training slot, the model puts all its
weight there, and nothing transfers: with oracle context that turned a 0.5 gain into a 1.2
loss. The bigram is now built from 1200 utterances reserved for it alone. Any feature
derived from a model fitted on the training references has this failure mode.

### 6.4 A structured model over paths: a cautionary note

A linear-chain CRF with a bigram transition, trained with an averaged structured perceptron,
loses to calibrated ROVER by 0.61 WER, and a learning curve from 200 to 3200 utterances is
flat (+0.57 to +0.66). It would have been easy to report that as evidence that learned
combination does not work.

It is evidence that the optimiser did not work. The perceptron takes unit steps on features
whose scales differ by an order of magnitude, never converges (4027 slot corrections in the
first epoch, 4003 in the sixth) and ends up with a weight of +7.3 on word length. The same
problem written convexly, with standardised features, **wins**. The paper should carry this
as a short methods note: a negative result from an unconverged optimiser is not a negative
result about the model class.

Two apparatus checks belong in the same note. The CRF could not reproduce its own baseline
(248 of 400 utterances differed at the weights that should have made it identical to ROVER)
because epsilon carried a stored pseudo-confidence with no free parameter; an `--identity`
check that asserts the general model contains its baseline caught it. Earlier, a decoder
sanity check passed on pseudo-random audio that decodes to a single token, so "6/6 identical"
was a statement about an empty output.

## 7. What this leaves (discussion)

The budget, against a gap of 9.35 WER:

| lever | worth | share of the gap |
|---|---|---|
| tuning alpha/eps on an adequate dev set | 0.28 | 3 % |
| confidence calibration | 0.00 | 0 % |
| Mangu-style network construction | 0.00 | 0 % |
| learned per-slot picker | 0.25 | 3 % |
| + neighbouring-slot bigram | 0.51 | 5 % |
| + oracle knowledge of the neighbouring words | 0.69 | 7 % |

Nothing applied after the decoder recovers more than a few percent of what composition could
in principle reach. Three conclusions, and the last is the proposal:

**An oracle number is uninterpretable without a control.** The n-best and compositional
oracles are already reported across the literature, but nobody separates how much of the gap
is structure and how much is the oracle's freedom to guess K times. That split is not a
detail: it is 2.8x for masked diffusion and 1.0x for a Whisper beam, so the same headline gap
means two entirely different things. Every oracle table should carry a shuffled control.

**The tighter bound is the useful one.** o_cp as currently used -- "achievable WER using all
tokens" -- is a bag of tokens with no construction behind it. A network-path bound is higher,
but it is the one a combiner could actually reach, and here it still sits 1.75x below the
n-best oracle. Reporting against the n-best oracle alone, as most correction papers do,
understates the headroom by that factor.

**The gap is segment-shaped, so the next model is a segment chooser.** Section 5b: one
contiguous switch recovers 54 % of it and four recover 85 %, the one-switch search space is
30 000 options and enumerable in microseconds, and every cheap path score fails. The work
that follows from this paper is a learned scorer over stitchings -- three or four decisions
per utterance instead of twenty-five, with a whole segment of context to decide on -- and it
needs no retraining, so it also measures how much of the gap is reachable without touching
the decoder.

**Closing the rest means changing what the decoder emits, not what is done with it.** The
measurements say which part. 12 % of reference words are in no candidate at all -- that is
diversity, and only the decoder can supply it. Of the words that are present, per-slot
statistics recover 4 % of the headroom, one neighbouring word takes it to 7 %, and knowing
that neighbour perfectly reaches 10 %, so the missing information is neither local nor, at
this order, textual -- which points at the acoustics, and therefore at the decoder. (One
neighbouring word is not "context": a full-sentence or neural LM is an untested lever and
this paper must not generalise from a bigram.) The natural next step, and the one
this paper should propose rather than claim, is a decoder trained knowing a combination
follows: candidates penalised for agreeing where they are wrong, confidences that are
comparable across candidates because the training objective made them so, and a combination
step differentiable enough to be part of that objective.

## 8. Relation to prior work

Checked 29.9.2026. The positions below are what the sweep actually found; where a claim of
ours is already in the literature it is said so here rather than in a footnote.

**The composition ceiling is prior art.**
- **HyPoradise**, Chen, Hu, Yang et al., NeurIPS 2023 D&B, arXiv:2309.15701. Section 5.2
  defines o_nb ("WER of the best candidate in the N-best list") and o_cp ("achievable WER
  using all tokens in the N-best list"). Both are tabulated over ten sets; the ratio runs
  1.4x to 4.7x. **Must be cited in our first paragraph.** What we add: a positional, network-
  path definition with a construction, against their unformalised bag of tokens.
- **GenSEC challenge**, Yang et al., IEEE SLT 2024, arXiv:2409.09785. Adopts both oracles as
  challenge metrics, so the concept is now community property.

**Oracles from the decoder's own search graph, not from an n-best list** -- related but a
different object, and the distinction is worth one clear sentence in the paper:
- **Faria, Janin, Riedhammer, Adkoli**, Interspeech 2022. The only published n-best vs
  word-level oracle ratio: 1.58 % to 1.19 % (1.33x) and 0.65 % at phrase level (2.4x), from
  Kaldi lattices. Our 1.75x has to be positioned against these.
- **Ma, Gales, Knill, Qian** (N-best T5), Interspeech 2023. Both oracles on one beam:
  test-other 4.34 (10-best) against 3.00 (lattice). Also the closest methodological
  competitor to our "stay inside the words the model proposed" argument -- they constrain LLM
  decoding to the lattice rather than trying to beat the oracle.
- **Mangu, Brill, Stolcke**, CSL 2000. The construction we reimplemented; lattice oracle 9.5
  against consensus 37.3. No n-best oracle alongside it.
- **Hakkani-Tur et al.**, CSL 2006, observe in one sentence the mechanism behind our whole
  claim: WCN oracle accuracy 86.7 % against lattice oracle 85.7 %, "because the alignment
  process creates new paths".

**How much of the network oracle a combiner recovers is prior art too.**
- **Hillard, Hoffmeister, Ostendorf, Schlueter, Ney** (iROVER), NAACL-HLT 2007. Eval, four
  systems: ROVER(conf) 7.0, iROVER 6.7, oracle 3.6 -- a learned per-slot classifier recovers
  about 9 % of the gap. Network built from whole hypotheses, which is structurally our setup
  with a different candidate source. **The paper we most risk duplicating; cite it where we
  report our own share.**
- **Hoffmeister, Schlueter, Ney**, Interspeech 2008, and **Hoffmeister's thesis**, RWTH 2011,
  chapter 6: oracle gains do not convert into WER gains, and no sophisticated combiner
  considerably outperforms confidence-weighted ROVER.
- **Schwenk and Gauvain**, ICSLP 2000: correct word present in over 95 % of ROVER slots.

**The single-parallel-decoder setting appears open.**
- **Whisfusion**, arXiv:2508.07048, and **Drax**, arXiv:2510.04162, both select one whole
  candidate; neither builds a network or reports a composition oracle.
- **Hystoc**, Benes, Kocour, Burget, Interspeech 2023, arXiv:2305.12579, already turns one
  system's n-best into a confusion network by iterative alignment -- **our construction
  exists; cite it and state what we add**, which is the oracle and the control, not the
  network.
- **Re-evaluating MBR for ASR**, Jinnai 2025, arXiv:2510.19471, notes that MBR with a
  token-level edit utility "reduces to a form of ROVER-style majority voting". We need one
  sentence separating selection-under-an-edit-utility from composition, or a reviewer will
  say MBR already does this.

**Cost.** The LLM correction literature essentially never reports inference cost. The one
comparable number is **Apple's Denoising LM**, arXiv:2405.15216: a 484M corrector at 44 ms
greedy on an H100. Our 0.35 ms should be compared against that, not against an unreported
LLaMA-13B.

**Tuning sensitivity is thin, and we should say so rather than overclaim.** Fiscus (ASRU
1997) reports alpha 0.2 on one set and 0.7 on another and calls the spread "somewhat
surprising"; Hystoc reports optima drifting with temperature. Neither is a sensitivity study.
The framing to use is Dodge et al., EMNLP 2019, applied to ASR combination.

**To read in full before writing:** HyPoradise section 5.2 and its tables; the GenSEC
challenge paper; iROVER (four pages); Hoffmeister's thesis chapter 6; Faria et al. 2022;
N-best T5; Hystoc; Jinnai 2025. Rao Ma's Cambridge thesis is the one item the sweep could not
fetch and remains unchecked.

## 9. Open items

- earnings22 has 6 of 8 shards.
- The tuning-aware interval should be reported for **every** tuned comparison in the paper,
  not only for the retracted ones.
- The neighbour bigram is add-k over 1200 in-domain references and looks at one adjacent
  word. The oracle-neighbour row bounds what *that* is worth (0.69); a full-sentence or
  neural LM is a different and untested lever, and the paper should say so rather than
  generalising from a bigram to "context".
