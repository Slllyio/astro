"""Sphuta numeric sub-engines — chart-level GATES Raman computes before (or
beside) judging a house, not Phase-D enrichments (doctrinal review promotion #6).

1. Beeja / Kshetra sphuta — the H5 fertility gate (HTJAH-I:5517-5527):
   Beeja (male seed)   = Sun + Venus + Jupiter, multiples of 360 expunged;
   Kshetra (female bed) = Mars + Moon + Jupiter, multiples of 360 expunged.
   Beeja must occupy an ODD sign and ODD navamsa; Kshetra an EVEN sign and
   EVEN navamsa (Raman's printed requirement — the two are mirrored, NOT both
   odd). The further textual conditions — benefic aspect/association, no evil
   planet in the 5th from the sphuta, not in a malefic sign, Rahu never joining
   (HTJAH-I:5521-5527) — are aspect-level doctrine checks that belong to the
   H5 judge, not to this pure numeric gate.

2. Special Dhana Lagna — H2 "A New Method of Examining Financial Prospects"
   (HTJAH-I:3229-3318): kala root numbers of the lords of the 9th from Lagna
   and from the Moon, summed, divided by 12; the remainder counted inclusively
   from Chandra Lagna (remainder 1 = the Moon's own sign, per worked Chart 49).

3. Sahams — the two sahams Raman cites for the 9th house (HTJAH-II:8664-8675):
   Paradesha (foreign country) = 9th house - 9th lord + Lagna lord;
   Jalapathana (voyage)        = Cancer 15 - Saturn + Lagna.
   30 degrees are added when the Lagna does not lie between the two values.
   NOTE (a): the printed Paradesha formula (HTJAH-II:8668) reads "+ Ascendant",
   but ALL FIVE worked charts (108-112) compute "+ Lagna lord"; the worked
   form is implemented. NOTE (b): "between" is operationalised as the shorter
   zodiacal arc between term (a) and term (b) — the only reading consistent
   with all ten worked computations (charts 108-112, both sahams each).
   No day/night variant is printed in HTJAH for these two sahams.

Skipped sahams (cited only in Varshaphal, an annual-chart context, not in the
HTJAH 9th-house corpus): Punya, Guru, Kirthi, Mitra, Raja, Putra, Jeeva,
Vyapara and the rest of the 64/21 Varshaphal list — see
``data/knowledge_library/sources/varshaphal_raman/chapter_007_yogas-sahams-etc.md``.

All longitudes come from ``chart.planets[name].lon``; pure functions, no
ephemeris calls. Sparse Track-B charts (missing planets) return ``None`` /
omit the saham instead of raising, per the Phase-1b primitives convention.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping, Optional

from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.sources import Citation

logger = logging.getLogger(__name__)

_BEEJA_PLANETS: Final[tuple[str, ...]] = ("Sun", "Venus", "Jupiter")
_KSHETRA_PLANETS: Final[tuple[str, ...]] = ("Mars", "Moon", "Jupiter")

#: Kala (rays) root numbers of the seven planets (HTJAH-I:3247-3255).
KALA_ROOT_NUMBERS: Final[Mapping[str, int]] = MappingProxyType({
    "Sun": 30, "Moon": 16, "Mars": 6, "Mercury": 8,
    "Jupiter": 10, "Venus": 12, "Saturn": 1,
})

#: Cancer 15 degrees — the fixed first term of the Jalapathana saham (HTJAH-II:8671).
_CANCER_15: Final[float] = 105.0

BEEJA_KSHETRA_CITATIONS: Final[tuple[Citation, ...]] = (
    Citation("HTJAH-I", 5517),   # Beeja = Sun + Venus + Jupiter, expunge 360s
    Citation("HTJAH-I", 5519),   # Kshetra = Mars + Moon + Jupiter
    Citation("HTJAH-I", 5521),   # Beeja: odd sign AND odd navamsa
    Citation("HTJAH-I", 5523),   # Kshetra: even sign AND even navamsa
    Citation("HTJAH-I", 5600),   # worked Chart 90: 271 = Capricorn 1 (even -> sterile)
)

DHANA_LAGNA_CITATIONS: Final[tuple[Citation, ...]] = (
    Citation("HTJAH-I", 3249),   # kala root numbers table
    Citation("HTJAH-I", 3257),   # lords of the 9th from Lagna and the Moon
    Citation("HTJAH-I", 3260),   # remainder counted from Chandra Lagna
    Citation("HTJAH-I", 3274),   # worked Chart 49 (remainder 1 = Moon's sign)
)

PARADESHA_CITATIONS: Final[tuple[Citation, ...]] = (
    Citation("HTJAH-II", 8668),  # printed formula ("+ Ascendant" — see module note a)
    Citation("HTJAH-II", 8674),  # +30 when the Ascendant does not lie between a and b
    Citation("HTJAH-II", 9181),  # worked Chart 109: "+ Lagna lord" form
    Citation("HTJAH-II", 9231),  # worked Chart 110: no +30, Lagna between
)

JALAPATHANA_CITATIONS: Final[tuple[Citation, ...]] = (
    Citation("HTJAH-II", 8671),  # printed formula: Cancer 15 - Saturn + Ascendant
    Citation("HTJAH-II", 8674),  # +30 rule
    Citation("HTJAH-II", 9193),  # worked Chart 109
    Citation("HTJAH-II", 9245),  # worked Chart 110
)


@dataclass(frozen=True)
class BeejaKshetra:
    """H5 fertility gate: both sensitive points with Raman's odd/even verdicts."""
    beeja_lon: float
    beeja_sign: int
    beeja_navamsa_sign: int
    beeja_strong: bool        # odd sign AND odd navamsa (HTJAH-I:5521-5522)
    kshetra_lon: float
    kshetra_sign: int
    kshetra_navamsa_sign: int
    kshetra_strong: bool      # even sign AND even navamsa (HTJAH-I:5523-5524)
    citations: tuple[Citation, ...]


