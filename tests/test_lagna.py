"""Engine-layer tests for ascendant (Lagna) and whole-sign house counting.

These tests cover the two pure functions added in the Phase 3 Lagna pass:
- `calculate_ascendant(jd, lat, lon)`
- `whole_sign_house(asc_sign, planet_sign)`

They do NOT touch routes, daemon, or persistence — that wiring lands in a
follow-up commit once the engine layer is reviewed.
"""
from __future__ import annotations

import pytest
import swisseph as swe

from app.core.ephemeris_engine import calculate_ascendant, whole_sign_house


# ============================================================================
# calculate_ascendant
# ============================================================================
# Pinned baseline: Bangalore 1990-07-15 12:00 IST (UTC 06:30).
# Independently verifiable via any Vedic-astrology calculator (drikpanchang,
# prokerala, Jagannatha Hora). They will all report Virgo (Kanya) Lagna near
# 173-174 deg sidereal Lahiri longitude. Do NOT regenerate from engine output.

def test_bangalore_1990_ascendant_is_virgo() -> None:
    jd = swe.julday(1990, 7, 15, 6.5, swe.GREG_CAL)
    asc = calculate_ascendant(jd, latitude=12.97, longitude=77.59)
    assert asc["sign_name"] == "Virgo"
    assert asc["sign"] == 6
    assert 150.0 <= asc["longitude"] < 180.0
    # Tighter pin: Swiss Ephemeris reports ~173.99 deg for this birth.
    assert 173.0 <= asc["longitude"] <= 175.0


def test_ascendant_changes_with_location() -> None:
    """Same moment, different geographies -> different ascending sign.

    The whole point of the ascendant is that it's geocentric — it depends on
    where on Earth you stand. If two wildly different lat/lon return the same
    sign at the same moment, something is wired wrong.
    """
    jd = swe.julday(1990, 7, 15, 6.5, swe.GREG_CAL)
    bangalore = calculate_ascendant(jd, 12.97, 77.59)
    new_york = calculate_ascendant(jd, 40.71, -74.01)
    assert bangalore["sign"] != new_york["sign"]


def test_ascendant_longitude_always_in_range() -> None:
    jd = swe.julday(2025, 1, 1, 12.0, swe.GREG_CAL)
    for lat, lon in [(0.0, 0.0), (45.0, 90.0), (-30.0, -60.0), (89.0, 0.0)]:
        asc = calculate_ascendant(jd, lat, lon)
        assert 0.0 <= asc["longitude"] < 360.0
        assert 1 <= asc["sign"] <= 12
        assert 0.0 <= asc["degree_in_sign"] < 30.0
        assert asc["sign_name"] in (
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        )


def test_ascendant_advances_through_signs_over_a_day() -> None:
    """Over 24 hours at a fixed location, the ascendant cycles through all
    12 signs. Sampling every 2 hours should hit at least 10 distinct signs."""
    base_jd = swe.julday(1990, 7, 15, 0.0, swe.GREG_CAL)
    signs_seen = {
        calculate_ascendant(base_jd + h / 24.0, 12.97, 77.59)["sign"]
        for h in range(0, 24, 2)
    }
    assert len(signs_seen) >= 10, f"only saw signs {sorted(signs_seen)} over 24h"


# ============================================================================
# whole_sign_house
# ============================================================================

@pytest.mark.parametrize("asc,planet,expected", [
    (1, 1, 1),    # asc Aries, planet Aries -> 1st
    (1, 2, 2),    # asc Aries, planet Taurus -> 2nd
    (1, 12, 12),  # asc Aries, planet Pisces -> 12th
    (6, 6, 1),    # any same-sign -> 1st
    (10, 1, 4),   # asc Capricorn, planet Aries -> 4th
    (10, 12, 3),  # asc Capricorn, planet Pisces -> 3rd
    (12, 1, 2),   # asc Pisces, planet Aries -> 2nd (wrap)
    (12, 11, 12), # asc Pisces, planet Aquarius -> 12th
    (3, 9, 7),    # opposition: 3rd sign -> 9th sign = 7th house
])
def test_whole_sign_house(asc: int, planet: int, expected: int) -> None:
    assert whole_sign_house(asc, planet) == expected


def test_whole_sign_house_validates_range() -> None:
    with pytest.raises(ValueError):
        whole_sign_house(0, 1)
    with pytest.raises(ValueError):
        whole_sign_house(1, 13)
    with pytest.raises(ValueError):
        whole_sign_house(13, 13)


def test_whole_sign_opposition_invariant() -> None:
    """The 7th house is always the opposite sign to the ascendant. Verify
    this property holds for all 12 ascendant choices."""
    for asc in range(1, 13):
        opposite_sign = ((asc - 1 + 6) % 12) + 1
        assert whole_sign_house(asc, opposite_sign) == 7
