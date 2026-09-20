#!/usr/bin/env python3
"""Download every evaluation set and write it as a JSONL manifest of 16 kHz mono audio.

Each set is filtered to the same bounds (config.MIN_DUR..MAX_DUR, <= MAX_REF_WORDS words) and
ordered by a hash of the utterance id, so shard k of a set is the same utterances for every
model. A manifest appears atomically when its set is complete; a set that fails leaves
<set>.failed instead, and the jobs that need it are skipped rather than retried forever.

Runs as its own process next to the GPU workers; sets come out in config.PREP_ORDER.
"""

from __future__ import annotations

import argparse
import io
import json
import random
import re
import shutil
import subprocess
import sys
import tarfile
import time
import traceback
import zipfile
import zlib
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from campaign import config as C  # noqa: E402

SR = 16000
SALT = "campaign-v1"


def order_key(uid: str) -> int:
    return zlib.crc32(f"{SALT}|{uid}".encode("utf-8"))


def safe_name(uid: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]", "_", uid)[:120]
    return f"{base}_{zlib.crc32(uid.encode('utf-8')) & 0xffffff:06x}"


def n_words(text: str) -> int:
    import scorers
    return len(scorers.normalize(text).split())


def keep(dur: float, text: str) -> bool:
    if not text or not (C.MIN_DUR <= dur <= C.MAX_DUR):
        return False
    return 1 <= n_words(text) <= C.MAX_REF_WORDS


def to_mono16k(audio: np.ndarray, sr: int) -> np.ndarray:
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)
    if sr != SR:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=SR).astype(np.float32)
    return audio


def decode_bytes(b: bytes) -> tuple[np.ndarray, int]:
    try:
        a, sr = sf.read(io.BytesIO(b), dtype="float32", always_2d=False)
        return a, sr
    except Exception:
        # mp3 on an old libsndfile, or anything else soundfile refuses: let ffmpeg do it
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            f.write(b)
            p = f.name
        try:
            out = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", p, "-f", "f32le",
                                  "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True)
            return np.frombuffer(out.stdout, dtype=np.float32).copy(), SR
        finally:
            Path(p).unlink(missing_ok=True)


def write_flac(path: Path, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0.999:
        audio = audio * (0.999 / peak)
    sf.write(str(path), audio, SR, format="FLAC", subtype="PCM_16")


def finish(man_dir: Path, name: str, rows: list[dict], meta: dict) -> None:
    rows.sort(key=lambda r: order_key(r["id"]))
    for i, r in enumerate(rows):
        r["rank"] = i
    tmp = man_dir / f"{name}.jsonl.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    meta.update(n_selected=len(rows), audio_min=round(sum(r["duration_s"] for r in rows) / 60, 2),
                n_clusters=len({r["cluster"] for r in rows}))
    C.write_json(man_dir / f"{name}.meta.json", meta)
    tmp.replace(man_dir / f"{name}.jsonl")
    print(f"[prep] {name}: {len(rows)} utts, {meta['audio_min']} min, "
          f"{meta['n_clusters']} clusters", flush=True)


def select(cands: list[dict], n_max: int | None) -> list[dict]:
    cands = [c for c in cands if keep(c["duration_s"], c["text"])]
    cands.sort(key=lambda c: order_key(c["id"]))
    return cands if n_max is None else cands[:n_max]


# ---------------------------------------------------------------------------------------------
# clusters: the unit a cluster bootstrap resamples. Speaker where known, else recording.
# ---------------------------------------------------------------------------------------------

AMI_MEETING = re.compile(r"((?:EN|ES|IS|TS|IB|IN)\d{4}[a-z])", re.I)


def cluster_of(set_name: str, uid: str, row: dict) -> str:
    if row.get("speaker_id") not in (None, ""):
        return str(row["speaker_id"])
    if set_name == "ami":
        m = AMI_MEETING.search(uid)
        if m:
            return m.group(1).upper()
    if set_name == "gigaspeech" and "_S" in uid:
        return uid.split("_S")[0]
    if set_name == "earnings22":
        return re.split(r"[_/-]", uid)[0]
    if set_name == "voxpopuli":
        return uid.split("_")[0]
    if set_name == "spgispeech" and "/" in uid:
        return uid.split("/")[0]
    if set_name == "common_voice":
        return uid              # no speaker ids in the leaderboard copy
    return uid


