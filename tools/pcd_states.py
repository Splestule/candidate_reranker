#!/usr/bin/env python3
"""Sibling states for training peer-conditioned denoising: for every training utterance, the
K = 8 rows of tree-early PDD (branch [1, 2, 8]) after step 3 of 4, exactly as decoding reaches
the last step, and the reference as target tokens in the model's own casing.

    PYTHONPATH=src:Whisfusion/src:tools python3 tools/pcd_states.py --train /tmp/pcd_data/train.jsonl \\
        --part 0/2 --out results/pcd/states_0.pkl
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--part", default="0/1", help="i/n: every n-th utterance starting at i")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    import numpy as np
    import data as dataio
    import pcd
    import wf_model
    from campaign.families import Whisfusion
    from scorers import normalize

    i, n = (int(x) for x in a.part.split("/"))
    rows = [json.loads(l) for l in open(a.train)][i::n]
    if a.limit:
        rows = rows[:a.limit]
    wf = Whisfusion({}).wf
    tok = wf.tokenizer
    bos = tok.bos_token_id if tok.bos_token_id is not None else 0
    out, t0 = [], time.time()
    for r in rows:
        try:
            cond = wf_model.encode_audio(wf, dataio.load_audio(r["audio"]))
            seed = zlib.crc32(f"{r['set']}/{r['id']}".encode()) % (2 ** 31)
            cur, _ = pcd.first_steps(wf, cond, seed)
            words = normalize(r["text"]).split()
            tgt = [bos] + [t for w in words for t in tok(w.upper(), add_special_tokens=False)["input_ids"]]
            if len(tgt) > cur.shape[1]:
                continue
            out.append(dict(set=r["set"], id=r["id"], audio=r["audio"], ref=words,
                            cur=cur.cpu().numpy().astype(np.int32), tgt=tgt))
        except Exception as e:
            print(f"  !! {r['set']}/{r['id']}: {type(e).__name__}: {e}", flush=True)
        if len(out) % 250 == 0 and out:
            print(f"  {len(out)} states, {(time.time() - t0) / len(out):.2f} s each", flush=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_bytes(pickle.dumps(out))
    print(f"done: {len(out)} states in {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0 if out else 1


if __name__ == "__main__":
    raise SystemExit(main())
