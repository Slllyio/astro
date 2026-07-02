"""Doctrine-relevance scorer — the base (karaka-laden) variant.

Reconstructed from its contract (``tests/test_dasha_doctrine_scorers.py`` and
the consumers ``dasha_doctrine_structural.py`` / ``dasha_doctrine_pooled.py``).
The original source module was never committed to the repo; this restores the
documented behaviour so the Round-11 doctrine-RR pipeline imports and runs.

The relevance of a Vimshottari dasha *lord* to an *event class*, given a natal
chart, decomposes into three additive parts:

    doctrine_relevance(L, E, chart) = HR(L, E, chart)     # house resonance
                                    + KR(L, E)            # karaka (chart-independent)
                                    + func_mod(L, chart)  # functional benefic/malefic

- **HR** is chart-dependent: how strongly the lord relates (by occupancy,
  rulership, aspect) to the houses that matter for the event class.
- **KR** is chart-*independent*: the natural significator boost (e.g. Venus for
  marriage, Saturn for death). This is the term the "structural" (karaka-
  stripped) variant drops, so that shuffling charts fully reshuffles the score.
- **func_mod** is chart-dependent: a small benefic/malefic nudge from the
  lord's functional nature (which houses it rules).

House weights (``_HOUSE_MAP``) follow the classical functional-house mapping
already encoded in ``app/medini/ml/survival_analysis.py``
(``EVENT_FUNCTIONAL_HOUSES``): marriage→7, career→10, death→8 (longevity), etc.
Karaka weights (``_KARAKA_MAP``) follow ``EVENT_KARAKAS`` there.
"""
from __future__ import annotations

from typing import Final, Mapping

# --------------------------------------------------------------------------- #
# House classification                                                         #
# --------------------------------------------------------------------------- #

_TRIKONA: Final[frozenset[int]] = frozenset({1, 5, 9})
_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_DUSTHANA: Final[frozenset[int]] = frozenset({6, 8, 12})

# Weight of a house-relation channel relative to occupancy.
_OCC_WEIGHT: Final[float] = 1.0
_RULE_WEIGHT: Final[float] = 1.0
_ASPECT_WEIGHT: Final[float] = 0.5


# --------------------------------------------------------------------------- #
# Event-class → house weights (HR) and karaka weights (KR)                     #
# --------------------------------------------------------------------------- #

# Which bhavas carry signal for each event class, and how much. Mirrors the
# classical functional-house mapping (BPHS / Phaladeepika consensus). Houses
# absent from a class's dict contribute 0.
_HOUSE_MAP: Final[Mapping[str, Mapping[int, float]]] = {
    "marriage":                {7: 1.0, 2: 0.5, 11: 0.3},
    "relationships":           {7: 1.0, 5: 0.5},
    "relationship":            {7: 1.0, 5: 0.5},
    "career":                  {10: 1.0, 6: 0.5, 11: 0.3, 2: 0.3},
    "work":                    {10: 1.0, 6: 0.5},
    "fame":                    {10: 1.0, 11: 0.5},
    # Death / longevity: 8th = longevity axis, 6th = disease, 2nd & 7th are the
    # classical maraka houses. (See docs/death_timing_findings.md §3.)
    "death":                   {8: 1.0, 6: 0.5, 2: 0.3, 7: 0.3},
    "death_cause_unspecified": {8: 1.0, 6: 0.5, 2: 0.3, 7: 0.3},
    "death by disease":        {8: 1.0, 6: 0.8},
    "health":                  {1: 1.0, 6: 0.5},
    "personal":                {1: 1.0, 4: 0.5, 5: 0.3},
    "family":                  {4: 1.0, 2: 0.5},
    "education":               {5: 1.0, 9: 0.5},
}

# Natural significators (chart-independent). Weight is the KR boost the lord
# receives when a dasha of that lord is scored for the event class.
_KARAKA_MAP: Final[Mapping[str, Mapping[str, float]]] = {
    "marriage":                {"Venus": 1.0, "Jupiter": 0.5},
    "relationships":           {"Venus": 1.0, "Mars": 0.5},
    "relationship":            {"Venus": 1.0, "Mars": 0.5},
    "career":                  {"Saturn": 1.0, "Sun": 0.5},
    "work":                    {"Saturn": 1.0, "Sun": 0.5},
    "fame":                    {"Sun": 1.0, "Jupiter": 0.5},
    "death":                   {"Saturn": 1.0},
    "death_cause_unspecified": {"Saturn": 1.0},
    "death by disease":        {"Saturn": 1.0, "Mars": 0.5},
    "health":                  {"Sun": 1.0, "Mars": 0.5},
    "personal":                {"Moon": 1.0},
    "family":                  {"Moon": 1.0, "Jupiter": 0.5},
    "education":               {"Mercury": 1.0, "Jupiter": 0.5},
}


# --------------------------------------------------------------------------- #
# Component scorers                                                            #
# --------------------------------------------------------------------------- #

def _int_or_none(v: object) -> int | None:
    try:
        if v is None:
            return None
        return int(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _house_resonance(
    lord: str, hmap: Mapping[int, float], natal_row: Mapping[str, object],
) -> float:
    """Chart-dependent house resonance of ``lord`` for a given house-weight map.

    Sums the event's house weights across the three ways a planet "touches" a
    house in this chart: occupancy, rulership, and (half-weighted) graha
    drishti. ``natal_row`` uses the ``occ_<lord>`` / ``rules_<lord>`` /
    ``aspects_<lord>`` convention from ``natal_lord_houses.parquet``.
    """
    l = lord.lower()
    score = 0.0
    occ = _int_or_none(natal_row.get(f"occ_{l}"))
    if occ is not None:
        score += _OCC_WEIGHT * hmap.get(occ, 0.0)
    for h in natal_row.get(f"rules_{l}", []) or []:
        hi = _int_or_none(h)
        if hi is not None:
            score += _RULE_WEIGHT * hmap.get(hi, 0.0)
    for h in natal_row.get(f"aspects_{l}", []) or []:
        hi = _int_or_none(h)
        if hi is not None:
            score += _ASPECT_WEIGHT * hmap.get(hi, 0.0)
    return score


def _functional_modifier(lord: str, natal_row: Mapping[str, object]) -> float:
    """Small benefic/malefic nudge from the lord's functional nature.

    A planet ruling a trikona (1/5/9) is functionally benefic (+); ruling a
    dusthana (6/8/12) is functionally malefic (−). Chart-dependent, so it
    reshuffles under chart permutation.
    """
    mod = 0.0
    for h in natal_row.get(f"rules_{lord.lower()}", []) or []:
        hi = _int_or_none(h)
        if hi is None:
            continue
        if hi in _TRIKONA:
            mod += 0.25
        if hi in _DUSTHANA:
            mod -= 0.25
    return mod


def _karaka_relevance(lord: str, event_class: str) -> float:
    """Chart-independent natural-significator weight (the KR term)."""
    return _KARAKA_MAP.get(event_class, {}).get(lord, 0.0)


def doctrine_relevance(
    lord: str, event_class: str, natal_row: Mapping[str, object],
) -> float:
    """Full relevance = HR + KR + func_mod."""
    hmap = _HOUSE_MAP.get(event_class, {})
    hr = _house_resonance(lord, hmap, natal_row)
    kr = _karaka_relevance(lord, event_class)
    fm = _functional_modifier(lord, natal_row)
    return hr + kr + fm
