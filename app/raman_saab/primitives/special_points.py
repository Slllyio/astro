from __future__ import annotations
from app.raman_saab.chart.model import RamanChart, SpecialPoint
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart import varga

_SEVEN: tuple[str, ...] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def atmakaraka(chart: RamanChart) -> str:
    """Strict 7-karaka Jaimini Atmakaraka: the planet with the highest degree-within-sign
    among the 7 visible planets. Rahu/Ketu are chayagrahas and CANNOT be AK (CLAUDE.md)."""
    present = [p for p in _SEVEN if p in chart.planets]
    return max(present, key=lambda p: chart.planets[p].lon % 30.0)


def karakamsa(chart: RamanChart) -> SpecialPoint:
    """Karakamsa = the Atmakaraka's navamsa sign, as a point (judged as a lagna in D9)."""
    ak = chart.planets[atmakaraka(chart)]
    sign = ak.navamsa_sign
    bhava = ((sign - chart.asc_sign) % 12) + 1     # rasi-house of the karakamsa sign
    # lon represents the navamsa SIGN this point stands for (not the AK's rasi lon) -> consistent
    return SpecialPoint(name="Karakamsa", lon=float((sign - 1) * 30), sign=sign, bhava=bhava,
                        navamsa_sign=sign)


def navamsa_lagna(chart: RamanChart) -> SpecialPoint:
    """The Navamsa (D9) ascendant — the navamsa of the rasi-lagna degree. Raman reads the body and
    temperament from the navamsa-lagna and its lord alongside the rasi-lagna."""
    sign = varga.navamsa_sign(chart.asc_lon)
    return SpecialPoint(name="NavamsaLagna", lon=chart.asc_lon, sign=sign,
                        bhava=((sign - chart.asc_sign) % 12) + 1, navamsa_sign=sign)


def navamsa_lagna_lord(chart: RamanChart) -> str:
    """Lord of the navamsa Lagna sign."""
    return SIGN_LORDS[varga.navamsa_sign(chart.asc_lon)]


def navamsa_seventh_lord(chart: RamanChart) -> str:
    """Lord of the 7th from the navamsa Lagna — Raman's spouse significator in the D9
    ('the 7th from Navamsha Lagna judges the spouse', HtJaH)."""
    nl = varga.navamsa_sign(chart.asc_lon)
    return SIGN_LORDS[((nl - 1 + 6) % 12) + 1]


def arudha_lagna(chart: RamanChart) -> SpecialPoint:
    """Jaimini Arudha (Pada) Lagna as a point. Delegates the sign to the single-source-of-truth
    formula in primitives/arudha.py (count from the lagna-lord; 1st/7th -> 10th); falls back to the
    Lagna itself only when the lagna-lord is absent (sparse Track-B chart)."""
    from app.raman_saab.primitives.arudha import arudha_pada
    a = arudha_pada(chart, 1)
    if a is None:                                   # lagna-lord absent (sparse chart)
        a = chart.asc_sign
    bhava = ((a - chart.asc_sign) % 12) + 1
    return SpecialPoint(name="ArudhaLagna", lon=float((a - 1) * 30), sign=a, bhava=bhava,
                        navamsa_sign=varga.navamsa_sign(float((a - 1) * 30)))
