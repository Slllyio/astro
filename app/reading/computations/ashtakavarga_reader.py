"""Tier-1 foundation: Ashtakavarga interpretive layer per Phaladeepika Ch.23-24.

Doctrine source: Phaladeepika Ch.23-24 (Mantreswara) -- Ashtakavarga
phaladhyaya & transit interpretation.

The raw BAV (Bhinnashtakavarga) and SAV (Sarvashtakavarga) bindu tables
are computed by ``app.core.ashtakavarga.compute_ashtakavarga``. This
module applies the classical interpretive thresholds from Phaladeepika
Ch.23-24:

SAV (Sarvashtakavarga) bands -- per house
==========================================

  - bindus >= 31  -> ``strong``    (positive direction; favourable bhava)
  - bindus 25-30  -> ``moderate``  (neutral; mixed results)
  - bindus < 25   -> ``weak``      (negative direction; obstructed bhava)

These thresholds come from Phaladeepika 23.10-12 (and BPHS 41.5-7): the
SAV total for the 12 signs sums to 337 (an empirically fixed number); a
mean per sign is ~28, so houses above 30 are "above-average favourable"
and houses below 25 fall into the "transit-disabled" band.

BAV (Bhinnashtakavarga) per planet per house
============================================

For interpreting transits, Phaladeepika 24.4-9 introduces the rule that
a transiting planet T needs **>= 4 bindus** in its own BAV row at the
sign it currently transits to deliver house-significant results. When
its bindu count there is below 4, the transit is "weak" (the planet may
still travel through that house, but classical doctrine demotes the
strength of its effects).

Reader output keys
==================

  - ``sav_house_<N>``         for N in 1..12  -- one Finding per bhava
  - ``bav_<planet>_house_<N>`` for planet in (Sun..Saturn), N in 1..12
                                              -- one Finding per (planet, house)

That is 12 + 7*12 = 96 Findings. Lunar nodes are not BAV contributors
per classical Ashtakavarga (BPHS 41.2-3) and are therefore absent from
the BAV grid.

Public API
==========

  read_ashtakavarga(d1_chart, asc_sign) -> dict[str, Finding]

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> charts = calculate_all_charts(
    ...     year=1990, month=7, day=15, hour=12, minute=0,
    ...     tz_offset=5.5, latitude=12.97, longitude=77.59,
    ... )
    >>> from app.reading.computations.ashtakavarga_reader import (
    ...     read_ashtakavarga,
    ... )
    >>> readings = read_ashtakavarga(
    ...     charts["d1"], asc_sign=charts["ascendant"]["sign"],
    ... )
    >>> "sav_house_1" in readings
    True
"""
from __future__ import annotations

import logging
from typing import Final

from app.core.ashtakavarga import BAV_PLANETS, compute_ashtakavarga
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thresholds (Phaladeepika Ch.23-24)
# ---------------------------------------------------------------------------

# SAV-per-house bands.
_SAV_STRONG_MIN: Final[int] = 31
_SAV_MODERATE_MIN: Final[int] = 25

# BAV-per-house transit-capability threshold.
_BAV_TRANSIT_MIN: Final[int] = 4


_FOUNDATION_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Band helpers
# ---------------------------------------------------------------------------


def _sav_band(bindus: int) -> str:
    """Phaladeepika Ch.23 -- per-house SAV interpretive bucket."""
    if bindus >= _SAV_STRONG_MIN:
        return "strong"
    if bindus >= _SAV_MODERATE_MIN:
        return "moderate"
    return "weak"


def _bav_band(bindus: int) -> str:
    """Phaladeepika Ch.24 -- transit-capability bucket for BAV."""
    return "transit_capable" if bindus >= _BAV_TRANSIT_MIN else "weak"


def _sav_direction(band: str) -> str:
    if band == "strong":
        return "positive"
    if band == "weak":
        return "negative"
    return "neutral"