@dataclass(frozen=True)
class DhanaLagna:
    """Raman's Special (Dhana) Lagna from the H2 'New Method' (HTJAH-I:3229-3318)."""
    sign: int                       # rasi 1..12 of the Special Dhana Lagna
    lord_ninth_from_lagna: str
    lord_ninth_from_moon: str
    root_total: int                 # sum of the two kala root numbers
    remainder: int                  # total mod 12, with 0 recorded as 12 (unprinted edge)
    citations: tuple[Citation, ...]


@dataclass(frozen=True)
class Saham:
    """A computed saham as a SpecialPoint-like frozen record."""
    name: str
    lon: float
    sign: int
    sign_lord: str
    rasi_house: int                 # whole-sign house counted from the Lagna
    navamsa_sign: int
    added_30: bool                  # True when the +30 correction was applied
    citations: tuple[Citation, ...]


def _sign_of(lon: float) -> int:
    """1-indexed rasi of a longitude (floor semantics: 30.0 is Taurus)."""
    return int((lon % 360.0) // 30.0) + 1


def _sum_longitudes(chart: RamanChart, names: tuple[str, ...]) -> Optional[float]:
    """Sum the named planets' longitudes mod 360, or None if any is absent."""
    missing = [n for n in names if n not in chart.planets]
    if missing:
        logger.debug("sphuta skipped - missing planets: %s", missing)
        return None
    return sum(chart.planets[n].lon for n in names) % 360.0


def beeja_sphuta(chart: RamanChart) -> Optional[float]:
    """Beeja (male seed) longitude = (Sun + Venus + Jupiter) mod 360
    (HTJAH-I:5517-5518). None when a required planet is absent."""
    return _sum_longitudes(chart, _BEEJA_PLANETS)


def kshetra_sphuta(chart: RamanChart) -> Optional[float]:
    """Kshetra (female bed) longitude = (Mars + Moon + Jupiter) mod 360
    (HTJAH-I:5519-5520). None when a required planet is absent."""
    return _sum_longitudes(chart, _KSHETRA_PLANETS)


def beeja_kshetra(chart: RamanChart) -> Optional[BeejaKshetra]:
    """The H5 fertility GATE: both sphutas with Raman's odd/even classification.

    Beeja is strong in an ODD sign and ODD navamsa; Kshetra is strong in an
    EVEN sign and EVEN navamsa (HTJAH-I:5521-5524). Benefic-aspect, malefic-sign
    and Rahu-conjunction conditions (HTJAH-I:5524-5527) are left to the H5
    judge — this is the pure numeric component. None if any of the five
    required planets is absent (sparse Track-B charts must not crash)."""
    beeja = beeja_sphuta(chart)
    kshetra = kshetra_sphuta(chart)
    if beeja is None or kshetra is None:
        return None
    beeja_sign = _sign_of(beeja)
    beeja_nav = varga.navamsa_sign(beeja)
    kshetra_sign = _sign_of(kshetra)
    kshetra_nav = varga.navamsa_sign(kshetra)
    return BeejaKshetra(
        beeja_lon=beeja, beeja_sign=beeja_sign, beeja_navamsa_sign=beeja_nav,
        beeja_strong=(beeja_sign % 2 == 1 and beeja_nav % 2 == 1),
        kshetra_lon=kshetra, kshetra_sign=kshetra_sign,
        kshetra_navamsa_sign=kshetra_nav,
        kshetra_strong=(kshetra_sign % 2 == 0 and kshetra_nav % 2 == 0),
        citations=BEEJA_KSHETRA_CITATIONS)


def special_dhana_lagna(chart: RamanChart) -> Optional[DhanaLagna]:
    """Raman's 'New Method' Special Dhana Lagna (HTJAH-I:3247-3272).

    Take the lords of the 9th from Lagna and from the Moon; add their kala
    root numbers; divide by 12; the remainder counted INCLUSIVELY from Chandra
    Lagna (remainder 1 = the Moon's own sign, per worked Chart 49,
    HTJAH-I:3274-3277) is the Special Dhana Lagna. A zero remainder is not
    printed by Raman; it is recorded as 12 (the 12th sign from the Moon),
    the only continuation of his inclusive count. None when the Moon is absent."""
    if "Moon" not in chart.planets:
        logger.debug("special_dhana_lagna skipped - Moon absent")
        return None
    moon_sign = chart.planets["Moon"].sign
    ninth_from_lagna = ((chart.asc_sign - 1 + 8) % 12) + 1
    ninth_from_moon = ((moon_sign - 1 + 8) % 12) + 1
    lord_lagna = SIGN_LORDS[ninth_from_lagna]
    lord_moon = SIGN_LORDS[ninth_from_moon]
    total = KALA_ROOT_NUMBERS[lord_lagna] + KALA_ROOT_NUMBERS[lord_moon]
    remainder = total % 12 or 12
    sign = ((moon_sign - 1) + (remainder - 1)) % 12 + 1
    return DhanaLagna(
        sign=sign, lord_ninth_from_lagna=lord_lagna,
        lord_ninth_from_moon=lord_moon, root_total=total,
        remainder=remainder, citations=DHANA_LAGNA_CITATIONS)


def _lagna_between(asc_lon: float, a: float, b: float) -> bool:
    """True when the Lagna lies within the SHORTER zodiacal arc between the
    saham terms (a) and (b), endpoints inclusive — the reading of Raman's
    'if the Ascendant does not lie between the two values' (HTJAH-II:8674-8675)
    consistent with all ten worked computations in charts 108-112. An exact
    180-degree separation takes the arc running zodiacally from a to b."""
    span_ab = (b - a) % 360.0
    if span_ab <= 180.0:
        start, width = a, span_ab
    else:
        start, width = b, 360.0 - span_ab
    return (asc_lon - start) % 360.0 <= width


def _build_saham(name: str, a: float, b: float, third: float,
                 chart: RamanChart, citations: tuple[Citation, ...]) -> Saham:
    """Saham = (a - b + third) mod 360, +30 when the Lagna is not between a and b."""
    lon = (a - b + third) % 360.0
    added_30 = not _lagna_between(chart.asc_lon % 360.0, a, b)
    if added_30:
        lon = (lon + 30.0) % 360.0
    sign = _sign_of(lon)
    return Saham(
        name=name, lon=lon, sign=sign, sign_lord=SIGN_LORDS[sign],
        rasi_house=((sign - chart.asc_sign) % 12) + 1,
        navamsa_sign=varga.navamsa_sign(lon), added_30=added_30,
        citations=citations)


def sahams(chart: RamanChart) -> dict[str, Saham]:
    """The two H9 sahams Raman cites (HTJAH-II:8664-8675); see module docstring
    for the worked-example pinning and the skipped Varshaphal-only sahams.

    Paradesha  = 9th house - 9th lord + Lagna lord (worked-chart form);
    Jalapathana = Cancer 15 - Saturn + Lagna.
    A saham whose inputs are absent on a sparse chart is omitted from the dict."""
    out: dict[str, Saham] = {}
    asc_lon = chart.asc_lon % 360.0
    ninth_house_lon = (asc_lon + 240.0) % 360.0
    ninth_lord = SIGN_LORDS[((chart.asc_sign - 1 + 8) % 12) + 1]
    lagna_lord = SIGN_LORDS[chart.asc_sign]
    if ninth_lord in chart.planets and lagna_lord in chart.planets:
        out["Paradesha"] = _build_saham(
            "Paradesha", ninth_house_lon, chart.planets[ninth_lord].lon,
            chart.planets[lagna_lord].lon, chart, PARADESHA_CITATIONS)
    else:
        logger.debug("Paradesha saham skipped - 9th lord %s or lagna lord %s absent",
                     ninth_lord, lagna_lord)
    if "Saturn" in chart.planets:
        out["Jalapathana"] = _build_saham(
            "Jalapathana", _CANCER_15, chart.planets["Saturn"].lon,
            asc_lon, chart, JALAPATHANA_CITATIONS)
    else:
        logger.debug("Jalapathana saham skipped - Saturn absent")
    return out
