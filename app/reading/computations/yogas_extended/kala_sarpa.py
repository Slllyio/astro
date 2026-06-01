"""Practitioner extended yoga: Kala Sarpa Yoga (D-12 strict definition).

Doctrine source: D-12 lockfile — strict 180° / Rahu-leading definition.
Post-Parashari yoga; consensus per K.N. Rao and PVR Narasimha Rao.

Classical rule (D-12 STRICT)
============================

The seven non-nodal planets (Sun, Moon, Mars, Mercury, Jupiter, Venus,
Saturn) fall entirely within ONE of the two 180° hemispheres bounded by
the Rahu-Ketu axis.

- **Kala Sarpa Yoga (KSY)**: all 7 in the **Rahu-leading** hemisphere
  (moving from Rahu forward 180° in zodiacal direction, all planets are
  inside that arc — i.e. between Rahu and Ketu with Rahu first).
  Classification: negative (karmic struggle / serpent of time).

- **Kala Amrita Yoga**: all 7 in the **Ketu-leading** hemisphere (moving
  from Ketu forward 180°, all planets are inside that arc — i.e. Rahu
  trails). Classification: positive (the more benign mirror).

**Strict only**: per D-12, partial / loose / near-Kala-Sarpa variants
(one stray planet, 5° tolerance, bidirectional) are NOT detected here.
They live in the Tier-3 ``dispute_surfacing`` layer.

At most one Finding is emitted per chart (the two strict variants are
mutually exclusive).

Algorithm
=========

Given Rahu's absolute longitude ``rahu_lon`` (0..360):

1. For each of the 7 non-nodal planets P with longitude ``p_lon``, compute
   the forward arc-distance from Rahu:
        forward_arc = (p_lon - rahu_lon) % 360.0
   This places the planet at 0..360 along the zodiacal direction.
2. **KSY check**: every planet has ``0 < forward_arc < 180``.
3. **Amrita check**: every planet has ``180 < forward_arc < 360``.

A planet exactly conjunct Rahu (``forward_arc == 0``) or Ketu
(``forward_arc == 180``) breaks both strict definitions and yields no
Finding.

Public API
==========

    detect_kala_sarpa(d1_chart, asc_sign) -> list[Finding]

ID pattern: ``practitioner.yogas_extended.kala_sarpa.<ksy|amrita>``.
classification="yoga"; direction="negative" for ksy, "positive" for amrita.
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# The 7 traditional / non-nodal planets used by Kala Sarpa.
_TRADITIONAL_SEVEN: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=D-12 lockfile — Kala Sarpa strict 180° Rahu-leading "
    "(K.N. Rao / PVR consensus)"
)


def _planet_longitude(
    d1_chart: Mapping[str, Mapping[str, object]], planet: str,
) -> float | None:
    entry = d1_chart.get(planet)
    if not entry:
        return None
    lon = entry.get("longitude")
    if not isinstance(lon, (int, float)):
        return None
    return float(lon) % 360.0


def _build_finding(
    variant: str,
    rahu_lon: float,
    forward_arcs: dict[str, float],
) -> Finding:
    labels = {
        "ksy":    "Kala Sarpa Yoga",
        "amrita": "Kala Amrita Yoga",
    }
    summaries = {
        "ksy": "all 7 planets in Rahu-leading 180° arc (karmic struggle)",
        "amrita": "all 7 planets in Ketu-leading 180° arc (benign mirror)",
    }
    direction = "negative" if variant == "ksy" else "positive"
    verdict = f"{labels[variant]} — {summaries[variant]}"[:140]
    evidence = [
        f"variant={variant}",
        f"rahu_longitude={rahu_lon:.2f}",
        "all_seven_in_strict_hemisphere=True",
        *[
            f"{p}_forward_arc_from_rahu={arc:.2f}"
            for p, arc in forward_arcs.items()
        ],
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id=f"practitioner.yogas_extended.kala_sarpa.{variant}",
        rule="kala_sarpa_yoga",
        source_sequence=None,
        classification="yoga",
        direction=direction,
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_kala_sarpa(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> list[Finding]:
    """Detect Kala Sarpa / Kala Amrita per D-12 strict definition.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int, "longitude": float, ...}}.
            Each planet record must carry a ``longitude`` field (0..360).
        asc_sign: 1..12 ascendant sign (validated; carried in evidence).

    Returns:
        A list with at most ONE Finding. Empty when Rahu is missing, any
        of the 7 traditional planets is missing a longitude, or neither
        strict variant matches.

    Raises:
        ValueError: if asc_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    rahu_lon = _planet_longitude(d1_chart, "Rahu")
    if rahu_lon is None:
        return []

    forward_arcs: dict[str, float] = {}
    for planet in _TRADITIONAL_SEVEN:
        p_lon = _planet_longitude(d1_chart, planet)
        if p_lon is None:
            return []
        forward_arcs[planet] = (p_lon - rahu_lon) % 360.0

    # KSY: every planet strictly in (0, 180) from Rahu.
    ksy = all(0.0 < arc < 180.0 for arc in forward_arcs.values())
    # Amrita: every planet strictly in (180, 360) from Rahu — i.e. they
    # all sit in the Ketu-leading half.
    amrita = all(180.0 < arc < 360.0 for arc in forward_arcs.values())

    if ksy:
        return [_build_finding("ksy", rahu_lon, forward_arcs)]
    if amrita:
        return [_build_finding("amrita", rahu_lon, forward_arcs)]
    return []


__all__ = ["detect_kala_sarpa"]
