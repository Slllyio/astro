"""Tier-1 foundation: six-fold house strength per BPHS Ch.28.

Doctrine source: BPHS Vol.II Ch.28 (Bhava-bala Adhyaya).

BPHS Ch.28 defines Bhava-bala as the composite strength of each bhava
(house). It decomposes into three sub-components:

  1. Bhavadhipati-bala  -- the *full Shadbala of the house's lord*. This
                           ties bhava strength to the planetary strength
                           system already computed in
                           ``app.core.shadbala.shadbala_total``.
  2. Bhava-Dig-bala     -- the *directional* strength of the bhava itself.
                           Per BPHS Ch.28, the four directions (East/North/
                           West/South = bhava 1/4/7/10) are weighted by the
                           bhava's intrinsic role. The 4th (Patala / North /
                           midnight) earns the highest weight (60 virupa),
                           the 7th moderate, the 10th the lowest. See
                           ``_BHAVA_DIG_WEIGHTS`` below for the full table.
  3. Bhava-Drishti-bala -- net aspect on the bhava cusp: full aspects from
                           benefics add virupa, full aspects from malefics
                           subtract. The signed sum is divided by 4 to
                           bring it into the virupa scale (mirrors the
                           Drik-bala convention from BPHS 27.38).

Composite total is the sum of the three components (Bhava-Drishti can be
negative, so a heavily afflicted bhava can have a total *below* its
bhavadhipati alone).

Band thresholds (spec):

  - very_strong : total >= 50
  - strong      : 35 <= total < 50
  - moderate    : 20 <= total < 35
  - weak        : total < 20

Direction in the emitted Finding:

  - positive when band in {strong, very_strong}
  - negative when band == weak
  - neutral  when band == moderate

Public API
==========

  compute_bhava_bala(d1_chart, asc_sign, shadbala_components=None)
      -> dict[int, Finding] keyed by house number 1..12.

Each Finding has ``id="foundation.bhava_bala.h<N>"``, classification
``"primitive"``, direction per the band, verdict carrying the composite
value and band tag, and an evidence list spelling out the three sub-
component virupa values.

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> charts = calculate_all_charts(
    ...     year=1990, month=7, day=15, hour=12, minute=0,
    ...     tz_offset=5.5, latitude=12.97, longitude=77.59,
    ... )
    >>> from app.reading.computations.bhava_bala import compute_bhava_bala
    >>> findings = compute_bhava_bala(
    ...     charts["d1"], asc_sign=charts["ascendant"]["sign"],
    ... )
    >>> findings[7].verdict        # doctest: +SKIP
    'House 7 Bhava-bala 42.3 (band: strong)'
"""
from __future__ import annotations

import logging
from typing import Final

from app.core.dignity import SIGN_RULERS
from app.core.shadbala import shadbala_total
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------


# Bhava-Dig-bala weights per BPHS Ch.28. The four cardinal directions are:
#   - 4th house (Patala / North / midnight)     -> 60 virupa (strongest)
#   - 7th house (West / Descendant)             -> 45 virupa
#   - 1st house (East / Lagna)                  -> 30 virupa (also kendra)
#   - 10th house (South / Madhya / midheaven)   ->  0 virupa (weakest by BPHS)
# Other houses interpolate in proportion to their kendra/panaphara/apoklima
# membership. This module's table follows the standard sthaira ratio that
# every kendra except 10 is "naturally strong"; the 10th is the lowest in
# Bhava-Dig because it is the area of greatest external EXPOSURE rather
# than internal STRENGTH (BPHS rationale). The numbers below are scaled
# such that the maximum (4th) caps at 60 virupa.
_BHAVA_DIG_WEIGHTS: Final[dict[int, float]] = {
    1: 30.0,
    2: 25.0,
    3: 20.0,
    4: 60.0,   # max -- North / Patala / midnight
    5: 35.0,
    6: 15.0,
    7: 45.0,   # 7th house (West)
    8: 10.0,
    9: 40.0,
    10: 0.0,   # min -- South / Madhya / midheaven
    11: 25.0,
    12:  5.0,
}


