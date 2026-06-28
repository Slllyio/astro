"""Jaimini Arudha padas — the "image / manifestation" of a bhava.

The Arudha pada of a house is found by counting from the house to its lord, then the same count
again from the lord; the resulting sign is the Arudha. Jaimini exception: if the Arudha falls in
the house itself (1st) or the 7th from it, take the 10th sign from that Arudha. The Arudha of the
Lagna is the **Arudha Lagna (AL)** — how the native is perceived by the world (status, wealth,
public image), as distinct from the Lagna (the actual self). Raman uses it for image/affluence.

Usage:
    from app.raman_saab.primitives import arudha
    al = arudha.arudha_lagna(chart)        # AL sign (1..12)
    a7 = arudha.arudha_pada(chart, 7)      # Upapada-adjacent partner image, etc.
"""
from __future__ import annotations

from typing import Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart


def arudha_pada(chart: RamanChart, house: int) -> Optional[int]:
    """Arudha pada sign (1..12) of the whole-sign `house` (counted from the Lagna). None if the
    house lord is absent (sparse Track-B)."""
    house_sign = ((chart.asc_sign - 1) + (house - 1)) % 12 + 1
    lord = SIGN_LORDS[house_sign]
    p = chart.planets.get(lord)
    if p is None:
        return None
    lord_sign = p.sign
    # count house->lord, then the same count lord-> : arudha = 2*lord - house (1-based, mod 12)
    ar = ((2 * lord_sign - house_sign - 1) % 12) + 1
    seventh = ((house_sign - 1 + 6) % 12) + 1
    if ar == house_sign or ar == seventh:           # Jaimini exception -> 10th from the Arudha
        ar = ((ar - 1 + 9) % 12) + 1
    return ar


def arudha_lagna(chart: RamanChart) -> Optional[int]:
    """Arudha Lagna (AL) — the Arudha pada of the 1st house; the native's worldly image/status."""
    return arudha_pada(chart, 1)


def upapada_lagna(chart: RamanChart) -> Optional[int]:
    """Upapada Lagna (UL) — the Arudha pada of the 12th house; the marriage/spouse image (Jaimini)."""
    return arudha_pada(chart, 12)