# ---------------------------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------------------------

def hf_file(repo: str, filename: str, raw: Path) -> Path:
    from huggingface_hub import hf_hub_download
    for attempt in range(4):
        try:
            return Path(hf_hub_download(repo_id=repo, filename=filename, repo_type="dataset",
                                        local_dir=str(raw / repo.replace("/", "__"))))
        except Exception as e:
            print(f"[prep] download {repo}/{filename} failed ({type(e).__name__}: {e}), retry",
                  flush=True)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"cannot download {repo}/{filename}")


def build_parquet(name: str, spec: dict, files: list[Path], audio_dir: Path) -> tuple[list[dict], dict]:
    import pyarrow.parquet as pq

    cands = []
    audio_by_id: dict[str, bytes] = {}
    n_total = 0
    for fp in files:
        t = pq.read_table(str(fp))
        cols = t.column_names
        id_col = "id" if "id" in cols else ("file" if "file" in cols else cols[0])
        text_col = next(c for c in ("text", "transcription", "sentence", "normalized_text") if c in cols)
        ids = [str(x) for x in t.column(id_col).to_pylist()]
        texts = t.column(text_col).to_pylist()
        durs = t.column("audio_length_s").to_pylist() if "audio_length_s" in cols else None
        spk = t.column("speaker_id").to_pylist() if "speaker_id" in cols else None
        audio = t.column("audio").to_pylist()
        n_total += len(ids)
        for i, uid in enumerate(ids):
            b = audio[i]["bytes"] if isinstance(audio[i], dict) else None
            if not b:
                continue
            if durs is not None and durs[i] is not None:
                dur = float(durs[i])
            else:
                try:
                    info = sf.info(io.BytesIO(b))
                    dur = info.frames / info.samplerate
                except Exception:
                    continue
            row = {"speaker_id": spk[i] if spk else None}
            cands.append(dict(id=uid, text=str(texts[i] or ""), duration_s=round(dur, 3),
                              cluster=cluster_of(name, uid, row)))
            audio_by_id[uid] = b
        del t, audio

    chosen = select(cands, spec.get("n_max"))
    rows = []
    for c in chosen:
        try:
            a, sr = decode_bytes(audio_by_id[c["id"]])
            a = to_mono16k(a, sr)
        except Exception as e:
            print(f"[prep] {name}/{c['id']}: undecodable ({type(e).__name__})", flush=True)
            continue
        p = audio_dir / name / f"{safe_name(c['id'])}.flac"
        write_flac(p, a)
        rows.append(dict(c, audio=str(p), lang=spec["lang"], set=name,
                         duration_s=round(len(a) / SR, 3)))
    meta = dict(source=spec.get("repo", C.ESB_REPO), files=[str(f.name) for f in files],
                n_total=n_total, n_passing_filter=len([c for c in cands if keep(c["duration_s"], c["text"])]))
    return rows, meta


def build_esb(name, spec, raw, audio_dir):
    n = spec["n_shards"]
    idx = sorted({min(n - 1, int((i + 0.5) * n / spec["take"])) for i in range(spec["take"])})
    files = [hf_file(C.ESB_REPO, f"{spec['config']}/test-{i:05d}-of-{n:05d}.parquet", raw) for i in idx]
    rows, meta = build_parquet(name, spec, files, audio_dir)
    meta["shards_used"] = idx
    for f in files:
        f.unlink(missing_ok=True)
    return rows, meta


def build_ls(name, spec, raw, audio_dir):
    files = [hf_file(spec["repo"], fn, raw) for fn in spec["files"]]
    rows, meta = build_parquet(name, spec, files, audio_dir)
    return rows, meta


