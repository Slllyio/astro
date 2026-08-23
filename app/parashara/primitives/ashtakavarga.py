"""Ashtakavarga — Bhinnashtakavarga (BAV) per planet and Sarvashtakavarga (SAV) (BPHS ch.66).

Each of the seven planets earns a bindu (benefic dot) in certain houses counted FROM each of eight
references — the seven planets and the Lagna. Summed, they give that planet's Bhinnashtakavarga; the
seven BAVs summed per sign give the Sarvashtakavarga, the backbone of bhava-strength and transit
judgment.

The benefic-place tables are the canonical Parashari tables (identical across Parashara, Varahamihira
and later authorities). They carry a HARD checksum: each planet's BAV total is fixed (Sun 48, Moon 49,
Mars 39, Mercury 54, Jupiter 56, Venus 52, Saturn 39) and the SAV total across the twelve signs is
ALWAYS 337. `_assert_checksum()` runs at import and the tests re-assert both, so a transcription error
cannot pass silently — the fidelity guarantee for a table that OCR would otherwise endanger.

Ported (not imported) from the ratcheted raman_saab tables, which carry the same checksum; re-keyed
to the lightweight (planet -> sign) + asc_sign inputs this engine uses, and cited to BPHS ch.66.
"""
from __future__ import annotations

from typing import Final, Mapping, Optional

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-66", 199)   # "Ashtakavarga of the Sun" — the tables' chapter

_REFS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna")
PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

#: Canonical BAV totals (checksum). SAV = sum of the seven = 337.
BAV_TOTALS: Final[Mapping[str, int]] = {
    "Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54,
    "Jupiter": 56, "Venus": 52, "Saturn": 39}
SAV_TOTAL: Final[int] = 337

#: benefic places: planet -> reference -> houses (1..12 from that reference) earning a bindu.
_BENEFIC: Final[Mapping[str, Mapping[str, tuple[int, ...]]]] = {
    "Sun": {
        "Sun": (1, 2, 4, 7, 8, 9, 10, 11), "Moon": (3, 6, 10, 11),
        "Mars": (1, 2, 4, 7, 8, 9, 10, 11), "Mercury": (3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (5, 6, 9, 11), "Venus": (6, 7, 12),
        "Saturn": (1, 2, 4, 7, 8, 9, 10, 11), "Lagna": (3, 4, 6, 10, 11, 12)},
    "Moon": {
        "Sun": (3, 6, 7, 8, 10, 11), "Moon": (1, 3, 6, 7, 10, 11),
        "Mars": (2, 3, 5, 6, 9, 10, 11), "Mercury": (1, 3, 4, 5, 7, 8, 10, 11),
        "Jupiter": (1, 4, 7, 8, 10, 11, 12), "Venus": (3, 4, 5, 7, 9, 10, 11),
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


def _ref_sign(ref: str, planet_signs: Mapping[str, int], asc_sign: int) -> Optional[int]:
    return asc_sign if ref == "Lagna" else planet_signs.get(ref)


def bhinnashtakavarga(planet: str, planet_signs: Mapping[str, int], *,
                      asc_sign: int) -> dict[int, int]:
    """Bindus per sign (1..12) in `planet`'s Bhinnashtakavarga. Total = BAV_TOTALS[planet]."""
    bindus = {s: 0 for s in range(1, 13)}
    for ref, houses in _BENEFIC[planet].items():
        rs = _ref_sign(ref, planet_signs, asc_sign)
        if rs is None:
            continue
        for h in houses:
            bindus[((rs - 1 + h - 1) % 12) + 1] += 1
    return bindus


def sarvashtakavarga(planet_signs: Mapping[str, int], *, asc_sign: int) -> dict[int, int]:
    """Bindus per sign (1..12) summed over the seven Bhinnashtakavargas. Total = 337."""
    sav = {s: 0 for s in range(1, 13)}
    for planet in PLANETS:
        for s, b in bhinnashtakavarga(planet, planet_signs, asc_sign=asc_sign).items():
            sav[s] += b
    return sav


def bindus_in_house(house: int, planet_signs: Mapping[str, int], *, asc_sign: int,
                    planet: Optional[str] = None) -> int:
    """SAV (or `planet`'s BAV) bindus in the whole-sign `house` counted from the Lagna."""
    sign = ((asc_sign - 1) + (house - 1)) % 12 + 1
    table = (sarvashtakavarga(planet_signs, asc_sign=asc_sign) if planet is None
             else bhinnashtakavarga(planet, planet_signs, asc_sign=asc_sign))
    return table[sign]


def _assert_checksum() -> None:
    """The tables' totals are invariants — verify them once at import so an edit cannot slip through."""
    for planet, expected in BAV_TOTALS.items():
        got = sum(len(h) for h in _BENEFIC[planet].values())
        if got != expected:
            raise AssertionError(f"{planet} BAV total {got} != canonical {expected}")
    if sum(BAV_TOTALS.values()) != SAV_TOTAL:
        raise AssertionError("SAV total != 337")


_assert_checksum()
