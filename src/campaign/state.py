"""Filesystem state shared by the orchestrator and the workers.

    <root>/run_config.json   the resolved config
    <root>/plan.json         every job, sorted by (tier, order)
    <root>/state/claims/     <job>.claim, created with O_EXCL by the worker that takes it
    <root>/state/done/       <job>.json, written when a job ends (done, partial or failed)
    <root>/state/attempts/   crash counters
    <root>/state/failed_models/
    <root>/dumps/<job>/<arm>.jsonl.gz
    <data>/manifests/<set>.jsonl | <set>.failed

Nothing here is held in memory across processes; every question is answered from the files,
so a worker that dies leaves nothing inconsistent behind.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from campaign import config as C

MAX_ATTEMPTS = 2


class State:
    def __init__(self, root: Path, data: Path):
        self.root = Path(root)
        self.data = Path(data)
        self.claims = self.root / "state" / "claims"
        self.done_dir = self.root / "state" / "done"
        self.attempts = self.root / "state" / "attempts"
        self.failed_models = self.root / "state" / "failed_models"
        self.dumps = self.root / "dumps"
        self.logs = self.root / "logs"
        self.analysis = self.root / "analysis"
        self.manifests = self.data / "manifests"
        for d in (self.claims, self.done_dir, self.attempts, self.failed_models, self.dumps,
                  self.logs, self.analysis, self.manifests):
            d.mkdir(parents=True, exist_ok=True)
        self._plan = None
        self._man: dict[str, list[dict]] = {}

    # --------------------------------------------------------------------------------- config

    def config(self) -> dict:
        with open(self.root / "run_config.json", encoding="utf-8") as f:
            return json.load(f)

    def plan(self) -> list[dict]:
        if self._plan is None:
            with open(self.root / "plan.json", encoding="utf-8") as f:
                self._plan = json.load(f)
        return self._plan

    def manifest(self, set_name: str) -> list[dict]:
        if set_name not in self._man:
            with open(self.manifests / f"{set_name}.jsonl", encoding="utf-8") as f:
                self._man[set_name] = [json.loads(line) for line in f if line.strip()]
        return self._man[set_name]

    # ---------------------------------------------------------------------------------- facts

    def manifest_ready(self, s: str) -> bool:
        return (self.manifests / f"{s}.jsonl").exists()

    def manifest_failed(self, s: str) -> bool:
        return (self.manifests / f"{s}.failed").exists()

    def prep_finished(self) -> bool:
        return (self.manifests / "_prep_done").exists()

    def is_done(self, jid: str) -> bool:
        return (self.done_dir / f"{jid}.json").exists()

    def is_claimed(self, jid: str) -> bool:
        return (self.claims / f"{jid}.claim").exists()

    def model_failed(self, mkey: str) -> bool:
        return (self.failed_models / f"{mkey}.txt").exists()

    def shard_empty(self, job: dict) -> bool:
        """Planned from an estimate of the set size; the manifest may be shorter."""
        return job["shard"] * job["shard_size"] >= len(self.manifest(job["set"]))

    def status(self, job: dict) -> str:
        """done | claimed | ready | waiting (for data) | dead (can never run)."""
        jid = job["id"]
        if self.is_done(jid):
            return "done"
        if self.is_claimed(jid):
            return "claimed"
        if self.model_failed(C.model_key(job)) or self.manifest_failed(job["set"]):
            return "dead"
        if not self.manifest_ready(job["set"]):
            return "dead" if self.prep_finished() else "waiting"
        if self.shard_empty(job):
            return "dead"
        return "ready"

    # ------------------------------------------------------------------------------- actions

    def claim_next(self, mkey: str, lane: int) -> dict | None:
        for job in self.plan():
            if C.model_key(job) != mkey or self.status(job) != "ready":
                continue
            try:
                fd = os.open(self.claims / f"{job['id']}.claim", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                continue
            with os.fdopen(fd, "w") as f:
                f.write(json.dumps({"lane": lane, "pid": os.getpid(), "t": time.time()}))
            return job
        return None

    def release(self, jid: str, crashed: bool = False) -> None:
        if crashed:
            p = self.attempts / f"{jid}.n"
            n = int(p.read_text()) + 1 if p.exists() else 1
            p.write_text(str(n))
            if n >= MAX_ATTEMPTS:
                self.mark_done(jid, {"job": jid, "status": "crashed", "attempts": n})
        (self.claims / f"{jid}.claim").unlink(missing_ok=True)

    def mark_done(self, jid: str, stats: dict) -> None:
        C.write_json(self.done_dir / f"{jid}.json", stats)

    def mark_model_failed(self, mkey: str, msg: str) -> None:
        (self.failed_models / f"{mkey}.txt").write_text(msg, encoding="utf-8")

    def orphaned_claims(self, lane: int) -> list[str]:
        """Claims held by a lane whose worker has exited, with no done marker."""
        out = []
        for p in self.claims.glob("*.claim"):
            jid = p.name[:-len(".claim")]
            if self.is_done(jid):
                continue
            try:
                info = json.loads(p.read_text())
            except Exception:
                continue
            if info.get("lane") == lane:
                out.append(jid)
        return out

    # ------------------------------------------------------------------------------ schedule

    def min_ready_tier(self) -> dict[str, int]:
        """Lowest tier with ready work, per model key."""
        out: dict[str, int] = {}
        for job in self.plan():
            k = C.model_key(job)
            if k in out and out[k] <= job["tier"]:
                continue
            if self.status(job) == "ready":
                out[k] = min(out.get(k, 99), job["tier"])
        return out

    def started(self) -> set[str]:
        """Model keys that have had their turn: a finished job, or one in flight on some lane.

        A model another lane is already running must count as started, or the two lanes keep
        yielding to each other and neither does any work.
        """
        out = set()
        for p in self.done_dir.glob("*.json"):
            try:
                s = json.loads(p.read_text())
            except Exception:
                continue
            if s.get("model"):
                out.add(s["model"] + (f"@{s['precision']}" if s.get("precision") else ""))
        by_id = {j["id"]: j for j in self.plan()}
        for p in self.claims.glob("*.claim"):
            job = by_id.get(p.name[: -len(".claim")])
            if job is not None:
                out.add(C.model_key(job))
        return out

    def should_yield(self, mkey: str) -> bool:
        """Give up the GPU when another model needs it more: it has work in a lower tier, or it
        has equal-tier work and has not run at all yet. Without the second rule a lane sticks
        with its model for the whole tier and a model late in the tier never starts."""
        tiers = self.min_ready_tier()
        mine = tiers.get(mkey)
        if mine is None:
            return False
        others = {k: t for k, t in tiers.items() if k != mkey}
        if not others:
            return False
        if min(others.values()) < mine:
            return True
        done = self.started()
        return mkey in done and any(t == mine and k not in done for k, t in others.items())

    def choose_model(self, current: str | None, preferred: list[str], busy: set[str]) -> str | None:
        """Model for a free lane: lowest ready tier first, then the lane's current model, then
        one no other lane is running, then the lane's preference order."""
        tiers = self.min_ready_tier()
        if not tiers:
            return None
        best = min(tiers.values())
        cands = [k for k, t in tiers.items() if t == best]
        # a model that has never run comes first, so every model is represented in a tier
        done = self.started()
        fresh = [k for k in cands if k not in done and k not in busy]
        if fresh:
            for p in preferred:
                if p in fresh:
                    return p
            return sorted(fresh)[0]
        if current in cands:
            return current
        free = [k for k in cands if k not in busy] or cands
        for p in preferred:
            if p in free:
                return p
        return sorted(free)[0]

    def any_waiting(self) -> bool:
        return any(self.status(j) == "waiting" for j in self.plan())

    def counts(self) -> dict:
        out: dict[str, int] = {}
        for j in self.plan():
            s = self.status(j)
            out[s] = out.get(s, 0) + 1
        return out
