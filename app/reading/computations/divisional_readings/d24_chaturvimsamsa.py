"""Divisional reading: D24 Chaturvimsamsa chart — education / Vidya.

Doctrine lock - D-16 (``docs/doctrine-decisions.md``)
=====================================================

**Education routes through D24.** Per BPHS Vol.I Ch.6 v.21 (Vidya /
education chart per Chaturvimsamsa), the D24 is the canonical
divisional for formal learning, scholarship, and academic achievement.
``app/reading/domains/education.py`` is the *sole consumer* of this
reading; it does NOT consult D9 (Navamsa — dharma/marriage) or D4
(Chaturthamsa — fixed assets/property) for education judgments.

This decision is the only one of the 16 lockfile decisions that
**corrects** a common modern variant rather than choosing among
legitimate classical alternatives.

D24 construction
================

Each 30° rashi splits into 24 × 1.25° parts. Odd signs start counting
from Leo (sign 5); even signs start counting from Cancer (sign 4). The
construction itself is in ``app.core.shodashavarga._chaturvimsamsa_d24``;
this module *reads* the finished D24 chart.

Reading targets
===============

  - **D24 Lagna** — overall educational frame.
  - **D24 4H lord** — formal-education foundation (4H = primary
    schooling / institutional learning).
  - **D24 5H lord** — intellectual capacity / higher-mind (5H =
    purva-punya, creative intelligence).
  - **D24 Jupiter** — natural karaka of wisdom (Vidya).
  - **D24 Mercury** — natural karaka of academic intellect.
  - **D24 <planet>** — per-planet placement, descriptive.

Direction policy
================

All Findings are ``classification="primitive"`` / ``direction="neutral"``
(domain-level interpretation lives in ``domains/education.py``).

Public API
==========

    read_d24_chaturvimsamsa(d24_chart, asc_sign) -> dict[str, Finding]

★NEW: this module is freshly added per the post-review revision; a
future doctrine-reviewer audit should pay extra attention.
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


# Natural karaka tags for education themes.
_EDUCATION_KARAKA: Final[dict[str, str]] = {
    "Jupiter": "wisdom / Vidya",
    "Mercury": "academic intellect / sastric mastery",
}


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=D-16 (D24 Chaturvimsamsa is the Vidya/education chart "
    "per BPHS Vol.I Ch.6 v.21)"
)


def _validate_sign(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(f"{name} must be a 1-indexed sign in 1..12, got {value!r}")
    return value


def _planet_d24_sign(
    d24_chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    entry = d24_chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return None
    return sign


def _dignity_descriptor(planet: str, sign: int) -> str:
    """Coarse dignity colouring for the verdict (own sign vs other)."""
    own = OWN_SIGNS.get(planet, set())
    if sign in own:
        return "in own sign — strong educational foundation"
    return "in a non-own sign"


def _planet_finding(planet: str, d24_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[d24_sign]
    karaka_tag = _EDUCATION_KARAKA.get(planet)
    descriptor = _dignity_descriptor(planet, d24_sign)
    if karaka_tag is not None:
        verdict = (
            f"D24 {planet} ({karaka_tag}) in {sign_name} — {descriptor}"
        )[:140]
    else:
        verdict = f"D24 {planet} in {sign_name} — {descriptor}"[:140]
    return Finding(
        id=f"d24.planet_in_{planet.lower()}",
        rule="d24_chaturvimsamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"d24_sign={d24_sign}",
            f"d24_sign_name={sign_name}",
            f"education_karaka={karaka_tag or 'no'}",
            f"dignity={descriptor}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _lagna_finding(asc_sign: int) -> Finding:
    sign_name = _SIGN_NAMES[asc_sign]
    verdict = (
        f"D24 Lagna anchored on D1 ascendant ({sign_name}) — education / Vidya frame"
    )[:140]
    return Finding(
        id="d24.lagna",
        rule="d24_chaturvimsamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"d1_asc_sign={asc_sign}",
            f"d1_asc_sign_name={sign_name}",
            "frame=education / Vidya",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _house_lord_finding(
    *,
    house_index: int,           # 4 or 5
    asc_sign: int,
    d24_chart: Mapping[str, Mapping[str, object]],
    id_suffix: str,
    theme_label: str,           # short phrase used in verdict
) -> Finding | None:
    house_sign = ((asc_sign - 1) + (house_index - 1)) % 12 + 1
    lord = SIGN_RULERS[house_sign]
    lord_d24_sign = _planet_d24_sign(d24_chart, lord)
    if lord_d24_sign is None:
        return None
    sign_name = _SIGN_NAMES[lord_d24_sign]
    descriptor = _dignity_descriptor(lord, lord_d24_sign)
    verdict = (
        f"D24 {house_index}H lord {lord} in {sign_name} — {theme_label}; {descriptor}"
    )[:140]
    return Finding(
        id=f"d24.{id_suffix}",
        rule="d24_chaturvimsamsa",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"house={house_index}",
            f"house_sign={house_sign}",
            f"house_sign_name={_SIGN_NAMES[house_sign]}",
            f"house_lord={lord}",
            f"d24_sign={lord_d24_sign}",
            f"d24_sign_name={sign_name}",
            f"theme={theme_label}",
            f"dignity={descriptor}",
            _DOCTRINE_SENTINEL,
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def read_d24_chaturvimsamsa(
    d24_chart: Mapping[str, Mapping[str, object]], asc_sign: int,
) -> dict[str, Finding]:
    """Interpret a D24 Chaturvimsamsa chart for education / Vidya themes.

    Per the D-16 doctrine lock, this is the canonical education
    divisional reading; ``domains/education.py`` is the sole expected
    consumer.

    Args:
        d24_chart: D24 chart from
            ``app.core.shodashavarga.compute_divisional_charts``.
        asc_sign: 1-indexed natal D1 ascendant sign.

    Returns:
        Dict keyed by Finding id. Always contains:
          - ``d24.lagna``                  (education frame anchor)
          - ``d24.planet_in_<planet>``     for each present natural planet
          - ``d24.fourth_house_lord``      when 4H lord present in D24
          - ``d24.fifth_house_lord``       when 5H lord present in D24
    """
    _validate_sign(asc_sign, "asc_sign")

    findings: dict[str, Finding] = {}
    findings["d24.lagna"] = _lagna_finding(asc_sign)

    for planet in _NATURAL_PLANETS:
        d24_sign = _planet_d24_sign(d24_chart, planet)
        if d24_sign is None:
            continue
        finding = _planet_finding(planet, d24_sign)
        findings[finding.id] = finding

    fourth = _house_lord_finding(
        house_index=4, asc_sign=asc_sign, d24_chart=d24_chart,
        id_suffix="fourth_house_lord",
        theme_label="formal-education foundation",
    )
    if fourth is not None:
        findings[fourth.id] = fourth

    fifth = _house_lord_finding(
        house_index=5, asc_sign=asc_sign, d24_chart=d24_chart,
        id_suffix="fifth_house_lord",
        theme_label="intellectual capacity / purva-punya",
    )
    if fifth is not None:
        findings[fifth.id] = fifth

    return findings


__all__ = ["read_d24_chaturvimsamsa"]
