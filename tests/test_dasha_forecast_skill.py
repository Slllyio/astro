"""Tests for Layer C forecast skill & calibration."""
from __future__ import annotations

import numpy as np

from app.medini.ml import dasha_forecast_skill as fs


def test_emp_cdf_monotone_bounded() -> None:
    cdf = fs._emp_cdf(np.array([20.0, 25, 30, 35, 40]))
    xs = np.linspace(15, 45, 50)
    y = cdf(xs)
    assert (np.diff(y) >= -1e-9).all() and y.min() >= 0 and y.max() <= 1
    assert cdf(np.array([10.0]))[0] == 0 and cdf(np.array([50.0]))[0] == 1


def _rec(a0, graded, ev_idx, dur=None):
    a0 = np.array(a0, float)
    a1 = a0 + 1.0
    d = np.ones(len(a0)) if dur is None else np.array(dur, float)
    return {"a0": a0, "a1": a1, "dur": d, "graded": np.array(graded), "ev_idx": ev_idx}


def test_fit_multiplier_recovers_signal() -> None:
    # events always at graded==4 windows → mult(4) should be the max level.
    recs = [_rec([20, 25, 30, 35], [0, 1, 4, 2], 2) for _ in range(100)]
    mult = fs.fit_multiplier(recs)
    assert mult[4] == max(mult.values()) and mult[4] > 1.2


def test_positive_skill_when_tilt_helps() -> None:
    cdf = fs._emp_cdf(np.linspace(18, 40, 200))
    recs = [_rec([20, 25, 30, 35], [0, 1, 4, 2], 2) for _ in range(150)]
    mult = fs.fit_multiplier(recs)
    ev = fs.evaluate(recs, mult, cdf)
    assert ev["log_skill"] > 0 and ev["bits_gained"] > 0


def test_zero_skill_when_multiplier_flat() -> None:
    cdf = fs._emp_cdf(np.linspace(18, 40, 200))
    recs = [_rec([20, 25, 30, 35], [1, 1, 1, 1], 2) for _ in range(80)]
    mult = {s: 1.0 for s in range(5)}            # no tilt
    ev = fs.evaluate(recs, mult, cdf)
    assert abs(ev["log_skill"]) < 1e-6 and abs(ev["bits_gained"]) < 1e-6


def test_reliability_perfectly_calibrated_has_low_ece() -> None:
    # build pairs where observed frequency matches forecast prob in each bin.
    rng = np.random.default_rng(0)
    calib = []
    for p in (0.1, 0.3, 0.5, 0.7, 0.9):
        for _ in range(400):
            calib.append((p, float(rng.random() < p)))
    rel = fs.reliability(calib)
    assert rel["ece"] < 0.05


def test_rps_perfect_vs_wrong() -> None:
    probs = np.array([0.0, 0.0, 1.0, 0.0])
    order = np.arange(4)
    assert fs._rps(probs, order, 2) == 0.0          # all mass on the true window
    assert fs._rps(probs, order, 0) > 0.0           # mass far from the truth
