#!/usr/bin/env python3
"""Autoregressive Whisper on the same utterances, as the reference row of the paper.

Whisfusion reuses Whisper-small's encoder, so Whisper-small itself is the obvious question:
how far is a parallel diffusion decoder plus composition from the model it was built on?
Batch 1, greedy, English, timed per utterance (encoder + decoding) on the same GPU.

    python3 tools/whisper_ref.py --data /tmp/campaign_data --sets ami,earnings22 --shard 2 \\
        --out results/whisper_small_s02.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--sets", required=True)
    ap.add_argument("--shard", type=int, default=2)
    ap.add_argument("--shard_size", type=int, default=200)
    ap.add_argument("--model", default="openai/whisper-small")
    ap.add_argument("--beams", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    import data as dataio

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if dev == "cuda" else torch.float32
    proc = WhisperProcessor.from_pretrained(a.model)
    model = WhisperForConditionalGeneration.from_pretrained(a.model, torch_dtype=dtype).to(dev).eval()

    def sync():
        if dev == "cuda":
            torch.cuda.synchronize()

    import numpy as np
    warm = proc(np.zeros(16000, np.float32), sampling_rate=16000, return_tensors="pt").input_features
    with torch.no_grad():  # first call compiles kernels; keep it out of the timings
        model.generate(warm.to(dev, dtype), language="en", task="transcribe", max_new_tokens=5)

    out_p = Path(a.out)
    done = set()
    if out_p.exists():
        done = {(r["set"], r["id"]) for r in map(json.loads, out_p.read_text().splitlines())}
    fh = out_p.open("a")
    n, t0 = 0, time.time()
    for s in [x for x in a.sets.split(",") if x]:
        rows = [json.loads(l) for l in open(Path(a.data) / "manifests" / f"{s}.jsonl")]
        rows = rows[a.shard * a.shard_size:(a.shard + 1) * a.shard_size]
        for r in rows:
            if (s, r["id"]) in done:
                continue
            audio = dataio.load_audio(r["audio"])
            feats = proc(audio, sampling_rate=16000, return_tensors="pt").input_features.to(dev, dtype)
            sync()
            t = time.time()
            with torch.no_grad():
                ids = model.generate(feats, language="en", task="transcribe", num_beams=a.beams,
                                     max_new_tokens=200)
            sync()
            sec = time.time() - t
            hyp = proc.batch_decode(ids, skip_special_tokens=True)[0].strip()
            fh.write(json.dumps(dict(set=s, id=r["id"], shard=a.shard, lang=r.get("lang", "en"),
                                     ref_text=r["text"], hyp=hyp, sec=sec,
                                     model=a.model, beams=a.beams)) + "\n")
            fh.flush()
            n += 1
            if n in (1, 10) or n % 200 == 0:
                print(f"  {n} utterances, {(time.time() - t0) / n:.2f} s each", flush=True)
    print(f"done: {n} new utterances")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
