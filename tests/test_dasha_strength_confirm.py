"""Tests for the pre-registered strength-confirmation design."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml import dasha_strength_confirm as sc


def test_half_split_deterministic_and_balanced() -> None:
    halves = [sc._half(f"LA:{i}") for i in range(2000)]
    assert sc._half("LA:1") == sc._half("LA:1")          # stable
    frac_a = halves.count("A") / len(halves)
    assert 0.45 < frac_a < 0.55                          # ~balanced


def _rec(flags_event: bool, p_flag: float, n=10, seed=0):
    """One synthetic native: n windows, equal duration, a fraction p_flag flagged;
    the event window's flag set explicitly."""
    rng = np.random.default_rng(seed)
    fl = rng.random(n) < p_flag
    w = np.full(n, 1.0 / n)
    return {"dur": np.ones(n), "w": w,
            "flags": {"S": fl}, "ehit": {"S": flags_event}}


def test_lift_z_and_perm_on_planted_signal() -> None:
    # every native: 20% of windows flagged, but the event ALWAYS lands on a flag
    # → big positive lift, tiny p.
    recs = []
    for i in range(300):
        r = _rec(flags_event=True, p_flag=0.2, n=10, seed=i)
        recs.append(r)
    out = sc._lift_z(recs, "S")
    assert out["lift"] > 3 and out["z"] > 8
    p = sc._perm_p(recs, "S", k=1000, seed=1)
    assert p < 0.01


def test_perm_null_is_uniformish() -> None:
    # event flag drawn consistently with exposure → no signal → p not tiny.
    recs = []
    for i in range(300):
        rng = np.random.default_rng(i)
        fl = rng.random(10) < 0.3
        w = np.full(10, 0.1)
        ev = bool(fl[rng.choice(10, p=w)])               # event ∝ duration (null)
        recs.append({"dur": np.ones(10), "w": w, "flags": {"S": fl},
                     "ehit": {"S": ev}})
    p = sc._perm_p(recs, "S", k=1000, seed=2)
    assert 0.05 < p < 0.95
