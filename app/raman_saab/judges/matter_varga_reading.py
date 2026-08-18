"""Generalized matter-varga reading — a REPORT-ONLY, spec-driven surface.

Where D-7/D-9/D-10/D-24/D-30 have bespoke readers (each carries matter-specific doctrine —
Beeja/Kṣetra, the navāṁśa-7th, bālāriṣṭa …), the remaining single-house matter-vargas share one
shape: judge the D1 house by Raman's real method, then show the matter-house inside its varga. This
one module reads them all from a spec table:

    wealth    → 2nd house  → D-2  Horā
    siblings  → 3rd house  → D-3  Drekkāṇa
    property  → 4th house  → D-4  Chaturthāṁśa
    comforts  → 4th house  → D-16 Ṣoḍaśāṁśa   (home comforts / vehicles)
    spiritual → 9th house  → D-20 Viṁśāṁśa    (dharma / worship)

The ``core`` verdict is Raman's real method (``judge_house``); the varga is a report-only overlay.
Imported by nothing in the D1 verdict path — the golden ratchet is untouched by construction.

Usage:
    from app.raman_saab.judges.matter_varga_reading import build_matter_varga_reading, MATTERS
    r = build_matter_varga_reading(chart, "siblings")
    r.core.verdict
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
from app.raman_saab.ordinals import ordinal

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


@dataclass(frozen=True)
class VargaMatterSpec:
    matter: str
    house: int
    sig: str                       # the signification key judged
    varga: int
    varga_name: str
    karakas: tuple[str, ...]
    citation: str


_SPECS: Final[dict[str, VargaMatterSpec]] = {
    "wealth": VargaMatterSpec("wealth", 2, "wealth", 2, "Horā", ("Jupiter",), "HTJAH-I:2316"),
    "siblings": VargaMatterSpec("siblings", 3, "siblings", 3, "Drekkāṇa", ("Mars",), "HTJAH-I:3428"),
    "property": VargaMatterSpec("property", 4, "property", 4, "Chaturthāṁśa", ("Mars", "Venus"),
                                "HTJAH-I:4303"),
    "comforts": VargaMatterSpec("comforts", 4, "home_comforts", 16, "Ṣoḍaśāṁśa", ("Venus",),
                                "HPA-11:87"),
    "spiritual": VargaMatterSpec("spiritual", 9, "dharma", 20, "Viṁśāṁśa", ("Jupiter",),
                                 "HPA-11:92"),
}

#: The matters this generalized reader covers.
MATTERS: Final[tuple[str, ...]] = tuple(_SPECS)


@dataclass(frozen=True)
class MatterVargaCore:
    matter: str
    house: int
    house_sign: int
    house_lord: str
    house_lord_house: int
    house_lord_dignity: Dignity
    house_occupants: tuple[str, ...]
    house_aspecting: tuple[str, ...]
    karakas: tuple[tuple[str, int, Dignity], ...]
    verdict: str


@dataclass(frozen=True)
class MatterVargaOverlay:
    varga: int
    varga_name: str
    lagna_sign: int
    lagna_lord: str
    lagna_occupants: tuple[str, ...]
    house_sign_in_varga: int
    house_occupants_in_varga: tuple[str, ...]


@dataclass(frozen=True)
class MatterVargaReading:
    core: MatterVargaCore
    overlay: MatterVargaOverlay
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


def build_matter_varga_reading(chart: RamanChart, matter: str) -> MatterVargaReading:
    """Read ``matter`` from Raman's real house-method + its report-only divisional overlay."""
    if matter not in _SPECS:
        raise ValueError(f"unknown matter {matter!r}; use one of {MATTERS}")
    spec = _SPECS[matter]
    house_sign = _house_of_sign(chart.asc_sign, spec.house)
    house_lord = SIGN_LORDS[house_sign]
    hl = chart.planets.get(house_lord)
    karakas = tuple((k, chart.planets[k].rasi_house, dignity(k, chart))
                    for k in spec.karakas if k in chart.planets)
    core = MatterVargaCore(
        matter=spec.matter, house=spec.house, house_sign=house_sign, house_lord=house_lord,
        house_lord_house=hl.rasi_house if hl else 0,
        house_lord_dignity=dignity(house_lord, chart) if hl else "neutral",
        house_occupants=_occupants(chart, spec.house),
        house_aspecting=tuple(drishti.aspecting_house(spec.house, chart)),
        karakas=karakas, verdict=_verdict(chart, spec.house, spec.sig))

    vc = cast_varga_chart(chart, spec.varga)
    overlay = MatterVargaOverlay(
        varga=spec.varga, varga_name=spec.varga_name, lagna_sign=vc.lagna_sign,
        lagna_lord=vc.lagna_lord, lagna_occupants=_v_occupants(vc, 1),
        house_sign_in_varga=_house_of_sign(vc.lagna_sign, spec.house),
        house_occupants_in_varga=_v_occupants(vc, spec.house))

    notes = (
        Tagged(f"{spec.matter} is judged from the {ordinal(spec.house)} house by Raman's real method — the "
               f"verdict here is his.", "RAMAN_EXPLICIT", spec.citation),
        Tagged(f"the D-{spec.varga} ({spec.varga_name}) is the classical varga for this matter via "
               "Raman's Parashara pointer; the overlay is report-only corroboration.",
               "CLASSICAL_NONCITABLE", "HPA-11:195"),
    )
    return MatterVargaReading(core=core, overlay=overlay, notes=notes)
