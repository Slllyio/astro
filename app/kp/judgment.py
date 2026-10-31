"""KP judgment: is a matter promised, by the cuspal sub-lord, and when.

The deciding rule (KPR3-SUB-DECIDES, KPR3-CUSP-SUB): a matter of house H is
read from the sub-lord of cusp H (the CSL) and the houses that CSL is a
significator of. For each matter the engine holds a favourable house group
(the houses Krishnamurti names for it) and a denial group, each cited.

Verdict, with no weighing beyond what the source states (ruling R12):

  PROMISED      CSL signifies a favourable house and no denial house
  DENIED        CSL signifies a denial house and no favourable house
  MIXED         CSL signifies both. Reader 3 gives no tie-break; the engine
                does not invent one ("calmly judge", KPR3-CALMLY).
  NOT_SIGNIFIED CSL signifies neither group

Every result lists the fired rules (each signification with its level and
reason) and the citations, and, when the birth time carries an uncertainty
window, how many minutes of that window give the same verdict. A verdict that
flips inside the window is reported as such, never smoothed.

Timing (KPR3-PERIODS, KPR3-DBA-PICK): candidate periods are those whose
dasa, bhukti and antara lords all signify a favourable house. Each window
also says whether any of its lords signifies a denial house.

The engine never takes an outcome as input. Results are deterministic
records, ready for a sealed blind test.

Usage:
    from app.kp.chart import Birth
    from app.kp.judgment import judge, MATTERS
    v = judge(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59,
                    uncertainty_minutes=5), "marriage")
    print(v.to_markdown())
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Final

from app.kp.chart import Birth, KPChart, cast
from app.kp.citations import CITATIONS
from app.kp.dasa import Period, periods_between
from app.kp.significators import Signification, houses_signified, planet_significations

PROMISED: Final = "PROMISED"
DENIED: Final = "DENIED"
MIXED: Final = "MIXED"
NOT_SIGNIFIED: Final = "NOT_SIGNIFIED"


@dataclass(frozen=True, slots=True)
class Matter:
    """A question KP can answer yes/no from one cusp.

    ``status`` is ``"cited"`` when Reader 3 names both groups for this cusp,
    ``"extended"`` when one group is borrowed from a narrower passage (see the
    ruling), ``"general"`` when the groups come from the general principle.
    """

    key: str
    question: str
    cusp: int
    favourable: frozenset[int]
    denial: frozenset[int]
    citations: tuple[str, ...]
    status: str
    ruling: str


def _rel(h: int, *offsets: int) -> frozenset[int]:
    return frozenset(((h - 1 + o) % 12) + 1 for o in offsets)


MATTERS: Final[dict[str, Matter]] = {m.key: m for m in (
    Matter("marriage", "Is marriage promised?", 7,
           frozenset({2, 7, 11}), frozenset({1, 6, 10, 12}),
           ("KPR3-MARRIAGE-HOUSES", "KPR3-H7-DENIAL", "KPR3-CUSP-SUB"), "extended", "R7"),
    Matter("health", "Is good health promised?", 1,
           frozenset({1, 11}), frozenset({6, 8, 12}),
           ("KPR3-HEALTH", "KPR3-ASC-SICK", "KPR3-ASC-11", "KPR3-CUSP-SUB"), "extended", "R13"),
    Matter("wealth", "Is gain of money promised?", 2,
           frozenset({2, 6, 11}), frozenset(),
           ("KPR3-FINANCE-SUB", "KPR3-CUSP-SUB"), "cited", "R14"),
    Matter("service", "Is employment (service) promised?", 10,
           frozenset({2, 6, 10}), frozenset({1, 5, 9}),
           ("KPR3-RETIRE", "KPR3-CUSP-SUB"), "extended", "R15"),
)}


def generic_matter(house: int) -> Matter:
    """General principle for any house H: favourable H, denial 6/8/12 from H (KPR3-6812)."""
    return Matter(f"house{house}", f"Is house {house} favourable?", house,
                  frozenset({house}), _rel(house, 5, 7, 11),
                  ("KPR3-6812", "KPR3-GENERAL", "KPR3-SUB-DECIDES"), "general", "R16")


def _matter(m: str | Matter) -> Matter:
    if isinstance(m, Matter):
        return m
    if m in MATTERS:
        return MATTERS[m]
    if m.startswith("house") and m[5:].isdigit():
        return generic_matter(int(m[5:]))
    raise KeyError(f"unknown matter {m!r}; known: {sorted(MATTERS)} or house1..house12")


def classify(fav_hit: set[int] | frozenset[int], den_hit: set[int] | frozenset[int]) -> str:
    """Ruling R12 verdict from the favourable and denial houses the CSL signifies."""
    if fav_hit and den_hit:
        return MIXED
    if fav_hit:
        return PROMISED
    if den_hit:
        return DENIED
    return NOT_SIGNIFIED


@dataclass(frozen=True, slots=True)
class TimingWindow:
    """A dasa-bhukti-antara whose lords all signify a favourable house."""

    period: Period
    denial_lords: tuple[str, ...]

    def label(self) -> str:
        a, b = self.period.dates()
        flag = f" (also denial via {', '.join(self.denial_lords)})" if self.denial_lords else ""
        return f"{self.period.label()} {a} to {b}{flag}"


@dataclass(frozen=True, slots=True)
class Verdict:
    """The KP answer to one matter for one chart, with everything that produced it."""

    matter: Matter
    verdict: str
    csl: str
    csl_houses: frozenset[int]
    fired: tuple[Signification, ...]
    csl_star_lord: str
    csl_sub_lord: str
    sub_lord_houses: frozenset[int]
    stability: dict[str, int] = field(default_factory=dict)
    window_minutes: float = 0.0
    timing: tuple[TimingWindow, ...] = ()

    @property
    def stable(self) -> bool:
        """True when every minute of the uncertainty window gives the same verdict."""
        return len(self.stability) <= 1

    def to_dict(self) -> dict:
        """Plain record for sealed storage / blind scoring."""
        return {
            "matter": self.matter.key, "cusp": self.matter.cusp, "verdict": self.verdict,
            "csl": self.csl, "csl_houses": sorted(self.csl_houses),
            "favourable_hit": sorted(self.csl_houses & self.matter.favourable),
            "denial_hit": sorted(self.csl_houses & self.matter.denial),
            "fired": [s.explain() for s in self.fired],
            "csl_star_lord": self.csl_star_lord, "csl_sub_lord": self.csl_sub_lord,
            "sub_lord_houses": sorted(self.sub_lord_houses),
            "status": self.matter.status, "ruling": self.matter.ruling,
            "citations": [CITATIONS[c].ref() for c in self.matter.citations],
            "window_minutes": self.window_minutes, "stability": dict(self.stability),
            "stable": self.stable, "timing": [t.label() for t in self.timing],
        }

    def to_markdown(self) -> str:
        """Human-readable reading: verdict, fired rules, citations, stability, timing."""
        m = self.matter
        lines = [
            f"### {m.question}  ->  **{self.verdict}**",
            f"Sub-lord of cusp {m.cusp}: **{self.csl}** (in the star of {self.csl_star_lord}, "
            f"sub of {self.csl_sub_lord}). It signifies houses {sorted(self.csl_houses)}.",
            f"Favourable houses {sorted(m.favourable)}: hit {sorted(self.csl_houses & m.favourable)}. "
            f"Denial houses {sorted(m.denial)}: hit {sorted(self.csl_houses & m.denial)}.",
            "", "Fired rules:",
        ]
        lines += [f"- {s.explain()}" for s in self.fired]
        lines += ["", f"Supplementary (not used in the verdict, KPR3-SUB-DECIDES): the CSL's own "
                      f"sub-lord {self.csl_sub_lord} signifies {sorted(self.sub_lord_houses)}.", "",
                  f"Rule status: {m.status} (ruling {m.ruling}). Citations:"]
        for c in m.citations:
            cit = CITATIONS[c]
            lines.append(f"- {cit.ref()} \"{cit.quote}\"" + (f" [{cit.note}]" if cit.note else ""))
        if self.window_minutes:
            counts = ", ".join(f"{k} {v} min" for k, v in sorted(self.stability.items()))
            lines += ["", f"Birth-time window ±{self.window_minutes:g} min: {counts}. "
                          + ("Stable." if self.stable else "NOT stable: the verdict depends on the exact minute.")]
        if self.timing:
            lines += ["", "Candidate periods (dasa-bhukti-antara lords all signify a favourable house):"]
            lines += [f"- {t.label()}" for t in self.timing]
        return "\n".join(lines)


def _core(chart: KPChart, m: Matter) -> tuple[str, str, frozenset[int], tuple[Signification, ...]]:
    sigs = planet_significations(chart)
    csl = chart.cusp(m.cusp).sub_lord
    houses = houses_signified(chart, csl, sigs)
    fired = tuple(s for s in sigs[csl] if s.house in (m.favourable | m.denial))
    return classify(houses & m.favourable, houses & m.denial), csl, houses, fired


def timing_windows(chart: KPChart, matter: str | Matter, jd0: float, jd1: float) -> tuple[TimingWindow, ...]:
    """Antaras in ``[jd0, jd1)`` whose MD, AD and PD lords all signify a favourable house."""
    m = _matter(matter)
    sigs = planet_significations(chart)
    hs = {p: houses_signified(chart, p, sigs) for p in sigs}
    out = []
    for p in periods_between(chart, jd0, jd1, depth=3):
        if all(hs[l] & m.favourable for l in p.lords):
            out.append(TimingWindow(p, tuple(l for l in dict.fromkeys(p.lords) if hs[l] & m.denial)))
    return tuple(out)


def judge(birth: Birth, matter: str | Matter, *, node_mode: str = "mean",
          timing_years: tuple[float, float] | None = None, step_minutes: float = 1.0) -> Verdict:
    """Judge one matter for one birth.

    Args:
      birth: Birth data; ``uncertainty_minutes`` sets the stability window.
      matter: A key of :data:`MATTERS`, ``"house<N>"``, or a :class:`Matter`.
      node_mode: Passed to :func:`app.kp.chart.cast`.
      timing_years: Optional (from_age, to_age) for candidate periods.
      step_minutes: Step for the stability scan.
    """
    m = _matter(matter)
    chart = cast(birth, node_mode=node_mode)
    verdict, csl, houses, fired = _core(chart, m)
    cpt = chart.planets[csl]
    sub_houses = houses_signified(chart, cpt.sub_lord)

    stability: Counter[str] = Counter()
    w = birth.uncertainty_minutes
    if w:
        n = int(round(w / step_minutes))
        for k in range(-n, n + 1):
            stability[_core(cast(birth.shifted(k * step_minutes), node_mode=node_mode), m)[0]] += 1

    timing: tuple[TimingWindow, ...] = ()
    if timing_years is not None:
        a, b = timing_years
        timing = timing_windows(chart, m, chart.jd_ut + a * 365.2425, chart.jd_ut + b * 365.2425)

    return Verdict(m, verdict, csl, houses, fired, cpt.star_lord, cpt.sub_lord, sub_houses,
                   dict(stability), w, timing)


__all__ = [
    "PROMISED", "DENIED", "MIXED", "NOT_SIGNIFIED", "Matter", "MATTERS", "generic_matter",
    "classify", "TimingWindow", "Verdict", "timing_windows", "judge",
]
