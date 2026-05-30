"""Divisional reading: D60 Shashtiamsa chart — past-life karma (sanchita).

Doctrine source
===============

BPHS Vol.I Ch.6-7 (Shodashavarga). Parashara calls the **D60
Shashtiamsa the most important divisional chart**; it carries the
sanchita (accumulated past-life) karma signature. Construction
(handled by ``app.core.shodashavarga._shashtiamsa_d60``):

  - Each 30° rashi is split into 60 × 0.5° parts.
  - Highest division -> the most birth-time-sensitive chart. A
    1-minute rectification error can shift D60 placements; every
    Finding's evidence carries a ``birth_time_sensitivity=very_high``
    marker so consumers do not over-rely on D60 without rectified time.

Interpretation
==============

  - **D60 Lagna** is the single most important point in D60 — the
    past-life karmic anchor.
  - **D60 lagna lord** — its D60 placement.
  - **D60 Atmakaraka** — the soul karaka's D60 sign is the Jaimini
    school's primary past-life direction signal.

Direction policy
================

D60 placements are descriptive — ``direction="neutral"`` for all
Findings. Karaka / domain layers may refine later.

Public API
==========

    read_d60_shashtiamsa(d60_chart, asc_sign, atmakaraka) -> dict[str, Finding]

IDs follow ``d60.<rule_slug>``.
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


_VALID_KARAKA_PLANETS: Final[frozenset[str]] = frozenset(_NATURAL_PLANETS)


_SIGN_ELEMENT: Final[dict[int, str]] = {
    1: "fire",   2: "earth",  3: "air",   4: "water",
    5: "fire",   6: "earth",  7: "air",   8: "water",
    9: "fire",  10: "earth", 11: "air",  12: "water",
}


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=BPHS Vol.I Ch.6-7 D60 Shashtiamsa — past-life karma (sanchita); "
    "Parashara calls D60 the most important divisional chart"
)


# Required sensitivity marker. Tests assert this string verbatim.
_BIRTH_TIME_SENSITIVITY: Final[str] = (
    "birth_time_sensitivity=very_high (D60 chart — 0.5°/part; 1-minute "
    "rectification error shifts placements)"
)


def _validate_sign(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(f"{name} must be a 1-indexed sign in 1..12, got {value!r}")
    return value


def _validate_karaka_name(name: str) -> str:
    if name not in _VALID_KARAKA_PLANETS:
        raise ValueError(
            f"atmakaraka must be one of {sorted(_VALID_KARAKA_PLANETS)}, "
            f"got {name!r}"
        )
    return name


def _planet_d60_sign(
    d60_chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    entry = d60_chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return None
    return sign


def _dignity_descriptor(planet: str, sign: int) -> str:
    own = OWN_SIGNS.get(planet, set())
    if sign in own:
        return "in own sign — favourable past-life merit"
    return "in a non-own sign"


def _theme_for(sign: int) -> str:
    elem = _SIGN_ELEMENT.get(sign, "mixed")
    return {
        "fire":  "active / pioneering karmic strand",
        "earth": "grounded / material karmic strand",
        "air":   "intellectual / communicative karmic strand",
        "water": "emotional / devotional karmic strand",
        "mixed": "varied karmic strand",
    }[elem]


def _planet_finding(planet: str, d60_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[d60_sign]
    descriptor = _dignity_descriptor(planet, d60_sign)
    theme = _theme_for(d60_sign)
    verdict = (
        f"D60 {planet} in {sign_name} — past-life karma strand; {descriptor}"
    )[:140]
    return Finding(
        id=f"d60.planet_in_{planet.lower()}",
        rule="d60_shashtiamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"d60_sign={d60_sign}",
            f"d60_sign_name={sign_name}",
            f"dignity={descriptor}",
            f"theme={theme}",
            _BIRTH_TIME_SENSITIVITY,
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _lagna_finding(asc_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[asc_sign]
    theme = _theme_for(asc_sign)
    verdict = (
        f"D60 Lagna anchored on D1 ascendant ({sign_name}) — past-life karma anchor"
    )[:140]
    return Finding(
        id="d60.lagna",
        rule="d60_shashtiamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"d1_asc_sign={asc_sign}",
            f"d1_asc_sign_name={sign_name}",
            "frame=past-life karma (sanchita)",
            f"theme={theme}",
            _BIRTH_TIME_SENSITIVITY,
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _lagna_lord_finding(
    asc_sign: int, d60_chart: Mapping[str, Mapping[str, object]],
) -> Finding | None:
    lagna_lord = SIGN_RULERS[asc_sign]
    d60_sign = _planet_d60_sign(d60_chart, lagna_lord)
    if d60_sign is None:
        return None
    sign_name = _SIGN_NAMES[d60_sign]
    descriptor = _dignity_descriptor(lagna_lord, d60_sign)
    theme = _theme_for(d60_sign)
    verdict = (
        f"D60 lagna lord {lagna_lord} in {sign_name} — past-life karma direction; "
        f"{descriptor}"
    )[:140]
    return Finding(
        id="d60.lagna_lord",
        rule="d60_shashtiamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"lagna_lord={lagna_lord}",
            f"d60_sign={d60_sign}",
            f"d60_sign_name={sign_name}",
            f"dignity={descriptor}",
            f"theme={theme}",
            "frame=past-life karma",
            _BIRTH_TIME_SENSITIVITY,
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _atmakaraka_finding(
    atmakaraka: str, d60_chart: Mapping[str, Mapping[str, object]],
) -> Finding | None:
    d60_sign = _planet_d60_sign(d60_chart, atmakaraka)
    if d60_sign is None:
        return None
    sign_name = _SIGN_NAMES[d60_sign]
    descriptor = _dignity_descriptor(atmakaraka, d60_sign)
    theme = _theme_for(d60_sign)
    verdict = (
        f"D60 Atmakaraka {atmakaraka} in {sign_name} — soul/atma karma direction; "
        f"{descriptor}"
    )[:140]
    return Finding(
        id="d60.atmakaraka",
        rule="d60_shashtiamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"atmakaraka={atmakaraka}",
            f"d60_sign={d60_sign}",
            f"d60_sign_name={sign_name}",
            f"dignity={descriptor}",
            f"theme={theme}",
            "karaka=Atmakaraka (soul karaka — primary Jaimini past-life signal)",
            _BIRTH_TIME_SENSITIVITY,
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def read_d60_shashtiamsa(
    d60_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    atmakaraka: str,
) -> dict[str, Finding]:
    """Interpret a D60 Shashtiamsa chart for past-life karma themes.

    Every Finding's evidence carries an explicit
    ``birth_time_sensitivity=very_high`` marker (D60 = 0.5° per part).

    Args:
        d60_chart: D60 chart from
            ``app.core.shodashavarga.compute_divisional_charts``.
        asc_sign: 1-indexed natal D1 ascendant sign.
        atmakaraka: planet name (one of the seven natural significators)
            currently holding the Atmakaraka role (computed elsewhere via
            the Jaimini karaka algorithm).

    Returns:
        Dict keyed by Finding id. Always contains:
          - ``d60.lagna``                  (past-life karma anchor)
          - ``d60.lagna_lord``             (when present in D60)
          - ``d60.planet_in_<planet>``     for each present natural planet
          - ``d60.atmakaraka``             (when AK planet present in D60)
    """
    _validate_sign(asc_sign, "asc_sign")
    _validate_karaka_name(atmakaraka)

    findings: dict[str, Finding] = {}
    findings["d60.lagna"] = _lagna_finding(asc_sign)

    lord_finding = _lagna_lord_finding(asc_sign, d60_chart)
    if lord_finding is not None:
        findings[lord_finding.id] = lord_finding

    for planet in _NATURAL_PLANETS:
        d60_sign = _planet_d60_sign(d60_chart, planet)
        if d60_sign is None:
            continue
        finding = _planet_finding(planet, d60_sign)
        findings[finding.id] = finding

    ak = _atmakaraka_finding(atmakaraka, d60_chart)
    if ak is not None:
        findings[ak.id] = ak

    return findings


__all__ = ["read_d60_shashtiamsa"]
