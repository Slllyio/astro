"""Tests for the chart-strength → event-age analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml.dasha_event_age import _frame, chart_index, correlate

CANCER, LIBRA, ARIES = 4, 7, 1


def _chart(pid: str, asc: int, saturn_sign: int) -> dict:
    return {"person_id": pid, "asc_sign": asc,
            "saturn_sign": saturn_sign, "saturn_house": 4,
            "venus_sign": LIBRA, "venus_house": 4,
            "jupiter_sign": CANCER, "jupiter_house": 1,
            "moon_sign": CANCER, "moon_house": 1,
            "mars_sign": ARIES, "mars_house": 10,
            "mercury_sign": LIBRA, "mercury_house": 4,
            "sun_sign": LIBRA, "sun_house": 4,
            "rahu_sign": ARIES, "ketu_sign": LIBRA,
            "rahu_house": 10, "ketu_house": 4}


def test_chart_index_returns_float() -> None:
    crow = pd.Series(_chart("p1", CANCER, LIBRA))
    v = chart_index(crow, (7,))
    assert isinstance(v, float)
    # missing asc → None
    bad = crow.copy(); bad["asc_sign"] = np.nan
    assert chart_index(bad, (7,)) is None


def test_frame_one_row_per_person() -> None:
    events = pd.DataFrame([
        {"person_id": "p1", "event_class": "marriage", "event_jd": 10.0,
         "age_at_event_years": 28.0},
        {"person_id": "p1", "event_class": "marriage", "event_jd": 20.0,
         "age_at_event_years": 40.0},  # later — should be dropped
        {"person_id": "p2", "event_class": "marriage", "event_jd": 5.0,
         "age_at_event_years": 32.0},
    ])
    charts = pd.DataFrame([_chart("p1", CANCER, LIBRA), _chart("p2", ARIES, ARIES)])
    fr = _frame(events, charts, "marriage", (7,))
    assert len(fr) == 2
    assert fr[fr.person_id == "p1"]["age"].iloc[0] == 28.0  # earliest kept


def test_correlate_detects_planted_signal() -> None:
    rng = np.random.default_rng(0)
    n = 300
    idx = rng.normal(size=n)
    age = 40 - 3.0 * idx + rng.normal(scale=1.0, size=n)   # strong negative
    fr = pd.DataFrame({"person_id": range(n), "index": idx, "age": age})
    r = correlate(fr, k=300, seed=1)
    assert r["rho"] < -0.5
    assert r["p_two_sided"] < 0.05
    assert r["age_gap"] < 0           # strong index → lower age
    # too few rows → graceful
    assert correlate(fr.head(10))["rho"] is None
