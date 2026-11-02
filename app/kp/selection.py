"""Krishnamurti's selection of the strong and fruitful significators, and the timing it narrows.

The A-D ladder (:mod:`app.kp.significators`) lists every planet tied to a house.
Krishnamurti then asks "how to eliminate the useless ones and select the useful
ones" (KPR4:p.118) and answers in three steps, each encoded here (rulings R24-R26):

1. **Strong significators** (R24). For each occupant of the house, the planets in
   its stars give the house's results and "are stronger than" the occupant; "if
   there is no planet in any of the 3 stars of the occupant, then the occupant
   offers the results ... and it is stronger than the lord" (KPR5:pp.208-209). An
   unoccupied house goes to the planets in its lord's stars, or, if none, to the
   lord itself ("If there is no planet, Sun gives lagna bhava results", KPR5:p.147).
   A node standing for a strong significator is taken too ("Kethu in Virgo
   represents Mercury. Take Kethu", KPR6:p.162), and so are planets in that node's
   star ("Kethu represents Saturn. Rahu is in Kethu star and Rahu is a significator",
   KPR4:p.190).
2. **Fruitful** (R25). "Further the sub lord of each of the significators. If a
   planet is in such a position that its sub lord is connected with the houses 2, 7
   and 11 then this planet is useful" (KPR4:p.118); a significator "in unfavourable
   sub" makes the matters suffer (KPR5:p.147). A significator is fruitful when its
   sub-lord signifies (A-D) a favourable house of the matter; a sub-lord that also
   signifies a denial house is flagged, not dropped.
3. **Ruling planets** (R26). "Ruling planets at the moment of judgement must agree"
   (KPR4:p.118); "the ruling planets at the moment of judgment ... are the real
   benefactors" (KPR4:p.189). Applied only when a moment of judgment is given, and
   the result then depends on that moment, as Krishnamurti's method does.

Strength (step 1) ranks; it does not filter. Krishnamurti's own worked periods use
lords the ladder names but step 1 would pass over (a bhukti of the "lord of 6" when 6
is occupied, KPR5:p.150), so the filter is steps 2 and 3, the ones he states as
elimination ("eliminate the useless ones", KPR4:p.118). Two flags ride along,
never filtering: Saturn among the selected ("will not deny but will cause delay",
KPR4:p.109) and selected planets that are retrograde or sit in a retrograde planet's
star (failure "when the significator ... is retrograde", KPR6:p.280). Nothing here
changes a verdict. :func:`selected_windows` narrows the R17 timing candidates to periods whose
three lords all survive steps 2-3, and reports how many of them are strong.

Day-fixing (R27): inside a selected window the day comes when the Sun (or, for a
finer day, the Moon) transits a position whose sign, star and sub lords are all
fruitful significators ("Sun, lord of 2, to fix the day must transit in Venus sign,
Moon star Saturn or Ketu sub", KPR4:p.133; again KPR4:p.189, where the sign lord
Venus is a significator but not a ruling planet, so R26 is not applied to it).
:func:`day_points` lists those positions and :func:`day_fix` finds the passes.

Usage:
    from app.kp.chart import Birth, cast
    from app.kp.selection import select, selected_windows
    c = cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))
    s = select(c, "marriage", judged=Birth(2026, 11, 2, 10, 0, tz=5.5, lat=12.97, lon=77.59))
    s.selected
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final

import swisseph as swe

from app.kp.chart import NODES, Birth, KPChart, cast
from app.kp.dasa import Period, periods_between
from app.kp.judgment import Matter, _matter
from app.kp.ruling import ruling_planets
from app.kp.subs import Division, divisions
from app.kp.transit import transit_longitude
from app.kp.significators import (
    houses_signified,
    node_represents,
    planet_significations,
)

CITATIONS: Final[tuple[str, ...]] = (
    "KPR4-ELIMINATE", "KPR5-STAR-DWELLERS", "KPR5-OCCUPANT-EMPTY", "KPR5-LORD-EMPTY", "KPR6-TAKE-NODE", "KPR4-NODE-STAR",
    "KPR4-USEFUL", "KPR5-SUB-THRIVE", "KPR4-RP-BENEFACTORS",
    "KPR4-SATURN-DELAY", "KPR6-RETRO-FAIL", "KPR4-DAY-FIX", "KPR4-DAY-FIX-2",
)


@dataclass(frozen=True, slots=True)
class Strong:
    """One strong significator of one house and why (R24)."""

    planet: str
    house: int
    why: str


def strong_from(houses: Iterable[int], occupants: Mapping[int, tuple[str, ...]],
                lords: Mapping[int, str], star_lord: Mapping[str, str],
                represents: Mapping[str, tuple[str, ...]]) -> tuple[Strong, ...]:
    """Ruling R24 on plain data, so it can be checked against printed examples.

    ``occupants[h]`` are the planets in bhava ``h``; ``lords[h]`` its cusp's sign lord;
    ``star_lord[p]`` each planet's star lord; ``represents[node]`` the planets a node
    stands for.
    """
    out: list[Strong] = []
    for h in houses:
        heads = occupants.get(h, ())
        kind = "occupant" if heads else "lord"
        if not heads:
            heads = (lords[h],)
        for head in heads:
            dwellers = [p for p, s in star_lord.items() if s == head]
            if dwellers:
                out += [Strong(p, h, f"in the star of {head}, {kind} of {h}") for p in dwellers]
            else:
                out.append(Strong(head, h, f"{kind} of {h}, no planet in its star"))
    seen = {(s.planet, s.house) for s in out}
    for node, reps in represents.items():
        for s in list(out):
            if s.planet in reps and (node, s.house) not in seen:
                seen.add((node, s.house))
                out.append(Strong(node, s.house, f"node standing for {s.planet}"))
                # The node acts as the planet, so planets in the node's star act for it too:
                # "Kethu represents Saturn. Rahu is in Kethu star and Rahu is a significator"
                # (KPR4:p.190).
                for p, sl in star_lord.items():
                    if sl == node and p != node and (p, s.house) not in seen:
                        seen.add((p, s.house))
                        out.append(Strong(p, s.house, f"in the star of {node}, standing for {s.planet}"))
    uniq: dict[tuple[str, int], Strong] = {}
    for s in out:
        uniq.setdefault((s.planet, s.house), s)
    return tuple(uniq.values())


def strong_significators(chart: KPChart, houses: Iterable[int]) -> tuple[Strong, ...]:
    """Ruling R24 for ``houses`` of ``chart``."""
    hs = tuple(houses)
    return strong_from(
        hs,
        {h: chart.occupants(h) for h in hs},
        {h: chart.house_lord(h) for h in hs},
        {p: pt.star_lord for p, pt in chart.planets.items()},
        {n: node_represents(chart, n) for n in NODES},
    )


@dataclass(frozen=True, slots=True)
class Fruit:
    """Ruling R25 for one significator: what its sub-lord signifies."""

    planet: str
    sub_lord: str
    favourable: frozenset[int]
    denial: frozenset[int]

    @property
    def fruitful(self) -> bool:
        return bool(self.favourable)


@dataclass(frozen=True, slots=True)
class Selection:
    """Every step of the selection for one matter."""

    matter: Matter
    significators: tuple[str, ...]     # A-D significators of a favourable house
    strong: tuple[Strong, ...]
    fruit: dict[str, Fruit]
    ruling: tuple[str, ...] | None     # None when no moment of judgment was given
    selected: tuple[str, ...]          # significators that are fruitful and (if given) ruling
    delay: bool = False                # Saturn is selected (KPR4-SATURN-DELAY)
    retrograde: tuple[str, ...] = ()   # selected planets retrograde or in a retrograde star

    def to_dict(self) -> dict:
        return {
            "matter": self.matter.key, "significators": list(self.significators),
            "strong": [f"{s.planet} ({s.house}: {s.why})" for s in self.strong],
            "fruitful": [p for p, f in self.fruit.items() if f.fruitful],
            "sub_also_denial": [p for p, f in self.fruit.items() if f.fruitful and f.denial],
            "ruling_planets": None if self.ruling is None else list(self.ruling),
            "selected": list(self.selected), "saturn_delay": self.delay,
            "retrograde_or_in_retrograde_star": list(self.retrograde), "citations": list(CITATIONS),
        }


def select(chart: KPChart, matter: str | Matter, *, judged: Birth | None = None) -> Selection:
    """Significators kept by R25 (fruitful) and, given a moment of judgment, R26 (ruling);
    R24's strong significators are reported for ranking."""
    m = _matter(matter)
    sigs = planet_significations(chart)
    hs = {p: houses_signified(chart, p, sigs) for p in sigs}
    significators = tuple(p for p in chart.planets if hs[p] & m.favourable)
    strong = strong_significators(chart, sorted(m.favourable))
    fruit = {}
    for p in chart.planets:
        sub = chart.planets[p].sub_lord
        fruit[p] = Fruit(p, sub, hs[sub] & m.favourable, hs[sub] & m.denial)
    ruling: tuple[str, ...] | None = None
    if judged is not None:
        rp = ruling_planets(cast(judged, node_mode=chart.node_mode))
        ruling = tuple(dict.fromkeys((*rp.planets, *rp.node_agents)))
    keep = [p for p in significators if fruit[p].fruitful and (ruling is None or p in ruling)]

    def retro(p: str) -> bool:
        return p not in NODES and chart.planets[p].retrograde

    flagged = tuple(p for p in keep if retro(p) or retro(chart.planets[p].star_lord))
    return Selection(m, significators, strong, fruit, ruling, tuple(keep), "Saturn" in keep, flagged)


