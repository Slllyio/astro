"""Tier-2 doctrine: Eclipse natal-point activation.

Doctrine source: Modern Jyotisha synthesis (K.N. Rao's predictive
astrology + BV Raman's *Eclipses in Mundane Astrology*). No single
BPHS verse — the rule is post-classical.

The rule
========

An eclipse (solar or lunar) whose ecliptic longitude falls within
±1° of a natal point (a natal planet's longitude or the lagna)
**activates** that natal point for the ~6 months following the
eclipse. The activation foregrounds the natal point's significations
in the native's life during that window.

Sign / direction
================

* Benefic natal point activated  → **positive** Finding (constructive
  activation — career milestones, learning peaks, finance peaks).
* Malefic natal point activated  → **negative** Finding (disruptive
  activation — friction, health events, separations).
* Lagna activation                → **neutral** Finding (general
  life-direction shift; sign-of-effect emerges from co-activated
  planets).

Benefic set: Jupiter, Venus, Mercury, Moon (canonical Vedic naturals).
Malefic set: Sun, Mars, Saturn, Rahu, Ketu.

Inputs
======

The detector accepts ``eclipses`` as a list of dicts with keys
``date`` (string), ``type`` ("solar" | "lunar"), ``degree`` (0..30),
``sign`` (1..12).

Public API
==========

    detect_eclipse_activation(d1_chart, asc_sign, eclipses) -> list[Finding]
"""
from __future__ import annotations

import logging
from typing import Final, Mapping, Sequence

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# ±1° activation orb.
_ACTIVATION_ORB: Final[float] = 1.0


# Lagna v1 simplification — mid-sign anchor. A future API extension may
# accept the precise lagna longitude.
_MID_SIGN_OFFSET: Final[float] = 15.0


# Benefic / malefic sets for direction.
_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})


# All 9 natal planets considered.
_NATAL_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _circular_distance(lon_a: float, lon_b: float) -> float:
    """Shortest-arc distance on the circle."""
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def _direction_for(planet_name: str) -> str:
    if planet_name in _BENEFICS:
        return "positive"
    if planet_name in _MALEFICS:
        return "negative"
    # Lagna or unknown
    return "neutral"


def _build_activation_finding(
    eclipse_date: str,
    eclipse_type: str,
    eclipse_lon: float,
    natal_point: str,
    natal_lon: float,
    direction: str,
) -> Finding:
    eclipse_sign = _SIGN_NAMES[int(eclipse_lon // 30.0) + 1]
    eclipse_deg = eclipse_lon % 30.0
    if natal_point == "Lagna":
        verdict = (
            f"{eclipse_type.capitalize()} eclipse at {eclipse_deg:.0f}° "
            f"{eclipse_sign} activates natal Lagna"
        )
    else:
        verdict = (
            f"{eclipse_type.capitalize()} eclipse at {eclipse_deg:.0f}° "
            f"{eclipse_sign} activates natal {natal_point}"
        )
    point_slug = natal_point.lower()
    return Finding(
        id=f"practitioner.eclipse_activation.{eclipse_date}_{point_slug}",
        rule="eclipse_natal_activation",
        source_sequence=None,
        classification="trigger",
        direction=direction,  # type: ignore[arg-type]
        verdict=verdict[:140],
        evidence=[
            f"eclipse_date={eclipse_date}",
            f"eclipse_type={eclipse_type}",
            f"eclipse_longitude={eclipse_lon:.4f}",
            f"natal_point={natal_point}",
            f"natal_longitude={natal_lon:.4f}",
            f"orb_degrees={_circular_distance(eclipse_lon, natal_lon):.4f}",
            "doctrine=K.N. Rao + BV Raman eclipse-activation (modern Jyotisha)",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_eclipse_activation(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    eclipses: Sequence[Mapping[str, object]],
) -> list[Finding]:
    """Detect eclipse-driven activations of natal points.

    Args:
        d1_chart: Mapping {planet_name: planet_record}. Each record's
            ``longitude`` field is consumed.
        asc_sign: 1..12 ascendant sign (used to derive a mid-sign lagna
            longitude for v1 — see TODO below).
        eclipses: Sequence of eclipse dicts with ``date`` (str), ``type``
            ("solar" | "lunar"), ``degree`` (float, 0..30), ``sign``
            (int, 1..12).

    Returns:
        List of Findings — one per (eclipse, natal_point) within ±1°.
        Empty when no activations are detected.

    Raises:
        ValueError: if ``asc_sign`` is outside 1..12 or any eclipse
            dict's sign/degree is malformed.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    # v1: lagna longitude = mid-sign of asc_sign.
    # TODO(reading.eclipse_natal_activation): accept the precise lagna
    # longitude as an optional parameter and prefer it when supplied.
    lagna_lon = (asc_sign - 1) * 30.0 + _MID_SIGN_OFFSET

    # Pre-compute natal longitudes (planets + Lagna).
    natal_points: list[tuple[str, float]] = []
    for planet in _NATAL_PLANETS:
        record = d1_chart.get(planet)
        if record is None:
            continue
        try:
            lon = float(record["longitude"])  # type: ignore[arg-type]
        except (KeyError, TypeError, ValueError):
            continue
        natal_points.append((planet, lon % 360.0))
    natal_points.append(("Lagna", lagna_lon % 360.0))

    findings: list[Finding] = []
    for eclipse in eclipses:
        try:
            ecl_sign = int(eclipse["sign"])  # type: ignore[arg-type]
            ecl_deg = float(eclipse["degree"])  # type: ignore[arg-type]
            ecl_date = str(eclipse["date"])
            ecl_type = str(eclipse["type"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"malformed eclipse record {eclipse!r}: {exc}"
            ) from exc
        if not 1 <= ecl_sign <= 12:
            raise ValueError(
                f"eclipse sign must be 1..12, got {ecl_sign}"
            )
        if not 0.0 <= ecl_deg < 30.0:
            raise ValueError(
                f"eclipse degree must be 0..30 (exclusive), got {ecl_deg}"
            )

        ecl_lon = (ecl_sign - 1) * 30.0 + ecl_deg

        for natal_point, natal_lon in natal_points:
            if _circular_distance(ecl_lon, natal_lon) <= _ACTIVATION_ORB:
                direction = _direction_for(natal_point)
                findings.append(_build_activation_finding(
                    ecl_date, ecl_type, ecl_lon,
                    natal_point, natal_lon, direction,
                ))

    return findings


__all__ = ["detect_eclipse_activation"]