def build_fleurs(name, spec, raw, audio_dir):
    from huggingface_hub import hf_hub_download
    repo = "google/fleurs"
    d = raw / f"fleurs_{spec['code']}"
    tsv = Path(hf_hub_download(repo, f"data/{spec['code']}/test.tsv", repo_type="dataset", local_dir=str(d)))
    tar = Path(hf_hub_download(repo, f"data/{spec['code']}/audio/test.tar.gz", repo_type="dataset",
                               local_dir=str(d)))
    cands = []
    with open(tsv, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 6:
                continue
            sent_id, fname, raw_text = p[0], p[1], p[2]
            try:
                dur = int(p[5]) / SR
            except ValueError:
                continue
            uid = fname.rsplit(".", 1)[0]
            cands.append(dict(id=uid, text=raw_text, duration_s=round(dur, 3), cluster=f"sent{sent_id}",
                              _fname=fname))
    chosen = {c["_fname"]: c for c in select(cands, spec.get("n_max"))}
    rows = []
    with tarfile.open(tar, "r:gz") as tf:
        for m in tf:
            base = m.name.rsplit("/", 1)[-1]
            if base not in chosen or not m.isfile():
                continue
            b = tf.extractfile(m).read()
            a, sr = decode_bytes(b)
            a = to_mono16k(a, sr)
            c = chosen[base]
            p = audio_dir / name / f"{safe_name(c['id'])}.flac"
            write_flac(p, a)
            rows.append(dict({k: v for k, v in c.items() if not k.startswith("_")}, audio=str(p),
                             lang=spec["lang"], set=name, duration_s=round(len(a) / SR, 3)))
    shutil.rmtree(d, ignore_errors=True)
    return rows, dict(source=repo, code=spec["code"], n_total=len(cands))


SLR83_MIRRORS = ["https://www.openslr.org/resources/83/{}.zip",
                 "https://us.openslr.org/resources/83/{}.zip",
                 "https://openslr.elda.org/resources/83/{}.zip",
                 "https://openslr.trmal.net/resources/83/{}.zip"]


def curl(urls: list[str], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    for url in urls:
        r = subprocess.run(["curl", "-L", "--fail", "--retry", "3", "--connect-timeout", "20",
                            "-s", "-o", str(out), url])
        if r.returncode == 0 and out.exists() and out.stat().st_size > 1000:
            return
        print(f"[prep] {url} failed (curl {r.returncode})", flush=True)
    raise RuntimeError(f"all mirrors failed for {out.name}")


def build_slr83(name, spec, raw, audio_dir):
    rows, per = [], {}
    for sub in spec["subsets"]:
        z = raw / "slr83" / f"{sub}.zip"
        if not z.exists():
            curl([u.format(sub) for u in SLR83_MIRRORS], z)
        cands = []
        with zipfile.ZipFile(z) as zf:
            names = {n.rsplit("/", 1)[-1]: n for n in zf.namelist()}
            index = names.get("line_index.csv")
            if index is None:
                raise RuntimeError(f"{sub}: no line_index.csv")
            for line in zf.read(index).decode("utf-8").splitlines():
                parts = line.strip().split(",", 2)
                if len(parts) != 3:
                    continue
                file_id, text = parts[1].strip(), parts[2].strip()
                if f"{file_id}.wav" not in names:
                    continue
                cands.append(dict(id=file_id, text=text, _member=names[f"{file_id}.wav"],
                                  cluster="_".join(file_id.split("_")[:2])))
            # duration needs the header, so read candidates in order until enough pass
            cands.sort(key=lambda c: order_key(c["id"]))
            got = 0
            for c in cands:
                if got >= spec["per_subset"]:
                    break
                b = zf.read(c["_member"])
                info = sf.info(io.BytesIO(b))
                dur = info.frames / info.samplerate
                if not keep(dur, c["text"]):
                    continue
                a, sr = decode_bytes(b)
                a = to_mono16k(a, sr)
                p = audio_dir / name / f"{safe_name(c['id'])}.flac"
                write_flac(p, a)
                rows.append(dict(id=c["id"], text=c["text"], cluster=c["cluster"], audio=str(p),
                                 lang=spec["lang"], set=name, duration_s=round(len(a) / SR, 3),
                                 subset=sub))
                got += 1
        per[sub] = got
        z.unlink(missing_ok=True)
        print(f"[prep] slr83/{sub}: {got}", flush=True)
    return rows, dict(source="openslr SLR83", per_subset=per)


def read_manifest(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_noise(name, spec, raw, audio_dir, man_dir: Path):
    base = read_manifest(man_dir / f"{spec['base']}.jsonl")[:spec["n"]]
    pool = read_manifest(man_dir / f"{spec['babble_from']}.jsonl")
    snr = float(spec["snr"])
    rows = []
    cache: dict[str, np.ndarray] = {}

    def load(p):
        if p not in cache:
            a, sr = sf.read(p, dtype="float32")
            cache[p] = to_mono16k(a, sr)
        return cache[p]

    for r in base:
        speech = load(r["audio"])
        n = len(speech)
        # seeded by the utterance alone, so every SNR of one utterance shares its noise
        rng = np.random.default_rng(order_key(r["id"]))
        if spec["noise"] == "babble":
            noise = np.zeros(n, dtype=np.float32)
            for j in rng.choice(len(pool), size=min(6, len(pool)), replace=False):
                src = load(pool[int(j)]["audio"])
                src = src / (np.sqrt(np.mean(src ** 2)) + 1e-8)
                reps = int(np.ceil((n + len(src)) / len(src)))
                tiled = np.tile(src, reps)
                off = int(rng.integers(0, len(src)))
                noise += tiled[off:off + n]
        else:
            noise = rng.standard_normal(n).astype(np.float32)
        ps = float(np.mean(speech ** 2)) + 1e-12
        pn = float(np.mean(noise ** 2)) + 1e-12
        mix = speech + noise * np.sqrt(ps / (pn * 10 ** (snr / 10.0)))
        p = audio_dir / name / f"{safe_name(r['id'])}.flac"
        write_flac(p, mix.astype(np.float32))
        rows.append(dict(id=r["id"], text=r["text"], cluster=r["cluster"], audio=str(p),
                         lang=r["lang"], set=name, duration_s=r["duration_s"]))
    if len(cache) > 2000:
        cache.clear()
    return rows, dict(source=f"{spec['base']} + {spec['noise']} @ {snr:g} dB SNR",
                      babble_from=spec["babble_from"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--data", required=True)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    cfg = C.load_config(args.config)
    sets = C.sets_for(cfg)
    data = Path(args.data)
    raw, audio_dir, man_dir = data / "raw", data / "audio", data / "manifests"
    man_dir.mkdir(parents=True, exist_ok=True)

    todo = [s for s in C.PREP_ORDER if s in sets and (args.only is None or s in args.only)]
    t_all = time.time()
    for name in todo:
        spec = sets[name]
        if (man_dir / f"{name}.jsonl").exists():
            print(f"[prep] {name}: already there", flush=True)
            continue
        t0 = time.time()
        try:
            kind = spec["kind"]
            if kind == "hf_parquet":
                rows, meta = build_ls(name, spec, raw, audio_dir)
            elif kind == "esb":
                rows, meta = build_esb(name, spec, raw, audio_dir)
            elif kind == "fleurs":
                rows, meta = build_fleurs(name, spec, raw, audio_dir)
            elif kind == "slr83":
                rows, meta = build_slr83(name, spec, raw, audio_dir)
            elif kind == "noise":
                for dep in (spec["base"], spec["babble_from"]):
                    if not (man_dir / f"{dep}.jsonl").exists():
                        raise RuntimeError(f"needs {dep}, which is not prepared")
                rows, meta = build_noise(name, spec, raw, audio_dir, man_dir)
            else:
                raise ValueError(kind)
            if not rows:
                raise RuntimeError("no utterances survived")
            meta.update(set=name, kind=kind, lang=spec["lang"], role=spec["role"],
                        domain=spec.get("domain"), filter=dict(min_dur=C.MIN_DUR, max_dur=C.MAX_DUR,
                                                               max_ref_words=C.MAX_REF_WORDS),
                        prep_s=round(time.time() - t0, 1))
            finish(man_dir, name, rows, meta)
        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            print(f"[prep] {name} FAILED: {msg}", flush=True)
            traceback.print_exc()
            (man_dir / f"{name}.failed").write_text(msg + "\n" + traceback.format_exc(), encoding="utf-8")
    shutil.rmtree(raw, ignore_errors=True)
    print(f"[prep] all done in {(time.time() - t_all) / 60:.1f} min", flush=True)
    (man_dir / "_prep_done").write_text(str(time.time()), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
