"""The procedure reader: a horoscope read house by house the way Raman reads his worked charts.

Stage 0, once per chart (spec 2): the functional benefics, malefics and yogakarakas for the
Lagna (HTJAH:519-646); the stronger of the Lagna and the Moon (HTJAH:644-646, measured by the
engine's ``chart_overview`` operationalisation); the span of life (the engine's
``ayurdaya.longevity``) and the Mahadashas that can run within it (HTJAH:763-765, 1578-1580).

Then, for each house and each matter: House -> Lord -> Karaka -> From the Moon -> Conclusion,
followed by the timing rules for the matter's events (spec 3, 5).

SEPARATE INSTRUMENT. Nothing here feeds ``house_template``, the scored judge, the golden ratchet,
the doctrine snapshot or the report sections; nothing in those imports this package.

Usage:
    from app.raman_saab.procedure import read_procedure
    reading = read_procedure(chart)
    reading.to_dict()
"""
from __future__ import annotations

import logging
from typing import Optional

import swisseph as swe

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.functional_nature import functional_nature, is_yogakaraka
from app.raman_saab.procedure import timing as tm
from app.raman_saab.procedure.citations import cite
from app.raman_saab.procedure.conclusion import conclude
from app.raman_saab.procedure.features import special_features
from app.raman_saab.procedure.grading import (
    SIGNS, grade_from_moon, grade_house, grade_planet, lord_of)
from app.raman_saab.procedure.matters import MATTERS, Matter, matter_for
from app.raman_saab.procedure.model import (
    Factor, MatterReading, ProcedureReading, StageZero)

logger = logging.getLogger(__name__)

_ORDER = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

#: Where the karaka sitting in the matter's own house harms it (Raman applies karako bhava
#: nashaya without naming it): mother, children, father.
_KARAKA_BHAVA: dict[str, tuple[tuple[int, ...], str]] = {
    "mother": ((4,), "karaka_in_bhava_mother"),
    "children": ((5,), "karaka_in_bhava_children"),
    "father": ((9,), "karaka_in_bhava_father"),
}

CONVENTIONS: tuple[str, ...] = (
    "Each testimony counts one step; a factor's Rasi grade is the net count on the five-step "
    "scale afflicted / blemished / moderate / fairly strong / strong.",
    "The Navamsa moves a factor's grade by at most one step (exalted, own or vargottama up; "
    "debilitated down; for a house, the benefics against the malefics in the same house from "
    "the Navamsa Lagna).",
    "A factor votes good at fairly strong or above, bad at blemished or below; two good votes "
    "make favourable, two bad votes afflicted, anything else mixed.",
    "Where Raman uses no karaka (the 9th's fortune, the 10th) the view from the Moon takes the "
    "third vote.",
    "The star lord (longevity and the father only) counts good in its own star or a benefic "
    "lord's, bad in a node's or the 6th/8th/12th lord's.",
    "The stronger of the Lagna and the Moon is the engine's measure (the sign lords' total "
    "Shadbala) and is reported, not used to re-weight: Raman prints no re-weighting rule.",
    "The marriageable window is ages 16 to 33.",
    "Wealth-yoga planets include 2nd/5th/9th/11th lords associated with one another.",
    "Saturn lowering the longevity band when weak mirrors his printed upward move.",
    "The 6th is read with the forward template, though Raman reads it backwards from the "
    "known disease.",
)


def _label(jd: float) -> str:
    y, m, _d, _h = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y)}-{int(m):02d}"


