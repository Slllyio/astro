"""Kala bala — temporal strength (BPHS ch.27). PARTIAL: Paksha bala encoded.

Kala bala is itself a sum of sub-components (BPHS-27:248-263): Nathonnata (diurnal/nocturnal),
Paksha (lunar fortnight), Tribhaga (day/night thirds), Varsha/Masa/Dina/Hora (calendar-lords),
Ayana (equinoctial). Most of those need an ephemeris TIME layer this engine's chart does not yet
carry — sunrise/sunset for day-night, tribhaga and the hora sequence; the weekday and clock hour
for the calendar-lords; declination for Ayana. Building that layer faithfully (not by approximation,
per the Prime Directive) is a named next task.

**Paksha bala** needs none of that — only the Sun-Moon elongation — so it is encoded now, fully.

    "Deduct the Sun's longitude from the Moon's; if above 6 signs deduct from 12; convert to degrees
     and divide by 3 = the Paksha bala of each benefic. A malefic's Paksha bala = 60 minus the
     benefic's. The Moon's Paksha bala is always doubled." (BPHS-27:304-326)
"""
from __future__ import annotations

import math
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.functional_nature import natural_benefic

PAKSHA_SOURCE: Final[Citation] = Citation("BPHS-27", 304)
AYANA_SOURCE: Final[Citation] = Citation("BPHS-27", 1451)

#: Sub-components of Kala bala still to encode. Paksha and Ayana are done; the rest need the
#: birth-time / sunrise / Hindu-calendar layer (day-night thirds, planetary-hour and weekday/
#: month/year lords) — and Nathonnata's OCR polarity is ambiguous, so it is deferred rather than
#: risk inverting the day/night sign.
PENDING_SUBCOMPONENTS: Final[tuple[str, ...]] = (
    "nathonnata", "tribhaga", "varsha", "masa", "vara", "hora")

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
