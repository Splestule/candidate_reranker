"""Per-word confidences from per-token ones, for tokenizers that mark word starts.

Whisper's byte-level BPE marks a word start with a leading "Ġ" (an encoded space); SentencePiece
uses "▁". Returns None when the grouping does not line up with the normalised words, so a
confidence is never attached to the wrong word; ROVER then votes by frequency alone.
"""

from __future__ import annotations

WORD_MARKERS = ("Ġ", "▁")          # "Ġ", "▁"


def word_conf_from_ids(tokenizer, ids: list[int], confs: list[float], text: str) -> list[float] | None:
    from scorers import normalize

    if not ids:
        return None
    pieces = tokenizer.convert_ids_to_tokens(list(ids))
    groups: list[tuple[list[str], list[float]]] = []
    for piece, c in zip(pieces, confs):
        if piece is None:
            continue
        starts = piece.startswith(WORD_MARKERS)
        if starts or not groups:
            groups.append(([piece], [float(c)]))
        else:
            groups[-1][0].append(piece)
            groups[-1][1].append(float(c))

    out = []
    for toks, cs in groups:
        try:
            word = tokenizer.convert_tokens_to_string(toks)
        except Exception:
            word = "".join(toks)
        # one group can still hold several normalised words ("5,000" -> "5000" is one, but
        # "--" between two words glued without a space is not); repeat its confidence
        for _ in normalize(word).split():
            out.append(sum(cs) / len(cs))
    return out if len(out) == len(normalize(text).split()) else None


def token_stats(text: str, probs: list[float], logprobs: list[float], entropies: list[float] | None,
                word_conf: list[float] | None, extra: dict | None = None) -> dict:
    """A candidate in the dump schema from its emitted tokens' probabilities."""
    import statistics

    if not probs:
        d = dict(text=text, avg_conf=0.0, min_conf=0.0, median_conf=0.0, mean_logprob=-20.0,
                 mean_entropy=0.0, n_tokens=0)
    else:
        d = dict(text=text,
                 avg_conf=float(sum(probs) / len(probs)),
                 min_conf=float(min(probs)),
                 median_conf=float(statistics.median(probs)),
                 mean_logprob=float(sum(logprobs) / len(logprobs)),
                 mean_entropy=float(sum(entropies) / len(entropies)) if entropies else 0.0,
                 n_tokens=len(probs))
    if word_conf is not None:
        d["word_conf"] = word_conf
    if extra:
        d.update(extra)
    return d
