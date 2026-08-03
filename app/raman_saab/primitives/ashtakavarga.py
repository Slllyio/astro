"""Ashtakavarga — Bhinnashtakavarga (BAV) per planet and Sarvashtakavarga (SAV).

BV Raman used Ashtakavarga constantly for bhava strength and as the backbone of transit timing:
a sign/bhava with more `bindus` (benefic dots) supports the planets transiting/owning it.

Each of the seven planets earns a bindu in certain houses counted FROM each of eight references
(the seven planets + the Lagna). The "benefic places" tables below are the canonical Parashari /
BPHS tables. They carry a hard checksum: each planet's BAV total is fixed and the SAV total across
all twelve signs is ALWAYS 337 — `tests/raman_saab/test_ashtakavarga.py` asserts both, so an
encoding error cannot pass silently.

Usage:
    from app.raman_saab.primitives import ashtakavarga as av
    bav = av.bhinnashtakavarga(chart, "Saturn")   # {sign 1..12 -> bindus}
    sav = av.sarvashtakavarga(chart)              # {sign 1..12 -> bindus}, sum is 337
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.model import RamanChart

_REFS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna")
PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

#: Canonical BAV totals (checksum). SAV = sum of the seven = 337.
BAV_TOTALS: Final[dict[str, int]] = {
    "Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54,
    "Jupiter": 56, "Venus": 52, "Saturn": 39}

# benefic places: planet -> reference -> houses (1..12 from that reference) earning a bindu.
_BENEFIC: Final[dict[str, dict[str, tuple[int, ...]]]] = {
    "Sun": {
        "Sun": (1, 2, 4, 7, 8, 9, 10, 11), "Moon": (3, 6, 10, 11),
        "Mars": (1, 2, 4, 7, 8, 9, 10, 11), "Mercury": (3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (5, 6, 9, 11), "Venus": (6, 7, 12),
        "Saturn": (1, 2, 4, 7, 8, 9, 10, 11), "Lagna": (3, 4, 6, 10, 11, 12)},
    "Moon": {
        "Sun": (3, 6, 7, 8, 10, 11), "Moon": (1, 3, 6, 7, 10, 11),
        "Mars": (2, 3, 5, 6, 9, 10, 11), "Mercury": (1, 3, 4, 5, 7, 8, 10, 11),
        "Jupiter": (1, 4, 7, 8, 10, 11, 12),    # Raman HPA ch.26: "1,4,7,8,10,11,12 from Jupiter" (was 1,2,..,11)
        "Venus": (3, 4, 5, 7, 9, 10, 11),
        "Saturn": (3, 5, 6, 11), "Lagna": (3, 6, 10, 11)},
    "Mars": {
        "Sun": (3, 5, 6, 10, 11), "Moon": (3, 6, 11),
        "Mars": (1, 2, 4, 7, 8, 10, 11), "Mercury": (3, 5, 6, 11),
        "Jupiter": (6, 10, 11, 12), "Venus": (6, 8, 11, 12),
        "Saturn": (1, 4, 7, 8, 9, 10, 11), "Lagna": (1, 3, 6, 10, 11)},
    "Mercury": {
        "Sun": (5, 6, 9, 11, 12), "Moon": (2, 4, 6, 8, 10, 11),
        "Mars": (1, 2, 4, 7, 8, 9, 10, 11), "Mercury": (1, 3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (6, 8, 11, 12), "Venus": (1, 2, 3, 4, 5, 8, 9, 11),
        "Saturn": (1, 2, 4, 7, 8, 9, 10, 11), "Lagna": (1, 2, 4, 6, 8, 10, 11)},
    "Jupiter": {
        "Sun": (1, 2, 3, 4, 7, 8, 9, 10, 11), "Moon": (2, 5, 7, 9, 11),
        "Mars": (1, 2, 4, 7, 8, 10, 11), "Mercury": (1, 2, 4, 5, 6, 9, 10, 11),
        "Jupiter": (1, 2, 3, 4, 7, 8, 10, 11), "Venus": (2, 5, 6, 9, 10, 11),
        "Saturn": (3, 5, 6, 12), "Lagna": (1, 2, 4, 5, 6, 7, 9, 10, 11)},
    "Venus": {
        "Sun": (8, 11, 12), "Moon": (1, 2, 3, 4, 5, 8, 9, 11, 12),
        "Mars": (3, 5, 6, 9, 11, 12), "Mercury": (3, 5, 6, 9, 11),
        "Jupiter": (5, 8, 9, 10, 11), "Venus": (1, 2, 3, 4, 5, 8, 9, 10, 11),
        "Saturn": (3, 4, 5, 8, 9, 10, 11), "Lagna": (1, 2, 3, 4, 5, 8, 9, 11)},
    "Saturn": {
        "Sun": (1, 2, 4, 7, 8, 10, 11), "Moon": (3, 6, 11),
        "Mars": (3, 5, 6, 10, 11, 12), "Mercury": (6, 8, 9, 10, 11, 12),
        "Jupiter": (5, 6, 11, 12), "Venus": (6, 11, 12),
        "Saturn": (3, 5, 6, 11), "Lagna": (1, 3, 4, 6, 10, 11)},
}


def _ref_sign(ref: str, chart: RamanChart) -> int | None:
    if ref == "Lagna":
        return chart.asc_sign
    p = chart.planets.get(ref)
    return None if p is None else p.sign


def bhinnashtakavarga(chart: RamanChart, planet: str) -> dict[int, int]:
    """Bindus per sign (1..12) in `planet`'s Bhinnashtakavarga. Total = BAV_TOTALS[planet]."""
    bindus = {s: 0 for s in range(1, 13)}
    for ref, houses in _BENEFIC[planet].items():
        rs = _ref_sign(ref, chart)
        if rs is None:
            continue
        for h in houses:
            bindus[((rs - 1 + h - 1) % 12) + 1] += 1
    return bindus


