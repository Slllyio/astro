"""The next-question suggester — which evidence would best split the surviving classes.

This encodes the interactive move that resolved the worked rect_case_01 session: the
supplied events (marriage, childbirth) were VENUS-natured and matched every candidate
("flat"), so the operator asked for an ORTHOGONAL event — the government job (a
Saturn/10th matter) — and for the mother's condition (an H4 natal fact), which split
raman from lahiri. Here that move is computed:

* **event suggestions** — for every taxonomy type NOT yet supplied, build each surviving
  candidate's Bhukti-level MATCH TIMELINE over [birth, horizon] (the intervals whose MD
  or AD lord is a significator of that type, per the Time-of-Fructification sets), and
  rank types by the mean pairwise symmetric-difference of those timelines: the type
  whose match windows disagree most between candidates is the question that, once
  dated, splits the set hardest.
* **fact suggestions** — signification keys where the best-raman and best-lahiri charts'
  judge_house verdicts DISAGREE (Tier-F, two casts): a zero-date question that
  discriminates the ayanamsa (exactly the mother question of the worked session).

Usage:
    from app.raman_saab.rectification import suggest
    sugg = suggest.suggest_events(ranked, cache, supplied={"marriage"},
                                  birth_jd=jd0, horizon_jd=jd_now)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.house_template import judge_all_houses
from app.raman_saab.primitives import vimshottari as vim
from app.raman_saab.rectification.candidates import CandidateChart, ChartCache
from app.raman_saab.rectification.events import EVENT_TAXONOMY
from app.raman_saab.rectification.scoring import CandidateScore, timer_union_for_spec

_Interval = tuple[float, float]


@dataclass(frozen=True)
class Suggestion:
    kind: Literal["event", "fact"]
    key: str
    question: str
    detail: str
    power: float                          # 0..1 discrimination power (events); 1.0 facts

    def render(self) -> str:
        return f"[{self.kind}] {self.question}  ({self.detail})"


# ---------------------------------------------------------------------------
# Interval arithmetic (all lengths in days)
# ---------------------------------------------------------------------------

def _merge(intervals: list[_Interval]) -> list[_Interval]:
    out: list[_Interval] = []
    for lo, hi in sorted(intervals):
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def _length(intervals: list[_Interval]) -> float:
    return sum(hi - lo for lo, hi in intervals)


def _intersect(a: list[_Interval], b: list[_Interval]) -> list[_Interval]:
    out: list[_Interval] = []
    i = j = 0
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if lo < hi:
            out.append((lo, hi))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out


def _jaccard_distance(a: list[_Interval], b: list[_Interval]) -> float:
    """|A Δ B| / |A ∪ B| over interval lengths; 0 = identical windows, 1 = disjoint."""
    union = _length(_merge(a + b))
    if union <= 0.0:
        return 0.0
    inter = _length(_intersect(_merge(a), _merge(b)))
    return (union - inter) / union


# ---------------------------------------------------------------------------
# Event suggestions
# ---------------------------------------------------------------------------

def _match_timeline(chart: RamanChart, spec, birth_jd: float,
                    horizon_jd: float) -> list[_Interval]:
    """Bhukti-level intervals in [birth, horizon] whose MD or AD lord is a
    significator of ``spec`` for this chart."""
    timers = timer_union_for_spec(chart, spec)
    out: list[_Interval] = []
    for md in vim.mahadasha_timeline(chart):
        if md.end_jd <= birth_jd or md.start_jd >= horizon_jd:
            continue
        for bh in vim.bhuktis(md):
            lo, hi = max(bh.start_jd, birth_jd), min(bh.end_jd, horizon_jd)
            if lo >= hi:
                continue
            if bh.maha in timers or (bh.antar and bh.antar in timers):
                out.append((lo, hi))
    return _merge(out)


def suggest_events(ranked: tuple[CandidateScore, ...], cache: ChartCache,
                   supplied: frozenset[str], *, birth_jd: float, horizon_jd: float,
                   top_n_candidates: int = 4, max_suggestions: int = 3,
                   ) -> tuple[Suggestion, ...]:
    """Rank the UNSUPPLIED event types by how differently their match windows fall
    across the leading candidates — the information-gain question ranking."""
    cands: list[CandidateChart] = [cs.candidate for cs in ranked[:top_n_candidates]]
    if len(cands) < 2:
        return ()
    charts = [cache.light(c) for c in cands]
    scored_types: list[tuple[float, str]] = []
    for key, spec in EVENT_TAXONOMY.items():
        if key in supplied:
            continue
        timelines = [_match_timeline(ch, spec, birth_jd, horizon_jd) for ch in charts]
        dists = [_jaccard_distance(timelines[i], timelines[j])
                 for i in range(len(timelines)) for j in range(i + 1, len(timelines))]
        power = sum(dists) / len(dists) if dists else 0.0
        scored_types.append((power, key))
    scored_types.sort(reverse=True)
    out: list[Suggestion] = []
    for power, key in scored_types[:max_suggestions]:
        if power <= 0.0:
            continue
        spec = EVENT_TAXONOMY[key]
        out.append(Suggestion(
            kind="event", key=key, question=spec.question, power=round(power, 3),
            detail=f"match windows disagree {power:.0%} across the leading classes"))
    return tuple(out)


# ---------------------------------------------------------------------------
# Fact suggestions (ayanamsa discriminators, Tier-F on the two frame-bests)
# ---------------------------------------------------------------------------

def suggest_facts(ranked: tuple[CandidateScore, ...], cache: ChartCache,
                  supplied_subjects: frozenset[str], *, max_suggestions: int = 3,
                  ) -> tuple[Suggestion, ...]:
    """Signification keys on which the best candidates of the two ayanamsas DISAGREE —
    zero-date questions that discriminate the frame (the 'mother' move)."""
    best: dict[str, CandidateChart] = {}
    for cs in ranked:
        ay = cs.candidate.ayanamsa
        if ay not in best:
            best[ay] = cs.candidate
    if len(best) < 2:
        return ()
    verdicts: dict[str, dict[str, str]] = {}
    for ay, cand in best.items():
        chart = cache.full(cand)
        verdicts[ay] = {
            sv.signification: sv.verdict
            for pf in judge_all_houses(chart) for sv in pf.significations}
    (ay_a, va), (ay_b, vb) = sorted(verdicts.items())
    out: list[Suggestion] = []
    for key in sorted(set(va) & set(vb)):
        if key in supplied_subjects or len(out) >= max_suggestions:
            continue
        a, b = va[key], vb[key]
        if a == b or "insufficient-evidence" in (a, b):
            continue
        if {a, b} == {"favourable", "afflicted"}:        # only the sharp disagreements
            out.append(Suggestion(
                kind="fact", key=key,
                question=f"Has '{key}' been notably good or notably troubled in life?",
                power=1.0,
                detail=f"{ay_a} judges it {a}, {ay_b} judges it {b} — "
                       f"the answer picks the ayanamsa"))
    return tuple(out)
