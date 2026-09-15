"""Notebook glue: locate attached data, install deps, run scripts in src/."""

from __future__ import annotations

import glob
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

WORK = Path("/kaggle/working")
CODE = WORK / "candidate_reranker"
RESULTS = WORK / "results"
UPSTREAM = WORK / "Whisfusion"
UPSTREAM_URL = "https://github.com/taeyoun811/Whisfusion.git"


def github_token() -> str | None:
    try:
        from kaggle_secrets import UserSecretsClient

        return UserSecretsClient().get_secret("GITHUB_TOKEN")
    except Exception:
        return None


def sync(repo_url: str, branch: str = "main") -> str:
    """Clone or fast-forward the repo. Returns the short commit hash."""
    token = github_token()
    url = repo_url
    if token and url.startswith("https://"):
        url = url.replace("https://", f"https://{token}@")

    if (CODE / ".git").exists():
        subprocess.run(["git", "-C", str(CODE), "fetch", "--depth", "1", "origin", branch],
                       check=True)
        subprocess.run(["git", "-C", str(CODE), "reset", "--hard", f"origin/{branch}"],
                       check=True)
    else:
        subprocess.run(["git", "clone", "--depth", "1", "-b", branch, url, str(CODE)],
                       check=True)

    return subprocess.run(["git", "-C", str(CODE), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


def _find(pattern: str, what: str) -> Path:
    hits = sorted(glob.glob(f"/kaggle/input/{pattern}", recursive=True))
    if not hits:
        raise FileNotFoundError(
            f"{what} not found under /kaggle/input. "
            "Add Input -> Your Work -> Notebook Output -> kaggle_prepare_data"
        )
    return Path(hits[0])


@dataclass
class Env:
    commit: str
    base_model: Path
    adapter: Path
    librispeech: Path
    ood: Path | None
    results: Path
    pythonpath: str

    def splits(self) -> list[str]:
        return sorted(p.name for p in self.librispeech.iterdir() if p.is_dir())


def prepare(commit: str = "") -> Env:
    """Install dependencies, fetch the upstream checkout, resolve data paths."""
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                    str(CODE / "requirements-kaggle.txt")], check=True)

    if not UPSTREAM.exists():
        subprocess.run(["git", "clone", "--depth", "1", UPSTREAM_URL, str(UPSTREAM)], check=True)

    base = _find("**/mdm-170M-*.safetensors", "base SMDM weights")
    adapter = _find("**/whisfusion_stage2_decoder.pt", "Whisfusion checkpoint")
    librispeech = _find("**/LibriSpeech/test-clean", "LibriSpeech").parent
    ood_hits = sorted(glob.glob("/kaggle/input/**/ood", recursive=True))
    ood = Path(ood_hits[0]) if ood_hits else None

    hf = sorted(glob.glob("/kaggle/input/**/hf", recursive=True))
    if hf:
        os.environ["HF_HOME"] = hf[0]

    RESULTS.mkdir(parents=True, exist_ok=True)

    env = Env(
        commit=commit,
        base_model=base,
        adapter=adapter,
        librispeech=librispeech,
        ood=ood,
        results=RESULTS,
        pythonpath=f"{CODE / 'src'}:{UPSTREAM / 'src'}",
    )

    print(f"commit      {commit or '(unknown)'}")
    print(f"base model  {base}")
    print(f"adapter     {adapter}")
    print(f"librispeech {librispeech}  {env.splits()}")
    if ood:
        print(f"ood         {ood}  {sorted(p.name for p in ood.iterdir() if p.is_dir())}")
    return env


def run(env: Env, script: str, *args: str) -> int:
    """Run a script from src/ and stream its output into the notebook."""
    cmd = [sys.executable, str(CODE / "src" / script), *map(str, args)]
    proc = subprocess.Popen(cmd, env=dict(os.environ, PYTHONPATH=env.pythonpath),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    for line in proc.stdout:
        print(line, end="")
    return proc.wait()


def gpu_info() -> None:
    import torch

    print(f"torch {torch.__version__}  cuda={torch.cuda.is_available()}")
    if not torch.cuda.is_available():
        print("no GPU: Settings -> Accelerator -> GPU T4 x2")
        return
    major, minor = torch.cuda.get_device_capability(0)
    print(f"{torch.cuda.get_device_name(0)}  compute capability {major}.{minor}")
    if major < 8:
        print("Turing/Pascal: no bf16, no FlashAttention 2 -- handled by wf_compat")
