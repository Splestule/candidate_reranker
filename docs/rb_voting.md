# Votes from distributions

Written before the run.

## Idea
In the confusion network each candidate gives one vote to the word it holds. That vote is the
argmax of a distribution the decoder already computed: at the last step a position was masked
the model predicted p_k(.) over the vocabulary and kept its top token. A row that chose
"their" at 0.51 over "there" at 0.49 votes exactly like a row that was sure. Here every row
gives each word v of the slot p_k(v), read at the first token of v, renormalised over the
slot's words. Same candidates, same network, same decoding cost.

## Why it should help (and when it cannot)
Let a slot have K rows and let x_k be row k's token.

Sampled tokens (a decoder that draws x_k ~ p_k, as flow matching / sampled diffusion does):
the hard share n(v)/K = (1/K) sum 1[x_k = v] and the soft share s(v) = (1/K) sum p_k(v) have
the same mean, because E[1[x_k = v] | p_k] = p_k(v). s is the conditional expectation of the
hard share given the distributions, so by Rao-Blackwell

    Var(n/K) = Var(s) + E[Var(n/K | p)] = Var(s) + (1/K^2) sum_k p_k(v)(1 - p_k(v)).

With i.i.d. rows the per-row variance splits into Var(p) (rows really differ) and E[p(1-p)]
(sampling noise). The soft vote removes the second term, which is worth a factor

    K_eff / K = (E[p(1-p)] + Var(p)) / Var(p)

in candidates: large when rows agree on the distribution but are each unsure (near-ties),
none when every row is confident.

Argmax tokens (Whisfusion PDD): x_k = argmax p_k, so given p_k the hard vote has no variance
left and the theorem does not apply directly. The diversity comes from the random masks, and
the two shares estimate different things: n(v)/K estimates P_mask(argmax = v), s(v) estimates
E_mask[p(v)]. The soft vote still keeps the margin the argmax throws away and breaks the ties
that are frequent at K = 4 (shares come in steps of 1/4). It helps if p_k is roughly
calibrated where rows disagree, and hurts if wrong rows are confidently wrong.

Known approximations: a word is read at its first token only (words that share a first token
split its probability, the holder keeps it if it is one of them); the distribution belongs to
the holder's position, so a row whose words are shifted reads a competitor at the wrong
place; deletions keep a hard vote; only the top 8 tokens are stored.

## Run
- tools/rb_run.py: flat K=4, flat K=8, tree-early K=8 with `track_topk=8` in pdd_decode
  (bookkeeping only, tokens identical; the smoke test checks it), plus acoustic scores.
  s01 of the 11 test sets to test, s00 of all 13 to train. s02 stays untouched.
- tools/rb_eval.py: ROVER tuned vs ROVER-RB (lambda in {0.25, 0.5, 0.75, 1} mixing hard and
  soft votes, vote temperature T in {1, 2, 4}, votes from p ** (1/T), both tuned on the
  training sets with ROVER's alpha and eps fixed); final vs final + RB (soft share at each T,
  its gap to the slot's best, unnormalised probability mass). T is there because the decoder
  is sharp: most kept tokens sit near p = 1, so at T = 1 soft and hard votes barely differ. Set-level
  3-fold CV, seeds 0-2, paired bootstrap. Diagnostics on contested slots: how often the top
  hard / soft vote is the reference, ties, mean share of the reference.

## What counts
- Primary: final + RB vs final at flat K=4, CI above 0 on every seed.
- Secondary: the same at K=8 and tree-early K=8; ROVER-RB vs ROVER (shows the effect
  without a learned model); whether RB at K=4 reaches hard votes at K=8.
- A null result is reported as one: the slot model may already recover the margin from the
  per-word confidence it has.
