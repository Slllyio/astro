"""Tier-1 foundation: Bhava Chalit (Sripati cusps) per D-8 doctrine lock.

Doctrine lock - D-8 (``docs/doctrine-decisions.md``)
====================================================

Use the **Sripati** house cusp system (BPHS Vol.II Ch.51) for the Bhava
Chalit chart. KP and Placidus are explicitly excluded by spec Section 2.

Algorithm
---------

The Lagna degree IS the bhava-madhya (cusp midpoint) of house 1. Each
bhava spans 30 degrees centered on its madhya; sandhi (boundaries)
sit at madhya +/- 15 degrees. Equivalently the LOWER sandhi of bhava N
sits at::

    lower_sandhi_N = (lagna_deg + (N - 1) * 30 - 15) mod 360

and the UPPER sandhi at ``lower_sandhi_N + 30`` (= LOWER of bhava N+1).

To assign a planet at sidereal longitude ``lon`` to its chalit-bhava,
shift the reference so the LOWER sandhi of bhava 1 sits at zero,
take the value mod 360, and floor-divide by 30::

    chalit_bhava = floor(((lon - (lagna_deg - 15)) mod 360) / 30) + 1

Half-open convention: the LOWER sandhi (lagna - 15) belongs to bhava 1
(inclusive); the UPPER sandhi (lagna + 15) belongs to bhava 2 (exclusive
for bhava 1). The wraparound at 360->0 is handled by the explicit
``mod 360`` and matches the project's "circular orb" convention from
``CLAUDE.md``.

Why this matters
----------------

A planet's rashi-house (sign from Lagna's rashi) may differ from its
chalit-bhava when the planet sits near a sign boundary OR when the Lagna
degree sits near a sign boundary (a "shifted" planet). The chalit chart
is the most-direct way to surface the discrepancy:

    Example: Lagna at Virgo 28 deg (abs 178); Mars at Libra 5 deg
    (abs 185). Mars rashi-house = 2 (Libra from Virgo). Mars
    chalit-bhava = 1 (within +-15 deg of lagna madhya). The chalit
    chart correctly assigns Mars to the 1st-house signification despite
    Mars's rashi being the 2nd from Lagna.

Direction in the emitted Finding
--------------------------------

- ``positive`` if chalit-bhava != rashi-bhava (a SHIFT is detected; this
  is the whole point of running the chalit computation).
- ``neutral`` otherwise (no shift; the chalit and rashi house agree).

Public API
==========

    compute_bhava_chalit(d1_chart, lagna_abs_lon, asc_sign) -> dict[str, Finding]

The input ``d1_chart`` mirrors ``chart["d1"]`` from
``calculate_all_charts``; each entry must carry ``longitude`` (absolute
sidereal degrees in 0..360). ``lagna_abs_lon`` is the Lagna's absolute
sidereal longitude. ``asc_sign`` is the Lagna's rashi (1..12).

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> chart = calculate_all_charts(1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    >>> from app.reading.computations.bhava_chalit import compute_bhava_chalit
    >>> chalit = compute_bhava_chalit(
    ...     chart["d1"],
    ...     chart["ascendant"]["longitude"],
    ...     chart["ascendant"]["sign"],
    ... )
    >>> chalit["Mars"].verdict
    'Mars rashi-house 8, chalit-bhava 7 (shifted)'
"""
from __future__ import annotations

import logging
from typing import Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Sign half-degree span used for the bhava sandhi (= 30 / 2).
_HALF_BHAVA: Final[float] = 15.0
_BHAVA_SPAN: Final[float] = 30.0
_ZODIAC: Final[float] = 360.0


# 3-vote envelope -- chalit assignment is a single deterministic
# computation, not a 3-pillar judgment.
_FOUNDATION_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _rashi_house_from_lagna(planet_sign: int, asc_sign: int) -> int:
    """Whole-sign rashi-house (1..12) of a planet from the Lagna sign."""
    return ((planet_sign - asc_sign) % 12) + 1


