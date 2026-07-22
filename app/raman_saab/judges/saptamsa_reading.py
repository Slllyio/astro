"""Saptāṁśa (D-7) children reading — a REPORT-ONLY, provenance-honest surface.

WHY THIS IS REPORT-ONLY (the doctrinal spine — read before extending):
B. V. Raman *defines* the Saptāṁśa and names it the children varga (HPA-11:187-199) but
**never casts or reads a D-7 for children anywhere** in HTJAH or Notable Horoscopes (a
full-text audit found 0 occurrences). His actual progeny engine is the **Rāśi 5th +
Navāṁśa-count + Beeja/Kṣetra sphuṭas** (HTJAH-I:5517-5527, 5902-5904). The successive-child
house rule and any D-7-lagna reading are **ABSENT in Raman** — they exist only in non-citable
modern sources (KP's 5→7→9 cusp scheme; Sanjay Rath's Maṇḍūka-gati in *Crux*). Gender and
child-affliction rules ARE Raman-explicit, but he states them for the **Rāśi 5th**, not the D-7.

Therefore this surface splits its output into:
  * ``raman_core`` — the AUTHORITATIVE children judgment, sourced entirely from Raman's real
    method (delegates to ``judge_house(chart, 5)`` + ``beeja_kshetra``). This is what decides.
  * ``d7_overlay`` — a corroborative D-7 picture, every field carrying a ``Provenance`` tag.
    The eldest-child locus (D-7 lagna) is read by the general "judge the varga as you judge the
    rāśi" principle; successive-child loci are the classical (non-citable) scheme, flagged.

VERDICT-AUTHORITY INVARIANT: this module is imported by NOTHING in the D1 verdict path
(``judges/house_template.py`` never imports it) — the golden ratchet is untouched by
construction. It is a standalone reading, exactly like ``judges/varga_judge.py``.

Usage:
    from app.raman_saab.judges.saptamsa_reading import build_saptamsa_children_reading
    reading = build_saptamsa_children_reading(chart)
    reading.raman_core.children_verdict          # the authoritative verdict
    reading.d7_overlay.child_loci[0].afflictions # the eldest-child D-7 afflictions
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.varga_chart import VargaChart, cast_varga_chart
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.karakas import BHAVA_KARAKA
from app.raman_saab.judges.house_template import judge_house
from app.raman_saab.judges.varga_judge import Dignity, _varga_dignity
from app.raman_saab.primitives import relationships as rel
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import NATURAL_MALEFICS
from app.raman_saab.primitives.sphutas import beeja_kshetra

Provenance = Literal[
    "RAMAN_EXPLICIT",           # Raman states it verbatim
    "RAMAN_GENERAL_PRINCIPLE",  # Raman's effect/principle applied to the D-7 by analogy
    "CLASSICAL_NONCITABLE",     # KP / Rath / Parashari classical — NOT in the Raman corpus
    "ABSENT_IN_RAMAN",          # a step Raman never treats; flagged, not silently supplied
]

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

# Raman's Rāśi-5th planet-in-the-house effects, applied to a D-7 child-locus BY ANALOGY
# (the effect text is RAMAN_EXPLICIT; its D-7 application is RAMAN_GENERAL_PRINCIPLE).
# Each quote is verbatim from the single line cited — no stitched composites (P-review fix).
_MALEFIC_5TH_EFFECT: Final[dict[str, tuple[str, str]]] = {
    "Ketu":   ("lacks the human touch in his approach towards one or two of the issues",
               "HTJAH-I:5293"),
    "Mars":   ("children die after some time", "HTJAH-I:5270"),
    "Saturn": ("sorrows through children", "HTJAH-I:5259"),
    "Rahu":   ("will lose a number of children", "HTJAH-I:5262"),
    "Sun":    ("deprives the person of children", "HTJAH-I:5232"),
}


@dataclass(frozen=True)
class Tagged:
    """One reading element with its doctrinal provenance and citation (empty when none)."""
    text: str
    provenance: Provenance
    cite: str = ""


@dataclass(frozen=True)
class ChildLocus:
    """One child's house-seat, read in the D-7 (and cross-referenced to the Rāśi 5th)."""
    ordinal: int                       # 1 = eldest
    label: str
    frame: str                         # "D7-lagna" | "D7-5th" | "D7-9th" …
    scheme: Provenance                 # eldest = general principle; successive = non-citable
    sign: int
    lord: str
    occupants: tuple[str, ...]
    aspecting: tuple[str, ...]
    afflictions: tuple[Tagged, ...]    # malefic occupant/aspect → Raman-cited effect (by analogy)


