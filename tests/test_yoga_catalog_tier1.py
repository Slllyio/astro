"""Tests for the Phase-3B Tier-1 yoga catalog — PMP, Gajakesari,
Budha-Aditya, Raja, Dhana.

Each detector returns a YogaInstance carrying continuous strength. Tests
verify (a) classical formation rules, (b) strength is in [0, 1], and
(c) YogaInstance structural fields are correctly populated.
"""
from __future__ import annotations

import pytest

from app.core.yogas import (
    detect_budha_aditya_instance,
    detect_dhana_yoga,
    detect_gajakesari_instance,
    detect_pancha_mahapurusha,
    detect_raja_yoga,
)


def _planet(sign: int, longitude: float | None = None) -> dict:
    if longitude is None:
        longitude = (sign - 1) * 30.0 + 15.0
    return {
        "sign": sign,
        "longitude": longitude,
        "degree_in_sign": longitude % 30.0,
        "is_retrograde": False,
    }


def _asc(sign: int) -> dict:
    return {"sign": sign, "longitude": (sign - 1) * 30.0}


def _base_chart() -> dict:
    """Neutral chart: planets parked in non-yoga-forming signs."""
    return {
        "Sun":     _planet(2),
        "Moon":    _planet(3),
        "Mars":    _planet(3),
        "Mercury": _planet(11),
        "Jupiter": _planet(11),
        "Venus":   _planet(11),
        "Saturn":  _planet(3),
        "Rahu":    _planet(5),
        "Ketu":    _planet(11),
    }


# --------------------------------------------------------------------------- #
# Pancha Mahapurusha — Phase-3B YogaInstance upgrade                          #
# --------------------------------------------------------------------------- #

def test_pmp_hamsa_fires_jupiter_exalted_in_kendra() -> None:
    """Jupiter exalted in Cancer (4), Lagna Capricorn (10) → Jupiter in 7th
    house (kendra) → Hamsa Yoga fires as YogaInstance."""
    chart = _base_chart()
    chart["Jupiter"] = _planet(4)  # exalted
    result = detect_pancha_mahapurusha(chart, _asc(10))
    names = [y.name for y in result]
    assert "Hamsa" in names
    hamsa = next(y for y in result if y.name == "Hamsa")
    assert hamsa.category == "mahapurusha"
    assert hamsa.participants == ("Jupiter",)
    assert 0.0 <= hamsa.strength <= 1.0


def test_pmp_returns_empty_when_none_fire() -> None:
    chart = _base_chart()
    # No PMP-eligible placements (all star-planets in neutral signs/houses).
    result = detect_pancha_mahapurusha(chart, _asc(1))
    assert result == []


def test_pmp_canonical_order_alphabetical() -> None:
    """When multiple PMP yogas fire, they return in the Ruchaka/Bhadra/Hamsa/
    Malavya/Sasa canonical order from BPHS 36.1-6."""
    # Aries asc; Mars own Aries kendra (1) + Saturn own Capricorn kendra (10)
    chart = _base_chart()
    chart["Mars"] = _planet(1)       # Aries (own, house 1 = kendra) → Ruchaka
    chart["Saturn"] = _planet(10)    # Capricorn (own, house 10 = kendra) → Sasa
    result = detect_pancha_mahapurusha(chart, _asc(1))
    names = [y.name for y in result]
    assert "Ruchaka" in names and "Sasa" in names
    assert names.index("Ruchaka") < names.index("Sasa")


# --------------------------------------------------------------------------- #
# Gajakesari (YogaInstance upgrade)                                           #
# --------------------------------------------------------------------------- #

def test_gajakesari_instance_fires() -> None:
    """Jupiter and Moon in mutual kendra → Gajakesari (as YogaInstance)."""
    chart = _base_chart()
    chart["Jupiter"] = _planet(1)
    chart["Moon"] = _planet(4)  # 4th from Jupiter (kendra distance)
    result = detect_gajakesari_instance(chart, _asc(1))
    assert result is not None
    assert result.name == "Gajakesari"
    assert result.category == "lunar"
    assert set(result.participants) == {"Jupiter", "Moon"}


def test_gajakesari_instance_does_not_fire_non_kendra() -> None:
    chart = _base_chart()
    chart["Jupiter"] = _planet(1)
    chart["Moon"] = _planet(2)  # 2nd from Jupiter (not kendra)
    assert detect_gajakesari_instance(chart, _asc(1)) is None


# --------------------------------------------------------------------------- #
# Budha-Aditya (YogaInstance upgrade)                                         #
# --------------------------------------------------------------------------- #

def test_budha_aditya_instance_fires_when_conjunct() -> None:
    chart = _base_chart()
    chart["Sun"] = _planet(5)
    chart["Mercury"] = _planet(5)  # same sign
    result = detect_budha_aditya_instance(chart, _asc(1))
    assert result is not None
    assert result.name == "Budha-Aditya"
    assert result.category == "solar"


