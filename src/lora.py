"""Minimal LoRA for the Whisfusion decoder, switchable at run time.

One adapter lives in the model at a time. With it disabled the model is exactly the base model,
so one copy of the weights serves both the anchor and the explorer.
"""

from __future__ import annotations

import math

import torch
from torch import nn

# every linear layer of the 18 decoder blocks; the lm_head stays frozen
TARGETS = ("attn.attn", "attn.proj", "cross_attn.q_proj", "cross_attn.kv_proj", "cross_attn.proj",
           "mlp.swiglu.w1", "mlp.swiglu.w2", "mlp.swiglu.w3")


class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, r: int, alpha: float):
        super().__init__()
        self.base = base
        self.scale = alpha / r
        self.A = nn.Parameter(torch.empty(r, base.in_features, dtype=torch.float32))
        self.B = nn.Parameter(torch.zeros(base.out_features, r, dtype=torch.float32))
        nn.init.kaiming_uniform_(self.A, a=math.sqrt(5))
        self.enabled = False

    def forward(self, x):
        y = self.base(x)
        if not self.enabled:
            return y
        d = (x.float() @ self.A.t()) @ self.B.t()
        return y + (d * self.scale).to(y.dtype)


def inject(model: nn.Module, r: int = 16, alpha: float = 32.0) -> list[nn.Parameter]:
    for p in model.parameters():
        p.requires_grad_(False)
    swaps = [(n, m) for n, m in model.named_modules()
             if isinstance(m, nn.Linear) and n.startswith("transformer.h.") and n.endswith(TARGETS)]
    for name, lin in swaps:
        parent = model.get_submodule(name.rsplit(".", 1)[0])
        lora = LoRALinear(lin, r, alpha).to(lin.weight.device)
        setattr(parent, name.rsplit(".", 1)[1], lora)
    return [p for m in model.modules() if isinstance(m, LoRALinear) for p in (m.A, m.B)]


def set_enabled(model: nn.Module, on: bool) -> None:
    for m in model.modules():
        if isinstance(m, LoRALinear):
            m.enabled = on


def lora_state(model: nn.Module) -> dict:
    return {k: v.detach().cpu() for k, v in model.state_dict().items() if k.endswith((".A", ".B"))}


def load(model: nn.Module, path: str) -> dict:
    """Inject (if needed) and load an adapter saved by tools/train_explorer.py."""
    ck = torch.load(path, map_location="cpu", weights_only=False)
    if not any(isinstance(m, LoRALinear) for m in model.modules()):
        inject(model, ck["r"], ck["alpha"])
    res = model.load_state_dict(ck["state"], strict=False)
    bad = [k for k in res.unexpected_keys]
    if bad:
        raise RuntimeError(f"adapter keys not in the model: {bad[:5]}")
    return ck
