"""Trimsāṁśa (D-30) health reading — a REPORT-ONLY, provenance-honest surface.

WHY A CHILD'S HEALTH IS READ FROM THEIR OWN NATIVITY (the doctrinal spine):
CLAUDE.md and the family readings both lock the rule that a person's health is judged from
**their own** chart, NEVER from a parent's children-varga (the D-7 answers *the parents' progeny
matter*; it does not diagnose the child). The D-30 (Trimsāṁśa) is Raman's **disease / ariṣṭa**
varga (HPA-11:195-201 domain pointer; definition HPA-11:165). Like the Saptāṁśa, Raman *defines*
it but does not demonstrably *cast/read* one in his worked nativities — his real health method is
the **1st (constitution) + 6th (disease) + 8th (chronic/longevity) + Moon (mind) + Mercury
(nervous-system/intellect) + the bālāriṣṭa infant-longevity gate** (HPA-14). So this surface
splits, exactly like ``saptamsa_reading.py``:

  * ``core`` — the AUTHORITATIVE health picture from Raman's real single-chart method
    (``judge_house`` on H1/H6/H8 + Moon/Mercury kārakas + ``balarishta``). This is what stands.
  * ``overlay`` — a corroborative D-30 picture, provenance-tagged, report-only.

VERDICT-AUTHORITY INVARIANT: imported by NOTHING in the D1 verdict path — a standalone reading,
exactly like ``saptamsa_reading.py`` and ``two_spouse_children.py``.

NOT A MEDICAL STATEMENT. This is an astrological reading in Raman's system, to be held alongside
real medical care, never in place of it — and never a clinical prognosis about a real child.

Usage:
    from app.raman_saab.judges.trimsamsa_health_reading import build_trimsamsa_health_reading
    r = build_trimsamsa_health_reading(chart)
    r.core.longevity_verdict          # the authoritative longevity signification
    r.core.balarishta_applies         # infant-longevity flag (+ .balarishta_cancelled)
    r.core.mercury_afflictions        # malefics on the nervous-system/communication kāraka
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.varga_chart import VargaChart, cast_varga_chart
from app.raman_saab.doctrine import drishti
from app.raman_saab.judges.house_template import judge_house
from app.raman_saab.judges.saptamsa_reading import Provenance, Tagged
from app.raman_saab.judges.varga_judge import Dignity, _varga_dignity
from app.raman_saab.primitives.balarishta import balarishta
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import NATURAL_MALEFICS

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


@dataclass(frozen=True)
class HealthCore:
    """The AUTHORITATIVE health picture — Raman's real single-chart method decides."""
    lagna_sign: int
    lagna_lord: str
    lagna_lord_house: int
    lagna_lord_dignity: Dignity
    health_verdict: str                # H1 health
    disease_verdict: str               # H6 disease_chronic
    longevity_verdict: str             # H8 longevity (the engine defers lifespan; this is a lean)
    balarishta_applies: bool
    balarishta_cancelled: bool
    balarishta_reasons: tuple[str, ...]
    moon_house: int                    # Moon = mind (manas) kāraka
    moon_dignity: Dignity
    moon_afflictions: tuple[str, ...]  # natural malefics conjunct/aspecting the Moon
    mercury_house: int                 # Mercury = nervous-system / intellect (Budhi) kāraka
    mercury_dignity: Dignity
    mercury_afflictions: tuple[str, ...]


@dataclass(frozen=True)
class D30Overlay:
    """The corroborative D-30 picture — REPORT-ONLY, provenance-tagged."""
    lagna_sign: int
    lagna_lord: str
    lagna_occupants: tuple[str, ...]
    sixth_sign: int
    eighth_sign: int
    moon_sign: int
    moon_dignity: Dignity
    mercury_sign: int
    mercury_dignity: Dignity
    lagna_afflictions: tuple[Tagged, ...]   # malefics on the D-30 lagna (health-seat), analogical


@dataclass(frozen=True)
class TrimsamsaHealthReading:
    """The whole reading: Raman-core (decides) + D-30 overlay (corroborates) + caveats."""
    core: HealthCore
    overlay: D30Overlay
    notes: tuple[Tagged, ...]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _house_of_sign(from_sign: int, offset: int) -> int:
    return ((from_sign - 1) + (offset - 1)) % 12 + 1


def _verdict(chart: RamanChart, house: int, sig: str) -> str:
    pf = judge_house(chart, house)
    sv = next((s for s in pf.significations if s.signification == sig), None)
    return sv.verdict if sv else "insufficient-evidence"


