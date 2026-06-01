"""Tests for ``app.reading.computations.shadbala_phase1``.

Doctrine source: BPHS Ch.27 (Sphuta Bala Adhyaya).

This module wraps the 5 Phase-1 Shadbala sub-components already exposed
by ``app.core.shadbala``:

  - Dig-bala         (BPHS 27.36) -- directional strength
  - Kala-bala        (BPHS 27.32-33, Phase-2 paksha-only sub-component)
  - Cheshta-bala     (BPHS 27.36-37) -- motional strength
  - Naisargika-bala  (BPHS 27.34)    -- innate per-planet constant
  - Drik-bala        (BPHS 27.38)    -- net aspectual strength

Sthana-bala (the Phase-0 component) is intentionally NOT re-emitted here
to preserve the Phase-0 / Phase-1 separation; downstream consumers can
attach it from the existing primitives.

Each Finding carries a verdict of the shape::

    "Saturn Shadbala-phase1: dig=10.0 kala=15.0 cheshta=20.0
     nai=2.0 drik=5.0 (total=52.0)"

For the 9 classical planets (Sun..Saturn + Rahu + Ketu). Lunar nodes
return 0 for components where classical doctrine does not assign a value
(Dig/Cheshta/Naisargika); we still emit a Finding so the dict is
exhaustive over the chart's 9 planets.
"""
from __future__ import annotations

import pytest

from app.reading.schema import Finding


_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


# ---------------------------------------------------------------------------
# Bangalore baseline fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def d1_chart(bangalore_chart) -> dict:
    return bangalore_chart["d1"]


@pytest.fixture(scope="module")
def asc_sign(bangalore_chart) -> int:
    return int(bangalore_chart["ascendant"]["sign"])


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestComputeShadbalaPhase1:

    def test_returns_dict_keyed_by_planet(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        assert isinstance(result, dict)
        # only the 9 classical planets present in d1
        assert set(result.keys()).issuperset({p for p in _PLANETS if p in d1_chart})

    def test_emits_findings(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        for planet, finding in result.items():
            assert isinstance(finding, Finding), (
                f"{planet} value is not a Finding"
            )

    def test_id_grammar(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        for planet, finding in result.items():
            assert finding.id == (
                f"foundation.shadbala_phase1.{planet.lower()}"
            ), f"unexpected id {finding.id!r}"

    def test_classification_is_primitive(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_verdict_carries_components(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        for planet, finding in result.items():
            for tag in ("dig=", "kala=", "cheshta=", "nai=", "drik=", "total="):
                assert tag in finding.verdict, (
                    f"{planet} verdict {finding.verdict!r} missing {tag!r}"
                )

    def test_doctrine_sentinel_in_evidence(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        for finding in result.values():
            joined = " ".join(finding.evidence)
            assert "BPHS" in joined


# ---------------------------------------------------------------------------
# Component correctness (delegating to app.core.shadbala)
# ---------------------------------------------------------------------------


class TestComponentCorrectness:
    """Spot-check that the wrapped values match app.core.shadbala outputs."""

    def test_naisargika_sun_is_60(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1, _parse_component,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        # BPHS 27.34: Sun's naisargika-bala = 60 virupa (rank 1 of 7)
        assert abs(_parse_component(result["Sun"], "nai") - 60.0) < 1e-3

    def test_naisargika_saturn_is_lowest(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1, _parse_component,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        # Saturn = 60/7 ≈ 8.571 virupa (rank 7 of 7)
        sat_nai = _parse_component(result["Saturn"], "nai")
        assert 8.0 < sat_nai < 9.0

    def test_total_is_sum_of_components(self, d1_chart, asc_sign):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1, _parse_component,
        )

        result = compute_shadbala_phase1(
            d1_chart, asc_sign, is_daytime=True,
        )
        for planet, finding in result.items():
            total = _parse_component(finding, "total")
            parts = sum(
                _parse_component(finding, key)
                for key in ("dig", "kala", "cheshta", "nai", "drik")
            )
            assert abs(total - parts) < 1e-3, (
                f"{planet}: total {total} != sum of parts {parts}"
            )


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestArgumentValidation:

    def test_invalid_asc_sign_raises(self, d1_chart):
        from app.reading.computations.shadbala_phase1 import (
            compute_shadbala_phase1,
        )

        with pytest.raises(ValueError):
            compute_shadbala_phase1(d1_chart, asc_sign=0, is_daytime=True)
        with pytest.raises(ValueError):
            compute_shadbala_phase1(d1_chart, asc_sign=13, is_daytime=True)
