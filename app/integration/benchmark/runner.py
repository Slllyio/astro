"""Benchmark runner — scores each (chart × event) pair and aggregates.

For each event:
1. Generate the integrated reading for the chart (cached per-chart since
   the natal reading doesn't change with the event date; only the dasha
   timing matters and we read that from the same reading).
2. Find the active dasha lord at the event date.
3. Extract the domain's overall direction from the reading.
4. Compare the direction against the event's documented polarity.

Scoring:
- "aligned" = direction matches polarity (positive↔positive, negative↔negative)
- "neutral" = direction is neutral (counted as neither alignment nor misalignment)
- "mixed" = direction is mixed (counted with mixed-handling rule)
- "misaligned" = direction is opposite the event polarity

Aggregate metrics:
- alignment_rate = aligned / (aligned + misaligned)
- coverage_rate = (aligned + misaligned) / total_events
- per_domain_alignment_rate, per_chart_alignment_rate
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.integration.benchmark.event_corpus import (
    CHART_REGISTRY,
    FAMOUS_EVENTS,
    FamousChart,
    FamousEvent,
)
from app.reading.proforma import compute as track_a_compute
from app.reading.schema import ChartInput

logger = logging.getLogger(__name__)


class EventOutcome(BaseModel):
    """Per-event scoring result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chart_name: str
    event_date: str
    domain: str
    event_polarity: str
    description: str
    engine_direction: str | None = None
    engine_confidence_band: str | None = None
    active_md_lord_at_event: str | None = None
    outcome: str  # "aligned" / "misaligned" / "neutral" / "mixed" / "skipped"
    reason: str | None = None


class PerDomainSummary(BaseModel):
    """Aggregate scoring for one domain across all charts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    total_events: int
    aligned: int
    misaligned: int
    neutral_or_mixed: int
    skipped: int
    alignment_rate: float = Field(ge=0.0, le=1.0)


class PerChartSummary(BaseModel):
    """Aggregate scoring for one chart across all its events."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chart_name: str
    total_events: int
    aligned: int
    misaligned: int
    neutral_or_mixed: int
    skipped: int
    alignment_rate: float = Field(ge=0.0, le=1.0)


