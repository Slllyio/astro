from __future__ import annotations

from typing import Final, Mapping

from app.raman_saab.chart.model import RamanChart

# The 5 planets that receive Cheshta Bala. Sun & Moon get NONE in the Shadbala total
# (GBB-6:23-28); their surrogates are computed only for Ishta/Kashta (Phase 1c-3).
PLANETS: Final[tuple[str, ...]] = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def chesta_kendra(seegrochcha: float, mean_lon: float, true_lon: float) -> float:
    """Sripathi Chesta Kendra (Arc of Retrogression), degrees 0..360.

    CK = Seegrochcha − (Mean + True)/2  (OCR-corrected; GBB-6:544-551 + external Sripathi).
    """
    ck = (seegrochcha - (mean_lon + true_lon) / 2.0) % 360.0
    return ck


def cheshta_bala(seegrochcha: float, mean_lon: float, true_lon: float) -> float:
    """Cheshta Bala in Shashtiamsas = reduced Chesta Kendra / 3 (0 at 0°, 60 at 180°)."""
    ck = chesta_kendra(seegrochcha, mean_lon, true_lon)
    if ck > 180.0:
        ck = 360.0 - ck
    return round(ck / 3.0, 3)


def cheshta_bala_for_chart(
    planet: str,
    chart: RamanChart,
    means: Mapping[str, float],
    seegrochchas: Mapping[str, float],
) -> float:
    """Chart-level Cheshta: 0 for Sun/Moon/nodes, else the formula using the supplied
    mean longitudes + seegrochchas and the planet's true longitude from the chart."""
    if planet not in PLANETS or planet not in chart.planets:
        return 0.0
    return cheshta_bala(seegrochchas[planet], means[planet], chart.planets[planet].lon)
