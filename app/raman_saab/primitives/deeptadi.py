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
    from the live classification; the other nine are computed.

    PRECEDENCE — SETTLED 2026-08-19 against the mounted corpus, so no future session
    re-hunts. Raman states NO precedence among the avasthas. What he does state is the
    opposite instruction: "Planets on account of their incessant movements get into certain
    states of existence called Avasthas which are ten in number. Each Avastha produces its
    own results. In the judgment of a horoscope ALL THESE DETAILS HAVE TO BE FULLY
    CONSIDERED." (HPA-7:39-44). A planet can satisfy several avasthas at once and he wants
    every one of them weighed.

    So the dignity-first ordering here is the ENGINE'S OWN CONVENTION and nothing more —
    it exists because this function has to return ONE string. It is not a claim about which
    state Raman thinks dominates, and it must not be described as one. The report already
    does the doctrinally right thing beside it: `states_all` discloses every state a planet
    matches, which is what HPA-7:42-44 actually asks for. If the single-state return is ever
    load-bearing for a verdict, that is the place to look first."""
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


def states_all(planet: str, chart: RamanChart) -> tuple[str, ...]:
    """EVERY Deeptadi state the planet matches, in `state()`'s own priority order (dignity
    first, then combustion, retrogression, position) — so the head of the tuple is always
    exactly `state()`'s answer and the tail is the secondary states that answer hides.
    Additive DISCLOSURE accessor (2026-08-18 report-critique): a retrograde planet in an
    enemy sign is Deena AND Sakta; showing only Deena beside a positions table that shows
    'retrograde' reads as a contradiction. Nothing judges from the tail; `state()` itself
    is unchanged."""
    p = chart.planets.get(planet)
    if p is None:
        return ("Santha",)
    d = dignity(planet, chart)
    matches: list[str] = []
    if d == "exalt":
        matches.append("Deeptha")
    if d in ("own", "moolatrikona"):
        matches.append("Swastha")
    if d == "debil":
        matches.append("Khala")
    if planet not in ("Sun", "Rahu", "Ketu") and getattr(p, "combust_fraction", 0.0) >= 0.5:
        matches.append("Vikala")
    if d == "enemy":
        matches.append("Deena")
    if getattr(p, "retrograde", False):
        matches.append("Sakta")
    if d == "friend":
        matches.append("Muditha")
    if (p.lon % 30.0) >= 22.5:                      # last quarter (4th pada) of the sign
        matches.append("Peedya")
    return tuple(matches) if matches else ("Santha",)


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
