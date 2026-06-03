"""Ishta Phala and Kashta Phala — benefic/malefic strength sub-scores (GBB-10).

Usage:
    from app.raman_saab.primitives.shadbala import ishta_kashta as ik
    ik.ishta_phala(ochcha_bala, chesta_bala)
    ik.kashta_phala(ochcha_bala, chesta_bala)
    ik.sun_chesta_surrogate(sayana_sun_lon)
    ik.moon_chesta_surrogate(moon_lon, sun_lon)
"""
from __future__ import annotations
import math


def ishta_phala(ochcha_bala: float, chesta_bala: float) -> float:
    """Benefic effect = sqrt(Ochcha × Chesta), Shashtiamsas 0-60 (GBB-10:93)."""
    return round(math.sqrt(max(0.0, ochcha_bala) * max(0.0, chesta_bala)), 3)


def kashta_phala(ochcha_bala: float, chesta_bala: float) -> float:
    """Malefic effect = sqrt((60−Ochcha) × (60−Chesta)), Shashtiamsas 0-60 (GBB-10:114)."""
    return round(math.sqrt(max(0.0, 60.0 - ochcha_bala) * max(0.0, 60.0 - chesta_bala)), 3)


def sun_chesta_surrogate(sayana_sun_lon: float) -> float:
    """Sun has no true Cheshta; for Ishta/Kashta use CK = (Sayana + 90) folded, /3 (GBB-10:46)."""
    ck = (sayana_sun_lon + 90.0) % 360.0
    if ck > 180.0:
        ck = 360.0 - ck
    return round(ck / 3.0, 3)


def moon_chesta_surrogate(moon_lon: float, sun_lon: float) -> float:
    """Moon Cheshta surrogate = (Moon − Sun) folded, /3 (GBB-10:72)."""
    ck = (moon_lon - sun_lon) % 360.0
    if ck > 180.0:
        ck = 360.0 - ck
    return round(ck / 3.0, 3)
