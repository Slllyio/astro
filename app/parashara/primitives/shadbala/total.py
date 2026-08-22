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
from app.parashara.primitives.shadbala.cheshta import cheshta_bala
from app.parashara.primitives.shadbala.dig import dig_bala
from app.parashara.primitives.shadbala.kala import ayana_bala, paksha_bala
from app.parashara.primitives.shadbala.naisargika import naisargika_bala
from app.parashara.primitives.shadbala.sthana import SthanaBala, sthana_bala

#: What is encoded vs pending, for honesty. FIVE full balas now (Sthana, Dig, Naisargika, Cheshta,
#: plus Kala's two computable sub-components Paksha + Ayana). Drik (graded drishti-value calc) and
#: the rest of Kala (day-night/hora/calendar lords — see shadbala.kala.PENDING_SUBCOMPONENTS) still
#: need dedicated builds, so the total is not yet the full six.
ENCODED_BALAS: Final[tuple[str, ...]] = (
    "sthana", "dig", "naisargika", "cheshta", "kala:paksha", "kala:ayana")
PENDING_BALAS: Final[tuple[str, ...]] = ("kala:rest", "drik")


@dataclass(frozen=True)
class PartialShadbala:
    planet: str
    sthana: SthanaBala
    dig: float
    naisargika: float
    cheshta: float
    kala_paksha: float
    kala_ayana: float
    complete: bool          # always False until all six balas are in

    @property
    def virupas(self) -> float:
        return (self.sthana.total + self.dig + self.naisargika + self.cheshta
                + self.kala_paksha + self.kala_ayana)

    @property
    def rupas(self) -> float:
        return self.virupas / VIRUPAS_PER_RUPA


def partial_shadbala(planet: str, longitudes: Mapping[str, float], *,
                     asc_sign: int, asc_longitude: float, moon_waxing: bool,
                     speed: float, ayanamsa: float) -> PartialShadbala:
    """Sthana + Dig + Naisargika + Cheshta + Kala(Paksha, Ayana) for one planet (virupas). PARTIAL."""
    paksha = paksha_bala(planet, longitudes, moon_waxing=moon_waxing)
    ayana = ayana_bala(planet, longitudes[planet], ayanamsa)
    # Sun's Cheshta = its Ayana; Moon's = its Paksha; others from speed.
    cheshta = cheshta_bala(planet, speed=speed, sun_ayana=ayana, moon_paksha=paksha)
    return PartialShadbala(
        planet=planet,
        sthana=sthana_bala(planet, longitudes, asc_sign=asc_sign),
        dig=dig_bala(planet, longitudes[planet], asc_longitude),
        naisargika=naisargika_bala(planet),
        cheshta=cheshta,
        kala_paksha=paksha,
        kala_ayana=ayana,
        complete=False,
    )


def partial_shadbala_all(longitudes: Mapping[str, float], *,
                         asc_sign: int, asc_longitude: float, moon_waxing: bool,
                         speeds: Mapping[str, float], ayanamsa: float) -> dict[str, PartialShadbala]:
    """Partial Shadbala for each of the seven grahas present."""
    from app.parashara.primitives.relationships import GRAHAS
    return {g: partial_shadbala(g, longitudes, asc_sign=asc_sign, asc_longitude=asc_longitude,
                                moon_waxing=moon_waxing, speed=speeds.get(g, 0.0), ayanamsa=ayanamsa)
            for g in GRAHAS if g in longitudes}
