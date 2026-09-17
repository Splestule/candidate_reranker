#!/usr/bin/env python3
"""What a candidate actually costs: wall clock and peak memory against K.

The encoder runs once per utterance whatever K is, so it is timed apart from decoding.
That split is the ceiling on what any branching scheme can save.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--librispeech", required=True, help="a split directory")
    ap.add_argument("--ks", default="1,3,5,10,15,20,30")
    ap.add_argument("--n_utts", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--n_steps", type=int, default=4)
    ap.add_argument("--seq_len", type=int, default=256)
    ap.add_argument("--dtype", default="auto")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))

    import torch

    import data as dataio
    import decode as dec
    import wf_model

    ks = [int(x) for x in args.ks.split(",")]
    wf = wf_model.load(args.base_model, args.adapter, dtype=args.dtype)
    cuda = wf.device == "cuda"

    utts = list(itertools.islice(
        dataio.iter_utterances("librispeech", args.librispeech), args.n_utts + args.warmup))
    audio = [(u, dataio.load_audio(u.audio_path)) for u in utts]
    warm, bench = audio[:args.warmup], audio[args.warmup:]
    total_audio = sum(u.duration_s for u, _ in bench)
    print(f"\n{len(bench)} utterances, {total_audio / 60:.1f} min of audio, "
          f"{args.warmup} warm-up\n")

    def sync():
        if cuda:
            torch.cuda.synchronize()

    rows = []
    for k in ks:
        for u, a in warm:
            dec.pdd_decode(wf, wf_model.encode_audio(wf, a), n_candidates=k,
                           n_steps=args.n_steps, seq_len=args.seq_len, seed=0)
        sync()
        if cuda:
            torch.cuda.reset_peak_memory_stats()

        t_enc = t_dec = 0.0
        for u, a in bench:
            sync(); t0 = time.time()
            cond = wf_model.encode_audio(wf, a)
            sync(); t1 = time.time()
            dec.pdd_decode(wf, cond, n_candidates=k, n_steps=args.n_steps,
                           seq_len=args.seq_len, seed=0)
            sync(); t2 = time.time()
            t_enc += t1 - t0
            t_dec += t2 - t1

        peak = torch.cuda.max_memory_allocated() / 2 ** 20 if cuda else 0.0
        rows.append({"k": k, "encode_s": t_enc, "decode_s": t_dec,
                     "total_s": t_enc + t_dec, "audio_s": total_audio,
                     "rtf": (t_enc + t_dec) / total_audio,
                     "rtf_decode": t_dec / total_audio, "peak_mb": peak})
        print(f"  k={k:<3} done  {t_enc + t_dec:6.1f} s", flush=True)

    base = next(r for r in rows if r["k"] == min(ks))
    print(f"\n{'k':<5}{'encode s':>10}{'decode s':>10}{'total s':>10}"
          f"{'RTF':>8}{'peak MB':>10}{'decode vs k=' + str(min(ks)):>16}")
    for r in rows:
        rel = r["decode_s"] / max(base["decode_s"], 1e-9)
        print(f"{r['k']:<5}{r['encode_s']:>10.1f}{r['decode_s']:>10.1f}"
              f"{r['total_s']:>10.1f}{r['rtf']:>8.4f}{r['peak_mb']:>10.0f}{rel:>15.2f}x")

    enc_share = 100.0 * base["encode_s"] / max(rows[-1]["total_s"], 1e-9)
    print(f"\nencoder is K-independent: at k={ks[-1]} it is {enc_share:.1f} % of the total, "
          "so no branching scheme can save more than the rest")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"n_utts": len(bench), "audio_s": total_audio, "rows": rows}, f, indent=2)
        print(f"written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
