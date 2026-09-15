"""Parallel Diffusion Decoding, returning all K candidates instead of the winner.

Step 0 masks everything and the update is argmax, so all K candidates are identical after
it; divergence comes from the masks of later steps. first_step_sampling samples there.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import torch

DEFAULT_SCHEDULE = [1.0, 0.9, 0.85, 0.8]


@dataclass
class Candidate:
    text: str
    avg_conf: float  # upstream selection metric: mean max-prob over non-pad positions
    min_conf: float
    median_conf: float
    mean_logprob: float
    mean_entropy: float
    n_tokens: int
    tokens: list[int] | None = field(default=None)


@dataclass
class DecodeResult:
    candidates: list[Candidate]
    n_unique: int
    identical_after_step1: bool


@torch.no_grad()
def pdd_decode(
    wf,
    condition: torch.Tensor,
    n_candidates: int = 15,
    n_steps: int = 4,
    mask_ratio_schedule: list[float] | None = None,
    seq_len: int = 256,
    first_step_sampling: bool = False,
    temperature: float = 1.0,
    save_tokens: bool = False,
    seed: int | None = None,
) -> DecodeResult:
    schedule = mask_ratio_schedule or DEFAULT_SCHEDULE
    device = wf.device
    mask_id = wf.mask_token_id
    pad_id = wf.pad_token_id

    gen = None
    if seed is not None:
        gen = torch.Generator(device=device)
        gen.manual_seed(seed)

    bos = wf.tokenizer.bos_token_id
    bos = 0 if bos is None else bos

    cur = torch.full((n_candidates, seq_len), mask_id, dtype=torch.long, device=device)
    cur[:, 0] = bos
    cond = condition.expand(n_candidates, -1, -1)

    final_logits = None
    after_step1 = None

    for step in range(n_steps):
        ratio = schedule[step] if step < len(schedule) else 0.7

        if ratio > 0:
            r = torch.rand((n_candidates, seq_len), device=device, generator=gen)
            mask_idx = r < ratio
            mask_idx[:, 0] = False
        else:
            mask_idx = torch.zeros((n_candidates, seq_len), dtype=torch.bool, device=device)

        masked = cur.clone()
        masked[mask_idx] = mask_id

        logits = wf.model(idx=masked, condition=cond)

        if step == 0 and first_step_sampling:
            probs = torch.softmax(logits.float() / temperature, dim=-1)
            pred = torch.multinomial(probs.view(-1, probs.size(-1)), 1,
                                     generator=gen).view(n_candidates, seq_len)
        else:
            pred = torch.argmax(logits, dim=-1)

        cur = torch.where(mask_idx, pred, masked)

        if step == 0:
            after_step1 = bool((cur == cur[0:1]).all().item())
        if step == n_steps - 1:
            final_logits = logits

    probs = torch.softmax(final_logits.float(), dim=-1)
    conf = probs.max(dim=-1).values
    logprob = torch.log(
        probs.gather(-1, cur.clamp(max=probs.size(-1) - 1).unsqueeze(-1)).squeeze(-1) + 1e-9
    )
    entropy = -(probs * torch.log(probs + 1e-9)).sum(-1)
    del probs, final_logits

    toks = cur.cpu()
    conf, logprob, entropy = conf.cpu(), logprob.cpu(), entropy.cpu()
    texts = wf.tokenizer.batch_decode(toks, skip_special_tokens=True)
    valid = toks != pad_id

    cands = []
    for i in range(n_candidates):
        v = valid[i]
        if int(v.sum()) == 0:
            v = torch.ones_like(v)
        c = conf[i][v]
        cands.append(
            Candidate(
                text=texts[i],
                avg_conf=float(c.mean()),
                min_conf=float(c.min()),
                median_conf=float(c.median()),
                mean_logprob=float(logprob[i][v].mean()),
                mean_entropy=float(entropy[i][v].mean()),
                n_tokens=int(v.sum()),
                tokens=toks[i][v].tolist() if save_tokens else None,
            )
        )

    return DecodeResult(
        candidates=cands,
        n_unique=len({c.text for c in cands}),
        identical_after_step1=bool(after_step1),
    )


def candidate_to_dict(c: Candidate) -> dict:
    d = asdict(c)
    if d["tokens"] is None:
        d.pop("tokens")
    return d
