"""Tier-2 doctrine: Marana Karaka Sthana (MKS) detection.

Doctrine source: BPHS Vol.I Ch.46 (locked via D-9 in
``docs/doctrine-decisions.md``).

A planet placed in its Marana Karaka Sthana ("house of death of the
significator") loses effectiveness for the significations it would
otherwise carry. Each planet has exactly one MKS house, except Ketu —
classical doctrine declares Ketu's MKS undefined, so this module emits
no Finding for Ketu regardless of placement (a deliberate sentinel,
not an omission).

Canonical MKS table (D-9)
=========================

+---------+-----------+
| Planet  | MKS House |
+=========+===========+
| Sun     | 12        |
| Moon    | 8         |
| Mars    | 7         |
| Mercury | 7         |
| Jupiter | 3         |
| Venus   | 6         |
| Saturn  | 1         |
| Rahu    | 9         |
| Ketu    | (None — N/A by classical doctrine)
+---------+-----------+

Public API
==========

    detect_mks(d1_chart, asc_sign) -> dict[str, Finding]

The returned dict carries one entry per planet that is in its MKS house.
Empty dict ⇒ no afflictions.

Whole-sign math
===============

House (1..12) of a planet from the ascendant is computed as
``((planet_sign - asc_sign) % 12) + 1``. This matches the project-wide
convention (see ``app/core/ephemeris_engine.whole_sign_house``).
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Canonical MKS table per D-9.
# Ketu is excluded — sentinel "not applicable" per BPHS doctrine.
MKS_HOUSE_BY_PLANET: Final[Mapping[str, int]] = {
    "Sun": 12,
    "Moon": 8,
    "Mars": 7,
    "Mercury": 7,
    "Jupiter": 3,
    "Venus": 6,
    "Saturn": 1,
    "Rahu": 9,
}


# Practitioner-tier confidence envelope (single deterministic lookup).
_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# 1-indexed sign names (index 0 unused).
_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    """Whole-sign house (1..12) of ``planet_sign`` relative to ``asc_sign``.

    Convention matches ``app/core/ephemeris_engine``: house = ((p - asc)
    mod 12) + 1, so a planet in the same sign as the ascendant is in
    house 1.
    """
    return ((planet_sign - asc_sign) % 12) + 1


def _ordinal(n: int) -> str:
    """English ordinal for 1..12 ('1st', '2nd', '3rd', '4th'...)."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _build_mks_finding(
    planet: str,
    mks_house: int,
    planet_sign: int,
    asc_sign: int,
) -> Finding:
    """Construct the Finding for one MKS detection."""
    sign_name = _SIGN_NAMES[planet_sign]
    verdict = (
        f"{planet} in {_ordinal(mks_house)} house (MKS — loss of "
        f"effectiveness)"
    )
    return Finding(
        id=f"practitioner.mks.{planet.lower()}",
        rule="marana_karaka_sthana",
        source_sequence=None,
        classification="affliction",
        direction="negative",
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"mks_house={mks_house}",
            f"planet_sign={sign_name}",
            f"asc_sign={_SIGN_NAMES[asc_sign]}",
            "doctrine=D-9 (BPHS Vol.I Ch.46 MKS table)",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_mks(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> dict[str, Finding]:
    """Detect Marana Karaka Sthana afflictions in a D1 chart.

    Args:
        d1_chart: Mapping ``{planet_name: {"sign": int (1..12), ...}}``.
            Must contain all 9 named planets (Sun, Moon, Mars, Mercury,
            Jupiter, Venus, Saturn, Rahu, Ketu). Only the ``sign`` field
            is consumed.
        asc_sign: 1..12 ascendant sign (1=Aries, 12=Pisces).

    Returns:
        Dict ``{planet: Finding}`` containing exactly the planets that
        are in their MKS house. Empty when no afflictions detected.
        Ketu is never present in the output (D-9 sentinel).

    Raises:
        ValueError: if ``asc_sign`` is outside 1..12 or any planet's
            ``sign`` field is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    findings: dict[str, Finding] = {}
    for planet, mks_house in MKS_HOUSE_BY_PLANET.items():
        record = d1_chart.get(planet)
        if record is None:
            # Caller forgot this planet — silently skip rather than crash;
            # callers running on the canonical d1 chart always have all
            # 9 planets, so this is a defensive branch.
            logger.debug("MKS: planet %s missing from d1_chart", planet)
            continue
        planet_sign = int(record["sign"])  # type: ignore[arg-type]
        if not 1 <= planet_sign <= 12:
            raise ValueError(
                f"{planet}.sign must be in 1..12, got {planet_sign}"
            )
        house = _whole_sign_house(planet_sign, asc_sign)
        if house == mks_house:
            findings[planet] = _build_mks_finding(
                planet, mks_house, planet_sign, asc_sign,
            )

    return findings


__all__ = ["detect_mks", "MKS_HOUSE_BY_PLANET"]