@dataclass(frozen=True, slots=True)
class SelectedWindow:
    """A dasa-bhukti-antara whose three lords are all selected significators."""

    period: Period
    strong_lords: tuple[str, ...]

    def label(self) -> str:
        a, b = self.period.dates()
        return f"{self.period.label()} {a} to {b} ({len(self.strong_lords)} of 3 lords strong)"


def selected_windows(chart: KPChart, matter: str | Matter, jd0: float, jd1: float, *,
                     judged: Birth | None = None) -> tuple[SelectedWindow, ...]:
    """Antaras in ``[jd0, jd1)`` whose MD, AD and PD lords are all in :func:`select`'s ``selected``."""
    sel = select(chart, matter, judged=judged)
    chosen = set(sel.selected)
    strong = {s.planet for s in sel.strong}
    return tuple(SelectedWindow(p, tuple(lord for lord in p.lords if lord in strong))
                 for p in periods_between(chart, jd0, jd1, depth=3) if set(p.lords) <= chosen)


def day_points(chart: KPChart, matter: str | Matter) -> tuple[Division, ...]:
    """Divisions whose sign, star and sub lords are all fruitful significators (R27)."""
    keep = set(select(chart, matter).selected)
    return tuple(d for d in divisions() if {d.sign_lord, d.star_lord, d.sub_lord} <= keep)


