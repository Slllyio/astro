"""Famous-chart accuracy benchmark.

Tests the integrated reading engine against well-documented historical
figures and their life events. For each (chart, event) pair, the
benchmark:

1. Generates the integrated reading for the chart at the event's date.
2. Extracts the direction (positive/negative/neutral/mixed) for the
   event's domain (career/marriage/children/wealth/health/education).
3. Compares the extracted direction against the event's documented
   polarity.

Produces per-chart + per-domain precision/recall numbers.

PHILOSOPHY: This is a CALIBRATION TOOL, not a proof. The mapping
"prediction direction matches event polarity" is heuristic — many real
events have mixed astrological signatures (e.g. a marriage that ends in
divorce). The benchmark surfaces ALIGNMENT RATES, not truth claims.
Doctrine is axiomatic; this just helps spot calibration drift.

Public surface
--------------
- ``FamousEvent`` — one ground-truth event record.
- ``FAMOUS_EVENTS`` — curated list of ~25 events across 6 charts.
- ``run_benchmark(events=FAMOUS_EVENTS, *, enrich=False)`` -> ``BenchmarkReport``
"""

from __future__ import annotations

from app.integration.benchmark.event_corpus import (
    FAMOUS_EVENTS,
    FamousEvent,
    FamousChart,
    CHART_REGISTRY,
)
from app.integration.benchmark.runner import (
    BenchmarkReport,
    EventOutcome,
    PerChartSummary,
    PerDomainSummary,
    run_benchmark,
    score_event,
)

__all__ = [
    "FamousEvent",
    "FamousChart",
    "FAMOUS_EVENTS",
    "CHART_REGISTRY",
    "BenchmarkReport",
    "EventOutcome",
    "PerChartSummary",
    "PerDomainSummary",
    "run_benchmark",
    "score_event",
]
