"""Load Whisfusion (frozen Whisper encoder + masked-diffusion decoder) for inference."""

from __future__ import annotations

from dataclasses import dataclass

import torch

import wf_compat

wf_compat.install()

from lit_gpt.diffmodel import TransEncoder, Config  # noqa: E402
from safetensors.torch import load_file  # noqa: E402
from transformers import (  # noqa: E402
    AutoTokenizer,
    WhisperForConditionalGeneration,
    WhisperProcessor,
)

DEFAULT_MODEL_NAME = "Diff_LLaMA_170M"
DEFAULT_TOKENIZER = "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T"
DEFAULT_WHISPER = "openai/whisper-small"


def pick_dtype(device: str, requested: str = "auto") -> torch.dtype:
    """The paper runs bf16; T4 and P100 do not support it, so we fall back to fp16."""
    if requested != "auto":
        return {"fp16": torch.float16, "bf16": torch.bfloat16, "fp32": torch.float32}[requested]
    if device != "cuda":
        return torch.float32
    return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16


@dataclass
class Whisfusion:
    model: TransEncoder
    config: Config
    tokenizer: object
    whisper_processor: object
    whisper_encoder: object
    device: str
    dtype: torch.dtype

    @property
    def mask_token_id(self) -> int:
        return self.config.padded_vocab_size

    @property
    def pad_token_id(self) -> int:
        return self.tokenizer.pad_token_id


def load(
    base_model_path: str,
    adapter_path: str,
    model_name: str = DEFAULT_MODEL_NAME,
    tokenizer_name: str = DEFAULT_TOKENIZER,
    whisper_name: str = DEFAULT_WHISPER,
    device: str | None = None,
    dtype: str = "auto",
    verbose: bool = True,
) -> Whisfusion:
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    torch_dtype = pick_dtype(device, dtype)

    if verbose:
        name = torch.cuda.get_device_name(0) if device == "cuda" else "cpu"
        print(f"[wf] device={device} ({name}) dtype={torch_dtype}")

    config = Config.from_name(model_name)
    model = TransEncoder(config)

    if base_model_path:
        if base_model_path.endswith(".safetensors"):
            base = load_file(base_model_path)
        else:
            base = torch.load(base_model_path, map_location="cpu", weights_only=False)
            base = base.get("state_dict", base)
        res = model.load_state_dict(base, strict=False)
        if verbose:
            print(f"[wf] base: {len(base)} keys, {len(res.missing_keys)} missing")

    # Stage 2 carries the whole decoder including cross-attention, so it overwrites
    # most of the base weights.
    ad = torch.load(adapter_path, map_location="cpu", weights_only=False)
    ad = ad.get("state_dict", ad) if isinstance(ad, dict) else ad
    res = model.load_state_dict(ad, strict=False)
    if verbose:
        print(f"[wf] adapter: {len(ad)} keys, {len(res.missing_keys)} missing, "
              f"{len(res.unexpected_keys)} unexpected")
    if res.missing_keys:
        raise RuntimeError(
            f"uninitialised parameters after loading: {res.missing_keys[:10]}"
            f"{' ...' if len(res.missing_keys) > 10 else ''}"
        )

    model = model.to(device=device, dtype=torch_dtype).eval()

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    whisper_processor = WhisperProcessor.from_pretrained(whisper_name)
    whisper = WhisperForConditionalGeneration.from_pretrained(whisper_name)
    whisper = whisper.to(device=device, dtype=torch_dtype).eval()

    if verbose:
        n = sum(p.numel() for p in model.parameters())
        ne = sum(p.numel() for p in whisper.model.encoder.parameters())
        print(f"[wf] decoder {n/1e6:.1f}M · Whisper encoder {ne/1e6:.1f}M")

    return Whisfusion(
        model=model,
        config=config,
        tokenizer=tokenizer,
        whisper_processor=whisper_processor,
        whisper_encoder=whisper.model.encoder,
        device=device,
        dtype=torch_dtype,
    )


@torch.no_grad()
def encode_audio(wf: Whisfusion, audio, sampling_rate: int = 16000) -> torch.Tensor:
    """1-D float audio -> (1, T_cond, n_embd) conditioning for the decoder."""
    inputs = wf.whisper_processor(audio, sampling_rate=sampling_rate, return_tensors="pt")
    feats = inputs.input_features.to(device=wf.device, dtype=wf.dtype)
    return wf.whisper_encoder(feats).last_hidden_state.to(wf.dtype)