# Benefic / malefic classification mirrors the Drik-bala convention in
# app/core/shadbala.py (BPHS 27.38). Mercury is treated as benefic in the
# Phase-2 simplification (no "becomes malefic when conjunct malefic" rule).
_BENEFIC: Final[frozenset[str]] = frozenset(
    {"Jupiter", "Venus", "Moon", "Mercury"}
)
_MALEFIC: Final[frozenset[str]] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
)


# Band thresholds (descending). The classifier walks this list and returns
# the first label whose threshold is satisfied.
_BAND_THRESHOLDS: Final[tuple[tuple[float, str], ...]] = (
    (50.0, "very_strong"),
    (35.0, "strong"),
    (20.0, "moderate"),
    (-1e12, "weak"),  # sentinel; everything else is weak
)


# 3-vote envelope -- bhava-bala is a single deterministic computation,
# not a 3-pillar judgment.
_FOUNDATION_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _band_for(total: float) -> str:
    """Return the band label for a composite Bhava-bala total."""
    for threshold, label in _BAND_THRESHOLDS:
        if total >= threshold:
            return label
    return "weak"  # unreachable given the sentinel; kept for explicitness


def _direction_for(band: str) -> str:
    """Map band -> Finding.direction enum value."""
    if band in ("strong", "very_strong"):
        return "positive"
    if band == "weak":
        return "negative"
    return "neutral"  # moderate


def _bhava_dig_bala(house: int) -> float:
    """Return Bhava-Dig-bala for a single house per BPHS Ch.28."""
    if not 1 <= house <= 12:
        raise ValueError(f"house out of range: {house!r}")
    return _BHAVA_DIG_WEIGHTS[house]


def _bhavadhipati_bala(
    house: int,
    d1_chart: dict,
    asc_sign: int,
    shadbala_components: dict | None,
) -> float:
    """Shadbala of the house's lord (planet ruling the bhava's rashi).

    Uses pre-computed ``shadbala_components`` if provided; otherwise
    delegates to ``app.core.shadbala.shadbala_total``. Returns 0 virupa
    when the lord's chart entry is missing.
    """
    house_sign = ((asc_sign - 1 + house - 1) % 12) + 1
    lord = SIGN_RULERS[house_sign]

    if shadbala_components is not None and lord in shadbala_components:
        breakdown = shadbala_components[lord]
        return float(breakdown.get("total", 0.0))

    entry = d1_chart.get(lord)
    if not entry:
        return 0.0

    lord_sign = entry.get("sign")
    if not isinstance(lord_sign, int):
        return 0.0
    lord_lon = entry.get("longitude")
    if not isinstance(lord_lon, (int, float)):
        lord_lon = (lord_sign - 1) * 30.0 + 15.0
    lord_d9 = entry.get("d9_sign", lord_sign)
    lord_house = ((lord_sign - asc_sign) % 12) + 1

    breakdown = shadbala_total(
        lord,
        longitude=float(lord_lon),
        d1_sign=lord_sign,
        d9_sign=lord_d9,
        house=lord_house,
        chart=d1_chart,
    )
    return breakdown["total"]


def _full_aspect_on_house(
    aspecter: str, aspecter_house: int, target_house: int
) -> bool:
    """True if planet at ``aspecter_house`` fully aspects ``target_house``.

    Mirrors the universal + planet-specific drishti rules from
    ``app.core.shadbala._aspect_strength_full``: every planet casts the
    7th-house aspect; Mars adds 4/8, Jupiter adds 5/9, Saturn adds 3/10,
    Rahu/Ketu use Jupiter-style 5/9 (locked project convention).
    """
    if aspecter_house == target_house:
        return False  # a planet does not aspect its own house
    distance = ((target_house - aspecter_house) % 12) + 1
    if distance == 7:
        return True
    if aspecter == "Mars" and distance in (4, 8):
        return True
    if aspecter == "Jupiter" and distance in (5, 9):
        return True
    if aspecter == "Saturn" and distance in (3, 10):
        return True
    if aspecter in {"Rahu", "Ketu"} and distance in (5, 9):
        return True
    return False


