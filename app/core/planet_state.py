"""Per-planet state primitives: combustion, vargottama, retrograde.

These are the small, well-defined deterministic checks that Phase-0
strength scoring and the broader yoga catalog (Phase 2) repeatedly need.

References:
- Combustion (Asta): BPHS Adhyaya 27 — orb in degrees from the Sun
  varies per planet.
- Vargottama: planet in the same rashi in D1 (Rashi) and D9 (Navamsa).
- Retrograde (Vakri): ecliptic longitude speed < 0; passed through from
  the ephemeris layer.

The project uses Lahiri sidereal longitudes; combustion arithmetic is
ayanamsa-invariant because both the Sun's and the planet's longitudes
are reported in the same frame.
"""
from __future__ import annotations

# BPHS Adhyaya 27 combustion orbs (degrees of ecliptic separation).
# Mercury and Venus have alternative smaller orbs while retrograde in
# some traditions; the orb-by-retrograde refinement is a Phase-1 task.
COMBUSTION_ORBS: dict[str, float] = {
    "Moon":    12.0,
    "Mars":    17.0,
    "Mercury": 14.0,
    "Jupiter": 11.0,
    "Venus":   10.0,
    "Saturn":  15.0,
}

# Planets that the combustion concept does not apply to.
_UNCOMBUSTIBLE: frozenset[str] = frozenset({"Sun", "Rahu", "Ketu"})


def combustion_orb(planet: str) -> float | None:
    """Return the BPHS combustion orb (degrees) for ``planet``.

    Returns ``None`` for Sun, Rahu, Ketu — those are not subject to
    combustion. Raises ``ValueError`` for unknown planet names.
    """
    if planet in _UNCOMBUSTIBLE:
        return None
    orb = COMBUSTION_ORBS.get(planet)
    if orb is None:
        raise ValueError(f"unknown planet: {planet!r}")
    return orb


def angular_separation(lon1: float, lon2: float) -> float:
    """Shortest arc between two ecliptic longitudes in degrees ([0, 180]).

    Inputs may lie outside ``[0, 360)``; both are normalised modulo 360
    before the arc is taken. The result is the circular distance, never
    the signed difference — callers that need direction must compute it
    themselves.
    """
    diff = (lon1 - lon2) % 360.0
    return min(diff, 360.0 - diff)


def is_combust(planet: str, planet_lon: float, sun_lon: float) -> bool:
    """True when ``planet`` is within its BPHS combustion orb of the Sun.

    The boundary is inclusive (a planet exactly at the orb is combust),
    matching Jagannatha Hora and Parashara's Light defaults.

    Returns ``False`` for Sun (cannot combust itself) and the nodes
    (no combustion concept). Raises ``ValueError`` for unknown planets.
    """
    if planet in _UNCOMBUSTIBLE:
        return False
    orb = COMBUSTION_ORBS.get(planet)
    if orb is None:
        raise ValueError(f"unknown planet: {planet!r}")
    return angular_separation(planet_lon, sun_lon) <= orb


def is_vargottama(d1_sign: int, d9_sign: int) -> bool:
    """True when a planet occupies the same rashi in D1 and D9.

    Vargottama is a major strengthening factor in classical scoring —
    treated as ``own sign`` for the divisional even when the planet isn't
    in its sva-kshetra.

    Both arguments are 1-indexed (1=Aries, 12=Pisces). Raises
    ``ValueError`` for out-of-range signs.
    """
    if not (1 <= d1_sign <= 12):
        raise ValueError(f"d1_sign out of range: {d1_sign!r}")
    if not (1 <= d9_sign <= 12):
        raise ValueError(f"d9_sign out of range: {d9_sign!r}")
    return d1_sign == d9_sign


def is_retrograde(planet_entry: dict | None) -> bool:
    """Return whether the chart entry indicates retrograde motion.

    Defensive: missing entry or missing flag is treated as direct motion.
    """
    if not planet_entry:
        return False
    return bool(planet_entry.get("is_retrograde", False))


__all__ = [
    "COMBUSTION_ORBS",
    "combustion_orb",
    "angular_separation",
    "is_combust",
    "is_vargottama",
    "is_retrograde",
]
