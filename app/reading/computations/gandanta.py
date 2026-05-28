"""Tier-0 primitive: Gandanta (water-to-fire nakshatra junction) detection.

A Gandanta zone is the ``+- 3 deg 20 min`` (one pada = 360/27/4) ribbon
straddling each of three water-to-fire transitions in the zodiac:

| Junction                          | Absolute sidereal longitude | From sign / to sign |
|-----------------------------------|-----------------------------|---------------------|
| Revati pada 4 -> Ashwini pada 1   | 360.0 (= 0.0)               | Pisces -> Aries     |
| Ashlesha pada 4 -> Magha pada 1   | 120.0                       | Cancer -> Leo       |
| Jyeshtha pada 4 -> Mula pada 1    | 240.0                       | Scorpio -> Sag.     |

Planets that occupy these knots are classically considered afflicted -- the
junction marks the transition out of a water sign (an emotional or
dissolving element) into a fire sign (a fresh, agitated element); the
abrupt elemental shift is read as inherently unstable.

Doctrine choice: the half-width is the classical 1-pada zone
(``360 / 27 / 4 ~ 3.333 deg``). Some traditions use a narrower +-1.5 deg
zone; we choose the wider classical reading per the task brief.

Public API:
    ``detect_gandanta(d1_chart) -> list[Finding]``

The input ``d1_chart`` is the same shape consumed by other Tier-0
modules: a dict keyed by planet name where each value carries a
``longitude`` (sidereal Lahiri, 0..360).
"""
from __future__ import annotations

import logging
from typing import Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Half-width of the classical Gandanta zone, equal to one pada.
GANDANTA_ZONE_HALFWIDTH: Final[float] = 360.0 / 27.0 / 4.0  # ~ 3.333... degrees


# Each junction carries the absolute sidereal longitude where the water
# sign ends, the outgoing nakshatra (water side), and the incoming
# nakshatra (fire side). Used for human-readable verdicts.
_JUNCTIONS: Final[tuple[tuple[float, str, str], ...]] = (
    (0.0, "Revati", "Ashwini"),
    (120.0, "Ashlesha", "Magha"),
    (240.0, "Jyeshtha", "Mula"),
)


_AFFLICTION_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _circular_distance(lon: float, junction: float) -> float:
    """Return ``min(|lon - junction|, 360 - |lon - junction|)``.

    Required because the Revati-Ashwini junction sits at the 359 deg / 0 deg
    wrap-around; naive ``abs()`` silently fails there. See CLAUDE.md
    locked convention "Circular orb distance".
    """
    diff = abs(lon - junction) % 360.0
    return min(diff, 360.0 - diff)


def _nearest_junction(lon: float) -> tuple[float, float, str, str] | None:
    """Find the junction the longitude is closest to and return its info.

    Returns ``(distance, junction_lon, outgoing_nakshatra, incoming_nakshatra)``
    if any junction is within the Gandanta zone, otherwise ``None``.
    """
    best: tuple[float, float, str, str] | None = None
    lon = lon % 360.0
    for jct_lon, outgoing, incoming in _JUNCTIONS:
        dist = _circular_distance(lon, jct_lon)
        if dist <= GANDANTA_ZONE_HALFWIDTH + 1e-9:  # epsilon for fp safety
            if best is None or dist < best[0]:
                best = (dist, jct_lon, outgoing, incoming)
    return best


def _gandanta_finding(
    planet: str, longitude: float, junction: tuple[float, float, str, str]
) -> Finding:
    """Build the Finding describing one planet's Gandanta affliction."""
    dist, jct_lon, outgoing, incoming = junction
    return Finding(
        id=f"primitive.gandanta.{planet.lower()}",
        rule="gandanta",
        source_sequence=None,
        classification="affliction",
        direction="negative",
        verdict=(
            f"{planet} at {longitude:.2f} deg is Gandanta "
            f"({outgoing}-{incoming})"
        ),
        evidence=[
            f"longitude={longitude:.4f}",
            f"junction={jct_lon:.1f}",
            f"distance_to_junction={dist:.4f}",
            f"zone_halfwidth={GANDANTA_ZONE_HALFWIDTH:.4f}",
        ],
        confidence=_AFFLICTION_CONFIDENCE,
    )


def detect_gandanta(d1_chart: dict) -> list[Finding]:
    """Detect planets sitting in any of the three Gandanta junctions.

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each position
            must carry ``longitude`` (sidereal Lahiri, in degrees).

    Returns:
        A list of ``primitive.gandanta.<planet>`` Findings, one per
        afflicted planet, in input order. Empty if no planet is in any
        zone.

    Raises:
        KeyError: if any entry in ``d1_chart`` lacks ``longitude``.
    """
    findings: list[Finding] = []
    for planet, position in d1_chart.items():
        try:
            lon = float(position["longitude"])
        except KeyError as exc:
            raise KeyError(
                f"planet {planet!r} missing required 'longitude' field"
            ) from exc

        junction = _nearest_junction(lon)
        if junction is not None:
            findings.append(_gandanta_finding(planet, lon, junction))
    return findings
