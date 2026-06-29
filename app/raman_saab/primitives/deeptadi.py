"""Deeptadi avasthas — Raman's ten planetary RESULT-STATES (Hindu Predictive Astrology Ch.7:40-83).

Each names the state a planet is in (exaltation, own, friend, auspicious sub-division, retrograde,
last-quarter, enemy, combust, debilitated, accelerated) and the kind of results it gives. Computed
from dignity + combustion + retrogression + position. Surfaced as ADDITIVE testimony alongside
Shadbala / Baladi / Jagradadi; verdict-invariant (the dignity/combustion inputs already drive the
Parashari verdict, so Deeptadi only REPORTS the named state, it does not re-score it).

Usage:
    from app.raman_saab.primitives import deeptadi
    deeptadi.state("Saturn", chart)   # -> 'Khala' | 'Deeptha' | ...
    deeptadi.chart_states(chart)      # -> {planet: (state, result)}
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.dignity import dignity

#: state -> (polarity, the result Raman gives) — HPA Ch.7:46-83.
RESULTS: Final[dict[str, tuple[int, str]]] = {
    "Deeptha": (+1, "exalted -> gains from conveyances, respect, fame, wealth, good progeny"),
    "Swastha": (+1, "own sign -> fame, wealth, position, lands, happiness, good children"),
    "Muditha": (+1, "friend's sign -> happiness"),
    "Santha":  (+1, "auspicious sub-division -> strength, courage, helping relations, comfort"),
    "Sakta":   (+1, "retrograde -> courage, reputation, wealth and progeny"),
    "Peedya":  (-1, "last quarter of the sign -> prosecution, incarceration, expulsion"),
    "Deena":   (-1, "enemy's sign -> jealousy, worry, sickness, degradation"),
    "Vikala":  (-1, "combust -> disease, loss of wife/children, disgrace"),
    "Khala":   (-1, "debilitated -> losses, quarrels with kin, imprisonment"),
    "Bhita":   (-1, "accelerated/defeated -> losses, torture, foes, danger abroad"),
}


def state(planet: str, chart: RamanChart) -> str:
    """The planet's dominant Deeptadi avastha (priority-ordered: dignity, then position). 'Bhita'
    (acceleration / planetary-war defeat) needs speed data the engine does not carry and is omitted
    from the live classification; the other nine are computed."""
    p = chart.planets.get(planet)
    if p is None:
        return "Santha"
    d = dignity(planet, chart)
    if d == "exalt":
        return "Deeptha"
    if d in ("own", "moolatrikona"):
        return "Swastha"
    if d == "debil":
        return "Khala"
    if planet not in ("Sun", "Rahu", "Ketu") and getattr(p, "combust_fraction", 0.0) >= 0.5:
        return "Vikala"
    if d == "enemy":
        return "Deena"
    if getattr(p, "retrograde", False):
        return "Sakta"
    if d == "friend":
        return "Muditha"
    if (p.lon % 30.0) >= 22.5:                      # last quarter (4th pada) of the sign
        return "Peedya"
    return "Santha"


def polarity(planet: str, chart: RamanChart) -> int:
    """+1 (Deeptha/Swastha/Muditha/Santha/Sakta) or -1 (the afflicted states)."""
    return RESULTS[state(planet, chart)][0]


def chart_states(chart: RamanChart) -> dict[str, tuple[str, str]]:
    """{planet: (state, result-phrase)} for the seven visible grahas + the nodes."""
    out: dict[str, tuple[str, str]] = {}
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        if planet in chart.planets:
            s = state(planet, chart)
            out[planet] = (s, RESULTS[s][1])
    return out