def _chalit_bhava(lon: float, lagna_abs_lon: float) -> int:
    """Sripati chalit-bhava (1..12) for a planet at ``lon``.

    Implementation: shift the reference so the LOWER sandhi of bhava 1
    sits at 0 degrees, then floor-divide by 30. The mod-360 absorbs
    wraparound at the 0/360 boundary.

    Sandhi convention: the LOWER sandhi belongs to its bhava (inclusive);
    the UPPER sandhi belongs to the NEXT bhava (exclusive). So a planet
    exactly at ``lagna_abs_lon - 15`` is in bhava 1, while a planet
    exactly at ``lagna_abs_lon + 15`` is in bhava 2.
    """
    shifted = (lon - (lagna_abs_lon - _HALF_BHAVA)) % _ZODIAC
    bhava = int(shifted // _BHAVA_SPAN) + 1
    # Defensive: should never trigger given the mod above, but guard
    # against floating-point quirks at exact-360 wraparound.
    if bhava > 12:
        bhava = ((bhava - 1) % 12) + 1
    if bhava < 1:
        bhava = ((bhava - 1) % 12) + 1
    return bhava


def _chalit_finding(
    planet: str,
    planet_lon: float,
    lagna_abs_lon: float,
    rashi_bhava: int,
    chalit_bhava: int,
) -> Finding:
    """Build the Finding for one planet's chalit-bhava assignment."""
    shifted = chalit_bhava != rashi_bhava
    direction = "positive" if shifted else "neutral"
    suffix = " (shifted)" if shifted else " (no shift)"
    verdict = (
        f"{planet} rashi-house {rashi_bhava}, chalit-bhava "
        f"{chalit_bhava}{suffix}"
    )
    return Finding(
        id=f"foundation.bhava_chalit.{planet.lower()}",
        rule="bhava_chalit",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"planet_longitude={planet_lon:.4f}",
            f"lagna_longitude={lagna_abs_lon:.4f}",
            f"rashi_bhava={rashi_bhava}",
            f"chalit_bhava={chalit_bhava}",
            f"shifted={'true' if shifted else 'false'}",
            "doctrine=D-8 (sripati_cusps)",
        ],
        confidence=_FOUNDATION_CONFIDENCE,
    )


def compute_bhava_chalit(
    d1_chart: dict,
    lagna_abs_lon: float,
    asc_sign: int,
) -> dict[str, Finding]:
    """Compute Sripati chalit-bhava for every planet in a D1 chart.

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each position
            must carry ``longitude`` (absolute sidereal degrees) and
            ``sign`` (1-indexed rashi).
        lagna_abs_lon: Absolute sidereal Lagna longitude in 0..360.
        asc_sign: Lagna's rashi (1=Aries .. 12=Pisces).

    Returns:
        Dict keyed by planet name, each value a
        ``foundation.bhava_chalit.<planet>`` Finding. The ``direction``
        is ``positive`` if the chalit-bhava differs from the rashi-
        bhava, ``neutral`` otherwise.

    Raises:
        ValueError: if ``lagna_abs_lon`` is not in ``[0, 360)`` or
            ``asc_sign`` is not in ``1..12``.
        KeyError: if a planet entry lacks ``longitude`` or ``sign``.
    """
    if not 0.0 <= lagna_abs_lon < _ZODIAC:
        raise ValueError(
            f"lagna_abs_lon must be in [0, 360), got {lagna_abs_lon!r}"
        )
    if not 1 <= asc_sign <= 12:
        raise ValueError(
            f"asc_sign must be in [1, 12], got {asc_sign!r}"
        )

    findings: dict[str, Finding] = {}
    for planet, entry in d1_chart.items():
        if "longitude" not in entry:
            raise KeyError(
                f"planet {planet!r} missing 'longitude' field"
            )
        lon = float(entry["longitude"])
        planet_sign = entry.get("sign")
        if planet_sign is None:
            # Derive sign from absolute longitude defensively.
            planet_sign = int(lon // 30) + 1
        planet_sign = int(planet_sign)

        rashi_bhava = _rashi_house_from_lagna(planet_sign, asc_sign)
        chalit_bhava = _chalit_bhava(lon, lagna_abs_lon)
        findings[planet] = _chalit_finding(
            planet, lon, lagna_abs_lon, rashi_bhava, chalit_bhava,
        )
    return findings


__all__ = ["compute_bhava_chalit"]
