"""Tests for app.llm.reading_prose — Phase 9.5 prose bridge."""
from __future__ import annotations

import pytest

# The `Citation` API (and `Interpretation.citations`) is in-flight round8 work
# not yet present on this branch; skip cleanly until it lands rather than
# erroring on collection.
try:
    from app.llm.interpreter import Citation as _Citation  # noqa: F401
except ImportError:
    pytest.skip(
        "app.llm.interpreter.Citation not present on this branch",
        allow_module_level=True,
    )

from app.core.chart_model import Chart
from app.core.dkp_modulation import Ashrama, DKPContext
from app.core.reading_composer import compose_reading
from app.llm.interpreter import Citation, Interpretation, LLMClient
from app.llm.reading_prose import (
    deterministic_bhava_section,
    deterministic_summary,
    interpret_bhava,
    interpret_reading,
)


@pytest.fixture
def chart() -> Chart:
    return Chart(
        asc_sign=6, asc_lon=173.99,
        planet_signs={"Sun": 3, "Moon": 12, "Mars": 4, "Mercury": 3,
                      "Jupiter": 4, "Venus": 4, "Saturn": 9,
                      "Rahu": 12, "Ketu": 6},
        planet_houses={"Sun": 10, "Moon": 7, "Mars": 11, "Mercury": 10,
                       "Jupiter": 11, "Venus": 11, "Saturn": 4,
                       "Rahu": 7, "Ketu": 1},
        planet_lons={"Sun": 88.6, "Moon": 351.0, "Mars": 120.5,
                     "Mercury": 95.2, "Jupiter": 101.8, "Venus": 102.0,
                     "Saturn": 268.4, "Rahu": 348.5, "Ketu": 168.5},
        person_id="test-baseline",
    )


@pytest.fixture
def full_ctx() -> DKPContext:
    return DKPContext(
        birth_latitude=12.97, birth_longitude=77.59,
        current_residence_country="IN", climate_mahabhuta="kapha",
        birth_date_iso="1990-07-15", age_years=35.0,
        active_mundane_event="none", active_dasha_lord="Mercury",
        ashrama=Ashrama.GRIHASTHA, marital_status="married",
        profession="engineering", prashna="career",
    )


class FailingClient:
    """Stub LLM client that always raises — exercises fallback path."""
    def complete(self, prompt: str) -> str:
        raise RuntimeError("simulated LLM failure")


class ScriptedClient:
    """Stub client returning fixed text — tests llm-source branch."""
    model = "test-model"
    def complete(self, prompt: str) -> str:
        return "Scripted LLM rephrasing of the framework findings."


class TestDeterministicBhavaSection:
    """Fallback prose composition from ReadingClaim fields."""

    def test_returns_interpretation(self, chart, full_ctx):
        """Always returns an Interpretation typed object."""
        reading = compose_reading(chart, full_ctx)
        result = deterministic_bhava_section(reading, 7)
        assert isinstance(result, Interpretation)

    def test_text_includes_bhava_name(self, chart, full_ctx):
        """Output mentions the Sanskrit/English bhava name."""
        reading = compose_reading(chart, full_ctx)
        result = deterministic_bhava_section(reading, 7)
        assert "Yuvati" in result.text or "spouse" in result.text.lower()

    def test_section_field_matches_bhava_number(self, chart, full_ctx):
        """The Interpretation.section field carries bhava number as str."""
        reading = compose_reading(chart, full_ctx)
        for b in (1, 5, 10):
            result = deterministic_bhava_section(reading, b)
            assert result.section == str(b)

    def test_source_is_fallback(self, chart, full_ctx):
        """Deterministic path always marks source='fallback'."""
        reading = compose_reading(chart, full_ctx)
        assert deterministic_bhava_section(reading, 1).source == "fallback"

    def test_citations_correspond_to_claim_citations(self, chart, full_ctx):
        """Number of returned citations == number of claim citations."""
        reading = compose_reading(chart, full_ctx)
        claim = reading.bhava_claims[7]
        result = deterministic_bhava_section(reading, 7)
        assert len(result.citations) == len(claim.citations)
        assert all(isinstance(c, Citation) for c in result.citations)

    def test_missing_bhava_returns_placeholder(self, chart, full_ctx):
        """Calling for a bhava outside the claims dict returns placeholder."""
        reading = compose_reading(chart, full_ctx)
        # Inject a bhava number not actually rendered? compose_reading
        # always covers 1..12, so this exercises the guard rail.
        from dataclasses import replace
        empty_reading = replace(reading, bhava_claims={})
        result = deterministic_bhava_section(empty_reading, 7)
        assert "No claim" in result.text


class TestDeterministicSummary:
    """Chart-level summary composition."""

    def test_summary_mentions_lagna(self, chart, full_ctx):
        """Output mentions the Lagna sign."""
        reading = compose_reading(chart, full_ctx)
        result = deterministic_summary(reading)
        assert "Lagna" in result.text

    def test_summary_mentions_strongest_and_weakest(self, chart, full_ctx):
        """Output mentions strongest + weakest planets."""
        reading = compose_reading(chart, full_ctx)
        result = deterministic_summary(reading)
        assert reading.strongest_planet in result.text
        assert reading.weakest_planet in result.text

    def test_summary_lists_active_yogas(self, chart, full_ctx):
        """Each active yoga name appears in the summary text."""
        reading = compose_reading(chart, full_ctx)
        result = deterministic_summary(reading)
        for y in reading.active_yogas:
            assert y.name in result.text


class TestInterpretBhava:
    """LLM path with fallback when client unavailable or raising."""

    def test_no_client_returns_fallback(self, chart, full_ctx):
        """No client → deterministic path used."""
        reading = compose_reading(chart, full_ctx)
        result = interpret_bhava(reading, 7, client=None)
        assert result.source == "fallback"

    def test_failing_client_falls_back(self, chart, full_ctx):
        """LLM exception → deterministic path used."""
        reading = compose_reading(chart, full_ctx)
        result = interpret_bhava(reading, 7, client=FailingClient())
        assert result.source == "fallback"

    def test_scripted_client_returns_llm_text(self, chart, full_ctx):
        """LLM client returns text → source='llm', text matches."""
        reading = compose_reading(chart, full_ctx)
        result = interpret_bhava(reading, 7, client=ScriptedClient())
        assert result.source == "llm"
        assert "Scripted LLM" in result.text
        assert result.model == "test-model"


class TestInterpretReading:
    """Full-chart rendering produces 13 Interpretation objects."""

    def test_returns_13_interpretations(self, chart, full_ctx):
        """1 summary + 12 bhava sections = 13."""
        reading = compose_reading(chart, full_ctx)
        out = interpret_reading(reading)
        assert len(out) == 13
        assert out[0].mode == "summary"
        assert all(out[i].mode == "section" for i in range(1, 13))

    def test_sections_cover_all_12_bhavas(self, chart, full_ctx):
        """Section interpretations carry sections '1'..'12'."""
        reading = compose_reading(chart, full_ctx)
        out = interpret_reading(reading)
        section_values = [o.section for o in out[1:]]
        assert section_values == [str(b) for b in range(1, 13)]
