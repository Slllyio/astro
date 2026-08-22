"""Kala bala — temporal strength (BPHS ch.27). COMPLETE: all sub-components encoded.

Kala bala is a sum of sub-components (BPHS-27:241-263): Nathonnata (diurnal/nocturnal), Paksha
(lunar fortnight), Tribhaga (day/night thirds), Varsha/Masa/Dina/Hora (the four calendar-lords),
and Ayana (equinoctial). Paksha and Ayana depend only on longitudes/ayanamsa; the other four
depend on the birth's TIME facts — day-or-night, which third, the clock hour, and the year/month/
weekday/hora lords — which the ephemeris layer resolves once (`chart.ephemeris.kala_context`) into
a `KalaContext`. This module owns that contract (its own input type) and consumes it; the astronomy
layer fills it, so the dependency runs primitive <- chart, never the reverse.

    "Deduct the Sun's longitude from the Moon's; if above 6 signs deduct from 12; convert to degrees
     and divide by 3 = the Paksha bala of each benefic. A malefic's Paksha bala = 60 minus the
     benefic's. The Moon's Paksha bala is always doubled." (BPHS-27:304-326)
    "Find the difference between midnight and apparent birth time (Unnata); Nata = 30 ghatis - Unnata;
     Natha bala for Moon/Mars/Saturn = Nata x 2; the Sun/Jupiter/Venus get 60 - that; Mercury full."
     (BPHS-27:232-239)
    "Tribhaga: 1 Rupa to Mercury/Sun/Saturn in the 1st/2nd/3rd third of day, to Moon/Venus/Mars in
     the thirds of night; Jupiter always. Two planets get it." (BPHS-27:330-359)
    "Varsha-Masa-Dina-Hora: 15, 30, 45, 60 virupas to the year/month/weekday/hora lord." (BPHS-27:363)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.functional_nature import natural_benefic

PAKSHA_SOURCE: Final[Citation] = Citation("BPHS-27", 304)
AYANA_SOURCE: Final[Citation] = Citation("BPHS-27", 1451)
NATHONNATA_SOURCE: Final[Citation] = Citation("BPHS-27", 232)
TRIBHAGA_SOURCE: Final[Citation] = Citation("BPHS-27", 330)
CALENDAR_SOURCE: Final[Citation] = Citation("BPHS-27", 363)

#: Every Kala sub-component is now encoded — nothing pending.
PENDING_SUBCOMPONENTS: Final[tuple[str, ...]] = ()


@dataclass(frozen=True)
class KalaContext:
    """The birth's time facts the time-dependent Kala sub-components need (BPHS ch.27).

    This is Kala bala's own input contract. `chart.ephemeris.kala_context` resolves it once from the
    birth moment + place (sunrise/sunset, the Ahargana calendar-lords, the planetary hour); the four
    time-based sub-components below read it. Defined HERE, not in the astronomy layer, so the import
    runs primitive <- chart.
    """
    is_day: bool               # birth between sunrise and sunset
    day_third: int             # 1, 2 or 3 — the third of the day (or night) of birth
    unnata_fraction: float     # 0 at (apparent) midnight -> 1 at noon (for Nathonnata)
    weekday_lord: str          # Vara/Dina lord (45 virupas)
    hora_lord: str             # planetary-hour lord (60 virupas)
    varsha_lord: str           # astrological-year lord (15 virupas)
    masa_lord: str             # astrological-month lord (30 virupas)


#: Diurnally strong / nocturnally strong groups for Nathonnata (BPHS-27:265-266).
_DAY_STRONG: Final[frozenset[str]] = frozenset({"Sun", "Jupiter", "Venus"})
_NIGHT_STRONG: Final[frozenset[str]] = frozenset({"Moon", "Mars", "Saturn"})
#: The planet ruling each third of day / of night (BPHS-27:348-353).
_TRIBHAGA_DAY: Final[Mapping[int, str]] = {1: "Mercury", 2: "Sun", 3: "Saturn"}
_TRIBHAGA_NIGHT: Final[Mapping[int, str]] = {1: "Moon", 2: "Venus", 3: "Mars"}

#: Obliquity of the ecliptic (deg) — 23 deg 27', the value BPHS uses for the Ayana formula.
_OBLIQUITY: Final[float] = 23.0 + 27.0 / 60.0
#: 60 / 46 deg 54' = 1.2793 — the sloka's own constant (max Kranti span is 2 x obliquity).
_AYANA_K: Final[float] = 60.0 / (2.0 * _OBLIQUITY)

#: Planets whose NORTHERN declination is favourable (take +Kranti); the others favour Southern.
_NORTH_FAVOURED: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Jupiter", "Venus"})
_SOUTH_FAVOURED: Final[frozenset[str]] = frozenset({"Moon", "Saturn"})


def _benefic_paksha(longitudes: Mapping[str, float]) -> float:
    """The benefic Paksha value = |Moon - Sun| (<=180) / 3, in virupas (0..60)."""
    diff = (longitudes["Moon"] - longitudes["Sun"]) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff / 3.0


def paksha_bala(planet: str, longitudes: Mapping[str, float], *, moon_waxing: bool) -> float:
    """Paksha bala of `planet` in virupas (BPHS-27:304-326).

    Benefics get the raw benefic value; malefics get 60 minus it; the Moon's result is doubled
    ("always doubled", whichever group she falls in). Benefic/malefic is the ch.3 natural nature,
    so the Moon depends on paksha and Mercury on its company.
    """
    b = _benefic_paksha(longitudes)
    # Classify with ch.3 natural nature (Moon by paksha, Mercury by companions in its sign).
    if planet == "Moon":
        is_benefic = moon_waxing
    elif planet == "Mercury":
        msign = int(longitudes["Mercury"] % 360.0 // 30) + 1
        companions = [p for p, l in longitudes.items()
                      if p != "Mercury" and int(l % 360.0 // 30) + 1 == msign]
        is_benefic = natural_benefic("Mercury", companions=companions)
    elif planet in ("Jupiter", "Venus"):
        is_benefic = True
    else:                                   # Sun, Mars, Saturn (Rahu/Ketu have no Shadbala)
        is_benefic = False
    value = b if is_benefic else 60.0 - b
    if planet == "Moon":
        value *= 2.0                        # the Moon's Paksha bala is always doubled
    return value


def _kranti(sidereal_longitude: float, ayanamsa: float) -> float:
    """Declination (Kranti, deg) of a body: dec = asin(sin(obliquity) * sin(sayana longitude)),
    where sayana = nirayana + ayanamsa (BPHS-27:1451, "Add Ayanamsa ... find the Bhuja")."""
    sayana = math.radians((sidereal_longitude + ayanamsa) % 360.0)
    return math.degrees(math.asin(math.sin(math.radians(_OBLIQUITY)) * math.sin(sayana)))


def ayana_bala(planet: str, sidereal_longitude: float, ayanamsa: float) -> float:
    """Equinoctial strength (BPHS-27:1451-1474): (23deg27' +/- Kranti) x 1.2793, the Sun doubled.

    +Kranti when the declination is in the planet's favoured hemisphere (north for Sun/Mars/Jupiter/
    Venus, south for Moon/Saturn), -Kranti otherwise; Mercury always +. Ranges 0..60 (120 for Sun).
    """
    if planet not in _NORTH_FAVOURED and planet not in _SOUTH_FAVOURED and planet != "Mercury":
        raise ValueError(f"Ayana bala is for the seven grahas, not {planet!r}")
    decl = _kranti(sidereal_longitude, ayanamsa)
    is_north = decl >= 0.0
    if planet == "Mercury":
        favourable = True
    elif planet in _NORTH_FAVOURED:
        favourable = is_north
    else:                                    # Moon, Saturn
        favourable = not is_north
    signed = abs(decl) if favourable else -abs(decl)
    bala = (_OBLIQUITY + signed) * _AYANA_K
    return bala * 2.0 if planet == "Sun" else bala


def nathonnata_bala(planet: str, ctx: KalaContext) -> float:
    """Diurnal/nocturnal strength (BPHS-27:232-239). Day-strong grahas rise to 60 at noon,
    night-strong to 60 at (apparent) midnight; Mercury always 60."""
    if planet == "Mercury":
        return 60.0
    if planet in _DAY_STRONG:
        return 60.0 * ctx.unnata_fraction
    if planet in _NIGHT_STRONG:
        return 60.0 * (1.0 - ctx.unnata_fraction)
    raise ValueError(f"Nathonnata bala is for the seven grahas, not {planet!r}")


def tribhaga_bala(planet: str, ctx: KalaContext) -> float:
    """Strength of the third of day/night (BPHS-27:330-359). Jupiter always 60; the graha ruling
    the birth's third gets 60; every other graha 0 — so exactly two grahas score."""
    if planet == "Jupiter":
        return 60.0
    ruler = (_TRIBHAGA_DAY if ctx.is_day else _TRIBHAGA_NIGHT)[ctx.day_third]
    return 60.0 if planet == ruler else 0.0


