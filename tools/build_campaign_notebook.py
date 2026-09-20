#!/usr/bin/env python3
"""Build the self-contained Kaggle campaign notebook(s) from src/.

Every source file the campaign needs is embedded as a %%writefile cell, so a notebook version is
a complete, pinned record of the code that produced its results: no git clone of this repo, no
dataset of code to keep in sync.

    python tools/build_campaign_notebook.py                         # notebooks/kaggle_campaign.ipynb
    python tools/build_campaign_notebook.py --variant smoke --user me --kernel_dir out/smoke

--kernel_dir also writes a kernel-metadata.json next to a copy of the notebook, ready for
`kaggle kernels push -p <kernel_dir>`. The metadata carries a username, so it is kept out of
the repo.
"""

from __future__ import annotations

import argparse
import pprint
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FILES = ["scorers.py", "compose.py", "bootstrap.py", "decode.py", "wf_model.py", "wf_compat.py", "data.py",
         "campaign/__init__.py", "campaign/config.py", "campaign/state.py", "campaign/tokwords.py",
         "campaign/prep_data.py", "campaign/drax_fast.py", "campaign/families.py", "campaign/worker.py",
         "campaign/analysis.py", "campaign/aggregate.py", "campaign/run.py"]

VARIANTS = {
    # full run: ~11 h on T4 x2
    # Drax at K=16 costs ~4.3 s/utt on a T4 (210 ms per candidate at 16 steps), Whisfusion ~2.2 s
    # at K=32; T=1.3 and fp16 were picked on dev in the smoke run
    "full": dict(MODE="full", RUN_HOURS=11.4, CONFIG={"tail_minutes": 25}),
    # second session: the controls that never got a GPU turn, Drax at its dev-tuned temperature,
    # and the Whisfusion K=64 scaling job
    "round2": dict(MODE="full", RUN_HOURS=3.5, CONFIG={"plan": "round2", "tail_minutes": 15,
                                                       "drax_low_T": 0.4}),
    # third session: the Drax temperature ladder on several datasets, dense where it bends
    "sweep": dict(MODE="full", RUN_HOURS=6.5, CONFIG={
        "plan": "sweep", "tail_minutes": 15, "models": ["drax"],
        "sweep_sets": ["ami", "earnings22", "ls-test-other"],
        "drax_sweep_T": [0.1, 0.4, 0.7, 1.0, 1.15, 1.3, 1.45, 1.6],
    }),
    # round 3: a temperature sweep for every family on the same sets, two more rungs on
    # each noise ladder, and deeper shards of every cell that already exists
    "round3": dict(MODE="full", RUN_HOURS=11.4, CONFIG={
        "plan": "round3", "tail_minutes": 25, "drax_low_T": 0.4,
        # five rungs, not the round-1 seven: 0.1 is the reference decode and 2.0 was already bad
        "drax_sweep_T": [0.4, 0.7, 1.0, 1.3, 1.6],
    }),
    # GPU smoke: every model, every job kind, a few utterances each; also calibrates Drax
    "smoke": dict(MODE="smoke", RUN_HOURS=0.9, CONFIG={
        "tail_minutes": 6, "shard_size": 12,
        "smoke": {"n_max": 48, "drax_calibration_shards": 3, "precision_check": True},
    }),
    # CPU debug: free (no accelerator), tiny decodes, every code path
    "cpu": dict(MODE="smoke", RUN_HOURS=1.6, CONFIG={
        "tail_minutes": 8, "shard_size": 2, "analysis_workers": 1,
        "k_main": {"whisfusion": 4, "drax": 3},
        "drax": {"T": 1.3, "steps": 2, "precision": "fp32", "ref_T": 0.1, "ref_K": 2},
        "drax_sweep_T": [0.1, 1.3], "drax_sweep_K": 2, "drax_steps_sweep": [1],
        "whisper_sample": {"K": 3, "T": 0.6}, "whisper_beams": 2, "ctc_sample": {"K": 3, "T": 1.0},
        "smoke": {"n_max": 4, "sets": ["ls-dev-clean", "ls-dev-other", "ls-test-clean", "ami",
                                       "fleurs-de", "ls-tc-babble5", "slr83"]},
    }),
}

