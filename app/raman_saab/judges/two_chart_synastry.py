"""Two-chart synastry — Raman's horoscope matching, a REPORT-ONLY surface.

Overlays two nativities the way Raman matches horoscopes in HTJAH Vol I (chapter on matrimony,
HTJAH-I:9200-9433): the **Kuja (Mangal) doṣa** of each chart and their mutual cancellation, the
**benefic/malefic overlay** (where one person's Jupiter/Venus/Moon fall in the other's houses —
trines and 3/11 harmonise, 6/8/12 strain), the **Sun-Moon** relation (2/12 dwirdwādaśā is
difficult), and the **cross-points** (one person's Moon-sign being the other's Lagna is
stabilising). Raman himself de-emphasises Aṣṭakūṭa ("more than Kuta agreement, it is the basic
structure that matters", HTJAH-I:9263), so this surface weighs structure, not kūṭa points.

It NETS NOTHING — no "compatible / incompatible" verdict (Raman gives a units-tolerance guideline,
not a binary); it reports the contacts and lets the reader weigh them. Imported by nothing in the
D1 verdict path — the golden ratchet is untouched by construction.

Usage:
    from app.raman_saab.judges.two_chart_synastry import build_two_chart_synastry
    s = build_two_chart_synastry(chart_a, "husband", chart_b, "wife")
    s.kuja_comparison   # the Mangal-dosha balance between the two
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.saptamsa_reading import Tagged

# Raman's Kuja-doṣa house set (from Lagna / Moon / Venus): the 2nd, 4th, 7th, 8th, 12th.
_KUJA_HOUSES: Final[frozenset[int]] = frozenset({2, 4, 7, 8, 12})
# Mars own signs (Aries=1, Scorpio=8) + exaltation (Capricorn=10) mitigate the doṣa.
_MARS_STRONG: Final[frozenset[int]] = frozenset({1, 8, 10})
_SUPPORTIVE: Final[frozenset[int]] = frozenset({1, 3, 4, 5, 7, 9, 10, 11})
_DIFFICULT: Final[frozenset[int]] = frozenset({6, 8, 12})
_OVERLAY_BENEFICS: Final[tuple[str, ...]] = ("Jupiter", "Venus", "Moon")


@dataclass(frozen=True)
class KujaProfile:
    """One chart's Kuja (Mangal) doṣa picture."""
    role: str
    refs: tuple[str, ...]           # of Lagna/Moon/Venus, which show Mars in a Kuja house
    house_from_lagna: int           # Mars's house from the Lagna (0 if not a Kuja house)
    strength: int                   # number of references carrying the doṣa (0..3)
    mitigated: bool                 # Mars own/exalted, or joined by Jupiter


@dataclass(frozen=True)
class TwoChartSynastry:
    """Two nativities overlaid — REPORT-ONLY, nets no verdict."""
    role_a: str
    role_b: str
    kuja_a: KujaProfile
    kuja_b: KujaProfile
    kuja_comparison: tuple[Tagged, ...]
    overlays: tuple[Tagged, ...]
    sun_moon: tuple[Tagged, ...]
    cross_points: tuple[Tagged, ...]
    notes: tuple[Tagged, ...]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _house_from(from_sign: int, planet_sign: int) -> int:
    return ((planet_sign - from_sign) % 12) + 1


def _kuja_profile(role: str, chart: RamanChart) -> KujaProfile:
    mars = chart.planets.get("Mars")
    if mars is None:
        return KujaProfile(role, (), 0, 0, False)
    refs: list[str] = []
    for label, planet in (("Lagna", None), ("Moon", "Moon"), ("Venus", "Venus")):
        ref_sign = chart.asc_sign if planet is None else (
            chart.planets[planet].sign if planet in chart.planets else None)
        if ref_sign is None:
            continue
        if _house_from(ref_sign, mars.sign) in _KUJA_HOUSES:
            refs.append(label)
    from_lagna = _house_from(chart.asc_sign, mars.sign)
    jup = chart.planets.get("Jupiter")
    mitigated = mars.sign in _MARS_STRONG or (jup is not None and jup.sign == mars.sign)
    return KujaProfile(role, tuple(refs), from_lagna if from_lagna in _KUJA_HOUSES else 0,
                       len(refs), mitigated)


