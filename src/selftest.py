#!/usr/bin/env python3
"""Checks the compat shims, checkpoint keys, fp16 stability and RTF before a long run."""

from __future__ import annotations

import argparse
import itertools
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=".")
    ap.add_argument("--n_utts", type=int, default=5)
    ap.add_argument("--n_candidates", type=int, default=15)
    ap.add_argument("--device", default=None)
    ap.add_argument("--dtype", default="auto")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    work = Path(args.work)

    import torch

    import data as dataio
    import decode as dec
    import scorers as S
    import wf_compat
    import wf_model

    print("=" * 66)
    print("SELFTEST")
    print("=" * 66)
    print(f"torch {torch.__version__}  cuda={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        cap = torch.cuda.get_device_capability(0)
        print(f"GPU: {torch.cuda.get_device_name(0)}  compute capability {cap[0]}.{cap[1]}")
        if cap[0] < 8:
            print("     Turing/Pascal: no bf16, no FlashAttention 2 -> fp16 + SDPA")
    wf_compat.assert_no_cuda_ext()
    print("[1/5] compat shims OK")

    base = work / "ckpt/mdm_safetensors/mdm-170M-100e18-rsl-0.01.safetensors"
    adapter = work / "ckpt/whisfusion_stage2_decoder.pt"
    ls = work / "data/LibriSpeech/test-clean"
    for p in (base, adapter, ls):
        if not p.exists():
            print(f"MISSING: {p}  -> run setup.sh or attach the data")
            return 1

    wf = wf_model.load(str(base), str(adapter), device=args.device, dtype=args.dtype)
    print("[2/5] checkpoint loaded with no missing keys")

    utts = list(itertools.islice(dataio.iter_utterances("librispeech", str(ls)), args.n_utts))
    t0 = time.time()
    audio_s = 0.0
    picked, oracle = [], []
    identical = 0

    for u in utts:
        cond = wf_model.encode_audio(wf, dataio.load_audio(u.audio_path))
        if not torch.isfinite(cond).all():
            print("NaN/Inf out of the Whisper encoder -- fp16 overflow. Try --dtype fp32.")
            return 1
        r = dec.pdd_decode(wf, cond, n_candidates=args.n_candidates, n_steps=4, seed=0)
        identical += int(r.identical_after_step1)
        w = [100 * S.wer_pair(u.text, c.text) for c in r.candidates]
        pick = max(range(len(w)), key=lambda i: r.candidates[i].avg_conf)
        picked.append(w[pick])
        oracle.append(min(w))
        audio_s += u.duration_s
        print(f"  {u.id}  {u.duration_s:4.1f}s  WER {w[pick]:5.1f} "
              f"(oracle {min(w):5.1f}, {r.n_unique}/{len(w)} unique)")
        print(f"      REF {S.normalize(u.text)[:68]}")
        print(f"      HYP {S.normalize(r.candidates[pick].text)[:68]}")

    mean_picked = sum(picked) / len(picked)
    if mean_picked > 60:
        print(f"\n[!] WER {mean_picked:.1f} % is far too high -- wrong weights, wrong "
              "tokenizer, or fp16 instability. Do not start the full run.")
        return 1
    print("[3/5] fp16 stable, no NaN")
    print(f"[4/5] model transcribes: WER {mean_picked:.1f} %, "
          f"oracle {sum(oracle)/len(oracle):.1f} % over {len(utts)} utts "
          "(not statistically meaningful, just proof of life)")

    el = time.time() - t0
    rtf = el / max(audio_s, 1e-6)
    print(f"[5/5] RTF {rtf:.4f}  ({el:.0f} s for {audio_s:.0f} s of audio)")
    print(f"\nfull test-clean (5.4 h of audio) would take about {5.4 * rtf:.1f} h")
    if 5.4 * rtf > 8:
        print("  -> will not fit a 9 h session. Use --resume across runs, "
              "or lower --n_candidates.")

    print(f"\ncandidates identical after step 1: {identical}/{len(utts)}")
    if identical == len(utts):
        print("  -> expected: step 0 masks everything, so all K inputs are the same "
              "and the update is argmax. Diversity comes from the masks of steps 2-4. "
              "Try --first_step_sampling as an ablation.")

    print("\nOK, ready for dump_candidates.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
