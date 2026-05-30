"""Divisional reading: D9 Navamsha chart — dharma / marriage / fruit-of-karma.

Doctrine source
===============

BPHS Vol.I Ch.6-7 (Shodashavarga). The D9 Navamsha is the **most
important secondary chart** in Vedic astrology; it governs dharma,
marriage potential, and the ultimate **phaladayaka** (fruit-bearing)
position of every planet. Construction (handled by
``app.core.shodashavarga._navamsha_d9``):

  - Each 30° rashi is split into 9 × 3.333° parts.
  - Odd signs start counting from the same sign.
  - Even signs start counting from the 7th sign from D1.

Interpretation
==============

  - **D9 Lagna** is the most important point of D9 — it sets the
    dharmic / marriage / phaladayaka frame for the whole life.
  - **D9 lagna lord** — its placement flavours how the dharmic frame is
    expressed.
  - **Vargottama planets** — any planet sitting in the same sign in BOTH
    D1 and D9 is *vargottama* (BPHS Vol.I Ch.8): its influence is
    unusually strong and consistent (good or bad according to its
    nature).
  - **D9 7H lord** — primary spouse signifier.
  - **D9 Venus** — spouse karaka (esp. male charts) / general
    relationship karaka.
  - **D9 Jupiter** — dharma karaka / husband karaka (esp. female charts).

Direction policy
================

D9 placements are descriptive — ``direction="neutral"`` for all
Findings. Marriage trigger / domain layers may apply finer judgment.

Public API
==========

    read_d9_navamsha(d1_chart, d9_chart, asc_sign) -> dict[str, Finding]

The reading takes BOTH the D1 and D9 charts because *vargottama*
detection requires comparing sign-position across the two vargas.

IDs follow ``d9.<rule_slug>``.
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


# Karaka tags for D9 reading. Jupiter and Venus carry marriage-specific
# karaka labels that route into the verdict phrasing.
_MARRIAGE_KARAKA: Final[dict[str, str]] = {
    "Venus":   "spouse karaka / relationship karaka",
    "Jupiter": "dharma karaka / husband karaka",
}


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=BPHS Vol.I Ch.6-7 D9 Navamsha — dharma/marriage/phaladayaka"
)


def _validate_sign(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(f"{name} must be a 1-indexed sign in 1..12, got {value!r}")
    return value


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


def _theme_for(sign: int) -> str:
    elem = _SIGN_ELEMENT.get(sign, "mixed")
    return {
        "fire":  "active and idealistic dharmic frame",
        "earth": "grounded and stable dharmic frame",
        "air":   "intellectual and communicative dharmic frame",
        "water": "emotional and devotional dharmic frame",
        "mixed": "varied dharmic frame",
    }[elem]


def _dignity_descriptor(planet: str, sign: int) -> str:
    own = OWN_SIGNS.get(planet, set())
    if sign in own:
        return "in own sign — strong phaladayaka"
    return "in a non-own sign"


def _planet_finding(
    planet: str, d9_sign: int, *, is_vargottama: bool,
) -> Finding:
    sign_name = _SIGN_NAMES[d9_sign]
    karaka_tag = _MARRIAGE_KARAKA.get(planet)
    descriptor = _dignity_descriptor(planet, d9_sign)
    vargottama_suffix = " — vargottama" if is_vargottama else ""
    if karaka_tag is not None:
        verdict = (
            f"D9 {planet} ({karaka_tag}) in {sign_name} — {descriptor}{vargottama_suffix}"
        )[:140]
    else:
        verdict = (
            f"D9 {planet} in {sign_name} — {descriptor}{vargottama_suffix}"
        )[:140]
    return Finding(
        id=f"d9.planet_in_{planet.lower()}",
        rule="d9_navamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"d9_sign={d9_sign}",
            f"d9_sign_name={sign_name}",
            f"marriage_karaka={karaka_tag or 'no'}",
            f"dignity={descriptor}",
            f"is_vargottama={'yes' if is_vargottama else 'no'}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _lagna_finding(asc_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[asc_sign]
    theme = _theme_for(asc_sign)
    verdict = (
        f"D9 Lagna anchored on D1 ascendant ({sign_name}) — dharma/marriage frame"
    )[:140]
    return Finding(
        id="d9.lagna",
        rule="d9_navamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"d1_asc_sign={asc_sign}",
            f"d1_asc_sign_name={sign_name}",
            "frame=dharma / marriage / phaladayaka",
            f"theme={theme}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _lagna_lord_finding(
    asc_sign: int, d9_chart: Mapping[str, Mapping[str, object]],
) -> Finding | None:
    """D9 placement of the D1 lagna lord."""
    lagna_lord = SIGN_RULERS[asc_sign]
    d9_sign = _planet_sign(d9_chart, lagna_lord)
    if d9_sign is None:
        return None
    sign_name = _SIGN_NAMES[d9_sign]
    descriptor = _dignity_descriptor(lagna_lord, d9_sign)
    verdict = (
        f"D9 lagna lord {lagna_lord} in {sign_name} — dharma expression; {descriptor}"
    )[:140]
    return Finding(
        id="d9.lagna_lord",
        rule="d9_navamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"lagna_lord={lagna_lord}",
            f"d9_sign={d9_sign}",
            f"d9_sign_name={sign_name}",
            f"dignity={descriptor}",
            "frame=dharma",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _seventh_house_lord_finding(
    asc_sign: int, d9_chart: Mapping[str, Mapping[str, object]],
) -> Finding | None:
    """D9 placement of the 7H lord (primary spouse signifier)."""
    seventh_sign = ((asc_sign - 1) + 6) % 12 + 1
    seventh_lord = SIGN_RULERS[seventh_sign]
    d9_sign = _planet_sign(d9_chart, seventh_lord)
    if d9_sign is None:
        return None
    sign_name = _SIGN_NAMES[d9_sign]
    descriptor = _dignity_descriptor(seventh_lord, d9_sign)
    verdict = (
        f"D9 7H lord {seventh_lord} in {sign_name} — spouse signifier; {descriptor}"
    )[:140]
    return Finding(
        id="d9.seventh_house_lord",
        rule="d9_navamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"seventh_house_sign={seventh_sign}",
            f"seventh_house_sign_name={_SIGN_NAMES[seventh_sign]}",
            f"seventh_lord={seventh_lord}",
            f"d9_sign={d9_sign}",
            f"d9_sign_name={sign_name}",
            f"dignity={descriptor}",
            "house=7 (spouse/marriage)",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def read_d9_navamsha(
    d1_chart: Mapping[str, Mapping[str, object]],
    d9_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> dict[str, Finding]:
    """Interpret a D9 Navamsha chart for dharma + marriage themes.

    Vargottama detection requires both charts — a planet is vargottama
    iff its sign is identical in D1 and D9.

    Args:
        d1_chart: D1 (rashi) chart, used ONLY for vargottama detection.
        d9_chart: D9 Navamsha chart from
            ``app.core.shodashavarga.compute_divisional_charts``.
        asc_sign: 1-indexed natal D1 ascendant sign.

    Returns:
        Dict keyed by Finding id. Always contains:
          - ``d9.lagna``                    (dharma/marriage anchor)
          - ``d9.lagna_lord``               (when present in D9)
          - ``d9.planet_in_<planet>``       for each present natural
                                            planet (Venus/Jupiter tagged
                                            as marriage karakas; any
                                            vargottama planet is
                                            flagged in evidence)
          - ``d9.seventh_house_lord``       (when 7L present in D9)
    """
    _validate_sign(asc_sign, "asc_sign")

    findings: dict[str, Finding] = {}
    findings["d9.lagna"] = _lagna_finding(asc_sign)

    lord_finding = _lagna_lord_finding(asc_sign, d9_chart)
    if lord_finding is not None:
        findings[lord_finding.id] = lord_finding

    for planet in _NATURAL_PLANETS:
        d9_sign = _planet_sign(d9_chart, planet)
        if d9_sign is None:
            continue
        d1_sign = _planet_sign(d1_chart, planet)
        is_vargottama = (d1_sign is not None) and (d1_sign == d9_sign)
        finding = _planet_finding(planet, d9_sign, is_vargottama=is_vargottama)
        findings[finding.id] = finding

    seventh = _seventh_house_lord_finding(asc_sign, d9_chart)
    if seventh is not None:
        findings[seventh.id] = seventh

    return findings


__all__ = ["read_d9_navamsha"]
