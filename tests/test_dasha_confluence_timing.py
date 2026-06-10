"""Tests for the confluence timing model + longitude builder."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.etl.build_longitudes import _GRAHAS, build, longitudes_for
from app.medini.ml.dasha_confluence_timing import (
    _ang_sep, _confluence, dose_response, peak_test,
)


# ── longitude builder ───────────────────────────────────────────────────────
def test_longitudes_for_shape() -> None:
    row = longitudes_for(2451545.0)  # J2000
    assert set(row) == {f"{g.lower()}_lon" for g in _GRAHAS}
    assert all(0.0 <= v < 360.0 for v in row.values())


def test_build_skips_missing_jd() -> None:
    charts = pd.DataFrame([
        {"person_id": "p1", "birth_jd_used": 2451545.0},
        {"person_id": "p2", "birth_jd_used": None},
    ])
    out = build(charts)
    assert list(out["person_id"]) == ["p1"] and "venus_lon" in out.columns


# ── confluence scoring ──────────────────────────────────────────────────────
def test_ang_sep_wraps() -> None:
    assert _ang_sep(10, 350) == 20
    assert _ang_sep(0, 180) == 180


def _facts(**over):
    f = {"houses": {"Venus": 7, "Mars": 1}, "signs": {"Venus": 7, "Mars": 7},
         "lons": {}, "prim": {"Venus"}, "d9": set(), "karaka": {"Venus"},
         "combust": set(), "good": {"Venus"}}
    f.update(over)
    return f


def test_confluence_counts_families() -> None:
    f = _facts()
    # MD=Venus is primary sig (F1), karaka (F4), well-dignified (F5) → ≥3
    c = _confluence("Venus", "Sun", f)
    assert c >= 3
    # neither lord activates → low
    assert _confluence("Sun", "Moon", _facts(prim=set(), karaka=set(), good=set())) == 0


def test_confluence_max_bounded() -> None:
    assert 0 <= _confluence("Venus", "Mars", _facts()) <= 6


# ── tests A & B on synthetic data ───────────────────────────────────────────
def _planted_table(signal: bool, n=200, seed=0):
    """Each person has 9 windows; if signal, the event sits in the max-conf one."""
    rng = np.random.default_rng(seed)
    rows = []
    for pid in range(n):
        confs = rng.integers(0, 7, size=9)
        ev_idx = int(np.argmax(confs)) if signal else int(rng.integers(0, 9))
        for j in range(9):
            rows.append({"person_id": pid, "md_seq": j, "ad_seq": 0,
                         "conf": int(confs[j]), "dur": 500.0, "age": 30.0,
                         "n_event": int(j == ev_idx), "is_first_event": j == ev_idx,
                         "in_band": True})
    return pd.DataFrame(rows)


def test_peak_test_detects_planted_signal() -> None:
    sig = peak_test(_planted_table(True), k=200, seed=1)
    assert sig["mean_percentile"] > 0.7 and sig["z"] > 3
    nul = peak_test(_planted_table(False), k=200, seed=1)
    assert abs(nul["mean_percentile"] - 0.5) < 0.06


def test_dose_response_runs_and_shapes() -> None:
    dr = dose_response(_planted_table(True))
    assert "curve" in dr and "trend_rho" in dr and "chi2_p" in dr
    assert all("rate_per_1k_yr" in r for r in dr["curve"])
