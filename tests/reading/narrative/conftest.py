"""Shared fixtures for narrative tests.

The Bangalore baseline ReadingOutput is the canonical anchor for the entire
`app.reading` package (see CLAUDE.md test-pinning policy). Generating it via
`_run_core_pipeline` once per test session keeps the suite fast and ensures
narrative tests exercise the real pipeline output shape (no hand-rolled
fakes that could drift from the schema).
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
    """Bangalore baseline ReadingOutput dict (Stages 1-7, no Tier-3).

    Session-scoped so it's computed exactly once across the entire
    tests/reading/narrative suite.
    """
    return _run_core_pipeline(CANONICAL_INPUT)
