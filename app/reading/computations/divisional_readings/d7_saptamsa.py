"""Divisional reading: D7 Saptamsa chart — children / progeny (santana).

Doctrine source
===============

BPHS Vol.I Ch.6-7 (Shodashavarga). The D7 Saptamsa governs **children
and progeny**. Construction (handled by
``app.core.shodashavarga._saptamsa_d7``):

  - Each 30° rashi is split into 7 × 4.286° parts.
  - Odd signs start counting from the same sign.
  - Even signs start counting from the 7th sign from D1.

Interpretation
==============

  - **D7 Lagna** anchors the overall children frame (the soul's
    relationship to progeny).
  - **D7 5H lord** is the primary signifier (5H = children house).
  - **D7 Jupiter** is the natural Putra-karaka (progeny karaka).
  - Each natural planet's D7 sign tells where its children-related
    energy is directed.

Direction policy
================

D7 placements are descriptive themes — ``direction="neutral"`` for all
Findings. Tier-3 enrichment / domain layers may up- or down-grade later.

Public API
==========

    read_d7_saptamsa(d7_chart, asc_sign) -> dict[str, Finding]

IDs follow ``d7.<rule_slug>``.
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.core.dignity import OWN_SIGNS, SIGN_RULERS
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_NATURAL_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


_SIGN_ELEMENT: Final[dict[int, str]] = {
    1: "fire",   2: "earth",  3: "air",   4: "water",
    5: "fire",   6: "earth",  7: "air",   8: "water",
    9: "fire",  10: "earth", 11: "air",  12: "water",
}


# Putra-karaka tag: Jupiter is the natural progeny karaka in BPHS.
_PROGENY_KARAKA: Final[dict[str, str]] = {
    "Jupiter": "putra-karaka / progeny karaka",
}


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=BPHS Vol.I Ch.6 D7 Saptamsa — children/progeny"
)


def _validate_sign(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(f"{name} must be a 1-indexed sign in 1..12, got {value!r}")
    return value


def _planet_d7_sign(
    d7_chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    entry = d7_chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return None
    return sign


def _theme_for(sign: int) -> str:
    elem = _SIGN_ELEMENT.get(sign, "mixed")
    return {
        "fire":  "active and assertive children indication",
        "earth": "stable and resourceful children indication",
        "air":   "communicative and bright children indication",
        "water": "emotional and nurturing children indication",
        "mixed": "varied children indication",
    }[elem]


def _dignity_descriptor(planet: str, sign: int) -> str:
    own = OWN_SIGNS.get(planet, set())
    if sign in own:
        return "in own sign — strong children indication"
    return "in a non-own sign"


def _planet_finding(planet: str, d7_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[d7_sign]
    karaka_tag = _PROGENY_KARAKA.get(planet)
    descriptor = _dignity_descriptor(planet, d7_sign)
    theme = _theme_for(d7_sign)
    if karaka_tag is not None:
        verdict = (
            f"D7 {planet} ({karaka_tag}) in {sign_name} — {descriptor}"
        )[:140]
    else:
        verdict = f"D7 {planet} in {sign_name} — children theme: {theme}"[:140]
    return Finding(
        id=f"d7.planet_in_{planet.lower()}",
        rule="d7_saptamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"d7_sign={d7_sign}",
            f"d7_sign_name={sign_name}",
            f"progeny_karaka={karaka_tag or 'no'}",
            f"dignity={descriptor}",
            f"theme={theme}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _lagna_finding(asc_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[asc_sign]
    theme = _theme_for(asc_sign)
    verdict = (
        f"D7 Lagna anchored on D1 ascendant ({sign_name}) — children/progeny frame"
    )[:140]
    return Finding(
        id="d7.lagna",
        rule="d7_saptamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"d1_asc_sign={asc_sign}",
            f"d1_asc_sign_name={sign_name}",
            "frame=children / progeny",
            f"theme={theme}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _fifth_house_lord_finding(
    asc_sign: int, d7_chart: Mapping[str, Mapping[str, object]],
) -> Finding | None:
    """D7 placement of the 5H lord (children house — primary signifier)."""
    fifth_sign = ((asc_sign - 1) + 4) % 12 + 1
    fifth_lord = SIGN_RULERS[fifth_sign]
    lord_d7_sign = _planet_d7_sign(d7_chart, fifth_lord)
    if lord_d7_sign is None:
        return None
    sign_name = _SIGN_NAMES[lord_d7_sign]
    descriptor = _dignity_descriptor(fifth_lord, lord_d7_sign)
    theme = _theme_for(lord_d7_sign)
    verdict = (
        f"D7 5H lord {fifth_lord} in {sign_name} — children-house signifier; {descriptor}"
    )[:140]
    return Finding(
        id="d7.fifth_house_lord",
        rule="d7_saptamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"fifth_house_sign={fifth_sign}",
            f"fifth_house_sign_name={_SIGN_NAMES[fifth_sign]}",
            f"fifth_lord={fifth_lord}",
            f"d7_sign={lord_d7_sign}",
            f"d7_sign_name={sign_name}",
            f"theme={theme}",
            f"dignity={descriptor}",
            "house=5 (children/progeny)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def read_d7_saptamsa(
    d7_chart: Mapping[str, Mapping[str, object]], asc_sign: int,
) -> dict[str, Finding]:
    """Interpret a D7 Saptamsa chart for children / progeny themes.

    Args:
        d7_chart: D7 chart from
            ``app.core.shodashavarga.compute_divisional_charts``, mapping
            ``planet_name -> position_dict`` with a 1-indexed ``sign`` field.
        asc_sign: 1-indexed natal D1 ascendant sign (used to derive the
            5H lord).

    Returns:
        Dict keyed by Finding id. Always contains:
          - ``d7.lagna``                  (children frame anchor)
          - ``d7.planet_in_<planet>``     for each present natural planet
                                          (Jupiter is tagged as
                                          putra-karaka)
          - ``d7.fifth_house_lord``       when 5H lord is in D7
    """
    _validate_sign(asc_sign, "asc_sign")

    findings: dict[str, Finding] = {}
    findings["d7.lagna"] = _lagna_finding(asc_sign)

    for planet in _NATURAL_PLANETS:
        d7_sign = _planet_d7_sign(d7_chart, planet)
        if d7_sign is None:
            continue
        finding = _planet_finding(planet, d7_sign)
        findings[finding.id] = finding

    fifth = _fifth_house_lord_finding(asc_sign, d7_chart)
    if fifth is not None:
        findings[fifth.id] = fifth

    return findings


__all__ = ["read_d7_saptamsa"]
