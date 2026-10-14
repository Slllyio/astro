"""Shadbala assembly (BPHS ch.27). COMPLETE: all six balas encoded.

`partial_shadbala` (the name is historical — the result is now the full six-fold strength) sums the
six balas Parashara names: Sthana, Dig, Naisargika, Cheshta, Drik, and Kala — the last itself a sum
of eight sub-components (Nathonnata, Paksha, Tribhaga, the four calendar-lords, Ayana). Every
sub-component traces to a ch.27 sloka. `complete=True` now that Kala's time-based sub-components are
resolved from the birth's sunrise/calendar context (`chart.ephemeris.kala_context`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.primitives.shadbala import VIRUPAS_PER_RUPA
from app.parashara.primitives.shadbala.cheshta import cheshta_bala
from app.parashara.primitives.shadbala.dig import dig_bala
from app.parashara.primitives.shadbala.drik import drik_bala
from app.parashara.primitives.shadbala.kala import KalaBala, KalaContext, kala_bala
from app.parashara.primitives.shadbala.naisargika import naisargika_bala
from app.parashara.primitives.shadbala.sthana import SthanaBala, sthana_bala

#: All SIX balas are now encoded — the Shadbala is complete.
ENCODED_BALAS: Final[tuple[str, ...]] = (
    "sthana", "dig", "naisargika", "cheshta", "drik", "kala")
PENDING_BALAS: Final[tuple[str, ...]] = ()


@dataclass(frozen=True)
class PartialShadbala:
    planet: str
    sthana: SthanaBala
    dig: float
    naisargika: float
    cheshta: float
    drik: float             # aspectual — may be NEGATIVE
    kala: KalaBala          # eight sub-components; .total is the temporal strength
    complete: bool          # True — all six balas encoded

    @property
    def virupas(self) -> float:
        return (self.sthana.total + self.dig + self.naisargika + self.cheshta + self.drik
                + self.kala.total)

    @property
    def rupas(self) -> float:
        return self.virupas / VIRUPAS_PER_RUPA


def partial_shadbala(planet: str, longitudes: Mapping[str, float], *,
                     asc_sign: int, asc_longitude: float, moon_waxing: bool,
                     speed: float, ayanamsa: float, kala_ctx: KalaContext) -> PartialShadbala:
    """The full six-fold Shadbala of one graha (virupas): Sthana + Dig + Naisargika + Cheshta +
    Drik + Kala (BPHS ch.27)."""
    kala = kala_bala(planet, longitudes, moon_waxing=moon_waxing, ayanamsa=ayanamsa, ctx=kala_ctx)
    # Sun's Cheshta = its Ayana; Moon's = its Paksha; others from speed.
    cheshta = cheshta_bala(planet, speed=speed, sun_ayana=kala.ayana, moon_paksha=kala.paksha)
    planet_signs = {p: int(l % 360.0 // 30) + 1 for p, l in longitudes.items()}
    return PartialShadbala(
        planet=planet,
        sthana=sthana_bala(planet, longitudes, asc_sign=asc_sign),
        dig=dig_bala(planet, longitudes[planet], asc_longitude),
        naisargika=naisargika_bala(planet),
        cheshta=cheshta,
        drik=drik_bala(planet, planet_signs, moon_waxing=moon_waxing),
        kala=kala,
        complete=True,
    )


def partial_shadbala_all(longitudes: Mapping[str, float], *,
                         asc_sign: int, asc_longitude: float, moon_waxing: bool,
                         speeds: Mapping[str, float], ayanamsa: float,
                         kala_ctx: KalaContext) -> dict[str, PartialShadbala]:
    """Full Shadbala for each of the seven grahas present."""
    from app.parashara.primitives.relationships import GRAHAS
    return {g: partial_shadbala(g, longitudes, asc_sign=asc_sign, asc_longitude=asc_longitude,
                                moon_waxing=moon_waxing, speed=speeds.get(g, 0.0),
                                ayanamsa=ayanamsa, kala_ctx=kala_ctx)
            for g in GRAHAS if g in longitudes}