def _kuja_comparison(a: KujaProfile, b: KujaProfile) -> tuple[Tagged, ...]:
    out: list[Tagged] = []
    if a.strength and b.strength:
        out.append(Tagged(
            "both charts carry Kuja (Mangal) doṣa → the doṣas cancel each other (the classical "
            "mutual cancellation Raman notes in matching)", "RAMAN_EXPLICIT", "HTJAH-I:9352"))
    elif a.strength or b.strength:
        who = a if a.strength else b
        out.append(Tagged(
            f"only the {who.role}'s chart carries Kuja doṣa (Mars in the {who.house_from_lagna}th "
            f"from Lagna; on {who.strength} of Lagna/Moon/Venus) → an imbalance to weigh",
            "RAMAN_EXPLICIT", "HTJAH-I:9352"))
    else:
        out.append(Tagged("neither chart carries Kuja doṣa", "RAMAN_EXPLICIT", "HTJAH-I:9352"))
    for p in (a, b):
        if p.strength and p.mitigated:
            out.append(Tagged(
                f"the {p.role}'s Kuja doṣa is mitigated (Mars own/exalted, or joined by Jupiter)",
                "RAMAN_GENERAL_PRINCIPLE"))
    return tuple(out)


def _overlay_one_way(a_role: str, a: RamanChart, b_role: str, b: RamanChart) -> list[Tagged]:
    out: list[Tagged] = []
    for planet in _OVERLAY_BENEFICS:
        p = a.planets.get(planet)
        if p is None:
            continue
        h = _house_from(b.asc_sign, p.sign)
        if h in _SUPPORTIVE:
            out.append(Tagged(
                f"{a_role}'s {planet} falls in {b_role}'s {h}th house (a benefic in a supportive "
                "place) — a harmonising contact", "RAMAN_EXPLICIT", "HTJAH-I:9328"))
        elif h in _DIFFICULT:
            out.append(Tagged(
                f"{a_role}'s {planet} falls in {b_role}'s {h}th (a 6/8/12 place) — a straining "
                "contact", "RAMAN_GENERAL_PRINCIPLE"))
    return out


def _sun_moon(a_role: str, a: RamanChart, b_role: str, b: RamanChart) -> tuple[Tagged, ...]:
    am, bm = a.planets.get("Moon"), b.planets.get("Moon")
    if am is None or bm is None:
        return ()
    d = _house_from(bm.sign, am.sign)
    if d in (2, 12):
        return (Tagged(f"{a_role}'s and {b_role}'s Moons are 2/12 apart (dwirdwādaśā) — a difficult "
                       "mind-contact", "RAMAN_EXPLICIT", "HTJAH-I:9336"),)
    if d in (1, 5, 7, 9):
        return (Tagged(f"{a_role}'s and {b_role}'s Moons are in harmony ({d}th apart)",
                       "RAMAN_GENERAL_PRINCIPLE"),)
    return ()


def _cross_points(a_role: str, a: RamanChart, b_role: str, b: RamanChart) -> list[Tagged]:
    out: list[Tagged] = []
    am = a.planets.get("Moon")
    if am is not None and am.sign == b.asc_sign:
        out.append(Tagged(
            f"{a_role}'s Moon-sign is {b_role}'s Lagna — a stabilising bond", "RAMAN_EXPLICIT",
            "HTJAH-I:9342"))
    return out


def build_two_chart_synastry(chart_a: RamanChart, role_a: str,
                             chart_b: RamanChart, role_b: str) -> TwoChartSynastry:
    """Overlay two nativities and report the matching contacts (nets no verdict)."""
    ka, kb = _kuja_profile(role_a, chart_a), _kuja_profile(role_b, chart_b)
    overlays = tuple(_overlay_one_way(role_a, chart_a, role_b, chart_b)
                     + _overlay_one_way(role_b, chart_b, role_a, chart_a))
    sun_moon = _sun_moon(role_a, chart_a, role_b, chart_b)
    cross = tuple(_cross_points(role_a, chart_a, role_b, chart_b)
                  + _cross_points(role_b, chart_b, role_a, chart_a))
    notes = (
        Tagged("REPORT-ONLY: imported by nothing in the D1 verdict path; nets no compatible/"
               "incompatible verdict — Raman gives a units-tolerance guideline, not a binary.",
               "RAMAN_EXPLICIT", "HTJAH-I:9263"),
        Tagged("structure over kūṭa: Raman ranks chart structure above Aṣṭakūṭa point-agreement.",
               "RAMAN_EXPLICIT", "HTJAH-I:9263"),
    )
    return TwoChartSynastry(role_a=role_a, role_b=role_b, kuja_a=ka, kuja_b=kb,
                            kuja_comparison=_kuja_comparison(ka, kb), overlays=overlays,
                            sun_moon=sun_moon, cross_points=cross, notes=notes)
