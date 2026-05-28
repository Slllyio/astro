"""Divisional reading: D12 Dwadasamsa chart — parents / heritage / ancestry.

Doctrine source
===============

BPHS Vol.I Ch.6-7 (Shodashavarga). The D12 Dwadasamsa governs
**parents, ancestors, lineage, and inherited karma**. Construction
(handled by ``app.core.shodashavarga._dwadasamsa_d12``):

  - Each 30° rashi is split into 12 × 2.5° parts.
  - The parts cycle through the 12 signs starting from the same sign.

Interpretation
==============

  - The **D12 Sun** is the natural karaka of the father; its D12 sign
    flavours the father's nature / father-figure influence.
  - The **D12 Moon** plays the same role for the mother.
  - The **D12 4H lord** is the primary parental-house signifier (4H =
    home/parents in BPHS).
  - The **D12 Lagna** anchors the overall ancestral / heritage flavour.

Public API
==========

    read_d12_dwadasamsa(d12_chart, asc_sign) -> dict[str, Finding]

IDs follow ``d12.<rule_slug>``.
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.core.dignity import SIGN_RULERS
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


# Per-karaka colourings.
_PARENT_KARAKA: Final[dict[str, str]] = {
    "Sun":  "father",
    "Moon": "mother",
}


def _validate_sign(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(f"{name} must be a 1-indexed sign in 1..12, got {value!r}")
    return value


def _planet_d12_sign(
    d12_chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    entry = d12_chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return None
    return sign


def _theme_for_parent(planet: str, sign: int) -> str:
    """Theme phrasing for a parent karaka in a D12 sign."""
    parent = _PARENT_KARAKA.get(planet, "parent")
    elem = _SIGN_ELEMENT.get(sign, "mixed")
    descriptor = {
        "fire":  "active and protective",
        "earth": "grounding and resourceful",
        "air":   "communicative and idealistic",
        "water": "emotional and nurturing",
        "mixed": "varied",
    }[elem]
    return f"{descriptor} {parent}-figure influence"


def _theme_for_general(sign: int) -> str:
    elem = _SIGN_ELEMENT.get(sign, "mixed")
    return {
        "fire":  "lineage of action and ambition",
        "earth": "lineage of stability and stewardship",
        "air":   "lineage of intellect and communication",
        "water": "lineage of feeling and continuity",
        "mixed": "varied lineage",
    }[elem]


def _planet_finding(planet: str, d12_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[d12_sign]
    parent = _PARENT_KARAKA.get(planet)
    if parent is not None:
        theme = _theme_for_parent(planet, d12_sign)
        verdict = f"D12: {planet} in {sign_name} -> {theme}"[:140]
    else:
        theme = _theme_for_general(d12_sign)
        verdict = f"D12: {planet} in {sign_name} -> ancestral theme: {theme}"[:140]
    return Finding(
        id=f"d12.planet_in_{planet.lower()}",
        rule="d12_dwadasamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"d12_sign={d12_sign}",
            f"d12_sign_name={sign_name}",
            f"theme={theme}",
            f"is_parent_karaka={parent or 'no'}",
            "doctrine=BPHS Vol.I Ch.6 D12 Dwadasamsa — parents/heritage",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _lagna_finding(asc_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[asc_sign]
    theme = _theme_for_general(asc_sign)
    verdict = (
        f"D12 Lagna anchored on D1 ascendant ({sign_name}) -> {theme}"
    )[:140]
    return Finding(
        id="d12.lagna",
        rule="d12_dwadasamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"d1_asc_sign={asc_sign}",
            f"d1_asc_sign_name={sign_name}",
            f"theme={theme}",
            "doctrine=BPHS Vol.I Ch.6 D12 Lagna anchor",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _fourth_house_lord_finding(
    asc_sign: int, d12_chart: Mapping[str, Mapping[str, object]],
) -> Finding | None:
    fourth_sign = ((asc_sign - 1) + 3) % 12 + 1
    fourth_lord = SIGN_RULERS[fourth_sign]
    lord_d12_sign = _planet_d12_sign(d12_chart, fourth_lord)
    if lord_d12_sign is None:
        return None
    sign_name = _SIGN_NAMES[lord_d12_sign]
    theme = _theme_for_general(lord_d12_sign)
    verdict = (
        f"D12 4H lord {fourth_lord} in {sign_name} -> parents/home theme: {theme}"
    )[:140]
    return Finding(
        id="d12.fourth_house_lord",
        rule="d12_dwadasamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"fourth_house_sign={fourth_sign}",
            f"fourth_house_sign_name={_SIGN_NAMES[fourth_sign]}",
            f"fourth_lord={fourth_lord}",
            f"d12_sign={lord_d12_sign}",
            f"d12_sign_name={sign_name}",
            f"theme={theme}",
            "doctrine=BPHS Vol.I Ch.6 D12 4H-lord rule",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def read_d12_dwadasamsa(
    d12_chart: Mapping[str, Mapping[str, object]], asc_sign: int,
) -> dict[str, Finding]:
    """Interpret a D12 Dwadasamsa chart for parental / heritage themes.

    Args:
        d12_chart: D12 chart from ``app.core.shodashavarga.compute_divisional_charts``.
        asc_sign: 1-indexed natal D1 ascendant sign.

    Returns:
        Dict keyed by Finding id. Always contains:
          - ``d12.lagna``                  (heritage anchor)
          - ``d12.planet_in_sun``          (father karaka, if present)
          - ``d12.planet_in_moon``         (mother karaka, if present)
          - ``d12.planet_in_<planet>``     for each present natural planet
          - ``d12.fourth_house_lord``      when 4H lord is in the chart
    """
    _validate_sign(asc_sign, "asc_sign")
    findings: dict[str, Finding] = {}

    findings["d12.lagna"] = _lagna_finding(asc_sign)

    for planet in _NATURAL_PLANETS:
        d12_sign = _planet_d12_sign(d12_chart, planet)
        if d12_sign is None:
            continue
        finding = _planet_finding(planet, d12_sign)
        findings[finding.id] = finding

    lord_finding = _fourth_house_lord_finding(asc_sign, d12_chart)
    if lord_finding is not None:
        findings[lord_finding.id] = lord_finding

    return findings


__all__ = ["read_d12_dwadasamsa"]
