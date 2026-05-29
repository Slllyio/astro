"""Practitioner remedies: daan (charity) per planet.

Doctrine source: Practitioner field-wisdom (foresightbypriyanka, dkscore,
traditional almanacs). Daan is the FRONT-LINE remedy: free, karmically
clean, immediately available, and to be performed BEFORE expensive
gemstone strengthening. The classical bundle for each planet pairs:

    - items: the substance(s) traditionally donated
    - weekday: the planet's vara (day) — donation should happen on this day
    - recipient: the recipient class that "absorbs" the planet's karma

Canonical table (verbatim, do NOT vary substance items):

  +---------+----------------------------------------+-----------------+----------------------+
  | Planet  | Items                                  | Weekday         | Recipient            |
  +=========+========================================+=================+======================+
  | Sun     | wheat, jaggery, copper, red items      | Sunday          | brahmins             |
  | Moon    | rice, milk, silver, white items        | Monday          | mother-figures       |
  | Mars    | red lentils (masoor), red cloth, copper| Tuesday         | soldiers/braves      |
  | Mercury | green moong, green cloth, emerald-like | Wednesday       | students             |
  | Jupiter | yellow items, chana dal, gold          | Thursday        | teachers/gurus       |
  | Venus   | white items, sugar, silk, perfume      | Friday          | women/cows           |
  | Saturn  | black sesame, mustard oil, iron, black | Saturday        | poor/elderly/disabled|
  | Rahu    | black blanket, gomedh stone            | Saturday evening| laborers             |
  | Ketu    | multi-colored cloth, mustard oil       | Tuesday evening | ascetics             |
  +---------+----------------------------------------+-----------------+----------------------+

Public API
==========

    recommend_daan(afflicted_planets) -> list[Finding]
    DAAN_TABLE: Final[dict[str, dict[str, str]]]
"""
from __future__ import annotations

import logging
from typing import Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_PLANETS: Final[frozenset[str]] = frozenset(
    {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
     "Venus", "Saturn", "Rahu", "Ketu"}
)


# Canonical daan table — frozen at module load.
DAAN_TABLE: Final[dict[str, dict[str, str]]] = {
    "Sun": {
        "items": "wheat, jaggery, copper, red items",
        "weekday": "Sunday",
        "recipient": "brahmins",
    },
    "Moon": {
        "items": "rice, milk, silver, white items",
        "weekday": "Monday",
        "recipient": "mother-figures",
    },
    "Mars": {
        "items": "red lentils (masoor), red cloth, copper",
        "weekday": "Tuesday",
        "recipient": "soldiers/braves",
    },
    "Mercury": {
        "items": "green moong, green cloth, emerald-like items",
        "weekday": "Wednesday",
        "recipient": "students",
    },
    "Jupiter": {
        "items": "yellow items, chana dal, gold",
        "weekday": "Thursday",
        "recipient": "teachers/gurus",
    },
    "Venus": {
        "items": "white items, sugar, silk, perfume",
        "weekday": "Friday",
        "recipient": "women/cows",
    },
    "Saturn": {
        "items": "black sesame, mustard oil, iron, black items",
        "weekday": "Saturday",
        "recipient": "poor/elderly/disabled",
    },
    "Rahu": {
        "items": "black blanket, gomedh stone if affordable",
        "weekday": "Saturday evening",
        "recipient": "laborers",
    },
    "Ketu": {
        "items": "multi-colored cloth, mustard oil",
        "weekday": "Tuesday evening",
        "recipient": "ascetics",
    },
}


assert set(DAAN_TABLE.keys()) == set(_PLANETS), (
    "DAAN_TABLE missing planets: "
    f"{set(_PLANETS) - set(DAAN_TABLE.keys())!r}"
)


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=Practitioner field-wisdom (foresightbypriyanka, dkscore, "
    "traditional almanacs)"
)


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _daan_finding(planet: str) -> Finding:
    """Build the daan Finding for one planet."""
    cell = DAAN_TABLE[planet]
    items = cell["items"]
    weekday = cell["weekday"]
    recipient = cell["recipient"]
    verdict = (
        f"{planet} daan: {items} ({weekday}, to {recipient})"
    )[:140]
    evidence = [
        f"planet={planet}",
        f"items={items}",
        f"weekday={weekday}",
        f"recipient={recipient}",
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id=f"practitioner.remedies.daan.{planet.lower()}",
        rule="daan_remedy",
        source_sequence=None,
        classification="primitive",
        direction="positive",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def recommend_daan(afflicted_planets: list[str]) -> list[Finding]:
    """Return one daan Finding per afflicted planet.

    Args:
        afflicted_planets: Ordered iterable of canonical planet names
            (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu).
            Order is preserved; exact duplicates are deduplicated (later
            occurrences dropped) so the output is ID-stable.

    Returns:
        List of Findings with ``id="practitioner.remedies.daan.<planet>"``
        in input order. Empty input yields an empty list.

    Raises:
        ValueError: if any element is not a canonical planet name
            (exact case required).
    """
    seen: set[str] = set()
    out: list[Finding] = []
    for planet in afflicted_planets:
        if planet not in _PLANETS:
            raise ValueError(
                f"unknown planet {planet!r}; must be one of {sorted(_PLANETS)!r}"
            )
        if planet in seen:
            continue
        seen.add(planet)
        out.append(_daan_finding(planet))
    return out


__all__ = ["recommend_daan", "DAAN_TABLE"]
