"""Tests for Vipareeta Sarala (8L) and Vimala (12L) Raja Yogas.

Both yogas share the BPHS 36 mechanism with Harsha (6L): a dusthana
lord (6/8/12) placed in another dusthana — alone — fires the inverted
"two negatives cancel" yoga. Tests mirror the Harsha test patterns.
"""
from __future__ import annotations

import pytest

from app.core.yoga_types import YogaInstance
from app.core.yogas import (
    detect_vipareeta_sarala,
    detect_vipareeta_vimala,
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


def _chart_with_lord(planet: str, sign: int) -> dict:
    """Minimal chart: target lord plus neutral fillers for other planets.

    Other planets parked in signs that are NOT in the same sign as the
    target — avoids accidental contamination of the alone-in-dusthana
    gate during tests.
    """
    base: dict[str, dict] = {}
    fillers = {
        "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4, "Jupiter": 5,
        "Venus": 6, "Saturn": 7, "Rahu": 8, "Ketu": 11,
    }
    fillers[planet] = sign
    # Avoid sharing the target's sign — bump any filler that collides.
    for p, s in list(fillers.items()):
        if p != planet and s == sign:
            fillers[p] = ((sign + 4) % 12) + 1
    for p, s in fillers.items():
        base[p] = _planet(s)
    return base


# --------------------------------------------------------------------------- #
# Sarala (8L in 6/8/12)                                                       #
# --------------------------------------------------------------------------- #

def test_sarala_aries_asc_8l_in_8th() -> None:
    """Aries asc → 8L = Mars (rules Scorpio = 8th sign). Mars in own 8th
    (Scorpio) fires Sarala."""
    chart = _chart_with_lord("Mars", 8)  # Mars in Scorpio
    result = detect_vipareeta_sarala(chart, _asc(1))
    assert result is not None
    assert isinstance(result, YogaInstance)
    assert result.name == "Vipareeta Sarala"
    assert result.category == "vipareeta_raj"
    assert result.participants == ("Mars",)
    assert result.promise_axis == "longevity_via_transformation"


def test_sarala_aries_asc_8l_in_6th() -> None:
    """Mars (8L for Aries) in Virgo (6th) → Sarala fires."""
    chart = _chart_with_lord("Mars", 6)
    # Mercury (6L) is in filler position; check it's not conjunct Mars.
    chart["Mercury"] = _planet(11)  # move Mercury away from Virgo
    result = detect_vipareeta_sarala(chart, _asc(1))
    assert result is not None


def test_sarala_does_not_fire_for_8l_outside_dusthana() -> None:
    chart = _chart_with_lord("Mars", 4)  # Mars in Cancer = 4th from Aries
    assert detect_vipareeta_sarala(chart, _asc(1)) is None


def test_sarala_alone_in_dusthana_gate() -> None:
    """Sarala blocked when 8L conjunct kendra/trikona lord. For Aries:
    Mars (8L) in Scorpio (8th) AND Saturn (10L) also in Scorpio → blocked."""
    chart = _chart_with_lord("Mars", 8)
    chart["Saturn"] = _planet(8)  # Saturn (10L for Aries) in same sign as Mars
    assert detect_vipareeta_sarala(chart, _asc(1)) is None


def test_sarala_strength_in_range() -> None:
    """Strength is always in [0, 1]."""
    for sign in (6, 8, 12):
        chart = _chart_with_lord("Mars", sign)
        result = detect_vipareeta_sarala(chart, _asc(1))
        if result is not None:
            assert 0.0 <= result.strength <= 1.0


# --------------------------------------------------------------------------- #
# Vimala (12L in 6/8/12)                                                      #
# --------------------------------------------------------------------------- #

def test_vimala_aries_asc_12l_in_12th() -> None:
    """Aries asc → 12L = Jupiter (rules Pisces = 12th sign). Jupiter in
    own 12th (Pisces) fires Vimala."""
    chart = _chart_with_lord("Jupiter", 12)
    # Mercury & other potential conflicts: move them away from Pisces
    chart["Mercury"] = _planet(2)
    result = detect_vipareeta_vimala(chart, _asc(1))
    assert result is not None
    assert result.name == "Vipareeta Vimala"
    assert result.participants == ("Jupiter",)
    assert result.promise_axis == "prudent_wealth_via_loss"


def test_vimala_aries_asc_12l_in_6th() -> None:
    """Jupiter (12L for Aries) in Virgo (6th) → Vimala fires."""
    chart = _chart_with_lord("Jupiter", 6)
    chart["Mercury"] = _planet(2)  # avoid Mercury (6L) in same sign
    result = detect_vipareeta_vimala(chart, _asc(1))
    assert result is not None


def test_vimala_does_not_fire_for_12l_outside_dusthana() -> None:
    chart = _chart_with_lord("Jupiter", 4)
    assert detect_vipareeta_vimala(chart, _asc(1)) is None


def test_vimala_alone_in_dusthana_gate() -> None:
    """Vimala blocked when 12L conjunct kendra/trikona lord."""
    chart = _chart_with_lord("Jupiter", 12)
    chart["Sun"] = _planet(12)  # Sun (5L for Aries trikona) in same sign
    assert detect_vipareeta_vimala(chart, _asc(1)) is None


def test_vimala_strength_in_range() -> None:
    for sign in (6, 8, 12):
        chart = _chart_with_lord("Jupiter", sign)
        chart["Mercury"] = _planet(2)
        result = detect_vipareeta_vimala(chart, _asc(1))
        if result is not None:
            assert 0.0 <= result.strength <= 1.0


# --------------------------------------------------------------------------- #
# Cross-check: 3 Vipareeta yogas distinguishable by dusthana lord             #
# --------------------------------------------------------------------------- #

def test_vipareeta_three_yogas_have_different_promise_axes() -> None:
    """Harsha, Sarala, Vimala address distinct life domains."""
    from app.core.yogas import detect_vipareeta_harsha
    # Use three different charts where each one yoga fires.
    # Harsha (6L Mercury in 6th Virgo):
    harsha_chart = _chart_with_lord("Mercury", 6)
    h = detect_vipareeta_harsha(harsha_chart, _asc(1))
    # Sarala (8L Mars in 8th Scorpio):
    sarala_chart = _chart_with_lord("Mars", 8)
    s = detect_vipareeta_sarala(sarala_chart, _asc(1))
    # Vimala (12L Jupiter in 12th Pisces):
    vimala_chart = _chart_with_lord("Jupiter", 12)
    vimala_chart["Mercury"] = _planet(2)
    v = detect_vipareeta_vimala(vimala_chart, _asc(1))

    assert h is not None and s is not None and v is not None
    promise_axes = {h.promise_axis, s.promise_axis, v.promise_axis}
    assert len(promise_axes) == 3, (
        f"Three Vipareeta yogas should have distinct promise axes; "
        f"got {promise_axes}"
    )
