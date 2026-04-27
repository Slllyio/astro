"""Tests for the Shodashavarga divisional charts (D2..D60).

Each test pins a hand-traced expected outcome derived from the Parashari
formulas, NOT from the engine itself. Boundary tests use pytest.approx with
a small absolute tolerance to absorb floating-point round-off.
"""
from __future__ import annotations

import pytest

from app.core.ephemeris_engine import calculate_divisional_longitude
from app.core.shodashavarga import (
    SHODASHAVARGA_DIVISORS,
    SHODASHAVARGA_NAMES,
    compute_divisional_charts,
    compute_divisional_longitude,
)


# Helper: derive (sign_1based, degree_in_sign) from a 0..360 longitude.
def _split(lon: float) -> tuple[int, float]:
    sign_index = int(lon // 30)
    return sign_index + 1, lon - sign_index * 30.0


# ----------------------------- D2 Hora --------------------------------------


def test_d2_hora_first_half_odd_sign_maps_to_leo():
    """0deg Aries (odd, first half) -> Leo (Sun's hora)."""
    lon = compute_divisional_longitude(0.0, 2)
    sign, _ = _split(lon)
    assert sign == 5  # Leo


def test_d2_hora_second_half_odd_sign_maps_to_cancer():
    """15.001deg Aries (odd, second half) -> Cancer (Moon's hora)."""
    lon = compute_divisional_longitude(15.001, 2)
    sign, _ = _split(lon)
    assert sign == 4  # Cancer


def test_d2_hora_first_half_even_sign_maps_to_cancer():
    """0deg Taurus (even, first half) -> Cancer (Moon's hora)."""
    lon = compute_divisional_longitude(30.0, 2)
    sign, _ = _split(lon)
    assert sign == 4  # Cancer


def test_d2_hora_second_half_even_sign_maps_to_leo():
    """20deg Taurus (even, second half) -> Leo (Sun's hora)."""
    lon = compute_divisional_longitude(30.0 + 20.0, 2)
    sign, _ = _split(lon)
    assert sign == 5  # Leo


# ----------------------------- D3 Drekkana ----------------------------------


def test_d3_drekkana_first_part_same_sign():
    """5deg Aries -> 1st drekkana -> Aries."""
    lon = compute_divisional_longitude(5.0, 3)
    sign, _ = _split(lon)
    assert sign == 1  # Aries


def test_d3_drekkana_second_part_5th_sign():
    """15deg Aries -> 2nd drekkana -> Leo (5th from Aries)."""
    lon = compute_divisional_longitude(15.0, 3)
    sign, _ = _split(lon)
    assert sign == 5  # Leo


def test_d3_drekkana_third_part_9th_sign():
    """25deg Aries -> 3rd drekkana -> Sagittarius (9th from Aries)."""
    lon = compute_divisional_longitude(25.0, 3)
    sign, _ = _split(lon)
    assert sign == 9  # Sagittarius


# ----------------------------- D7 Saptamsa ----------------------------------


def test_d7_saptamsa_odd_sign_first_part():
    """0deg Aries (odd) -> 1st saptamsa -> Aries (starts from itself)."""
    lon = compute_divisional_longitude(0.0, 7)
    sign, _ = _split(lon)
    assert sign == 1  # Aries


def test_d7_saptamsa_odd_sign_second_part():
    """A point just past 30/7deg Aries -> 2nd saptamsa -> Taurus."""
    span = 30.0 / 7.0
    lon = compute_divisional_longitude(span + 0.01, 7)
    sign, _ = _split(lon)
    assert sign == 2  # Taurus


def test_d7_saptamsa_even_sign_first_part_starts_from_seventh():
    """0deg Taurus (even) -> 1st saptamsa -> Scorpio (7th from Taurus)."""
    lon = compute_divisional_longitude(30.0, 7)
    sign, _ = _split(lon)
    assert sign == 8  # Scorpio


def test_d7_saptamsa_even_sign_last_part_wraps():
    """Late Taurus (even) close to 30deg -> 7th saptamsa -> Taurus
    (Scorpio + 6 mod 12 = Taurus)."""
    span = 30.0 / 7.0
    # 7th part: index 6, range [6*span, 7*span) within Taurus.
    lon = compute_divisional_longitude(30.0 + 6.0 * span + 0.01, 7)
    sign, _ = _split(lon)
    assert sign == 2  # Taurus


# ----------------------------- D9 fallback ----------------------------------


def test_d9_navamsa_falls_back_to_engine():
    """compute_divisional_longitude(60.0, 9) must match engine output exactly.
    60deg = start of Gemini, 1st navamsa."""
    ours = compute_divisional_longitude(60.0, 9)
    theirs = calculate_divisional_longitude(60.0, 9)
    assert ours == pytest.approx(theirs, abs=1e-9)


def test_d10_dasamsa_falls_back_to_engine():
    """D10 must also defer to the existing engine."""
    ours = compute_divisional_longitude(45.5, 10)
    theirs = calculate_divisional_longitude(45.5, 10)
    assert ours == pytest.approx(theirs, abs=1e-9)


# ----------------------------- D12 Dwadasamsa -------------------------------


def test_d12_dwadasamsa_first_part_same_sign():
    """1.0deg Aries (clearly within 1st part of 0-2.5deg) -> Aries."""
    lon = compute_divisional_longitude(1.0, 12)
    sign, _ = _split(lon)
    assert sign == 1  # Aries


def test_d12_dwadasamsa_twelfth_part_pisces():
    """27.5deg Aries -> 12th dwadasamsa -> Pisces (Aries + 11)."""
    lon = compute_divisional_longitude(27.5, 12)
    sign, _ = _split(lon)
    assert sign == 12  # Pisces


def test_d12_dwadasamsa_taurus_first_part():
    """0deg Taurus -> 1st dwadasamsa -> Taurus."""
    lon = compute_divisional_longitude(30.0, 12)
    sign, _ = _split(lon)
    assert sign == 2  # Taurus


# ----------------------------- D16 Shodasamsa -------------------------------


def test_d16_movable_starts_from_aries():
    """0deg Aries (movable) -> 1st shodasamsa -> Aries."""
    lon = compute_divisional_longitude(0.0, 16)
    sign, _ = _split(lon)
    assert sign == 1  # Aries


def test_d16_fixed_starts_from_leo():
    """0deg Taurus (fixed) -> 1st shodasamsa -> Leo."""
    lon = compute_divisional_longitude(30.0, 16)
    sign, _ = _split(lon)
    assert sign == 5  # Leo


def test_d16_dual_starts_from_sagittarius():
    """0deg Gemini (dual) -> 1st shodasamsa -> Sagittarius."""
    lon = compute_divisional_longitude(60.0, 16)
    sign, _ = _split(lon)
    assert sign == 9  # Sagittarius


def test_d16_movable_second_part():
    """Just past 1.875deg Aries (movable) -> 2nd shodasamsa -> Taurus."""
    lon = compute_divisional_longitude(1.875 + 0.001, 16)
    sign, _ = _split(lon)
    assert sign == 2  # Taurus


# ----------------------------- D24 Chaturvimsamsa ---------------------------


def test_d24_odd_sign_starts_from_leo():
    """0deg Aries (odd) -> 1st chaturvimsamsa -> Leo."""
    lon = compute_divisional_longitude(0.0, 24)
    sign, _ = _split(lon)
    assert sign == 5  # Leo


def test_d24_even_sign_starts_from_cancer():
    """0deg Taurus (even) -> 1st chaturvimsamsa -> Cancer."""
    lon = compute_divisional_longitude(30.0, 24)
    sign, _ = _split(lon)
    assert sign == 4  # Cancer


def test_d24_odd_sign_second_part():
    """Just past 1.25deg Aries (odd) -> 2nd chaturvimsamsa -> Virgo (Leo+1)."""
    lon = compute_divisional_longitude(1.25 + 0.001, 24)
    sign, _ = _split(lon)
    assert sign == 6  # Virgo


# ----------------------------- D30 Trimsamsa --------------------------------


def test_d30_trimsamsa_odd_sign_mars_range():
    """2.5deg Aries (Mars's range 0-5) -> Aries (Mars's own sign)."""
    lon = compute_divisional_longitude(2.5, 30)
    sign, _ = _split(lon)
    assert sign == 1  # Aries


def test_d30_trimsamsa_odd_sign_saturn_range():
    """8deg Aries (Saturn's range 5-10) -> Aquarius (Saturn's own sign)."""
    lon = compute_divisional_longitude(8.0, 30)
    sign, _ = _split(lon)
    assert sign == 11  # Aquarius


def test_d30_trimsamsa_odd_sign_jupiter_range():
    """15deg Aries (Jupiter's range 10-18) -> Sagittarius."""
    lon = compute_divisional_longitude(15.0, 30)
    sign, _ = _split(lon)
    assert sign == 9  # Sagittarius


def test_d30_trimsamsa_even_sign_venus_range():
    """2.5deg Taurus (even, Venus's range 0-5) -> Taurus (Venus's own sign)."""
    lon = compute_divisional_longitude(30.0 + 2.5, 30)
    sign, _ = _split(lon)
    assert sign == 2  # Taurus


def test_d30_trimsamsa_even_sign_mars_range():
    """27deg Taurus (even, Mars's range 25-30) -> Scorpio (Mars's own sign)."""
    lon = compute_divisional_longitude(30.0 + 27.0, 30)
    sign, _ = _split(lon)
    assert sign == 8  # Scorpio


# ----------------------------- D20 Vimsamsa ---------------------------------


def test_d20_movable_starts_from_aries():
    """0deg Aries (movable) -> 1st vimsamsa -> Aries."""
    lon = compute_divisional_longitude(0.0, 20)
    sign, _ = _split(lon)
    assert sign == 1


def test_d20_fixed_starts_from_sagittarius():
    """0deg Taurus (fixed) -> 1st vimsamsa -> Sagittarius."""
    lon = compute_divisional_longitude(30.0, 20)
    sign, _ = _split(lon)
    assert sign == 9


def test_d20_dual_starts_from_leo():
    """0deg Gemini (dual) -> 1st vimsamsa -> Leo."""
    lon = compute_divisional_longitude(60.0, 20)
    sign, _ = _split(lon)
    assert sign == 5


# ----------------------------- D27 Bhamsa -----------------------------------


def test_d27_movable_starts_from_aries():
    """0deg Aries (movable) -> 1st bhamsa -> Aries."""
    lon = compute_divisional_longitude(0.0, 27)
    sign, _ = _split(lon)
    assert sign == 1


def test_d27_fixed_starts_from_cancer():
    """0deg Taurus (fixed) -> 1st bhamsa -> Cancer."""
    lon = compute_divisional_longitude(30.0, 27)
    sign, _ = _split(lon)
    assert sign == 4


def test_d27_dual_starts_from_libra():
    """0deg Gemini (dual) -> 1st bhamsa -> Libra."""
    lon = compute_divisional_longitude(60.0, 27)
    sign, _ = _split(lon)
    assert sign == 7


# ----------------------------- D40 Khavedamsa -------------------------------


def test_d40_odd_sign_starts_from_aries():
    """0deg Aries (odd) -> 1st khavedamsa -> Aries."""
    lon = compute_divisional_longitude(0.0, 40)
    sign, _ = _split(lon)
    assert sign == 1


def test_d40_even_sign_starts_from_libra():
    """0deg Taurus (even) -> 1st khavedamsa -> Libra."""
    lon = compute_divisional_longitude(30.0, 40)
    sign, _ = _split(lon)
    assert sign == 7


# ----------------------------- D45 Akshavedamsa -----------------------------


def test_d45_movable_starts_from_aries():
    """0deg Aries (movable) -> 1st akshavedamsa -> Aries."""
    lon = compute_divisional_longitude(0.0, 45)
    sign, _ = _split(lon)
    assert sign == 1


def test_d45_fixed_starts_from_leo():
    """0deg Taurus (fixed) -> 1st akshavedamsa -> Leo."""
    lon = compute_divisional_longitude(30.0, 45)
    sign, _ = _split(lon)
    assert sign == 5


def test_d45_dual_starts_from_sagittarius():
    """0deg Gemini (dual) -> 1st akshavedamsa -> Sagittarius."""
    lon = compute_divisional_longitude(60.0, 45)
    sign, _ = _split(lon)
    assert sign == 9


# ----------------------------- D60 Shastiamsa -------------------------------


def test_d60_starts_from_same_sign():
    """0deg Aries -> 1st shastiamsa -> Aries (cycles from itself)."""
    lon = compute_divisional_longitude(0.0, 60)
    sign, _ = _split(lon)
    assert sign == 1


def test_d60_second_part_next_sign():
    """Just past 0.5deg Aries -> 2nd shastiamsa -> Taurus."""
    lon = compute_divisional_longitude(0.5 + 0.001, 60)
    sign, _ = _split(lon)
    assert sign == 2


# ----------------------------- Boundary epsilon -----------------------------


def test_d2_boundary_epsilon():
    """Boundary at exactly 15deg Aries: floor maps to second half (Cancer for odd)."""
    lon = compute_divisional_longitude(15.0, 2)
    sign, _ = _split(lon)
    # 15.0 / 15 == 1.0, floor=1 -> second half -> Cancer for odd sign.
    assert sign == 4


def test_d3_boundary_epsilon_just_below_10():
    """At 9.999deg Aries we are still in the 1st drekkana -> Aries."""
    lon = compute_divisional_longitude(10.0 - 1e-9, 3)
    sign, _ = _split(lon)
    assert sign == 1


# ----------------------------- Top-level integration ------------------------


def _make_d1(longitude: float) -> dict[str, dict]:
    """Build a single-planet d1 chart with the project's expected shape."""
    sign_index = int(longitude // 30)
    return {
        "Sun": {
            "longitude": longitude,
            "sign": sign_index + 1,
            "sign_name": "X",  # not consumed by the routine under test
            "degree_in_sign": longitude - sign_index * 30.0,
            "is_retrograde": False,
            "name": "Sun",
        }
    }


def test_compute_divisional_charts_returns_all_14_vargas():
    """Top-level integration: the result has 14 vargas and each contains
    a position dict for the input planet with a valid 1..12 sign."""
    d1 = _make_d1(173.99)  # late Virgo

    charts = compute_divisional_charts(d1)

    # Every divisor in the spec is represented.
    assert len(charts) == 14
    for divisor in SHODASHAVARGA_DIVISORS:
        chart_name = SHODASHAVARGA_NAMES[divisor]
        assert chart_name in charts, f"missing varga {chart_name}"

        sun_pos = charts[chart_name]["Sun"]
        # Required keys from position_from_longitude + name.
        for key in ("longitude", "sign", "sign_name", "degree_in_sign", "is_retrograde", "name"):
            assert key in sun_pos, f"{chart_name} Sun position missing {key}"
        assert 1 <= sun_pos["sign"] <= 12, f"{chart_name} Sun sign out of range"
        assert 0.0 <= sun_pos["degree_in_sign"] < 30.0
        assert 0.0 <= sun_pos["longitude"] < 360.0
        assert sun_pos["name"] == "Sun"
        assert sun_pos["is_retrograde"] is False


def test_compute_divisional_charts_preserves_retrograde_flag():
    """A retrograde input planet stays retrograde across all vargas."""
    d1 = _make_d1(100.0)
    d1["Sun"]["is_retrograde"] = True

    charts = compute_divisional_charts(d1)
    for chart_name, chart in charts.items():
        assert chart["Sun"]["is_retrograde"] is True, f"{chart_name} dropped retrograde flag"


def test_compute_divisional_charts_handles_multiple_planets():
    """Multiple planets should each appear in every varga."""
    d1 = {
        "Sun": {"longitude": 10.0, "is_retrograde": False},
        "Moon": {"longitude": 200.0, "is_retrograde": False},
    }
    charts = compute_divisional_charts(d1)
    for chart in charts.values():
        assert set(chart.keys()) == {"Sun", "Moon"}


def test_compute_divisional_longitude_rejects_invalid_divisor():
    with pytest.raises(ValueError):
        compute_divisional_longitude(10.0, 5)  # not a Shodashavarga divisor
    with pytest.raises(ValueError):
        compute_divisional_longitude(10.0, 0)