def _bav_direction(band: str) -> str:
    return "positive" if band == "transit_capable" else "negative"


# ---------------------------------------------------------------------------
# House <-> sign rotation
# ---------------------------------------------------------------------------


def _sign_for_house(asc_sign: int, house: int) -> int:
    """1-indexed rashi falling in the requested whole-sign house from lagna."""
    return ((asc_sign - 1 + house - 1) % 12) + 1


# ---------------------------------------------------------------------------
# Finding builders
# ---------------------------------------------------------------------------


def _parse_bindus(finding: Finding) -> int:
    """Test-helper: pull the bindu count out of a Finding's evidence."""
    for line in finding.evidence:
        if line.startswith("bindus="):
            return int(line[len("bindus="):])
    raise KeyError("bindus= not found in evidence")


def _sav_finding(house: int, sign: int, bindus: int) -> Finding:
    band = _sav_band(bindus)
    direction = _sav_direction(band)
    key = f"sav_house_{house}"
    return Finding(
        id=f"foundation.ashtakavarga_reader.{key}",
        rule="sav_house",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=f"SAV house {house} (sign {sign}) bindus={bindus} band={band}",
        evidence=[
            f"house={house}",
            f"sign={sign}",
            f"bindus={bindus}",
            f"band={band}",
            "doctrine=Phaladeepika Ch.23 Ashtakavarga (SAV per house)",
        ],
        confidence=_FOUNDATION_CONFIDENCE,
    )


def _bav_finding(
    planet: str, house: int, sign: int, bindus: int,
) -> Finding:
    band = _bav_band(bindus)
    direction = _bav_direction(band)
    key = f"bav_{planet.lower()}_house_{house}"
    return Finding(
        id=f"foundation.ashtakavarga_reader.{key}",
        rule="bav_house",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=(
            f"BAV {planet} house {house} bindus={bindus} band={band}"
        ),
        evidence=[
            f"planet={planet}",
            f"house={house}",
            f"sign={sign}",
            f"bindus={bindus}",
            f"band={band}",
            "doctrine=Phaladeepika Ch.24 Ashtakavarga (BAV transit capability)",
        ],
        confidence=_FOUNDATION_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_ashtakavarga(
    d1_chart: dict, asc_sign: int,
) -> dict[str, Finding]:
    """Apply Phaladeepika Ch.23-24 interpretive layer over BAV + SAV.

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each entry
            must carry a 1..12 ``sign``.
        asc_sign: Ascendant rashi (1..12).

    Returns:
        Dict of 12 SAV-per-house Findings plus 84 BAV-per-house Findings,
        keyed by ``sav_house_<N>`` and ``bav_<planet>_house_<N>``.

    Raises:
        ValueError: if ``asc_sign`` is not in ``1..12``.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(
            f"asc_sign must be in [1, 12], got {asc_sign!r}"
        )

    ascendant = {"sign": asc_sign}
    av = compute_ashtakavarga(d1_chart, ascendant)
    sav: list[int] = list(av["sav"])
    bav_per_planet: dict[str, list[int]] = dict(av["bav_per_planet"])

    out: dict[str, Finding] = {}

    # SAV-per-house: rotate the 12-sign SAV vector by asc_sign so house 1
    # picks the lagna's rashi.
    for house in range(1, 13):
        sign = _sign_for_house(asc_sign, house)
        bindus = int(sav[sign - 1])
        key = f"sav_house_{house}"
        out[key] = _sav_finding(house, sign, bindus)

    # BAV-per-house: same rotation, per BAV planet.
    for planet in BAV_PLANETS:
        bav_row = bav_per_planet.get(planet, [0] * 12)
        for house in range(1, 13):
            sign = _sign_for_house(asc_sign, house)
            bindus = int(bav_row[sign - 1])
            key = f"bav_{planet.lower()}_house_{house}"
            out[key] = _bav_finding(planet, house, sign, bindus)

    return out


__all__ = [
    "read_ashtakavarga",
]
