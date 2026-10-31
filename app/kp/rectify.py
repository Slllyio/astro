"""KP birth-time rectification: score candidate minutes against dated life events.

A KP reading turns on the cusp sub-lords, and those change every few minutes of
birth time (the 7th-cusp sub-lord about every 5.9 minutes, docs/kp/KP_PREFLIGHT).
This module searches a window around a stated time, minute by minute, and asks
of each candidate minute two questions per known event, both from Reader 3 rules
the engine already encodes:

  TIMING  (KPR3-PERIODS, KPR3-DBA-PICK, ruling R17) Did the event fall in a
          dasa-bhukti-antara whose lords all signify the event's houses?
          Only levels whose single period covers the event's whole stated date
          interval are scorable: a year-dated event can never claim antara
          evidence (rule RR3 below).
  PROMISE (KPR3-CUSP-SUB, KPR3-SUB-DECIDES, ruling R12) Does the cusp sub-lord of
          the event's cusp allow the event (PROMISED or MIXED; for illness,
          DENIED or MIXED health)?

Rectification rulings (named because Reader 3 states no rectification method):

  RR1  An event scores 1 for a timing match and 1 for a consistent promise. The two are
       added with equal weight. Reader 3 gives no weights; equal is the no-choice choice.
  RR2  Event types and their houses are only those the KP engine already cites
       (KP_EVENT_TYPES). Childbirth uses the general principle (R16, status general).
  RR3  Resolution honesty: a dasa level counts only if one period of that level covers
       the event's whole date interval (day, month or year).
  RR4  Ruling-planet rectification (the lagna sub-lord among the ruling planets at the
       moment of judgment) is NOT encoded. It is not stated in Reader 3, and Readers 1
       and 6, where it would be, are not held.
  RR5  The answer is the set of minutes sharing the top score, reported as intervals,
       never a single minute. When that set covers most of the window the report says
       the events do not discriminate.

The rectified result hands off to the KP engine as a ``Birth`` whose
``uncertainty_minutes`` covers the whole top-scoring set, so the engine's own
stability scan reports every verdict that still depends on the minute.

Events used to rectify a person must never be used to test KP on that person.
:func:`split_events` makes a seeded, deterministic split into a rectification
set and a sealed test set, and :class:`EventLedger` refuses any reuse.

Usage:
    from app.kp.chart import Birth
    from app.kp.rectify import KPEvent, rectify
    birth = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)
    events = [KPEvent("marriage", 2016, 2, 14), KPEvent("service_start", 2012, 7, 1)]
    result = rectify(birth, events, window_minutes=30)
    print(result.to_markdown())
    band = stability_band(birth, 15)  # default hand-off: stated time + which sub-lords hold
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Final, Iterable, Optional, Sequence

import swisseph as swe

from app.kp.chart import Birth, KPChart, cast
from app.kp.citations import CITATIONS
from app.kp.dasa import Period, periods_on
from app.kp.judgment import DENIED, MIXED, PROMISED, MATTERS, Matter, generic_matter
from app.kp.judgment import _core as _judge_core
from app.kp.significators import houses_signified, planet_significations

logger = logging.getLogger(__name__)

_LEVELS: Final[tuple[str, ...]] = ("dasa", "bhukti", "antara")


@dataclass(frozen=True, slots=True)
class KPEventType:
    """One kind of event: the houses its period lords must signify, and its promise test."""

    key: str
    question: str
    houses: frozenset[int]
    contrary: frozenset[int]
    promise_matter: Optional[Matter]
    promise_ok: frozenset[str]
    citations: tuple[str, ...]
    status: str
    ruling: str


KP_EVENT_TYPES: Final[dict[str, KPEventType]] = {t.key: t for t in (
    KPEventType("marriage", "When did the marriage take place?",
                frozenset({2, 7, 11}), frozenset({1, 6, 10, 12}),
                MATTERS["marriage"], frozenset({PROMISED, MIXED}),
                ("KPR3-MARRIAGE-HOUSES", "KPR3-H7-DENIAL", "KPR3-PERIODS", "KPR3-DBA-PICK"),
                "extended", "R7, R17"),
    KPEventType("service_start", "When did employment (service) begin?",
                frozenset({2, 6, 10}), frozenset({1, 5, 9}),
                MATTERS["service"], frozenset({PROMISED, MIXED}),
                ("KPR3-RETIRE", "KPR3-PERIODS", "KPR3-DBA-PICK"), "extended", "R15, R17"),
    KPEventType("service_end", "When did service end (retirement, dismissal, resignation)?",
                frozenset({1, 5, 9}), frozenset({2, 6, 10}),
                None, frozenset(),
                ("KPR3-RETIRE", "KPR3-PERIODS"), "cited", "R15, R17"),
    KPEventType("gain", "When was a significant gain of money?",
                frozenset({2, 6, 11}), frozenset(),
                MATTERS["wealth"], frozenset({PROMISED}),
                ("KPR3-FINANCE-SUB", "KPR3-PERIODS", "KPR3-DBA-PICK"), "cited", "R14, R17"),
    KPEventType("illness", "When was a serious illness or medical procedure?",
                frozenset({6, 8, 12}), frozenset({1, 11}),
                MATTERS["health"], frozenset({DENIED, MIXED}),
                ("KPR3-HEALTH", "KPR3-ASC-SICK", "KPR3-PERIODS"), "extended", "R13, R17"),
    KPEventType("childbirth", "When was a child born?",
                frozenset({5}), frozenset({10, 12, 4}),
                generic_matter(5), frozenset({PROMISED, MIXED}),
                ("KPR3-6812", "KPR3-GENERAL", "KPR3-PERIODS"), "general", "R16, R17"),
)}


def _jd(y: int, m: int, d: int) -> float:
    return swe.julday(y, m, d, 0.0, swe.GREG_CAL)


@dataclass(frozen=True, slots=True)
class KPEvent:
    """A dated life event. ``month``/``day`` may be None when not known."""

    event_type: str
    year: int
    month: Optional[int] = None
    day: Optional[int] = None
    event_id: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        if self.event_type not in KP_EVENT_TYPES:
            raise ValueError(f"unknown KP event type {self.event_type!r}; known: {sorted(KP_EVENT_TYPES)}")
        if self.day is not None and self.month is None:
            raise ValueError("a day-dated event needs its month")

    @property
    def spec(self) -> KPEventType:
        return KP_EVENT_TYPES[self.event_type]

    @property
    def precision(self) -> str:
        return "day" if self.day is not None else ("month" if self.month is not None else "year")

    @property
    def key(self) -> str:
        """Stable identity used by the ledger."""
        if self.event_id:
            return self.event_id
        return f"{self.event_type}:{self.year}-{self.month or 0:02d}-{self.day or 0:02d}"

    def jd_bounds(self) -> tuple[float, float]:
        """UT interval [start, end) covered by the stated precision."""
        if self.day is not None:
            a = _jd(self.year, self.month, self.day)
            return a, a + 1.0
        if self.month is not None:
            a = _jd(self.year, self.month, 1)
            b = _jd(self.year + (self.month == 12), self.month % 12 + 1, 1)
            return a, b
        return _jd(self.year, 1, 1), _jd(self.year + 1, 1, 1)


@dataclass(frozen=True, slots=True)
class EventScore:
    """How one candidate minute explains one event."""

    event: KPEvent
    lords: tuple[str, ...]          # scorable period lords, MD downward
    level_hits: tuple[bool, ...]    # lord signifies the event houses
    timing: bool                    # every scorable level hits (R17)
    promise: Optional[bool]         # None when the type has no promise test
    promise_verdict: str
    csl: str

    @property
    def score(self) -> int:
        return int(self.timing) + int(bool(self.promise))

    def explain(self) -> str:
        sp = self.event.spec
        lv = ", ".join(f"{_LEVELS[i]} {l} {'yes' if h else 'no'}"
                       for i, (l, h) in enumerate(zip(self.lords, self.level_hits)))
        t = (f"timing {'MATCH' if self.timing else 'no match'} "
             f"(lords signifying {sorted(sp.houses)}: {lv or 'no scorable level'})")
        if self.promise is None:
            p = "promise: not tested for this type"
        else:
            p = (f"promise {'consistent' if self.promise else 'inconsistent'} "
                 f"(cusp {sp.promise_matter.cusp} sub-lord {self.csl}: {self.promise_verdict})")
        return f"{self.event.key}: {t}; {p}"


def _scorable_chain(chart: KPChart, ev: KPEvent) -> tuple[Period, ...]:
    """Periods (MD..antara) that cover the event's whole interval (RR3)."""
    a, b = ev.jd_bounds()
    start = periods_on(chart, a, depth=3)
    end = periods_on(chart, b - 1e-6, depth=3)
    out = []
    for p, q in zip(start, end):
        if p.lords != q.lords:
            break
        out.append(p)
    return tuple(out)