@dataclass(frozen=True)
class RamanCore:
    """The AUTHORITATIVE children judgment — entirely from Raman's real method."""
    rasi_fifth_sign: int
    rasi_fifth_lord: str
    rasi_fifth_lord_house: int
    rasi_fifth_lord_dignity: Dignity
    rasi_fifth_occupants: tuple[str, ...]
    rasi_fifth_aspecting: tuple[str, ...]
    putrakaraka: str                   # Jupiter
    putrakaraka_house: int
    putrakaraka_dignity: Dignity
    putrakaraka_navamsa_dignity: Dignity   # the redemptive/annihilation signal
    beeja_strong: Optional[bool]
    kshetra_strong: Optional[bool]
    children_verdict: str              # from judge_house(chart, 5)
    verdict_metadata: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class D7Overlay:
    """The corroborative D-7 picture — REPORT-ONLY, provenance-tagged."""
    lagna_sign: int
    lagna_lord: str
    lagna_occupants: tuple[str, ...]
    fifth_sign: int
    fifth_lord: str
    fifth_occupants: tuple[str, ...]
    jupiter_sign: int
    jupiter_house: Optional[int]
    jupiter_dignity: Dignity
    child_loci: tuple[ChildLocus, ...]
    gender_indicators: tuple[Tagged, ...]


@dataclass(frozen=True)
class SaptamsaChildrenReading:
    """The whole reading: Raman-core (decides) + D-7 overlay (corroborates) + caveats."""
    raman_core: RamanCore
    d7_overlay: D7Overlay
    notes: tuple[Tagged, ...]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _house_of_sign(from_sign: int, offset: int) -> int:
    """Sign that is `offset` houses (1..12) from `from_sign` (1=itself)."""
    return ((from_sign - 1) + (offset - 1)) % 12 + 1


def _navamsa_dignity(planet: str, chart: RamanChart) -> Dignity:
    p = chart.planets.get(planet)
    if p is None:
        return "neutral"
    return _varga_dignity(planet, p.navamsa_sign)


def _d7_occupants(vc: VargaChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                 if n in vc.positions and vc.positions[n].house == house)


def _d7_aspecting_house(vc: VargaChart, house: int) -> tuple[str, ...]:
    """Planets casting a whole-sign aspect on D-7 `house` — reuses the locked drishti table
    (nodes 7th-only; Mars 4/8, Jupiter 5/9, Saturn 3/10)."""
    out: list[str] = []
    for name in _PLANET_ORDER:
        pos = vc.positions.get(name)
        if pos is None or pos.house is None or name not in drishti.ASPECT_HOUSES:
            continue
        dist = ((house - pos.house) % 12) + 1
        if dist in drishti.ASPECT_HOUSES[name]:
            out.append(name)
    return tuple(out)


def _afflictions(occupants: tuple[str, ...], aspecting: tuple[str, ...]) -> tuple[Tagged, ...]:
    """Malefics tenanting or aspecting the locus → Raman's Rāśi-5th effect, applied to the
    D-7 seat by the general varga principle (RAMAN_GENERAL_PRINCIPLE)."""
    seen: set[str] = set()
    out: list[Tagged] = []
    for name in _PLANET_ORDER:
        if name not in NATURAL_MALEFICS or name in seen:
            continue
        where = "on" if name in occupants else ("aspects" if name in aspecting else None)
        if where is None:
            continue
        seen.add(name)
        eff = _MALEFIC_5TH_EFFECT.get(name)
        if eff is None:
            continue
        text, cite = eff
        out.append(Tagged(f"{name} {where} the seat - {text}", "RAMAN_GENERAL_PRINCIPLE", cite))
    return tuple(out)


def _gender_indicators(chart: RamanChart, fifth_lord: str) -> tuple[Tagged, ...]:
    """Raman's Rāśi-5th sex-of-child rules that FIRE for this chart (RAMAN_EXPLICIT). These
    read the Rāśi, never the D-7 (Raman gives no D-7 gender rule)."""
    out: list[Tagged] = []
    ll = chart.planets.get(fifth_lord)
    if ll is not None and ll.rasi_house in (1, 2, 3):
        out.append(Tagged(
            "5th lord in the 1st/2nd/3rd → first child male", "RAMAN_EXPLICIT", "HTJAH-I:5206"))
    fifth = _house_of_sign(chart.asc_sign, 5)
    occ5 = {n for n, p in chart.planets.items() if p.rasi_house == 5}
    eleventh = _house_of_sign(chart.asc_sign, 11)
    malefic_11 = any(p.rasi_house == 11 and n in NATURAL_MALEFICS
                     for n, p in chart.planets.items())
    if malefic_11 and {"Moon", "Venus"} <= occ5:
        out.append(Tagged(
            "malefic in the 11th + Moon & Venus in the 5th → first-born a daughter",
            "RAMAN_EXPLICIT", "HTJAH-I:5219"))
    # feminine-predominance heuristic (Chart 107, HTJAH-I:5952). Raman's rule needs a
    # CONFLUENCE of feminine elements (even sign AND feminine/hermaphrodite planets, from Lagna
    # AND Chandra-Lagna); a single even 5th sign is a looser proxy for it, so this fires as a
    # GENERAL-PRINCIPLE lean, not a verbatim Raman rule (P-review fix).
    if fifth % 2 == 0:
        out.append(Tagged(
            "the 5th is a feminine (even) sign - leans toward female issue",
            "RAMAN_GENERAL_PRINCIPLE", "HTJAH-I:5952"))
    return tuple(out)