@dataclass(frozen=True, slots=True)
class DayPass:
    """A body passing a day-fixing position."""

    body: str
    division: Division
    start_jd: float
    end_jd: float

    def label(self) -> str:
        y, m, d, _ = swe.revjul(self.start_jd, swe.GREG_CAL)
        dv = self.division
        return (f"{self.body} in {dv.sign_lord} sign, {dv.star_lord} star, {dv.sub_lord} sub "
                f"from {y:04d}-{m:02d}-{d:02d}")


def day_fix(chart: KPChart, matter: str | Matter, jd0: float, jd1: float, *,
            bodies: tuple[str, ...] = ("Sun",), step_days: float = 0.05) -> tuple[DayPass, ...]:
    """When ``bodies`` pass the R27 positions inside ``[jd0, jd1)``, in time order."""
    pts = day_points(chart, matter)
    if not pts:
        return ()
    out: list[DayPass] = []
    for b in bodies:
        cur: tuple[Division, float] | None = None
        jd = jd0
        while jd < jd1:
            lon = transit_longitude(b, jd, chart.node_mode)
            inside = next((d for d in pts if float(d.start) <= lon < float(d.end)), None)
            if inside is not None and cur is None:
                cur = (inside, jd)
            elif cur is not None and inside is not cur[0]:
                out.append(DayPass(b, cur[0], cur[1], jd))
                cur = (inside, jd) if inside is not None else None
            jd += step_days
        if cur is not None:
            out.append(DayPass(b, cur[0], cur[1], jd1))
    return tuple(sorted(out, key=lambda p: p.start_jd))


__all__ = ["day_points", "DayPass", "day_fix", 
    "CITATIONS",
    "Fruit",
    "SelectedWindow",
    "Selection",
    "Strong",
    "select",
    "selected_windows",
    "strong_from",
    "strong_significators",
]
