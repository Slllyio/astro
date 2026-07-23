"""General-varga reading — a REPORT-ONLY strength/character surface for the matterless vargas.

The Bhāṁśa (D-27), Khavedāṁśa (D-40), Akṣavedāṁśa (D-45) and Ṣaṣṭyāṁśa (D-60) carry NO single
life-matter (their domain-table rows have no house or kāraka) — they read the chart's GENERAL
strength, character, and accumulated karma. So this reader does not judge a house; it reads each
varga's own picture: the varga lagna and its lord, which planets are strong (exalted/own) or weak
(debilitated) inside the varga, and the benefic/malefic load on the varga lagna.

PROVENANCE: the general-strength use of D-27 is a general principle on Raman's Parashara varga
pointer (HPA-11). The D-40/D-45/D-60 lineage-karma readings (mother's line / father's line /
past-births karma) are **CLASSICAL_NONCITABLE** (Sanjay Rath, *Crux*) — flagged, not live-Raman.

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path — the golden ratchet is
untouched by construction.

Usage:
    from app.raman_saab.judges.general_varga_reading import build_general_varga_reading, GENERAL_VARGAS
    r = build_general_varga_reading(chart, 60)   # the Ṣaṣṭyāṁśa (accumulated karma)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.varga_chart import VargaChart, cast_varga_chart
from app.raman_saab.judges.saptamsa_reading import Provenance, Tagged
from app.raman_saab.judges.varga_judge import Dignity, _varga_dignity
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS, NATURAL_MALEFICS

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


@dataclass(frozen=True)
class GeneralVargaSpec:
    varga: int
    varga_name: str
    theme: str
    provenance: Provenance
    citation: str


_SPECS: Final[dict[int, GeneralVargaSpec]] = {
    27: GeneralVargaSpec(27, "Bhāṁśa", "general strength & weakness (bala/abala)",
                         "RAMAN_GENERAL_PRINCIPLE", "HPA-11:100"),
    40: GeneralVargaSpec(40, "Khavedāṁśa", "auspicious & inauspicious general effects; the "
                         "mother's-lineage karma (Rath)", "CLASSICAL_NONCITABLE", "HPA-11:110"),
    45: GeneralVargaSpec(45, "Akṣavedāṁśa", "general character & conduct; the father's-lineage "
                         "karma (Rath)", "CLASSICAL_NONCITABLE", "HPA-11:113"),
    60: GeneralVargaSpec(60, "Ṣaṣṭyāṁśa", "all matters; the accumulated karma of past births "
                         "(Rath gives it the highest weightage)", "CLASSICAL_NONCITABLE",
                         "HPA-11:116"),
}

#: The general (matterless) vargas this reader covers.
GENERAL_VARGAS: Final[tuple[int, ...]] = tuple(_SPECS)


@dataclass(frozen=True)
class GeneralVargaReading:
    """One matterless varga's own strength/character picture — REPORT-ONLY."""
    varga: int
    varga_name: str
    theme: str
    lagna_sign: int
    lagna_lord: str
    lagna_lord_dignity: Dignity            # the varga-lagna-lord's dignity INSIDE the varga
    benefics_on_lagna: tuple[str, ...]
    malefics_on_lagna: tuple[str, ...]
    strong_planets: tuple[str, ...]        # exalted / own in this varga
    weak_planets: tuple[str, ...]          # debilitated in this varga
    notes: tuple[Tagged, ...]


def _lagna_occupants(vc: VargaChart, group: frozenset[str]) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                if n in vc.positions and vc.positions[n].house == 1 and n in group)


def build_general_varga_reading(chart: RamanChart, varga: int) -> GeneralVargaReading:
    """Read a matterless varga's own strength/character (no house judged)."""
    if varga not in _SPECS:
        raise ValueError(f"D{varga} is not a general-strength varga; use one of {GENERAL_VARGAS}")
    spec = _SPECS[varga]
    vc = cast_varga_chart(chart, varga)
    strong: list[str] = []
    weak: list[str] = []
    for n in _PLANET_ORDER:
        pos = vc.positions.get(n)
        if pos is None:
            continue
        dig = _varga_dignity(n, pos.sign)
        if dig in ("exalt", "own"):
            strong.append(n)
        elif dig == "debil":
            weak.append(n)
    ll = vc.lagna_lord
    ll_pos = vc.positions.get(ll)
    notes = (
        Tagged(f"D-{spec.varga} ({spec.varga_name}) — {spec.theme}.", spec.provenance,
               spec.citation),
        Tagged("this reads the varga's own strength/character (no D1 house judged); report-only, "
               "the golden ratchet is untouched.", "RAMAN_GENERAL_PRINCIPLE"),
    )
    return GeneralVargaReading(
        varga=spec.varga, varga_name=spec.varga_name, theme=spec.theme,
        lagna_sign=vc.lagna_sign, lagna_lord=ll,
        lagna_lord_dignity=_varga_dignity(ll, ll_pos.sign) if ll_pos else "neutral",
        benefics_on_lagna=_lagna_occupants(vc, frozenset(NATURAL_BENEFICS)),
        malefics_on_lagna=_lagna_occupants(vc, frozenset(NATURAL_MALEFICS)),
        strong_planets=tuple(strong), weak_planets=tuple(weak), notes=notes)
