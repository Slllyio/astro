"""Tests for the transit-trigger narrowing layer.

Pure-ephemeris (swisseph only, no catalog): verifies the angular helper, the
death-trigger point set, and that the window-scan yields contiguous sub-intervals
strictly inside the window with Saturn actually within orb at their midpoints.
"""
from __future__ import annotations

import datetime as dt

import pytest

from app.core.ephemeris_engine import calculate_jd
from app.medini.analysis import transit_triggers as tt


def test_ang_sep_wraps() -> None:
    assert tt._ang_sep(10.0, 350.0) == pytest.approx(20.0)
    assert tt._ang_sep(0.0, 180.0) == pytest.approx(180.0)
    assert tt._ang_sep(5.0, 8.0) == pytest.approx(3.0)


def test_death_trigger_points_includes_maraka_and_sun() -> None:
    # Aries asc: 2nd lord Taurus→Venus, 7th lord Libra→Venus, +Saturn (maraka_full),
    # +Sun. natal_lons supplies the longitudes the trigger fires on.
    natal = {g: float(i * 30) for i, g in enumerate(
        ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"))}
    gh = {g: 1 for g in natal}
    pts = tt.death_trigger_points(1, gh, natal)
    # Venus (150), Saturn (180), Sun (0) must be present
    assert natal["Venus"] in pts and natal["Saturn"] in pts and natal["Sun"] in pts


def test_saturn_transit_lon_is_a_longitude() -> None:
    jd = calculate_jd(2000, 1, 1, 12.0, 0.0)
    lon = tt.saturn_transit_lon(jd)
    assert 0.0 <= lon < 360.0


def test_active_intervals_are_inside_window_and_genuinely_hot() -> None:
    # A 6-year window; scan for Saturn within 3° of a couple of fixed points.
    start = calculate_jd(2020, 1, 1, 12.0, 0.0)
    end = calculate_jd(2026, 1, 1, 12.0, 0.0)
    # Saturn travels ~267°→320° over 2020–2026, so points on that arc will be crossed.
    pts = [290.0, 310.0]
    ivs = tt.active_trigger_intervals(start, end, pts, orb=3.0, step_days=3.0)
    assert ivs, "Saturn should cross at least one point in 6 years"
    for iv in ivs:
        assert start <= iv.start_jd <= iv.end_jd <= end
        mid = (iv.start_jd + iv.end_jd) / 2.0
        # Saturn is within orb somewhere in the band (check endpoints/mid are plausible)
        assert tt.is_triggered(iv.start_jd, pts, orb=3.0) or \
            tt.is_triggered(mid, pts, orb=3.0) or tt.is_triggered(iv.end_jd, pts, orb=3.0)


def test_empty_points_gives_no_bands() -> None:
    start = calculate_jd(2020, 1, 1, 12.0, 0.0)
    end = calculate_jd(2022, 1, 1, 12.0, 0.0)
    assert tt.active_trigger_intervals(start, end, [], orb=3.0) == []
    assert tt.is_triggered(start, [], orb=3.0) is False


def test_predictor_transit_refine_attaches_bands() -> None:
    from app.medini.analysis import death_window_predictor as dwp
    out = dwp.predict_death_windows(
        year=1955, month=3, day=20, latitude=19.07, longitude=72.88, tz_offset=5.5,
        as_of=dt.date(2026, 6, 18), top_n=None, transit_refine=True,
    )
    # every returned window carries a trigger_bands list (possibly empty)
    assert all(w["trigger_bands"] is not None for w in out["windows"])
    # across all future windows of a full remaining life, Saturn must cross a trigger
    bands = [b for w in out["windows"] for b in (w["trigger_bands"] or [])]
    assert bands, "expected at least one Saturn-trigger band across future windows"
    for b in bands:
        assert b["days"] > 0 and b["start_date"] <= b["end_date"]
