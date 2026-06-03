"""Dig Bala — Directional Strength (Shashtiamsas).

Usage:
    from app.raman_saab.primitives.shadbala.dig import dig_bala

Reference: B.V. Raman, *Graha & Bhava Balas* (GBB) §2 / GBB-4:35-100.

Each planet is full-strength (60 Sh) at its powerful bhava-madhya and has zero
strength at the diametrically opposite bhava-madhya (the powerless point).
Arc is measured from the powerless madhya and divided by 3 to yield Shashtiamsas.

Documented carry-over:
    Track-B charts (from_stated_positions) have no Sripathi cusps; the equal-house
    fallback is an approximation.  The Saturn fixture pin is injected via a synthetic
    1st-madhya (294.95°).  Full Dig-column reconciliation against all 7 planets
    requires the real Sripathi cusps → deferred to Phase 1c-3 (ephemeris-cast fixture).
"""

from __future__ import annotations

from typing import Final

from app.raman_saab.chart.model import RamanChart

# Powerful house (full Dig) per planet, GBB-4:35-43.
_POWERFUL_HOUSE: Final[dict[str, int]] = {
    "Jupiter": 1, "Mercury": 1,
    "Sun": 10,    "Mars": 10,
    "Saturn": 7,
    "Moon": 4,    "Venus": 4,
}


def _powerless_madhya(planet: str, chart: RamanChart) -> float:
    """Bhava-madhya of the house OPPOSITE the planet's powerful house (the zero point)."""
    powerful = _POWERFUL_HOUSE[planet]
    powerless_house = ((powerful - 1 + 6) % 12) + 1
    if chart.bhava_madhyas:
        return chart.bhava_madhyas[powerless_house - 1]
    # ephemeris-free fallback: equal-house cusp mid-points from the Lagna
    return (chart.asc_lon + (powerless_house - 1) * 30) % 360.0


def dig_bala(planet: str, chart: RamanChart) -> float:
    """Directional strength in Shashtiamsas: arc from the powerless bhava-madhya / 3.
    Reference point is the Bhava-MADHYA cusp (GBB-4:91), not the rasi/bhava-begin.
    Returns 0.0 for nodes (Rahu/Ketu) and unknown planets."""
    if planet not in _POWERFUL_HOUSE or planet not in chart.planets:
        return 0.0
    arc = (chart.planets[planet].lon - _powerless_madhya(planet, chart)) % 360.0
    if arc > 180.0:
        arc = 360.0 - arc
    return round(arc / 3.0, 3)
