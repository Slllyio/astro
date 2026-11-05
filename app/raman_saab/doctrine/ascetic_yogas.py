"""Ascetic (Sanyasa / Parivraja) yogas -- only the formation rules Raman states in his own words.

Raman's textbook list is HTJAH-II:11025-11053 (the 10th-house chapter). He also names Parivraja
yogas in many worked charts, but loosely and with hedges -- "a slight adaptation of the 4th
stanza of Chap. XV of Brihat Jataka" (NH:2388-2390), "may be construed as some sort of a
Parivraja Yoga" (NH:3863-3864), "Strictly speaking no Parivraja yoga" (NH:6916-6917) -- and he
cancels the four-planets-in-one-sign pattern twice (NH:14603-14606, 14860-14863). Two independent
engine-blind reviews (2026-10-14) agreed: encode the stated list, not the hedged readings, and
document the under-firing (it misses Buddha, Vivekananda and Sivananda as Raman read them).

Encoded (both reviews):
- FOUR planets in the 10th "make one a renunciate" -- unless "the Sun be one of the planets ...
  and causes combustion" (HTJAH-II:11032-11035); combustion anywhere in the orb (II:4067-4076).
- The Moon in a decanate of Saturn aspected by Saturn, or in the Navamsa of Saturn or Mars aspected
  by Saturn (HTJAH-II:11037-11040). Subsumes "the Moon in a sign of Mars aspected by Saturn and in
  a decanate of Saturn" (11045-11047).
- "If Saturn or the Lagna lord aspect the lord of the sign occupied by the Moon" (11043-11045) --
  the strict form only: an aspect, never the planet being that lord itself (Raman's looser
  applications at NH:6921 and HTJAH-II:12659-12663 are not followed).
- "If the Moon is in the 9th house free of aspects" (11049-11050).

Not encoded: "three strong planets ... and the 10th lord also fortified" and the weak-Lagna-lord
rule (one review dropped them; they lean on strength grades); "five planets ... in a quadrant or
trine" (ambiguous: one sign or spread?); Jupiter in the 9th for six Lagnas gives "a holy man",
a weaker outcome than asceticism.
"""
from __future__ import annotations

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.varga import varga_sign_by_name
from app.raman_saab.doctrine import drishti


def _four_in_the_10th(chart: RamanChart) -> bool:
    there = [n for n, p in chart.planets.items() if p.rasi_house == 10]
    if len(there) < 4:
        return False
    sun_combusts = "Sun" in there and any(
        chart.planets[n].combust_fraction > 0.0 for n in there if n != "Sun")
    return not sun_combusts


def _moon_in_saturn_amsa_aspected_by_saturn(chart: RamanChart) -> bool:
    moon = chart.planets.get("Moon")
    if moon is None or not drishti.aspects_planet("Saturn", "Moon", chart):
        return False
    d3_lord = SIGN_LORDS[varga_sign_by_name(moon.lon, "D3")]
    d9_lord = SIGN_LORDS[varga_sign_by_name(moon.lon, "D9")]
    return d3_lord == "Saturn" or d9_lord in ("Saturn", "Mars")


def _moon_sign_lord_aspected(chart: RamanChart) -> bool:
    moon = chart.planets.get("Moon")
    if moon is None:
        return False
    target = SIGN_LORDS[moon.sign]
    return any(drishti.aspects_planet(a, target, chart)
               for a in {"Saturn", SIGN_LORDS[chart.asc_sign]})


def _moon_in_the_9th_unaspected(chart: RamanChart) -> bool:
    moon = chart.planets.get("Moon")
    return moon is not None and moon.rasi_house == 9 and not drishti.aspecting_planets("Moon", chart)


_RULES = (
    ("four planets in the 10th (HTJAH-II:11032)", _four_in_the_10th),
    ("the Moon in a Saturn decanate or a Saturn/Mars navamsa, aspected by Saturn "
     "(HTJAH-II:11037)", _moon_in_saturn_amsa_aspected_by_saturn),
    ("Saturn or the Lagna lord aspecting the Moon-sign lord (HTJAH-II:11043)",
     _moon_sign_lord_aspected),
    ("the Moon in the 9th free of aspects (HTJAH-II:11049)", _moon_in_the_9th_unaspected),
)


def ascetic_yogas(chart: RamanChart) -> list[str]:
    """Which of Raman's stated ascetic yogas the chart holds (empty when none)."""
    return [name for name, test in _RULES if test(chart)]
