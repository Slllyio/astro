"""Siddhāṁśa (D-24) education reading — a REPORT-ONLY surface.

The Siddhāṁśa is the classical learning varga, but Raman's OWN method judges education from the
**4th house and its lord, with the kārakas Jupiter (learning) and Mercury (intellect/expression)**
("Education is generally ascertained from the 4th and the kāraka of education, viz. Jupiter",
AFB-6:23; the 4th = vidyā-sthāna, HTJAH-I:4701) — supported by the 5th (intellect). This surface
reads Raman's method as the authoritative core and adds a report-only D-24 overlay.

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path — the golden ratchet is
untouched by construction.

Usage:
    from app.raman_saab.judges.siddhamsa_education_reading import build_siddhamsa_education_reading
    r = build_siddhamsa_education_reading(chart)
    r.core.education_verdict   # Raman's authoritative education read
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
from app.raman_saab.primitives.dignity import dignity

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_EDU_KARAKAS: Final[tuple[str, ...]] = ("Jupiter", "Mercury")


@dataclass(frozen=True)
class EducationCore:
    """The AUTHORITATIVE education picture — Raman's real method (4th + Jupiter/Mercury + 5th)."""
    fourth_sign: int
    fourth_lord: str
    fourth_lord_house: int
    fourth_lord_dignity: Dignity
    fourth_occupants: tuple[str, ...]
    fourth_aspecting: tuple[str, ...]
    karakas: tuple[tuple[str, int, Dignity, Dignity], ...]  # (kāraka, house, rasi dig, navāṁśa dig)
    education_verdict: str
    intellect_verdict: str


@dataclass(frozen=True)
class SiddhamsaOverlay:
    """The corroborative D-24 picture — REPORT-ONLY."""
    lagna_sign: int
    lagna_lord: str
    lagna_occupants: tuple[str, ...]
    fourth_sign: int
    fourth_occupants: tuple[str, ...]
    jupiter_sign: int
    jupiter_dignity: Dignity
    mercury_sign: int
    mercury_dignity: Dignity


@dataclass(frozen=True)
class SiddhamsaEducationReading:
    core: EducationCore
    overlay: SiddhamsaOverlay
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


def _d24_occupants(vc: VargaChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                if n in vc.positions and vc.positions[n].house == house)


def build_siddhamsa_education_reading(chart: RamanChart) -> SiddhamsaEducationReading:
    """Assemble the Siddhāṁśa education reading — Raman's method decides, the D-24 overlay corroborates."""
    fourth = _house_of_sign(chart.asc_sign, 4)
    fourth_lord = SIGN_LORDS[fourth]
    fl = chart.planets.get(fourth_lord)
    karakas = tuple(
        (k, chart.planets[k].rasi_house, dignity(k, chart), _navamsa_dignity(k, chart))
        for k in _EDU_KARAKAS if k in chart.planets)
    core = EducationCore(
        fourth_sign=fourth,
        fourth_lord=fourth_lord,
        fourth_lord_house=fl.rasi_house if fl else 0,
        fourth_lord_dignity=dignity(fourth_lord, chart) if fl else "neutral",
        fourth_occupants=_occupants(chart, 4),
        fourth_aspecting=tuple(drishti.aspecting_house(4, chart)),
        karakas=karakas,
        education_verdict=_verdict(chart, 4, "education"),
        intellect_verdict=_verdict(chart, 5, "intellect"))

    vc = cast_varga_chart(chart, 24)
    jd, md = vc.positions.get("Jupiter"), vc.positions.get("Mercury")
    overlay = SiddhamsaOverlay(
        lagna_sign=vc.lagna_sign,
        lagna_lord=vc.lagna_lord,
        lagna_occupants=_d24_occupants(vc, 1),
        fourth_sign=_house_of_sign(vc.lagna_sign, 4),
        fourth_occupants=_d24_occupants(vc, 4),
        jupiter_sign=jd.sign if jd else 0,
        jupiter_dignity=_varga_dignity("Jupiter", jd.sign) if jd else "neutral",
        mercury_sign=md.sign if md else 0,
        mercury_dignity=_varga_dignity("Mercury", md.sign) if md else "neutral")

    notes = (
        Tagged("Raman ascertains education from the 4th and the kāraka Jupiter (with Mercury for "
               "intellect/expression) — his real method decides here.", "RAMAN_EXPLICIT",
               "AFB-6:23"),
        Tagged("the 4th is the vidyā-sthāna (HTJAH-I:4701); the 5th (intellect) supports it.",
               "RAMAN_EXPLICIT", "HTJAH-I:4701"),
        Tagged("the Siddhāṁśa itself is the classical learning scheme via Raman's Parashara pointer; "
               "the D-24 overlay is report-only corroboration.", "CLASSICAL_NONCITABLE",
               "HPA-11:195"),
    )
    return SiddhamsaEducationReading(core=core, overlay=overlay, notes=notes)