def _planet_afflictions(planet: str, chart: RamanChart) -> tuple[str, ...]:
    """Natural malefics conjunct OR aspecting `planet` (whole-sign drishti) — the affliction
    load on a health kāraka (Moon = mind, Mercury = nervous-system/intellect)."""
    p = chart.planets.get(planet)
    if p is None:
        return ()
    house = p.rasi_house
    conj = {n for n, q in chart.planets.items()
            if q.rasi_house == house and n in NATURAL_MALEFICS and n != planet}
    asp = {n for n in drishti.aspecting_house(house, chart) if n in NATURAL_MALEFICS}
    return tuple(n for n in _PLANET_ORDER if n in (conj | asp))


def _d30_occupants(vc: VargaChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                 if n in vc.positions and vc.positions[n].house == house)


def _d30_lagna_afflictions(vc: VargaChart) -> tuple[Tagged, ...]:
    """Natural malefics on the D-30 lagna (the disease-varga's health-seat) — read by the
    general 'judge the varga as the rāśi' principle (RAMAN_GENERAL_PRINCIPLE; Raman never casts
    a D-30). The Trimsāṁśa's classical role is to show the KIND of ariṣṭa, but the per-varga
    reading is not Raman-demonstrated, so it is corroboration only."""
    out: list[Tagged] = []
    for n in _d30_occupants(vc, 1):
        if n in NATURAL_MALEFICS:
            out.append(Tagged(
                f"{n} on the D-30 lagna (the ariṣṭa/health-seat) — an affliction to the "
                "constitution by the general varga principle", "RAMAN_GENERAL_PRINCIPLE",
                "HPA-11:165"))
    return tuple(out)


# ---------------------------------------------------------------------------
# public builder
# ---------------------------------------------------------------------------

def build_trimsamsa_health_reading(chart: RamanChart) -> TrimsamsaHealthReading:
    """Assemble the provenance-honest D-30 health reading for `chart`.

    ``core`` decides (Raman's real 1st/6th/8th + Moon/Mercury + bālāriṣṭa method); ``overlay``
    corroborates (report-only). NOT a medical prognosis."""
    lagna_sign = chart.asc_sign
    lagna_lord = SIGN_LORDS[lagna_sign]
    ll = chart.planets.get(lagna_lord)
    moon = chart.planets.get("Moon")
    merc = chart.planets.get("Mercury")
    bal = balarishta(chart)

    core = HealthCore(
        lagna_sign=lagna_sign,
        lagna_lord=lagna_lord,
        lagna_lord_house=ll.rasi_house if ll else 0,
        lagna_lord_dignity=dignity(lagna_lord, chart) if ll else "neutral",
        health_verdict=_verdict(chart, 1, "health"),
        disease_verdict=_verdict(chart, 6, "disease_chronic"),
        longevity_verdict=_verdict(chart, 8, "longevity"),
        balarishta_applies=bal.applies,
        balarishta_cancelled=bal.cancelled,
        balarishta_reasons=bal.reasons,
        moon_house=moon.rasi_house if moon else 0,
        moon_dignity=dignity("Moon", chart) if moon else "neutral",
        moon_afflictions=_planet_afflictions("Moon", chart),
        mercury_house=merc.rasi_house if merc else 0,
        mercury_dignity=dignity("Mercury", chart) if merc else "neutral",
        mercury_afflictions=_planet_afflictions("Mercury", chart))

    vc = cast_varga_chart(chart, 30)
    md = vc.positions.get("Moon")
    mc = vc.positions.get("Mercury")
    overlay = D30Overlay(
        lagna_sign=vc.lagna_sign,
        lagna_lord=vc.lagna_lord,
        lagna_occupants=_d30_occupants(vc, 1),
        sixth_sign=_house_of_sign(vc.lagna_sign, 6),
        eighth_sign=_house_of_sign(vc.lagna_sign, 8),
        moon_sign=md.sign if md else 0,
        moon_dignity=_varga_dignity("Moon", md.sign) if md else "neutral",
        mercury_sign=mc.sign if mc else 0,
        mercury_dignity=_varga_dignity("Mercury", mc.sign) if mc else "neutral",
        lagna_afflictions=_d30_lagna_afflictions(vc))

    notes = (
        Tagged("The D-30 (Trimsāṁśa) is Raman's disease/ariṣṭa varga (HPA-11:195-201), but he "
               "defines it without casting one — the verdict here is his real method (1st/6th/8th "
               "+ Moon/Mercury + bālāriṣṭa); the D-30 overlay only corroborates.",
               "RAMAN_EXPLICIT", "HPA-11:198"),
        Tagged("A child's health is read from the child's OWN nativity, never from a parent's "
               "children-varga (CLAUDE.md lock).", "RAMAN_GENERAL_PRINCIPLE"),
        Tagged("Raman's system speaks of affliction, protection and relief — not clinical "
               "diagnosis or cure. This is an astrological reading to hold ALONGSIDE real medical "
               "care, never in place of it, and never a prognosis about a real child.",
               "RAMAN_GENERAL_PRINCIPLE"),
    )
    return TrimsamsaHealthReading(core=core, overlay=overlay, notes=notes)
