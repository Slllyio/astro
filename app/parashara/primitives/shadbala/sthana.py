"""Sthana bala — positional strength (BPHS ch.27, slokas 1-6).

Five sub-components, summed (BPHS-27:190):
  * Uchcha (exaltation)         — distance from the debilitation point / 3, max 60 (sl.1-6)
  * Saptavargaja (7-varga dignity) — per varga: moolatrikona 45 / own 30 / extreme-friend 20 /
                                  friend 15 / neutral 10 / enemy 4 / extreme-enemy 2, summed (sl.2-4)
  * Ojhayugmarasiamsa (odd/even) — 15 in the favoured parity of rasi + 15 of navamsa (sl.4.5)
  * Kendradi (angular)          — angle 60 / succedent 30 / cadent 15 (sl.5)
  * Drekkana (decanate)         — male/female/eunuch planet in 1st/2nd/3rd decanate -> 15 (sl.6)

All in virupas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.longevity import deep_exaltation_point
from app.parashara.primitives.relationships import (
    EXALTATION, MOOLATRIKONA, SIGN_LORDS, compound)
from app.raman_saab.chart import varga as _varga     # substrate: division sign arithmetic

SOURCE: Final[Citation] = Citation("BPHS-27", 26)
SAPTAVARGAJA_SOURCE: Final[Citation] = Citation("BPHS-27", 110)

#: Saptavarga = the 7 vargas (Rasi, Hora, Drekkana, Saptamsa, Navamsa, Dwadasamsa, Trimsamsa).
_SAPTAVARGA: Final[tuple[int, ...]] = (1, 2, 3, 7, 9, 12, 30)

#: 7-tier dignity value in virupas (BPHS-27:110).
_DIGNITY_VIRUPAS: Final[dict[str, float]] = {
    "moolatrikona": 45.0, "own": 30.0,
    "adhi_mitra": 20.0, "mitra": 15.0, "sama": 10.0, "shatru": 4.0, "adhi_shatru": 2.0,
}

#: Ojhayugma: planets that gain the strength in ODD signs (male/neutral) vs EVEN (female).
_ODD_FAVOURED: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Jupiter", "Mercury", "Saturn"})
_EVEN_FAVOURED: Final[frozenset[str]] = frozenset({"Venus", "Moon"})

#: Drekkana: which decanate (1/2/3) each planet-sex gains 15 virupas in (BPHS-27:163).
_DREKKANA_PART: Final[dict[str, int]] = {
    "Sun": 1, "Mars": 1, "Jupiter": 1,        # male -> 1st
    "Venus": 2, "Moon": 2,                     # female -> 2nd
    "Mercury": 3, "Saturn": 3,                 # eunuch -> 3rd
}

_KENDRA = frozenset({1, 4, 7, 10})
_PANAPHARA = frozenset({2, 5, 8, 11})


def _signs_owned(planet: str) -> tuple[int, ...]:
    return tuple(s for s, lord in SIGN_LORDS.items() if lord == planet)


def uchcha_bala(planet: str, longitude: float) -> float:
    """Exaltation strength: distance from the deep debilitation point / 3, max 60 (BPHS-27:1-6)."""
    debil = (deep_exaltation_point(planet) + 180.0) % 360.0
    diff = (longitude - debil) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff / 3.0        # 0 at debilitation, 60 at exaltation (180 deg away)


def saptavargaja_bala(planet: str, longitudes: Mapping[str, float]) -> float:
    """Dignity summed across the seven vargas (BPHS-27:2-4)."""
    plon = longitudes[planet] % 360.0
    psign = int(plon // 30) + 1
    total = 0.0
    for n in _SAPTAVARGA:
        vsign = _varga.varga_sign(plon, n)
        if vsign == MOOLATRIKONA.get(planet):
            total += _DIGNITY_VIRUPAS["moolatrikona"]
        elif vsign in _signs_owned(planet):
            total += _DIGNITY_VIRUPAS["own"]
        else:
            lord = SIGN_LORDS[vsign]
            lord_sign = int(longitudes[lord] % 360.0 // 30) + 1 if lord in longitudes else psign
            distance = ((lord_sign - psign) % 12) + 1
            rel = compound(planet, lord, house_distance=distance)
            total += _DIGNITY_VIRUPAS[rel]
    return total


def ojhayugmarasiamsa_bala(planet: str, longitude: float) -> float:
    """Odd/even strength in rasi + navamsa, 15 virupas each (BPHS-27:4.5)."""
    lon = longitude % 360.0
    rasi = int(lon // 30) + 1
    navamsa = _varga.navamsa_sign(lon)
    total = 0.0
    for sign in (rasi, navamsa):
        odd = (sign % 2 == 1)
        if (planet in _ODD_FAVOURED and odd) or (planet in _EVEN_FAVOURED and not odd):
            total += 15.0
    return total


def kendradi_bala(house_from_lagna: int) -> float:
    """Angular strength: angle 60 / succedent 30 / cadent 15 (BPHS-27:5)."""
    if house_from_lagna in _KENDRA:
        return 60.0
    if house_from_lagna in _PANAPHARA:
        return 30.0
    return 15.0


def drekkana_bala(planet: str, longitude: float) -> float:
    """Decanate strength: 15 virupas if the planet's sex matches its decanate (BPHS-27:6)."""
    if planet not in _DREKKANA_PART:
        return 0.0
    decanate = int((longitude % 30.0) // 10) + 1     # 1, 2 or 3
    return 15.0 if decanate == _DREKKANA_PART[planet] else 0.0


@dataclass(frozen=True)
class SthanaBala:
    uchcha: float
    saptavargaja: float
    ojhayugmarasiamsa: float
    kendradi: float
    drekkana: float

    @property
    def total(self) -> float:
        return (self.uchcha + self.saptavargaja + self.ojhayugmarasiamsa
                + self.kendradi + self.drekkana)


def sthana_bala(planet: str, longitudes: Mapping[str, float], *, asc_sign: int) -> SthanaBala:
    """Full positional strength of `planet` (virupas), all five sub-components."""
    lon = longitudes[planet] % 360.0
    psign = int(lon // 30) + 1
    house = ((psign - asc_sign) % 12) + 1
    return SthanaBala(
        uchcha=uchcha_bala(planet, lon),
        saptavargaja=saptavargaja_bala(planet, longitudes),
        ojhayugmarasiamsa=ojhayugmarasiamsa_bala(planet, lon),
        kendradi=kendradi_bala(house),
        drekkana=drekkana_bala(planet, lon),
    )
