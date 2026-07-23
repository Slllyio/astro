"""Daśāṁśa (D-10) career reading — a REPORT-ONLY surface.

The Daśāṁśa is the classical career varga, but Raman's OWN profession method is the **10th house,
its lord, the lord's NAVĀṀŚA strength, and the shaḍvarga strength of the career significators**
(HTJAH-II:9729-9811) — the dasāṁśa chart being the classical scheme via his Parashara pointer
(HPA-11:195). This surface reads Raman's method as the authoritative core (with the four career
kārakas — Saturn/Mercury/Jupiter/Sun) and adds a report-only D-10 overlay.

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path — the golden ratchet is
untouched by construction.

Usage:
    from app.raman_saab.judges.dasamsa_career_reading import build_dasamsa_career_reading
    r = build_dasamsa_career_reading(chart)
    r.core.career_verdict            # Raman's authoritative career read
    r.core.tenth_lord_navamsa_dignity  # his key profession-strength signal
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
_CAREER_KARAKAS: Final[tuple[str, ...]] = ("Saturn", "Mercury", "Jupiter", "Sun")


@dataclass(frozen=True)
class CareerCore:
    """The AUTHORITATIVE career picture — Raman's real method (10th + lord's navāṁśa + kārakas)."""
    tenth_sign: int
    tenth_lord: str
    tenth_lord_house: int
    tenth_lord_dignity: Dignity
    tenth_lord_navamsa_dignity: Dignity        # Raman's key profession-strength signal
    tenth_occupants: tuple[str, ...]
    tenth_aspecting: tuple[str, ...]
    karakas: tuple[tuple[str, int, Dignity], ...]   # (career kāraka, house, rasi dignity)
    career_verdict: str
    honour_verdict: str


@dataclass(frozen=True)
class DasamsaOverlay:
    """The corroborative D-10 picture — REPORT-ONLY."""
    lagna_sign: int
    lagna_lord: str
    lagna_occupants: tuple[str, ...]
    tenth_sign: int
    tenth_occupants: tuple[str, ...]
    tenth_lord_d10_dignity: Dignity


@dataclass(frozen=True)
class DasamsaCareerReading:
    core: CareerCore
    overlay: DasamsaOverlay
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


def _d10_occupants(vc: VargaChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                if n in vc.positions and vc.positions[n].house == house)


def build_dasamsa_career_reading(chart: RamanChart) -> DasamsaCareerReading:
    """Assemble the Daśāṁśa career reading — Raman's method decides, the D-10 overlay corroborates."""
    tenth = _house_of_sign(chart.asc_sign, 10)
    tenth_lord = SIGN_LORDS[tenth]
    tl = chart.planets.get(tenth_lord)
    karakas = tuple(
        (k, chart.planets[k].rasi_house, dignity(k, chart))
        for k in _CAREER_KARAKAS if k in chart.planets)
    core = CareerCore(
        tenth_sign=tenth,
        tenth_lord=tenth_lord,
        tenth_lord_house=tl.rasi_house if tl else 0,
        tenth_lord_dignity=dignity(tenth_lord, chart) if tl else "neutral",
        tenth_lord_navamsa_dignity=_navamsa_dignity(tenth_lord, chart),
        tenth_occupants=_occupants(chart, 10),
        tenth_aspecting=tuple(drishti.aspecting_house(10, chart)),
        karakas=karakas,
        career_verdict=_verdict(chart, 10, "career"),
        honour_verdict=_verdict(chart, 10, "status_honour"))

    vc = cast_varga_chart(chart, 10)
    d10_tenth = _house_of_sign(vc.lagna_sign, 10)
    tld10 = vc.positions.get(tenth_lord)
    overlay = DasamsaOverlay(
        lagna_sign=vc.lagna_sign,
        lagna_lord=vc.lagna_lord,
        lagna_occupants=_d10_occupants(vc, 1),
        tenth_sign=d10_tenth,
        tenth_occupants=_d10_occupants(vc, 10),
        tenth_lord_d10_dignity=_varga_dignity(tenth_lord, tld10.sign) if tld10 else "neutral")

    notes = (
        Tagged("Raman's profession method: the 10th, its lord, the lord's NAVĀṀŚA strength, and the "
               "shaḍvarga strength of the career significators — his real method decides here.",
               "RAMAN_EXPLICIT", "HTJAH-II:9729"),
        Tagged("honour / public standing (10th) cited HTJAH-II:9442.", "RAMAN_EXPLICIT",
               "HTJAH-II:9442"),
        Tagged("the Daśāṁśa itself is the classical career scheme via Raman's Parashara pointer; "
               "the D-10 overlay is report-only corroboration.", "CLASSICAL_NONCITABLE",
               "HPA-11:195"),
    )
    return DasamsaCareerReading(core=core, overlay=overlay, notes=notes)
