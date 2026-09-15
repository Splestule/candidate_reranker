"""Pure-PyTorch stand-ins for the CUDA extensions lit-gpt/SMDM imports.

FlashAttention 2 needs Ampere; Kaggle serves T4 or P100. Registering replacements in
sys.modules keeps the upstream checkout untouched. Call install() before importing lit_gpt.
"""

from __future__ import annotations

import importlib.machinery
import sys
import types

import torch
import torch.nn as nn
import torch.nn.functional as F

_INSTALLED = False


def _make_module(name: str) -> types.ModuleType:
    # importlib.util.find_spec() raises ValueError on a module whose __spec__ is
    # None, and transformers calls it while probing for flash-attn.
    m = types.ModuleType(name)
    m.__spec__ = importlib.machinery.ModuleSpec(name, None)
    m.__file__ = f"<wf_compat shim: {name}>"
    return m


def _apply_rotary(x1, x2, cos, sin, out1, out2, conj):
    """rotary_emb.apply_rotary. out1 may alias x1, so compute both before writing."""
    a, b = x1.float(), x2.float()
    c, s = cos.float(), sin.float()
    if conj:
        o1, o2 = a * c + b * s, -a * s + b * c
    else:
        o1, o2 = a * c - b * s, a * s + b * c
    out1.copy_(o1.to(out1.dtype))
    out2.copy_(o2.to(out2.dtype))


class SwiGLU(nn.Module):
    """Unpacked xformers.ops.SwiGLU; w1/w2/w3 match the checkpoint keys."""

    def __init__(self, in_features, hidden_features, out_features=None,
                 bias=True, *, _pack_weights=True):
        super().__init__()
        out_features = out_features if out_features is not None else in_features
        self.w1 = nn.Linear(in_features, hidden_features, bias=bias)
        self.w2 = nn.Linear(in_features, hidden_features, bias=bias)
        self.w3 = nn.Linear(hidden_features, out_features, bias=bias)

    def forward(self, x):
        return self.w3(F.silu(self.w1(x)) * self.w2(x))


class RMSNorm(nn.Module):
    """Stand-in for lit_gpt.rmsnorm.FusedRMSNorm."""

    def __init__(self, size: int, dim: int = -1, eps: float = 1e-5):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(size))
        self.eps = eps
        self.dim = dim

    def forward(self, x):
        dtype = x.dtype
        xf = x.float()  # mean(x*x) overflows in fp16 and surfaces as NaN layers later
        xf = xf * torch.rsqrt(torch.mean(xf * xf, dim=self.dim, keepdim=True) + self.eps)
        return xf.to(dtype) * self.weight


def _flash_attn_func(q, k, v, dropout_p=0.0, softmax_scale=None, causal=False, **kw):
    """FlashAttention-2 signature, SDPA underneath. (B, T, H, D) in and out."""
    q, k, v = q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2)
    if q.shape[1] != k.shape[1]:  # GQA / MQA
        k = k.repeat_interleave(q.shape[1] // k.shape[1], dim=1)
        v = v.repeat_interleave(q.shape[1] // v.shape[1], dim=1)
    y = F.scaled_dot_product_attention(q, k, v, dropout_p=dropout_p,
                                       scale=softmax_scale, is_causal=causal)
    return y.transpose(1, 2)


def install(verbose: bool = True) -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    if "lit_gpt.diffmodel" in sys.modules or "lit_gpt.model" in sys.modules:
        raise RuntimeError(
            "install() must run before lit_gpt is imported: lit_gpt copies "
            "apply_rotary_emb_func into its own namespace at import time."
        )

    # Let transformers finish its flash-attn probe before the shim shadows it.
    try:
        import transformers  # noqa: F401
    except Exception:
        pass

    if "rotary_emb" not in sys.modules:
        m = _make_module("rotary_emb")
        m.apply_rotary = _apply_rotary
        sys.modules["rotary_emb"] = m

    for name in ("dropout_layer_norm", "xentropy_cuda_lib"):
        # Empty is fine: FusedRMSNorm is replaced below and fused cross-entropy
        # is training-only.
        if name not in sys.modules:
            sys.modules[name] = _make_module(name)

    try:
        import flash_attn  # noqa: F401
    except Exception:
        m = _make_module("flash_attn")
        m.flash_attn_func = _flash_attn_func
        sys.modules["flash_attn"] = m

    try:
        from xformers.ops import SwiGLU as _  # noqa: F401
    except Exception:
        xf = sys.modules.get("xformers") or _make_module("xformers")
        ops = _make_module("xformers.ops")
        ops.SwiGLU = SwiGLU
        xf.ops = ops
        sys.modules["xformers"] = xf
        sys.modules["xformers.ops"] = ops

    # Config.norm_class imports FusedRMSNorm lazily, so patching the attribute is enough.
    import lit_gpt.rmsnorm as _rms

    _rms.FusedRMSNorm = RMSNorm

    _INSTALLED = True
    if verbose:
        print("[wf_compat] shims active: rotary_emb, dropout_layer_norm, "
              "flash_attn, xformers.ops.SwiGLU, FusedRMSNorm")


def assert_no_cuda_ext() -> None:
    """flash-attn installed via pip wins over the shim and dies on T4/P100."""
    from lightning_utilities.core.imports import RequirementCache

    if bool(RequirementCache("flash-attn>=2.0.0.post1")):
        raise RuntimeError("flash-attn is pip-installed; uninstall it: pip uninstall -y flash-attn")
