"""Audio loading via soundfile; `datasets` now needs torchcodec, which breaks on Kaggle."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
import soundfile as sf

TARGET_SR = 16000


@dataclass
class Utterance:
    id: str
    audio_path: str
    text: str
    duration_s: float


def load_audio(path: str, target_sr: int = TARGET_SR) -> np.ndarray:
    audio, sr = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != target_sr:
        import librosa

        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    return audio.astype(np.float32)


def iter_librispeech(root: str) -> Iterator[Utterance]:
    root_p = Path(root)
    if not root_p.exists():
        raise FileNotFoundError(root)

    for trans in sorted(root_p.rglob("*.trans.txt")):
        refs = {}
        with open(trans, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" ", 1)
                if len(parts) == 2:
                    refs[parts[0]] = parts[1]
        for uid, text in sorted(refs.items()):
            p = trans.parent / f"{uid}.flac"
            if not p.exists():
                continue
            info = sf.info(str(p))
            yield Utterance(uid, str(p), text, info.frames / info.samplerate)


def iter_manifest(path: str) -> Iterator[Utterance]:
    """JSONL per utterance: {"id":.., "audio":.., "text":..}. Entry point for any corpus."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            ap = d["audio"]
            dur = d.get("duration_s")
            if dur is None:
                info = sf.info(ap)
                dur = info.frames / info.samplerate
            yield Utterance(str(d.get("id", Path(ap).stem)), ap, d["text"], float(dur))


def iter_utterances(source: str, path: str) -> Iterator[Utterance]:
    if source == "librispeech":
        return iter_librispeech(path)
    if source == "manifest":
        return iter_manifest(path)
    raise ValueError(f"unknown source: {source}")
