"""Bhinnashtakavarga (BAV) and Sarvashtakavarga (SAV) per Parashari tradition.

For each of the 7 traditional planets P and each of the 8 contributors C
(7 planets + Lagna), a sign S receives 1 bindu in P's BAV iff S is at one
of the canonical "favorable" house-offsets from C's natal sign. The offset
table is the standard Brihat Parashara Hora Shastra table.

Conventions:
  - Sign indices internally: 0-based for list access (Aries=0, ..., Pisces=11).
  - External `sign` keys on the d1 / ascendant dicts are 1-based (1..12),
    matching `app.core.ephemeris_engine`.
  - Rahu/Ketu do NOT have their own BAV in classical Ashtakavarga and are
    NOT contributors. The 7 BAV planets are Sun..Saturn.
  - The Lagna's contribution comes from `ascendant["sign"]`, not any planet.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

# Order is the row order of the BAV matrix.
BAV_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)

BAV_CONTRIBUTORS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna",
)

# Benefic-house offsets, 1-indexed from each contributor's natal sign.
# Ported verbatim from portal/astro_probability_engine/astrology/bav_rules.py.
_BENEFIC_OFFSETS: dict[str, dict[str, tuple[int, ...]]] = {
    "Sun": {
        "Sun":     (1, 2, 4, 7, 8, 9, 10, 11),
        "Moon":    (3, 6, 10, 11),
        "Mars":    (1, 2, 4, 7, 8, 9, 10, 11),
        "Mercury": (3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (5, 6, 9, 11),
        "Venus":   (6, 7, 12),
        "Saturn":  (1, 2, 4, 7, 8, 9, 10, 11),
        "Lagna":   (3, 4, 6, 10, 11, 12),
    },
    "Moon": {
        "Sun":     (3, 6, 7, 8, 10, 11),
        "Moon":    (1, 3, 6, 7, 10, 11),
        "Mars":    (2, 3, 5, 6, 9, 10, 11),
        "Mercury": (1, 3, 4, 5, 7, 8, 10, 11),
        "Jupiter": (1, 4, 7, 8, 10, 11, 12),
        "Venus":   (3, 4, 5, 7, 9, 10, 11),
        "Saturn":  (3, 5, 6, 11),
        "Lagna":   (3, 6, 10, 11),
    },
    "Mars": {
        "Sun":     (3, 5, 6, 10, 11),
        "Moon":    (3, 6, 11),
        "Mars":    (1, 2, 4, 7, 8, 9, 10, 11),
        "Mercury": (3, 5, 6, 11),
        "Jupiter": (6, 10, 11, 12),
        "Venus":   (6, 8, 11, 12),
        "Saturn":  (1, 4, 7, 8, 9, 10, 11),
        "Lagna":   (1, 3, 6, 10, 11),
    },
    "Mercury": {
        "Sun":     (5, 6, 9, 11, 12),
        "Moon":    (2, 4, 6, 8, 10, 11),
        "Mars":    (1, 2, 4, 7, 8, 9, 10, 11),
        "Mercury": (1, 3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (6, 8, 11, 12),
        "Venus":   (1, 2, 3, 4, 5, 8, 9, 11),
        "Saturn":  (1, 2, 4, 7, 8, 9, 10, 11),
        "Lagna":   (1, 2, 4, 6, 8, 10, 11),
    },
    "Jupiter": {
        "Sun":     (1, 2, 3, 4, 7, 8, 9, 10, 11),
        "Moon":    (2, 5, 7, 9, 11),
        "Mars":    (1, 2, 4, 7, 8, 10, 11),
        "Mercury": (1, 2, 4, 5, 6, 9, 10, 11),
        "Jupiter": (1, 2, 3, 4, 7, 8, 10, 11),
        "Venus":   (2, 5, 6, 9, 10, 11),
        "Saturn":  (3, 5, 6, 12),
        "Lagna":   (1, 2, 4, 5, 6, 7, 9, 10, 11),
    },
    "Venus": {
        "Sun":     (8, 11, 12),
        "Moon":    (1, 2, 3, 4, 5, 8, 9, 11, 12),
        "Mars":    (3, 4, 6, 9, 11, 12),
        "Mercury": (3, 5, 6, 9, 11),
        "Jupiter": (5, 8, 9, 10, 11),
        "Venus":   (1, 2, 3, 4, 5, 8, 9, 10, 11),
        "Saturn":  (3, 4, 5, 8, 9, 10, 11),
        "Lagna":   (1, 2, 3, 4, 5, 8, 9, 11),
    },
    "Saturn": {
        "Sun":     (1, 2, 4, 7, 8, 10, 11),
        "Moon":    (3, 6, 11),
        "Mars":    (3, 5, 6, 10, 11, 12),
        "Mercury": (6, 8, 9, 10, 11, 12),
        "Jupiter": (5, 6, 11, 12),
        "Venus":   (6, 11, 12),
        "Saturn":  (3, 5, 6, 11),
        "Lagna":   (1, 3, 4, 6, 10, 11),
    },
}


class BavMatrix(TypedDict):
    """Full 7-planet x 12-sign Ashtakavarga matrix plus the SAV row."""
    bav_per_planet: dict[str, list[int]]
    sav: list[int]
    bav_totals: dict[str, int]


def _sign_int(value: object, label: str) -> int:
    """Coerce + validate that `value` is a 1..12 sign index."""
    try:
        s = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a 1..12 sign int, got {value!r}") from exc
    if not 1 <= s <= 12:
        raise ValueError(f"{label} sign must be in 1..12, got {s}")
    return s


def compute_ashtakavarga(
    d1_chart: Mapping[str, Mapping[str, object]],
    ascendant: Mapping[str, object],
) -> BavMatrix:
    """Compute the full Ashtakavarga matrix.

    Args:
        d1_chart: Mapping {planet_name: {"sign": int (1..12), ...}}. Must
            contain all 7 BAV_PLANETS keys; extra keys (Rahu, Ketu) are
            ignored. Only the `sign` field is consumed.
        ascendant: Mapping with key "sign" (1..12). Provides the Lagna's
            contributing sign.

    Returns:
        BavMatrix with:
          - bav_per_planet: {planet: list[int] of length 12, each in 0..8}
            indexed 0..11 for signs Aries..Pisces.
          - sav: list[int] of length 12 (column-wise sum across the 7 BAVs).
          - bav_totals: {planet: int} -- sum of each planet's 12 entries.

    Raises:
        ValueError: missing planet in d1_chart or invalid sign value.
    """
    # Build {contributor: 1..12 sign}.
    positions: dict[str, int] = {}
    for planet in BAV_PLANETS:
        if planet not in d1_chart:
            raise ValueError(f"d1_chart missing required planet {planet!r}")
        positions[planet] = _sign_int(d1_chart[planet].get("sign"), planet)
    if "sign" not in ascendant:
        raise ValueError("ascendant dict missing 'sign'")
    positions["Lagna"] = _sign_int(ascendant["sign"], "Lagna")

    bav_per_planet: dict[str, list[int]] = {}
    sav = [0] * 12

    for planet in BAV_PLANETS:
        row = [0] * 12
        rules = _BENEFIC_OFFSETS[planet]
        for contributor in BAV_CONTRIBUTORS:
            donor_sign = positions[contributor]  # 1..12
            for offset in rules[contributor]:
                # 1-indexed modular forward count, then back to 0-indexed list pos.
                target_sign_1based = ((donor_sign - 1 + offset - 1) % 12) + 1
                row[target_sign_1based - 1] += 1
        bav_per_planet[planet] = row
        for s in range(12):
            sav[s] += row[s]

    bav_totals = {p: sum(bav_per_planet[p]) for p in BAV_PLANETS}

    return BavMatrix(
        bav_per_planet=bav_per_planet,
        sav=sav,
        bav_totals=bav_totals,
    )
