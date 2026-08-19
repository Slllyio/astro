"""Track-B vocation harness — pins the statistical machinery and the null result.

Fast: the stratified-permutation test is exercised on synthetic arrays (no
ephemeris casting). The headline (all 19 tests null, powered) is pinned from the
committed results JSON when present.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.medini.ml.raman_saab import vocation_validate as V

_ROOT = Path(__file__).resolve().parents[1]
_RESULTS = _ROOT / "data/ml_runs/raman_saab/vocation_validation.json"


def _rng_decades(n, seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(190, 200, size=n) * 10  # decades 1900..1990


def test_strat_test_null_is_calibrated():
    """Independent feature and label → RR ≈ 1, |z| small."""
    rng = np.random.default_rng(1)
    n = 40_000
    feat = (rng.random(n) < 0.4).astype(int)
    label = (rng.random(n) < 0.1).astype(int)          # independent of feat
    dec = _rng_decades(n)
    r = V.strat_test(feat, label, dec)
    assert 0.9 <= r["rr"] <= 1.1, r["rr"]
    assert abs(r["z"]) < 3.0, r["z"]


def test_strat_test_recovers_planted_effect():
    """A label engineered to RR≈1.3 among feature-positives is recovered."""
    n = 40_000
    dec = _rng_decades(n, seed=2)
    rng = np.random.default_rng(2)
    feat = (rng.random(n) < 0.4).astype(int)
    r = V.planted_recovery(feat, dec, n_L=4000, target_rr=1.30, seed=3)
    assert r["rr"] is not None and r["rr"] >= 1.22, r["rr"]
    assert r["z"] > 5, r["z"]


def test_null_calibration_helper():
    """The shuffle-based calibration returns z ~ N(0,1)."""
    n = 20_000
    dec = _rng_decades(n, seed=4)
    rng = np.random.default_rng(4)
    feat = (rng.random(n) < 0.35).astype(int)
    cal = V.null_calibration(feat, dec, n_L=2000, reps=120, seed=5)
    assert abs(cal["z_mean"]) < 0.25, cal
    assert 0.8 <= cal["z_sd"] <= 1.2, cal


def test_house_of_lon_wraps_correctly():
    # equal 30° houses starting at 10° Aries → longitude 200° sits in house 7
    cusps = tuple((10 + 30 * i) % 360 for i in range(12))
    assert V._house_of_lon(200.0, cusps) == 7
    assert V._house_of_lon(15.0, cusps) == 1


def test_headline_all_null_and_powered():
    """The committed run: every family null (RR < 1.20), null powered."""
    if not _RESULTS.exists():
        return  # results not materialised in this checkout
    o = json.loads(_RESULTS.read_text())
    assert o["n_persons"] >= 55_000, o["n_persons"]
    families = (o["family1_karaka_vocation"] + o["family2_eminence_yogas"]
                + o["family3_gauquelin_mars"])
    assert len(families) == 19
    for r in families:
        assert r["verdict"] in ("refuted", "underpowered"), r
        if r["rr"] is not None:
            assert r["rr"] < 1.20, r          # no family clears the effect gate
    # null powered: calibrated + a G1-sized planted effect recovered
    v = o["validity"]
    assert abs(v["null_calibration"]["z_mean"]) < 0.2
    assert 0.85 <= v["null_calibration"]["z_sd"] <= 1.15
    assert v["planted_rr120"]["rr"] >= 1.15 and v["planted_rr120"]["z"] > 8
