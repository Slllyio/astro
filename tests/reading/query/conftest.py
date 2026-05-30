"""Shared fixtures for query-layer tests.

The Bangalore baseline ReadingOutput is the canonical anchor (see CLAUDE.md
test-pinning policy). We reuse the narrative-layer fixture pattern: compute
once per session and feed every test the same dict.
"""
from __future__ import annotations

import pytest

from app.reading.proforma import _run_core_pipeline
from app.reading.schema import ChartInput


CANONICAL_INPUT = ChartInput(
    dob="1990-07-15",
    time="12:00",
    tz="+05:30",
    lat=12.97,
    lon=77.59,
)


@pytest.fixture(scope="session")
def bangalore_reading() -> dict:
    """Bangalore baseline ReadingOutput dict (Stages 1-7, no Tier-3 enrichment)."""
    return _run_core_pipeline(CANONICAL_INPUT)
