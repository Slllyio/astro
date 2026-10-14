"""Combustion (Astangata) — a planet too close to the Sun loses its rays (BPHS ch.7).

Parashara gives a table of combustion degrees, differing for direct and retrograde motion (BPHS-7,
the "table for degrees of combustion"). A planet within that many degrees of the Sun is combust and
its results are impaired. The Sun itself cannot be combust; Rahu and Ketu "should not be treated as
combust although they may be longitudinally close to the Sun, for they are only mathematical points"
(BPHS-7:707).

Orbs as printed in this edition's table (Mercury 14/12 and Venus 10/8 match the classical standard,
confirming the reading): Moon 12 (never retrograde), Mars 17/8, Mercury 14/12, Jupiter 11/11,
Venus 10/8, Saturn 16/16. Jupiter's two cells are OCR-garbled in the scan; 11 deg is the settled
classical value and is used for both.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-7", 660)   # "the following table for degrees of combustion"

#: Combustion orb (deg) in direct motion.
_ORB_DIRECT: Final[Mapping[str, float]] = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0, "Jupiter": 11.0, "Venus": 10.0, "Saturn": 16.0}
#: Combustion orb (deg) in retrograde motion (the Moon never retrogrades).
_ORB_RETRO: Final[Mapping[str, float]] = {
    "Mars": 8.0, "Mercury": 12.0, "Jupiter": 11.0, "Venus": 8.0, "Saturn": 16.0}


def _sep(a: float, b: float) -> float:
    """Circular separation in degrees (0..180) — the platform's min(diff, 360-diff) convention."""
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def is_combust(planet: str, planet_longitude: float, sun_longitude: float, *,
               retrograde: bool = False) -> bool:
    """True if `planet` is combust — within its BPHS orb of the Sun (BPHS ch.7).

    The Sun (the source) and the nodes (mathematical points) are never combust. Retrograde uses the
    smaller retro orb where the table gives one.
    """
    if planet in ("Sun", "Rahu", "Ketu"):
        return False
    orb = _ORB_RETRO.get(planet) if retrograde else _ORB_DIRECT.get(planet)
    if orb is None:
        orb = _ORB_DIRECT.get(planet)
    if orb is None:
        return False
    return _sep(planet_longitude, sun_longitude) < orb


def combust_planets(longitudes: Mapping[str, float], *,
                    speeds: Mapping[str, float] | None = None) -> tuple[str, ...]:
    """Every combust graha in the chart (BPHS ch.7). `speeds` (deg/day; <0 retrograde) selects the
    retro orb where available; omit it to use direct orbs throughout."""
    sun = longitudes.get("Sun")
    if sun is None:
        return ()
    out: list[str] = []
    for p, lon in longitudes.items():
        retro = bool(speeds and speeds.get(p, 0.0) < 0.0)
        if is_combust(p, lon, sun, retrograde=retro):
            out.append(p)
    return tuple(out)