def _bhava_drishti_bala(
    house: int, d1_chart: dict, asc_sign: int
) -> float:
    """Net aspectual strength on the bhava cusp (BPHS 27.38 convention).

    Each benefic that fully aspects the house contributes +60 virupa;
    each malefic that fully aspects contributes -60. The signed sum is
    divided by 4 to bring it into the virupa scale (matches the
    Drik-bala /4 convention in BPHS 27.38).
    """
    benefic_sum = 0.0
    malefic_sum = 0.0
    for planet, entry in d1_chart.items():
        if planet not in _BENEFIC and planet not in _MALEFIC:
            continue
        planet_sign = entry.get("sign")
        if not isinstance(planet_sign, int):
            continue
        planet_house = ((planet_sign - asc_sign) % 12) + 1
        if not _full_aspect_on_house(planet, planet_house, house):
            continue
        if planet in _BENEFIC:
            benefic_sum += 60.0
        else:
            malefic_sum += 60.0
    return (benefic_sum - malefic_sum) / 4.0


def _verdict_for(house: int, total: float, band: str) -> str:
    """Human-readable one-line verdict for the Finding."""
    return f"House {house} Bhava-bala {total:.1f} (band: {band})"


def _bhava_finding(
    house: int,
    bhavadhipati: float,
    bhava_dig: float,
    bhava_drishti: float,
    total: float,
    band: str,
) -> Finding:
    """Build the Finding for one bhava's composite Bhava-bala."""
    direction = _direction_for(band)
    return Finding(
        id=f"foundation.bhava_bala.h{house}",
        rule="bhava_bala",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=_verdict_for(house, total, band),
        evidence=[
            f"house={house}",
            f"bhavadhipati={bhavadhipati:.2f}",
            f"bhava_dig={bhava_dig:.2f}",
            f"bhava_drishti={bhava_drishti:.2f}",
            f"total={total:.2f}",
            f"band={band}",
            "doctrine=BPHS Ch.28 (six-fold bhava-bala)",
        ],
        confidence=_FOUNDATION_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_bhava_bala(
    d1_chart: dict,
    asc_sign: int,
    shadbala_components: dict | None = None,
) -> dict[int, Finding]:
    """Compute composite Bhava-bala for every house (1..12).

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each entry
            must carry at least ``sign`` (1..12) and (recommended)
            ``longitude``. Used both for the lord's Shadbala and the
            bhava-cusp aspect calculation.
        asc_sign: Ascendant rashi (1=Aries .. 12=Pisces).
        shadbala_components: Optional pre-computed planet -> shadbala-
            breakdown cache. When supplied, keys must be planet names
            and values must be dicts with at least ``total``. When
            ``None``, the function computes per-lord Shadbala on demand.

    Returns:
        Dict keyed by house number (1..12), each value a Finding with
        ``id="foundation.bhava_bala.h<N>"``.

    Raises:
        ValueError: if ``asc_sign`` is not in ``1..12``.

    Example:
        >>> findings = compute_bhava_bala(d1, asc_sign=6)
        >>> findings[1].direction in {"positive", "negative", "neutral"}
        True
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(
            f"asc_sign must be in [1, 12], got {asc_sign!r}"
        )

    out: dict[int, Finding] = {}
    for house in range(1, 13):
        bhavadhipati = _bhavadhipati_bala(
            house, d1_chart, asc_sign, shadbala_components,
        )
        bhava_dig = _bhava_dig_bala(house)
        bhava_drishti = _bhava_drishti_bala(house, d1_chart, asc_sign)
        total = bhavadhipati + bhava_dig + bhava_drishti
        band = _band_for(total)
        out[house] = _bhava_finding(
            house, bhavadhipati, bhava_dig, bhava_drishti, total, band,
        )
    return out


__all__ = [
    "compute_bhava_bala",
]
