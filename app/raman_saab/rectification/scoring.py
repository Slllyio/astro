"""Rectification scoring — how well one candidate chart explains the evidence.

Three channels, subtotals ALWAYS visible (never one opaque number):

* **Channel A — event-daśā LORD fit** (primary). Per event, resolve the running
  (Mahadasha, Bhukti, Pratyantar) at the event date and test each lord against the
  event's fructification significators: ``timer_set(house)`` (HTJAH-I:1586-1596 — lord /
  aspecters / occupants / lord-from-Moon / karaka) unioned over the event's aux houses,
  plus the event-type karakas Raman names (e.g. Venus+Moon for marriage, AFB-9:98).
  Level weights: the Bhukti is the trigger (W_AD > W_MD, HTJAH-II:668-702), the
  Pratyantar refines. A level is SCORABLE only when ONE period of that level covers the
  event's whole stated-precision interval — a year-grade event can never claim
  Pratyantar-level evidence (resolution honesty, enforced here).

* **Channel B — HOUSE-ACTIVATION fit** (co-primary). Per event, compute
  ``active_houses(chart, jd)`` — the houses the running MD/AD lords activate per the
  Time-of-Fructification doctrine (HTJAH-II:680-694: both lords time the house ->
  "par excellence"; one -> "limited") — and grade whether the event's house is lit:
  par_excellence +1.0, limited +0.5, absent -> penalty. The full lit-house panel is
  carried on the score for display.

* **Natal-fact channel** (Tier-F only). ``judge_house`` verdict vs the observed fact:
  exact +1, one-off 0, opposite -1. A Shadbala-less light chart reaching this scorer is
  a programming error -> ValueError (the tier guard).

Relative-death events consult the maraka apparatus (HTJAH-I:770-795) **rotated to the
relative's frame**, per Raman's worked usage — "Mars ... not only owns the second and
seventh Maraka but is actually situated in the second from Matru-Karaka"
(HTJAH-I:4479-4481): the primary bonus needs a running lord that is a maraka FROM THE
EVENT'S BHAVA (lord/occupant of its 2nd or 7th); the native-lagna maraka set is the
secondary tier. (Doctrine-gate finding: a lagna-framed overlay alone would be a bug.)

Usage:
    from app.raman_saab.rectification import scoring
    cs = scoring.score_candidate(cand, cache, events, facts, include_facts=False)
    cs.channels.event_lords, cs.channels.event_houses, cs.channels.total
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, Optional

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.house_template import judge_house
from app.raman_saab.primitives import vimshottari as vim
from app.raman_saab.rectification.arithmetic import ArithmeticScore, arithmetic_score
from app.raman_saab.rectification.candidates import CandidateChart, ChartCache
from app.raman_saab.rectification.events import LifeEvent, NatalFact

Level = Literal["maha", "antar", "pratyantar"]

# Channel-A level weights: the Bhukti triggers (HTJAH-II:668-702), MD contextualises,
# the Pratyantar refines.
W_MD: Final[float] = 1.0
W_AD: Final[float] = 1.5
W_PD: Final[float] = 0.75
#: Channel-A penalty when NO scorable level's lord is a significator, scaled by the
#: event's date precision (a vague year hurts less than a pinpointed day).
NO_MATCH_PENALTY: Final[float] = -1.0
_PRECISION_FACTOR: Final[dict[str, float]] = {"day": 1.0, "month": 0.75, "year": 0.5}
# Channel-B grades (HTJAH-II:680-694) + absent penalty.
ACTIVE_PAR: Final[float] = 1.0
ACTIVE_LIMITED: Final[float] = 0.5
ACTIVE_ABSENT_PENALTY: Final[float] = -0.5
# Maraka overlay for relative-death events (HTJAH-I:770-795).
MARAKA_BONUS_STRONG: Final[float] = 0.5
MARAKA_BONUS_ANY: Final[float] = 0.25
# Fact-channel agreement values.
_OPPOSITES: Final[frozenset[frozenset[str]]] = frozenset(
    {frozenset({"favourable", "afflicted"})})


@dataclass(frozen=True)
class LevelMatch:
    level: Level
    lord: Optional[str]
    matched: bool
    scorable: bool
    weight: float


@dataclass(frozen=True)
class EventScore:
    """One (candidate, event) fit — channel A + channel B parts kept separate."""
    event_index: int
    event_type: str
    house: int
    levels: tuple[LevelMatch, ...]
    active_grade: Optional[str]              # par_excellence | limited | absent | None(unscorable)
    active_panel: tuple[str, ...]            # e.g. ("H2:par_excellence", "H11:limited")
    maraka_bonus: float
    penalty: float
    lords_part: float                        # weighted channel-A contribution
    houses_part: float                       # weighted channel-B contribution
    notes: tuple[str, ...]

    @property
    def subtotal(self) -> float:
        return self.lords_part + self.houses_part


@dataclass(frozen=True)
class FactScore:
    fact_index: int
    subject: str
    engine_verdict: Optional[str]
    engine_degree: Optional[str]             # reported, never scored (v1)
    agreement: float
    subtotal: float
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChannelScores:
    """Per-channel subtotals; the report renders these, never only the total."""
    event_lords: float
    event_houses: float
    facts: float
    arithmetic: float

    @property
    def total(self) -> float:
        return self.event_lords + self.event_houses + self.facts + self.arithmetic


@dataclass(frozen=True)
class CandidateScore:
    candidate: CandidateChart
    event_scores: tuple[EventScore, ...]
    fact_scores: tuple[FactScore, ...]
    arithmetic_detail: Optional[ArithmeticScore]
    channels: ChannelScores


def timer_union_for_spec(chart: RamanChart, spec) -> frozenset[str]:
    """timer_set over an EventSpec's house + aux houses, plus its named karakas.
    Public: the suggester scores HYPOTHETICAL event types with it."""
    timers = set(vim.timer_set(chart, spec.house))
    for h in spec.aux_houses:
        timers |= vim.timer_set(chart, h)
    timers |= set(spec.karakas)
    return frozenset(timers)


def _timer_union(chart: RamanChart, event: LifeEvent) -> frozenset[str]:
    return timer_union_for_spec(chart, event.spec)


def _relative_marakas(chart: RamanChart, house: int) -> frozenset[str]:
    """Maraka grahas FROM the relative's bhava (frame rotation, HTJAH-I:4479-4481):
    the lords of, and occupants of, the 2nd and 7th counted from ``house``."""
    from app.raman_saab.chart.constants import SIGN_LORDS
    out: set[str] = set()
    for offset in (1, 6):                                    # 2nd and 7th from the bhava
        rel_house = ((house - 1) + offset) % 12 + 1
        rel_sign = ((chart.asc_sign - 1) + (rel_house - 1)) % 12 + 1
        out.add(SIGN_LORDS[rel_sign])
        out.update(n for n, p in chart.planets.items() if p.rasi_house == rel_house)
    return frozenset(out)


def _covers(period, lo: float, hi: float) -> bool:
    return period is not None and period.start_jd <= lo and hi <= period.end_jd


def score_event(chart: RamanChart, event: LifeEvent, index: int = 0) -> EventScore:
    """Channels A + B for one event against one (Tier-L) candidate chart."""
    spec = event.spec
    lo, hi = event.jd_bounds()
    jp = event.jd_point()
    pf = _PRECISION_FACTOR[event.precision]
    timers = _timer_union(chart, event)
    notes: list[str] = []

    # ── resolve the three levels at the event instant ─────────────────────────
    md_period = next((p for p in vim.mahadasha_timeline(chart) if p.contains(jp)), None)
    ad_period = vim.dasha_on(chart, jp)
    pd_period = vim.pratyantar_on(chart, jp)
    levels: list[LevelMatch] = []
    for level, period, lord, weight in (
            ("maha", md_period, md_period.maha if md_period else None, W_MD),
            ("antar", ad_period,
             ad_period.antar if ad_period and ad_period.antar else None, W_AD),
            ("pratyantar", pd_period,
             pd_period.pratyantar if pd_period and pd_period.pratyantar else None, W_PD)):
        scorable = lord is not None and _covers(period, lo, hi)
        if lord is not None and not scorable:
            notes.append(f"{level} unresolvable at {event.precision} precision")
        levels.append(LevelMatch(level=level, lord=lord,
                                 matched=(lord in timers if lord else False),
                                 scorable=scorable, weight=weight))

    lords_raw = sum(lm.weight for lm in levels if lm.matched and lm.scorable)
    penalty = 0.0
    if not any(lm.matched and lm.scorable for lm in levels):
        penalty = NO_MATCH_PENALTY * pf
        notes.append("no scorable period lord is a significator (negative evidence)")

    # ── maraka overlay (relative-death events), ROTATED to the relative's frame ──
    # Primary (+0.5): a scorable running lord is a maraka FROM THE EVENT'S BHAVA —
    # lord/occupant of its 2nd or 7th (HTJAH-I:4479-4481 worked usage). Secondary
    # (+0.25): the period is a native-lagna maraka period (HTJAH-I:770-795).
    maraka_bonus = 0.0
    if spec.maraka_overlay:
        rel = _relative_marakas(chart, spec.house)
        running = {lm.lord for lm in levels if lm.scorable and lm.lord}
        if running & rel:
            maraka_bonus = MARAKA_BONUS_STRONG
        elif vim.is_maraka_period(chart, jp, strength="any"):
            maraka_bonus = MARAKA_BONUS_ANY

    # ── channel B: house activation (AD-resolution -> AD scorability gates it) ─
    ad_scorable = any(lm.level == "antar" and lm.scorable for lm in levels)
    active_grade: Optional[str] = None
    houses_raw = 0.0
    panel: tuple[str, ...] = ()
    if ad_scorable:
        actives = vim.active_houses(chart, jp)
        panel = tuple(f"H{a.house}:{a.grade}" for a in actives)
        by_house = {a.house: a.grade for a in actives}
        grades = [by_house.get(h) for h in (spec.house, *spec.aux_houses)]
        if "par_excellence" in grades:
            active_grade, houses_raw = "par_excellence", ACTIVE_PAR
        elif "limited" in grades:
            active_grade, houses_raw = "limited", ACTIVE_LIMITED
        else:
            active_grade, houses_raw = "absent", ACTIVE_ABSENT_PENALTY * pf
            notes.append(f"H{spec.house} not among the period's active houses")
    else:
        notes.append("house-activation unscorable at this precision")

    return EventScore(
        event_index=index, event_type=event.event_type, house=spec.house,
        levels=tuple(levels), active_grade=active_grade, active_panel=panel,
        maraka_bonus=maraka_bonus, penalty=penalty,
        lords_part=(lords_raw + maraka_bonus + penalty) * event.weight,
        houses_part=houses_raw * event.weight,
        notes=tuple(notes))


def score_fact(chart: RamanChart, fact: NatalFact, index: int = 0) -> FactScore:
    """Natal-fact agreement on a FULL (Tier-F) chart. Raises on a light chart."""
    # Tier guard: the seven visible grahas must carry Shadbala (nodes never do, even on
    # a full cast — compute_shadbala covers Sun..Saturn only).
    if any(chart.planets[g].shadbala_rupas is None
           for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
           if g in chart.planets):
        raise ValueError(
            "score_fact needs a Tier-F (full-cast) chart — a Shadbala-less light chart "
            "would silently degrade judge_house verdicts")
    pf = judge_house(chart, fact.house)
    sv = next((s for s in pf.significations if s.signification == fact.subject), None)
    if sv is None:
        return FactScore(index, fact.subject, None, None, 0.0,
                         0.0, (f"signification {fact.subject!r} not judged",))
    if sv.verdict == "insufficient-evidence":
        return FactScore(index, fact.subject, sv.verdict, sv.degree, 0.0, 0.0,
                         ("engine returned insufficient-evidence (not penalised)",))
    if sv.verdict == fact.observed:
        agreement = 1.0
    elif frozenset({sv.verdict, fact.observed}) in _OPPOSITES:
        agreement = -1.0
    else:
        agreement = 0.0
    return FactScore(index, fact.subject, sv.verdict, sv.degree, agreement,
                     agreement * fact.weight)


def score_candidate(
    cand: CandidateChart, cache: ChartCache,
    events: tuple[LifeEvent, ...], facts: tuple[NatalFact, ...] = (),
    *, include_facts: bool = False, include_arithmetic: bool = True,
) -> CandidateScore:
    """All channels for one candidate. Facts (Tier-F, expensive) only when asked —
    the session runs them on the surviving top-K, never the whole class list."""
    chart_l = cache.light(cand)
    event_scores = tuple(score_event(chart_l, ev, i) for i, ev in enumerate(events))
    arith = arithmetic_score(chart_l, cand.birth) if include_arithmetic else None
    fact_scores: tuple[FactScore, ...] = ()
    if include_facts and facts:
        chart_f = cache.full(cand)
        fact_scores = tuple(score_fact(chart_f, f, i) for i, f in enumerate(facts))
    channels = ChannelScores(
        event_lords=sum(es.lords_part for es in event_scores),
        event_houses=sum(es.houses_part for es in event_scores),
        facts=sum(fs.subtotal for fs in fact_scores),
        arithmetic=arith.subtotal if arith else 0.0)
    return CandidateScore(candidate=cand, event_scores=event_scores,
                          fact_scores=fact_scores, arithmetic_detail=arith,
                          channels=channels)
