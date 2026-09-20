#!/usr/bin/env python3
"""One GPU, one model: claim that model's jobs in plan order and decode them.

A claim is a file created with O_EXCL, so two workers never take the same job. Rows are
appended to a plain JSONL per (job, arm) as they are decoded and gzipped when the job ends; a
job cut short by the deadline or a crash keeps every finished utterance, and a rerun of the
same job skips them.

The worker exits instead of idling when (a) its model has nothing claimable left, or (b) some
other model has claimable work in a strictly lower tier: the parent then gives the GPU to that
model. Model load failures are recorded so no lane tries that model again.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import queue
import shutil
import socket
import sys
import threading
import time
import traceback
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from campaign import config as C  # noqa: E402
from campaign import state as ST  # noqa: E402


def round_floats(obj, nd=4):
    if isinstance(obj, float):
        return round(obj, nd)
    if isinstance(obj, list):
        return [round_floats(x, nd) for x in obj]
    if isinstance(obj, dict):
        return {k: round_floats(v, nd) for k, v in obj.items()}
    return obj


def utt_seed(base: int, uid: str, arm: str) -> int:
    return (base ^ zlib.crc32(f"{uid}|{arm}".encode("utf-8"))) & 0x7FFFFFFF


def read_done_ids(path: Path) -> set[str]:
    done = set()
    for p in (path, path.with_suffix(path.suffix + ".gz")):
        if not p.exists():
            continue
        opener = gzip.open if p.suffix == ".gz" else open
        try:
            with opener(p, "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        done.add(json.loads(line)["id"])
                    except Exception:
                        pass
        except (EOFError, OSError):
            pass
    return done


def compress(path: Path) -> None:
    """Merge a plain JSONL into its .gz (a resumed job may already have one)."""
    if not path.exists():
        return
    gz = path.with_suffix(path.suffix + ".gz")
    rows = []
    if gz.exists():
        try:
            with gzip.open(gz, "rt", encoding="utf-8") as f:
                rows = [line for line in f if line.strip()]
        except (EOFError, OSError):
            pass
    with open(path, encoding="utf-8") as f:
        rows += [line for line in f if line.strip()]
    tmp = gz.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for line in rows:
            f.write(line if line.endswith("\n") else line + "\n")
    tmp.replace(gz)
    path.unlink()


class Prefetch:
    """Loads audio for the next utterances on a thread while the GPU decodes."""

    def __init__(self, rows, depth=6):
        import data as dataio

        self.q: queue.Queue = queue.Queue(maxsize=depth)
        self.rows = rows
        self._load = dataio.load_audio
        self.t = threading.Thread(target=self._run, daemon=True)
        self.t.start()

    def _run(self):
        for r in self.rows:
            try:
                self.q.put((r, self._load(r["audio"]), None))
            except Exception as e:
                self.q.put((r, None, e))
        self.q.put(None)

    def __iter__(self):
        while True:
            item = self.q.get()
            if item is None:
                return
            yield item


def run_job(job: dict, fam, st: ST.State, deadline: float, cfg: dict, log) -> dict:
    import torch

    man = st.manifest(job["set"])
    S = job["shard_size"]
    rows = man[job["shard"] * S:(job["shard"] + 1) * S]
    out_dir = st.dumps / job["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {a["name"]: out_dir / f"{a['name']}.jsonl" for a in job["arms"]}
    done = None
    for a in job["arms"]:
        d = read_done_ids(paths[a["name"]])
        done = d if done is None else done & d
    todo = [r for r in rows if r["id"] not in (done or set())]
    log(f"job {job['id']}: {len(rows)} utts, {len(rows) - len(todo)} already done, arms "
        f"{[a['name'] for a in job['arms']]}")

    cuda = torch.cuda.is_available()
    if cuda:
        torch.cuda.reset_peak_memory_stats()

    def sync():
        if cuda:
            torch.cuda.synchronize()

    stats = dict(n_ok=0, n_err=0, audio_s=0.0, encode_s=0.0, decode_s={a["name"]: 0.0 for a in job["arms"]},
                 started=time.time(), status="done")
    fhs = {k: open(p, "a", encoding="utf-8") for k, p in paths.items()}
    try:
        for n, (u, audio, err) in enumerate(Prefetch(todo)):
            if time.time() > deadline:
                stats["status"] = "partial"
                log(f"deadline reached inside {job['id']} after {n} utts")
                break
            if err is not None or audio is None:
                stats["n_err"] += 1
                log(f"  [!] {u['id']}: audio load failed: {err}")
                continue
            try:
                sync(); t0 = time.time()
                enc = fam.encode(audio, job["lang"])
                sync(); t_enc = time.time() - t0
                outs = {}
                for a in job["arms"]:
                    sync(); t1 = time.time()
                    cands, extra = fam.decode(enc, a, utt_seed(cfg["seed"], u["id"], a["name"]), job["lang"])
                    sync()
                    # time spent only on measurement (Whisper's confidence pass) is not decoding
                    outs[a["name"]] = (cands, extra, time.time() - t1 - extra.get("score_s", 0.0))
            except torch.cuda.OutOfMemoryError as e:  # type: ignore[attr-defined]
                stats["n_err"] += 1
                log(f"  [!] {u['id']}: CUDA OOM ({e}); skipping")
                torch.cuda.empty_cache()
                continue
            except Exception as e:
                stats["n_err"] += 1
                log(f"  [!] {u['id']}: {type(e).__name__}: {e}")
                if stats["n_err"] <= 3:
                    log(traceback.format_exc())
                if stats["n_err"] >= 20 and stats["n_err"] > 0.5 * (stats["n_ok"] + stats["n_err"]):
                    stats["status"] = "failed"
                    log(f"  too many errors in {job['id']}, giving up on it")
                    break
                continue

            for name, (cands, extra, t_dec) in outs.items():
                row = dict(id=u["id"], dataset=job["set"], lang=job["lang"], cluster=u.get("cluster"),
                           duration_s=u["duration_s"], reference=u["text"], model=job["model"],
                           arm=name, n_unique=len({c["text"] for c in cands}),
                           encode_s=round(t_enc, 4), decode_s=round(t_dec, 4), candidates=cands, **extra)
                fhs[name].write(json.dumps(round_floats(row), ensure_ascii=False) + "\n")
                stats["decode_s"][name] += t_dec
            stats["encode_s"] += t_enc
            stats["audio_s"] += u["duration_s"]
            stats["n_ok"] += 1
            if stats["n_ok"] % 10 == 0:
                for fh in fhs.values():
                    fh.flush()
            if stats["n_ok"] % 50 == 0:
                el = time.time() - stats["started"]
                log(f"  {job['id']}: {stats['n_ok']}/{len(todo)}  {el / stats['n_ok']:.2f} s/utt")
    finally:
        for fh in fhs.values():
            fh.close()
    for p in paths.values():
        compress(p)

    stats["wall_s"] = time.time() - stats["started"]
    stats["n_in_shard"] = len(rows)
    stats["n_resumed"] = len(rows) - len(todo)
    if cuda:
        stats["peak_mem_mb"] = torch.cuda.max_memory_allocated() / 2 ** 20
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="model key, e.g. drax or drax@bf16")
    ap.add_argument("--lane", type=int, default=0)
    ap.add_argument("--root", required=True, help="campaign output dir")
    ap.add_argument("--data", required=True)
    ap.add_argument("--deadline", type=float, required=True)
    args = ap.parse_args()

    st = ST.State(Path(args.root), Path(args.data))
    cfg = st.config()
    model, _, precision = args.model.partition("@")
    log_path = st.logs / f"lane{args.lane}.log"

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] [lane{args.lane} {args.model}] {msg}"
        print(line, flush=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    import torch
    log(f"host {socket.gethostname()}  cuda={torch.cuda.is_available()}  "
        f"device={torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}")

    fam = None
    n_jobs = 0
    while time.time() < args.deadline:
        if st.should_yield(args.model):
            log("yielding: another model has lower-tier work waiting")
            break
        job = st.claim_next(args.model, args.lane)
        if job is None:
            log("nothing claimable for this model")
            break
        if fam is None:
            t0 = time.time()
            try:
                from campaign import families
                fam = families.load(model, precision or None)
            except Exception as e:
                log(f"MODEL LOAD FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}")
                st.mark_model_failed(args.model, f"{type(e).__name__}: {e}")
                st.release(job["id"])
                return 3
            log(f"model loaded in {time.time() - t0:.0f} s")
        try:
            stats = run_job(job, fam, st, args.deadline, cfg, log)
        except Exception as e:
            log(f"JOB CRASHED {job['id']}: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            st.release(job["id"], crashed=True)
            continue
        st.mark_done(job["id"], dict(stats, job=job["id"], model=job["model"], lane=args.lane))
        n_jobs += 1
        el = stats["wall_s"]
        log(f"done {job['id']} [{stats['status']}] {stats['n_ok']} utts in {el / 60:.1f} min "
            f"({el / max(stats['n_ok'], 1):.2f} s/utt, RTF {el / max(stats['audio_s'], 1e-6):.3f})")
    log(f"exiting after {n_jobs} jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
