"""KP event timing: when do the significators of an event's houses run together?

Reader 3 names, for many events, the houses whose significators must run
"conjointly" (dasa, bhukti and antara lords) for the event to happen. Most of
these come with no cusp and no denial group, so they are timing rules, not
promise verdicts (those live in :mod:`app.kp.judgment`). Ruling R19.

Each :class:`Event` holds:

* ``houses``  the house group; a period is a candidate when its dasa, bhukti
  and antara lords each signify at least one of these houses (as ruling R17).
* ``confirm`` optional extra houses Krishnamurti names as a condition on the
  same significators (e.g. 3 and 9 for engagement). Each window reports which
  lords also signify a confirming house; windows are never dropped for it.
* ``citations`` the verbatim passages (``app.kp.citations``).

Longevity and maraka timing (houses 1, 8, 3 against 2, 7, 12) are
deliberately NOT encoded (ruling R20).

Usage:
    from app.kp.chart import Birth, cast
    from app.kp.events import EVENTS, event_windows
    chart = cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))
    for w in event_windows(chart, "transfer", from_age=20, to_age=40):
        print(w.label())
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kp.chart import KPChart
from app.kp.citations import CITATIONS
from app.kp.dasa import Period, periods_between
from app.kp.significators import houses_signified, planet_significations

YEAR: Final = 365.2425


@dataclass(frozen=True, slots=True)
class Event:
    """An event Reader 3 times by the conjoined periods of a house group's significators."""

    key: str
    label: str
    houses: frozenset[int]
    citations: tuple[str, ...]
    confirm: frozenset[int] = frozenset()


def _e(key: str, label: str, houses: set[int], cites: tuple[str, ...], confirm: set[int] = frozenset()) -> Event:
    return Event(key, label, frozenset(houses), cites, frozenset(confirm))


EVENTS: Final[dict[str, Event]] = {e.key: e for e in (
    _e("marriage", "Marriage", {2, 7, 11}, ("KPR3-ENGAGEMENT", "KPR4-PROMISE")),
    _e("engagement", "Engagement of marriage", {2, 7, 11}, ("KPR3-ENGAGEMENT",), {3, 9}),
    _e("childbirth", "Birth of a child", {2, 5, 11}, ("KPR4-CHILD-HOUSES", "KPR3-CHILD")),
    _e("service_start", "Getting employment", {2, 6, 10}, ("KPR3-RETIRE",)),
    _e("service_end", "End of service or retirement", {1, 5, 9}, ("KPR3-RETIRE",)),
    _e("business", "Business", {2, 7, 10}, ("KPR3-BUSINESS-HOUSES",)),
    _e("money", "Making money", {2, 10, 11}, ("KPR3-MONEY",)),
    _e("building", "Owning a building", {4, 11, 12}, ("KPR3-BUILDING",)),
    _e("disposal", "Disposal of property", {3, 5, 10}, ("KPR3-DISPOSAL",)),
    _e("study", "School and college studies", {4, 11}, ("KPR3-STUDY",)),
    _e("study_abroad", "Research or study away from home", {9, 12}, ("KPR3-STUDY",), {11}),
    _e("scholarship", "Scholarship", {6, 11}, ("KPR3-SCHOLARSHIP",)),
    _e("transfer", "Transfer or change of residence", {3, 9, 12}, ("KPR3-TRANSFER",), {6, 10}),
    _e("deputation", "Deputation with higher pay", {5, 9, 11}, ("KPR3-DEPUTATION",), {12}),
    _e("overseas", "Living overseas", {12}, ("KPR3-OVERSEAS",), {3, 9}),
    _e("regain_position", "Regaining one's position", {10, 11}, ("KPR3-REGAIN",)),
    _e("confinement", "Imprisonment", {3, 8, 12}, ("KPR3-CONFINEMENT",)),
)}


@dataclass(frozen=True, slots=True)
class EventWindow:
    """A dasa-bhukti-antara whose three lords all signify the event's houses."""

    event: Event
    period: Period
    confirmed_by: tuple[str, ...]

    def label(self) -> str:
        a, b = self.period.dates()
        c = ""
        if self.event.confirm:
            c = (f" (confirming houses {sorted(self.event.confirm)} via {', '.join(self.confirmed_by)})"
                 if self.confirmed_by else f" (no lord signifies {sorted(self.event.confirm)})")
        return f"{self.period.label()} {a} to {b}{c}"

    def to_dict(self) -> dict:
        a, b = self.period.dates()
        return {"event": self.event.key, "lords": list(self.period.lords), "from": a, "to": b,
                "confirmed_by": list(self.confirmed_by)}


def event_windows(chart: KPChart, event: str | Event, *, from_age: float, to_age: float) -> tuple[EventWindow, ...]:
    """Candidate periods between two ages for one event (ruling R19)."""
    e = EVENTS[event] if isinstance(event, str) else event
    sigs = planet_significations(chart)
    hs = {p: houses_signified(chart, p, sigs) for p in sigs}
    j0, j1 = chart.jd_ut + from_age * YEAR, chart.jd_ut + to_age * YEAR
    out = []
    for p in periods_between(chart, j0, j1, depth=3):
        if all(hs[l] & e.houses for l in p.lords):
            conf = tuple(l for l in dict.fromkeys(p.lords) if hs[l] & e.confirm)
            out.append(EventWindow(e, p, conf))
    return tuple(out)


def coverage(windows: tuple[EventWindow, ...], from_jd: float, to_jd: float) -> float:
    """Share of ``[from_jd, to_jd)`` covered by the windows: the chance rate of a hit."""
    tot = sum(max(0.0, min(w.period.end_jd, to_jd) - max(w.period.start_jd, from_jd)) for w in windows)
    return tot / (to_jd - from_jd)


def citations_for(event: str) -> list[str]:
    """``source:lines "quote"`` strings for one event."""
    return [f'{CITATIONS[c].ref()} "{CITATIONS[c].quote}"' for c in EVENTS[event].citations]


__all__ = ["Event", "EVENTS", "EventWindow", "event_windows", "coverage", "citations_for"]
