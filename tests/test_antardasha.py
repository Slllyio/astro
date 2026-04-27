"""Vimshottari Antardasha tests, pinned to the Bangalore 1990-07-15 baseline.

These tests validate `compute_antardashas` against:

  - Hand-computed durations (formula:
        AD_days = MD_total_years * AD_lord_years / 120 * 365.2425
    ). For Mercury MD (17 yrs) this gives the 9 durations enumerated below.
  - The fixed Vimshottari sequence rotation (MD lord first, then canonical
    cycle wrapping back).
  - Conservation: the 9 ADs sum to the full MD duration and the last AD's
    end_jd matches the existing engine's MD end_jd within a small rounding
    tolerance.

Expected values are computed analytically here (per the spec instructions),
*not* lifted from `compute_antardashas`'s own output.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
import swisseph as swe

from app.core.antardasha import compute_antardashas
from app.core.ephemeris_engine import (
    DAYS_PER_VEDIC_YEAR,
    calculate_all_charts,
    calculate_vimshottari_mahadasha,
)


# ---------------------------------------------------------------------------
# Bangalore 1990 baseline inputs.
# ---------------------------------------------------------------------------
# Birth: 1990-07-15 12:00 IST in Bangalore. Moon sidereal Lahiri ~ 356.32 deg
# (Revati nakshatra) -> Mercury MD totalling 17 yrs.
BANGALORE_BIRTH = dict(year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5)

# Vimshottari canonical cycle, used for sequence assertions.
VIMSHOTTARI_CYCLE = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]

# Lord -> Vimshottari weight (years). Source: Parashara / standard references.
LORD_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

MERCURY_MD_TOTAL_YEARS = 17.0

# Hand-computed AD durations for Mercury MD. AD_yrs = 17 * lord_yrs / 120.
# Cross-checked against the spec's table (e.g. Mercury AD: 17*17/120 = 2.4083 yr).
EXPECTED_MERCURY_AD_DURATIONS_YEARS = {
    lord: MERCURY_MD_TOTAL_YEARS * yrs / 120 for lord, yrs in LORD_YEARS.items()
}

# Order of ADs *within* a Mercury MD: Mercury first, then continue the cycle
# starting at the index after Mercury (= Ketu) and wrap around.
EXPECTED_MERCURY_AD_SEQUENCE = [
    "Mercury", "Ketu", "Venus", "Sun", "Moon",
    "Mars", "Rahu", "Jupiter", "Saturn",
]


@pytest.fixture(scope="module")
def bangalore_inputs() -> dict[str, float]:
    """Resolve birth_jd + sidereal Moon longitude for the Bangalore baseline."""
    charts = calculate_all_charts(**BANGALORE_BIRTH)
    return {
        "birth_jd": charts["birth_jd"],
        "moon_longitude": charts["d1"]["Moon"]["longitude"],
    }


@pytest.fixture(scope="module")
def mercury_ads(bangalore_inputs: dict[str, float]) -> list[dict[str, Any]]:
    return compute_antardashas(
        bangalore_inputs["moon_longitude"], bangalore_inputs["birth_jd"]
    )


# ---------------------------------------------------------------------------
# Structural assertions: count, parent-lord, type shape.
# ---------------------------------------------------------------------------

def test_returns_exactly_nine_periods(mercury_ads: list[dict[str, Any]]) -> None:
    assert len(mercury_ads) == 9


def test_all_share_mercury_as_maha_lord(mercury_ads: list[dict[str, Any]]) -> None:
    assert {ad["maha_lord"] for ad in mercury_ads} == {"Mercury"}


def test_each_period_has_required_keys(mercury_ads: list[dict[str, Any]]) -> None:
    expected_keys = {
        "maha_lord", "antar_lord", "start_date", "end_date",
        "start_jd", "end_jd", "duration_years",
    }
    for ad in mercury_ads:
        assert set(ad.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Test case 1: first AD of a Mercury MD is Mercury-Mercury.
# ---------------------------------------------------------------------------

def test_first_ad_is_same_as_md_lord(mercury_ads: list[dict[str, Any]]) -> None:
    assert mercury_ads[0]["antar_lord"] == "Mercury"
    assert mercury_ads[0]["maha_lord"] == "Mercury"


# ---------------------------------------------------------------------------
# Test case 3: ADs are in the documented Mercury-first rotation order.
# ---------------------------------------------------------------------------

def test_ad_sequence_matches_rotation(mercury_ads: list[dict[str, Any]]) -> None:
    actual = [ad["antar_lord"] for ad in mercury_ads]
    assert actual == EXPECTED_MERCURY_AD_SEQUENCE


def test_ad_sequence_is_a_rotation_of_canonical_cycle(
    mercury_ads: list[dict[str, Any]],
) -> None:
    """The Mercury-first rotation must be a rotation of Ketu->...->Mercury."""
    actual = [ad["antar_lord"] for ad in mercury_ads]
    cycle_doubled = VIMSHOTTARI_CYCLE + VIMSHOTTARI_CYCLE
    # The actual sequence should appear as a contiguous slice somewhere in
    # the doubled cycle.
    found = any(
        cycle_doubled[i : i + len(actual)] == actual
        for i in range(len(VIMSHOTTARI_CYCLE))
    )
    assert found, f"sequence {actual} is not a rotation of {VIMSHOTTARI_CYCLE}"


# ---------------------------------------------------------------------------
# Test case 4: monotonically increasing start_jds.
# ---------------------------------------------------------------------------

def test_start_jds_are_monotonically_increasing(
    mercury_ads: list[dict[str, Any]],
) -> None:
    start_jds = [ad["start_jd"] for ad in mercury_ads]
    for prev, curr in zip(start_jds, start_jds[1:]):
        assert curr > prev, f"start_jd not increasing: {prev} -> {curr}"


def test_each_ad_end_jd_equals_next_start_jd(
    mercury_ads: list[dict[str, Any]],
) -> None:
    """No gaps and no overlap between consecutive ADs (JD-exact contiguity)."""
    for prev, curr in zip(mercury_ads, mercury_ads[1:]):
        assert prev["end_jd"] == pytest.approx(curr["start_jd"], abs=1e-9)


# ---------------------------------------------------------------------------
# Test case 6: per-AD duration matches the hand-computed formula.
# ---------------------------------------------------------------------------

def test_each_ad_duration_matches_formula(
    mercury_ads: list[dict[str, Any]],
) -> None:
    """duration_years == MD_total * lord_yrs / 120, within FP tolerance."""
    for ad in mercury_ads:
        expected = EXPECTED_MERCURY_AD_DURATIONS_YEARS[ad["antar_lord"]]
        assert ad["duration_years"] == pytest.approx(expected, rel=1e-9)


def test_each_ad_jd_span_matches_duration(
    mercury_ads: list[dict[str, Any]],
) -> None:
    """end_jd - start_jd == duration_years * 365.2425, within FP tolerance.

    Guards against silent drift if someone replaces JD arithmetic with
    `datetime.timedelta` inside the implementation.
    """
    for ad in mercury_ads:
        span_days = ad["end_jd"] - ad["start_jd"]
        expected_days = ad["duration_years"] * DAYS_PER_VEDIC_YEAR
        assert span_days == pytest.approx(expected_days, abs=1e-9)


# ---------------------------------------------------------------------------
# Test case 2: 9 ADs sum to the full MD duration (17 yrs).
# ---------------------------------------------------------------------------

def test_durations_sum_to_md_total(mercury_ads: list[dict[str, Any]]) -> None:
    total = sum(ad["duration_years"] for ad in mercury_ads)
    assert total == pytest.approx(MERCURY_MD_TOTAL_YEARS, abs=1e-9)


# ---------------------------------------------------------------------------
# Test case 5: last AD ends at the MD's end_jd (within ~1 day).
# ---------------------------------------------------------------------------

def test_last_ad_aligns_with_md_end(
    mercury_ads: list[dict[str, Any]], bangalore_inputs: dict[str, float]
) -> None:
    md = calculate_vimshottari_mahadasha(
        bangalore_inputs["moon_longitude"], bangalore_inputs["birth_jd"]
    )
    md_end = dt.date.fromisoformat(md["end_date"])
    ad_end = dt.date.fromisoformat(mercury_ads[-1]["end_date"])
    delta_days = abs((md_end - ad_end).days)
    assert delta_days <= 1, f"last AD ends {delta_days} days from MD end"


def test_first_ad_starts_at_md_start(
    mercury_ads: list[dict[str, Any]], bangalore_inputs: dict[str, float]
) -> None:
    md = calculate_vimshottari_mahadasha(
        bangalore_inputs["moon_longitude"], bangalore_inputs["birth_jd"]
    )
    md_start = dt.date.fromisoformat(md["start_date"])
    ad_start = dt.date.fromisoformat(mercury_ads[0]["start_date"])
    delta_days = abs((md_start - ad_start).days)
    assert delta_days <= 1, f"first AD starts {delta_days} days from MD start"


# ---------------------------------------------------------------------------
# Sanity check: ISO date strings are parseable and consistent with their JDs.
# ---------------------------------------------------------------------------

def test_iso_date_strings_match_their_jds(
    mercury_ads: list[dict[str, Any]],
) -> None:
    """ISO strings should equal swe.revjul(jd) reformatted (no off-by-one)."""
    for ad in mercury_ads:
        sy, sm, sd, _ = swe.revjul(ad["start_jd"], swe.GREG_CAL)
        ey, em, ed, _ = swe.revjul(ad["end_jd"], swe.GREG_CAL)
        assert ad["start_date"] == f"{int(sy):04d}-{int(sm):02d}-{int(sd):02d}"
        assert ad["end_date"] == f"{int(ey):04d}-{int(em):02d}-{int(ed):02d}"


# ---------------------------------------------------------------------------
# Cross-MD smoke test: a Moon MD must yield a Moon-first sequence.
# ---------------------------------------------------------------------------
# Reuses the March 2025 anchor pinned in test_dasha_dates.py (Moon at 46.667
# deg = halfway through Rohini, Moon-ruled, 10-yr MD). Confirms the
# sub-period rotation works for non-Mercury parents too.

MARCH_2025_BIRTH_JD = swe.julday(2030, 3, 14, 12.0, swe.GREG_CAL)
MARCH_2025_MOON_LONGITUDE = 46.6666667


def test_moon_md_produces_moon_first_rotation() -> None:
    ads = compute_antardashas(MARCH_2025_MOON_LONGITUDE, MARCH_2025_BIRTH_JD)
    sequence = [ad["antar_lord"] for ad in ads]
    expected = [
        "Moon", "Mars", "Rahu", "Jupiter", "Saturn",
        "Mercury", "Ketu", "Venus", "Sun",
    ]
    assert sequence == expected
    assert all(ad["maha_lord"] == "Moon" for ad in ads)


def test_moon_md_durations_sum_to_ten_years() -> None:
    ads = compute_antardashas(MARCH_2025_MOON_LONGITUDE, MARCH_2025_BIRTH_JD)
    total = sum(ad["duration_years"] for ad in ads)
    assert total == pytest.approx(10.0, abs=1e-9)
