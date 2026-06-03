"""Shadbala total assembly and minimum-required verdict.

Usage:
    from app.raman_saab.primitives.shadbala.total import assemble_shadbala, is_powerful, MIN_REQUIRED

    br = assemble_shadbala(sthana, dig, kala, cheshta, naisargika, drik)
    # br.total is in Shashtiamsas; Rupas = br.total / 60
    powerful = is_powerful("Mercury", br.total / 60)
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.model import ShadbalaBreakdown

# Minimum-required total Shadbala in Rupas per planet (GBB-8:303-312).
MIN_REQUIRED: Final[dict[str, float]] = {
    "Sun": 5.0,
    "Moon": 6.0,
    "Mars": 5.0,
    "Mercury": 7.0,
    "Jupiter": 6.5,
    "Venus": 5.5,
    "Saturn": 5.0,
}


def assemble_shadbala(
    sthana: float,
    dig: float,
    kala: float,
    cheshta: float,
    naisargika: float,
    drik: float,
) -> ShadbalaBreakdown:
    """Sum the six components (Shashtiamsas; Drik is signed) into a ShadbalaBreakdown.

    `total` is in Shashtiamsas; divide by 60 for Rupas (GBB-8:262).
    Drik Bala is already signed (negative when net malefic aspects dominate) and
    is added directly — it must not be abs()-ed here.
    """
    total_sh = sthana + dig + kala + cheshta + naisargika + drik
    return ShadbalaBreakdown(
        sthana=sthana,
        dig=dig,
        kala=kala,
        cheshta=cheshta,
        naisargika=naisargika,
        drik=drik,
        total=round(total_sh, 3),
    )


def is_powerful(planet: str, total_rupas: float) -> bool:
    """True iff the planet's total Shadbala (Rupas) meets its minimum required (GBB-8:303)."""
    req = MIN_REQUIRED.get(planet)
    return req is not None and total_rupas >= req
