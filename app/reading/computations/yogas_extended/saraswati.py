"""Practitioner extended yoga: Saraswati Yoga (Phaladeepika).

Doctrine source: Phaladeepika (Mantreshwara) — Saraswati Yoga.

Classical rule
==============

Saraswati Yoga indicates extreme scholarly, literary, and artistic
talent — the blessings of Saraswati (the goddess of knowledge). It
forms when:

    **Mercury, Jupiter, AND Venus** each occupy a **kendra** (1/4/7/10),
    **kona** (5/9), or the **2nd house** from lagna — i.e. each sits in
    the qualifying-house set {1, 2, 4, 5, 7, 9, 10} — AND **at least
    one of the three** is in its own sign or exaltation.

The qualifying-house set unifies kendra+kona+2H per Phaladeepika's
verse "kendra-trikona-dvitiya-sthita". The dignity gate
(one-of-three in own/exalted) distinguishes Saraswati from a weaker
echo placement.

Public API
==========

    detect_saraswati(d1_chart, asc_sign) -> list[Finding]

ID pattern: ``practitioner.yogas_extended.saraswati.detected``.
classification="yoga", direction="positive".
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# The three benefics whose joint placement defines Saraswati.
_SARASWATI_PLANETS: Final[tuple[str, ...]] = ("Mercury", "Jupiter", "Venus")

# Qualifying-house set per Phaladeepika: kendra + kona + 2H.
_QUALIFYING_HOUSES: Final[frozenset[int]] = frozenset({1, 2, 4, 5, 7, 9, 10})

# Exaltation signs (BPHS Ch.3 v.40).
_EXALTATION: Final[dict[str, int]] = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7,
}

# Own signs (BPHS Ch.3).
_OWN_SIGNS: Final[dict[str, frozenset[int]]] = {
    "Sun":     frozenset({5}),
    "Moon":    frozenset({4}),
    "Mars":    frozenset({1, 8}),
    "Mercury": frozenset({3, 6}),
    "Jupiter": frozenset({9, 12}),
    "Venus":   frozenset({2, 7}),
    "Saturn":  frozenset({10, 11}),
}


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=Phaladeepika Saraswati Yoga (Mer+Jup+Ven in 1/2/4/5/7/9/10)"
)


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    return ((planet_sign - asc_sign) % 12) + 1


def _is_dignified(planet: str, sign: int) -> bool:
    if sign == _EXALTATION.get(planet):
        return True
    if sign in _OWN_SIGNS.get(planet, frozenset()):
        return True
    return False


def _dignity_label(planet: str, sign: int) -> str:
    if sign == _EXALTATION.get(planet):
        return "exalted"
    if sign in _OWN_SIGNS.get(planet, frozenset()):
        return "own"
    return "neutral"


def _planet_sign(
    d1_chart: Mapping[str, Mapping[str, object]], planet: str,
) -> int | None:
    entry = d1_chart.get(planet)
    if not entry:
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not 1 <= sign <= 12:
        return None
    return sign


def _build_finding(
    placements: list[tuple[str, int, int, str]],
) -> Finding:
    """Construct Finding from per-planet (planet, sign, house, dignity)."""
    parts_str = "+".join(
        f"{p}({house}H,{dignity})" for p, _, house, dignity in placements
    )
    verdict = (
        f"Saraswati Yoga — Mer/Jup/Ven in 1/2/4/5/7/9/10 from lagna; "
        f"{parts_str} (scholarship, arts)"
    )[:140]
    evidence = [
        f"planets={[p for p, _, _, _ in placements]!r}",
        *[
            f"{p}_sign={sign}" for p, sign, _, _ in placements
        ],
        *[
            f"{p}_house={house}" for p, _, house, _ in placements
        ],
        *[
            f"{p}_dignity={dignity}" for p, _, _, dignity in placements
        ],
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id="practitioner.yogas_extended.saraswati.detected",
        rule="saraswati_yoga",
        source_sequence=None,
        classification="yoga",
        direction="positive",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_saraswati(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> list[Finding]:
    """Detect Saraswati Yoga per Phaladeepika.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int, ...}}.
        asc_sign: 1..12 ascendant sign.

    Returns:
        A list with at most ONE Finding. Empty when not all three
        benefics sit in {1,2,4,5,7,9,10} from lagna, OR when none of
        the three is in own/exalted dignity.

    Raises:
        ValueError: if asc_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    placements: list[tuple[str, int, int, str]] = []
    for planet in _SARASWATI_PLANETS:
        sign = _planet_sign(d1_chart, planet)
        if sign is None:
            return []
        house = _whole_sign_house(sign, asc_sign)
        if house not in _QUALIFYING_HOUSES:
            return []
        placements.append((planet, sign, house, _dignity_label(planet, sign)))

    # Dignity gate: at least one of the three must be own/exalted.
    if not any(_is_dignified(p, s) for p, s, _, _ in placements):
        return []

    return [_build_finding(placements)]


__all__ = ["detect_saraswati"]
