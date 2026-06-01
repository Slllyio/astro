"""Smoke tests for the Gap-module annotator.

These tests run the actual Track-A pipeline on the Bangalore baseline,
build a Track-B Chart from the result, and verify each Gap module
either produces output or skips gracefully with a reason."""

from __future__ import annotations

import json

import pytest

from app.core.chart_model import Chart
from app.integration.gap_annotator import (
    GapAnnotatedReading,
    GapModuleEntry,
    annotate_with_gap_modules,
    chart_from_reading,
)
from app.reading.proforma import compute
from app.reading.schema import ChartInput


# ---------------------------------------------------------------------------
# Shared fixture: a real Bangalore reading
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def bangalore_reading() -> dict:
    """Compute Track A's reading for the canonical Bangalore baseline.

    Module-scoped because compute() takes ~0.6s cold; running it once and
    sharing across all tests in this module."""
    ci = ChartInput(
        dob="1990-07-15", time="12:00", tz="+05:30",
        lat=12.97, lon=77.59,
    )
    return compute(ci, enrich=False)


# ---------------------------------------------------------------------------
# chart_from_reading bridge
# ---------------------------------------------------------------------------

class TestChartFromReading:
    """Build a Track-B Chart from a Track-A reading."""

    def test_returns_chart_instance(self, bangalore_reading):
        chart = chart_from_reading(bangalore_reading)
        assert isinstance(chart, Chart)

    def test_chart_has_virgo_lagna(self, bangalore_reading):
        """Bangalore baseline → Virgo lagna (sign 6)."""
        chart = chart_from_reading(bangalore_reading)
        assert chart.asc_sign == 6

    def test_chart_has_nine_planets(self, bangalore_reading):
        chart = chart_from_reading(bangalore_reading)
        assert set(chart.planet_signs.keys()).issuperset({
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        })

    def test_chart_planet_signs_are_1_to_12(self, bangalore_reading):
        chart = chart_from_reading(bangalore_reading)
        for planet, sign in chart.planet_signs.items():
            assert 1 <= sign <= 12, f"{planet}: sign {sign} out of range"

    def test_chart_missing_planets_raises_keyerror(self):
        """Reading without chart.planets must fail loudly."""
        with pytest.raises(KeyError, match="chart"):
            chart_from_reading({"chart": {}})


# ---------------------------------------------------------------------------
# End-to-end annotator
# ---------------------------------------------------------------------------

class TestAnnotateBangaloreBaseline:
    """Full Bangalore run — most Gap modules should run successfully."""

    def test_returns_envelope(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        assert isinstance(result, GapAnnotatedReading)

    def test_chart_was_built(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        assert result.chart_built is True
        assert result.chart_summary is not None
        assert result.chart_summary["asc_sign"] == 6

    def test_eight_gap_modules_attempted(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        assert set(result.gap_modules.keys()) == {"A", "B", "D", "E", "F", "G", "H", "J"}

    def test_at_least_five_gap_modules_succeed(self, bangalore_reading):
        """For Bangalore baseline with day_of_week+is_day_birth supplied,
        at least 5 Gap modules must produce output."""
        result = annotate_with_gap_modules(
            bangalore_reading, day_of_week=6, is_day_birth=True,
        )
        assert result.available_count >= 5

    def test_gap_b_always_skipped(self, bangalore_reading):
        """Gap B (varga_confirmation) is structurally skipped because it
        needs per-bhava pillar scores Track A doesn't provide directly."""
        result = annotate_with_gap_modules(bangalore_reading)
        assert result.gap_modules["B"].available is False
        assert "pillar_score" in result.gap_modules["B"].reason


class TestPerGapAvailability:
    """Per-Gap availability and result shape for the Bangalore baseline."""

    def test_gap_a_ashtakavarga_runs(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        a = result.gap_modules["A"]
        assert a.available, f"Gap A skipped: {a.reason}"
        # AshtakavargaPredictive dataclass projects out 'sav_per_bhava' field
        assert "sav_per_bhava" in a.result

    def test_gap_d_karakamsa_runs(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        d = result.gap_modules["D"]
        assert d.available, f"Gap D skipped: {d.reason}"
        assert "arudha_lagna" in d.result
        assert "upapada_lagna" in d.result

    def test_gap_e_sensitive_points_runs_with_day_inputs(self, bangalore_reading):
        result = annotate_with_gap_modules(
            bangalore_reading, day_of_week=6, is_day_birth=True,
        )
        e = result.gap_modules["E"]
        assert e.available, f"Gap E skipped: {e.reason}"
        # SensitivePointsReport contains bhrigu_bindu + pranapada + upagrahas
        assert "bhrigu_bindu" in e.result

    def test_gap_f_avastha_runs(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        f = result.gap_modules["F"]
        assert f.available, f"Gap F skipped: {f.reason}"
        assert "baladi" in f.result
        assert "deeptadi" in f.result

    def test_gap_g_vimsopaka_runs(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        g = result.gap_modules["G"]
        assert g.available, f"Gap G skipped: {g.reason}"

    def test_gap_h_nakshatra_deep_runs(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        h = result.gap_modules["H"]
        assert h.available, f"Gap H skipped: {h.reason}"
        assert "moon_nakshatra_attributes" in h.result


class TestGracefulDegradation:
    """When inputs are missing, the annotator must skip gracefully — no
    raising — and surface a useful reason."""

    def test_no_chart_planets_skips_everything(self):
        """Reading without chart.planets → chart_built=False, all skipped."""
        result = annotate_with_gap_modules({"chart": {}, "meta": {}})
        assert result.chart_built is False
        assert result.available_count == 0
        assert result.skipped_count == 8
        for entry in result.gap_modules.values():
            assert entry.available is False
            assert entry.reason is not None

    def test_skip_reasons_are_human_readable(self):
        result = annotate_with_gap_modules({"chart": {}})
        reasons = {entry.reason for entry in result.gap_modules.values() if entry.reason}
        # All reasons should mention "chart" since that's the failure
        assert all("chart" in r.lower() for r in reasons)


class TestSerialization:
    """GapAnnotatedReading round-trips through JSON."""

    def test_envelope_roundtrip(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        as_json = json.dumps(result.model_dump(mode="json"))
        revived = GapAnnotatedReading.model_validate(json.loads(as_json))
        assert revived.chart_built == result.chart_built
        assert set(revived.gap_modules.keys()) == set(result.gap_modules.keys())

    def test_envelope_includes_integration_version(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        assert result.integration_version == "0.3.0"


class TestModuleEntryStructure:
    """GapModuleEntry has the right shape regardless of availability."""

    def test_available_entry_has_result_no_reason(self, bangalore_reading):
        result = annotate_with_gap_modules(bangalore_reading)
        gap_a = result.gap_modules["A"]
        if gap_a.available:
            assert gap_a.result is not None
            assert gap_a.reason is None

    def test_skipped_entry_has_reason_no_result(self):
        result = annotate_with_gap_modules({"chart": {}})
        for entry in result.gap_modules.values():
            assert entry.reason is not None
            assert entry.result is None
