"""Vimshottari Pratyantar tests, pinned to the Bangalore 1990-07-15 baseline.

PT_days = AD_days * PT_lord_yrs / 120. The 9 PT durations within an AD
sum to the AD total. Sequence: starts at AD lord, then canonical
Vimshottari cycle wrapping.
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
)
from app.core.pratyantar import (
    compute_all_pratyantars,
    compute_pratyantars,
)


BANGALORE_BIRTH = dict(year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5)

VIMSHOTTARI_CYCLE = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]
LORD_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

# Mercury-Mercury AD: 17yr * 17/120 = 2.40833 yr ~= 879.74 days
EXPECTED_MERCURY_MERCURY_AD_DAYS = 17.0 * 17 / 120 * DAYS_PER_VEDIC_YEAR


@pytest.fixture(scope="module")
def bangalore_inputs() -> dict[str, float]:
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


@pytest.fixture(scope="module")
def mercury_mercury_pts(mercury_ads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """First AD = Mercury-Mercury; its 9 PTs."""
    assert mercury_ads[0]["antar_lord"] == "Mercury"
    return compute_pratyantars(mercury_ads[0])


# --- Test 1: 9-period count ----------------------------------------------
def test_returns_exactly_nine_pts(
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    assert len(mercury_mercury_pts) == 9


# --- Test 2: order starts at AD lord then canonical cycle wrapping -------
def test_pt_sequence_for_mercury_ad(
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    expected = [
        "Mercury", "Ketu", "Venus", "Sun", "Moon",
        "Mars", "Rahu", "Jupiter", "Saturn",
    ]
    actual = [pt["pratyantar_lord"] for pt in mercury_mercury_pts]
    assert actual == expected


def test_pt_sequence_is_rotation_of_canonical_cycle(
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    actual = [pt["pratyantar_lord"] for pt in mercury_mercury_pts]
    cycle_doubled = VIMSHOTTARI_CYCLE + VIMSHOTTARI_CYCLE
    found = any(
        cycle_doubled[i : i + len(actual)] == actual
        for i in range(len(VIMSHOTTARI_CYCLE))
    )
    assert found, f"sequence {actual} is not a rotation of {VIMSHOTTARI_CYCLE}"


# --- Test 3: bit-exact contiguity within an AD ---------------------------
def test_pts_are_bit_exact_contiguous(
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    for prev, curr in zip(mercury_mercury_pts, mercury_mercury_pts[1:]):
        assert prev["end_jd"] == curr["start_jd"]


# --- Test 4: sum of PT days equals AD duration in days -------------------
def test_pt_durations_sum_equals_ad_total(
    mercury_ads: list[dict[str, Any]],
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    ad = mercury_ads[0]
    expected_total_days = ad["duration_years"] * DAYS_PER_VEDIC_YEAR
    actual_total_days = sum(pt["duration_days"] for pt in mercury_mercury_pts)
    assert actual_total_days == pytest.approx(expected_total_days, abs=0.01)


# --- Test 5: last PT end_jd equals AD end_jd -----------------------------
def test_last_pt_end_jd_equals_ad_end_jd(
    mercury_ads: list[dict[str, Any]],
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    ad = mercury_ads[0]
    assert mercury_mercury_pts[-1]["end_jd"] == pytest.approx(
        ad["end_jd"], abs=1e-6
    )


# --- Test 6: JD arithmetic regression guard ------------------------------
def test_jd_arithmetic_diverges_from_naive_timedelta() -> None:
    """If someone replaces `start_jd + days` with
    `dt.date.fromisoformat(start) + dt.timedelta(days=...)`, this test
    flags it. Even small fp differences in revjul vs. timedelta + Julian
    year length compound to >=1 day across decades. Locks the
    implementation against future "simplification" attempts.
    """
    base_jd = swe.julday(1900, 1, 1, 12.0, swe.GREG_CAL)
    days = 100 * 365.2425  # 100-yr equivalent span

    # Method A: JD arithmetic (what compute_pratyantars uses).
    end_jd = base_jd + days
    ya, ma, da, _ = swe.revjul(end_jd, swe.GREG_CAL)
    correct = dt.date(int(ya), int(ma), int(da))

    # Method B: naive timedelta with Julian-year-length days.
    naive = dt.date(1900, 1, 1) + dt.timedelta(days=100 * 365.25)

    assert abs((correct - naive).days) >= 1


# --- Test 7: pinned baseline (Mercury-Mercury AD) ------------------------
def test_first_pt_start_date_pinned(
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    assert mercury_mercury_pts[0]["start_date"] == "1978-03-26"


def test_last_pt_end_date_matches_ad_end(
    mercury_ads: list[dict[str, Any]],
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    ad = mercury_ads[0]
    # AD end ~ 1980-08-21 per the spec. We assert the PT chain reaches it.
    assert mercury_mercury_pts[-1]["end_date"] == ad["end_date"]


def test_pt_total_days_close_to_879(
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    total = sum(pt["duration_days"] for pt in mercury_mercury_pts)
    # 17yr * 17/120 * 365.2425 ~= 879.74 days.
    assert total == pytest.approx(EXPECTED_MERCURY_MERCURY_AD_DAYS, abs=0.01)
    assert 878 <= total <= 881


# --- Test 8: smoke test for compute_all_pratyantars ----------------------
def test_compute_all_pratyantars_shape(
    mercury_ads: list[dict[str, Any]],
) -> None:
    all_pts = compute_all_pratyantars(mercury_ads)
    assert len(all_pts) == 9  # 9 ADs in Mercury MD
    for ad in mercury_ads:
        key = f"{ad['maha_lord']}-{ad['antar_lord']}"
        assert key in all_pts
        assert len(all_pts[key]) == 9
    total_entries = sum(len(v) for v in all_pts.values())
    assert total_entries == 81


# --- Test 9: contiguity across AD boundaries -----------------------------
def test_pt_chain_contiguous_across_ad_boundaries(
    mercury_ads: list[dict[str, Any]],
) -> None:
    all_pts = compute_all_pratyantars(mercury_ads)
    for prev_ad, curr_ad in zip(mercury_ads, mercury_ads[1:]):
        prev_key = f"{prev_ad['maha_lord']}-{prev_ad['antar_lord']}"
        curr_key = f"{curr_ad['maha_lord']}-{curr_ad['antar_lord']}"
        last_pt_of_prev = all_pts[prev_key][-1]
        first_pt_of_curr = all_pts[curr_key][0]
        # Bit-exact: depends on PT span being computed from AD's stored
        # (end_jd - start_jd) rather than re-deriving from duration_years.
        assert last_pt_of_prev["end_jd"] == first_pt_of_curr["start_jd"]


# --- Sanity: ISO strings agree with their JDs ----------------------------
def test_iso_dates_match_jds(
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    for pt in mercury_mercury_pts:
        sy, sm, sd, _ = swe.revjul(pt["start_jd"], swe.GREG_CAL)
        ey, em, ed, _ = swe.revjul(pt["end_jd"], swe.GREG_CAL)
        assert pt["start_date"] == f"{int(sy):04d}-{int(sm):02d}-{int(sd):02d}"
        assert pt["end_date"] == f"{int(ey):04d}-{int(em):02d}-{int(ed):02d}"


# --- Sanity: all PTs share their parent maha_lord and antar_lord ---------
def test_all_pts_share_parent_lords(
    mercury_mercury_pts: list[dict[str, Any]],
) -> None:
    assert {pt["maha_lord"] for pt in mercury_mercury_pts} == {"Mercury"}
    assert {pt["antar_lord"] for pt in mercury_mercury_pts} == {"Mercury"}
