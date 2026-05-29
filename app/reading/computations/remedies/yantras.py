"""Practitioner remedies: yantras (geometric diagrams) per planet.

Doctrine source: Practitioner field-wisdom (foresightbypriyanka, dkscore,
traditional almanacs). Yantras are geometric diagrams installed at home
to pacify a planet. Each graha has a canonical Sanskrit-named yantra,
a traditional installation direction, and a recommended metal substrate.

Canonical table (verbatim):

  +---------+--------------------+----------+------------------+
  | Planet  | Yantra             | Direction| Substrate        |
  +=========+====================+==========+==================+
  | Sun     | Surya Yantra       | east     | copper plate     |
  | Moon    | Chandra Yantra     | north-west| silver plate    |
  | Mars    | Mangal Yantra      | south    | copper plate     |
  | Mercury | Budha Yantra       | north    | brass plate      |
  | Jupiter | Guru Yantra        | north-east| gold/yellow plate|
  | Venus   | Shukra Yantra      | south-east| silver plate    |
  | Saturn  | Shani Yantra       | west     | iron plate       |
  | Rahu    | Rahu Yantra        | south-west| mixed-metal     |
  | Ketu    | Ketu Yantra        | south    | mixed-metal      |
  +---------+--------------------+----------+------------------+

Public API
==========

    recommend_yantras(afflicted_planets) -> list[Finding]
    YANTRA_TABLE: Final[dict[str, dict[str, str]]]
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


# Canonical yantra table — frozen at module load.
YANTRA_TABLE: Final[dict[str, dict[str, str]]] = {
    "Sun": {
        "name": "Surya Yantra",
        "placement": "east wall",
        "substrate": "copper plate",
    },
    "Moon": {
        "name": "Chandra Yantra",
        "placement": "north-west wall",
        "substrate": "silver plate",
    },
    "Mars": {
        "name": "Mangal Yantra",
        "placement": "south wall",
        "substrate": "copper plate",
    },
    "Mercury": {
        "name": "Budha Yantra",
        "placement": "north wall",
        "substrate": "brass plate",
    },
    "Jupiter": {
        "name": "Guru Yantra",
        "placement": "north-east wall",
        "substrate": "gold/yellow plate",
    },
    "Venus": {
        "name": "Shukra Yantra",
        "placement": "south-east wall",
        "substrate": "silver plate",
    },
    "Saturn": {
        "name": "Shani Yantra",
        "placement": "west wall",
        "substrate": "iron plate",
    },
    "Rahu": {
        "name": "Rahu Yantra",
        "placement": "south-west wall",
        "substrate": "mixed-metal plate",
    },
    "Ketu": {
        "name": "Ketu Yantra",
        "placement": "south wall",
        "substrate": "mixed-metal plate",
    },
}


assert set(YANTRA_TABLE.keys()) == set(_PLANETS), (
    "YANTRA_TABLE missing planets: "
    f"{set(_PLANETS) - set(YANTRA_TABLE.keys())!r}"
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


def _yantra_finding(planet: str) -> Finding:
    """Build a yantra Finding for one planet."""
    cell = YANTRA_TABLE[planet]
    name = cell["name"]
    placement = cell["placement"]
    substrate = cell["substrate"]
    verdict = (
        f"{name} ({planet}) - install on {placement} ({substrate})"
    )[:140]
    evidence = [
        f"planet={planet}",
        f"yantra={name}",
        f"placement={placement}",
        f"substrate={substrate}",
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id=f"practitioner.remedies.yantra.{planet.lower()}",
        rule="yantra_remedy",
        source_sequence=None,
        classification="primitive",
        direction="positive",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def recommend_yantras(afflicted_planets: list[str]) -> list[Finding]:
    """Return one yantra Finding per afflicted planet.

    Args:
        afflicted_planets: Ordered iterable of canonical planet names.
            Duplicates are dropped (first-occurrence wins); order
            preserved.

    Returns:
        List of Findings with id ``practitioner.remedies.yantra.<planet>``.

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
        out.append(_yantra_finding(planet))
    return out


__all__ = ["recommend_yantras", "YANTRA_TABLE"]
