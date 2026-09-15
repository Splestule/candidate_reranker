#!/usr/bin/env python3
"""Turn an out-of-domain corpus into the JSONL manifest dump_candidates.py reads.

Supports the openslr crowdsourced dialect sets (SLR83 and friends): a flat directory of
wav files next to a line_index.csv of "lineid, fileid, transcription".

    python make_manifest.py --slr83 data/ood/*/ --out data/ood/dialects.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import soundfile as sf


def read_slr83(root: Path) -> list[dict]:
    index = root / "line_index.csv"
    if not index.exists():
        raise FileNotFoundError(index)

    out = []
    with open(index, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",", 2)          # transcripts may contain commas
            if len(parts) != 3:
                continue
            _, file_id, text = (p.strip() for p in parts)
            wav = root / f"{file_id}.wav"
            if not wav.exists() or not text:
                continue
            info = sf.info(str(wav))
            out.append({
                "id": file_id,
                "audio": str(wav.resolve()),
                "text": text,
                "duration_s": round(info.frames / info.samplerate, 3),
                "source": root.name,
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slr83", nargs="+", required=True, help="extracted subset directories")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max_seconds", type=float, default=30.0)
    args = ap.parse_args()

    rows = []
    for d in args.slr83:
        root = Path(d)
        got = read_slr83(root)
        rows += got
        print(f"{root.name}: {len(got)} utterances")

    rows = [r for r in rows if r["duration_s"] <= args.max_seconds]
    rows.sort(key=lambda r: r["id"])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    total = sum(r["duration_s"] for r in rows)
    print(f"\n{len(rows)} utterances, {total/60:.1f} min of audio -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
