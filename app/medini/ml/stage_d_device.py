"""Fork-A Stage D — device resolver.

Resolves a torch device for DeepHit training based on preference and what's
actually available. CPU is always the safe fallback; DirectML (AMD/Intel
Windows GPU) is preferred on this workstation; CUDA falls through.

This is a spec deviation from the F14 'CPU-only' constraint in the design
spec — switching to GPU is documented in the run record (`device` field)
so any verdict carrying GPU runs can be replayed honestly.

Usage:
    from app.medini.ml.stage_d_device import resolve_device, device_label
    dev = resolve_device("dml")           # or "auto" / "cpu" / "cuda"
    label = device_label(dev)             # e.g. "dml:Radeon RX 9060 XT"

Why a separate module: both stage_d_train (creates model, sends tensors)
and stage_d_evaluate / cross-check scripts (loads model for inference)
need the same resolution. Centralizing avoids divergent resolution.
"""
from __future__ import annotations

import logging

import torch

logger = logging.getLogger(__name__)


def resolve_device(preference: str = "auto") -> torch.device:
    """Resolve a torch device from a preference string.

    `preference`:
      - "auto" — try dml, then cuda, then cpu
      - "dml"  — DirectML; falls back to cpu with a warning if unavailable
      - "cuda" — NVIDIA; falls back to cpu with a warning if unavailable
      - "cpu"  — always cpu
    """
    pref = preference.lower()

    if pref == "cpu":
        return torch.device("cpu")

    if pref in ("dml", "auto"):
        try:
            import torch_directml  # noqa: F401 -- presence check only
            return torch_directml.device()
        except ImportError:
            if pref == "dml":
                logger.warning("torch_directml not installed; falling back to cpu")
            # fall through to cuda check under "auto"
        except Exception as e:
            logger.warning("torch_directml.device() raised %s; falling back", e)

    if pref in ("cuda", "auto"):
        if torch.cuda.is_available():
            return torch.device("cuda:0")
        if pref == "cuda":
            logger.warning("CUDA not available; falling back to cpu")

    return torch.device("cpu")


def device_label(device: torch.device) -> str:
    """Human-readable label for the run record's `device` field."""
    if device.type == "cuda":
        return f"cuda:{torch.cuda.get_device_name(device)}"
    if device.type == "privateuseone":
        # DirectML registers as a `privateuseone` backend in torch.
        try:
            import torch_directml
            return f"dml:{torch_directml.device_name(0)}"
        except Exception:
            return "dml"
    return "cpu"
