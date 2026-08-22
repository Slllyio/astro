"""Dig bala — directional strength (BPHS ch.27, slokas 7-7.5).

Each planet has a direction of full strength and is powerless 180 degrees away:
    Jupiter, Mercury -> Ascendant (east) ; Venus, Moon -> 4th (north) ;
    Saturn -> 7th (west)                 ; Sun, Mars -> 10th (south).

    "Deduct the 4th house from Sun and Mars; the 7th from Jupiter and Mercury; the 10th from Venus
     and the Moon; the ascendant from Saturn. If the sum is above 180 deduct from 360 ... divided by
     3 ... full on the cusp = 1 Rupa." (BPHS-27:201)

The point DEDUCTED is the powerless point (opposite the full point). Distance from it / 3 = virupas,
max 60 at the full cusp.

Cusp approximation: this engine's chart carries the ascendant degree but not every bhava madhya, so
the Nth cusp is taken as `asc_longitude + (N-1)*30` (equal-house from the ascendant degree). BPHS's
strict Dig bala uses the chalit bhava madhya; the equal-house cusp is a documented approximation
that is exact for the ascendant/7th and close elsewhere. Flagged so it can be tightened when bhava
madhyas are carried.
"""
from __future__ import annotations

from typing import Final

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-27", 201)

#: The house whose cusp is the planet's POWERLESS point (opposite its full-strength direction).
_POWERLESS_HOUSE: Final[dict[str, int]] = {
    "Sun": 4, "Mars": 4,          # full at 10th (south)
    "Jupiter": 7, "Mercury": 7,   # full at 1st (east)
    "Venus": 10, "Moon": 10,      # full at 4th (north)
    "Saturn": 1,                  # full at 7th (west)
}


def dig_bala(planet: str, longitude: float, asc_longitude: float) -> float:
    """Directional strength of `planet` in virupas (0..60).

    Args:
        planet: the graha.
        longitude: its sidereal longitude (deg).
        asc_longitude: the ascendant's longitude (deg) — used for the equal-house cusps.
    """
    if planet not in _POWERLESS_HOUSE:
        raise ValueError(f"Dig bala is defined for the seven grahas, not {planet!r}")
    powerless_cusp = (asc_longitude + (_POWERLESS_HOUSE[planet] - 1) * 30.0) % 360.0
    diff = (longitude - powerless_cusp) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff            # distance from the powerless point, 0..180
    return diff / 3.0                  # 0 at powerless, 60 at the full cusp (180 deg away)
