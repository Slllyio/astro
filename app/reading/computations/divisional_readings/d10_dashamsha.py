"""Divisional reading: D10 Dashamsha chart — career / karma execution.

Doctrine source
===============

BPHS Vol.I Ch.6-7 (Shodashavarga). The D10 Dashamsha governs **career,
karma in the world, profession, and public standing**. Construction
(handled by ``app.core.shodashavarga._dashamsha_d10``):

  - Each 30° rashi is split into 10 × 3° parts.

Interpretation
==============

This reading is the heaviest of the divisional readings because it
incorporates the **5-pillar career synthesis** absorbed from the
spec's ``career_d10_pillars`` rule. The five pillars represent the
classical-modern compromise on how to read career out of a chart:

  1. **Pillar 1 — D1 10L placement** (sign-element of the 10H lord
     in D1; the natal foundation).
  2. **Pillar 2 — D10 lagna lord** (D10's own lagna lord's D10
     placement; how the D10 lagna expresses).
  3. **Pillar 3 — Amatya Karaka in D10** (Jaimini's professional
     karaka; spec absorbs this).
  4. **Pillar 4 — Strongest career karaka by D10 own-sign** (Sun /
     Mercury / Mars: government / consulting / action karakas).
  5. **Pillar 5 — Saturn in D10** (the service / discipline karaka).

A **concordance** is computed as the count of pillars whose D10-side
sign falls into the same element (fire / earth / air / water). High
concordance (≥ 3 / 5) flags a strong unified career theme.

Direction policy
================

All findings are ``classification="primitive"`` / ``direction="neutral"``
— career domain layers may refine later.

Public API
==========

    read_d10_dashamsha(d1_chart, d10_chart, asc_sign, amatya_karaka) -> dict[str, Finding]

IDs follow ``d10.<rule_slug>``.
"""
from __future__ import annotations

import logging
from collections import Counter
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


# Career karakas: government (Sun) / consulting (Mercury) / action (Mars).
_CAREER_KARAKAS: Final[tuple[str, ...]] = ("Sun", "Mercury", "Mars")


_KARAKA_THEME: Final[dict[str, str]] = {
    "Sun":     "authority / government / leadership",
    "Mercury": "consulting / commerce / communication",
    "Mars":    "action / engineering / military",
    "Saturn":  "service / discipline / endurance",
}


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=BPHS Vol.I Ch.6-7 D10 Dashamsha — career/karma execution"
)


