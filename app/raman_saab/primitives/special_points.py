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
    return SpecialPoint(name="Karakamsa", lon=ak.lon, sign=sign, bhava=bhava,
                        navamsa_sign=sign)


def arudha_lagna(chart: RamanChart) -> SpecialPoint:
    """Jaimini Arudha (Pada) Lagna: count from the lagna-lord as many signs as it is
    from the Lagna; if the result falls in the 1st or 7th, take the 10th from there."""
    asc = chart.asc_sign
    lord = SIGN_LORDS[asc]
    lord_house = chart.planets[lord].rasi_house if lord in chart.planets else 1
    lord_sign = ((asc - 1) + (lord_house - 1)) % 12 + 1
    a = ((lord_sign - 1) + (lord_house - 1)) % 12 + 1
    rel = ((a - asc) % 12) + 1
    if rel in (1, 7):                               # Jaimini exception
        a = ((a - 1) + 9) % 12 + 1
    bhava = ((a - asc) % 12) + 1
    return SpecialPoint(name="ArudhaLagna", lon=float((a - 1) * 30), sign=a, bhava=bhava,
                        navamsa_sign=varga.navamsa_sign(float((a - 1) * 30)))
