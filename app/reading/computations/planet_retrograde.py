"""Tier-0 primitive: extract per-planet retrograde flag as Findings.

This module is pure data extraction. It reads the ``is_retrograde`` flag
already computed by ``app.core.ephemeris_engine.calculate_d1_position``
(based on Swiss Ephemeris longitudinal speed, ``swe.FLG_SPEED``) and
re-emits it in the universal Finding shape so downstream reading-layer
sequences can consume it.

No interpretive judgment is applied here -- ``direction="neutral"`` --
because retrogression alone has no positive/negative valence. Higher-tier
modules (e.g. functional reversals, dasha-step checks) layer that
interpretation on top.

Public API:
    ``detect_retrograde(d1_chart) -> dict[str, Finding]``

The input ``d1_chart`` mirrors ``chart["d1"]`` from
``calculate_all_charts``: a dict keyed by planet name where each value
carries at least an ``is_retrograde: bool`` key.

Usage:
    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> chart = calculate_all_charts(1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    >>> from app.reading.computations.planet_retrograde import detect_retrograde
    >>> findings = detect_retrograde(chart["d1"])
    >>> findings["Mars"].verdict
    'Mars is retrograde'   # or 'Mars is direct' depending on the chart
"""
from __future__ import annotations

import logging

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# 3-vote envelope -- retrogression is a single objective fact rather than
# a 3-pillar (house/lord/karaka) judgment. We set all votes False with band
# "indicative_only" so the score stays at 0.0, matching the "no doctrine
# interpretation applied" semantics.
_PRIMITIVE_CONFIDENCE = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _retrograde_finding(planet: str, is_retrograde: bool) -> Finding:
    """Build the Finding for one planet's retrograde state.

    The verdict is human-readable and intentionally compact so it slots
    cleanly into downstream UI/RAG contexts (well under the 140-char
    schema limit).
    """
    state = "retrograde" if is_retrograde else "direct"
    return Finding(
        id=f"primitive.planet_retrograde.{planet.lower()}",
        rule="planet_retrograde",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=f"{planet} is {state}",
        evidence=[
            f"swisseph FLG_SPEED -> is_retrograde={is_retrograde}",
        ],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def detect_retrograde(d1_chart: dict) -> dict[str, Finding]:
    """Extract per-planet retrograde state from a D1 chart.

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each position
            must carry an ``is_retrograde`` boolean (as produced by
            ``app.core.ephemeris_engine.calculate_d1_position``). Sun and
            Moon are physically never retrograde; Rahu/Ketu use the True
            Node speed sign reported by Swiss Ephemeris.

    Returns:
        A dict keyed by the same planet names as ``d1_chart``, mapping
        each to a ``primitive.planet_retrograde.<planet>`` Finding.

    Raises:
        KeyError: if any entry in ``d1_chart`` lacks ``is_retrograde``.
    """
    findings: dict[str, Finding] = {}
    for planet, position in d1_chart.items():
        try:
            flag = bool(position["is_retrograde"])
        except KeyError as exc:
            raise KeyError(
                f"planet {planet!r} missing required 'is_retrograde' field"
            ) from exc
        findings[planet] = _retrograde_finding(planet, flag)
    return findings
