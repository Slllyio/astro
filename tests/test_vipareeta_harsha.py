"""Tests for Vipareeta Harsha Raj Yoga detection + strength scoring.

The Phase-0 wedge yoga. Forms when the 6th-house-lord (from Lagna) is
placed in the 6th, 8th, or 12th house from Lagna. The "two negatives"
cancel, conferring victory over enemies, recovery from setbacks, and
career success through overcoming adversity.

Reference: BPHS — Vipareeta Raja Yoga chapter.
"""
from __future__ import annotations

import pytest

from app.core.yoga_types import YogaInstance
from app.core.yogas import detect_vipareeta_harsha


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _planet(sign: int, longitude: float | None = None,
            is_retrograde: bool = False) -> dict:
    """Build a chart-entry. Defaults longitude to mid-sign (15°) if omitted."""
    if longitude is None:
        longitude = (sign - 1) * 30.0 + 15.0
    return {
        "sign": sign,
        "longitude": longitude,
        "degree_in_sign": longitude % 30.0,
        "is_retrograde": is_retrograde,
    }


def _asc(sign: int) -> dict:
    return {"sign": sign, "longitude": (sign - 1) * 30.0}


def _chart_with_lord(lord_planet: str, lord_sign: int,
                     lord_longitude: float | None = None) -> dict:
    """Minimal chart: just the 6th lord placement + nine-planet stubs.

    Other planets parked at irrelevant signs to avoid spurious detection
    in any future expanded yoga set sharing the chart fixture.
    """
    base: dict[str, dict] = {
        "Sun": _planet(3),       # Gemini
        "Moon": _planet(11),     # Aquarius
        "Mars": _planet(2),      # Taurus
        "Mercury": _planet(11),  # Aquarius
        "Jupiter": _planet(11),  # Aquarius
        "Venus": _planet(11),    # Aquarius
        "Saturn": _planet(3),    # Gemini
        "Rahu": _planet(5),
        "Ketu": _planet(11),
    }
    base[lord_planet] = _planet(lord_sign, lord_longitude)
    return base


# --------------------------------------------------------------------------- #
# Detection — positive cases                                                  #
# --------------------------------------------------------------------------- #

def test_harsha_aries_asc_6th_lord_in_6th() -> None:
    """Aries asc → 6th lord = Mercury. Mercury in Virgo (own 6th) → forms."""
    chart = _chart_with_lord("Mercury", 6)  # Virgo
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is not None
    assert isinstance(result, YogaInstance)
    assert result.name == "Vipareeta Harsha"
    assert result.category == "vipareeta_raj"
    assert result.participants == ("Mercury",)
    assert result.lords_involved == ("Mercury",)
    assert 6 in result.houses_activated
    assert result.strength > 0.0


def test_harsha_aries_asc_6th_lord_in_8th() -> None:
    """Aries asc → Mercury in Scorpio (8th from Aries) → forms."""
    chart = _chart_with_lord("Mercury", 8)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is not None
    assert result.participants == ("Mercury",)
    assert 8 in result.houses_activated


def test_harsha_aries_asc_6th_lord_in_12th() -> None:
    """Aries asc → Mercury in Pisces (12th from Aries) → forms."""
    chart = _chart_with_lord("Mercury", 12)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is not None
    assert 12 in result.houses_activated


def test_harsha_taurus_asc_with_venus() -> None:
    """Taurus asc → 6th sign = Libra → 6th lord = Venus.
    Venus in Pisces (12th from Taurus, but wait — let me check):

    From Taurus, the houses are: 1=Taurus, 2=Gemini, 3=Cancer, 4=Leo,
    5=Virgo, 6=Libra, 7=Scorpio, 8=Sagittarius, 9=Capricorn, 10=Aquarius,
    11=Pisces, 12=Aries. So Pisces (11) = 11th from Taurus, NOT 12th.
    Use Aries (1) instead = 12th from Taurus.
    """
    chart = _chart_with_lord("Venus", 1)  # Aries = 12th from Taurus
    result = detect_vipareeta_harsha(chart, _asc(2))
    assert result is not None
    assert result.participants == ("Venus",)


def test_harsha_aquarius_asc_with_moon() -> None:
    """Aquarius (11) asc → 6th sign = Cancer (4) → 6th lord = Moon.
    Houses from Aquarius: 1=Aqu, 2=Pis, 3=Ari, 4=Tau, 5=Gem, 6=Can, 7=Leo,
    8=Vir, 9=Lib, 10=Sco, 11=Sag, 12=Cap. So Moon in Virgo (sign 6) =
    8th house from Aquarius → forms.
    """
    chart = _chart_with_lord("Moon", 6)
    result = detect_vipareeta_harsha(chart, _asc(11))
    assert result is not None
    assert result.participants == ("Moon",)
    assert 8 in result.houses_activated


