"""Shared chart-inspection helpers for the modern_life detectors.

These helpers operate on the **raw chart dict** produced by
:func:`app.core.ephemeris_engine.calculate_all_charts` and the
``asc_sign`` (1..12) lagna rashi. No detector recomputes signs/houses;
helpers only project house-from-lagna and read planet sign membership.

All helpers are pure functions: given identical input they return
identical output (no mutation, no I/O).
"""
from __future__ import annotations

from typing import Final, Mapping

# Sign indices (1-indexed) that are *dual* (Dvisvabhava). Practitioners
# read these as indicators of fluidity / change.
DUAL_SIGNS: Final[frozenset[int]] = frozenset({3, 6, 9, 12})  # Gem, Vir, Sag, Pis

# Sign indices considered movable (Chara).
MOVABLE_SIGNS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})

# Fixed signs (Sthira).
FIXED_SIGNS: Final[frozenset[int]] = frozenset({2, 5, 8, 11})

# Mapping of (lagna_sign, planet) -> True if the planet is the natural
# functional benefic/malefic for that lagna — kept simple for the
# modern-life advisory layer (full functional_nature lives in foundations).


def house_sign_from_asc(asc_sign: int, house: int) -> int:
    """Return the rashi at ``house`` (1..12) counting from ``asc_sign``.

    >>> house_sign_from_asc(6, 10)  # Virgo lagna -> 10H is Gemini
    3
    """
    if not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign must be 1..12, got {asc_sign!r}")
    if not (1 <= house <= 12):
        raise ValueError(f"house must be 1..12, got {house!r}")
    return ((asc_sign - 1) + (house - 1)) % 12 + 1


def planet_house(asc_sign: int, planet_sign: int) -> int:
    """Whole-sign house occupied by a planet given asc_sign + planet sign."""
    if not (1 <= asc_sign <= 12 and 1 <= planet_sign <= 12):
        raise ValueError("signs must be 1..12")
    return ((planet_sign - asc_sign) % 12) + 1


def planet_sign(d_chart: Mapping[str, Mapping], planet: str) -> int | None:
    """Read the integer sign (1..12) of ``planet`` from a divisional dict."""
    entry = d_chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    sign = entry.get("sign")
    if isinstance(sign, int) and 1 <= sign <= 12:
        return sign
    return None


def planets_in_house(
    asc_sign: int, d_chart: Mapping[str, Mapping], house: int
) -> list[str]:
    """Return planets occupying ``house`` (whole-sign) in ``d_chart``."""
    target_sign = house_sign_from_asc(asc_sign, house)
    out: list[str] = []
    for name, entry in d_chart.items():
        if not isinstance(entry, Mapping):
            continue
        if entry.get("sign") == target_sign:
            out.append(name)
    return out


def planets_in_sign(
    d_chart: Mapping[str, Mapping], sign: int
) -> list[str]:
    """Return planets occupying ``sign`` (1..12) in ``d_chart``."""
    if not (1 <= sign <= 12):
        raise ValueError("sign must be 1..12")
    out: list[str] = []
    for name, entry in d_chart.items():
        if not isinstance(entry, Mapping):
            continue
        if entry.get("sign") == sign:
            out.append(name)
    return out


def planet_nakshatra_lord(d_chart: Mapping[str, Mapping], planet: str) -> str | None:
    """Read the nakshatra-lord of ``planet`` (e.g. Moon's pada-lord)."""
    entry = d_chart.get(planet)
    if not isinstance(entry, Mapping):
        return None
    nak = entry.get("nakshatra")
    if not isinstance(nak, Mapping):
        return None
    lord = nak.get("lord")
    if isinstance(lord, str) and lord:
        return lord
    return None


__all__ = [
    "DUAL_SIGNS",
    "MOVABLE_SIGNS",
    "FIXED_SIGNS",
    "house_sign_from_asc",
    "planet_house",
    "planet_sign",
    "planets_in_house",
    "planets_in_sign",
    "planet_nakshatra_lord",
]
