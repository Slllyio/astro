"""Navāṁśa (D-9) marriage reading — a REPORT-ONLY surface.

The Navāṁśa is Raman's marriage varga *and* his general strength-check — the one division that
already modulates the D1 verdict. For MARRIAGE specifically he judges the **7th house, its lord,
the kāraka Venus, and — crucially — the 7th from the Navāṁśa lagna** ("the 7th house from the
Navamsa Lagna and its lord indicate the wife/husband", HTJAH-II). This surface reads that method
as the authoritative core and adds a report-only D-9 overlay (the navāṁśa lagna, the navāṁśa 7th,
Venus's navāṁśa dignity, the vargottama planets).

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path — the golden ratchet is
untouched by construction, exactly like ``saptamsa_reading.py`` / ``trimsamsa_health_reading.py``.

Usage:
    from app.raman_saab.judges.navamsa_marriage_reading import build_navamsa_marriage_reading
    r = build_navamsa_marriage_reading(chart)
    r.core.marital_verdict         # Raman's authoritative marital-happiness read
    r.core.navamsa_seventh_lord    # the spouse significator from the navāṁśa 7th
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.varga_chart import VargaChart, cast_varga_chart
from app.raman_saab.doctrine import drishti
from app.raman_saab.judges.house_template import judge_house
from app.raman_saab.judges.saptamsa_reading import Tagged
from app.raman_saab.judges.varga_judge import Dignity, _varga_dignity
from app.raman_saab.primitives import special_points
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import NATURAL_MALEFICS

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_KUJA_HOUSES: Final[frozenset[int]] = frozenset({2, 4, 7, 8, 12})


@dataclass(frozen=True)
class MarriageCore:
    """The AUTHORITATIVE marriage picture — Raman's real method (7th + Venus + navāṁśa-7th)."""
    seventh_sign: int
    seventh_lord: str
    seventh_lord_house: int
    seventh_lord_dignity: Dignity
    seventh_occupants: tuple[str, ...]
    seventh_aspecting: tuple[str, ...]
    venus_house: int                       # Kalatra-kāraka
    venus_dignity: Dignity
    venus_navamsa_dignity: Dignity
    navamsa_lagna_sign: int
    navamsa_seventh_lord: str              # the spouse significator (7th from navāṁśa lagna)
    kuja_dosha: bool                       # Mars in 2/4/7/8/12 from Lagna
    spouse_verdict: str
    marital_verdict: str


@dataclass(frozen=True)
class NavamsaOverlay:
    """The corroborative D-9 picture — REPORT-ONLY."""
    lagna_sign: int
    lagna_lord: str
    lagna_occupants: tuple[str, ...]
    seventh_sign: int
    seventh_occupants: tuple[str, ...]
    venus_sign: int
    venus_dignity: Dignity
    vargottama: tuple[str, ...]            # planets whose D9 sign == D1 sign


@dataclass(frozen=True)
class NavamsaMarriageReading:
    core: MarriageCore
    overlay: NavamsaOverlay
    notes: tuple[Tagged, ...]


def _house_of_sign(from_sign: int, offset: int) -> int:
    return ((from_sign - 1) + (offset - 1)) % 12 + 1


def _verdict(chart: RamanChart, house: int, sig: str) -> str:
    pf = judge_house(chart, house)
    sv = next((s for s in pf.significations if s.signification == sig), None)
    return sv.verdict if sv else "insufficient-evidence"


def _occupants(chart: RamanChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                if n in chart.planets and chart.planets[n].rasi_house == house)


def _navamsa_dignity(planet: str, chart: RamanChart) -> Dignity:
    p = chart.planets.get(planet)
    return _varga_dignity(planet, p.navamsa_sign) if p is not None else "neutral"


def _d9_occupants(vc: VargaChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                if n in vc.positions and vc.positions[n].house == house)


def _kuja_dosha(chart: RamanChart) -> bool:
    mars = chart.planets.get("Mars")
    if mars is None:
        return False
    return mars.rasi_house in _KUJA_HOUSES


def build_navamsa_marriage_reading(chart: RamanChart) -> NavamsaMarriageReading:
    """Assemble the Navāṁśa marriage reading — Raman's method decides, the D-9 overlay corroborates."""
    seventh = _house_of_sign(chart.asc_sign, 7)
    seventh_lord = SIGN_LORDS[seventh]
    sl = chart.planets.get(seventh_lord)
    venus = chart.planets.get("Venus")
    core = MarriageCore(
        seventh_sign=seventh,
        seventh_lord=seventh_lord,
        seventh_lord_house=sl.rasi_house if sl else 0,
        seventh_lord_dignity=dignity(seventh_lord, chart) if sl else "neutral",
        seventh_occupants=_occupants(chart, 7),
        seventh_aspecting=tuple(drishti.aspecting_house(7, chart)),
        venus_house=venus.rasi_house if venus else 0,
        venus_dignity=dignity("Venus", chart) if venus else "neutral",
        venus_navamsa_dignity=_navamsa_dignity("Venus", chart),
        navamsa_lagna_sign=special_points.navamsa_lagna(chart).sign,
        navamsa_seventh_lord=special_points.navamsa_seventh_lord(chart),
        kuja_dosha=_kuja_dosha(chart),
        spouse_verdict=_verdict(chart, 7, "spouse"),
        marital_verdict=_verdict(chart, 7, "marital_happiness"))

    vc = cast_varga_chart(chart, 9)
    d9_seventh = _house_of_sign(vc.lagna_sign, 7)
    vd = vc.positions.get("Venus")
    overlay = NavamsaOverlay(
        lagna_sign=vc.lagna_sign,
        lagna_lord=vc.lagna_lord,
        lagna_occupants=_d9_occupants(vc, 1),
        seventh_sign=d9_seventh,
        seventh_occupants=_d9_occupants(vc, 7),
        venus_sign=vd.sign if vd else 0,
        venus_dignity=_varga_dignity("Venus", vd.sign) if vd else "neutral",
        vargottama=tuple(n for n in _PLANET_ORDER
                         if n in chart.planets and chart.planets[n].vargottama))

    notes = (
        Tagged("Raman judges marriage from the 7th house, its lord, the kāraka Venus, and the 7th "
               "from the Navāṁśa lagna — his real method decides here.", "RAMAN_EXPLICIT",
               "HTJAH-II:225"),
        Tagged("marital happiness (7th) is judged with the spouse: HTJAH-II:200.", "RAMAN_EXPLICIT",
               "HTJAH-II:200"),
        Tagged("the D-9 overlay corroborates (report-only); vargottama planets are doubly strong.",
               "RAMAN_GENERAL_PRINCIPLE"),
    )
    return NavamsaMarriageReading(core=core, overlay=overlay, notes=notes)
