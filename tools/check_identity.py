#!/usr/bin/env python3
"""At K=1 every method must be the identity, under every normalisation.

One candidate means one vote in every slot, so ROVER can only return that candidate. Any
difference is the scoring pipeline, not the method. This catches the whole class of bug where
a hypothesis and its reference travel through different amounts of normalisation -- which cost
us 2 to 7 WER points of imaginary penalty and briefly looked like a negative result.

    PYTHONPATH=src python tools/check_identity.py results/campaign-2026-09-20/dumps
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

from rapidfuzz.distance import Levenshtein

import compose
from scorers import normalize


def norms():
    out = {"legacy": lambda t, lang: normalize(t).split()}
    try:
        from whisper_normalizer.basic import BasicTextNormalizer
        from whisper_normalizer.english import EnglishTextNormalizer
        en, basic = EnglishTextNormalizer(), BasicTextNormalizer()
        out["whisper"] = lambda t, lang: (en if lang == "en" else basic)(t).split()
    except ImportError:
        print("note: whisper_normalizer missing, checking the legacy normaliser only")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dumps", help="a campaign dumps/ directory")
    ap.add_argument("--n_utts", type=int, default=100)
    args = ap.parse_args()

    files = sorted(Path(args.dumps).glob("*/greedy.jsonl.gz"))
    if not files:
        print(f"no K=1 arms under {args.dumps}")
        return 1

    bad = 0
    for path in files:
        rows = []
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= args.n_utts:
                    break
                rows.append(json.loads(line))
        rows = [r for r in rows if len(r["candidates"]) == 1]
        if not rows:
            continue
        for name, norm in norms().items():
            diff = 0
            for r in rows:
                lang = r.get("lang", "en")
                words = norm(r["candidates"][0]["text"], lang)
                slots = compose.confusion_network([words], 0, None, None)
                diff += Levenshtein.distance(words, compose.rover(slots, 1.0, 1.0, 0.5))
            flag = "ok" if diff == 0 else f"FAIL, {diff} edits"
            bad += diff != 0
            print(f"  {path.parent.name[:44]:<46}{name:<9}{flag}")
    print("\nidentity holds everywhere" if not bad else f"\n{bad} arm/normaliser pairs broken")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