def _child_loci(vc: VargaChart) -> tuple[ChildLocus, ...]:
    """Eldest = the D-7 lagna (the domain-varga's own seat, RAMAN_GENERAL_PRINCIPLE).
    Successive children by the KP/Rath 5→7→9 house scheme — CLASSICAL_NONCITABLE, flagged
    (Raman gives no successive-child rule)."""
    plan = (
        (1, "eldest (1st child)", "D7-lagna", 1, "RAMAN_GENERAL_PRINCIPLE"),
        (2, "2nd child", "D7-7th", 7, "CLASSICAL_NONCITABLE"),
        (3, "3rd child", "D7-9th", 9, "CLASSICAL_NONCITABLE"),
    )
    out: list[ChildLocus] = []
    for ordinal, label, frame, house, scheme in plan:
        sign = _house_of_sign(vc.lagna_sign, house)
        occ = _d7_occupants(vc, house)
        asp = _d7_aspecting_house(vc, house)
        out.append(ChildLocus(
            ordinal=ordinal, label=label, frame=frame, scheme=scheme,  # type: ignore[arg-type]
            sign=sign, lord=SIGN_LORDS[sign], occupants=occ, aspecting=asp,
            afflictions=_afflictions(occ, asp)))
    return tuple(out)


# ---------------------------------------------------------------------------
# public builder
# ---------------------------------------------------------------------------

def build_saptamsa_children_reading(chart: RamanChart) -> SaptamsaChildrenReading:
    """Assemble the provenance-honest D-7 children reading for `chart`.

    ``raman_core`` decides (Raman's real method); ``d7_overlay`` corroborates (report-only)."""
    # --- Raman core (authoritative) ---
    fifth_sign = _house_of_sign(chart.asc_sign, 5)
    fifth_lord = SIGN_LORDS[fifth_sign]
    ll = chart.planets.get(fifth_lord)
    karaka = BHAVA_KARAKA[5]                          # Jupiter (Putrakāraka)
    jup = chart.planets.get(karaka)
    bk = beeja_kshetra(chart)
    pf = judge_house(chart, 5)
    child_sv = next((sv for sv in pf.significations if sv.signification == "children"), None)

    raman_core = RamanCore(
        rasi_fifth_sign=fifth_sign,
        rasi_fifth_lord=fifth_lord,
        rasi_fifth_lord_house=ll.rasi_house if ll else 0,
        rasi_fifth_lord_dignity=dignity(fifth_lord, chart) if ll else "neutral",
        rasi_fifth_occupants=tuple(n for n in _PLANET_ORDER
                                   if n in chart.planets and chart.planets[n].rasi_house == 5),
        rasi_fifth_aspecting=tuple(drishti.aspecting_house(5, chart)),
        putrakaraka=karaka,
        putrakaraka_house=jup.rasi_house if jup else 0,
        putrakaraka_dignity=dignity(karaka, chart) if jup else "neutral",
        putrakaraka_navamsa_dignity=_navamsa_dignity(karaka, chart),
        beeja_strong=bk.beeja_strong if bk else None,
        kshetra_strong=bk.kshetra_strong if bk else None,
        children_verdict=child_sv.verdict if child_sv else "insufficient-evidence",
        verdict_metadata=child_sv.metadata if child_sv else ())

    # --- D-7 overlay (report-only) ---
    vc = cast_varga_chart(chart, 7)
    d7_fifth_sign = _house_of_sign(vc.lagna_sign, 5)
    jd7 = vc.positions.get(karaka)
    overlay = D7Overlay(
        lagna_sign=vc.lagna_sign,
        lagna_lord=vc.lagna_lord,
        lagna_occupants=_d7_occupants(vc, 1),
        fifth_sign=d7_fifth_sign,
        fifth_lord=SIGN_LORDS[d7_fifth_sign],
        fifth_occupants=_d7_occupants(vc, 5),
        jupiter_sign=jd7.sign if jd7 else 0,
        jupiter_house=jd7.house if jd7 else None,
        jupiter_dignity=_varga_dignity(karaka, jd7.sign) if jd7 else "neutral",
        child_loci=_child_loci(vc),
        gender_indicators=_gender_indicators(chart, fifth_lord))

    notes = (
        Tagged("Raman defines the Saptamsa and names it the children varga, but never casts or "
               "reads a D-7 for children - the verdict below is his real method (Rasi 5th + "
               "Navamsa + Beeja/Kshetra); the D-7 overlay only corroborates.",
               "RAMAN_EXPLICIT", "HPA-11:187"),
        Tagged("Successive-child loci (2nd, 3rd) use the classical KP/Rath house scheme - ABSENT "
               "in Raman; treat as suggestive, not authoritative.",
               "CLASSICAL_NONCITABLE"),
    )
    return SaptamsaChildrenReading(raman_core=raman_core, d7_overlay=overlay, notes=notes)
