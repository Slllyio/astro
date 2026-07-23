"""Two-spouse progeny synthesis — a REPORT-ONLY cross-reference of BOTH parents' charts.

WHY THIS EXISTS (the doctrinal spine — read before extending):
B. V. Raman judges progeny from a native's OWN 5th house/Navamsa/sphutas, but for a couple
he explicitly says to judge **both spouses' 5th houses** (HTJAH-I:5436) and allows one
partner's strong significators to **offset** the other's affliction (HTJAH-I:5968). He gives,
however, **NO formula** for netting two parental verdicts into a single child verdict. Per the
Prime Directive's "no silent approximation", this surface therefore does exactly what Raman's
text supports and no more:

  * it REPORTS each parent's authoritative children testimony (from `saptamsa_reading`);
  * it surfaces their CONCORDANCES — structural afflictions true in *both* charts (a
    two-witness signal that Raman's cross-check is meant to catch);
  * it surfaces the REDEMPTIVE THREAD — the offsetting/mitigating significators (5968);
  * and it **nets nothing** — computes no combined verdict. The final synthesis is the human's.

VERDICT-AUTHORITY INVARIANT: this module is imported by NOTHING in the D1 verdict path
(`judges/house_template.py` never imports it) — the golden ratchet is untouched by
construction. It is a standalone reading, exactly like `judges/saptamsa_reading.py`.

Usage:
    from app.raman_saab.judges.two_spouse_children import build_two_spouse_children_synthesis
    syn = build_two_spouse_children_synthesis(father_chart, mother_chart, "father", "mother")
    syn.concordances        # afflictions true in BOTH charts (HTJAH-I:5436)
    syn.redemptive_thread   # offsetting significators (HTJAH-I:5968)
    # syn has NO combined_verdict — 'report both, net nothing' by design.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.saptamsa_reading import (
    SaptamsaChildrenReading, Tagged, build_saptamsa_children_reading)
from app.raman_saab.judges.varga_judge import Dignity

_DUSTHANAS: Final[tuple[int, ...]] = (6, 8, 12)
_DIGNIFIED: Final[tuple[Dignity, ...]] = ("exalt", "own")


@dataclass(frozen=True)
class SpouseChildTestimony:
    """One parent's children testimony, distilled from that chart's Saptamsa reading."""
    role: str
    verdict: str                       # from raman_core (Raman's real method)
    fifth_sign: int
    fifth_lord: str
    fifth_lord_house: int
    fifth_lord_dignity: Dignity
    putrakaraka_house: int
    putrakaraka_rasi_dignity: Dignity
    putrakaraka_navamsa_dignity: Dignity
    beeja_strong: Optional[bool]
    kshetra_strong: Optional[bool]
    d7_eldest_afflictions: tuple[Tagged, ...]   # eldest-child seat (D-7 lagna) afflictions


@dataclass(frozen=True)
class TwoSpouseChildrenSynthesis:
    """Both parents' progeny testimonies cross-referenced — REPORT-ONLY, nets no verdict.

    There is DELIBERATELY no ``combined_verdict`` field: Raman supplies no netting rule
    (HTJAH-I:5436/5968 are qualitative), so the human draws the final conclusion."""
    testimonies: tuple[SpouseChildTestimony, ...]
    concordances: tuple[Tagged, ...]      # structural afflictions true in BOTH charts
    redemptive_thread: tuple[Tagged, ...]  # offsetting/mitigating significators (5968)
    notes: tuple[Tagged, ...]


# ---------------------------------------------------------------------------
# distillation + cross-reference
# ---------------------------------------------------------------------------

def _testimony(role: str, r: SaptamsaChildrenReading) -> SpouseChildTestimony:
    rc = r.raman_core
    eldest = r.d7_overlay.child_loci[0] if r.d7_overlay.child_loci else None
    return SpouseChildTestimony(
        role=role,
        verdict=rc.children_verdict,
        fifth_sign=rc.rasi_fifth_sign,
        fifth_lord=rc.rasi_fifth_lord,
        fifth_lord_house=rc.rasi_fifth_lord_house,
        fifth_lord_dignity=rc.rasi_fifth_lord_dignity,
        putrakaraka_house=rc.putrakaraka_house,
        putrakaraka_rasi_dignity=rc.putrakaraka_dignity,
        putrakaraka_navamsa_dignity=rc.putrakaraka_navamsa_dignity,
        beeja_strong=rc.beeja_strong,
        kshetra_strong=rc.kshetra_strong,
        d7_eldest_afflictions=eldest.afflictions if eldest else ())


def _concordances(a: SpouseChildTestimony, b: SpouseChildTestimony) -> tuple[Tagged, ...]:
    """Structural afflictions present in BOTH charts — the two-witness signal Raman's
    both-spouses cross-check (HTJAH-I:5436) is designed to catch. Scoped to two spouses."""
    out: list[Tagged] = []
    if a.verdict == b.verdict == "afflicted":
        out.append(Tagged(
            "both parents' 5th houses independently read the children matter AFFLICTED - a "
            "two-witness concordance (Raman judges BOTH spouses' 5th houses for progeny)",
            "RAMAN_EXPLICIT", "HTJAH-I:5436"))
    if a.beeja_strong is False and b.beeja_strong is False:
        out.append(Tagged(
            "Beeja (male-seed sphuta) is weak in BOTH charts - a concordant fertility affliction",
            "RAMAN_EXPLICIT", "HTJAH-I:5517"))
    if a.kshetra_strong is False and b.kshetra_strong is False:
        out.append(Tagged(
            "Kshetra (female-field sphuta) is weak in BOTH charts - a concordant fertility "
            "affliction", "RAMAN_EXPLICIT", "HTJAH-I:5517"))
    if a.fifth_lord_house in _DUSTHANAS and b.fifth_lord_house in _DUSTHANAS:
        out.append(Tagged(
            f"the 5th-lord sits in a dusthana in BOTH charts ({a.role}: house "
            f"{a.fifth_lord_house}; {b.role}: house {b.fifth_lord_house}) - the progeny "
            "significator exiled to a house of loss repeats across both spouses",
            "RAMAN_GENERAL_PRINCIPLE", "HTJAH-I:5192"))
    if a.putrakaraka_house in _DUSTHANAS and b.putrakaraka_house in _DUSTHANAS:
        out.append(Tagged(
            "the Putra-Karaka (Jupiter) sits in a dusthana in BOTH charts",
            "RAMAN_GENERAL_PRINCIPLE", "HTJAH-I:5192"))
    return tuple(out)


def _redemptive(tests: tuple[SpouseChildTestimony, ...]) -> tuple[Tagged, ...]:
    """The offsetting/mitigating significators Raman permits (HTJAH-I:5968) — reported, never
    netted into the verdict."""
    out: list[Tagged] = []
    nav = [t for t in tests if t.putrakaraka_navamsa_dignity in _DIGNIFIED]
    for t in nav:
        out.append(Tagged(
            f"Putra-Karaka Jupiter is navamsa-{t.putrakaraka_navamsa_dignity} in the {t.role}'s "
            "chart - fruit-chart dignity ('withheld, not annihilated')",
            "RAMAN_GENERAL_PRINCIPLE", "HTJAH-I:5902"))
    if len(tests) > 1 and len(nav) == len(tests):
        out.append(Tagged(
            "the redemptive thread is a TWO-WITNESS finding: the Putra-Karaka is navamsa-"
            "dignified in BOTH parents' charts - the promise is strained/late but carries "
            "underlying substance", "RAMAN_GENERAL_PRINCIPLE", "HTJAH-I:5968"))
    for t in tests:
        if t.fifth_lord_dignity == "exalt":
            out.append(Tagged(
                f"the 5th-lord {t.fifth_lord} is EXALTED in the {t.role}'s chart (real underlying "
                f"capacity, though placed in house {t.fifth_lord_house})",
                "RAMAN_GENERAL_PRINCIPLE", "HTJAH-I:5968"))
    for t in tests:
        if t.putrakaraka_house == 5:
            out.append(Tagged(
                f"the Putra-Karaka (Jupiter) occupies the 5th itself in the {t.role}'s chart - "
                "the significator seated in its own progeny house",
                "RAMAN_GENERAL_PRINCIPLE", "HTJAH-I:5968"))
    return tuple(out)


def _notes() -> tuple[Tagged, ...]:
    return (
        Tagged("Raman prescribes judging BOTH spouses' 5th houses for progeny (HTJAH-I:5436) "
               "and allows one partner's strong significators to offset the other's "
               "(HTJAH-I:5968).", "RAMAN_EXPLICIT", "HTJAH-I:5436"),
        Tagged("He gives NO formula for netting two parental verdicts into one child verdict; "
               "this synthesis REPORTS both testimonies + their concordances and redemptive "
               "threads and NETS NOTHING - the final reading is the human's.", "ABSENT_IN_RAMAN"),
        Tagged("REPORT-ONLY: imported by nothing in the D1 verdict path; the golden ratchet is "
               "untouched by construction.", "RAMAN_GENERAL_PRINCIPLE"),
    )


# ---------------------------------------------------------------------------
# public builders
# ---------------------------------------------------------------------------

def synthesize_from_readings(
    reading_a: SaptamsaChildrenReading, role_a: str,
    reading_b: SaptamsaChildrenReading, role_b: str,
) -> TwoSpouseChildrenSynthesis:
    """Cross-reference two already-built Saptamsa readings (the testable, swisseph-free core)."""
    ta = _testimony(role_a, reading_a)
    tb = _testimony(role_b, reading_b)
    tests = (ta, tb)
    return TwoSpouseChildrenSynthesis(
        testimonies=tests,
        concordances=_concordances(ta, tb),
        redemptive_thread=_redemptive(tests),
        notes=_notes())


def build_two_spouse_children_synthesis(
    parent_a: RamanChart, parent_b: RamanChart,
    role_a: str = "parent A", role_b: str = "parent B",
) -> TwoSpouseChildrenSynthesis:
    """Build both parents' Saptamsa readings and cross-reference them (HTJAH-I:5436/5968)."""
    return synthesize_from_readings(
        build_saptamsa_children_reading(parent_a), role_a,
        build_saptamsa_children_reading(parent_b), role_b)
