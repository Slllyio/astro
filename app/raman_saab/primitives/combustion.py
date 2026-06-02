from __future__ import annotations
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.relationships import COMBUSTION_ORB


def _circ_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def combust_fraction(planet: str, chart: RamanChart) -> float:
    """0.0 (free) .. 1.0 (exact conjunction with Sun), linear within the planet's orb."""
    if planet not in COMBUSTION_ORB or planet not in chart.planets or "Sun" not in chart.planets:
        return 0.0
    orb = COMBUSTION_ORB[planet]
    sep = _circ_sep(chart.planets[planet].lon, chart.planets["Sun"].lon)
    if sep >= orb:
        return 0.0
    return round(1.0 - sep / orb, 6)
