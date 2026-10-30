"""Raman's "Special features" paragraph: what is unusual in the chart, named before any house.

T3 of ``docs/raman_saab/PROCEDURE_READER_FIXES_PREREG_2026-10-28.md``. Descriptive only: nothing
here changes a grade or a verdict. Each line is a fact the engine already computes, in the order
Raman tends to open with: the Lagna, planets whose Rasi and Navamsa dignities pull apart, planets
in their own Navamsa, Kemadruma and its cancellation, Kuja dosha from the three points, and
planets near a Bhava-sandhi with the margin in degrees (the margin shows how far the birth time
must be trusted before the sandhi reading can be).

Usage:
    from app.raman_saab.procedure.features import special_features
    special_features(chart)   # -> tuple[str, ...]
"""
from __future__ import annotations

from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives import bhangas
from app.raman_saab.primitives import relationships as rel
from app.raman_saab.primitives.dignity import dignity

SIGNS: tuple[str, ...] = (
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_NODES = frozenset({"Rahu", "Ketu"})
#: A planet this close to a Bhava-sandhi (degrees) is named with its margin.
SANDHI_MARGIN_DEG = 1.0


def _nav_state(planet: str, sign: int) -> str:
    if sign == rel.EXALTATION[planet][0]:
        return "exalted"
    if sign == rel.DEBILITATION[planet][0]:
        return "debilitated"
    if SIGN_LORDS[sign] == planet:
        return "own"
    return ""


def _and(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1] if xs else ""


def _arc(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def special_features(chart: RamanChart) -> tuple[str, ...]:
    """The unusual features of ``chart``, one sentence each."""
    out: list[str] = []
    nl = varga.navamsa_sign(chart.asc_lon)
    if nl == chart.asc_sign:
        out.append(f"The Lagna is vargottama: {SIGNS[chart.asc_sign]} rises in its own "
                   "Navamsa, a strength of the Lagna.")
    planets = [n for n in chart.planets if n not in _NODES]
    for n in planets:
        p = chart.planets[n]
        d1, d9 = dignity(n, chart), _nav_state(n, p.navamsa_sign)
        if d1 == "exalt" and d9 == "debilitated":
            out.append(f"{n} is exalted in {SIGNS[p.sign]} but debilitated in the Navamsa "
                       f"({SIGNS[p.navamsa_sign]}); the Rasi strength is qualified.")
        elif d1 == "debil" and d9 == "exalted":
            out.append(f"{n} is debilitated in {SIGNS[p.sign]} but exalted in the Navamsa "
                       f"({SIGNS[p.navamsa_sign]}), which cancels the debility (HTJAH:16178-16181).")
        elif d1 == "debil" and d9 == "debilitated":
            out.append(f"{n} is debilitated in both the Rasi and the Navamsa ({SIGNS[p.sign]}).")
    ll = SIGN_LORDS[chart.asc_sign]
    lp = chart.planets.get(ll)
    if lp is not None and _nav_state(ll, lp.navamsa_sign) == "debilitated" \
            and dignity(ll, chart) != "exalt":
        out.append(f"The Lagna lord {ll} is debilitated in the Navamsa "
                   f"({SIGNS[lp.navamsa_sign]}).")
    vg = [n for n in planets if chart.planets[n].vargottama]
    if vg:
        out.append("Vargottama: " + ", ".join(vg) + ".")
    own = [f"{n} ({SIGNS[chart.planets[n].navamsa_sign]})" for n in planets
           if not chart.planets[n].vargottama and _nav_state(n, chart.planets[n].navamsa_sign) == "own"]
    if own:
        out.append("In their own Navamsa: " + ", ".join(own) + ".")
    if bhangas.kemadruma(chart):
        if bhangas.kemadruma_bhanga(chart):
            out.append("Kemadruma is present (nothing beside the Moon) but cancelled "
                       "(3HC:2182-2185).")
        else:
            out.append("Kemadruma is present and not cancelled (HPA-20:208).")
    from app.raman_saab.doctrine.rule_sets.house_07_kalatra.combinations import (
        evaluate_kuja_dosha)
    kd = evaluate_kuja_dosha(chart)
    if kd.mars_present:
        stands = [f.origin for f in kd.frames if f.stands]
        free = [f.origin for f in kd.frames if not f.house]
        if stands:
            out.append("Kuja dosha from " + _and(stands) + "; free from "
                       + (_and(free) or "none") + ". Raman checks all three "
                       "(HTJAH-II:2593-2600)" + ("; it is neutralised by Mars' association"
                       if kd.conjunct_jupiter or kd.conjunct_moon or kd.universal_exempt
                       else "") + ".")
    if chart.bhava_sandhis:
        for n, p in chart.planets.items():
            m = min(_arc(p.lon, s) for s in chart.bhava_sandhis)
            if m < SANDHI_MARGIN_DEG:
                out.append(f"{n} is {m:.2f} degrees from a Bhava-sandhi; a small change in the "
                           "birth time moves it across, so its Bhava results are uncertain.")
    return tuple(out)
