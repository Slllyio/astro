"""Rectification report — ranked candidates with HONEST framing.

Rendering rules (enforced by construction, not convention):
  * the winner is always printed as its CLASS INTERVAL, never a point time;
  * the ``resolution_statement`` is COMPUTED from the evidence precisions present
    (year-grade events resolve ayanamsa + hour-scale classes; a day-grade event
    ~10-minute classes; facts alone only the lagna/navamsa class);
  * channel subtotals (lords / houses / facts / arithmetic) are always visible;
  * the per-event matrix renders the two ayanamsa tracks SIDE-BY-SIDE, each cell
    carrying the (MD, AD, PD) lords, the match marks, and the house-activation grade;
  * a dedicated ayanamsa-verdict section names the winner, the margin, and WHICH
    events drove the separation (dual-ayanamsa analysis is mandatory, per user lock).

Usage:
    from app.raman_saab.rectification.report import build_report, to_text
    rep = build_report(mode="rectify", scored=scored, events=events, facts=facts)
    print(to_text(rep))
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.raman_saab.rectification.events import LifeEvent, NatalFact
from app.raman_saab.rectification.scoring import CandidateScore

_CONF_CLEAR: float = 1.5
_CONF_LEAN: float = 0.5


@dataclass(frozen=True)
class AyanamsaVerdict:
    winner: Optional[str]                 # "raman" | "lahiri" | None (tie / one-track)
    margin: float                         # best(winner) - best(runner-up), total score
    best_by_ayanamsa: tuple[tuple[str, str, float], ...]   # (ayanamsa, time_str, total)
    driving_events: tuple[str, ...]       # events whose match differs between the bests
    statement: str


@dataclass(frozen=True)
class ConfidenceStatement:
    margin_top2: float
    n_surviving: int
    wording: str


@dataclass(frozen=True)
class RectificationReport:
    mode: str
    n_candidates: int
    ranked: tuple[CandidateScore, ...]    # top-K, descending total
    events: tuple[LifeEvent, ...]
    facts: tuple[NatalFact, ...]
    ayanamsa_verdict: AyanamsaVerdict
    resolution_statement: str
    confidence: ConfidenceStatement
    discriminators: tuple[str, ...] = ()  # wired by the suggester phase
    flat_events: tuple[str, ...] = ()
    correlated_pairs: tuple[tuple[str, str], ...] = ()
    suggestions: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def _event_match_vector(cs: CandidateScore) -> tuple[bool, ...]:
    """Per-event 'any scorable level matched' — the basic discrimination signature."""
    return tuple(any(lm.matched and lm.scorable for lm in es.levels)
                 for es in cs.event_scores)


def _ayanamsa_verdict(scored: tuple[CandidateScore, ...],
                      events: tuple[LifeEvent, ...]) -> AyanamsaVerdict:
    best: dict[str, CandidateScore] = {}
    for cs in scored:
        ay = cs.candidate.ayanamsa
        if ay not in best or cs.channels.total > best[ay].channels.total:
            best[ay] = cs
    rows = tuple(sorted(((ay, cs.candidate.time_str, cs.channels.total)
                         for ay, cs in best.items()),
                        key=lambda r: r[2], reverse=True))
    if len(rows) < 2:
        ay = rows[0][0] if rows else None
        return AyanamsaVerdict(ay, 0.0, rows, (),
                               "single-ayanamsa run — no cross-frame verdict")
    margin = rows[0][2] - rows[1][2]
    va, vb = _event_match_vector(best[rows[0][0]]), _event_match_vector(best[rows[1][0]])
    driving = tuple(events[i].event_type for i in range(min(len(va), len(vb)))
                    if va[i] != vb[i])
    if margin < 1e-9:
        stmt = "the two ayanamsas tie on this evidence — supply a discriminating event"
        winner = None
    else:
        drv = ", ".join(driving) if driving else "aggregate score only (no single event flips)"
        stmt = (f"{rows[0][0]} leads {rows[1][0]} by {margin:+.2f}; driven by: {drv}")
        winner = rows[0][0]
    return AyanamsaVerdict(winner, margin, rows, driving, stmt)


def _resolution_statement(events: tuple[LifeEvent, ...],
                          facts: tuple[NatalFact, ...],
                          top: Optional[CandidateScore]) -> str:
    precisions = {ev.precision for ev in events}
    if "day" in precisions:
        claim = "day-grade events present: class resolution down to ~minutes is claimable"
    elif "month" in precisions:
        claim = "month-grade events: hour-scale classes + the ayanamsa are resolvable"
    elif precisions:
        claim = ("year-grade events only: the ayanamsa and hour-scale classes are "
                 "resolvable; minutes are NOT claimable")
    elif facts:
        claim = "natal facts only: resolution is limited to the lagna/navamsa class"
    else:
        claim = "no evidence supplied yet"
    if top is not None:
        lo, hi = top.candidate.interval_local
        claim += (f". Winner is the CLASS INTERVAL {lo}..{hi} "
                  f"({top.candidate.ayanamsa}), never a point time")
    return claim


def _confidence(ranked: tuple[CandidateScore, ...], n_candidates: int) -> ConfidenceStatement:
    if len(ranked) < 2:
        return ConfidenceStatement(0.0, n_candidates, "insufficient candidates to compare")
    margin = ranked[0].channels.total - ranked[1].channels.total
    if margin >= _CONF_CLEAR:
        wording = "clear separation between the leading classes"
    elif margin >= _CONF_LEAN:
        wording = "a lean, not a verdict — more discriminating events would firm it"
    else:
        wording = "statistically indistinct leaders — treat the ranking as provisional"
    return ConfidenceStatement(margin, n_candidates, wording)


def build_report(*, mode: str, scored: tuple[CandidateScore, ...],
                 events: tuple[LifeEvent, ...], facts: tuple[NatalFact, ...],
                 top_k: int = 8) -> RectificationReport:
    ordered = sorted(scored, key=lambda cs: cs.channels.total, reverse=True)
    ranked_list = list(ordered[:top_k])
    # Dual-ayanamsa mandate: even when one frame sweeps the top-K, the OTHER frame's
    # best candidate is appended so both tracks always render side-by-side.
    present = {cs.candidate.ayanamsa for cs in ranked_list}
    for cs in ordered:
        if cs.candidate.ayanamsa not in present:
            ranked_list.append(cs)
            present.add(cs.candidate.ayanamsa)
    ranked = tuple(ranked_list)
    return RectificationReport(
        mode=mode, n_candidates=len(scored), ranked=ranked, events=events, facts=facts,
        ayanamsa_verdict=_ayanamsa_verdict(scored, events),
        resolution_statement=_resolution_statement(events, facts,
                                                   ranked[0] if ranked else None),
        confidence=_confidence(ranked, len(scored)))


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _cell(cs: CandidateScore, i: int) -> str:
    es = cs.event_scores[i]
    lords = "/".join((lm.lord or "-") + ("*" if lm.matched and lm.scorable else "")
                     for lm in es.levels)
    grade = {"par_excellence": "PAR", "limited": "lim", "absent": "abs",
             None: "n/a"}[es.active_grade]
    return f"{lords} [{grade}]"


def _candidate_header(cs: CandidateScore) -> str:
    lo, hi = cs.candidate.interval_local
    return (f"{cs.candidate.ayanamsa:7} {lo}..{hi}  total {cs.channels.total:+.2f} "
            f"(lords {cs.channels.event_lords:+.2f} | houses {cs.channels.event_houses:+.2f}"
            f" | facts {cs.channels.facts:+.2f} | arith {cs.channels.arithmetic:+.2f})")


def to_text(rep: RectificationReport) -> str:
    """Plain-text rendering: ranked classes with channel subtotals, the side-by-side
    per-event matrix (one ayanamsa block per track), active-house panels, the ayanamsa
    verdict, resolution statement, and confidence."""
    out: list[str] = []
    out.append(f"=== RECTIFICATION REPORT ({rep.mode}; {rep.n_candidates} candidate "
               f"classes) ===")
    out.append(f"resolution: {rep.resolution_statement}")
    out.append(f"confidence: margin {rep.confidence.margin_top2:+.2f} — "
               f"{rep.confidence.wording}")
    out.append("")
    out.append("--- ranked candidate classes (channel subtotals always visible) ---")
    for rank, cs in enumerate(rep.ranked, 1):
        out.append(f"#{rank} {_candidate_header(cs)}")
    # side-by-side ayanamsa blocks of the per-event matrix
    out.append("")
    out.append("--- per-event fit matrix (MD/AD/PD lords, * = scorable significator "
               "match, [grade] = house activation) ---")
    for ay in sorted({cs.candidate.ayanamsa for cs in rep.ranked}):
        block = [cs for cs in rep.ranked if cs.candidate.ayanamsa == ay]
        out.append(f"  [{ay} track]")
        for i, ev in enumerate(rep.events):
            cells = "  |  ".join(f"{cs.candidate.time_str} {_cell(cs, i)}"
                                 for cs in block[:3])
            date = f"{ev.year}" + (f"-{ev.month:02d}" if ev.month else "") + (
                f"-{ev.day:02d}" if ev.day else "")
            out.append(f"    {ev.event_type:20} {date:10}  {cells}")
    # active-house panels of the leader
    if rep.ranked:
        out.append("")
        out.append("--- active houses at each event (leader class) — HTJAH-II:680-694 ---")
        leader = rep.ranked[0]
        for es in leader.event_scores:
            panel = " ".join(es.active_panel) if es.active_panel else "(unscorable)"
            out.append(f"    {es.event_type:20} H{es.house:<2} -> {panel}")
    out.append("")
    out.append(f"--- ayanamsa verdict (dual-frame analysis is mandatory) ---")
    for ay, t, total in rep.ayanamsa_verdict.best_by_ayanamsa:
        out.append(f"    best {ay:7} @ {t}  total {total:+.2f}")
    out.append(f"    VERDICT: {rep.ayanamsa_verdict.statement}")
    if rep.discriminators or rep.flat_events:
        out.append("")
        out.append(f"--- evidence orthogonality ---")
        if rep.discriminators:
            out.append(f"    discriminators : {', '.join(rep.discriminators)}")
        if rep.flat_events:
            out.append(f"    flat (non-discriminating): {', '.join(rep.flat_events)}")
        for a, b in rep.correlated_pairs:
            out.append(f"    correlated pair: {a} ~ {b} (count as one witness)")
    if rep.suggestions:
        out.append("")
        out.append("--- next most-discriminating questions ---")
        for s in rep.suggestions:
            out.append(f"    * {s}")
    return "\n".join(out)


def to_markdown(rep: RectificationReport) -> str:
    """Markdown rendering — same content, table-formed."""
    out: list[str] = []
    out.append(f"# Rectification report ({rep.mode})")
    out.append("")
    out.append(f"- **Candidates:** {rep.n_candidates} classes")
    out.append(f"- **Resolution:** {rep.resolution_statement}")
    out.append(f"- **Confidence:** margin {rep.confidence.margin_top2:+.2f} — "
               f"{rep.confidence.wording}")
    out.append("")
    out.append("## Ranked classes")
    out.append("")
    out.append("| # | ayanamsa | class interval | lords | houses | facts | arith | total |")
    out.append("|---|----------|----------------|-------|--------|-------|-------|-------|")
    for rank, cs in enumerate(rep.ranked, 1):
        lo, hi = cs.candidate.interval_local
        ch = cs.channels
        out.append(f"| {rank} | {cs.candidate.ayanamsa} | {lo}..{hi} "
                   f"| {ch.event_lords:+.2f} | {ch.event_houses:+.2f} "
                   f"| {ch.facts:+.2f} | {ch.arithmetic:+.2f} | **{ch.total:+.2f}** |")
    out.append("")
    out.append("## Per-event fit (side-by-side ayanamsa tracks)")
    for ay in sorted({cs.candidate.ayanamsa for cs in rep.ranked}):
        block = [cs for cs in rep.ranked if cs.candidate.ayanamsa == ay]
        out.append("")
        out.append(f"### {ay} track")
        out.append("")
        header = "| event | date | " + " | ".join(
            cs.candidate.time_str for cs in block[:3]) + " |"
        out.append(header)
        out.append("|" + "---|" * (2 + len(block[:3])))
        for i, ev in enumerate(rep.events):
            date = f"{ev.year}" + (f"-{ev.month:02d}" if ev.month else "") + (
                f"-{ev.day:02d}" if ev.day else "")
            cells = " | ".join(_cell(cs, i) for cs in block[:3])
            out.append(f"| {ev.event_type} | {date} | {cells} |")
    out.append("")
    out.append("## Ayanamsa verdict")
    out.append("")
    for ay, t, total in rep.ayanamsa_verdict.best_by_ayanamsa:
        out.append(f"- best **{ay}** @ {t}: total {total:+.2f}")
    out.append(f"- **{rep.ayanamsa_verdict.statement}**")
    if rep.suggestions:
        out.append("")
        out.append("## Next questions")
        for s in rep.suggestions:
            out.append(f"- {s}")
    return "\n".join(out)