def score_event(chart: KPChart, ev: KPEvent, sigs: dict | None = None,
                promise_cache: dict | None = None) -> EventScore:
    """Score one event on one cast chart."""
    sigs = sigs or planet_significations(chart)
    sp = ev.spec
    chain = _scorable_chain(chart, ev)
    lords = chain[-1].lords if chain else ()
    hits = tuple(bool(houses_signified(chart, l, sigs) & sp.houses) for l in lords)
    timing = bool(hits) and all(hits)
    promise: Optional[bool] = None
    verdict, csl = "", ""
    if sp.promise_matter is not None:
        key = sp.promise_matter.key
        if promise_cache is not None and key in promise_cache:
            verdict, csl = promise_cache[key]
        else:
            verdict, csl, _, _ = _judge_core(chart, sp.promise_matter)
            if promise_cache is not None:
                promise_cache[key] = (verdict, csl)
        promise = verdict in sp.promise_ok
    return EventScore(ev, lords, hits, timing, promise, verdict, csl)


@dataclass(frozen=True, slots=True)
class MinuteScore:
    """One candidate minute: offset from the stated time and the score of every event."""

    offset: int
    events: tuple[EventScore, ...]
    cusp_sub_lords: tuple[str, ...]

    @property
    def total(self) -> int:
        return sum(e.score for e in self.events)

    @property
    def timing_total(self) -> int:
        return sum(e.timing for e in self.events)

    @property
    def promise_total(self) -> int:
        return sum(bool(e.promise) for e in self.events)


