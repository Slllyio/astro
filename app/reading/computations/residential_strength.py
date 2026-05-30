"""Tier-0 primitive: residential strength of each planet (D-5 locked).

Doctrine lock — D-5 (``docs/doctrine-decisions.md``)
====================================================

A planet's residential strength within a bhava follows a **linear falloff
from Bhaav-Madhya (cusp midpoint) to the bhava sandhi (junction)**, zero
at sandhi:

    strength = 60 × (1 − distance_from_madhya / 15)

The divisor is **15°**, not 30°. Under whole-sign Vedic doctrine the
half-bhava distance from Bhaav-Madhya to sandhi is 15° (the sign spans
30°; the madhya sits midway; sandhi is at the 0°/30° sign boundary, i.e.
15° away). The circular distance ``min(diff, 30 - diff)`` naturally maxes
at 15°, so the formula reaches **exactly zero at sandhi** as the lockfile
requires.

.. note::

   Pre-checkpoint-#1 the divisor was 30 (BUG: strength never reached zero
   because the maximum natural distance is 15, so strength bottomed at
   30, never 0). The D-5 lockfile was amended 2026-05-27 to correct this
   to honour the "zero at sandhi" invariant under BPHS whole-sign
   half-bhava semantics. See ``docs/doctrine-decisions.md`` D-5 entry.

For this Tier-0 primitive the comparison is the planet's
*degree-within-sign* vs. the **Lagna's degree-within-its-sign**: a
planet at the same degree as the Lagna sits at the Bhaav-Madhya of its
own bhava and scores 60; a planet 15° away (the sandhi) scores 0.

The classification bands are **degree-distance based** (more classical
than strength-value cutoffs, which were a derived quantity):

| band         | degree-distance from madhya | rationale                       |
|--------------|-----------------------------|---------------------------------|
| very_strong  | ≤ 3°                        | Phaladeepika 3° intense band    |
| strong       | ≤ 8°                        | BPHS 8° effective zone          |
| moderate     | ≤ 12°                       | remainder until sandhi          |
| weak         | > 12°                       | approaching / at sandhi         |

The continuous strength score lives in ``evidence`` as ``strength=`` and
the categorical degree-based band lives as ``band=``.

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


# Sign span — the circular-distance modulus. Two degrees-within-sign
# differ by at most 30° on the cycle; the circular minimum yields the
# half-sign max of 15°.
_SIGN_SPAN: Final[float] = 30.0

# Sandhi distance — the distance from Bhaav-Madhya to bhava sandhi under
# whole-sign Vedic doctrine. The half-bhava span is 15° each direction
# from madhya. Strength reaches zero at this distance.
_SANDHI_DISTANCE: Final[float] = 15.0

# Strength scale — BPHS / Phaladeepika 60-Rupa convention.
_MAX_STRENGTH: Final[float] = 60.0

# Band thresholds — degree-distance based (see module docstring).
_VERY_STRONG_MAX_DIST: Final[float] = 3.0   # Phaladeepika 3° intense
_STRONG_MAX_DIST: Final[float] = 8.0        # BPHS 8° effective zone
_MODERATE_MAX_DIST: Final[float] = 12.0     # remainder until sandhi
# > 12° -> "weak"


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

    The natural maximum of this function is 15° (the half-sign span),
    which is exactly the sandhi distance under whole-sign doctrine.
    """
    diff = abs(planet_deg - lagna_deg) % _SIGN_SPAN
    return min(diff, _SIGN_SPAN - diff)


def _band_for(distance: float) -> ResidentialBand:
    """Bucket a degree-distance (from madhya) into the four classical bands.

    The cutoffs are degree-based per D-5 (more classical than the
    earlier strength-value cutoffs, which were a derived quantity):

    - ≤ 3°  -> very_strong (Phaladeepika intense zone)
    - ≤ 8°  -> strong (BPHS effective zone)
    - ≤ 12° -> moderate (remainder until sandhi)
    - > 12° -> weak (approaching / at sandhi)
    """
    if distance <= _VERY_STRONG_MAX_DIST:
        return "very_strong"
    if distance <= _STRONG_MAX_DIST:
        return "strong"
    if distance <= _MODERATE_MAX_DIST:
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
        # Linear falloff: 1 - distance/15, clamped at 0. The circular
        # distance naturally maxes at 15° (the sandhi distance under
        # whole-sign doctrine), so strength = 0 at sandhi exactly.
        ratio = max(0.0, 1.0 - distance / _SANDHI_DISTANCE)
        strength = _MAX_STRENGTH * ratio
        band = _band_for(distance)
        findings[planet] = _strength_finding(
            planet, deg, lagna_degree, distance, strength, band
        )
    return findings


__all__ = ["compute_residential_strength", "ResidentialBand"]
