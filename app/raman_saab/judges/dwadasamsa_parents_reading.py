"""Dvādaśāṁśa (D-12) parents reading — a REPORT-ONLY surface.

The Dvādaśāṁśa is Raman's parents varga (HPA-11:147, "father and mother"). Raman judges the mother
from the **4th house + kāraka Moon** (HTJAH-I:4387) and the father from the **9th house + kāraka
Sun** (HTJAH-II:7291). This surface reads both parents by that real method as the authoritative
core and adds a report-only D-12 overlay (each parent's house inside the Dvādaśāṁśa).

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path — the golden ratchet is
untouched by construction.

Usage:
    from app.raman_saab.judges.dwadasamsa_parents_reading import build_dwadasamsa_parents_reading
    r = build_dwadasamsa_parents_reading(chart)
    r.core.mother_verdict, r.core.father_verdict
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
from app.raman_saab.judges.varga_judge import Dignity
from app.raman_saab.primitives.dignity import dignity

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


@dataclass(frozen=True)
class ParentPicture:
    """One parent, from their house + kāraka (Raman's real method)."""
    parent: str
    house: int
    house_sign: int
    house_lord: str
    house_lord_house: int
    house_lord_dignity: Dignity
    house_occupants: tuple[str, ...]
    house_aspecting: tuple[str, ...]
    karaka: str
    karaka_house: int
    karaka_dignity: Dignity
    verdict: str


@dataclass(frozen=True)
class DwadasamsaOverlay:
    """The corroborative D-12 picture — REPORT-ONLY."""
    lagna_sign: int
    lagna_lord: str
    fourth_sign: int                   # the mother-house in the D-12
    fourth_occupants: tuple[str, ...]
    ninth_sign: int                    # the father-house in the D-12
    ninth_occupants: tuple[str, ...]


@dataclass(frozen=True)
class DwadasamsaParentsReading:
    mother: ParentPicture
    father: ParentPicture
    overlay: DwadasamsaOverlay
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


def _v_occupants(vc: VargaChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                if n in vc.positions and vc.positions[n].house == house)


def _parent(chart: RamanChart, parent: str, house: int, sig: str, karaka: str) -> ParentPicture:
    house_sign = _house_of_sign(chart.asc_sign, house)
    house_lord = SIGN_LORDS[house_sign]
    hl = chart.planets.get(house_lord)
    k = chart.planets.get(karaka)
    return ParentPicture(
        parent=parent, house=house, house_sign=house_sign, house_lord=house_lord,
        house_lord_house=hl.rasi_house if hl else 0,
        house_lord_dignity=dignity(house_lord, chart) if hl else "neutral",
        house_occupants=_occupants(chart, house),
        house_aspecting=tuple(drishti.aspecting_house(house, chart)),
        karaka=karaka, karaka_house=k.rasi_house if k else 0,
        karaka_dignity=dignity(karaka, chart) if k else "neutral",
        verdict=_verdict(chart, house, sig))


def build_dwadasamsa_parents_reading(chart: RamanChart) -> DwadasamsaParentsReading:
    """Assemble the Dvādaśāṁśa parents reading — Raman's method decides, the D-12 overlay corroborates."""
    mother = _parent(chart, "mother", 4, "mother", "Moon")
    father = _parent(chart, "father", 9, "father", "Sun")

    vc = cast_varga_chart(chart, 12)
    overlay = DwadasamsaOverlay(
        lagna_sign=vc.lagna_sign, lagna_lord=vc.lagna_lord,
        fourth_sign=_house_of_sign(vc.lagna_sign, 4), fourth_occupants=_v_occupants(vc, 4),
        ninth_sign=_house_of_sign(vc.lagna_sign, 9), ninth_occupants=_v_occupants(vc, 9))

    notes = (
        Tagged("the mother is judged from the 4th + kāraka Moon (HTJAH-I:4387), the father from "
               "the 9th + kāraka Sun (HTJAH-II:7291) — Raman's real method decides.",
               "RAMAN_EXPLICIT", "HTJAH-I:4387"),
        Tagged("the Dvādaśāṁśa is Raman's parents varga (HPA-11:147); the D-12 overlay is "
               "report-only corroboration.", "CLASSICAL_NONCITABLE", "HPA-11:147"),
    )
    return DwadasamsaParentsReading(mother=mother, father=father, overlay=overlay, notes=notes)
