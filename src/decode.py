"""Parallel Diffusion Decoding, returning all K candidates instead of the winner.

Step 0 masks everything and the update is argmax, so all K candidates are identical after
it; divergence comes from the masks of later steps. first_step_sampling samples there.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import torch

DEFAULT_SCHEDULE = [1.0, 0.9, 0.85, 0.8]
WORD_START = "\u2581"  # SentencePiece word boundary


def _word_confidences(tokenizer, ids, confs, text) -> list[float] | None:
    """Mean confidence per normalised word, or None if it will not line up."""
    from scorers import normalize

    special = set(tokenizer.all_special_ids)
    pairs = [(i, c) for i, c in zip(ids, confs) if i not in special]
    if not pairs:
        return None
    keep_ids, keep_conf = zip(*pairs)
    pieces = tokenizer.convert_ids_to_tokens(list(keep_ids))

    words, buf, cur = [], [], []
    for piece, c in zip(pieces, keep_conf):
        if piece.startswith(WORD_START) and buf:
            words.append(("".join(buf), cur))
            buf, cur = [], []
        buf.append(piece.lstrip(WORD_START))
        cur.append(float(c))
    if buf:
        words.append(("".join(buf), cur))

    out = [sum(cs) / len(cs) for w, cs in words if normalize(w)]
    return out if len(out) == len(normalize(text).split()) else None


@dataclass
class Candidate:
    text: str
    avg_conf: float  # upstream selection metric: mean max-prob over non-pad positions
    min_conf: float
    median_conf: float
    mean_logprob: float
    mean_entropy: float
    n_tokens: int
    word_conf: list[float] | None = field(default=None)
    tokens: list[int] | None = field(default=None)


@dataclass
class DecodeResult:
    candidates: list[Candidate]
    n_unique: int
    identical_after_step1: bool
    n_candidates_used: int = 0      # differs from the request only when adaptive is on
    uncertainty: float | None = None  # mean (1 - max prob) at the probe step, if measured
    branch_widths: list[int] | None = None   # rows actually decoded at each step


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
    branch_schedule: list[int] | None = None,
    mask_mode: str = "uniform",
    adaptive: dict | None = None,
) -> DecodeResult:
    """branch_schedule gives the number of distinct mask groups at each step.

    Flat sampling is every candidate drawing its own mask at every step, which is
    branch_schedule = [K, K, K, K] and is what None means. A tree shares masks early and
    splits later: [1, 4, 32, 32] decodes one row, then four, then thirty-two, so siblings
    carry a common prefix. Rows are only materialised when they split, so a narrow early
    schedule is also cheaper, not just more correlated.

    mask_mode "uncertain" draws the mask with probability proportional to 1 - confidence
    from the previous step instead of uniformly, keeping the same expected mask ratio, so
    re-prediction is spent where the model is unsure rather than spread evenly.

    adaptive sizes the whole tree per utterance: after probe_step the width is set from how
    uncertain the shared prefix is, so an easy utterance gets a small tree and a hard one a
    large tree. dict(base, u0, gamma, k_min, k_max, probe_step); K = base * (u/u0) ** gamma.
    """
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

    widths = list(branch_schedule) if branch_schedule else [n_candidates] * n_steps
    widths = [max(1, int(w)) for w in widths[:n_steps]]
    widths += [widths[-1]] * (n_steps - len(widths))
    probe = int((adaptive or {}).get("probe_step", 1))

    rows = widths[0]
    cur = torch.full((rows, seq_len), mask_id, dtype=torch.long, device=device)
    cur[:, 0] = bos

    final_logits = None
    after_step1 = None
    conf_prev = None
    uncertainty = None
    used = []

    for step in range(n_steps):
        ratio = schedule[step] if step < len(schedule) else 0.7

        want = widths[step]
        if want > rows:                       # split: every parent takes the same children
            idx = torch.arange(want, device=device) % rows if want % rows else None
            cur = cur[idx] if idx is not None else cur.repeat_interleave(want // rows, dim=0)
            if conf_prev is not None:
                conf_prev = conf_prev[idx] if idx is not None else \
                    conf_prev.repeat_interleave(want // rows, dim=0)
        elif want < rows:                     # prune, which is how adaptive width shrinks
            cur = cur[:want]                  # rows are interchangeable at the probe step
            if conf_prev is not None:
                conf_prev = conf_prev[:want]
        rows = want
        used.append(rows)
        cond = condition.expand(rows, -1, -1)

        if ratio <= 0:
            mask_idx = torch.zeros((rows, seq_len), dtype=torch.bool, device=device)
        elif mask_mode == "uncertain" and conf_prev is not None:
            # Mask exactly as many positions as the uniform draw would, but choose them by
            # weighted sampling WITHOUT replacement. The first version scaled a per-position
            # probability, which at a high mask ratio pinned the low-confidence positions to
            # p = 1: they were re-masked every step, never accumulated context and never
            # settled, and WER came out four times worse. Sampling a fixed count keeps the
            # budget identical to flat and still leaves every position a chance to be spared.
            n_mask = int(round(ratio * (seq_len - 1)))
            w = (1.0 - conf_prev).clamp_min(1e-6)
            w = torch.cat([torch.zeros_like(w[:, :1]), w[:, 1:]], dim=1)   # never the BOS slot
            mask_idx = torch.zeros((rows, seq_len), dtype=torch.bool, device=device)
            if n_mask > 0:
                pick = torch.multinomial(w, min(n_mask, seq_len - 1),
                                         replacement=False, generator=gen)
                mask_idx.scatter_(1, pick, True)
        else:
            r = torch.rand((rows, seq_len), device=device, generator=gen)
            mask_idx = r < ratio
            mask_idx[:, 0] = False

        masked = cur.clone()
        masked[mask_idx] = mask_id

        logits = wf.model(idx=masked, condition=cond)

        if step == 0 and first_step_sampling:
            probs = torch.softmax(logits.float() / temperature, dim=-1)
            pred = torch.multinomial(probs.view(-1, probs.size(-1)), 1,
                                     generator=gen).view(rows, seq_len)
        else:
            pred = torch.argmax(logits, dim=-1)

        cur = torch.where(mask_idx, pred, masked)
        if mask_mode == "uncertain" or adaptive is not None:
            conf_prev = torch.softmax(logits.float(), dim=-1).max(dim=-1).values

        if adaptive is not None and step == probe and uncertainty is None:
            a = adaptive
            uncertainty = float((1.0 - conf_prev).mean())
            # base is the TARGET MEAN width, not a ceiling, and u0 is the measured median
            # uncertainty (0.021 over three sets), not a guess. The first version used
            # u0 = 0.15, about seven times too high, so every utterance clipped to k_min.
            k = a.get("base", n_candidates) * (uncertainty / a.get("u0", 0.021)) ** a.get("gamma", 1.0)
            k = int(min(max(round(k), a.get("k_min", 2)), a.get("k_max", n_candidates)))
            scale = k / max(n_candidates, 1)
            for s in range(step + 1, n_steps):       # re-aim the rest of the tree at k
                widths[s] = max(1, min(k, round(widths[s] * scale)))
            widths[n_steps - 1] = k

        if step == 0:
            after_step1 = bool((cur == cur[0:1]).all().item())
        if step == n_steps - 1:
            final_logits = logits

    n_candidates = cur.size(0)

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
        ids = toks[i][v].tolist()
        cands.append(
            Candidate(
                text=texts[i],
                avg_conf=float(c.mean()),
                min_conf=float(c.min()),
                median_conf=float(c.median()),
                mean_logprob=float(logprob[i][v].mean()),
                mean_entropy=float(entropy[i][v].mean()),
                n_tokens=int(v.sum()),
                word_conf=_word_confidences(wf.tokenizer, ids, c.tolist(), texts[i]),
                tokens=ids if save_tokens else None,
            )
        )

    return DecodeResult(
        candidates=cands,
        n_unique=len({c.text for c in cands}),
        identical_after_step1=bool(after_step1),
        n_candidates_used=len(cands),
        uncertainty=uncertainty,
        branch_widths=used,
    )


def candidate_to_dict(c: Candidate) -> dict:
    d = asdict(c)
    for key in ("tokens", "word_conf"):
        if d[key] is None:
            d.pop(key)
    return d
