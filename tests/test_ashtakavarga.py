"""Tests for Bhinnashtakavarga (BAV) + Sarvashtakavarga (SAV).

Pinned baseline: Bangalore 1990-07-15 12:00 IST (tz_offset=5.5, lat=12.97,
lon=77.59). Expected BAV totals are pinned from the canonical Parashari rule
table -- they're equivalently producible by the vendored portal's
BAVCalculator.calculate_bav(). The rule table itself is the authority; the
totals below are the deterministic output of applying that table to the
sidereal-Lahiri sign positions for the pinned natal chart.

Per-planet BAV totals are CHART-INVARIANT of this rule table:
each total = sum of the rule-row lengths, which is chart-independent.
SAV grand total = 338 always.
"""
from __future__ import annotations

import pytest

from app.core.ashtakavarga import (
    BAV_CONTRIBUTORS,
    BAV_PLANETS,
    compute_ashtakavarga,
)
from app.core.ephemeris_engine import calculate_all_charts


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Bangalore 1990-07-15 12:00 IST -- same anchor as test_dasha_dates.py.
BANGALORE_BIRTH = dict(
    year=1990, month=7, day=15, hour=12, minute=0,
    tz_offset=5.5, latitude=12.97, longitude=77.59,
)


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    """Compute the natal chart once per module run."""
    return calculate_all_charts(**BANGALORE_BIRTH)


@pytest.fixture(scope="module")
def bangalore_bav(bangalore_chart: dict) -> dict:
    """Compute the Ashtakavarga matrix for the pinned Bangalore chart."""
    return compute_ashtakavarga(
        bangalore_chart["d1"], bangalore_chart["ascendant"]
    )


# ---------------------------------------------------------------------------
# Shape invariants
# ---------------------------------------------------------------------------

def test_bav_per_planet_has_seven_keys(bangalore_bav: dict) -> None:
    assert set(bangalore_bav["bav_per_planet"]) == set(BAV_PLANETS)
    assert len(bangalore_bav["bav_per_planet"]) == 7


def test_each_bav_row_is_twelve_ints_in_range(bangalore_bav: dict) -> None:
    for planet, row in bangalore_bav["bav_per_planet"].items():
        assert isinstance(row, list), f"{planet} row not a list"
        assert len(row) == 12, f"{planet} row length != 12"
        for s, b in enumerate(row):
            assert isinstance(b, int), f"{planet}[{s}] not an int"
            # max 8 contributors -> max 8 bindus per sign
            assert 0 <= b <= 8, f"{planet}[{s}] = {b} out of 0..8"


def test_sav_is_twelve_ints(bangalore_bav: dict) -> None:
    sav = bangalore_bav["sav"]
    assert isinstance(sav, list)
    assert len(sav) == 12
    for s, v in enumerate(sav):
        assert isinstance(v, int), f"sav[{s}] not an int"
        # 7 planets * 8 contributors = 56 max per sign; loose upper bound.
        assert 0 <= v <= 56, f"sav[{s}] = {v} out of 0..56"


def test_sav_total_in_typical_range(bangalore_bav: dict) -> None:
    """SAV grand total is a fixed invariant: 338.

    Each row's total equals the sum of the rule-table row lengths (which is
    chart-independent). Across the 7 BAVs that's:
        Sun=48 + Moon=49 + Mars=40 + Mercury=54 + Jupiter=56 + Venus=52 + Saturn=39
        = 338.
    This holds for every valid natal chart.
    """
    total = sum(bangalore_bav["sav"])
    assert total == 338


# ---------------------------------------------------------------------------
# SAV is the column sum of the 7 BAV rows
# ---------------------------------------------------------------------------

def test_sav_equals_column_sum(bangalore_bav: dict) -> None:
    bavs = bangalore_bav["bav_per_planet"]
    for s in range(12):
        col_sum = sum(bavs[p][s] for p in BAV_PLANETS)
        assert bangalore_bav["sav"][s] == col_sum, (
            f"sign {s+1}: sav={bangalore_bav['sav'][s]} but column sum={col_sum}"
        )


# ---------------------------------------------------------------------------
# Symmetry / individual-rule end-to-end
# ---------------------------------------------------------------------------

