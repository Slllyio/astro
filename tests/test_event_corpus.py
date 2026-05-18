"""Tests for the Round 4 per-event corpus pipeline.

Covers two surfaces:
1. The ``active_dasha_at`` + ``compute_full_mahadasha_cycle`` helpers in
   ``feature_engineering`` — pinned against the Bangalore baseline so
   they stay consistent with ``tests/test_dasha_dates.py``.
2. The corpus builder's negative-sampling invariants — same person,
   same calendar month/day, INTEGER year offsets ≥ 2 years.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pytest
import swisseph as swe

from app.medini.etl.event_corpus import (
    NEGATIVE_EXCLUSION_RADIUS_DAYS,
    _draw_negative_jds,
    _event_date_to_jd,
)
from app.medini.etl.feature_engineering import (
    active_dasha_at,
    compute_full_mahadasha_cycle,
)
from app.medini.etl.lahiri_worker import init_worker

# Pre-set Lahiri once for the whole test module — the helpers need it
# for the moon-longitude reads inside `calculate_vimshottari_mahadasha`.
init_worker()

# Bangalore baseline (matches tests/test_dasha_dates.py): 1990-07-15
# 12:00 IST (UTC+5.5).
BANGALORE_JD = swe.julday(1990, 7, 15, 12.0 - 5.5, swe.GREG_CAL)


def _bangalore_moon_lon() -> float:
    return swe.calc_ut(BANGALORE_JD, swe.MOON, swe.FLG_SIDEREAL)[0][0]


# ---------- active_dasha_at / compute_full_mahadasha_cycle ----------


def test_full_mahadasha_cycle_spans_120_years():
    """The 9 MDs returned must cumulatively span exactly 120 years."""
    cycle = compute_full_mahadasha_cycle(BANGALORE_JD, _bangalore_moon_lon())
    assert len(cycle) == 9
    span_years = (cycle[-1][2] - cycle[0][1]) / 365.2425
    assert abs(span_years - 120.0) < 0.01


def test_active_dasha_at_birth_matches_natal_pin():
    """At birth_jd, active MD must be Mercury (Bangalore baseline pin)."""
    result = active_dasha_at(
        BANGALORE_JD, BANGALORE_JD, _bangalore_moon_lon(),
    )
    assert result["active_md_lord"] == "Mercury"
    # MD elapsed at birth ~ 12.305 yr — matches dasha_start_age_mercury pin
    assert result["md_elapsed_years"] == pytest.approx(12.305, abs=0.05)


def test_active_dasha_at_birth_plus_5_years_in_ketu():
    """Ketu MD opens ~4.7 yr after birth → at +5yr we should be in Ketu."""
    event_jd = BANGALORE_JD + 5 * 365.2425
    result = active_dasha_at(event_jd, BANGALORE_JD, _bangalore_moon_lon())
    assert result["active_md_lord"] == "Ketu"
    assert result["md_elapsed_years"] == pytest.approx(0.305, abs=0.05)


def test_active_dasha_outside_120_year_window_returns_sentinel():
    """JDs beyond 120 yr post-cycle → sentinel "none" lord and NaN years."""
    event_jd = BANGALORE_JD + 130 * 365.2425
    result = active_dasha_at(event_jd, BANGALORE_JD, _bangalore_moon_lon())
    assert result["active_md_lord"] == "none"
    assert result["active_ad_lord"] == "none"
    assert np.isnan(result["md_elapsed_years"])


# ---------- _event_date_to_jd ----------


def test_event_date_to_jd_full_date():
    jd = _event_date_to_jd("1990-07-15", None)
    expected = swe.julday(1990, 7, 15, 12.0, swe.GREG_CAL)
    assert jd == pytest.approx(expected, abs=1e-6)


def test_event_date_to_jd_year_fallback_uses_july_1():
    """Missing date + present year → July 1 12:00 UT."""
    jd = _event_date_to_jd(None, 1985)
    expected = swe.julday(1985, 7, 1, 12.0, swe.GREG_CAL)
    assert jd == pytest.approx(expected, abs=1e-6)


def test_event_date_to_jd_returns_none_when_both_missing():
    assert _event_date_to_jd(None, None) is None


# ---------- Negative sampling invariants ----------


def test_negative_sampling_preserves_month_and_day():
    """Strict negatives must share the calendar month + day with the anchor
    positive; only the year shifts. This is the critical seasonality
    control that drops marriage AUC from a confounded 0.97 to ~0.56.
    """
    rng = np.random.default_rng(42)
    # Synthetic person born 1970-01-01, single positive event on 1995-06-15
    birth_jd = swe.julday(1970, 1, 1, 12.0, swe.GREG_CAL)
    positive_jd = swe.julday(1995, 6, 15, 12.0, swe.GREG_CAL)
    negatives = _draw_negative_jds(
        rng, birth_jd, [positive_jd], n_to_draw=50,
    )
    assert len(negatives) >= 40, "rejection sampler should fill mostly"
    for neg_jd in negatives:
        y, m, d, _ = swe.revjul(neg_jd, swe.GREG_CAL)
        assert (int(m), int(d)) == (6, 15), (
            f"negative {y:.0f}-{int(m)}-{int(d)} doesn't match anchor 06-15"
        )


def test_negative_sampling_respects_min_offset():
    """Shifts must be ≥ 2 calendar years from the anchor — keeps the
    negative outside the same Saturn-return phase."""
    rng = np.random.default_rng(0)
    birth_jd = swe.julday(1970, 1, 1, 12.0, swe.GREG_CAL)
    positive_jd = swe.julday(1995, 6, 15, 12.0, swe.GREG_CAL)
    negatives = _draw_negative_jds(
        rng, birth_jd, [positive_jd], n_to_draw=30,
    )
    for neg_jd in negatives:
        gap_years = abs(neg_jd - positive_jd) / 365.2425
        assert gap_years >= 1.9, f"negative within {gap_years:.2f}yr of positive"


def test_negative_sampling_excludes_event_window():
    """Negatives must not land within ±30 days of any positive event."""
    rng = np.random.default_rng(1)
    birth_jd = swe.julday(1970, 1, 1, 12.0, swe.GREG_CAL)
    # Two events 5 years apart, both June 15
    pos_a = swe.julday(1990, 6, 15, 12.0, swe.GREG_CAL)
    pos_b = swe.julday(1995, 6, 15, 12.0, swe.GREG_CAL)
    negatives = _draw_negative_jds(rng, birth_jd, [pos_a, pos_b], n_to_draw=20)
    for neg_jd in negatives:
        for pos_jd in [pos_a, pos_b]:
            assert abs(neg_jd - pos_jd) >= NEGATIVE_EXCLUSION_RADIUS_DAYS


def test_negative_sampling_stays_in_lifespan():
    """Negatives must fall in [birth + 1yr, min(birth + 100yr, today)]."""
    rng = np.random.default_rng(2)
    birth_jd = swe.julday(1970, 1, 1, 12.0, swe.GREG_CAL)
    positive_jd = swe.julday(1995, 6, 15, 12.0, swe.GREG_CAL)
    negatives = _draw_negative_jds(rng, birth_jd, [positive_jd], n_to_draw=20)
    today = dt.date.today()
    today_jd = swe.julday(today.year, today.month, today.day, 12.0, swe.GREG_CAL)
    for neg_jd in negatives:
        assert neg_jd >= birth_jd + 365
        assert neg_jd <= min(birth_jd + 100 * 365.2425, today_jd)


def test_negative_sampling_with_no_positives_returns_empty():
    rng = np.random.default_rng(3)
    birth_jd = swe.julday(1970, 1, 1, 12.0, swe.GREG_CAL)
    assert _draw_negative_jds(rng, birth_jd, [], n_to_draw=10) == []
