"""Scan a whole day for its CLEAN spans — pure iteration over `window_scorer`.

Raman's electional question is "**when** today is clean?", not "how is noon?". This module
answers it the only way the doctrine licenses: it samples the day at a fixed interval and
evaluates every sample with the EXISTING scorer (`window_scorer.evaluate_moment`), then joins
the runs of consecutive passing samples into contiguous spans. **It adds no doctrine of its
own** — the hard-fail ordering is Raman's essentials ordering (MUHURTHA-10:226-228, applied
by the scorer), the negative windows are the ones `negative_windows` already computes, and a
span is nothing more than "every sample inside it passed that same judgment".

Honesty about resolution (Measured-Truth framing applies wherever this is surfaced): a span
is VERIFIED at its sample points and interpolated between them, so it is only as fine as the
sample interval; a span's end is the next sample point (exclusive), clipped so that no
hard-blocked window can ever fall inside a span. Output is a statement of Raman's electional
method, never a validated prediction.

The module is PURE — like every other window function in this package it takes Julian Days
and a caller-supplied sampler, so tests need no ephemeris. `app/api/electional_routes.py`
supplies the live sampler (`compute_panchanga` + `cast_chart`).

Usage:
    from app.raman_saab.electional.day_scanner import scan_day, MomentInputs
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Final, Optional

import swisseph as swe

from app.raman_saab.electional.negative_windows import Window
from app.raman_saab.electional.window_scorer import MomentEvaluation, evaluate_moment

#: Half an hour — fine enough that no Rahu Kalam / durmuhurtha window (each at least a
#: fifteenth of a day or night) can hide between two samples, coarse enough to keep a full
#: sunrise-to-sunrise scan at ~48 evaluations.
DEFAULT_SAMPLE_MINUTES: Final[int] = 30

#: The eight essentials the scorer counts, in the order it counts them (five panchanga limbs
#: then Tarabala, Chandrabala, Panchaka). Names only — the doctrine lives in the scorer.
ESSENTIAL_FACTORS: Final[tuple[str, ...]] = (
    "tithi", "vara", "nakshatra", "yoga", "karana", "tarabala", "chandrabala", "panchaka")


@dataclass(frozen=True)
class MomentInputs:
    """Everything about a moment that CHANGES through the day, as the scorer wants it.

    The native's own janma star/rasi and the day's negative windows do not vary within the
    scan, so they are scan-level arguments; these seven do (the panchanga limbs roll over,
    the Moon changes rasi, the lagna changes every ~2 hours).
    """

    tithi_in_paksha: int
    weekday: int
    day_nakshatra: int
    yoga: int
    karana: int
    election_moon_rasi: int
    lagna_sign: int


@dataclass(frozen=True)
class Sample:
    """One judged instant of the scan."""

    jd: float
    local_iso: str
    evaluation: MomentEvaluation

    @property
    def ok(self) -> bool:
        return self.evaluation.ok

    @property
    def score(self) -> int:
        return self.evaluation.score


@dataclass(frozen=True)
class CleanSpan:
    """A contiguous run of samples that ALL passed the scorer's hard-fail ordering."""

    start_jd: float
    end_jd: float
    start_local: str
    end_local: str
    duration_minutes: float
    samples: int
    score: int              # essentials score guaranteed across the whole span (the minimum)
    score_max: int          # best essentials score any sample in the span reached
    passing: tuple[str, ...]  # factors favourable at EVERY sample of the span
    failing: tuple[str, ...]  # factors unfavourable at ANY sample of the span (none is a
    #                           hard failure — a hard failure would have ended the span)


@dataclass(frozen=True)
class DayScan:
    """The whole day: its samples, its clean spans (chronological) and what blocked it."""

    start_jd: float
    end_jd: float
    sample_minutes: int
    samples: tuple[Sample, ...]
    clean_spans: tuple[CleanSpan, ...]
    blocked_windows: tuple[Window, ...]

    @property
    def clean_sample_count(self) -> int:
        return sum(1 for s in self.samples if s.ok)


def jd_to_local_iso(jd: float, tz_offset: float) -> str:
    """A UT Julian Day as a local ISO-8601 timestamp at `tz_offset` hours.

    Calendar conversion goes through `swe.revjul` (never `datetime` arithmetic on the JD) per
    the project's JD rule; only the final wall-clock assembly uses `datetime`. The half-second
    nudge rounds the seconds field instead of truncating it, so an exact wall-clock instant
    that `revjul` returns as 5.4999999 h prints 05:30:00 rather than 05:29:59.
    """
    year, month, day, hour = swe.revjul(jd + tz_offset / 24.0, swe.GREG_CAL)
    tz = timezone(timedelta(hours=tz_offset))
    stamp = (datetime(int(year), int(month), int(day), tzinfo=tz)
             + timedelta(hours=float(hour), seconds=0.5))
    return stamp.isoformat(timespec="seconds")


def _factor_split(ev: MomentEvaluation) -> tuple[frozenset[str], frozenset[str]]:
    """(favourable, unfavourable) essential-factor names for one evaluation."""
    good = {lv.limb for lv in ev.limbs if lv.suitable}
    bad = {lv.limb for lv in ev.limbs if not lv.suitable}
    for name, ok in (("tarabala", ev.tarabala.favourable), ("chandrabala", ev.chandrabala_ok),
                     ("panchaka", ev.panchaka.favourable)):
        (good if ok else bad).add(name)
    return frozenset(good), frozenset(bad)