def prasthara(chart: RamanChart, planet: str) -> dict[int, frozenset[str]]:
    """The Prasthara Chakra of `planet`'s Ashtakavarga: per sign (1..12), WHICH of the eight
    references (the seven grahas + "Lagna") contributed a bindu there.

    `bhinnashtakavarga` collapses this to counts; the Prasthara keeps the contributors, which
    is what Kakshya transit judgment needs — "the number of bindus in a Rasi ... is the sum-
    total of the contribution of each planet and the Prasthara Chakra reveals the planets that
    make the contribution" (Raman, Ashtakavarga System of Prediction ch.XIII). Derived from the
    SAME `_BENEFIC` tables as the counts, so the checksums that guard those guard this too:
    `len(prasthara[s]) == bhinnashtakavarga[s]` for every sign by construction."""
    out: dict[int, set[str]] = {s: set() for s in range(1, 13)}
    for ref, houses in _BENEFIC[planet].items():
        rs = _ref_sign(ref, chart)
        if rs is None:
            continue
        for h in houses:
            out[((rs - 1 + h - 1) % 12) + 1].add(ref)
    return {s: frozenset(refs) for s, refs in out.items()}


def sarvashtakavarga(chart: RamanChart) -> dict[int, int]:
    """Bindus per sign (1..12) summed over the seven Bhinnashtakavargas. Total = 337."""
    sav = {s: 0 for s in range(1, 13)}
    for planet in PLANETS:
        for s, b in bhinnashtakavarga(chart, planet).items():
            sav[s] += b
    return sav


def bindus_in_house(chart: RamanChart, house: int, planet: str | None = None) -> int:
    """SAV (or `planet`'s BAV) bindus in the whole-sign `house` counted from the Lagna."""
    sign = ((chart.asc_sign - 1) + (house - 1)) % 12 + 1
    table = sarvashtakavarga(chart) if planet is None else bhinnashtakavarga(chart, planet)
    return table[sign]
