#!/usr/bin/env python3
"""What each configuration costs at inference, from the timing files the run wrote.

Every component is timed per utterance on the run's GPU (T4, fp16), synchronised around the
model calls: decoding (tools/loop_decode.py times flat K, tree-early and the tree up to the
snapshot on the same utterances), the decoder's consensus passes (tools/refine.py), and the
external LMs (tools/gpt_slots.py). Shared by every configuration and listed once: the Whisper
encoder and the step-zero acoustic reading the final pipeline uses as features. Two GPUs ran in
parallel chains, so absolute milliseconds are per GPU; ratios are what to compare.

    python3 tools/compute_report.py results/refine2
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

DECODER_PARAMS = 261.5e6        # Whisfusion decoder, as wf_model reports it
SEQ = 256


def mean(v):
    return sum(v) / len(v) if v else float("nan")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "results/refine2")
    files = sorted(root.glob("*.timing.json"))
    if not files:
        print(f"no timing files in {root}")
        return 1
    dec, comp, lms = None, defaultdict(lambda: dict(ms=[], passes=[])), {}
    for f in files:
        t = json.loads(f.read_text())
        if "tree" in t:
            dec = t
        elif "model" in t:
            lms[(Path(t["model"]).name, t["arm"])] = t
        else:
            v = ("lora " if t["lora"] else "") + f"{t['mode']}/{t['context']}"
            for ms, ps, arm in zip(t["ms"], t["passes"], t["arm"]):
                comp[(arm, v)]["ms"].append(ms)
                comp[(arm, v)]["passes"].append(ps)

    gflop = 2 * DECODER_PARAMS * SEQ / 1e9
    print(f"decoder pass = one {SEQ}-token row, ~{gflop:.0f} GFLOP (2 x {DECODER_PARAMS / 1e6:.0f}M x {SEQ})\n")
    if dec:
        P = dec["passes"]
        print("| component | ms / utt | decoder passes |\n|---|---|---|")
        print(f"| Whisper encoder (shared) | {mean(dec['encode']):.1f} | |")
        print(f"| step-zero acoustic reading (shared feature) | {mean(dec['acoustic']):.1f} | 1 |")
        print(f"| decode flat K=8 (anchor-k8) | {mean(dec['flat']):.1f} | {P['flat']} |")
        print(f"| decode tree-early (tree-k8) | {mean(dec['tree_plain']):.1f} | {P['tree']} |")
        print(f"| (tree-early with the snapshot records built, all utterances) | {mean(dec['tree']):.1f} | |")
        print(f"| decode tree to the snapshot (loop-k8) | {mean(dec['loop_only']):.1f} | {P['loop_only']} |")
    for (arm, v), d in sorted(comp.items()):
        print(f"| decoder scoring {v}, {arm} | {mean(d['ms']):.1f} | {mean(d['passes']):.1f} |")
    for (m, arm), t in sorted(lms.items()):
        tok = mean(t["tokens"])
        print(f"| LM {m} ({t['params'] / 1e6:.0f}M) on {arm} | {mean(t['ms']):.1f} | "
              f"{tok:.0f} LM tokens, ~{2 * t['params'] * tok / 1e9:.0f} GFLOP |")

    if not dec:
        return 0
    base = {"anchor-k8": mean(dec["flat"]), "tree-k8": mean(dec["tree_plain"]), "loop-k8": mean(dec["loop_only"])}
    print("\nper configuration (decode + composition; encoder and acoustic reading excluded, common to all)")
    print("| configuration | ms / utt | x flat K=8 |\n|---|---|---|")
    ref = base["anchor-k8"]
    rows = [("anchor-k8 final", base["anchor-k8"]), ("tree-k8 final", base["tree-k8"])]
    for (arm, v), d in sorted(comp.items()):
        if arm in base:
            rows.append((f"{arm} final +score [{v}]", base[arm] + mean(d["ms"])))
    for (m, arm), t in sorted(lms.items()):
        if arm in base:
            rows.append((f"{arm} final +{m}", base[arm] + mean(t["ms"])))
    for name, ms in rows:
        print(f"| {name} | {ms:.1f} | {ms / ref:.2f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
