#!/usr/bin/env python3
"""Flat sampling must be bit-identical to the decoder before branching was added.

The tree parameters default to off, so the old path has to survive untouched: same seed,
same masks, same text. This loads the committed decode.py straight out of git alongside the
working one, runs both on the same utterances, and compares. Everything measured before
today was produced by the old path, so if this fails those numbers are no longer comparable.

    PYTHONPATH=src python tools/check_decode_identity.py --base_model ... --adapter ... \
        --librispeech <split dir> --n_utts 8 --ref HEAD
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import subprocess
import sys
import tempfile
from pathlib import Path


def load_old(ref: str):
    src = subprocess.run(["git", "show", f"{ref}:src/decode.py"],
                         capture_output=True, text=True, check=True).stdout
    tmp = Path(tempfile.mkdtemp()) / "decode_old.py"
    tmp.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("decode_old", tmp)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["decode_old"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--librispeech", required=True)
    ap.add_argument("--n_utts", type=int, default=8)
    ap.add_argument("--k", type=int, default=16)
    ap.add_argument("--ref", default="HEAD", help="git ref holding the reference decoder")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    import data as dataio
    import decode as new
    import wf_model

    old = load_old(args.ref)
    wf = wf_model.load(args.base_model, args.adapter)
    utts = list(itertools.islice(dataio.iter_utterances("librispeech", args.librispeech),
                                 args.n_utts))

    bad = 0
    for n, u in enumerate(utts):
        cond = wf_model.encode_audio(wf, dataio.load_audio(u.audio_path))
        a = old.pdd_decode(wf, cond, n_candidates=args.k, n_steps=4, seed=1000 + n)
        b = new.pdd_decode(wf, cond, n_candidates=args.k, n_steps=4, seed=1000 + n)
        ta = [c.text for c in a.candidates]
        tb = [c.text for c in b.candidates]
        same = ta == tb
        bad += not same
        print(f"  {u.id:<24}{'ok' if same else 'MISMATCH'}"
              f"   unique {a.n_unique} -> {b.n_unique}")
        if not same:
            for i, (x, y) in enumerate(zip(ta, tb)):
                if x != y:
                    print(f"      cand {i}\n        old: {x[:90]}\n        new: {y[:90]}")
                    break

    print(f"\n{len(utts) - bad}/{len(utts)} identical"
          + ("" if bad else "  — flat sampling is unchanged"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
