"""Tier-0 primitive: residential strength of each planet (D-5 locked).

Doctrine lock — D-5 (``docs/doctrine-decisions.md``)
====================================================

A planet's residential strength within a bhava follows a **linear falloff
from Bhaav-Madhya (cusp midpoint) to the bhava sandhi (junction)**, zero
at sandhi:

    strength = 60 × (1 − distance_from_madhya / 30)

For this Tier-0 primitive the comparison is the planet's
*degree-within-sign* vs. the **Lagna's degree-within-its-sign**: a
planet at the same degree as the Lagna sits at the Bhaav-Madhya of its
own bhava and scores 60; a planet on the opposite side of its sign sits
at sandhi and the strength falls off linearly.

The 8°-strong / 3°-very-strong **classification bands** are a
*post-processing overlay* applied on top of the continuous formula, not
the formula itself. The continuous score lives in ``evidence`` as
``strength=`` and the categorical band lives as ``band=``.

| band         | range (strength) |
|--------------|------------------|
| very_strong  | ≥ 51             |
| strong       | ≥ 40             |
| moderate     | ≥ 20             |
| weak         | < 20             |

Public API
==========

    compute_residential_strength(d1_chart, lagna_degree) -> dict[str, Finding]

The input ``d1_chart`` mirrors ``chart["d1"]`` from
``calculate_all_charts``; each entry must carry ``degree_in_sign`` (or
``longitude``). ``lagna_degree`` is the Lagna's
``degree_in_sign`` (in degrees ``[0, 30)``).

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> chart = calculate_all_charts(1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    >>> from app.reading.computations.residential_strength import (
    ...     compute_residential_strength,
    ... )
    >>> strengths = compute_residential_strength(
    ...     chart["d1"], chart["ascendant"]["degree_in_sign"]
    ... )
    >>> strengths["Saturn"].verdict
    'Saturn residential strength ... (band: ...)'
"""
from __future__ import annotations

import logging
from typing import Final, Literal

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Half-sign span — the maximum circular distance between two
# degrees-within-sign. The formula clips ``distance`` to ``30.0`` so
# pathological inputs never produce a negative strength.
_MAX_DISTANCE: Final[float] = 30.0

# Strength scale — BPHS / Phaladeepika 60-Rupa convention.
_MAX_STRENGTH: Final[float] = 60.0

# Band thresholds (see module docstring).
_VERY_STRONG_MIN: Final[float] = 51.0
_STRONG_MIN: Final[float] = 40.0
_MODERATE_MIN: Final[float] = 20.0


# 3-vote envelope — residential strength is a single deterministic
# computation, not a 3-pillar judgment.
_PRIMITIVE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


ResidentialBand = Literal["very_strong", "strong", "moderate", "weak"]


def _circular_distance(planet_deg: float, lagna_deg: float) -> float:
    """Compute circular degree-within-sign distance.

    Returns ``min(|p - l|, 30 - |p - l|)`` so that the 359°/2° style
    cusp wraparound (here 29.5° -> 0.5° within-sign) doesn't fall over.
    Matches the project-wide circular-orb convention from CLAUDE.md.
    """
    diff = abs(planet_deg - lagna_deg) % _MAX_DISTANCE
    return min(diff, _MAX_DISTANCE - diff)


def _band_for(strength: float) -> ResidentialBand:
    """Bucket a continuous strength into the four classical bands."""
    if strength >= _VERY_STRONG_MIN:
        return "very_strong"
    if strength >= _STRONG_MIN:
        return "strong"
    if strength >= _MODERATE_MIN:
        return "moderate"
    return "weak"


def _strength_finding(
    planet: str,
    planet_deg: float,
    lagna_deg: float,
    distance: float,
    strength: float,
    band: ResidentialBand,
) -> Finding:
    """Build the Finding for one planet's residential strength."""
    return Finding(
        id=f"primitive.residential_strength.{planet.lower()}",
        rule="residential_strength",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=(
            f"{planet} residential strength {strength:.1f} "
            f"(band: {band})"
        ),
        evidence=[
            f"planet_degree_in_sign={planet_deg:.4f}",
            f"lagna_degree_in_sign={lagna_deg:.4f}",
            f"distance_from_madhya={distance:.4f}",
            f"strength={strength:.4f}",
            f"band={band}",
            "doctrine=D-5 (linear_falloff_to_sandhi)",
        ],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def compute_residential_strength(
    d1_chart: dict,
    lagna_degree: float,
) -> dict[str, Finding]:
    """Compute residential strength for every planet in a D1 chart.

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each position
            must carry ``degree_in_sign`` (preferred) or ``longitude``.
        lagna_degree: Lagna's degree-within-sign, in degrees ``[0, 30)``.

    Returns:
        Dict keyed by planet name, each value a
        ``primitive.residential_strength.<planet>`` Finding.

    Raises:
        ValueError: if ``lagna_degree`` is not in ``[0, 30)``.
        KeyError: if a planet entry lacks both ``degree_in_sign`` and
            ``longitude``.
    """
    if not 0.0 <= lagna_degree < 30.0:
        raise ValueError(
            f"lagna_degree must be in [0, 30), got {lagna_degree!r}"
        )

    findings: dict[str, Finding] = {}
    for planet, entry in d1_chart.items():
        deg = entry.get("degree_in_sign")
        if deg is None:
            try:
                lon = float(entry["longitude"])
            except KeyError as exc:
                raise KeyError(
                    f"planet {planet!r} missing both 'degree_in_sign' and "
                    f"'longitude'"
                ) from exc
            deg = lon % 30.0
        deg = float(deg)

        distance = _circular_distance(deg, lagna_degree)
        # Linear falloff: 1 - distance/30, clamped at 0 (defensive — natural
        # max for the circular distance is 15).
        ratio = max(0.0, 1.0 - distance / _MAX_DISTANCE)
        strength = _MAX_STRENGTH * ratio
        band = _band_for(strength)
        findings[planet] = _strength_finding(
            planet, deg, lagna_degree, distance, strength, band
        )
    return findings


__all__ = ["compute_residential_strength", "ResidentialBand"]