INTRO = """# Candidate composition campaign

Parallel and diffusion ASR decoders produce K candidate transcripts per utterance at little extra
cost. This notebook measures, at scale, whether composing them word by word (ROVER over a
confusion network) beats picking one of them whole, across:

- **models**: Whisfusion (masked diffusion), Drax (discrete flow matching); controls: Whisper-small
  and Whisper-large-v3-turbo (autoregressive: greedy, beam n-best, samples) and Parakeet-CTC-1.1B
  (one-step parallel, sampled CTC paths);
- **data**: LibriSpeech dev/test, the Open ASR Leaderboard test sets (AMI, Earnings22, VoxPopuli,
  GigaSpeech, SPGISpeech, Common Voice), FLEURS (en + de/fr/es/it/pt for Drax), SLR83 accents, and
  a controlled babble/white-noise ladder on test-clean.

Two independent worker processes, one per T4, pull jobs from a tiered queue: every cell of the
design gets the same coverage first, then more. Everything is written incrementally; results land
in `/kaggle/working/campaign/results/` (`REPORT.md`, `campaign_summary.json`, per-utterance tables).

**Accelerator: GPU T4 x2. Internet: on.** Nothing needs to be attached.
"""

SETUP = r'''import os, subprocess, sys, time, json, shutil
t_setup = time.time()

def sh(cmd, check=True):
    r = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if r.returncode != 0:
        print(f"$ {cmd}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
        if check:
            raise RuntimeError(f"failed: {cmd}")
    return r

sh("pip install -q 'lightning>=2.1' lightning-utilities rapidfuzz jiwer einops sentencepiece "
   "omegaconf whisper-normalizer")
UP = "/tmp/upstream"
os.makedirs(UP, exist_ok=True)
PINS = {"Whisfusion": ("https://github.com/taeyoun811/Whisfusion.git", "aa9afe3688ccd15ebf096ec9845d67925d1a3aea"),
        "drax": ("https://github.com/aiola-lab/drax.git", "ffab757b1c88d9c6cdf9912d543032f98fc085e3")}
upstream = {}
for name, (url, pin) in PINS.items():
    d = f"{UP}/{name}"
    if not os.path.exists(d):
        sh(f"git clone -q {url} {d}")
        sh(f"git -C {d} checkout -q {pin}", check=False)
    upstream[name] = sh(f"git -C {d} rev-parse HEAD").stdout.strip()
print("upstream:", upstream)

import importlib.util
assert importlib.util.find_spec("flash_attn") is None, "flash-attn must not be installed on T4 (see wf_compat)"
import torch
print("torch", torch.__version__, "gpus", [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())])
print(f"setup {time.time() - t_setup:.0f} s")
'''

RUN = r'''CODE = "/kaggle/working/code/src"
ROOT = "/kaggle/working/campaign"
DATA = "/tmp/campaign_data"
cfg = dict(CONFIG, mode=MODE, run_hours=RUN_HOURS - (time.time() - NB_START) / 3600, upstream=upstream)
cfg_path = "/kaggle/working/campaign_config.json"
with open(cfg_path, "w") as f:
    json.dump(cfg, f, indent=2)
print(f"campaign budget {cfg['run_hours']:.2f} h")

env = dict(os.environ, PYTHONPATH=f"{CODE}:{UP}/Whisfusion/src", HF_HOME="/tmp/hf",
           DRAX_ROOT=f"{UP}/drax", TOKENIZERS_PARALLELISM="false", HF_HUB_DISABLE_PROGRESS_BARS="1",
           TRANSFORMERS_VERBOSITY="error", PYTHONUNBUFFERED="1")
p = subprocess.Popen([sys.executable, "-m", "campaign.run", "--config", cfg_path, "--root", ROOT,
                      "--data", DATA], env=env, cwd=CODE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, bufsize=1)
for line in p.stdout:
    print(line, end="", flush=True)
print("campaign exit code", p.wait())
'''

