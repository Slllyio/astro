"""Drekkana (decanate, D3) — the three 10° parts of a sign and their lords (BPHS ch.6 sl.7-8).

Each sign's three decanates fall in the 1st, 5th and 9th signs from it, "respectively lorded by
Narada, Agasthya and Doorvasa" (BPHS-6:162). The decanate lord is the lord of that 1st/5th/9th sign.
The D3 is read for happiness through co-born (siblings, BPHS-7 use-domains).

The decanate SIGN itself is already in the Shodasavarga table; this adds the part index (1/2/3), the
lord, and the sage-deity — the pieces used in co-born and iconographic (prasna) analysis. Pure
arithmetic over the varga substrate, which matches the 1st/5th/9th rule exactly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart import varga as _varga
from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import SIGN_LORDS

SOURCE: Final[Citation] = Citation("BPHS-6", 162)     # sl.7-8, "DECANATE"

#: decanate index (1..3) -> the presiding sage-deity (BPHS-6:162).
DEITIES: Final[tuple[str, ...]] = ("Narada", "Agasthya", "Doorvasa")


@dataclass(frozen=True)
class Drekkana:
    index: int       # 1, 2 or 3 (which 10° part of the rasi)
    sign: int        # the decanate sign (1st/5th/9th from the rasi), 1..12
    lord: str        # lord of the decanate sign
    deity: str       # Narada / Agasthya / Doorvasa


def drekkana(longitude: float) -> Drekkana:
    """The decanate of a body at `longitude`: its part index, sign, lord and deity (BPHS-6:7-8)."""
    lon = longitude % 360.0
    index = int((lon % 30.0) // 10.0) + 1        # 1..3
    sign = _varga.drekkana_sign(lon)
    return Drekkana(index=index, sign=sign, lord=SIGN_LORDS[sign], deity=DEITIES[index - 1])


def drekkana_all(longitudes) -> dict[str, Drekkana]:
    """Every body's decanate."""
    return {body: drekkana(lon) for body, lon in longitudes.items()}
