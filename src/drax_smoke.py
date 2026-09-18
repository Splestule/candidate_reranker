#!/usr/bin/env python3
"""Does the composition gap exist in a second model, from a different generative family?

Drax is discrete flow matching, not masked diffusion, and it is a much stronger model
(2.6 vs our 8.2 WER on test-clean). Its paper samples several candidates and selects one
by a score function, which is the thing this project argues against.

Deliberately self-contained: it only uses Drax's public Transcriber API, so nothing here
depends on their internals. No per-token confidences, so the baseline is MBR rather than
mean confidence -- which is the comparison that matters anyway.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
import statistics
import sys
import time
from pathlib import Path

from rapidfuzz.distance import Levenshtein


def summarise(rows: list[dict], seed: int = 0) -> dict:
    """MBR, ROVER, both oracles and the shuffled control over one set of dumps."""
    import compose
    import scorers as S

    rng = random.Random(seed)
    pool = [w for r in rows[:200] for w in S.normalize(r["candidates"][0]["text"]).split()]

    tot_ref = 0
    edits = {k: 0 for k in ["mbr", "rover", "oracle_cand", "oracle_comp", "control"]}
    uniq, pair = [], []

    for row in rows:
        ref = S.normalize(row["reference"]).split()
        cands, _ = compose.prepare(row)
        k = len(cands)

        wers = [Levenshtein.distance(ref, c) for c in cands]
        mbr = S.s_mbr_wer(row["candidates"])
        slots = compose.confusion_network(cands, compose.central_index(cands))

        best_single = min(wers)
        picks = {
            "mbr": Levenshtein.distance(ref, cands[max(range(k), key=lambda i: mbr[i])]),
            "rover": Levenshtein.distance(ref, compose.rover(slots, float(k), 1.0, 0.5)),
            "oracle_cand": best_single,
            "oracle_comp": min(compose.oracle_path(slots, ref), best_single),
            "control": min(compose.oracle_path(
                compose.shuffled_control(slots, pool, rng), ref), best_single),
        }
        for key, e in picks.items():
            edits[key] += e
        tot_ref += len(ref)

        uniq.append(len({" ".join(c) for c in cands}))
        d = [Levenshtein.distance(cands[i], cands[j]) / max(len(cands[i]), len(cands[j]), 1)
             for i in range(k) for j in range(i + 1, k)]
        pair.append(100.0 * statistics.fmean(d) if d else 0.0)

    out = {key: 100.0 * e / max(tot_ref, 1) for key, e in edits.items()}
    out["mean_unique"] = statistics.fmean(uniq)
    out["mean_pairwise"] = statistics.fmean(pair)
    out["n_utts"] = len(rows)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_path", default="aiola/drax-v1")
    ap.add_argument("--librispeech", required=True, help="a split directory")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--n_utts", type=int, default=40)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--sampling_steps", type=int, default=8)
    ap.add_argument("--temperatures", default="0.1,0.3,0.6,1.0")
    ap.add_argument("--language", default="en")
    ap.add_argument("--max_seconds", type=float, default=15.0)
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import data as dataio

    from drax import Transcriber

    utts = [u for u in itertools.islice(
        dataio.iter_utterances("librispeech", args.librispeech), args.n_utts * 4)
        if u.duration_s <= args.max_seconds][:args.n_utts]
    audio_s = sum(u.duration_s for u in utts)
    print(f"{len(utts)} utterances, {audio_s / 60:.1f} min of audio, k = {args.k}, "
          f"{args.sampling_steps} sampling steps\n")

    asr = Transcriber(model_path=args.model_path)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for temp in [float(t) for t in args.temperatures.split(",")]:
        dump_path = out_dir / f"drax-t{temp}-k{args.k}.jsonl"
        rows, t0 = [], time.time()

        with open(dump_path, "w", encoding="utf-8") as f:
            for n, u in enumerate(utts, 1):
                # K copies of one file in one batch: K stochastic samples, public API only.
                res = asr.transcribe([u.audio_path] * args.k,
                                     language=[args.language] * args.k,
                                     sampling_steps=args.sampling_steps,
                                     temperature=temp)
                texts = [r.transcript for r in res]
                row = {
                    "id": u.id,
                    "dataset": "drax-smoke",
                    "duration_s": round(u.duration_s, 3),
                    "reference": u.text,
                    "n_unique": len(set(texts)),
                    "candidates": [{"text": t} for t in texts],
                }
                rows.append(row)
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                if n % 10 == 0:
                    print(f"  t={temp}  {n}/{len(utts)}  {time.time() - t0:.0f} s", flush=True)

        s = summarise(rows)
        s["temperature"] = temp
        s["seconds"] = time.time() - t0
        s["rtf"] = s["seconds"] / max(audio_s, 1e-9)
        results.append(s)
        print(f"  t={temp} done in {s['seconds']:.0f} s -> {dump_path}\n", flush=True)

    print("=" * 78)
    print(f"{'temp':>6}{'unique/k':>10}{'pairwise %':>12}{'MBR':>8}{'ROVER':>8}"
          f"{'oracle':>8}{'komp.':>8}{'kontrola':>10}{'RTF':>8}")
    print("=" * 78)
    for s in results:
        print(f"{s['temperature']:>6}{s['mean_unique']:>10.1f}{s['mean_pairwise']:>12.1f}"
              f"{s['mbr']:>8.2f}{s['rover']:>8.2f}{s['oracle_cand']:>8.2f}"
              f"{s['oracle_comp']:>8.2f}{s['control']:>10.2f}{s['rtf']:>8.3f}")

    print("\nCo v tom hledat:")
    print("  1. unique/k nad 1.0        -> kandidati se vubec rozchazeji")
    print("  2. ROVER pod MBR           -> skladani bije vyber i tady")
    print("  3. komp. hluboko pod oracle a kontrola blizko oracle")
    print("                             -> je to informace, ne volnost vyberu")

    with open(out_dir / "drax-smoke.json", "w", encoding="utf-8") as f:
        json.dump({"args": vars(args), "results": results}, f, indent=2)
    print(f"\nwritten: {out_dir / 'drax-smoke.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