def score_minute(birth: Birth, offset: int, events: Sequence[KPEvent],
                 node_mode: str = "mean") -> MinuteScore:
    """Cast the chart ``offset`` minutes from ``birth`` and score every event."""
    chart = cast(birth.shifted(offset), node_mode=node_mode)
    sigs = planet_significations(chart)
    cache: dict = {}
    scores = tuple(score_event(chart, e, sigs, cache) for e in events)
    return MinuteScore(offset, scores, tuple(c.sub_lord for c in chart.cusps))


def _runs(offsets: Iterable[int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for o in sorted(offsets):
        if out and o == out[-1][1] + 1:
            out[-1] = (out[-1][0], o)
        else:
            out.append((o, o))
    return out


@dataclass(frozen=True)
class RectificationResult:
    """Every minute's score, the top-scoring intervals, and the honesty notes."""

    birth: Birth
    window_minutes: int
    minutes: tuple[MinuteScore, ...]
    events: tuple[KPEvent, ...]
    notes: tuple[str, ...] = field(default=())

    @property
    def best_total(self) -> int:
        return max(m.total for m in self.minutes)

    @property
    def top_offsets(self) -> tuple[int, ...]:
        b = self.best_total
        return tuple(m.offset for m in self.minutes if m.total == b)

    @property
    def top_intervals(self) -> list[tuple[int, int]]:
        return _runs(self.top_offsets)

    @property
    def top_share(self) -> float:
        """Fraction of the window tied at the top score: the chance hit rate."""
        return len(self.top_offsets) / len(self.minutes)

    @property
    def runner_up_total(self) -> Optional[int]:
        rest = sorted({m.total for m in self.minutes}, reverse=True)
        return rest[1] if len(rest) > 1 else None

    def score_at(self, offset: int) -> MinuteScore:
        return next(m for m in self.minutes if m.offset == offset)

    def percentile_rank(self, offset: int) -> float:
        """Rank of a minute among all minutes, 0 = best, 1 = worst, ties at mid-rank."""
        s = self.score_at(offset).total
        better = sum(m.total > s for m in self.minutes)
        ties = sum(m.total == s for m in self.minutes) - 1
        n = len(self.minutes) - 1
        return (better + 0.5 * ties) / n if n else 0.5

    def kp_birth(self) -> Birth:
        """The rectified birth: centre of the top set, window covering all of it.

        UNVALIDATED (T1 could not be run, docs/kp/RECTIFICATION_T1_RESULTS.md). Per the user's
        decision of 2026-10-31 the KP engine keeps the STATED time and reads
        :func:`stability_band` instead; this hand-off is shown beside it, never in its place.
        """
        lo, hi = min(self.top_offsets), max(self.top_offsets)
        mid = (lo + hi) / 2
        b = self.birth.shifted(mid)
        return Birth(b.year, b.month, b.day, b.hour, b.minute, b.tz, b.lat, b.lon,
                     second=b.second, uncertainty_minutes=max(1.0, (hi - lo) / 2),
                     label=(self.birth.label + " (KP-rectified)").strip())

    def stable_cusps(self) -> dict[int, Optional[str]]:
        """Cusp -> its sub-lord if the same over every top minute, else None."""
        tops = [m for m in self.minutes if m.total == self.best_total]
        out: dict[int, Optional[str]] = {}
        for i in range(12):
            subs = {m.cusp_sub_lords[i] for m in tops}
            out[i + 1] = subs.pop() if len(subs) == 1 else None
        return out

    def to_dict(self) -> dict:
        best = self.score_at(self.top_offsets[0])
        kb = self.kp_birth()
        return {
            "stated": f"{self.birth.year:04d}-{self.birth.month:02d}-{self.birth.day:02d} "
                      f"{self.birth.hour:02d}:{self.birth.minute:02d}",
            "window_minutes": self.window_minutes, "n_events": len(self.events),
            "best_total": self.best_total, "max_possible": sum(
                1 + (e.spec.promise_matter is not None) for e in self.events),
            "runner_up_total": self.runner_up_total,
            "top_intervals_offset_min": self.top_intervals, "top_share": round(self.top_share, 3),
            "kp_birth": {"time": f"{kb.hour:02d}:{kb.minute:02d}:{kb.second:04.1f}",
                         "date": f"{kb.year:04d}-{kb.month:02d}-{kb.day:02d}",
                         "uncertainty_minutes": kb.uncertainty_minutes},
            "stable_cusp_sub_lords": self.stable_cusps(),
            "fired_at_first_top_minute": [e.explain() for e in best.events],
            "citations": sorted({CITATIONS[c].ref() for e in self.events for c in e.spec.citations}),
            "notes": list(self.notes),
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        L = [f"## KP rectification of {d['stated']} (±{self.window_minutes} min, {d['n_events']} events)", "",
             f"Top score {d['best_total']} of {d['max_possible']} (runner-up {d['runner_up_total']}).",
             "Top-scoring minutes (offset from stated time): "
             + ", ".join(f"{a:+d}..{b:+d}" if a != b else f"{a:+d}" for a, b in self.top_intervals)
             + f". They cover {d['top_share']:.0%} of the window, so a random minute would land "
               f"there {d['top_share']:.0%} of the time.",
             f"Hand-off to the KP engine: {d['kp_birth']['date']} {d['kp_birth']['time']} "
             f"±{d['kp_birth']['uncertainty_minutes']:g} min.", "",
             "Cusp sub-lords across the top set: " + ", ".join(
                 f"{h}:{s or 'CHANGES'}" for h, s in d["stable_cusp_sub_lords"].items()), "",
             "Rules fired at the first top minute:"]
        L += [f"- {x}" for x in d["fired_at_first_top_minute"]]
        L += ["", "Citations:"]
        seen = set()
        for e in self.events:
            for c in e.spec.citations:
                if c not in seen:
                    seen.add(c)
                    L.append(f"- {CITATIONS[c].ref()} \"{CITATIONS[c].quote}\"")
        if self.notes:
            L += ["", "Notes:"] + [f"- {n}" for n in self.notes]
        return "\n".join(L)


def rectify(birth: Birth, events: Sequence[KPEvent], *, window_minutes: int = 30,
            node_mode: str = "mean", ledger: "EventLedger | None" = None,
            person: str = "") -> RectificationResult:
    """Score every minute in ``birth`` ± ``window_minutes`` against ``events``.

    If a ledger is given, the events are recorded as used for rectification of
    ``person`` and become ineligible for any KP test on that person.
    """
    if not events:
        raise ValueError("rectification needs at least one dated event")
    if ledger is not None:
        ledger.record_rectification(person, events)
    minutes = []
    for k in range(-window_minutes, window_minutes + 1):
        minutes.append(score_minute(birth, k, events, node_mode))
    notes = []
    if len(events) < 3:
        notes.append(f"Only {len(events)} event(s): many minutes will tie. Three or more day-dated events are needed.")
    if sum(e.precision == "day" for e in events) == 0:
        notes.append("No day-dated event: antara-level evidence is unavailable (RR3), so resolution is coarse.")
    res = RectificationResult(birth, window_minutes, tuple(minutes), tuple(events))
    if len(res.top_intervals) > 1:
        notes.append(f"The top score is split over {len(res.top_intervals)} separate intervals; the hand-off "
                     "window spans all of them.")
    if res.top_share > 0.5:
        notes.append(f"The top score covers {res.top_share:.0%} of the window: these events do not pick out a time.")
    notes.append("Not validated: the real-data recovery test could not be run (no people qualified, "
                 "docs/kp/RECTIFICATION_T1_RESULTS.md). Use the stated time and stability_band() for KP "
                 "readings; this result is shown beside it, not in its place.")
    return RectificationResult(birth, window_minutes, tuple(minutes), tuple(events), tuple(notes))


# --- the event split: rectification set vs sealed test set ------------------

SPLIT_SALT: Final[str] = "kp-rect-split-v1"


def split_events(person: str, events: Sequence[KPEvent], *, rect_fraction: float = 0.5,
                 salt: str = SPLIT_SALT) -> tuple[tuple[KPEvent, ...], tuple[KPEvent, ...]]:
    """Seeded, order-independent split of one person's events into (rectification, sealed).

    Each event's place is fixed by sha256(salt|person|event key), so adding the person's
    other events later never moves an event across the line. At least one event is sealed
    whenever the person has two or more.
    """
    def h(e: KPEvent) -> str:
        return hashlib.sha256(f"{salt}|{person}|{e.key}".encode()).hexdigest()
    ranked = sorted(events, key=h)
    n_rect = int(round(len(ranked) * rect_fraction))
    if len(ranked) >= 2:
        n_rect = min(max(n_rect, 1), len(ranked) - 1)
    return tuple(ranked[:n_rect]), tuple(ranked[n_rect:])


class ReuseError(RuntimeError):
    """An event used to rectify a person was offered as a test of KP on that person."""


@dataclass
class EventLedger:
    """Records which events rectified which person, and refuses to let them test KP."""

    used: dict[str, set[str]] = field(default_factory=dict)

    def record_rectification(self, person: str, events: Iterable[KPEvent]) -> None:
        self.used.setdefault(person, set()).update(e.key for e in events)

    def check_test(self, person: str, events: Iterable[KPEvent]) -> None:
        """Raise ReuseError if any event already rectified this person."""
        bad = sorted(self.used.get(person, set()) & {e.key for e in events})
        if bad:
            raise ReuseError(f"{person}: events {bad} were used to rectify this birth time "
                             "and cannot test KP on the same person")

    def to_dict(self) -> dict:
        return {p: sorted(v) for p, v in sorted(self.used.items())}

    @classmethod
    def from_dict(cls, d: dict) -> "EventLedger":
        return cls({p: set(v) for p, v in d.items()})


# --- the stability band (the default hand-off while rectification is unmeasured) ---

@dataclass(frozen=True, slots=True)
class SubLordRun:
    """One cusp's sub-lord over a contiguous span of the window (offsets in minutes)."""

    cusp: int
    sub_lord: str
    start: int
    end: int


@dataclass(frozen=True)
class StabilityBand:
    """Which cusp sub-lords hold across the stated time's uncertainty window, and which flip."""

    birth: Birth
    window_minutes: int
    runs: tuple[SubLordRun, ...]

    def cusp_runs(self, cusp: int) -> tuple[SubLordRun, ...]:
        return tuple(r for r in self.runs if r.cusp == cusp)

    def stable(self, cusp: int) -> Optional[str]:
        """The cusp's sub-lord if it is the same over the whole window, else None."""
        rs = self.cusp_runs(cusp)
        return rs[0].sub_lord if len(rs) == 1 else None

    @property
    def stable_cusps(self) -> tuple[int, ...]:
        return tuple(c for c in range(1, 13) if self.stable(c))

    def to_dict(self) -> dict:
        return {
            "stated": f"{self.birth.year:04d}-{self.birth.month:02d}-{self.birth.day:02d} "
                      f"{self.birth.hour:02d}:{self.birth.minute:02d}",
            "window_minutes": self.window_minutes,
            "stable_cusps": {c: self.stable(c) for c in self.stable_cusps},
            "flipping_cusps": {c: [(r.sub_lord, r.start, r.end) for r in self.cusp_runs(c)]
                               for c in range(1, 13) if not self.stable(c)},
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        L = [f"## Cusp sub-lord stability for {d['stated']} ±{self.window_minutes} min", "",
             "The KP engine uses the stated time. Only readings that rest on a stable cusp sub-lord "
             "hold whatever the exact minute.", "",
             "| cusp | sub-lord over the window |", "|---|---|"]
        for c in range(1, 13):
            rs = self.cusp_runs(c)
            if len(rs) == 1:
                L.append(f"| {c} | {rs[0].sub_lord} (stable) |")
            else:
                L.append(f"| {c} | " + "; ".join(f"{r.sub_lord} {r.start:+d}..{r.end:+d}" for r in rs)
                         + " (CHANGES) |")
        return "\n".join(L)


def stability_band(birth: Birth, window_minutes: float | None = None, *,
                   node_mode: str = "mean") -> StabilityBand:
    """Cusp sub-lords minute by minute across ``birth`` ± window (default: its uncertainty_minutes)."""
    w = int(round(window_minutes if window_minutes is not None else birth.uncertainty_minutes))
    subs = [tuple(c.sub_lord for c in cast(birth.shifted(k), node_mode=node_mode).cusps)
            for k in range(-w, w + 1)]
    runs: list[SubLordRun] = []
    for i in range(12):
        start = -w
        for k in range(1, len(subs) + 1):
            if k == len(subs) or subs[k][i] != subs[k - 1][i]:
                runs.append(SubLordRun(i + 1, subs[k - 1][i], start, k - 1 - w))
                start = k - w
    return StabilityBand(birth, w, tuple(runs))


__all__ = [
    "KPEventType", "KP_EVENT_TYPES", "KPEvent", "EventScore", "score_event", "MinuteScore",
    "score_minute", "RectificationResult", "rectify", "SPLIT_SALT", "split_events",
    "ReuseError", "EventLedger", "SubLordRun", "StabilityBand", "stability_band",
]