# --------------------------------------------------------------------------- #
# Detection — negative cases                                                  #
# --------------------------------------------------------------------------- #

def test_harsha_aries_asc_6th_lord_in_4th_no_yoga() -> None:
    """Mercury in Cancer = 4th from Aries → no yoga (4 not in {6,8,12})."""
    chart = _chart_with_lord("Mercury", 4)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is None


def test_harsha_aries_asc_6th_lord_in_2nd_no_yoga() -> None:
    """Mercury in Taurus = 2nd from Aries → no yoga."""
    chart = _chart_with_lord("Mercury", 2)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is None


@pytest.mark.parametrize(
    "lord_house,should_form",
    [
        (1, False), (2, False), (3, False), (4, False),
        (5, False), (6, True),  (7, False), (8, True),
        (9, False), (10, False), (11, False), (12, True),
    ],
)
def test_harsha_forms_only_in_dusthana(
    lord_house: int, should_form: bool
) -> None:
    """Sweep across all 12 houses for Aries-asc Mercury placement."""
    # Mercury in (lord_house)-th sign from Aries means sign index = lord_house
    # (since asc_sign = 1, house = (sign - 1) % 12 + 1 = sign for Aries).
    chart = _chart_with_lord("Mercury", lord_house)
    result = detect_vipareeta_harsha(chart, _asc(1))
    if should_form:
        assert result is not None, lord_house
    else:
        assert result is None, lord_house


# --------------------------------------------------------------------------- #
# Strength scoring                                                            #
# --------------------------------------------------------------------------- #

def test_harsha_strength_strong_lord_is_low() -> None:
    """Phase-1 INVERTED strength + corrected Saptavargaja table.

    Mercury at Virgo 15° (longitude 165°): own (Virgo) AND exalted, NOT
    Moolatrikona (Mercury MT range is Virgo 16-20°, longitude 166-170°).
    Saptavargaja takes own=30 (higher tier than exalted=20). Sthana-bala:
        uchcha 60 + saptavargaja 30 + oja_yugma 0 + kendradi 15 + drekkana 15
        = 120 virupa
    Inverted strength = 1 - (120/210) ≈ 0.4286.

    Lower than pre-Phase-1 (0.357) because saptavargaja corrected from
    45 to 30 — bringing Mercury's "strong placement" lower in virupa,
    making the inversion give a HIGHER yoga strength than before. This
    is the expected directional shift from the audit fix."""
    chart = _chart_with_lord("Mercury", 6, lord_longitude=165.0)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is not None
    assert result.strength == pytest.approx(1.0 - 120.0 / 210.0, abs=0.005)


def test_harsha_strength_weak_lord_is_high() -> None:
    """Phase-1 INVERTED strength + corrected Saptavargaja table.

    Mercury debilitated in Pisces 15° (longitude 345°): debilitated.
    Phase-1: debilitated virupa = 0 (was 1.875). Sthana-bala:
        uchcha 0 + saptavargaja 0 + oja_yugma 0 + kendradi 15 + drekkana 15
        = 30 virupa (was 31.875)
    Inverted strength = 1 - (30/210) ≈ 0.8571 (HIGHEST Vipareeta strength
    — textbook Harsha)."""
    chart = _chart_with_lord("Mercury", 12, lord_longitude=345.0)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is not None
    assert result.strength == pytest.approx(1.0 - 30.0 / 210.0, abs=0.005)


def test_harsha_strength_in_range_0_1() -> None:
    """Strength is always normalised to [0, 1]."""
    for sign in (6, 8, 12):
        chart = _chart_with_lord("Mercury", sign)
        result = detect_vipareeta_harsha(chart, _asc(1))
        assert result is not None
        assert 0.0 <= result.strength <= 1.0


# --------------------------------------------------------------------------- #
# Alone-in-dusthana gate (Phase-1 audit fix — classical BPHS / Phaladeepika)  #
# --------------------------------------------------------------------------- #

def test_harsha_blocked_when_lord_conjunct_kendra_lord() -> None:
    """Phase-1 audit fix: 6L in dusthana conjunct a kendra lord must
    NOT form the yoga (classical "alone in dusthana" rule per Mantreshwara
    Phaladeepika Ch. 7). For Aries asc, kendra lords are Mars (1L),
    Moon (4L), Venus (7L), Saturn (10L). Place Mercury (6L) in Pisces (12)
    with Saturn (10L) also in Pisces → yoga blocked."""
    chart = _chart_with_lord("Mercury", 12)
    # Move Saturn into Pisces (same sign as Mercury) — Saturn is 10L for Aries.
    chart["Saturn"] = _planet(12)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is None, (
        "Yoga must be blocked when 6L is conjunct a kendra lord "
        "(Saturn = 10L for Aries asc)"
    )


