"""Practitioner extended yoga: Daridra Yoga (Phaladeepika).

Doctrine source: Phaladeepika (Mantreshwara) — Daridra Yoga.

Classical rule
==============

Daridra Yoga is a poverty / struggle indicator — the inverse of
Lakshmi / fortune yogas. The 11th house signifies income, gains, and
ambitions fulfilled. When its lord (11L) is trapped in a **dusthana**
(6th, 8th, or 12th house), the gains-bringer is locked in houses of
disease/enemies, sudden change/death, and loss/expenses — gains are
delayed, eaten by debts, or never materialise.

Formation rule:

    The **11th-house lord** (11L) is placed in the **6th, 8th, or 12th
    house** from the lagna, AND there is no Vipareeta cancellation.

Vipareeta cancellation
======================

Phaladeepika notes that if the 11L participating in this configuration
ALSO has lagna-lord co-rulership (i.e. 11L == 1L), the placement reads
as a Vipareeta Raja Yoga candidate rather than as a pure Daridra. The
ascendant lord in a dusthana is the foundation of Vipareeta Raja Yoga;
treating it as Daridra would double-count against the
:mod:`app.reading.computations.trika_doctrine` detector.

Note: 1L==11L is classically impossible for any of the 12 Vedic lagnas
under the standard sign-rulership map (BPHS Ch.3), so the guard is
defensive — it costs nothing and documents the doctrine intent.

Public API
==========

    detect_daridra(d1_chart, asc_sign) -> list[Finding]

ID pattern: ``practitioner.yogas_extended.daridra.detected``.
classification="yoga", direction="negative" (affliction-yoga).
"""
from __future__ import annotations

import logging
from typing import Final, Mapping

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Sign rulers (BPHS Vol.I Ch.3).
_SIGN_RULERS: Final[dict[int, str]] = {
    1: "Mars",     2: "Venus",   3: "Mercury", 4: "Moon",
    5: "Sun",      6: "Mercury", 7: "Venus",   8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

_DUSTHANAS: Final[frozenset[int]] = frozenset({6, 8, 12})


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)

_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=Phaladeepika Daridra Yoga (11L in 6/8/12 dusthana)"
)


def _house_lord(asc_sign: int, house: int) -> str:
    sign = ((asc_sign - 1 + house - 1) % 12) + 1
    return _SIGN_RULERS[sign]


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    return ((planet_sign - asc_sign) % 12) + 1


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
    eleventh_lord: str, sign: int, house: int, asc_sign: int,
) -> Finding:
    verdict = (
        f"Daridra Yoga — 11L {eleventh_lord} in {house}H "
        f"dusthana (income struggles, debts)"
    )[:140]
    evidence = [
        f"11L={eleventh_lord}",
        f"11L_sign={sign}",
        f"11L_house={house}",
        f"asc_sign={asc_sign}",
        "dusthana=6/8/12",
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id="practitioner.yogas_extended.daridra.detected",
        rule="daridra_yoga",
        source_sequence=None,
        classification="yoga",
        direction="negative",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_daridra(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> list[Finding]:
    """Detect Daridra Yoga per Phaladeepika.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int, ...}}.
        asc_sign: 1..12 ascendant sign.

    Returns:
        A list with at most ONE Finding. Empty when the 11L is not in
        a dusthana (6/8/12) from lagna, when 11L is missing from the
        chart, or when the Vipareeta-suppression gate fires (11L == 1L).

    Raises:
        ValueError: if asc_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    eleventh_lord = _house_lord(asc_sign, 11)
    lagna_lord = _house_lord(asc_sign, 1)

    # Defensive Vipareeta-suppression: classically impossible for the 12
    # Vedic lagnas, but documents the doctrine intent. If 11L == 1L,
    # delegate to trika_doctrine / vipareeta detection.
    if eleventh_lord == lagna_lord:
        return []

    sign = _planet_sign(d1_chart, eleventh_lord)
    if sign is None:
        return []

    house = _whole_sign_house(sign, asc_sign)
    if house not in _DUSTHANAS:
        return []

    return [_build_finding(eleventh_lord, sign, house, asc_sign)]


__all__ = ["detect_daridra"]
