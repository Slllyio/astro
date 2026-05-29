"""Practitioner remedies: Beej (seed) mantras per planet.

Doctrine source: classical Vedic remedies tradition + practitioner field
wisdom. Beej mantras are single-syllable seed-mantras attached to each
of the 9 grahas. The classical prescription pairs each mantra with a
recommended completion count (e.g. Saturn = 23,000 reps) and a weekday
of practice (the planet's vara/day).

The recommender emits one Finding per afflicted planet — recommendations
ONLY, never judgments. The ``classification`` is ``"primitive"`` and
``direction="neutral"``: mantras are remedial-neutral.

Canonical Beej mantra table (verbatim, do NOT vary transliteration)
===================================================================

  +---------+-----------------------------------------------+--------+----------+
  | Planet  | Mantra                                        | Reps   | Weekday  |
  +=========+===============================================+========+==========+
  | Sun     | Om Hraam Hreem Hraum Sah Suryaya Namah        |   7000 | Sunday   |
  | Moon    | Om Shraam Shreem Shraum Sah Chandraya Namah   |  11000 | Monday   |
  | Mars    | Om Kraam Kreem Kraum Sah Bhaumaya Namah       |  10000 | Tuesday  |
  | Mercury | Om Braam Breem Braum Sah Budhaya Namah        |   9000 | Wednesday|
  | Jupiter | Om Graam Greem Graum Sah Gurave Namah         |  19000 | Thursday |
  | Venus   | Om Draam Dreem Draum Sah Shukraya Namah       |  16000 | Friday   |
  | Saturn  | Om Praam Preem Praum Sah Shanaye Namah        |  23000 | Saturday |
  | Rahu    | Om Bhraam Bhreem Bhraum Sah Rahave Namah      |  18000 | Saturday |
  | Ketu    | Om Sraam Sreem Sraum Sah Ketave Namah         |  17000 | Saturday |
  +---------+-----------------------------------------------+--------+----------+

Public API
==========

    recommend_mantras(afflicted_planets) -> list[Finding]
    BEEJ_MANTRA_TABLE: Final[dict[str, dict[str, str | int]]]
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


# Canonical table — frozen at module-import time. Verbatim transliteration
# (Roman-alphabet ITRANS-ish). Do NOT introduce alternative spellings.
BEEJ_MANTRA_TABLE: Final[dict[str, dict[str, str | int]]] = {
    "Sun": {
        "mantra": "Om Hraam Hreem Hraum Sah Suryaya Namah",
        "reps": 7000,
        "weekday": "Sunday",
    },
    "Moon": {
        "mantra": "Om Shraam Shreem Shraum Sah Chandraya Namah",
        "reps": 11000,
        "weekday": "Monday",
    },
    "Mars": {
        "mantra": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
        "reps": 10000,
        "weekday": "Tuesday",
    },
    "Mercury": {
        "mantra": "Om Braam Breem Braum Sah Budhaya Namah",
        "reps": 9000,
        "weekday": "Wednesday",
    },
    "Jupiter": {
        "mantra": "Om Graam Greem Graum Sah Gurave Namah",
        "reps": 19000,
        "weekday": "Thursday",
    },
    "Venus": {
        "mantra": "Om Draam Dreem Draum Sah Shukraya Namah",
        "reps": 16000,
        "weekday": "Friday",
    },
    "Saturn": {
        "mantra": "Om Praam Preem Praum Sah Shanaye Namah",
        "reps": 23000,
        "weekday": "Saturday",
    },
    "Rahu": {
        "mantra": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
        "reps": 18000,
        "weekday": "Saturday",
    },
    "Ketu": {
        "mantra": "Om Sraam Sreem Sraum Sah Ketave Namah",
        "reps": 17000,
        "weekday": "Saturday",
    },
}


# Table integrity assertion at module load.
assert set(BEEJ_MANTRA_TABLE.keys()) == set(_PLANETS), (
    "BEEJ_MANTRA_TABLE missing planets: "
    f"{set(_PLANETS) - set(BEEJ_MANTRA_TABLE.keys())!r}"
)


# Recommendations are not 3-pillar judgments, so the confidence envelope
# is the indicative_only sentinel used elsewhere in the practitioner tier.
_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _mantra_finding(planet: str) -> Finding:
    """Build the Finding for one (planet -> Beej mantra) recommendation."""
    cell = BEEJ_MANTRA_TABLE[planet]
    mantra = cell["mantra"]
    reps = cell["reps"]
    weekday = cell["weekday"]
    verdict = (
        f"Mantra for {planet}: {mantra} ({reps} reps, {weekday})"
    )[:140]
    evidence = [
        f"planet={planet}",
        f"mantra={mantra}",
        f"reps={reps}",
        f"weekday={weekday}",
        "doctrine=classical Vedic remedies tradition + practitioner field wisdom",
    ]
    return Finding(
        id=f"practitioner.remedies.mantra.{planet.lower()}",
        rule="mantra_remedy",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def recommend_mantras(afflicted_planets: list[str]) -> list[Finding]:
    """Return one Beej-mantra Finding per afflicted planet.

    Args:
        afflicted_planets: Ordered iterable of canonical planet names
            (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu).
            Order is preserved; exact duplicates are deduplicated (later
            occurrences dropped) to keep the output ID-stable.

    Returns:
        List of Findings with ``id="practitioner.remedies.mantra.<planet>"``
        in the same order as the (deduplicated) input. Empty input
        returns an empty list.

    Raises:
        ValueError: if any element of ``afflicted_planets`` is not a
            canonical planet name (exact case required).
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
        out.append(_mantra_finding(planet))
    return out


__all__ = ["recommend_mantras", "BEEJ_MANTRA_TABLE"]