REPORT = r'''from pathlib import Path
rep = Path(ROOT) / "results" / "REPORT.md"
print(rep.read_text() if rep.exists() else "no report")
total = 0
for f in sorted(Path(ROOT).rglob("*")):
    if f.is_file():
        total += f.stat().st_size
print(f"\noutput: {total / 1e9:.2f} GB in {ROOT}")
for f in sorted(Path(ROOT).iterdir()):
    print(f"  {f.name:<32} {f.stat().st_size / 1e6 if f.is_file() else 0:10.1f} MB")
'''


def cell(kind: str, src: str) -> dict:
    lines = src.splitlines(keepends=True)
    c = {"cell_type": kind, "metadata": {}, "source": lines}
    if kind == "code":
        c.update(execution_count=None, outputs=[])
    return c


def build(variant: str) -> dict:
    v = VARIANTS[variant]
    cells = [cell("markdown", INTRO + (f"\n\n**Variant: {variant}.**" if variant != "full" else ""))]
    cells.append(cell("code", "import time\nNB_START = time.time()\n"
                              f"MODE = {v['MODE']!r}\nRUN_HOURS = {v['RUN_HOURS']!r}   # whole notebook, "
                              "setup included; Kaggle stops at 12 h\n"
                              f"CONFIG = {pprint.pformat(v['CONFIG'], width=100, sort_dicts=False)}\n"))
    cells.append(cell("markdown", "Code: every module the campaign runs, written to `/kaggle/working/code/src`."))
    cells.append(cell("code", "import os\nfor d in ['/kaggle/working/code/src/campaign']:\n"
                              "    os.makedirs(d, exist_ok=True)\n"))
    for rel in FILES:
        text = (SRC / rel).read_text(encoding="utf-8")
        cells.append(cell("code", f"%%writefile /kaggle/working/code/src/{rel}\n{text}"))
    cells.append(cell("markdown", "Dependencies and the two upstream repositories, pinned."))
    cells.append(cell("code", SETUP))
    cells.append(cell("markdown", "The campaign. Progress is printed every 10 minutes; worker logs are in "
                                  "`campaign/logs/`."))
    cells.append(cell("code", RUN))
    cells.append(cell("code", REPORT))
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                                        "name": "python3"},
                                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 5}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="full", choices=sorted(VARIANTS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--kernel_dir", default=None)
    ap.add_argument("--user", default=None)
    ap.add_argument("--slug", default=None)
    args = ap.parse_args()

    nb = build(args.variant)
    name = "kaggle_campaign.ipynb" if args.variant == "full" else f"kaggle_campaign_{args.variant}.ipynb"
    out = Path(args.out) if args.out else ROOT / "notebooks" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"notebook: {out}")

    if args.kernel_dir:
        if not args.user:
            raise SystemExit("--kernel_dir needs --user")
        kd = Path(args.kernel_dir)
        kd.mkdir(parents=True, exist_ok=True)
        (kd / name).write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
        slug = args.slug or ("candidate-composition-campaign" if args.variant == "full"
                             else f"candidate-composition-{args.variant}")
        meta = {"id": f"{args.user}/{slug}", "title": slug, "code_file": name, "language": "python",
                "kernel_type": "notebook", "is_private": True, "enable_gpu": args.variant != "cpu",
                "enable_tpu": False, "enable_internet": True, "keywords": [], "dataset_sources": [],
                "kernel_sources": [], "competition_sources": [], "model_sources": []}
        if args.variant != "cpu":
            meta["machine_shape"] = "NvidiaTeslaT4"
        (kd / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"kernel dir: {kd}  ({meta['id']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
