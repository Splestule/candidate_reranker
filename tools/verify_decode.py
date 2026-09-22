#!/usr/bin/env python3
"""Run the decoder checks against real speech from a campaign that already prepared data.

check_decode itself takes --manifest; this only finds one and points it there.

    PYTHONPATH=src python tools/verify_decode.py /tmp/campaign_data --n_utts 6
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="a campaign data root, or any directory holding manifests/")
    ap.add_argument("--set", default=None, help="which prepared set to probe with")
    ap.add_argument("--n_utts", type=int, default=6)
    ap.add_argument("--k", type=int, default=16)
    args = ap.parse_args()

    root = Path(args.root)
    mans = sorted((root / "manifests").glob("*.jsonl")) or sorted(root.glob("*.jsonl"))
    if args.set:
        mans = [p for p in mans if p.stem == args.set]
    if not mans:
        print(f"no manifest under {root}; prepare data first")
        return 2

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    import check_decode
    return check_decode.main(str(mans[0]), args.n_utts, args.k)


if __name__ == "__main__":
    raise SystemExit(main())
