"""Shadbala assembly (BPHS ch.27). PARTIAL: three of the six balas encoded so far.

`partial_shadbala` sums Sthana + Dig + Naisargika and stamps `complete=False`, because the full
Shadbala is SIX balas — Kala, Cheshta and Drik are not yet encoded (they need birth-time precision,
planetary speed, and weighted drishti respectively). The result is never presented as a six-fold
total; it is an honest partial that already ranks planets on the three strongest-signal balas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.primitives.shadbala import VIRUPAS_PER_RUPA
from app.parashara.primitives.shadbala.dig import dig_bala
from app.parashara.primitives.shadbala.kala import paksha_bala
from app.parashara.primitives.shadbala.naisargika import naisargika_bala
from app.parashara.primitives.shadbala.sthana import SthanaBala, sthana_bala

#: What is encoded vs pending, for honesty. Kala is present only as its Paksha sub-component;
#: Cheshta and Drik, and Kala's remaining sub-components, need the ephemeris time/speed/declination
#: layer (see shadbala.kala.PENDING_SUBCOMPONENTS).
ENCODED_BALAS: Final[tuple[str, ...]] = ("sthana", "dig", "naisargika", "kala:paksha")
PENDING_BALAS: Final[tuple[str, ...]] = ("kala:rest", "cheshta", "drik")


@dataclass(frozen=True)
class PartialShadbala:
    planet: str
    sthana: SthanaBala
    dig: float
    naisargika: float
    kala_paksha: float      # the one Kala sub-component encoded so far
    complete: bool          # always False until all six balas are in

    @property
    def virupas(self) -> float:
        return self.sthana.total + self.dig + self.naisargika + self.kala_paksha

    @property
    def rupas(self) -> float:
        return self.virupas / VIRUPAS_PER_RUPA


def partial_shadbala(planet: str, longitudes: Mapping[str, float], *,
                     asc_sign: int, asc_longitude: float, moon_waxing: bool) -> PartialShadbala:
    """Sthana + Dig + Naisargika + Kala(Paksha) for one planet (virupas). PARTIAL."""
    return PartialShadbala(
        planet=planet,
        sthana=sthana_bala(planet, longitudes, asc_sign=asc_sign),
        dig=dig_bala(planet, longitudes[planet], asc_longitude),
        naisargika=naisargika_bala(planet),
        kala_paksha=paksha_bala(planet, longitudes, moon_waxing=moon_waxing),
        complete=False,
    )


def partial_shadbala_all(longitudes: Mapping[str, float], *,
                         asc_sign: int, asc_longitude: float,
                         moon_waxing: bool) -> dict[str, PartialShadbala]:
    """Partial Shadbala for each of the seven grahas present."""
    from app.parashara.primitives.relationships import GRAHAS
    return {g: partial_shadbala(g, longitudes, asc_sign=asc_sign, asc_longitude=asc_longitude,
                                moon_waxing=moon_waxing)
            for g in GRAHAS if g in longitudes}
