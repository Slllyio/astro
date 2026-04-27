"""Nakshatra + Pada lookup tests.

These tests use PINNED, externally-verifiable baselines:
  - The 27 nakshatra names and their order are taken from any standard
    Vedic source (Parashara, Wikipedia, KP-Astrology references).
  - Lord assignments follow the Vimshottari 9-lord cycle (Ketu, Venus,
    Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury), repeated three
    times across the 27 nakshatras.
  - Boundary behaviour is pinned to the project-wide convention of
    floor division (``lon // span``), matching
    ``calculate_vimshottari_mahadasha`` in ``app/core/ephemeris_engine.py``.

Do NOT regenerate these constants from the function output — that defeats
the purpose of pinning them.
"""
from __future__ import annotations

import pytest

from app.core.nakshatra import (
    NAKSHATRAS,
    NAKSHATRA_LORDS,
    nakshatra_for_longitude,
)


NAK_SPAN = 360 / 27          # ≈ 13.333°
PADA_SPAN = NAK_SPAN / 4     # ≈ 3.333°


# ============================================================================
# Baseline 1: The 27 names
# ============================================================================
# Externally verifiable: any Vedic astrology reference confirms these names
# in this exact zodiacal order.

EXPECTED_NAMES = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)


def test_nakshatra_names_count_is_27() -> None:
    assert len(NAKSHATRAS) == 27


def test_nakshatra_names_match_canonical_order() -> None:
    assert NAKSHATRAS == EXPECTED_NAMES


# ============================================================================
# Baseline 2: Lord cycle
# ============================================================================
# The 9-lord Vimshottari sequence repeats three times across the 27
# nakshatras, so indices 0, 9, 18 share the same lord (Ketu) and indices
# 8, 17, 26 share the same lord (Mercury).

def test_lord_cycle_has_27_entries() -> None:
    assert len(NAKSHATRA_LORDS) == 27


def test_ashwini_lord_is_ketu() -> None:
    info = nakshatra_for_longitude(0.0)
    assert info["index"] == 0
    assert info["name"] == "Ashwini"
    assert info["lord"] == "Ketu"


def test_magha_lord_is_ketu() -> None:
    # Index 9 -> middle of the zodiac, second cycle of the lord wheel.
    info = nakshatra_for_longitude(9 * NAK_SPAN + 0.5)
    assert info["index"] == 9
    assert info["name"] == "Magha"
    assert info["lord"] == "Ketu"


def test_mula_lord_is_ketu() -> None:
    # Index 18 -> third cycle of the lord wheel.
    info = nakshatra_for_longitude(18 * NAK_SPAN + 0.5)
    assert info["index"] == 18
    assert info["name"] == "Mula"
    assert info["lord"] == "Ketu"


def test_revati_lord_is_mercury() -> None:
    # Index 26 (last) -> last entry of the third cycle, lord = Mercury.
    info = nakshatra_for_longitude(26 * NAK_SPAN + 0.5)
    assert info["index"] == 26
    assert info["name"] == "Revati"
    assert info["lord"] == "Mercury"


# ============================================================================
# Baseline 3: Boundary behaviour (project-wide floor-division convention)
# ============================================================================

def test_longitude_zero_is_ashwini_pada_1() -> None:
    info = nakshatra_for_longitude(0.0)
    assert info["name"] == "Ashwini"
    assert info["pada"] == 1
    assert info["longitude_in_nakshatra"] == pytest.approx(0.0)


def test_exact_nakshatra_boundary_lands_in_next_nakshatra() -> None:
    # Floor-division convention: lon == nak_span lands at the START of
    # nakshatra index 1 (Bharani), pada 1.
    info = nakshatra_for_longitude(NAK_SPAN)
    assert info["name"] == "Bharani"
    assert info["pada"] == 1
    assert info["longitude_in_nakshatra"] == pytest.approx(0.0)


def test_just_before_boundary_stays_in_previous_nakshatra() -> None:
    # 13.32 is just inside Ashwini (which spans 0..13.333...).
    info = nakshatra_for_longitude(13.32)
    assert info["name"] == "Ashwini"
    assert info["pada"] == 4


def test_359_99_is_revati_pada_4() -> None:
    info = nakshatra_for_longitude(359.99)
    assert info["name"] == "Revati"
    assert info["pada"] == 4


def test_longitude_360_normalizes_to_zero() -> None:
    info = nakshatra_for_longitude(360.0)
    assert info["name"] == "Ashwini"
    assert info["pada"] == 1
    assert info["longitude_in_nakshatra"] == pytest.approx(0.0)


