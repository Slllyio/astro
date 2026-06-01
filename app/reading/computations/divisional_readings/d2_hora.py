"""Divisional reading: D2 Hora chart — wealth / source-of-income theme.

Doctrine source
===============

BPHS Vol.I Ch.6-7 (Shodashavarga). D2 is the **Hora** chart: each 30°
rashi is split into two 15° halves. Each half maps to one of TWO target
signs only:

  - Cancer (sign 4) -> ruled by the Moon -> "Moon's Hora"
  - Leo (sign 5)    -> ruled by the Sun  -> "Sun's Hora"

Odd-sign mapping: first 15° -> Sun's Hora (Leo), second 15° -> Moon's Hora.
Even-sign mapping: first 15° -> Moon's Hora (Cancer), second 15° -> Sun's
Hora. The Hora-construction itself lives in
``app.core.shodashavarga._hora_d2``; this module only *reads* the
finished D2 chart.

Interpretation
==============

  - **Moon's Hora (Cancer)**: wealth flows from emotional / nurturing /
    domestic / fluid sources — caregiving, family business, food,
    fluids/dairy, hospitality, real estate of homes.
  - **Sun's Hora (Leo)**: wealth flows from authoritative / public /
    self-made / structural sources — leadership, government service,
    direct entrepreneurship, gold/copper/light, public-facing trade.

Direction policy
================

Hora membership is descriptive, not "good" or "bad". The Finding's
``direction`` is ``"neutral"`` for ordinary planets. The lagna-lord
Hora carries the same direction (its interpretation is a theme, not a
benediction).

Public API
==========

    read_d2_hora(d2_chart, asc_sign) -> dict[str, Finding]

The returned dict is keyed by Finding id. IDs follow the grammar
``d2.<rule_slug>`` per spec Section 6 (a domain-style ID grammar is
used because the reading is per-varga, not per-Tier).
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


# The two Hora signs and their interpretive themes.
_MOON_HORA_SIGN: Final[int] = 4   # Cancer
_SUN_HORA_SIGN: Final[int] = 5    # Leo


_HORA_THEMES: Final[dict[int, str]] = {
    _MOON_HORA_SIGN: "emotional/nurturing sources",
    _SUN_HORA_SIGN:  "authoritative/public sources",
}

_HORA_RULER: Final[dict[int, str]] = {
    _MOON_HORA_SIGN: "Moon",
    _SUN_HORA_SIGN:  "Sun",
}


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_NATURAL_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


def _validate_sign(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1 <= value <= 12):
        raise ValueError(f"{name} must be a 1-indexed sign in 1..12, got {value!r}")
    return value


def _hora_label(sign: int) -> str:
    ruler = _HORA_RULER.get(sign)
    if ruler is None:
        return f"non-Hora sign ({_SIGN_NAMES[sign]})"
    sign_name = _SIGN_NAMES[sign]
    return f"{ruler}'s Hora ({sign_name})"


def _theme(sign: int) -> str:
    return _HORA_THEMES.get(sign, "indeterminate (non-Hora sign)")


def _planet_finding(planet: str, d2_sign: int) -> Finding:
    """Construct the per-planet D2 Hora Finding."""
    label = _hora_label(d2_sign)
    theme = _theme(d2_sign)
    verdict = f"D2: {planet} in {label} -> wealth via {theme}"[:140]
    return Finding(
        id=f"d2.planet_in_{planet.lower()}_hora",
        rule="d2_hora",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"d2_sign={d2_sign}",
            f"d2_sign_name={_SIGN_NAMES[d2_sign]}",
            f"hora_ruler={_HORA_RULER.get(d2_sign, 'none')}",
            f"theme={theme}",
            "doctrine=BPHS Vol.I Ch.6 D2 Hora — wealth source",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _lagna_lord_finding(
    lagna_lord: str, d2_sign: int,
) -> Finding:
    """Lagna-lord-in-Hora Finding (high-information signal for income)."""
    label = _hora_label(d2_sign)
    theme = _theme(d2_sign)
    verdict = (
        f"D2 lagna lord {lagna_lord} in {label} -> primary income theme: {theme}"
    )[:140]
    return Finding(
        id="d2.lagna_lord_in_hora",
        rule="d2_hora",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"lagna_lord={lagna_lord}",
            f"d2_sign={d2_sign}",
            f"d2_sign_name={_SIGN_NAMES[d2_sign]}",
            f"hora_ruler={_HORA_RULER.get(d2_sign, 'none')}",
            f"theme={theme}",
            "doctrine=BPHS Vol.I Ch.6 D2 Hora lagna-lord rule",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _planet_d2_sign(
    d2_chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    """Extract a planet's D2 sign; returns None if the planet is absent
    or malformed."""
    entry = d2_chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return None
    return sign


def read_d2_hora(
    d2_chart: Mapping[str, Mapping[str, object]], asc_sign: int,
) -> dict[str, Finding]:
    """Interpret a D2 Hora chart for wealth themes.

    Args:
        d2_chart: D2 chart from ``app.core.shodashavarga.compute_divisional_charts``,
            mapping ``planet_name -> position_dict`` with a 1-indexed
            ``sign`` field.
        asc_sign: 1-indexed Ascendant sign of the D1 chart (used to
            identify the lagna lord).

    Returns:
        Dict keyed by Finding id. Always contains a ``d2.lagna_lord_in_hora``
        Finding (when the lagna lord is present in the chart) and a
        ``d2.planet_in_<lowercased>_hora`` Finding for each member of the
        7-planet natural set found in the chart.
    """
    _validate_sign(asc_sign, "asc_sign")

    findings: dict[str, Finding] = {}

    # Per-planet Findings.
    for planet in _NATURAL_PLANETS:
        d2_sign = _planet_d2_sign(d2_chart, planet)
        if d2_sign is None:
            continue
        finding = _planet_finding(planet, d2_sign)
        findings[finding.id] = finding

    # Lagna-lord-in-Hora (high-signal).
    lagna_lord = SIGN_RULERS[asc_sign]
    ll_sign = _planet_d2_sign(d2_chart, lagna_lord)
    if ll_sign is not None:
        ll_finding = _lagna_lord_finding(lagna_lord, ll_sign)
        findings[ll_finding.id] = ll_finding

    return findings


__all__ = ["read_d2_hora"]
