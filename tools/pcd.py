"""Peer-conditioned denoising: the last PDD step reads what the K sibling rows hold.

PDD runs K rows in parallel and every step fills all masked positions, so before the last step
each row is a complete sentence and so are its K-1 siblings. The siblings' disagreement carries
information (signal over luck 2.8x against a shuffled control, gain tracking disagreement at
r = 0.87), but every combiner so far read it only after decoding. Here the denoiser gets it as
input: at every position of row k, a learned projection of

  the mean embedding of the K-1 siblings' tokens there, and
  [share of siblings agreeing with row k, share of the position's majority]

is added to row k's input embeddings, for the last step only. LoRA adapts the decoder to use it.
The projections start at zero, so before training the model is exactly the base model.

Variants, identical in data, steps and parameters, differing only in what the extra input holds:
  peer   the K-1 siblings of the same utterance              (the method)
  self   row k's own previous tokens, nothing from siblings  (classic self-conditioning)
  shuf   K-1 rows of a different utterance                   (is it information or capacity?)
  plain  nothing; LoRA trained on the same last-step task    (in-domain fine-tuning)
"""

from __future__ import annotations

import torch
from torch import nn

SCHEDULE = [1.0, 0.9, 0.85, 0.8]
BRANCH = [1, 2, 8, 8]
MODES = ("peer", "self", "shuf", "plain")


def embedding_module(model):
    """The decoder's token embedding: transformer.wte in lit_gpt, else the largest nn.Embedding."""
    tr = getattr(model, "transformer", None)
    if tr is not None and isinstance(getattr(tr, "wte", None), nn.Embedding):
        return "transformer.wte", tr.wte
    name, best = max(((n, m) for n, m in model.named_modules() if isinstance(m, nn.Embedding)),
                     key=lambda nm: nm[1].num_embeddings)
    return name, best


class PeerInjector(nn.Module):
    """Adds the projected peer features to the embedding output while .add is set."""

    def __init__(self, model, mode: str):
        super().__init__()
        assert mode in MODES
        self.mode = mode
        self.emb_name, self.emb = embedding_module(model)
        d = self.emb.embedding_dim
        self.proj = nn.Linear(d, d, bias=False)
        self.agree = nn.Linear(2, d, bias=False)
        nn.init.zeros_(self.proj.weight)
        nn.init.zeros_(self.agree.weight)
        self.add = None
        self.hook = self.emb.register_forward_hook(self._hook)

    def _hook(self, mod, inp, out):
        if self.add is None or self.add.shape != out.shape:
            return out
        return out + self.add.to(out.dtype)

    def features(self, rows, own, peers):
        """rows: indices into the batch; own (B, L) the row's previous tokens; peers (B, K-1, L)
        the tokens the extra input describes. Returns (B, L, D) to add, in float32."""
        if self.mode == "plain":
            return None
        E = self.emb.weight
        d = E.shape[1]
        if self.mode == "self":
            mean = torch.nn.functional.layer_norm(E[own].float(), (d,))
            ag = torch.zeros(own.shape + (2,), device=own.device)
        else:
            # normalised: an unscaled mean embedding blew up the peer variant in run 1 (step 500)
            mean = torch.nn.functional.layer_norm(E[peers].float().mean(1), (d,))
            same = (peers == own[:, None, :]).float().mean(1)
            allk = torch.cat([own[:, None, :], peers], 1)
            # share of the position's majority token among all K rows
            maj = (allk[:, :, None, :] == allk[:, None, :, :]).float().mean(2).max(1).values
            ag = torch.stack([same, maj], -1)
        return self.proj(mean) + self.agree(ag)

    def state(self):
        return {k: v.detach().cpu() for k, v in self.state_dict().items() if not k.startswith("emb.")}

    def load(self, sd):
        missing = self.load_state_dict(sd, strict=False)
        bad = [k for k in missing.missing_keys if not k.startswith("emb.")]
        if bad:
            raise RuntimeError(f"injector keys missing: {bad}")


@torch.no_grad()
def first_steps(wf, cond, seed: int, n_steps: int = 3, seq_len: int = 256):
    """Tree-early PDD up to (not including) the last step, exactly as decode.pdd_decode does it
    with branch_schedule BRANCH and uniform masks. Returns (rows after n_steps, generator) so the
    last step can draw the same mask pdd_decode would."""
    dev = wf.device
    gen = torch.Generator(device=dev)
    gen.manual_seed(seed)
    bos = wf.tokenizer.bos_token_id
    bos = 0 if bos is None else bos
    rows = BRANCH[0]
    cur = torch.full((rows, seq_len), wf.mask_token_id, dtype=torch.long, device=dev)
    cur[:, 0] = bos
    for step in range(n_steps):
        want = BRANCH[step]
        if want > rows:
            idx = torch.arange(want, device=dev) % rows if want % rows else None
            cur = cur[idx] if idx is not None else cur.repeat_interleave(want // rows, dim=0)
        rows = want
        r = torch.rand((rows, seq_len), device=dev, generator=gen)
        m = r < SCHEDULE[step]
        m[:, 0] = False
        masked = cur.clone()
        masked[m] = wf.mask_token_id
        logits = wf.model(idx=masked, condition=cond.expand(rows, -1, -1))
        cur = torch.where(m, logits.argmax(-1), masked)
    return cur, gen


def last_mask(cur, gen, step: int = 3):
    r = torch.rand(cur.shape, device=cur.device, generator=gen)
    m = r < SCHEDULE[step]
    m[:, 0] = False
    return m


def align_targets(hyp, ref, pad, ignore=-100):
    """Reference tokens placed on the hypothesis' positions, where the two correspond one to one.

    The last step keeps the row's unmasked tokens and predicts the masked ones in place, so a
    target is only meaningful at a position whose hypothesis token has a reference counterpart:
    equal tokens and same-length substitutions. Insertions, deletions and length-changing
    substitutions get `ignore`. Run 1 used the reference unaligned and taught the step to write
    the reference shifted against the kept tokens, which broke every word after the first shift.
    hyp, ref: 1-D LongTensors of the full padded length L (position 0 = BOS)."""
    from rapidfuzz.distance import Levenshtein
    L = hyp.shape[0]
    h = hyp.tolist()
    r = ref.tolist()
    nh = next((i for i in range(1, L) if h[i] == pad), L)
    nr = next((i for i in range(1, L) if r[i] == pad), L)
    out = [ignore] * L
    for tag, i1, i2, j1, j2 in Levenshtein.opcodes(h[:nh], r[:nr]):
        if tag in ("equal", "replace") and i2 - i1 == j2 - j1:
            for d in range(i2 - i1):
                out[i1 + d] = r[j1 + d]
    for i in range(max(nh, nr), L):        # both already ended: the step must keep the length
        out[i] = pad
    return torch.tensor(out, dtype=torch.long, device=hyp.device)


def peer_tokens(cur, other=None):
    """(K, K-1, L): for each row, the other rows of the same utterance -- or, for the shuffled
    control, K-1 rows of a different utterance's state `other`."""
    k = cur.shape[0]
    src = cur if other is None else other
    idx = torch.tensor([[j for j in range(k) if j != i] for i in range(k)], device=cur.device)
    if other is not None and other.shape[0] != k:
        idx = idx % other.shape[0]
    return src[idx]
