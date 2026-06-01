"""Tier-2 doctrine: Vipareeta Raja Yoga (trika-lord parivartana).

Doctrine source: Classical Parashari (BPHS Vol.I Ch.36 — Raja Yogas) +
Sanjay Rath, *Crux of Vedic Astrology* (Vipareeta Raja Yoga discussion).

Vipareeta Raja Yoga is the "negation of negation" rule. The 6th, 8th,
and 12th houses are the **trika** (dusthana) houses — each carries a
distinct misfortune signification (enemies/disease, sudden change/death,
loss/expenses). The lords of these houses (the **trika lords**) are
classical malefics by lordship.

When two trika lords engage in **parivartana** (mutual sign-exchange:
lord A sits in lord B's house and lord B sits in lord A's house), the
cumulative misfortune flips into a reversal-yoga that grants
unexpected gains and power — the canonical "Vipareeta" outcome.

Lagna-lord exclusion (the contamination guard)
==============================================

The yoga FIRES only when the lagna lord (1L) does NOT sit in either of
the two exchanged trika houses. If 1L is in the 6th or 8th (etc.) of
the exchanging pair, the self-significator gets dragged into the
dusthana orbit and the reversal is contaminated — classical
commentators (Rath, PVR) demote this case to a non-Vipareeta exchange.

Algorithm
=========

1. Compute the lagna lord (rashi-lord of asc_sign) and the three trika
   lords (6L, 8L, 12L).
2. For each pair {(6L, 8L), (6L, 12L), (8L, 12L)}:
   a. Skip pairs where the two lord names are identical (sometimes a
      single planet rules two trika houses — Aries: Mars rules 1 AND 8,
      Mercury rules 3 AND 6, etc.). A planet cannot exchange with itself.
   b. Skip pairs where one of the trika lords IS the lagna lord (1L
      cannot be a trika lord in the Vipareeta sense).
   c. Compute the two houses involved in the candidate parivartana
      (the two trika houses owned by the pair).
   d. Check parivartana: lord A sits in house B, AND lord B sits in
      house A.
   e. Check lagna-lord exclusion: 1L NOT in either house.
   f. If all hold, emit a Vipareeta Finding.

Whole-sign math (project convention): house = ((sign - asc) % 12) + 1.

Public API
==========

    detect_trika_exchanges(d1_chart, asc_sign) -> list[Finding]
"""
from __future__ import annotations

import logging
from itertools import combinations
from typing import Final, Mapping

from app.core.dignity import SIGN_RULERS
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# The three trika (dusthana) houses.
_TRIKA_HOUSES: Final[tuple[int, ...]] = (6, 8, 12)


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _house_lord(asc_sign: int, house: int) -> str:
    """Return the rashi-lord of the given whole-sign house from asc."""
    sign = ((asc_sign + house - 2) % 12) + 1
    return SIGN_RULERS[sign]


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    return ((planet_sign - asc_sign) % 12) + 1


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _build_finding(
    lord_a: str, house_a: int,
    lord_b: str, house_b: int,
    asc_sign: int,
) -> Finding:
    """Build a Vipareeta Finding for a detected parivartana."""
    # Sort the pair label so id is deterministic regardless of detection
    # order ("jupiter_saturn" not "saturn_jupiter").
    a_name, a_house, b_name, b_house = (
        (lord_a, house_a, lord_b, house_b)
        if lord_a.lower() < lord_b.lower()
        else (lord_b, house_b, lord_a, house_a)
    )
    pair_id = f"{a_name.lower()}_{b_name.lower()}"
    verdict = (
        f"Vipareeta: {a_house}L {a_name} in {_ordinal(b_house)}H + "
        f"{b_house}L {b_name} in {_ordinal(a_house)}H — exchange yoga"
    )
    return Finding(
        id=f"practitioner.trika.vipareeta_{pair_id}",
        rule="vipareeta_raja_yoga",
        source_sequence=None,
        classification="yoga",
        direction="positive",
        verdict=verdict,
        evidence=[
            f"trika_lord_a={lord_a}({house_a}L)",
            f"trika_lord_b={lord_b}({house_b}L)",
            f"parivartana_houses=({house_a},{house_b})",
            f"asc_sign={asc_sign}",
            "doctrine=Classical Parashari + Sanjay Rath Vipareeta Raja Yoga",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_trika_exchanges(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> list[Finding]:
    """Detect Vipareeta Raja Yoga from trika-lord parivartana.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int (1..12), ...}}.
        asc_sign: 1..12 ascendant sign.

    Returns:
        List of Findings for each detected Vipareeta exchange. Empty when
        no exchange (or all candidate exchanges are contaminated by the
        lagna lord sitting in one of the exchanged houses).

    Raises:
        ValueError: if asc_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    lagna_lord = _house_lord(asc_sign, 1)
    trika_lords: dict[int, str] = {
        h: _house_lord(asc_sign, h) for h in _TRIKA_HOUSES
    }

    # Lookup: planet -> current whole-sign house.
    planet_houses: dict[str, int] = {}
    for planet, record in d1_chart.items():
        planet_sign = int(record["sign"])  # type: ignore[arg-type]
        if not 1 <= planet_sign <= 12:
            raise ValueError(
                f"{planet}.sign must be in 1..12, got {planet_sign}"
            )
        planet_houses[planet] = _whole_sign_house(planet_sign, asc_sign)

    findings: list[Finding] = []
    seen_pairs: set[frozenset[str]] = set()
    for house_a, house_b in combinations(_TRIKA_HOUSES, 2):
        lord_a = trika_lords[house_a]
        lord_b = trika_lords[house_b]

        # Skip pairs where the two trika lords are the same planet
        # (a planet cannot exchange with itself).
        if lord_a == lord_b:
            continue
        # Skip pairs where either trika lord IS the lagna lord — the
        # 1L cannot also be a pure trika lord for Vipareeta purposes.
        if lagna_lord in (lord_a, lord_b):
            continue
        # Avoid duplicate detection in the (rare) case the same lord-pair
        # appears via multiple trika-pair enumerations.
        pair_key = frozenset({lord_a, lord_b})
        if pair_key in seen_pairs:
            continue

        # Parivartana check: lord A in house B AND lord B in house A.
        if planet_houses.get(lord_a) != house_b:
            continue
        if planet_houses.get(lord_b) != house_a:
            continue

        # Lagna-lord exclusion: 1L must not sit in either exchanged house.
        lagna_house = planet_houses.get(lagna_lord)
        if lagna_house in (house_a, house_b):
            continue

        seen_pairs.add(pair_key)
        findings.append(_build_finding(
            lord_a, house_a, lord_b, house_b, asc_sign
        ))

    return findings


__all__ = ["detect_trika_exchanges"]
