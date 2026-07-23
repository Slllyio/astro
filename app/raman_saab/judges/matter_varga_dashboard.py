"""Matter-varga dashboard — the deep divisional analysis of a chart, one matter per row.

The generic ``varga_judge.build_shodasavarga_report`` describes all sixteen divisions *shallowly*
(one four-principle status per varga). This dashboard instead dispatches each life-matter to its
DEDICATED deep reader and surfaces that reader's AUTHORITATIVE (Raman-method) verdict:

    children  → D-7  Sapthāṁśa    (``saptamsa_reading``)
    marriage  → D-9  Navāṁśa      (``navamsa_marriage_reading``)
    career    → D-10 Daśāṁśa      (``dasamsa_career_reading``)
    education → D-24 Siddhāṁśa    (``siddhamsa_education_reading``)
    health    → D-30 Triṁśāṁśa    (``trimsamsa_health_reading``)

Each verdict is Raman's real method (the deep reader's core), not the generic varga status — so a
caller sees, at a glance, where a chart is strong or afflicted matter-by-matter, and which deep
reader to consult for the full picture. REPORT-ONLY; imported by nothing in the D1 verdict path.

Usage:
    from app.raman_saab.judges.matter_varga_dashboard import build_matter_varga_dashboard
    d = build_matter_varga_dashboard(chart)
    for e in d.entries:  print(e.matter, e.varga_name, e.verdict)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.dasamsa_career_reading import build_dasamsa_career_reading
from app.raman_saab.judges.navamsa_marriage_reading import build_navamsa_marriage_reading
from app.raman_saab.judges.saptamsa_reading import Tagged, build_saptamsa_children_reading
from app.raman_saab.judges.siddhamsa_education_reading import build_siddhamsa_education_reading
from app.raman_saab.judges.trimsamsa_health_reading import build_trimsamsa_health_reading


@dataclass(frozen=True)
class MatterVargaEntry:
    """One life-matter, its divisional home, and the deep reader's authoritative verdict."""
    matter: str
    varga: int
    varga_name: str
    verdict: str
    reader: str          # the dedicated module to consult for the full reading


@dataclass(frozen=True)
class MatterVargaDashboard:
    """The deep matter-by-matter divisional snapshot — REPORT-ONLY."""
    entries: tuple[MatterVargaEntry, ...]
    notes: tuple[Tagged, ...]


# (matter, varga, varga name, dedicated reader module) — the dispatch table.
_DISPATCH: Final[tuple[tuple[str, int, str, str], ...]] = (
    ("children", 7, "Sapthāṁśa", "saptamsa_reading"),
    ("marriage", 9, "Navāṁśa", "navamsa_marriage_reading"),
    ("career", 10, "Daśāṁśa", "dasamsa_career_reading"),
    ("education", 24, "Siddhāṁśa", "siddhamsa_education_reading"),
    ("health", 30, "Triṁśāṁśa", "trimsamsa_health_reading"),
)


def _verdict_for(matter: str, chart: RamanChart) -> str:
    if matter == "children":
        return build_saptamsa_children_reading(chart).raman_core.children_verdict
    if matter == "marriage":
        return build_navamsa_marriage_reading(chart).core.marital_verdict
    if matter == "career":
        return build_dasamsa_career_reading(chart).core.career_verdict
    if matter == "education":
        return build_siddhamsa_education_reading(chart).core.education_verdict
    if matter == "health":
        return build_trimsamsa_health_reading(chart).core.disease_verdict
    return "insufficient-evidence"


def build_matter_varga_dashboard(chart: RamanChart) -> MatterVargaDashboard:
    """Run every dedicated matter-varga reader and collect its authoritative verdict."""
    entries = tuple(
        MatterVargaEntry(matter=m, varga=v, varga_name=name, reader=reader,
                         verdict=_verdict_for(m, chart))
        for m, v, name, reader in _DISPATCH)
    notes = (
        Tagged("each verdict is the dedicated reader's Raman-method CORE, not the generic varga "
               "status — consult the named reader for the full divisional reading.",
               "RAMAN_GENERAL_PRINCIPLE"),
        Tagged("REPORT-ONLY: imported by nothing in the D1 verdict path; the golden ratchet is "
               "untouched by construction.", "RAMAN_GENERAL_PRINCIPLE"),
    )
    return MatterVargaDashboard(entries=entries, notes=notes)
