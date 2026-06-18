"""Tests for the per-chart death-window predictor.

The core path needs only swisseph (no DuckDB catalog): it casts a real chart and
enumerates the Vimśottarī windows, so these tests exercise the genuine ephemeris.
The endpoint is mounted standalone (no app.main dependency), matching the doctrine
router test style.
"""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.doctrine_routes import doctrine_router
from app.medini.analysis import death_window_predictor as dwp

# A fixed living-person chart: Bangalore, 1960-07-15 12:00 +05:30.
_CHART = dict(
    year=1960, month=7, day=15, hour=12, minute=0,
    latitude=12.97, longitude=77.59, tz_offset=5.5,
)
_AS_OF = dt.date(2026, 6, 18)


def test_bracket_for_age() -> None:
    assert dwp._bracket_for_age(10.0, dwp.DEFAULT_BRACKETS) == "alpa"
    assert dwp._bracket_for_age(50.0, dwp.DEFAULT_BRACKETS) == "madhya"
    assert dwp._bracket_for_age(80.0, dwp.DEFAULT_BRACKETS) == "purna"
    # past the final bound still lands in the last bracket
    assert dwp._bracket_for_age(999.0, dwp.DEFAULT_BRACKETS) == "purna"


def test_jd_to_iso_roundtrips_a_known_date() -> None:
    from app.core.ephemeris_engine import calculate_jd
    jd = calculate_jd(2000, 1, 1, 12.0, 0.0)
    assert dwp._jd_to_iso(jd) == "2000-01-01"


def test_predict_structure_and_ranking() -> None:
    out = dwp.predict_death_windows(as_of=_AS_OF, **_CHART)
    assert out["asc_sign"] >= 1 and out["asc_sign"] <= 12
    assert out["current_age"] > 60.0
    assert out["significators"] == list(dwp._DEATH_COMPOSITE)
    wins = out["windows"]
    assert wins, "a 1960 chart must have future windows after 2026"
    assert len(wins) == out["n_future_windows"]

    # every returned window ends after the as-of date
    for w in wins:
        assert w["end_date"] > _AS_OF.isoformat()
        assert 0 <= w["md_score"] <= 3
        assert len(w["md_roles"]) == w["md_score"]
        assert w["bracket"] in ("alpa", "madhya", "purna")
        # risk == composite × bracket × ad reinforcement (within rounding)
        expect = w["composite_factor"] * w["bracket_factor"] * w["ad_factor"]
        assert w["risk_score"] == pytest.approx(expect, abs=1e-3)

    # sorted by risk descending, ranks 1..N contiguous
    risks = [w["risk_score"] for w in wins]
    assert risks == sorted(risks, reverse=True)
    assert [w["rank"] for w in wins] == list(range(1, len(wins) + 1))


def test_top_n_limits_results() -> None:
    full = dwp.predict_death_windows(as_of=_AS_OF, **_CHART)
    top3 = dwp.predict_death_windows(as_of=_AS_OF, top_n=3, **_CHART)
    assert len(top3["windows"]) == 3
    # the top-3 are the same first three of the full ranking
    assert [w["window_id"] for w in top3["windows"]] == \
        [w["window_id"] for w in full["windows"][:3]]


def test_composite_role_count_drives_factor() -> None:
    # A higher composite role-count must map to a >= composite factor (monotone).
    out = dwp.predict_death_windows(as_of=_AS_OF, **_CHART)
    by_score: dict[int, float] = {}
    for w in out["windows"]:
        by_score.setdefault(w["md_score"], w["composite_factor"])
    for s, f in by_score.items():
        assert f == pytest.approx(dwp.DEFAULT_COMPOSITE_FACTOR[s], abs=1e-6)


def test_unknown_significator_raises() -> None:
    with pytest.raises(ValueError):
        dwp.predict_death_windows(as_of=_AS_OF, significators=("bogus",), **_CHART)


