"""Birth Time Rectification (BTR) — Gap M.

When birth time is uncertain (±30min or ±2hr or more), the Lagna degree
shifts and the entire chart-frame moves. BPHS Ch.95-97 + BV Raman's
*A Manual of Hindu Astrology* prescribe iterative rectification using
either Tattva (element-personality) matching or event-based scoring.

This module implements the EVENT METHOD (more rigorous than tattva):

  1. Caller provides a list of (known_event_jd, expected_bhava) pairs
     drawn from the native's life history (marriage, career change,
     parent's death, etc.).
  2. Perturb birth_jd across a window (e.g., ±60min in 1-min steps).
  3. For each perturbation: cast a new Lagna degree (the only thing
     that moves with birth_time within a few hours) and compute a
     fitness score:
         score = sum over events of:
             bhava_verdict_strength(perturbed_chart, expected_bhava,
                                     active_dasha_at_event_jd)
  4. Return the perturbation with the highest fitness as the candidate
     rectified birth time.

The chart computation itself (Lagna degree per minute of birth time)
requires the project's existing ephemeris engine — this module is the
SCORING + SEARCH layer. The caller supplies a chart-builder callable
that takes (birth_jd_perturbation) and returns a Chart.

## Why this works

The Lagna degree advances ~1° every 4 minutes (24h/360° = 4min/°). A
60-minute uncertainty window = ~15° of Lagna drift = potentially 1
sign-change. The relevant bhavas FOR THE NATIVE'S LIFE shift entirely
as Lagna changes. If the actual events match best when Lagna is X°,
that's the rectified Lagna degree.

## Caveats

- Need ≥3 well-dated events for stable rectification. With 1-2 events,
  multiple birth times tie.
- This is a SCORING search, not a deterministic solve — the highest-
  fitness time is the candidate, but human astrologer verification is
  recommended before locking the Lagna.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Final, Sequence

from app.core.chart_model import Chart


# Default perturbation window: ±60 minutes in 1-minute steps
DEFAULT_WINDOW_MINUTES: Final[int] = 60
DEFAULT_STEP_MINUTES: Final[int] = 1


@dataclass(frozen=True)
class KnownEvent:
    """One known life event used to score birth time perturbations."""
    event_jd: float
    expected_bhava: int          # 1..12 (which bhava the event should activate)
    label: str                   # human-readable event description
    weight: float = 1.0          # higher weight = more confident event


@dataclass(frozen=True)
class RectificationCandidate:
    """One candidate birth time + its fitness score."""
    perturbation_minutes: int    # offset from initial birth_jd (signed)
    candidate_birth_jd: float
    fitness_score: float         # higher = better fit
    per_event_scores: tuple[float, ...]  # score per known event


@dataclass(frozen=True)
class RectificationReport:
    """Full BTR report — best candidate + ranked alternatives."""
    initial_birth_jd: float
    best_candidate: RectificationCandidate
    top_candidates: tuple[RectificationCandidate, ...]   # top 5 by fitness
    n_events_used: int
    window_minutes: int
    notes: tuple[str, ...]


# Bhava scorer signature: given (chart, target_bhava, event_jd) → score
# Score range: -1.0 (afflicted) to +1.0 (strong).
BhavaScorer = Callable[[Chart, int, float], float]

# Chart builder signature: given a birth-time perturbation in minutes,
# return a Chart with the perturbed Lagna.
ChartBuilder = Callable[[float], Chart]


_MINUTES_PER_DAY: Final[float] = 1440.0


def _score_perturbation(
    perturbation_minutes: int,
    initial_birth_jd: float,
    events: Sequence[KnownEvent],
    chart_builder: ChartBuilder,
    bhava_scorer: BhavaScorer,
) -> RectificationCandidate:
    """Score a single perturbation against all known events."""
    candidate_jd = initial_birth_jd + (perturbation_minutes / _MINUTES_PER_DAY)
    chart = chart_builder(candidate_jd)
    per_event: list[float] = []
    fitness = 0.0
    for event in events:
        score = bhava_scorer(chart, event.expected_bhava, event.event_jd)
        per_event.append(score)
        fitness += score * event.weight
    return RectificationCandidate(
        perturbation_minutes=perturbation_minutes,
        candidate_birth_jd=candidate_jd,
        fitness_score=fitness,
        per_event_scores=tuple(per_event),
    )


def rectify_birth_time(
    initial_birth_jd: float,
    events: Sequence[KnownEvent],
    chart_builder: ChartBuilder,
    bhava_scorer: BhavaScorer,
    window_minutes: int = DEFAULT_WINDOW_MINUTES,
    step_minutes: int = DEFAULT_STEP_MINUTES,
) -> RectificationReport:
    """Run BTR search and return the best-fit birth time.

    Args:
        initial_birth_jd: caller's best-guess birth time (Julian Day).
        events: known life events with expected bhava activation.
        chart_builder: callable (birth_jd) → Chart that recomputes the
            chart at the perturbed birth time. Caller wires this to
            the project's ephemeris engine.
        bhava_scorer: callable (chart, target_bhava, event_jd) → score.
            Caller wires this to bhava_judge.judge_bhava + active
            transit context at event_jd.
        window_minutes: ± minutes to search (default 60).
        step_minutes: granularity of search (default 1).

    Returns:
        RectificationReport with best candidate + top 5 alternatives.

    Raises:
        ValueError: if events list is empty.
    """
    if not events:
        raise ValueError("BTR requires at least 1 known event for scoring")
    if window_minutes < step_minutes:
        raise ValueError(
            f"window_minutes ({window_minutes}) must be >= step_minutes ({step_minutes})"
        )

    candidates: list[RectificationCandidate] = []
    for offset in range(-window_minutes, window_minutes + 1, step_minutes):
        candidates.append(_score_perturbation(
            offset, initial_birth_jd, events, chart_builder, bhava_scorer,
        ))

    candidates.sort(key=lambda c: c.fitness_score, reverse=True)
    best = candidates[0]
    notes: list[str] = []
    if len(events) < 3:
        notes.append(
            f"Only {len(events)} events provided — rectification may be unstable. "
            "Recommend ≥3 well-dated events for confident BTR."
        )
    # Check if best is a clear winner or there's a tie
    if len(candidates) > 1:
        second = candidates[1]
        margin = best.fitness_score - second.fitness_score
        if margin < 0.1:
            notes.append(
                f"Best candidate margin over runner-up is small ({margin:.3f}); "
                "multiple birth times fit nearly equally — human astrologer "
                "verification recommended."
            )

    return RectificationReport(
        initial_birth_jd=initial_birth_jd,
        best_candidate=best,
        top_candidates=tuple(candidates[:5]),
        n_events_used=len(events),
        window_minutes=window_minutes,
        notes=tuple(notes),
    )


# ─── Default scorer (for testing / simple usage) ────────────────────


def simple_bhava_scorer(
    chart: Chart, target_bhava: int, event_jd: float,
) -> float:
    """A minimal bhava scorer for testing — uses lord placement heuristic.

    Production-grade usage should wire bhava_judge.judge_bhava + gochara
    overlay at event_jd. This simple scorer returns +1 if the target
    bhava's lord is in a Kendra/Trikona, -1 if in dusthana, else 0.

    The event_jd is unused in this scorer — production scorer would
    use it for gochara computation.
    """
    from app.core.functional_roles import functional_roles
    roles = functional_roles(chart.asc_sign)
    lord = next(
        (p for p, r in roles.items() if target_bhava in r.houses_ruled), None,
    )
    if not lord:
        return 0.0
    h = chart.house_of(lord)
    if h is None:
        return 0.0
    if h in {1, 4, 5, 7, 9, 10}:
        return 1.0
    if h in {6, 8, 12}:
        return -1.0
    return 0.0
