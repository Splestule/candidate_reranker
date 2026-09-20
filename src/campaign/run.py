#!/usr/bin/env python3
"""Orchestrator: data prep, one lane per GPU, analysis in the background, aggregation at the end.

    python -m campaign.run --config run_config.json --root /kaggle/working/campaign --data /tmp/cdata

A lane is a thread that keeps one GPU busy. It asks the shared state which model has the
lowest-tier work ready, starts a worker process for that model pinned to its GPU
(CUDA_VISIBLE_DEVICES), and when the worker exits (its model ran out of work, or it yielded to
lower-tier work elsewhere) picks again. Two independent processes rather than DDP: the models
are small enough that data parallelism across utterances is all that is needed.

Deadlines: GPU work stops `tail_minutes` before `run_hours`; the tail finishes the analysis of
every dump and writes the results. Everything written before a crash or a timeout is kept.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
sys.path.insert(0, str(SRC))

from campaign import config as C  # noqa: E402
from campaign import state as ST  # noqa: E402

T_START = time.time()


def say(msg: str) -> None:
    el = (time.time() - T_START) / 60
    print(f"[{time.strftime('%H:%M:%S')} +{el:6.1f}m] {msg}", flush=True)


def env_info() -> dict:
    info = dict(python=platform.python_version(), host=platform.node())
    try:
        import torch
        info.update(torch=torch.__version__, cuda=torch.version.cuda, n_gpus=torch.cuda.device_count(),
                    gpus=[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())])
    except Exception as e:
        info["torch"] = f"ERROR {e}"
    for mod in ("transformers", "huggingface_hub", "numpy", "pandas", "rapidfuzz", "soundfile", "librosa"):
        try:
            info[mod] = str(__import__(mod).__version__)
        except Exception as e:
            info[mod] = f"ERROR {type(e).__name__}"
    try:
        info["nvidia_smi"] = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        pass
    try:
        du = shutil.disk_usage("/tmp")
        info["tmp_free_gb"] = round(du.free / 1e9, 1)
        info["cpu_count"] = os.cpu_count()
    except Exception:
        pass
    return info


class Lane(threading.Thread):
    def __init__(self, gpu: int, st: ST.State, args, preferred: list[str], gpu_deadline: float,
                 busy: dict, lock: threading.Lock):
        super().__init__(daemon=True)
        self.gpu, self.st, self.args = gpu, st, args
        self.preferred = preferred
        self.deadline = gpu_deadline
        self.busy, self.lock = busy, lock
        self.current: str | None = None
        self.proc: subprocess.Popen | None = None
        self.launches = 0
        self.idle_s = 0.0

    def run(self):
        while time.time() < self.deadline - 60:
            with self.lock:
                others = {m for g, m in self.busy.items() if g != self.gpu and m}
                model = self.st.choose_model(self.current, self.preferred, others)
                if model:
                    self.busy[self.gpu] = model
            if model is None:
                if self.st.any_waiting() or not self.st.prep_finished():
                    time.sleep(15)
                    self.idle_s += 15
                    continue
                say(f"lane {self.gpu}: no work left")
                break
            self.current = model
            self.launches += 1
            say(f"lane {self.gpu}: starting {model}")
            env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(self.gpu), PYTHONUNBUFFERED="1")
            log = self.st.logs / f"worker_gpu{self.gpu}_{self.launches:03d}_{model.replace('@', '_')}.log"
            cmd = [sys.executable, "-m", "campaign.worker", "--model", model, "--lane", str(self.gpu),
                   "--root", str(self.st.root), "--data", str(self.st.data), "--deadline", str(self.deadline)]
            with open(log, "w", encoding="utf-8") as fh:
                self.proc = subprocess.Popen(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT)
                rc = self.proc.wait()
            with self.lock:
                self.busy[self.gpu] = None
            for jid in self.st.orphaned_claims(self.gpu):
                say(f"lane {self.gpu}: releasing orphaned claim {jid} (worker rc={rc})")
                self.st.release(jid, crashed=True)
            text = log.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            errs = [ln for ln in lines if "[!]" in ln or "Traceback" in ln or "CRASHED" in ln]
            dones = [ln.split("] ", 2)[-1] for ln in lines if "] done " in ln]
            say(f"lane {self.gpu}: {model} exited rc={rc}, {len(dones)} jobs, {len(errs)} error lines")
            for ln in dones[-6:]:
                say(f"    {ln}")
            for ln in errs[:4]:
                say(f"    ERR {ln[-400:]}")
            if rc != 0:
                say(f"lane {self.gpu}: worker {model} log tail:\n{text[-3000:]}")
                if rc not in (0, 3):
                    time.sleep(5)
        say(f"lane {self.gpu}: finished ({self.launches} worker launches, idle {self.idle_s / 60:.1f} min)")


def analysis_task(root: str, job: dict, k_main: int) -> list[dict]:
    sys.path.insert(0, str(SRC))
    from campaign import analysis
    try:
        os.nice(5)
    except Exception:
        pass
    return analysis.analyze_job(Path(root), job, k_main)


def k_main_of(cfg: dict, job: dict) -> int:
    return cfg["k_main"].get(job["model"], 64)


def progress(st: ST.State, cfg: dict) -> dict:
    counts = st.counts()
    by_model: dict[str, dict] = {}
    for p in st.done_dir.glob("*.json"):
        try:
            s = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        m = s.get("model", p.stem.split("__")[0])
        d = by_model.setdefault(m, dict(jobs=0, utts=0, audio_h=0.0, wall_h=0.0))
        d["jobs"] += 1
        d["utts"] += s.get("n_ok", 0)
        d["audio_h"] += s.get("audio_s", 0.0) / 3600
        d["wall_h"] += s.get("wall_s", 0.0) / 3600
    tiers: dict[int, dict] = {}
    for j in st.plan():
        t = tiers.setdefault(j["tier"], {"total": 0, "done": 0})
        t["total"] += 1
        t["done"] += st.is_done(j["id"])
    return dict(elapsed_h=(time.time() - T_START) / 3600, jobs=counts, by_model=by_model, tiers=tiers)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--n_gpus", type=int, default=None)
    args = ap.parse_args()

    cfg = C.load_config(args.config)
    root, data = Path(args.root), Path(args.data)
    root.mkdir(parents=True, exist_ok=True)
    t_end = T_START + cfg["run_hours"] * 3600
    gpu_deadline = t_end - cfg["tail_minutes"] * 60
    cfg["t_start_unix"], cfg["t_end_unix"], cfg["gpu_deadline_unix"] = T_START, t_end, gpu_deadline
    C.write_json(root / "run_config.json", cfg)

    plan = C.PLANS.get(cfg.get("plan", "full"), C.build_plan)(cfg)
    C.write_json(root / "plan.json", plan)
    info = env_info()
    C.write_json(root / "env.json", info)
    say(f"env: {json.dumps(info)}")
    tiers = {}
    for j in plan:
        tiers[j["tier"]] = tiers.get(j["tier"], 0) + 1
    say(f"plan: {len(plan)} jobs, per tier {dict(sorted(tiers.items()))}; GPU work until "
        f"+{(gpu_deadline - T_START) / 3600:.2f} h, results by +{(t_end - T_START) / 3600:.2f} h")

    st = ST.State(root, data)

    # data prep in the background; manifests appear one by one
    prep_log = open(st.logs / "prep.log", "a", encoding="utf-8")
    prep = subprocess.Popen([sys.executable, "-m", "campaign.prep_data", "--config", str(root / "run_config.json"),
                             "--data", str(data)], stdout=prep_log, stderr=subprocess.STDOUT,
                            env=dict(os.environ, PYTHONUNBUFFERED="1"))

    n_gpus = args.n_gpus if args.n_gpus is not None else max(1, info.get("n_gpus", 0) or 0)
    if not info.get("n_gpus"):
        say("no CUDA device: running one CPU lane (debug mode)")
    lock = threading.Lock()
    busy: dict = {}
    prefs = [["drax", "whisper-turbo", "whisfusion", "whisper-small", "parakeet-ctc"],
             ["whisfusion", "whisper-small", "parakeet-ctc", "drax", "whisper-turbo"]]
    lanes = [Lane(g, st, args, prefs[g % 2], gpu_deadline, busy, lock) for g in range(n_gpus)]
    for ln in lanes:
        ln.start()

    pool = cf.ProcessPoolExecutor(max_workers=max(1, cfg["analysis_workers"]))
    submitted: dict[str, cf.Future] = {}
    plan_by_id = {j["id"]: j for j in plan}
    last_prog = 0.0

    def submit_finished():
        for p in st.done_dir.glob("*.json"):
            jid = p.stem
            if jid in submitted or jid not in plan_by_id:
                continue
            job = plan_by_id[jid]
            if all((st.analysis / f"{jid}__{a['name']}.parquet").exists() for a in job["arms"]):
                submitted[jid] = None
                continue
            submitted[jid] = pool.submit(analysis_task, str(root), job, k_main_of(cfg, job))

    prep_reported = False
    while any(ln.is_alive() for ln in lanes):
        time.sleep(20)
        submit_finished()
        if prep.poll() is not None and not prep_reported:
            prep_reported = True
            say(f"data prep finished rc={prep.returncode}; "
                f"failed sets: {[p.stem for p in st.manifests.glob('*.failed')]}")
        if time.time() - last_prog > 600:
            last_prog = time.time()
            pr = progress(st, cfg)
            C.write_json(root / "progress.json", pr)
            done_an = sum(1 for f in submitted.values() if f is not None and f.done())
            say(f"progress: jobs {pr['jobs']}; tiers "
                f"{ {t: f'{v['done']}/{v['total']}' for t, v in sorted(pr['tiers'].items())} }; "
                f"analysed {done_an}/{len(submitted)}")
            for m, d in sorted(pr["by_model"].items()):
                say(f"    {m:<16} {d['jobs']:>4} jobs {d['utts']:>6} utts {d['audio_h']:6.2f} h audio "
                    f"{d['wall_h']:6.2f} GPU-h")
        if time.time() > t_end - 5 * 60:
            say("hard end approaching; abandoning lanes")
            for ln in lanes:
                if ln.proc is not None and ln.proc.poll() is None:
                    ln.proc.kill()
            break

    if prep.poll() is None:
        prep.terminate()
    say("GPU phase over; finishing analysis")
    submit_finished()
    for jid, fut in list(submitted.items()):
        if fut is None:
            continue
        remaining = t_end - 8 * 60 - time.time()
        if remaining <= 0:
            say("out of time for analysis; the rest can be run offline with campaign.analysis")
            break
        try:
            fut.result(timeout=remaining)
        except Exception as e:
            say(f"analysis of {jid} failed: {type(e).__name__}: {e}")
    pool.shutdown(wait=False, cancel_futures=True)

    # provenance: exactly which utterances every set held
    (root / "manifests").mkdir(exist_ok=True)
    for p in st.manifests.glob("*"):
        if p.suffix in (".jsonl", ".json") or p.name.endswith(".failed"):
            shutil.copy(p, root / "manifests" / p.name)

    pr = progress(st, cfg)
    C.write_json(root / "progress.json", pr)
    say("aggregating")
    try:
        remaining = max(60, t_end - time.time() - 60)
        rc = subprocess.run([sys.executable, "-m", "campaign.aggregate", "--root", str(root)],
                            timeout=remaining, env=dict(os.environ, PYTHONUNBUFFERED="1")).returncode
        say(f"aggregate rc={rc}")
    except subprocess.TimeoutExpired:
        say("aggregate timed out; run `python -m campaign.aggregate --root ...` offline")
    except Exception:
        traceback.print_exc()
    pack(root)
    say(f"done in {(time.time() - T_START) / 3600:.2f} h")
    return 0


def pack(root: Path) -> None:
    """Thousands of small files become a handful of tarballs; results/ stays browsable."""
    import tarfile
    for name in ("dumps", "analysis", "state", "logs", "manifests"):
        d = root / name
        if not d.exists():
            continue
        try:
            with tarfile.open(root / f"{name}.tar", "w") as tf:
                tf.add(d, arcname=name)
            shutil.rmtree(d)
            say(f"packed {name}.tar ({(root / f'{name}.tar').stat().st_size / 1e6:.0f} MB)")
        except Exception as e:
            say(f"packing {name} failed: {e}")


if __name__ == "__main__":
    raise SystemExit(main())
