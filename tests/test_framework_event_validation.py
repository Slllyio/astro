"""Tests for app.medini.ml.framework_event_validation."""
from __future__ import annotations

import pandas as pd
import pytest

from app.core.chart_model import Chart
from app.medini.ml.framework_event_validation import (
    EventClassResult,
    _baseline_distribution,
    _event_distribution,
    _extract_transit_signs,
    _lift,
    format_results,
)


def _fake_readings_df() -> pd.DataFrame:
    """A 4-row readings.parquet-shaped frame."""
    rows = []
    for i, label in enumerate(["strong", "medium", "weak", "afflicted"]):
        rows.append({
            f"b7_label": label,
            f"b10_label": label,
            f"b8_label": label,
        })
    return pd.DataFrame(rows)


def _fake_chart() -> Chart:
    return Chart(
        asc_sign=1, asc_lon=0.0,
        planet_signs={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                      "Jupiter", "Venus", "Saturn",
                                      "Rahu", "Ketu"]},
        planet_houses={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                       "Jupiter", "Venus", "Saturn",
                                       "Rahu", "Ketu"]},
        planet_lons={p: 0.0 for p in ["Sun", "Moon", "Mars", "Mercury",
                                       "Jupiter", "Venus", "Saturn",
                                       "Rahu", "Ketu"]},
        person_id="TEST:1",
    )


class TestExtractTransitSigns:
    """Pull 9-planet transit columns from an event_dossier row."""

    def test_extracts_all_9_planets_when_complete(self):
        """All 9 ``t_<planet>_sign`` populated → returns 9-key dict."""
        row = pd.Series({f"t_{g}_sign": 6 for g in [
            "sun", "moon", "mars", "mercury", "jupiter",
            "venus", "saturn", "rahu", "ketu",
        ]})
        out = _extract_transit_signs(row)
        assert len(out) == 9
        assert out["Sun"] == 6

    def test_returns_empty_when_one_planet_missing(self):
        """Any missing planet → empty dict (all-or-nothing semantics)."""
        row = pd.Series({f"t_{g}_sign": 6 for g in [
            "sun", "moon", "mars", "mercury", "jupiter",
            "venus", "saturn", "rahu",  # ketu missing
        ]})
        out = _extract_transit_signs(row)
        assert out == {}

    def test_returns_empty_when_sign_out_of_range(self):
        """Validation: sign 0 or 13 → empty dict."""
        row = pd.Series({**{f"t_{g}_sign": 6 for g in [
            "moon", "mars", "mercury", "jupiter",
            "venus", "saturn", "rahu", "ketu",
        ]}, "t_sun_sign": 0})
        assert _extract_transit_signs(row) == {}


class TestLift:
    """Lift ratio computation with edge cases."""

    def test_lift_basic(self):
        """0.1 / 0.05 = 2.0 — common case."""
        assert _lift(0.1, 0.05) == pytest.approx(2.0)

    def test_lift_unity_when_equal(self):
        """Same rate event and baseline → lift = 1.0."""
        assert _lift(0.5, 0.5) == 1.0

    def test_lift_nan_when_baseline_zero(self):
        """Division by zero baseline returns NaN safely."""
        import math
        assert math.isnan(_lift(0.1, 0.0))


class TestBaselineDistribution:
    """Population-baseline label distribution."""

    def test_distribution_sums_to_one(self):
        """All probabilities sum to 1.0 (within 4 labels)."""
        dist, n = _baseline_distribution(_fake_readings_df(), bhava=7)
        assert n == 4
        assert sum(dist.values()) == pytest.approx(1.0)

    def test_missing_column_returns_zeros(self):
        """A bhava with no ``b{n}_label`` column → all zeros."""
        df = pd.DataFrame({"unrelated_col": [1, 2]})
        dist, n = _baseline_distribution(df, bhava=7)
        assert n == 0
        assert all(v == 0.0 for v in dist.values())


class TestEventClassResult:
    """Dataclass structural integrity."""

    def test_frozen_dataclass(self):
        """EventClassResult is immutable."""
        r = EventClassResult(
            event_class="marriage", target_bhava=7,
            n_events=10, n_baseline=100,
            event_dist={"strong": 0.1, "medium": 0.5, "weak": 0.3, "afflicted": 0.1},
            baseline_dist={"strong": 0.05, "medium": 0.6, "weak": 0.3, "afflicted": 0.05},
            lift_strong=2.0, lift_afflicted=2.0,
        )
        with pytest.raises(Exception):
            r.lift_strong = 1.0  # type: ignore[misc]


class TestFormatResults:
    """Plain-text report rendering."""

    def test_format_includes_header(self):
        """Output starts with the FRAMEWORK title banner."""
        r = EventClassResult(
            event_class="marriage", target_bhava=7,
            n_events=10, n_baseline=100,
            event_dist={lbl: 0.25 for lbl in
                        ["strong", "medium", "weak", "afflicted"]},
            baseline_dist={lbl: 0.25 for lbl in
                           ["strong", "medium", "weak", "afflicted"]},
            lift_strong=1.0, lift_afflicted=1.0,
        )
        out = format_results([r])
        assert "FRAMEWORK EVENT-VALIDATION" in out
        assert "marriage" in out
