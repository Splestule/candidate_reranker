#!/usr/bin/env python3
"""Run PDD over a dataset and write every candidate to JSONL.

Writes incrementally; --resume picks up where a killed session left off.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="librispeech", choices=["librispeech", "manifest"])
    ap.add_argument("--path", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base_model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--tag", default=None)

    ap.add_argument("--n_candidates", type=int, default=15)
    ap.add_argument("--n_steps", type=int, default=4)
    ap.add_argument("--seq_len", type=int, default=256)
    ap.add_argument("--schedule", default="1.0,0.9,0.85,0.8")

    ap.add_argument("--first_step_sampling", action="store_true",
                    help="sample instead of argmax in step 0; see decode.py")
    ap.add_argument("--temperature", type=float, default=1.0)

    ap.add_argument("--max_utts", type=int, default=None)
    ap.add_argument("--max_seconds", type=float, default=None)
    ap.add_argument("--save_tokens", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dtype", default="auto", choices=["auto", "fp16", "bf16", "fp32"])
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import data as dataio
    import decode as dec
    import wf_model

    schedule = [float(x) for x in args.schedule.split(",")]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    done: set[str] = set()
    if args.resume and out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["id"])
                except Exception:
                    pass
        print(f"[resume] {len(done)} utterances already done")

    wf = wf_model.load(args.base_model, args.adapter, device=args.device, dtype=args.dtype)

    tag = args.tag or Path(args.path).name
    n = skipped = 0
    audio_s = 0.0
    t0 = time.time()

    mode = "a" if (args.resume and out_path.exists()) else "w"
    with open(out_path, mode, encoding="utf-8") as fout:
        for u in dataio.iter_utterances(args.source, args.path):
            if args.max_utts is not None and n >= args.max_utts:
                break
            if u.id in done:
                continue
            if args.max_seconds is not None and u.duration_s > args.max_seconds:
                skipped += 1
                continue

            try:
                cond = wf_model.encode_audio(wf, dataio.load_audio(u.audio_path))
                res = dec.pdd_decode(
                    wf, cond,
                    n_candidates=args.n_candidates,
                    n_steps=args.n_steps,
                    mask_ratio_schedule=schedule,
                    seq_len=args.seq_len,
                    first_step_sampling=args.first_step_sampling,
                    temperature=args.temperature,
                    save_tokens=args.save_tokens,
                    seed=args.seed + n,
                )
            except Exception as e:
                # One bad file must not take down an overnight run.
                print(f"[!] {u.id}: {type(e).__name__}: {e}")
                continue

            fout.write(json.dumps({
                "id": u.id,
                "dataset": tag,
                "duration_s": round(u.duration_s, 3),
                "reference": u.text,
                "n_unique": res.n_unique,
                "identical_after_step1": res.identical_after_step1,
                "candidates": [dec.candidate_to_dict(c) for c in res.candidates],
            }, ensure_ascii=False) + "\n")

            n += 1
            audio_s += u.duration_s
            if n % 25 == 0:
                fout.flush()
                el = time.time() - t0
                print(f"  {n} utts · {el/60:.1f} min · {el/n:.2f} s/utt · "
                      f"RTF {el/max(audio_s,1e-6):.3f}", flush=True)

    el = time.time() - t0
    print(f"\ndone: {n} utterances ({audio_s/60:.1f} min audio) in {el/60:.1f} min")
    if audio_s:
        print(f"RTF {el/audio_s:.4f} -> 1 h of audio costs {el/audio_s*60:.1f} min")
    if skipped:
        print(f"skipped by --max_seconds: {skipped}")
    print(f"written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
