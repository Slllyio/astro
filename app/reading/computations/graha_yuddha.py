"""Tier-2 doctrine: Graha Yuddha (planetary war) winner detection.

Doctrine source: BPHS Vol.I Ch.27 v.13 (locked via D-13 in
``docs/doctrine-decisions.md``).

When two **non-luminary** planets (Mars, Mercury, Jupiter, Venus, Saturn)
sit within 1° of longitude of each other in the **same sign**, they
engage in Graha Yuddha. The winner is determined by celestial latitude
— the **more northern** planet wins; the loser's significations spoil
lifelong (treated as if combust).

D-13 invariants
===============

* **Luminaries (Sun, Moon) NEVER engage in graha yuddha.** Classical
  doctrine excludes them entirely.
* **Same-sign requirement.** A pair straddling a sign cusp (e.g. one at
  29.8° Aries, the other at 0.5° Taurus) is technically a conjunction,
  not a graha yuddha — modern Parashari practice keeps the war
  intra-sign.
* **1° orb in longitude.** BPHS verse uses a tight 1° tolerance.
* **Latitude tie-break.** The more northern (ecliptic latitude greater
  in the +N direction) planet wins. When latitude data is missing for
  either combatant the war is silently skipped (defensive).
* **Nodes (Rahu, Ketu) are formally non-luminary, but they have no
  meaningful celestial latitude in the same sense (they ARE the lunar
  nodes), so they are also excluded from graha yuddha computation in
  modern practice.** Limiting participants to the 5 visible non-luminary
  planets (Ma, Me, Ju, Ve, Sa) is consistent with BPHS and with
  jagannathahora.io's output.

Public API
==========

    detect_graha_yuddha(d1_chart) -> list[Finding]
"""
from __future__ import annotations

import logging
from itertools import combinations
from typing import Final, Mapping

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Planets eligible for graha yuddha (D-13).
_COMBATANTS: Final[tuple[str, ...]] = (
    "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


# 1° longitude tolerance.
_ORB_DEGREES: Final[float] = 1.0


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _longitude_distance(lon_a: float, lon_b: float) -> float:
    """Circular ecliptic distance (degrees). Same as the project-wide
    convention: ``min(diff, 360 - diff)`` where diff = |lon_a - lon_b| mod
    360. Returns a non-negative number in [0, 180]."""
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def _safe_get(record: Mapping[str, object], key: str) -> object | None:
    """Mapping.get without crashing on TypedDict-style records."""
    try:
        return record.get(key)  # type: ignore[union-attr]
    except AttributeError:
        return None


def _build_war_finding(
    winner: str, winner_lat: float,
    loser: str, loser_lat: float,
    sign: int,
) -> Finding:
    """Build a Finding for one detected graha yuddha."""
    pair_id = f"{winner.lower()}_vs_{loser.lower()}"
    verdict = (
        f"{winner} wins over {loser} ({winner} latitude"
        f"{winner_lat:+.2f}° vs {loser} {loser_lat:+.2f}°)"
    )
    return Finding(
        id=f"practitioner.graha_yuddha.{pair_id}",
        rule="graha_yuddha",
        source_sequence=None,
        classification="affliction",
        direction="negative",
        verdict=verdict[:140],
        evidence=[
            f"winner={winner}",
            f"loser={loser}",
            f"winner_latitude={winner_lat:+.4f}",
            f"loser_latitude={loser_lat:+.4f}",
            f"shared_sign={sign}",
            "doctrine=D-13 (BPHS Vol.I Ch.27 v.13 northern-latitude wins)",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_graha_yuddha(
    d1_chart: Mapping[str, Mapping[str, object]],
) -> list[Finding]:
    """Detect Graha Yuddha across non-luminary planet pairs.

    Args:
        d1_chart: Mapping {planet_name: planet_record}. Each record must
            carry ``longitude`` (degrees), ``sign`` (1..12). When
            ``latitude`` is also present it enables winner determination
            per D-13; when absent the candidate pair is silently
            skipped.

    Returns:
        List of Findings — one per detected war. The Finding's id pairs
        the winner first ("mars_vs_saturn" when Mars wins).

    Raises:
        Nothing — defensive on missing fields (graha yuddha is only
        emitted when all required fields are present and the doctrine
        invariants hold).
    """
    findings: list[Finding] = []

    for planet_a, planet_b in combinations(_COMBATANTS, 2):
        record_a = d1_chart.get(planet_a)
        record_b = d1_chart.get(planet_b)
        if record_a is None or record_b is None:
            continue

        sign_a = _safe_get(record_a, "sign")
        sign_b = _safe_get(record_b, "sign")
        lon_a = _safe_get(record_a, "longitude")
        lon_b = _safe_get(record_b, "longitude")
        if sign_a is None or sign_b is None:
            continue
        if lon_a is None or lon_b is None:
            continue

        # Same-sign requirement.
        if sign_a != sign_b:
            continue

        # 1° orb in longitude.
        try:
            dist = _longitude_distance(float(lon_a), float(lon_b))
        except (TypeError, ValueError):
            continue
        if dist > _ORB_DEGREES:
            continue

        # Latitude required for winner determination.
        lat_a = _safe_get(record_a, "latitude")
        lat_b = _safe_get(record_b, "latitude")
        if lat_a is None or lat_b is None:
            logger.debug(
                "graha_yuddha: %s/%s within orb but missing latitude — skip",
                planet_a, planet_b,
            )
            continue

        try:
            lat_a_f = float(lat_a)
            lat_b_f = float(lat_b)
        except (TypeError, ValueError):
            continue

        # Northern-latitude winner. Equal-latitude is a degenerate tie;
        # treat it as no war (defensive — astronomically vanishingly rare).
        if lat_a_f > lat_b_f:
            findings.append(_build_war_finding(
                planet_a, lat_a_f, planet_b, lat_b_f, int(sign_a),
            ))
        elif lat_b_f > lat_a_f:
            findings.append(_build_war_finding(
                planet_b, lat_b_f, planet_a, lat_a_f, int(sign_a),
            ))
        # else: equal latitudes — no winner — skip.

    return findings


__all__ = ["detect_graha_yuddha"]
