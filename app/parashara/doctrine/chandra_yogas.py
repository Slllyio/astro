"""Lunar (Chandra) yogas (BPHS ch.37) — yogas reckoned from the Moon.

Parashara's ch.37 gives the classical yogas that depend on what surrounds the Moon: Sunapha, Anapha
and Durudhara (a graha in the 2nd, the 12th, or both from the Moon), Kemadruma (the Moon left bare),
Adhi yoga (benefics in the 6th/7th/8th from the Moon) and a Moon-Dhana yoga (benefics in the upachayas
from the Moon). All are cleanly chart-computable, so this module detects each and cites Parashara's own
defining sloka.

Convention: these yogas count the five tara-grahas (Mars, Mercury, Jupiter, Venus, Saturn) — the Sun
is excluded by the text ("a planet other than the Sun"), the Moon is the reference point, and the
shadowy nodes do not participate. "Benefics" for Adhi/Dhana are the three natural benefics Jupiter,
Venus and Mercury.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

_WORK: Final[str] = "BPHS-37"
#: Grahas that populate the lunar yogas (Sun excluded by the text; Moon is the reference; no nodes).
_TARA: Final[tuple[str, ...]] = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
#: Natural benefics for Adhi / Moon-Dhana (the three; Moon is the reference point here).
_BENEFICS: Final[tuple[str, ...]] = ("Jupiter", "Venus", "Mercury")

SUNAPHA_SOURCE: Final[Citation] = Citation(_WORK, 83)     # sl.7 — Sunapha/Anapha/Duradhara
KEMADRUMA_SOURCE: Final[Citation] = Citation(_WORK, 106)  # sl.11
ADHI_SOURCE: Final[Citation] = Citation(_WORK, 48)        # sl.5 — Adhi yoga from the Moon
DHANA_SOURCE: Final[Citation] = Citation(_WORK, 58)       # sl.6 — Dhana yoga from the Moon

_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_UPACHAYA_FROM_MOON: Final[frozenset[int]] = frozenset({3, 6, 10, 11})


@dataclass(frozen=True)
class ChandraYoga:
    name: str
    reason: str
    source: Citation


def _house(ref_sign: int, sign: int) -> int:
    return ((sign - ref_sign) % 12) + 1


def _tara_houses_from_moon(planet_signs: Mapping[str, int], moon_sign: int) -> dict[str, int]:
    return {p: _house(moon_sign, planet_signs[p]) for p in _TARA if p in planet_signs}


def detect(planet_signs: Mapping[str, int], *, moon_sign: int, asc_sign: int) -> tuple[ChandraYoga, ...]:
    """Every lunar yoga present in the chart (BPHS ch.37), each cited.

    `planet_signs` maps grahas -> sign (1..12); `moon_sign`/`asc_sign` are 1..12.
    """
    h = _tara_houses_from_moon(planet_signs, moon_sign)
    in_2nd = [p for p, d in h.items() if d == 2]
    in_12th = [p for p, d in h.items() if d == 12]
    conjunct = [p for p, d in h.items() if d == 1]
    out: list[ChandraYoga] = []

    if in_2nd and in_12th:
        out.append(ChandraYoga("Durudhara",
                               f"grahas in both the 2nd ({', '.join(in_2nd)}) and 12th "
                               f"({', '.join(in_12th)}) from the Moon", SUNAPHA_SOURCE))
    elif in_2nd:
        out.append(ChandraYoga("Sunapha", f"{', '.join(in_2nd)} in the 2nd from the Moon",
                               SUNAPHA_SOURCE))
    elif in_12th:
        out.append(ChandraYoga("Anapha", f"{', '.join(in_12th)} in the 12th from the Moon",
                               SUNAPHA_SOURCE))

    # Kemadruma: excluding the Sun, no graha with the Moon, in the 2nd/12th from her, or in a
    # kendra from the ascendant (BPHS-37 sl.11 — the last clause is the cancellation).
    in_kendra_from_lagna = [p for p in _TARA if p in planet_signs
                            and _house(asc_sign, planet_signs[p]) in _KENDRAS]
    if not (in_2nd or in_12th or conjunct or in_kendra_from_lagna):
        out.append(ChandraYoga("Kemadruma", "the Moon has no graha with her, in her 2nd/12th, or in "
                               "a kendra from the ascendant", KEMADRUMA_SOURCE))

    # Adhi yoga: benefics in the 6th, 7th and 8th from the Moon.
    adhi = {_house(moon_sign, planet_signs[b]) for b in _BENEFICS if b in planet_signs} & {6, 7, 8}
    if adhi == {6, 7, 8}:
        out.append(ChandraYoga("Adhi", "benefics occupy the 6th, 7th and 8th from the Moon",
                               ADHI_SOURCE))

    # Moon-Dhana yoga: the three benefics in the upachayas (3/6/10/11) from the Moon.
    if all(b in planet_signs and _house(moon_sign, planet_signs[b]) in _UPACHAYA_FROM_MOON
           for b in _BENEFICS):
        out.append(ChandraYoga("Chandra-Dhana", "the benefics occupy upachayas (3/6/10/11) from the "
                               "Moon", DHANA_SOURCE))
    return tuple(out)
