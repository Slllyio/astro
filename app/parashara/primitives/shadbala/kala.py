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

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.functional_nature import natural_benefic

PAKSHA_SOURCE: Final[Citation] = Citation("BPHS-27", 304)

#: Sub-components of Kala bala still to encode (each needs the ephemeris time/declination layer).
PENDING_SUBCOMPONENTS: Final[tuple[str, ...]] = (
    "nathonnata", "tribhaga", "varsha", "masa", "vara", "hora", "ayana")


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
