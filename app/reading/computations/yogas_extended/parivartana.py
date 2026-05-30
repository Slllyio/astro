"""Practitioner extended yoga: Parivartana (mutual sign exchange).

Doctrine source: BPHS / Phaladeepika — Parivartana Yoga.

Classical rule
==============

Parivartana = mutual sign-exchange between two house lords. The lord of
house A sits in the sign owned by house B's lord, AND the lord of house
B sits in the sign owned by house A's lord. Each pair of houses is
counted ONCE (5↔9 is the same exchange as 9↔5).

Variants
========

- **Maha Parivartana**: between a **Trikona** (1/5/9) and a **Kendra**
  (1/4/7/10) lord — classical Raja Yoga. Also fires for kendra-kendra
  (excluding 1↔1, impossible) and trikona-trikona, as both pairs are
  the auspicious "dharma-artha-axis" exchange.
- **Khala Parivartana**: any other exchange that does NOT involve a
  trika (6/8/12) house — modest exchange yoga.
- **Dainya Parivartana**: an exchange where **exactly one** of the two
  houses is a trika (6/8/12). The other is a non-trika house. Treats
  as a struggle yoga (direction=negative).

Coordination with ``trika_doctrine.py``
=======================================

When **both** houses of the exchange are trika (6/8/12), the
``trika_doctrine.detect_trika_exchanges`` module already emits the
Vipareeta Raja Yoga finding. This module SKIPS those both-trika cases
to avoid double-detection.

Public API
==========

    detect_parivartana(d1_chart, asc_sign) -> list[Finding]

The Finding id pattern is
``practitioner.yogas_extended.parivartana.<houseA>_<houseB>_<variant>``
where houseA < houseB.
"""
from __future__ import annotations

import logging
from itertools import combinations
from typing import Final, Mapping

from app.core.dignity import SIGN_RULERS
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_TRIKONA_HOUSES: Final[frozenset[int]] = frozenset({1, 5, 9})
_KENDRA_HOUSES: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKA_HOUSES: Final[frozenset[int]] = frozenset({6, 8, 12})


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


_DOCTRINE_SENTINEL: Final[str] = (
    "doctrine=BPHS / Phaladeepika Parivartana Yoga "
    "(mutual sign exchange of two house lords)"
)


def _house_lord(asc_sign: int, house: int) -> str:
    sign = ((asc_sign + house - 2) % 12) + 1
    return SIGN_RULERS[sign]


def _whole_sign_house(planet_sign: int, asc_sign: int) -> int:
    return ((planet_sign - asc_sign) % 12) + 1


def _classify_variant(house_a: int, house_b: int) -> str | None:
    """Classify the exchange between ``house_a`` and ``house_b``.

    Returns one of ``"maha"`` / ``"khala"`` / ``"dainya"``, or ``None``
    if the exchange should be SKIPPED (both-trika — handled by
    ``trika_doctrine.py``).
    """
    a_trika = house_a in _TRIKA_HOUSES
    b_trika = house_b in _TRIKA_HOUSES
    if a_trika and b_trika:
        return None  # handled by trika_doctrine
    if a_trika or b_trika:
        return "dainya"
    a_auspicious = (
        house_a in _TRIKONA_HOUSES or house_a in _KENDRA_HOUSES
    )
    b_auspicious = (
        house_b in _TRIKONA_HOUSES or house_b in _KENDRA_HOUSES
    )
    if a_auspicious and b_auspicious:
        return "maha"
    return "khala"


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _build_finding(
    house_a: int, lord_a: str,
    house_b: int, lord_b: str,
    variant: str,
) -> Finding:
    labels = {
        "maha":   "Maha Parivartana",
        "khala":  "Khala Parivartana",
        "dainya": "Dainya Parivartana",
    }
    direction = "negative" if variant == "dainya" else "positive"
    verdict = (
        f"{labels[variant]} — {house_a}L {lord_a} in "
        f"{_ordinal(house_b)}H + {house_b}L {lord_b} in "
        f"{_ordinal(house_a)}H"
    )[:140]
    evidence = [
        f"variant={variant}",
        f"house_a={house_a}",
        f"lord_a={lord_a}",
        f"house_b={house_b}",
        f"lord_b={lord_b}",
        _DOCTRINE_SENTINEL,
    ]
    return Finding(
        id=(
            f"practitioner.yogas_extended.parivartana."
            f"{house_a}_{house_b}_{variant}"
        ),
        rule="parivartana_yoga",
        source_sequence=None,
        classification="yoga",
        direction=direction,
        verdict=verdict,
        evidence=evidence,
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def detect_parivartana(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
) -> list[Finding]:
    """Detect Parivartana yoga (mutual sign-exchange) variants.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int (1..12), ...}}.
        asc_sign: 1..12 ascendant sign.

    Returns:
        Findings list, one per detected exchange (each pair counted once).
        Skips both-trika exchanges (handled by ``trika_doctrine.py``).

    Raises:
        ValueError: if asc_sign is outside 1..12.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")

    # Compute house lord for each of the 12 houses.
    house_lords: dict[int, str] = {
        h: _house_lord(asc_sign, h) for h in range(1, 13)
    }

    # Compute the whole-sign house each planet occupies.
    planet_houses: dict[str, int] = {}
    for planet, record in d1_chart.items():
        sign = record.get("sign")  # type: ignore[union-attr]
        if not isinstance(sign, int) or not 1 <= sign <= 12:
            continue
        planet_houses[planet] = _whole_sign_house(sign, asc_sign)

    findings: list[Finding] = []
    seen_pairs: set[tuple[int, int]] = set()
    for house_a, house_b in combinations(range(1, 13), 2):
        lord_a = house_lords[house_a]
        lord_b = house_lords[house_b]
        # A planet cannot exchange with itself (single planet ruling
        # both houses — e.g. Mars rules Aries (1) and Scorpio (8) for
        # Aries lagna).
        if lord_a == lord_b:
            continue
        # Parivartana: lord_a sits in house_b, lord_b sits in house_a.
        if planet_houses.get(lord_a) != house_b:
            continue
        if planet_houses.get(lord_b) != house_a:
            continue
        variant = _classify_variant(house_a, house_b)
        if variant is None:
            continue  # both-trika — handled by trika_doctrine.
        pair_key = (house_a, house_b)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        findings.append(_build_finding(
            house_a, lord_a, house_b, lord_b, variant,
        ))

    return findings


__all__ = ["detect_parivartana"]