def _validate_sign(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(f"{name} must be a 1-indexed sign in 1..12, got {value!r}")
    return value


def _validate_karaka_name(name: str) -> str:
    if name not in _VALID_KARAKA_PLANETS:
        raise ValueError(
            f"amatya_karaka must be one of {sorted(_VALID_KARAKA_PLANETS)}, "
            f"got {name!r}"
        )
    return name


def _planet_sign(
    chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    entry = chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return None
    return sign


def _dignity_descriptor(planet: str, sign: int) -> str:
    own = OWN_SIGNS.get(planet, set())
    if sign in own:
        return "in own sign — strong career signifier"
    return "in a non-own sign"


def _strongest_career_karaka(
    d10_chart: Mapping[str, Mapping[str, object]],
) -> tuple[str | None, int | None]:
    """Return (planet, d10_sign) of the strongest career karaka among
    Sun / Mercury / Mars by D10 own-sign placement. Falls back to the
    first karaka with a valid D10 placement when none is in own-sign."""
    in_own: list[tuple[str, int]] = []
    any_placed: list[tuple[str, int]] = []
    for k in _CAREER_KARAKAS:
        s = _planet_sign(d10_chart, k)
        if s is None:
            continue
        any_placed.append((k, s))
        if s in OWN_SIGNS.get(k, set()):
            in_own.append((k, s))
    if in_own:
        return in_own[0]
    if any_placed:
        return any_placed[0]
    return None, None


def _lagna_finding(asc_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[asc_sign]
    verdict = (
        f"D10 Lagna anchored on D1 ascendant ({sign_name}) — career/karma frame"
    )[:140]
    return Finding(
        id="d10.lagna",
        rule="d10_dashamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"d1_asc_sign={asc_sign}",
            f"d1_asc_sign_name={sign_name}",
            "frame=career / karma execution",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _lagna_lord_finding(
    asc_sign: int, d10_chart: Mapping[str, Mapping[str, object]],
) -> Finding | None:
    lagna_lord = SIGN_RULERS[asc_sign]
    d10_sign = _planet_sign(d10_chart, lagna_lord)
    if d10_sign is None:
        return None
    sign_name = _SIGN_NAMES[d10_sign]
    descriptor = _dignity_descriptor(lagna_lord, d10_sign)
    verdict = (
        f"D10 lagna lord {lagna_lord} in {sign_name} — career signifier; {descriptor}"
    )[:140]
    return Finding(
        id="d10.lagna_lord",
        rule="d10_dashamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"lagna_lord={lagna_lord}",
            f"d10_sign={d10_sign}",
            f"d10_sign_name={sign_name}",
            f"dignity={descriptor}",
            "frame=career",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _tenth_house_lord_finding(
    asc_sign: int, d10_chart: Mapping[str, Mapping[str, object]],
) -> Finding | None:
    tenth_sign = ((asc_sign - 1) + 9) % 12 + 1
    tenth_lord = SIGN_RULERS[tenth_sign]
    d10_sign = _planet_sign(d10_chart, tenth_lord)
    if d10_sign is None:
        return None
    sign_name = _SIGN_NAMES[d10_sign]
    descriptor = _dignity_descriptor(tenth_lord, d10_sign)
    verdict = (
        f"D10 10H lord {tenth_lord} in {sign_name} — career-house signifier; {descriptor}"
    )[:140]
    return Finding(
        id="d10.tenth_house_lord",
        rule="d10_dashamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"tenth_house_sign={tenth_sign}",
            f"tenth_house_sign_name={_SIGN_NAMES[tenth_sign]}",
            f"tenth_lord={tenth_lord}",
            f"d10_sign={d10_sign}",
            f"d10_sign_name={sign_name}",
            f"dignity={descriptor}",
            "house=10 (career)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _amatya_karaka_finding(
    amatya_karaka: str, d10_chart: Mapping[str, Mapping[str, object]],
) -> Finding | None:
    d10_sign = _planet_sign(d10_chart, amatya_karaka)
    if d10_sign is None:
        return None
    sign_name = _SIGN_NAMES[d10_sign]
    descriptor = _dignity_descriptor(amatya_karaka, d10_sign)
    verdict = (
        f"D10 Amatya Karaka {amatya_karaka} in {sign_name} — professional karaka; {descriptor}"
    )[:140]
    return Finding(
        id="d10.amatya_karaka",
        rule="d10_dashamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"amatya_karaka={amatya_karaka}",
            f"d10_sign={d10_sign}",
            f"d10_sign_name={sign_name}",
            f"dignity={descriptor}",
            "karaka=Amatya (Jaimini professional)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _pillar_signs(
    d1_chart: Mapping[str, Mapping[str, object]],
    d10_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    amatya_karaka: str,
) -> list[tuple[str, str, int | None]]:
    """Compute the 5 pillars. Each entry is (pillar_label, planet,
    sign_value_or_None). Pillar 1's sign is read from D1; the other
    four pillars are read from D10."""
    # Pillar 1 — D1 10L placement (from D1 chart).
    tenth_sign = ((asc_sign - 1) + 9) % 12 + 1
    tenth_lord = SIGN_RULERS[tenth_sign]
    p1_sign = _planet_sign(d1_chart, tenth_lord)

    # Pillar 2 — D10 lagna lord (the lagna of D10 is conventionally
    # anchored on the D1 ascendant; the lagna *lord* is the D1 ASC
    # sign's ruler, whose D10 placement we read).
    lagna_lord = SIGN_RULERS[asc_sign]
    p2_sign = _planet_sign(d10_chart, lagna_lord)

    # Pillar 3 — Amatya Karaka in D10.
    p3_sign = _planet_sign(d10_chart, amatya_karaka)

    # Pillar 4 — Strongest career karaka (Sun/Mercury/Mars) in D10.
    p4_planet, p4_sign = _strongest_career_karaka(d10_chart)

    # Pillar 5 — Saturn in D10 (service / discipline).
    p5_sign = _planet_sign(d10_chart, "Saturn")

    return [
        ("pillar_1", f"D1 10L={tenth_lord}", p1_sign),
        ("pillar_2", f"D10 lagna lord={lagna_lord}", p2_sign),
        ("pillar_3", f"Amatya Karaka={amatya_karaka}", p3_sign),
        ("pillar_4", f"strongest career karaka={p4_planet or 'none'}", p4_sign),
        ("pillar_5", "Saturn (service karaka)", p5_sign),
    ]


def _five_pillar_finding(
    d1_chart: Mapping[str, Mapping[str, object]],
    d10_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    amatya_karaka: str,
) -> Finding:
    pillars = _pillar_signs(d1_chart, d10_chart, asc_sign, amatya_karaka)
    # Elements present.
    elements: list[str] = []
    for _label, _desc, sign in pillars:
        if sign is None:
            continue
        elem = _SIGN_ELEMENT.get(sign)
        if elem is not None:
            elements.append(elem)
    if elements:
        counter = Counter(elements)
        top_elem, top_count = counter.most_common(1)[0]
        # Concordance is N out of 5 pillars (not out of placed-pillars)
        # — pillars not in chart count as 0 concordance contributors.
        concordance = top_count
        if top_count >= 2:
            theme = f"{top_elem}-element career theme"
        else:
            theme = "mixed / no dominant element"
    else:
        top_elem = "none"
        concordance = 0
        theme = "no pillars resolved"

    verdict = (
        f"D10 career: {concordance}/5 pillars concord on {theme}"
    )[:140]

    evidence: list[str] = []
    for label, desc, sign in pillars:
        sign_name = _SIGN_NAMES[sign] if sign is not None else "absent"
        elem = _SIGN_ELEMENT.get(sign, "none") if sign is not None else "none"
        evidence.append(f"{label}: {desc} -> sign={sign_name} ({elem})")
    evidence.extend([
        f"top_element={top_elem}",
        f"concordance={concordance}/5",
        f"theme={theme}",
        "spec_rule=career_d10_pillars (absorbed into D10 reading)",
        _DOCTRINE_SENTINEL,
    ])

    return Finding(
        id="d10.career_5_pillars",
        rule="d10_dashamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _planet_finding(planet: str, d10_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[d10_sign]
    karaka_theme = _KARAKA_THEME.get(planet)
    descriptor = _dignity_descriptor(planet, d10_sign)
    if karaka_theme is not None:
        verdict = (
            f"D10 {planet} ({karaka_theme}) in {sign_name} — {descriptor}"
        )[:140]
    else:
        verdict = f"D10 {planet} in {sign_name} — {descriptor}"[:140]
    return Finding(
        id=f"d10.planet_in_{planet.lower()}",
        rule="d10_dashamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"d10_sign={d10_sign}",
            f"d10_sign_name={sign_name}",
            f"career_karaka_theme={karaka_theme or 'no'}",
            f"dignity={descriptor}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def read_d10_dashamsha(
    d1_chart: Mapping[str, Mapping[str, object]],
    d10_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    amatya_karaka: str,
) -> dict[str, Finding]:
    """Interpret a D10 Dashamsha chart for career / karma themes.

    Takes BOTH D1 and D10 because the 5-pillar synthesis (Pillar 1) reads
    the D1 placement of the 10L while the rest read D10 placements.

    Args:
        d1_chart: D1 (rashi) chart.
        d10_chart: D10 Dashamsha chart from
            ``app.core.shodashavarga.compute_divisional_charts``.
        asc_sign: 1-indexed natal D1 ascendant sign.
        amatya_karaka: planet name (one of the seven natural
            significators) currently holding the Amatya-Karaka role
            (computed elsewhere via the Jaimini karaka algorithm).

    Returns:
        Dict keyed by Finding id. Always contains:
          - ``d10.lagna``                  (career frame anchor)
          - ``d10.lagna_lord``             (when present in D10)
          - ``d10.planet_in_<planet>``     for each present natural planet
          - ``d10.tenth_house_lord``       (when 10L present in D10)
          - ``d10.amatya_karaka``          (when Amatya planet present in D10)
          - ``d10.career_5_pillars``       (5-pillar synthesis, always emits)
    """
    _validate_sign(asc_sign, "asc_sign")
    _validate_karaka_name(amatya_karaka)

    findings: dict[str, Finding] = {}
    findings["d10.lagna"] = _lagna_finding(asc_sign)

    lord_finding = _lagna_lord_finding(asc_sign, d10_chart)
    if lord_finding is not None:
        findings[lord_finding.id] = lord_finding

    for planet in _NATURAL_PLANETS:
        d10_sign = _planet_sign(d10_chart, planet)
        if d10_sign is None:
            continue
        finding = _planet_finding(planet, d10_sign)
        findings[finding.id] = finding

    tenth = _tenth_house_lord_finding(asc_sign, d10_chart)
    if tenth is not None:
        findings[tenth.id] = tenth

    amatya = _amatya_karaka_finding(amatya_karaka, d10_chart)
    if amatya is not None:
        findings[amatya.id] = amatya

    pillars = _five_pillar_finding(d1_chart, d10_chart, asc_sign, amatya_karaka)
    findings[pillars.id] = pillars

    return findings


__all__ = ["read_d10_dashamsha"]