def stage_zero(chart: RamanChart) -> StageZero:
    """Spec 2: functional natures, the stronger reference, the span and the dasas within it."""
    functional = tuple((p, functional_nature(p, chart)) for p in _ORDER if p in chart.planets)
    ykaraka = tuple(p for p in ("Mars", "Venus", "Saturn")
                    if p in chart.planets and is_yogakaraka(p, chart.asc_sign))
    from app.raman_saab.judges.chart_overview import _stronger_frame
    stronger = _stronger_frame(chart)
    span = span_class = method = balarishta = None
    dasas: list[tuple[str, str, str, str]] = []
    if chart.jd_ut is not None:
        from app.raman_saab.primitives import ayurdaya
        from app.raman_saab.primitives import vimshottari as vd
        res = ayurdaya.longevity(chart)
        span, span_class, method = round(res.total_years, 1), res.longevity_class, res.method
        end = chart.jd_ut + res.total_years * 365.2425
        for md in vd.mahadasha_timeline(chart, 130.0):
            if md.end_jd < chart.jd_ut:
                continue
            if md.start_jd >= end:
                status = "after the span: none of its periods runs"
                dasas.append((md.maha, _label(md.start_jd), _label(md.end_jd), status))
                break
            status = ("within the span" if md.end_jd <= end else
                      "begins within the span and runs past it")
            dasas.append((md.maha, _label(max(md.start_jd, chart.jd_ut)), _label(md.end_jd),
                          status))
    if chart.balarishta is not None:
        b = chart.balarishta
        balarishta = ("present" + (" but cancelled" if b.cancelled else "")
                      if b.applies else "absent")
    note = ("the stronger of the two by the total Shadbala of their sign lords (the engine's "
            "measure); on a chart without Shadbala the Lagna")
    lagna = f"{SIGNS[chart.asc_sign]} (lord {SIGN_LORDS[chart.asc_sign]})"
    return StageZero(lagna, functional, ykaraka, stronger, note, span, span_class, method,
                     balarishta, tuple(dasas),
                     (cite("functional_for_dasha"), cite("functional_benefics"),
                      cite("functional_malefics"), cite("yogakaraka"), cite("stronger_reference"),
                      cite("span_first"), cite("dasa_within_span")),
                     special_features(chart))


def read_matter(chart: RamanChart, house: int, key: Optional[str] = None, *,
                with_timing: bool = True, span: Optional[float] = None,
                span_class: Optional[str] = None) -> MatterReading:
    """House -> Lord -> Karaka -> From the Moon -> Conclusion (-> timing) for one matter."""
    matter = matter_for(house, key)
    return _read(chart, matter, with_timing, span, span_class)


def _read(chart: RamanChart, matter: Matter, with_timing: bool, span: Optional[float],
          span_class: Optional[str]) -> MatterReading:
    house = matter.house
    lord = lord_of(chart, house)
    factors: dict[str, Factor] = {"house": grade_house(chart, house)}
    factors["lord"] = grade_planet(chart, lord, step="lord", house=house,
                                   role=f"the {_ord(house)} lord", star_lord=matter.star_lord)
    karaka_note = matter.karaka_note
    if matter.karaka is not None:
        if matter.karaka == lord:
            f = factors["lord"]
            factors["karaka"] = Factor("karaka", f"the karaka {lord}", f.items, f.rasi_grade,
                                       f.navamsa_shift, f.navamsa_note, f.grade, f.redeeming,
                                       "lord", "the karaka is the lord itself: the same "
                                               "discussion applies")
        else:
            kb, kcite = _KARAKA_BHAVA.get(matter.key, ((), ""))
            factors["karaka"] = grade_planet(chart, matter.karaka, step="karaka", house=house,
                                             role="the karaka", star_lord=matter.star_lord,
                                             karaka_bhava=kb, karaka_bhava_cite=kcite)
    factors["moon"] = grade_from_moon(chart, house)
    lagna_lord = None
    if matter.decider == "longevity":
        ll = SIGN_LORDS[chart.asc_sign]
        lagna_lord = grade_planet(chart, ll, step="lord", house=1, role="the Lagna lord",
                                  star_lord=True)
    links = tm.wealth_links(chart) if matter.decider == "gains" else ()
    life: Optional[tuple[float, str]] = None
    if matter.decider == "longevity" and chart.jd_ut is not None:
        if span is not None and span_class is not None:
            life = (span, span_class)
        else:
            from app.raman_saab.primitives import ayurdaya
            res = ayurdaya.longevity(chart)
            life = (res.total_years, res.longevity_class)
    concl = conclude(matter, factors, lagna_lord=lagna_lord, wealth_links=links, life=life)
    timing = tm.timing_for(chart, matter, span, span_class) if with_timing else ()
    ordered = tuple(factors[s] for s in ("house", "lord", "karaka", "moon") if s in factors)
    return MatterReading(house, matter.key, matter.label, matter.karaka, karaka_note, ordered,
                         concl, timing)


def _ord(n: int) -> str:
    from app.raman_saab.ordinals import ordinal
    return ordinal(n)


def read_procedure(chart: RamanChart, *, name: str = "", with_timing: bool = True
                   ) -> ProcedureReading:
    """The whole reading: Stage 0, then every matter of houses 1-12 in Raman's order."""
    s0 = stage_zero(chart)
    matters: list[MatterReading] = []
    for house in range(1, 13):
        for m in MATTERS[house]:
            matters.append(_read(chart, m, with_timing, s0.span_years, s0.span_class))
    nm = name or (chart.birth.name if chart.birth is not None else "")
    return ProcedureReading(nm, chart.ayanamsa, s0, tuple(matters), CONVENTIONS)