def test_budha_aditya_does_not_fire_different_signs() -> None:
    chart = _base_chart()
    chart["Sun"] = _planet(5)
    chart["Mercury"] = _planet(6)
    assert detect_budha_aditya_instance(chart, _asc(1)) is None


# --------------------------------------------------------------------------- #
# Raja Yoga (kendra-trikona lord conjunction)                                 #
# --------------------------------------------------------------------------- #

def test_raja_yoga_fires_5l_with_4l_for_aries_asc() -> None:
    """For Aries asc: 5L = Sun (trikona), 4L = Moon (kendra). Sun + Moon
    conjunct in same sign → Raja Yoga fires.

    Note: detector picks the STRONGEST pair. The base chart has other
    potential conjunctions in Aquarius (Jupiter+Venus), so we move
    other lords away to make Sun+Moon the only candidate."""
    chart = _base_chart()
    chart["Sun"] = _planet(7)
    chart["Moon"] = _planet(7)   # same sign as Sun → 5L + 4L conjunct
    chart["Jupiter"] = _planet(2)  # move 9L away from any conjunction
    chart["Venus"] = _planet(3)    # move 7L away
    chart["Saturn"] = _planet(9)   # move 10L away
    chart["Mars"] = _planet(11)    # move 1L=8L away (kendra/dusthana)
    result = detect_raja_yoga(chart, _asc(1))
    assert result is not None
    assert result.name == "Raja Yoga"
    assert result.category == "raja"
    # Participants alphabetised
    assert result.participants == ("Moon", "Sun")


def test_raja_yoga_excludes_1l_self_pair() -> None:
    """For Aries asc, 1L = Mars (both kendra AND trikona). Mars alone
    doesn't form Raja Yoga with itself."""
    chart = _base_chart()
    # Move Mars alone; no other kendra-trikona conjunction.
    chart["Mars"] = _planet(1)
    chart["Sun"] = _planet(5)   # 5L solo in Leo
    chart["Moon"] = _planet(4)  # 4L solo in Cancer
    chart["Jupiter"] = _planet(9)  # 9L solo
    chart["Saturn"] = _planet(10)  # 10L solo
    chart["Venus"] = _planet(7)    # 7L solo
    result = detect_raja_yoga(chart, _asc(1))
    assert result is None


def test_raja_yoga_does_not_fire_unrelated_planets() -> None:
    """Two non-kendra-trikona-lord planets in same sign do NOT form Raj Yoga."""
    chart = _base_chart()
    # For Aries asc, Mercury rules 3 (not kendra/trikona) and 6 (not k/t).
    # So Mercury conjunct anything else shouldn't form RY by 6L/3L route.
    chart["Mercury"] = _planet(7)
    chart["Ketu"] = _planet(7)
    # Move actual kendra/trikona lords to non-shared signs.
    chart["Sun"] = _planet(11)
    chart["Moon"] = _planet(3)
    chart["Jupiter"] = _planet(2)
    chart["Saturn"] = _planet(5)
    chart["Venus"] = _planet(6)
    chart["Mars"] = _planet(8)
    result = detect_raja_yoga(chart, _asc(1))
    assert result is None


# --------------------------------------------------------------------------- #
# Dhana Yoga (2L + 11L conjunction)                                           #
# --------------------------------------------------------------------------- #

def test_dhana_yoga_fires_2l_with_11l_aries_asc() -> None:
    """For Aries asc: 2L = Venus (Taurus), 11L = Saturn (Aquarius).
    Venus + Saturn conjunct → Dhana Yoga."""
    chart = _base_chart()
    chart["Venus"] = _planet(11)
    chart["Saturn"] = _planet(11)  # both in Aquarius
    result = detect_dhana_yoga(chart, _asc(1))
    assert result is not None
    assert result.name == "Dhana Yoga"
    assert result.category == "dhana"
    assert set(result.participants) == {"Venus", "Saturn"}


def test_dhana_yoga_does_not_fire_when_lords_separate() -> None:
    chart = _base_chart()
    chart["Venus"] = _planet(11)
    chart["Saturn"] = _planet(7)  # separate signs
    assert detect_dhana_yoga(chart, _asc(1)) is None


def test_dhana_yoga_skipped_when_same_lord_for_2_and_11() -> None:
    """Some ascendants have the same planet ruling both 2nd and 11th.
    For Scorpio asc: 2L = Sagittarius's Jupiter; 11L = Virgo's Mercury —
    different lords. Hmm let me re-check.

    Actually for Aquarius asc: 2L = Pisces's Jupiter; 11L = Sagittarius's
    Jupiter — SAME lord (Jupiter rules both Sagittarius and Pisces).
    Then Dhana Yoga is undefined."""
    chart = _base_chart()
    chart["Jupiter"] = _planet(1)
    result = detect_dhana_yoga(chart, _asc(11))   # Aquarius asc
    # 2L=Jupiter (Pisces), 11L=Jupiter (Sagittarius) → same lord, undefined.
    assert result is None