def test_harsha_blocked_when_lord_conjunct_trikona_lord() -> None:
    """6L conjunct a trikona lord (5L or 9L) also blocks the yoga.
    For Aries asc: 5L = Sun (Leo), 9L = Jupiter (Sagittarius). Place
    Mercury (6L) in Scorpio (8th from Aries) with Jupiter (9L) also
    in Scorpio → yoga blocked."""
    chart = _chart_with_lord("Mercury", 8)
    chart["Jupiter"] = _planet(8)  # Jupiter (9L) in same sign as Mercury
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is None, (
        "Yoga must be blocked when 6L is conjunct a trikona lord "
        "(Jupiter = 9L for Aries asc)"
    )


def test_harsha_fires_when_lord_alone_in_dusthana() -> None:
    """Baseline: 6L alone in dusthana (no benefic lord conjunction) →
    yoga fires normally. This is the canonical case used by all other
    detection tests above."""
    chart = _chart_with_lord("Mercury", 6)  # Mercury alone in Virgo (own 6th)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is not None
    assert result.name == "Vipareeta Harsha"


def test_harsha_fires_when_lord_conjunct_only_another_dusthana_lord() -> None:
    """When the 6L is conjunct ONLY another dusthana lord (NOT a kendra/
    trikona lord), the yoga still fires. For Aries asc: 8L = Mars, 12L = Jupiter.

    Place Mercury (6L) in Scorpio (8th house). Co-locate Mars (8L) there
    too. Since Mars is the 8L (dusthana lord) AND Mars is also the 1L
    (kendra lord for Aries) — wait that's a kendra lord. Bad example.

    For Aries asc, ONLY 8L and 12L are non-kendra non-trikona lords:
        8L = Mars (rules Aries=1L too, so kendra lord)
        12L = Jupiter (rules Sagittarius=9L too, so trikona lord)

    So for Aries asc EVERY other lord is also kendra/trikona — and the
    alone-gate is most stringent. Test on Taurus asc instead:
        Asc Taurus (2); 6L = Venus (Libra); 8L = Jupiter; 12L = Mars
        Jupiter is NOT a kendra/trikona lord for Taurus (rules 8 and 11 only)
        — kendra/trikona for Taurus: 1L Venus, 4L Sun, 5L Mercury, 7L Mars,
        9L Saturn, 10L Saturn. So Jupiter is NOT in that set.

    Place Venus (6L) in Aries (12th from Taurus) and Jupiter in Aries
    too: yoga should fire (Jupiter is 8L, a dusthana lord, not kendra/
    trikona)."""
    chart = _chart_with_lord("Venus", 1)  # Venus (6L for Taurus asc) in Aries
    chart["Jupiter"] = _planet(1)  # Jupiter (8L for Taurus, not kendra/trikona)
    result = detect_vipareeta_harsha(chart, _asc(2))
    assert result is not None, (
        "Yoga must still fire when 6L is conjunct only another dusthana lord; "
        "Jupiter is 8L for Taurus and NOT a kendra/trikona lord"
    )


# --------------------------------------------------------------------------- #
# Edge cases                                                                  #
# --------------------------------------------------------------------------- #

def test_harsha_missing_lord_returns_none() -> None:
    """Chart without the relevant lord planet entry → no yoga, no crash."""
    chart = _chart_with_lord("Mercury", 6)
    del chart["Mercury"]
    assert detect_vipareeta_harsha(chart, _asc(1)) is None


def test_harsha_invalid_ascendant_raises() -> None:
    chart = _chart_with_lord("Mercury", 6)
    with pytest.raises(ValueError):
        detect_vipareeta_harsha(chart, {"sign": 0})
    with pytest.raises(ValueError):
        detect_vipareeta_harsha(chart, {"sign": 13})


def test_harsha_returns_frozen_dataclass() -> None:
    """YogaInstance is immutable — attempting to mutate raises."""
    chart = _chart_with_lord("Mercury", 6)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is not None
    with pytest.raises(Exception):
        result.strength = 0.99  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# YogaInstance structure                                                      #
# --------------------------------------------------------------------------- #

def test_yoga_instance_fields() -> None:
    """All fields must be present and immutable types (tuples not lists)."""
    chart = _chart_with_lord("Mercury", 6)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is not None
    assert isinstance(result.name, str)
    assert isinstance(result.category, str)
    assert isinstance(result.participants, tuple)
    assert isinstance(result.houses_activated, tuple)
    assert isinstance(result.promise_axis, str)
    assert isinstance(result.lords_involved, tuple)
    assert isinstance(result.strength, float)


def test_yoga_instance_promise_axis() -> None:
    """Harsha's promise axis ties to career-via-adversity, used downstream
    when seeding V[event_class, yoga_slot] priors in the YSH-CM."""
    chart = _chart_with_lord("Mercury", 6)
    result = detect_vipareeta_harsha(chart, _asc(1))
    assert result is not None
    assert result.promise_axis == "career_via_adversity"
