#!/usr/bin/env python3
"""Per-word acoustic scores for every candidate, folded into the same confusion network.

The whole-path likelihood (tools/pll_rescore.py) carries information the vote does not --
partial Spearman 0.2-0.3 after controlling for agreement on three sets -- but it cannot turn
that into a better pick among ~34 whole transcripts. A slot is a different problem: two to
five words, one decision, the evidence right there. So the same acoustic signal is brought
down to the word, and the slot model gets it as one more feature.

The acoustic score is the decoder's step-zero reading of the audio: everything masked, one
forward pass per utterance, so the input does not depend on any candidate and there is no
context leak. Each candidate's words are then scored by the log-probability that reading
gives their tokens at the positions the candidate puts them, optionally allowing the token to
sit up to --window positions away (a candidate with one extra word early shifts everything
after it, and the step-zero reading has no way to know).

The per-word scores go through compose.confusion_network exactly like the word confidences
do, so every slot word ends up with [votes, summed acoustic score] beside its [votes, summed
confidence], on the identical network. The record format is the one calibrate_rover.py
writes, plus `aslots_w0` / `aslots_w<window>`, so slot_eval.py reads either.

    PYTHONPATH=src:Whisfusion/src:tools python3 tools/audio_slots.py \\
        --data data --dumps_root results/campaign-2026-09-20/dumps --per_set 120
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")

SETS = ["ls-dev-clean", "ls-dev-other", "ls-test-clean", "ls-test-other", "ami", "earnings22",
        "voxpopuli", "gigaspeech", "spgispeech", "common_voice", "ls-tc-babble5",
        "ls-tc-babble0", "ls-tc-white5"]


def acoustic_reading(wf, cond, seq_len):
    """log p(token at position | audio) for every position, from one fully masked pass."""
    import torch
    bos = wf.tokenizer.bos_token_id
    probe = torch.full((1, seq_len), wf.mask_token_id, dtype=torch.long, device=wf.device)
    probe[0, 0] = 0 if bos is None else bos
    with torch.no_grad():
        logits = wf.model(idx=probe, condition=cond)
    return torch.log_softmax(logits[0].float(), dim=-1)          # (seq_len, vocab)


def word_scores(wf, lp, text, window):
    """Mean token log-prob per normalised word of one candidate, or None if it will not line up."""
    import torch
    import decode as dec
    ids = wf.tokenizer(text, add_special_tokens=False)["input_ids"][: lp.size(0) - 1 - window]
    if not ids:
        return None
    t = torch.tensor(ids, dtype=torch.long)
    pos = torch.arange(1, len(ids) + 1)
    best = None
    for s in range(-window, window + 1):
        q = (pos + s).clamp(1, lp.size(0) - 1)
        v = lp[q, t]
        best = v if best is None else torch.maximum(best, v)
    return dec._word_confidences(wf.tokenizer, ids, best.tolist(), text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="prep_data output with manifests/")
    ap.add_argument("--dumps_root", required=True)
    ap.add_argument("--model", default="whisfusion")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--shard", default="s00", help="comma separated, e.g. s00,s01")
    ap.add_argument("--sets", default=",".join(SETS))
    ap.add_argument("--per_set", type=int, default=120)
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--window", type=int, default=2)
    ap.add_argument("--seq_len", type=int, default=256)
    ap.add_argument("--out", default="results/audio_cache.pkl")
    a = ap.parse_args()

    import compose
    import data as dataio
    import decompose as D
    import wf_model
    from campaign.families import Whisfusion
    from scorers import normalize

    out_p = Path(a.out)
    out = pickle.loads(out_p.read_bytes()) if out_p.exists() else []
    seen = {(r["set"], r["id"]) for r in out}
    print(f"resuming with {len(out)} utterances" if out else "fresh cache", flush=True)

    wf = Whisfusion({}).wf
    windows = sorted({0, a.window})
    t0, done_now, dropped = time.time(), 0, 0
    for s in [x for x in a.sets.split(",") if x]:
        dumps = [Path(a.dumps_root) / f"{a.model}__{s}__{sh}__{a.arm}" / f"{a.arm}.jsonl.gz"
                 for sh in a.shard.split(",") if sh]
        dumps = [d for d in dumps if d.exists()]
        man = Path(a.data) / "manifests" / f"{s}.jsonl"
        if not dumps or not man.exists():
            print(f"[{s}] skipped: {'no dump' if not dumps else 'no manifest'}", flush=True)
            continue
        rows = {}
        for dump in dumps:
            with gzip.open(dump, "rt", encoding="utf-8") as fh:
                for line in fh:
                    d = json.loads(line)
                    rows[d["id"]] = d
        have = sum(1 for r in out if r["set"] == s)
        for u in dataio.iter_manifest(str(man)):
            if have >= a.per_set:
                break
            row = rows.get(u.id)
            if row is None or (s, u.id) in seen:
                continue
            raw = row["candidates"][: a.k]
            cands = [normalize(c["text"]).split() for c in raw]
            ref = normalize(row["reference"]).split()
            if not ref:
                continue
            cond = wf_model.encode_audio(wf, dataio.load_audio(u.audio_path))
            lp = acoustic_reading(wf, cond, a.seq_len)
            aud = {w: [] for w in windows}
            keep = []
            for i, (words, c) in enumerate(zip(cands, raw)):
                if not words or "word_conf" not in c or len(c["word_conf"]) != len(words):
                    continue
                per = {w: word_scores(wf, lp, c["text"], w) for w in windows}
                if any(v is None or len(v) != len(words) for v in per.values()):
                    continue
                keep.append(i)
                for w in windows:
                    aud[w].append([math.exp(x) for x in per[w]])
            if len(keep) < 2:
                dropped += 1
                continue
            cands = [cands[i] for i in keep]
            confs = [list(raw[i]["word_conf"]) for i in keep]
            bb = compose.central_index(cands)
            by_slot = D.reference_by_slot(cands, bb, ref)
            slots = compose.confusion_network(cands, bb, confs, None)
            if len(by_slot) != len(slots):
                dropped += 1
                continue
            rec = dict(set=s, id=u.id, cluster=row.get("cluster") or u.id, n_cand=len(cands),
                       ref=ref, ref_by_slot=by_slot,
                       slots=[{w: list(v) for w, v in sl.items()} for sl in slots])
            for w in windows:
                asl = compose.confusion_network(cands, bb, aud[w], None)
                rec[f"aslots_w{w}"] = [{x: list(v) for x, v in sl.items()} for sl in asl]
            out.append(rec)
            seen.add((s, u.id))
            have += 1
            done_now += 1
            if done_now % 25 == 0:
                out_p.write_bytes(pickle.dumps(out))
                print(f"  {len(out)} cached ({s}: {have}), "
                      f"{(time.time() - t0) / done_now:.1f} s each", flush=True)
        out_p.write_bytes(pickle.dumps(out))
        print(f"[{s}] {have} utterances", flush=True)
    print(f"done: {len(out)} utterances, {dropped} dropped (tokenisation did not line up)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