def test_pd_depth_gives_finer_windows() -> None:
    ad = dwp.predict_death_windows(as_of=_AS_OF, top_n=None, **_CHART)
    pd_ = dwp.predict_death_windows(as_of=_AS_OF, top_n=None, depth="pd", **_CHART)
    assert pd_["depth"] == "pd"
    # PD partitions each AD into 9 → strictly more (and finer) future windows
    assert pd_["n_future_windows"] > ad["n_future_windows"]
    w = pd_["windows"][0]
    assert w["pd_lord"] is not None and w["pd_seq"] is not None
    assert w["pd_score"] is not None and w["pd_factor"] is not None
    # PD resolves to sub-year windows (vs multi-year ADs)
    spans = [x["end_age"] - x["start_age"] for x in pd_["windows"]]
    assert min(spans) < 1.0


def test_invalid_depth_raises() -> None:
    with pytest.raises(ValueError):
        dwp.predict_death_windows(as_of=_AS_OF, depth="bogus", **_CHART)


def test_mortality_model_conditional_reads() -> None:
    # Deaths uniformly at ages 0,1,...,99 → clean closed-form checks.
    m = dwp.MortalityModel(ages=tuple(float(a) for a in range(100)))
    assert m.survival(0.0) == pytest.approx(1.0)
    assert m.survival(50.0) == pytest.approx(0.5, abs=0.02)
    assert m.mass(0.0, 50.0) == pytest.approx(0.5, abs=0.02)
    # P(die within 10y | alive at 50) = mass(50,60)/survival(50) = 10/50 = 0.2
    assert m.prob_within(50.0, 10.0) == pytest.approx(0.2, abs=0.02)
    # median remaining at 50 ≈ 25 (half of the 50 remaining years)
    assert m.median_remaining(50.0) == pytest.approx(25.0, abs=2.0)


def test_calibrated_probabilities_sum_and_rank() -> None:
    # Skew deaths toward 70-90 so the calibrated ranking favours that age band.
    ages = tuple(float(a) for a in (list(range(60, 95)) * 10))
    m = dwp.MortalityModel(ages=ages)
    out = dwp.predict_death_windows(as_of=_AS_OF, mortality=m, **_CHART)
    assert out["calibrated"] is True
    assert "median_remaining_years" in out and "prob_within_10y" in out
    wins = out["windows"]
    # every future window carries a probability; they sum to ~1 over the full set
    assert all(w["probability"] is not None for w in wins)
    assert sum(w["probability"] for w in wins) == pytest.approx(1.0, abs=1e-3)
    # ranked by probability descending now (not risk_score)
    probs = [w["probability"] for w in wins]
    assert probs == sorted(probs, reverse=True)
    # the #1 window should overlap the corpus's high-mortality band (60-95)
    top = wins[0]
    assert top["end_age"] >= 60 and top["start_age"] <= 95


@pytest.mark.asyncio
async def test_death_window_endpoint() -> None:
    app = FastAPI()
    app.include_router(doctrine_router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as ac:
        r = await ac.get("/medini/doctrine/death-window", params={
            "year": 1960, "month": 7, "day": 15, "hour": 12, "minute": 0,
            "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5,
            "as_of": "2026-06-18", "top_n": 5,
        })
        assert r.status_code == 200
        body = r.json()
        assert len(body["windows"]) == 5
        assert body["windows"][0]["rank"] == 1

        # bad as_of -> 422
        r2 = await ac.get("/medini/doctrine/death-window", params={
            "year": 1960, "month": 7, "day": 15,
            "latitude": 12.97, "longitude": 77.59, "as_of": "not-a-date",
        })
        assert r2.status_code == 422


@pytest.mark.asyncio
async def test_death_window_page_served() -> None:
    app = FastAPI()
    app.include_router(doctrine_router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as ac:
        r = await ac.get("/medini/doctrine/death-window/page")
        assert r.status_code == 200
        assert "dw-form" in r.text and "Death-Window Predictor" in r.text


@pytest.mark.asyncio
async def test_calibrate_without_catalog_returns_503(monkeypatch) -> None:
    # Force the catalog to look absent so calibration is unavailable.
    from pathlib import Path

    from app.medini.analysis import doctrine_validator as dv
    monkeypatch.setattr(dv, "DEFAULT_CATALOG", Path("/nonexistent/catalog.duckdb"))

    app = FastAPI()
    app.include_router(doctrine_router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as ac:
        r = await ac.get("/medini/doctrine/death-window", params={
            "year": 1960, "month": 7, "day": 15,
            "latitude": 12.97, "longitude": 77.59,
            "calibrate": "true",
        })
        assert r.status_code == 503