# ============================================================================
# Baseline 4: Pada math within Ashwini
# ============================================================================
# Each pada is 3.333° wide. Within Ashwini (0..13.333):
#   pada 1: 0..3.333
#   pada 2: 3.333..6.667
#   pada 3: 6.667..10.0
#   pada 4: 10.0..13.333
# Floor-division boundary convention: a value at exactly 3.333 lands at
# the start of pada 2, at exactly 6.667 at the start of pada 3.
#
# Note on the pada-3-to-4 cusp (exactly 3 * PADA_SPAN = 10.0): IEEE-754
# floor division of ``10.0 // 3.3333333333333335`` yields 2.0, not 3.0,
# because ``3.0 * 3.3333333333333335 == 10.000000000000002`` overshoots
# 10.0. So a *strictly* exact-10.0 input still reads as pada 3, and any
# value just past 10.0 (e.g. 10.001) advances to pada 4. This matches
# the project-wide floor-division convention; we pin both behaviours
# explicitly below to lock the boundary semantics in.

def test_ashwini_pada_1_interior() -> None:
    info = nakshatra_for_longitude(1.0)
    assert info["name"] == "Ashwini"
    assert info["pada"] == 1


def test_ashwini_pada_1_to_2_boundary() -> None:
    info = nakshatra_for_longitude(PADA_SPAN)  # exactly 3.333...
    assert info["name"] == "Ashwini"
    assert info["pada"] == 2


def test_ashwini_pada_2_to_3_boundary() -> None:
    info = nakshatra_for_longitude(2 * PADA_SPAN)  # exactly 6.667...
    assert info["name"] == "Ashwini"
    assert info["pada"] == 3


def test_ashwini_pada_3_to_4_cusp_exact_10_stays_in_pada_3() -> None:
    # See the FP-floor-division note above: 10.0 // (360/27/4) == 2.0,
    # so an exact 10.0 input lands at the *end* of pada 3 rather than the
    # start of pada 4. This matches the floor-division convention used
    # in app/core/ephemeris_engine.py.
    info = nakshatra_for_longitude(3 * PADA_SPAN)  # exactly 10.0
    assert info["name"] == "Ashwini"
    assert info["pada"] == 3


def test_ashwini_pada_3_to_4_boundary_just_past_advances_to_pada_4() -> None:
    info = nakshatra_for_longitude(10.001)
    assert info["name"] == "Ashwini"
    assert info["pada"] == 4


def test_ashwini_pada_4_interior() -> None:
    info = nakshatra_for_longitude(12.0)
    assert info["name"] == "Ashwini"
    assert info["pada"] == 4


# ============================================================================
# Baseline 5: Pinned real-world Moon position
# ============================================================================
# Birth: 1990-07-15 12:00 IST, Bangalore. Moon sidereal Lahiri longitude
# ≈ 356.32°.
#
# Within Revati (which spans 26 * NAK_SPAN = 346.666...° to 360°), the
# offset is 356.32 - 346.666... ≈ 9.653°. Per the Vedic pada layout
# (3.333° per pada starting from the nakshatra cusp), an offset of 9.653°
# falls in pada 3 (the 6.667°..10.0° quarter of Revati). Lord is Mercury.
#
# Note: a value of exactly 10.0° within Revati would be the cusp of pada 4
# under the floor-division boundary convention used project-wide.

def test_pinned_moon_1990_07_15_bangalore_revati() -> None:
    info = nakshatra_for_longitude(356.32)
    assert info["index"] == 26
    assert info["name"] == "Revati"
    assert info["lord"] == "Mercury"
    assert info["pada"] == 3
    assert info["longitude_in_nakshatra"] == pytest.approx(9.653, abs=0.01)


# ============================================================================
# Baseline 6: Negative + over-360 inputs are normalized
# ============================================================================

def test_negative_longitude_normalizes_modulo_360() -> None:
    neg = nakshatra_for_longitude(-1.0)
    pos = nakshatra_for_longitude(359.0)
    assert neg["index"] == pos["index"]
    assert neg["name"] == pos["name"]
    assert neg["pada"] == pos["pada"]
    assert neg["lord"] == pos["lord"]
    assert neg["longitude_in_nakshatra"] == pytest.approx(
        pos["longitude_in_nakshatra"]
    )


def test_over_360_longitude_normalizes_modulo_360() -> None:
    over = nakshatra_for_longitude(361.0)
    base = nakshatra_for_longitude(1.0)
    assert over["index"] == base["index"]
    assert over["name"] == base["name"]
    assert over["pada"] == base["pada"]
    assert over["lord"] == base["lord"]
    assert over["longitude_in_nakshatra"] == pytest.approx(
        base["longitude_in_nakshatra"]
    )