class BenchmarkReport(BaseModel):
    """Top-level benchmark report — per-event outcomes + aggregations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "0.6.0"
    total_events: int
    aligned: int
    misaligned: int
    neutral_or_mixed: int
    skipped: int
    overall_alignment_rate: float = Field(ge=0.0, le=1.0)
    per_event: list[EventOutcome]
    per_domain: list[PerDomainSummary]
    per_chart: list[PerChartSummary]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jd_from_iso(date_iso: str) -> float:
    """Crude JD-from-ISO date for active-MD lookup at event date."""
    # Use the same algorithm Track A uses internally; for simplicity here we
    # invoke swe via a thin wrapper. Avoid dependency by approximation:
    # JD = 367*Y - 7*(Y + (M+9)/12)/4 + 275*M/9 + D + 1721013.5
    from datetime import date
    d = date.fromisoformat(date_iso)
    y, m, day = d.year, d.month, d.day
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    b = 2 - a + (a // 4)
    return (
        int(365.25 * (y + 4716))
        + int(30.6001 * (m + 1))
        + day + b - 1524.5
        + 0.5  # noon-of-day reference
    )


def _find_active_md_at(reading: dict[str, Any], event_jd: float) -> str | None:
    """Look up the active Vimshottari MD lord for the event JD."""
    md_judgments = (reading.get("sequences") or {}).get("md_judgments") or []
    for entry in md_judgments:
        start = entry.get("start_jd")
        end = entry.get("end_jd")
        if start is None or end is None:
            continue
        if float(start) <= event_jd < float(end):
            return str(entry.get("md_lord", ""))
    return None


def _extract_domain_direction(reading: dict[str, Any], domain: str) -> tuple[str | None, str | None]:
    """Pull the (direction, confidence_band) for one domain from the reading."""
    domain_block = (reading.get("domains") or {}).get(domain)
    if not isinstance(domain_block, dict):
        return None, None
    overall = domain_block.get("overall_verdict") or {}
    confidence = domain_block.get("confidence") or {}
    return overall.get("direction"), confidence.get("band")


def _classify_outcome(engine_direction: str | None, event_polarity: str) -> str:
    """Map (direction, polarity) to alignment label."""
    if engine_direction is None:
        return "skipped"
    if engine_direction == "neutral":
        return "neutral"
    if engine_direction == "mixed":
        return "mixed"
    if event_polarity == "mixed":
        # Mixed events accept any non-neutral direction as "aligned"
        return "aligned"
    # Direct match
    if (engine_direction == event_polarity):
        return "aligned"
    return "misaligned"


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_event(
    chart: FamousChart,
    event: FamousEvent,
    *,
    enrich: bool = False,
    reading_cache: dict[str, dict] | None = None,
) -> EventOutcome:
    """Score one (chart × event) pair.

    Parameters
    ----------
    chart
        FamousChart with birth data.
    event
        FamousEvent with date + domain + polarity.
    enrich
        If True, runs Track A's Tier-3 enrichments (slower).
    reading_cache
        Optional dict to memoize the reading per chart_name so multiple
        events on the same chart don't recompute the full pipeline.
    """
    cache_key = event.chart_name
    if reading_cache is not None and cache_key in reading_cache:
        reading = reading_cache[cache_key]
    else:
        try:
            chart_input = ChartInput(
                dob=chart.dob, time=chart.time, tz=chart.tz,
                lat=chart.lat, lon=chart.lon,
            )
            reading = track_a_compute(chart_input, enrich=enrich)
            if reading_cache is not None:
                reading_cache[cache_key] = reading
        except Exception as exc:
            return EventOutcome(
                chart_name=event.chart_name,
                event_date=event.event_date,
                domain=event.domain,
                event_polarity=event.polarity,
                description=event.description,
                outcome="skipped",
                reason=f"compute() failed: {type(exc).__name__}: {exc}",
            )

    direction, band = _extract_domain_direction(reading, event.domain)
    event_jd = _jd_from_iso(event.event_date)
    md_lord = _find_active_md_at(reading, event_jd)

    outcome = _classify_outcome(direction, event.polarity)

    return EventOutcome(
        chart_name=event.chart_name,
        event_date=event.event_date,
        domain=event.domain,
        event_polarity=event.polarity,
        description=event.description,
        engine_direction=direction,
        engine_confidence_band=band,
        active_md_lord_at_event=md_lord,
        outcome=outcome,
        reason=None if direction is not None else "domain not present in reading",
    )


def _aggregate_alignment(items: list[EventOutcome]) -> tuple[int, int, int, int, float]:
    """Returns (aligned, misaligned, neutral_or_mixed, skipped, alignment_rate)."""
    aligned = sum(1 for x in items if x.outcome == "aligned")
    misaligned = sum(1 for x in items if x.outcome == "misaligned")
    neutral_or_mixed = sum(1 for x in items if x.outcome in ("neutral", "mixed"))
    skipped = sum(1 for x in items if x.outcome == "skipped")
    denom = aligned + misaligned
    rate = aligned / denom if denom > 0 else 0.0
    return aligned, misaligned, neutral_or_mixed, skipped, rate


def run_benchmark(
    events: list[FamousEvent] | None = None,
    *,
    enrich: bool = False,
    chart_registry: dict[str, FamousChart] | None = None,
) -> BenchmarkReport:
    """Run the full benchmark across all supplied events.

    Parameters
    ----------
    events
        Defaults to ``FAMOUS_EVENTS`` if None.
    enrich
        Run Track A's Tier-3 enrichments. Adds ~3-5s per chart; the
        ``reading_cache`` keeps it to per-chart cost instead of per-event.
    chart_registry
        Defaults to ``CHART_REGISTRY`` if None.
    """
    if events is None:
        events = FAMOUS_EVENTS
    if chart_registry is None:
        chart_registry = CHART_REGISTRY

    reading_cache: dict[str, dict] = {}
    per_event: list[EventOutcome] = []

    for event in events:
        chart = chart_registry.get(event.chart_name)
        if chart is None:
            per_event.append(EventOutcome(
                chart_name=event.chart_name,
                event_date=event.event_date,
                domain=event.domain,
                event_polarity=event.polarity,
                description=event.description,
                outcome="skipped",
                reason=f"chart {event.chart_name!r} not in CHART_REGISTRY",
            ))
            continue
        per_event.append(score_event(
            chart, event, enrich=enrich, reading_cache=reading_cache,
        ))

    # Per-domain aggregation
    domains = sorted({e.domain for e in events})
    per_domain: list[PerDomainSummary] = []
    for domain in domains:
        items = [x for x in per_event if x.domain == domain]
        aligned, misaligned, neutral_or_mixed, skipped, rate = _aggregate_alignment(items)
        per_domain.append(PerDomainSummary(
            domain=domain,
            total_events=len(items),
            aligned=aligned, misaligned=misaligned,
            neutral_or_mixed=neutral_or_mixed, skipped=skipped,
            alignment_rate=rate,
        ))

    # Per-chart aggregation
    charts = sorted({e.chart_name for e in events})
    per_chart: list[PerChartSummary] = []
    for chart_name in charts:
        items = [x for x in per_event if x.chart_name == chart_name]
        aligned, misaligned, neutral_or_mixed, skipped, rate = _aggregate_alignment(items)
        per_chart.append(PerChartSummary(
            chart_name=chart_name,
            total_events=len(items),
            aligned=aligned, misaligned=misaligned,
            neutral_or_mixed=neutral_or_mixed, skipped=skipped,
            alignment_rate=rate,
        ))

    # Top-level aggregation
    total_aligned, total_misaligned, total_n_or_m, total_skipped, overall_rate = (
        _aggregate_alignment(per_event)
    )

    return BenchmarkReport(
        total_events=len(per_event),
        aligned=total_aligned,
        misaligned=total_misaligned,
        neutral_or_mixed=total_n_or_m,
        skipped=total_skipped,
        overall_alignment_rate=overall_rate,
        per_event=per_event,
        per_domain=per_domain,
        per_chart=per_chart,
    )