def _window_in_gap(windows: tuple[Window, ...], earlier_jd: float, later_jd: float) -> bool:
    """True when a hard-blocked window lies between two consecutive samples.

    Neither endpoint can be inside a window (both are clean samples, and the scorer's
    membership test is half-open `start <= jd < end`), so any overlap means the window sits
    wholly in the gap — the run must be split there rather than paved over.
    """
    return any(w.start_jd < later_jd and w.end_jd > earlier_jd for w in windows)


def _span_end(windows: tuple[Window, ...], last_clean_jd: float, next_sample_jd: float,
              day_end_jd: float) -> float:
    """Where a run's span may honestly be said to end.

    The next sample point (exclusive — taken from the sample grid itself, so the exclusion is
    exact in floating point), never past the scan's own end, and never past the start of a
    hard-blocked window — so a blocked window can never fall inside a clean span.
    """
    end = min(next_sample_jd, day_end_jd)
    later = [w.start_jd for w in windows if w.start_jd > last_clean_jd]
    return min(end, min(later)) if later else end


def scan_day(*, day_start_jd: float, day_end_jd: float, janma_nakshatra: int, janma_rasi: int,
             sampler: Callable[[float], MomentInputs],
             sample_minutes: int = DEFAULT_SAMPLE_MINUTES,
             act: Optional[str] = None,
             negative_windows: tuple[Window, ...] = (),
             tz_offset: float = 0.0) -> DayScan:
    """Judge `[day_start_jd, day_end_jd)` every `sample_minutes` and return the clean spans.

    `sampler(jd)` supplies the moment's panchanga limbs, Moon rasi and lagna (the caller owns
    the ephemeris; this module owns only the iteration). `janma_nakshatra` / `janma_rasi` /
    `act` / `negative_windows` are passed through to `evaluate_moment` unchanged, so every
    sample is judged EXACTLY as a single-moment reading of that instant would be.

    Raises:
        ValueError: on a non-positive interval or an empty/reversed scan span.
    """
    if sample_minutes <= 0:
        raise ValueError("sample_minutes must be positive")
    if day_end_jd <= day_start_jd:
        raise ValueError("day_end_jd must be after day_start_jd")

    step = sample_minutes / 1440.0
    count = max(1, int(round((day_end_jd - day_start_jd) / step)))

    samples: list[Sample] = []
    for i in range(count):
        jd = day_start_jd + i * step
        if jd >= day_end_jd:
            break
        m = sampler(jd)
        ev = evaluate_moment(
            jd=jd, janma_nakshatra=janma_nakshatra, janma_rasi=janma_rasi,
            tithi_in_paksha=m.tithi_in_paksha, weekday=m.weekday,
            day_nakshatra=m.day_nakshatra, yoga=m.yoga, karana=m.karana,
            election_moon_rasi=m.election_moon_rasi, lagna_sign=m.lagna_sign,
            act=act, negative_windows=negative_windows)
        samples.append(Sample(jd=jd, local_iso=jd_to_local_iso(jd, tz_offset), evaluation=ev))

    runs: list[list[int]] = []
    for i, s in enumerate(samples):
        if not s.ok:
            continue
        joins = (runs and i == runs[-1][-1] + 1
                 and not _window_in_gap(negative_windows, samples[i - 1].jd, s.jd))
        if joins:
            runs[-1].append(i)
        else:
            runs.append([i])

    spans: list[CleanSpan] = []
    for run in runs:
        first, last = samples[run[0]], samples[run[-1]]
        end_jd = _span_end(negative_windows, last.jd,
                           day_start_jd + (run[-1] + 1) * step, day_end_jd)
        good, bad = _factor_split(first.evaluation)
        for idx in run[1:]:
            g, b = _factor_split(samples[idx].evaluation)
            good, bad = good & g, bad | b
        scores = [samples[i].score for i in run]
        spans.append(CleanSpan(
            start_jd=first.jd, end_jd=end_jd,
            start_local=first.local_iso, end_local=jd_to_local_iso(end_jd, tz_offset),
            duration_minutes=round((end_jd - first.jd) * 1440.0, 2), samples=len(run),
            score=min(scores), score_max=max(scores),
            passing=tuple(f for f in ESSENTIAL_FACTORS if f in good),
            failing=tuple(f for f in ESSENTIAL_FACTORS if f in bad)))

    return DayScan(start_jd=day_start_jd, end_jd=day_end_jd, sample_minutes=sample_minutes,
                   samples=tuple(samples), clean_spans=tuple(spans),
                   blocked_windows=tuple(negative_windows))


def rank_spans(spans: tuple[CleanSpan, ...]) -> tuple[CleanSpan, ...]:
    """Spans best-first: highest guaranteed essentials score, then longest, then earliest.

    Ranking is presentational ONLY — `score` is the scorer's own favourable-essentials count
    (MUHURTHA-10:226-228 ordering), and a higher count is not a promise of anything.
    """
    return tuple(sorted(spans, key=lambda s: (-s.score, -s.duration_minutes, s.start_jd)))