def vara_bala(planet: str, ctx: KalaContext) -> float:
    """Weekday-lord strength: 45 virupas to the Dina (Vara) lord, else 0 (BPHS-27:363)."""
    return 45.0 if planet == ctx.weekday_lord else 0.0


def hora_bala(planet: str, ctx: KalaContext) -> float:
    """Planetary-hour strength: 60 virupas to the Hora lord, else 0 (BPHS-27:363)."""
    return 60.0 if planet == ctx.hora_lord else 0.0


def masa_bala(planet: str, ctx: KalaContext) -> float:
    """Astrological-month-lord strength: 30 virupas to the Masa lord, else 0 (BPHS-27:363)."""
    return 30.0 if planet == ctx.masa_lord else 0.0


def varsha_bala(planet: str, ctx: KalaContext) -> float:
    """Astrological-year-lord strength: 15 virupas to the Varsha (Abda) lord, else 0 (BPHS-27:363)."""
    return 15.0 if planet == ctx.varsha_lord else 0.0


@dataclass(frozen=True)
class KalaBala:
    """All sub-components of Kala bala for one graha (BPHS ch.27), in virupas.

    Eight in total: Nathonnata, Paksha, Tribhaga, the four calendar-lords (Varsha/Masa/Vara/Hora),
    and Ayana. `.total` is the graha's whole temporal strength.
    """
    nathonnata: float
    paksha: float
    tribhaga: float
    varsha: float
    masa: float
    vara: float
    hora: float
    ayana: float

    @property
    def total(self) -> float:
        return (self.nathonnata + self.paksha + self.tribhaga + self.varsha
                + self.masa + self.vara + self.hora + self.ayana)


def kala_bala(planet: str, longitudes: Mapping[str, float], *,
              moon_waxing: bool, ayanamsa: float, ctx: KalaContext) -> KalaBala:
    """The full Kala bala of `planet` — every sub-component (BPHS ch.27)."""
    return KalaBala(
        nathonnata=nathonnata_bala(planet, ctx),
        paksha=paksha_bala(planet, longitudes, moon_waxing=moon_waxing),
        tribhaga=tribhaga_bala(planet, ctx),
        varsha=varsha_bala(planet, ctx),
        masa=masa_bala(planet, ctx),
        vara=vara_bala(planet, ctx),
        hora=hora_bala(planet, ctx),
        ayana=ayana_bala(planet, longitudes[planet], ayanamsa),
    )
