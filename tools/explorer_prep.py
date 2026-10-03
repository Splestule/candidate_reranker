#!/usr/bin/env python3
"""Where does composition need help? Labels for training the vote explorer.

Decodes LibriSpeech train-clean-100 utterances with the anchor exactly as at inference
(K candidates, flat PDD), builds the confusion network over them and aligns the reference to
it. Every reference word gets the anchor's vote share for itself and for each competitor in
its slot, and a class:

  maj   the anchor already outvotes every competitor: the explorer must not get in the way
  min   the word is in the network but loses the vote: the explorer should add votes
  hole  the word is not in the network at all: only the explorer can bring it

Each word is located by its first token in the reference tokenisation (the training target),
so the training loss can read the explorer's probability for it at that position.

    python3 tools/explorer_prep.py --utts 8000 --out results/explorer2/labels.pkl
"""

from __future__ import annotations

import argparse
import io
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")


def files(n_shards):
    from huggingface_hub import hf_hub_download
    return [hf_hub_download("openslr/librispeech_asr", f"all/train.clean.100/{i:04d}.parquet",
                            repo_type="dataset") for i in range(n_shards)]


def rows(paths, skip_first=0):
    """Deterministic order over the shards; the first skip_first rows of the last shard are
    the held-out diagnostics of tools/train_explorer.py and never appear here."""
    import pyarrow.parquet as pq
    for n, p in enumerate(paths):
        t = pq.read_table(p, columns=["audio", "text", "id"])
        for i, r in enumerate(t.to_pylist()):
            if n == len(paths) - 1 and i < skip_first:
                continue
            yield r


def first_tokens(tok, text):
    """Index of the first token of every whitespace word in the padded training target."""
    enc = tok(text, return_offsets_mapping=True, max_length=256, truncation=True)
    offs = enc["offset_mapping"]
    starts, pos = [], 0
    for w in text.split(" "):
        if w:
            starts.append(pos)
        pos += len(w) + 1
    out, j = [], 1                       # position 0 is BOS
    for s in starts:
        while j < len(offs) and offs[j][1] <= s:
            j += 1
        out.append(j if j < len(offs) else None)
    return out, enc["input_ids"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--utts", type=int, default=8000)
    ap.add_argument("--shards", type=int, default=5)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--val_utts", type=int, default=256)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import soundfile as sf
    import compose
    import decompose as D
    from campaign.families import Whisfusion
    from scorers import normalize
    EPS = D.EPS

    fam = Whisfusion({})
    tok = fam.wf.tokenizer
    out_p = Path(a.out)
    out = pickle.loads(out_p.read_bytes()) if out_p.exists() else {}
    stats = {"maj": 0, "min": 0, "hole": 0, "unaligned": 0}
    t0, n = time.time(), 0
    for r in rows(files(a.shards), a.val_utts):
        if len(out) >= a.utts:
            break
        if r["id"] in out:
            continue
        audio = sf.read(io.BytesIO(r["audio"]["bytes"]), dtype="float32")[0]
        enc = fam.encode(audio, "en")
        cands, _ = fam.decode(enc, {"K": a.k, "steps": 4}, seed=n, lang="en")
        words = [normalize(c["text"]).split() for c in cands]
        ref = normalize(r["text"]).split()
        if not ref or not any(words):
            continue
        bb = compose.central_index(words)
        slots = compose.confusion_network(words, bb, None, None)
        by_slot = D.reference_by_slot(words, bb, ref)
        if len(by_slot) != len(slots):
            continue
        ftok, ids = first_tokens(tok, r["text"])
        labels = []
        j = 0
        for slot, rw in zip(slots, by_slot):
            if rw == EPS:
                continue
            while j < len(ref) and ref[j] != rw:
                j += 1
            if j >= len(ref):
                break
            pos = ftok[j] if j < len(ftok) else None
            j += 1
            if pos is None:
                stats["unaligned"] += 1
                continue
            tot = sum(v[0] for v in slot.values())
            share = {w: v[0] / tot for w, v in slot.items()}
            mine = share.get(rw, 0.0)
            comp = [(w, s) for w, s in share.items() if w != rw]
            best = max([s for _, s in comp], default=0.0)
            cls = "hole" if mine == 0 else ("maj" if mine > best else "min")
            stats[cls] += 1
            # competitors as first token of the word in the model's own casing; EPS has none
            comp_t = [(None if w == EPS else tok(w.upper(), add_special_tokens=False)["input_ids"][0], s)
                      for w, s in comp]
            labels.append((pos, ids[pos], mine, comp_t, cls))
        out[r["id"]] = labels
        n += 1
        if n in (1, 10) or n % 250 == 0:
            tot = max(sum(stats[c] for c in ("maj", "min", "hole")), 1)
            print(f"  {len(out)} utterances, {(time.time() - t0) / n:.2f} s each; words "
                  + ", ".join(f"{c} {100 * stats[c] / tot:.1f}%" for c in ("maj", "min", "hole"))
                  + f", unaligned {stats['unaligned']}", flush=True)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_bytes(pickle.dumps(out))
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_bytes(pickle.dumps(out))
    print(f"done: {len(out)} utterances, {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