def test_sun_in_own_bav_from_sun_contributor() -> None:
    """The Sun contributes bindus to the Sun's BAV in offsets {1,2,4,7,8,9,10,11}
    counted from the Sun's own natal sign.

    With ALL planets at sign 1 (Aries) and Lagna at sign 1, moving the Sun
    alone to sign 2 should rotate ONLY the Sun-from-Sun contribution.
    Differencing localises that contributor's footprint into the Sun's BAV.

    Sun-from-Sun at sign 1 deposits at signs {1,2,4,7,8,9,10,11}.
    Sun-from-Sun at sign 2 deposits at signs {2,3,5,8,9,10,11,12}.
    Removed:  {1,4,7}   -> indices 0,3,6
    Added:    {3,5,12}  -> indices 2,4,11
    Common:   {2,8,9,10,11}
    """
    asc = {"sign": 1}
    chart_all_aries = {p: {"sign": 1} for p in BAV_PLANETS}

    base = compute_ashtakavarga(chart_all_aries, asc)["bav_per_planet"]["Sun"]

    chart_sun_taurus = {p: {"sign": 1} for p in BAV_PLANETS}
    chart_sun_taurus["Sun"] = {"sign": 2}
    shifted = compute_ashtakavarga(chart_sun_taurus, asc)["bav_per_planet"]["Sun"]

    diff = [shifted[i] - base[i] for i in range(12)]
    expected_drops = {0, 3, 6}        # signs 1,4,7 lost a bindu
    expected_gains = {2, 4, 11}       # signs 3,5,12 gained a bindu
    expected_unchanged = {1, 7, 8, 9, 10}  # signs 2,8,9,10,11 unchanged

    for i in range(12):
        if i in expected_drops:
            assert diff[i] == -1, f"sign {i+1} expected -1 diff, got {diff[i]}"
        elif i in expected_gains:
            assert diff[i] == +1, f"sign {i+1} expected +1 diff, got {diff[i]}"
        elif i in expected_unchanged:
            assert diff[i] == 0, f"sign {i+1} expected 0 diff, got {diff[i]}"


# ---------------------------------------------------------------------------
# Pinned Bangalore baseline -- totals per planet
# ---------------------------------------------------------------------------
#
# Per-planet totals are chart-INDEPENDENT: each total = sum of rule-row
# lengths = the same number for every chart. So the assertions below are
# really invariants of the rule table:
#   Sun=48, Moon=49, Mars=40, Mercury=54, Jupiter=56, Venus=52, Saturn=39
# (Total 338 = SAV grand total.)

EXPECTED_BANGALORE_TOTALS = {
    "Sun": 48,
    "Moon": 49,
    "Mars": 40,
    "Mercury": 54,
    "Jupiter": 56,
    "Venus": 52,
    "Saturn": 39,
}


def test_bangalore_pinned_per_planet_totals(bangalore_bav: dict) -> None:
    assert bangalore_bav["bav_totals"] == EXPECTED_BANGALORE_TOTALS


def test_bangalore_sav_grand_total(bangalore_bav: dict) -> None:
    assert sum(bangalore_bav["sav"]) == sum(EXPECTED_BANGALORE_TOTALS.values())


# ---------------------------------------------------------------------------
# Edge case: all planets at sign 1 (Aries) -- synthetic chart
# ---------------------------------------------------------------------------

def test_all_planets_at_aries_returns_valid_matrix() -> None:
    """All 7 BAV planets and Lagna at sign 1: function must return a valid
    matrix. Every BAV row must still sum to its rule-row length."""
    d1 = {planet: {"sign": 1} for planet in BAV_PLANETS}
    asc = {"sign": 1}

    result = compute_ashtakavarga(d1, asc)

    assert set(result["bav_per_planet"]) == set(BAV_PLANETS)
    for planet, row in result["bav_per_planet"].items():
        assert len(row) == 12
        assert all(0 <= b <= 8 for b in row)
        # row total invariant -- same as for any chart
        assert sum(row) == EXPECTED_BANGALORE_TOTALS[planet]
    assert sum(result["sav"]) == 338


# ---------------------------------------------------------------------------
# Negative-path validation
# ---------------------------------------------------------------------------

def test_missing_planet_raises_value_error() -> None:
    d1 = {p: {"sign": 1} for p in BAV_PLANETS if p != "Saturn"}
    with pytest.raises(ValueError, match="Saturn"):
        compute_ashtakavarga(d1, {"sign": 1})


def test_invalid_sign_raises_value_error() -> None:
    d1 = {p: {"sign": 1} for p in BAV_PLANETS}
    d1["Sun"] = {"sign": 13}
    with pytest.raises(ValueError, match="1..12"):
        compute_ashtakavarga(d1, {"sign": 1})


def test_missing_ascendant_sign_raises_value_error() -> None:
    d1 = {p: {"sign": 1} for p in BAV_PLANETS}
    with pytest.raises(ValueError, match="ascendant"):
        compute_ashtakavarga(d1, {})


# ---------------------------------------------------------------------------
# Bonus contributor symmetry: BAV_CONTRIBUTORS shape
# ---------------------------------------------------------------------------

def test_bav_contributors_includes_lagna_and_seven_planets() -> None:
    assert set(BAV_CONTRIBUTORS) == set(BAV_PLANETS) | {"Lagna"}
    assert len(BAV_CONTRIBUTORS) == 8
