"""Practitioner extended yoga: Vipareeta Raja Yoga — positional variants.

Doctrine source: BPHS Vol.I — Vipareeta Raja Yoga (positional form).

Classical rule
==============

The 6th, 8th, and 12th houses are the **trika** (dusthana) houses, each
of which carries a misfortune signification (enemies/disease, sudden
change/death, loss/expenses). Their lords are classical malefics by
lordship.

The **positional Vipareeta variants** fire when a single trika lord sits
in one of the three trika houses (its own or another's). The home-house
misfortune is neutralised when its lord retreats into the dusthana orbit
— a reversal-yoga that grants unexpected gains.

Variants
========

- **Harsha Vipareeta**: 6L placed in 6, 8, or 12 from Lagna.
- **Sarala Vipareeta**: 8L placed in 6, 8, or 12 from Lagna.
- **Vimala Vipareeta**: 12L placed in 6, 8, or 12 from Lagna.

Coordination with ``trika_doctrine.py``
=======================================

``trika_doctrine.detect_trika_exchanges`` detects the EXCHANGE variant
(two trika lords in mutual sign-exchange, e.g. 6L↔8L). This module
detects the POSITIONAL variant (single trika lord in another dusthana,
no exchange required).

If a positional placement also satisfies an exchange condition (e.g. 6L
in 8H AND 8L in 6H), both modules fire. The positional finding here
carries a ``coexists_with=trika_doctrine.vipareeta_<pair>`` evidence
note so downstream synthesis can deduplicate the EXCHANGE half.

Public API
==========

    detect_vipareeta(d1_chart, asc_sign) -> list[Finding]

The Finding id pattern is
``practitioner.yogas_extended.vipareeta.<harsha|sarala|vimala>``.
classification="yoga", direction="positive".
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.core.dignity import SIGN_RULERS
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# The three trika (dusthana) houses.
_TRIKA_HOUSES: Final[tuple[int, ...]] = (6, 8, 12)

# House → positional-variant label.
_VARIANT_BY_OWNED_HOUSE: Final[dict[int, str]] = {
    6: "harsha",
    8: "sarala",
    12: "vimala",
}

# Long-form labels for verdict text.
_VARIANT_LABEL: Final[dict[str, str]] = {
    "harsha": "Harsha Vipareeta",
    "sarala": "Sarala Vipareeta",
    "vimala": "Vimala Vipareeta",
}


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=BPHS Vol.I Vipareeta Raja Yoga (positional — single trika "
    "lord in 6/8/12 from Lagna)"
)


def _house_lord(asc_sign: int, house: int) -> str:
    """Return the rashi-lord of the given whole-sign house from asc."""
    sign = ((asc_sign + house - 2) % 12) + 1
    return SIGN_RULERS[sign]


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    return ((planet_sign - asc_sign) % 12) + 1


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _coexisting_exchange_pair(
    owned_house: int,
    lord: str,
    occupied_house: int,
    asc_sign: int,
    planet_houses: dict[str, int],
) -> str | None:
    """If the positional placement implies a coexisting EXCHANGE
    (handled by trika_doctrine.py), return the canonical pair_id
    string used by that module; else None.

    The exchange fires when ``lord`` is in ``occupied_house`` AND the
    lord of ``occupied_house`` is in ``owned_house``, and the two
    houses are distinct trika houses (6/8, 6/12, or 8/12).
    """
    if occupied_house == owned_house:
        return None
    if occupied_house not in _TRIKA_HOUSES:
        return None
    other_lord = _house_lord(asc_sign, occupied_house)
    if other_lord == lord:
        return None
    if planet_houses.get(other_lord) != owned_house:
        return None
    # Deterministic pair id (alphabetical) to mirror trika_doctrine.py.
    a, b = sorted([lord.lower(), other_lord.lower()])
    return f"trika_doctrine.vipareeta_{a}_{b}"


def _build_finding(
    variant: str,
    lord: str,
    owned_house: int,
    occupied_house: int,
    asc_sign: int,
    coexists_with: str | None,
) -> Finding:
    label = _VARIANT_LABEL[variant]
    verdict = (
        f"{label} — {owned_house}L {lord} in {_ordinal(occupied_house)}H "
        f"(dusthana-into-dusthana reversal)"
    )[:140]
    evidence = [
        f"variant={variant}",
        f"trika_lord={lord}",
        f"owned_house={owned_house}",
        f"occupied_house={occupied_house}",
        f"asc_sign={asc_sign}",
    ]
    if coexists_with is not None:
        evidence.append(f"coexists_with={coexists_with}")
    evidence.append(_DOCTRINE_SENTINEL)
    return Finding(
        id=f"practitioner.yogas_extended.vipareeta.{variant}",
        rule="vipareeta_raja_yoga_positional",
        source_sequence=None,
        classification="yoga",
        direction="positive",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_vipareeta(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> list[Finding]:
    """Detect positional Vipareeta Raja Yoga variants.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int (1..12), ...}}.
        asc_sign: 1..12 ascendant sign.

    Returns:
        Findings list, one per detected positional variant. Empty when
        none of 6L/8L/12L sit in 6/8/12.

    Raises:
        ValueError: if asc_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    # Trika lords keyed by the trika house they own.
    trika_lords: dict[int, str] = {
        h: _house_lord(asc_sign, h) for h in _TRIKA_HOUSES
    }

    # Build planet → whole-sign house lookup.
    planet_houses: dict[str, int] = {}
    for planet, record in d1_chart.items():
        sign = record.get("sign")  # type: ignore[union-attr]
        if not isinstance(sign, int) or not 1 <= sign <= 12:
            continue
        planet_houses[planet] = _whole_sign_house(sign, asc_sign)

    findings: list[Finding] = []
    for owned_house, lord in trika_lords.items():
        occupied_house = planet_houses.get(lord)
        if occupied_house is None:
            continue
        if occupied_house not in _TRIKA_HOUSES:
            continue
        variant = _VARIANT_BY_OWNED_HOUSE[owned_house]
        coexists_with = _coexisting_exchange_pair(
            owned_house=owned_house,
            lord=lord,
            occupied_house=occupied_house,
            asc_sign=asc_sign,
            planet_houses=planet_houses,
        )
        findings.append(_build_finding(
            variant=variant,
            lord=lord,
            owned_house=owned_house,
            occupied_house=occupied_house,
            asc_sign=asc_sign,
            coexists_with=coexists_with,
        ))

    return findings


__all__ = ["detect_vipareeta"]
