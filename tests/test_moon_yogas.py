"""Tests for Moon-based yogas: Sunapha, Anapha, Durudhura, Kemadruma.

BPHS 73 (Chandra-yoga-adhyaya). Each yoga depends on which planets sit
in the 2nd / 12th / same-sign positions from the Moon.
"""
from __future__ import annotations

import pytest

from app.core.yogas import (
    detect_anapha,
    detect_durudhura,
    detect_kemadruma,
    detect_sunapha,
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


# Build a chart with Moon in a specific sign and all other planets in
# deliberately-distant signs. Tests then override individual planet
# positions to set up the desired yoga configuration.
def _base_chart(moon_sign: int) -> dict:
    """Moon at moon_sign; other planets parked 5+ houses away (no Moon yoga)."""
    far_sign = ((moon_sign - 1 + 5) % 12) + 1   # 6th from Moon
    farther_sign = ((moon_sign - 1 + 7) % 12) + 1  # 8th from Moon
    return {
        "Sun":     _planet(((moon_sign - 1 + 4) % 12) + 1),    # 5th from Moon
        "Moon":    _planet(moon_sign),
        "Mars":    _planet(far_sign),
        "Mercury": _planet(farther_sign),
        "Jupiter": _planet(far_sign),
        "Venus":   _planet(farther_sign),
        "Saturn":  _planet(far_sign),
        "Rahu":    _planet(farther_sign),
        "Ketu":    _planet(far_sign),
    }


# --------------------------------------------------------------------------- #
# Sunapha — planet in 2nd from Moon                                           #
# --------------------------------------------------------------------------- #

def test_sunapha_fires_with_jupiter_in_2nd_from_moon() -> None:
    """Moon in Aries (1) + Jupiter in Taurus (2) → 2nd from Moon → Sunapha."""
    chart = _base_chart(moon_sign=1)
    chart["Jupiter"] = _planet(2)   # 2nd from Aries
    result = detect_sunapha(chart, _asc(1))
    assert result is not None
    assert result.name == "Sunapha"
    assert "Jupiter" in result.participants
    assert result.promise_axis == "self_acquired_wealth"


def test_sunapha_does_not_fire_with_only_sun_in_2nd() -> None:
    """Sun in 2nd from Moon does NOT count — BPHS 73 excludes Sun."""
    chart = _base_chart(moon_sign=1)
    chart["Sun"] = _planet(2)
    # All eligible planets are in their distant filler signs.
    assert detect_sunapha(chart, _asc(1)) is None


def test_sunapha_does_not_fire_with_only_nodes_in_2nd() -> None:
    """Rahu/Ketu in 2nd from Moon do NOT count."""
    chart = _base_chart(moon_sign=1)
    chart["Rahu"] = _planet(2)
    chart["Ketu"] = _planet(2)
    assert detect_sunapha(chart, _asc(1)) is None


# --------------------------------------------------------------------------- #
# Anapha — planet in 12th from Moon                                           #
# --------------------------------------------------------------------------- #

def test_anapha_fires_with_venus_in_12th_from_moon() -> None:
    """Moon in Cancer (4) + Venus in Gemini (3) → 12th from Moon → Anapha."""
    chart = _base_chart(moon_sign=4)
    chart["Venus"] = _planet(3)
    result = detect_anapha(chart, _asc(1))
    assert result is not None
    assert result.name == "Anapha"
    assert "Venus" in result.participants
    assert result.promise_axis == "fame_and_social_standing"


def test_anapha_does_not_fire_for_sun_or_nodes_only() -> None:
    chart = _base_chart(moon_sign=4)
    chart["Sun"] = _planet(3)  # Sun in 12th — doesn't count
    assert detect_anapha(chart, _asc(1)) is None


# --------------------------------------------------------------------------- #
# Durudhura — planets in BOTH 2nd AND 12th from Moon                          #
# --------------------------------------------------------------------------- #

def test_durudhura_requires_both_sides() -> None:
    """Jupiter in 2nd AND Mercury in 12th → Durudhura fires."""
    chart = _base_chart(moon_sign=1)
    chart["Jupiter"] = _planet(2)    # 2nd
    chart["Mercury"] = _planet(12)   # 12th from Aries
    result = detect_durudhura(chart, _asc(1))
    assert result is not None
    assert result.name == "Durudhura"
    assert set(result.participants) >= {"Jupiter", "Mercury"}


def test_durudhura_fails_with_only_sunapha() -> None:
    chart = _base_chart(moon_sign=1)
    chart["Jupiter"] = _planet(2)
    # Nothing in 12th
    assert detect_durudhura(chart, _asc(1)) is None


def test_durudhura_fails_with_only_anapha() -> None:
    chart = _base_chart(moon_sign=1)
    chart["Mercury"] = _planet(12)
    # Nothing in 2nd
    assert detect_durudhura(chart, _asc(1)) is None


# --------------------------------------------------------------------------- #
# Kemadruma — Moon fully isolated                                             #
# --------------------------------------------------------------------------- #

def test_kemadruma_fires_when_moon_fully_isolated() -> None:
    """Moon with NO eligible planet in 2nd, 12th, or same-sign → Kemadruma."""
    chart = _base_chart(moon_sign=1)
    # All eligible planets are 5+ houses away — none in 2nd, 12th, or 1.
    result = detect_kemadruma(chart, _asc(1))
    assert result is not None
    assert result.name == "Kemadruma"
    assert result.promise_axis == "affliction_poverty_isolation"
    assert 0.0 <= result.strength <= 1.0


def test_kemadruma_cancelled_by_sunapha_planet() -> None:
    """If any eligible planet is in 2nd from Moon, Kemadruma does NOT fire."""
    chart = _base_chart(moon_sign=1)
    chart["Jupiter"] = _planet(2)   # Sunapha exists → Kemadruma cancelled
    assert detect_kemadruma(chart, _asc(1)) is None


def test_kemadruma_cancelled_by_anapha_planet() -> None:
    chart = _base_chart(moon_sign=1)
    chart["Mercury"] = _planet(12)  # Anapha exists → Kemadruma cancelled
    assert detect_kemadruma(chart, _asc(1)) is None


def test_kemadruma_cancelled_by_conjunction_with_moon() -> None:
    """Planet conjunct Moon (same sign) cancels Kemadruma per classical
    interpretation (the conjunction provides support)."""
    chart = _base_chart(moon_sign=1)
    chart["Jupiter"] = _planet(1)   # Jupiter conjunct Moon in Aries
    assert detect_kemadruma(chart, _asc(1)) is None


def test_kemadruma_not_cancelled_by_sun_or_nodes_only() -> None:
    """Sun/Rahu/Ketu conjunct Moon does NOT cancel Kemadruma."""
    chart = _base_chart(moon_sign=1)
    chart["Sun"] = _planet(1)
    chart["Rahu"] = _planet(2)   # Rahu in 2nd
    chart["Ketu"] = _planet(12)  # Ketu in 12th
    result = detect_kemadruma(chart, _asc(1))
    assert result is not None, (
        "Sun + nodes near Moon should NOT cancel Kemadruma per BPHS 73"
    )
