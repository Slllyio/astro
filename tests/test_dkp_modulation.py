"""Tests for app.core.dkp_modulation — Phase 8 DKP wrapper."""
from __future__ import annotations

import pytest

from app.core.bhava_judge import judge_bhava
from app.core.chart_model import Chart
from app.core.dkp_modulation import (
    Ashrama,
    DKPContext,
    apply_dkp_modulation,
    context_completeness,
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
    )


class TestContextCompleteness:
    """Counting populated fields."""

    def test_empty_context_zero(self):
        """No fields populated → 0/12."""
        assert context_completeness(DKPContext()) == 0

    def test_full_context_twelve(self):
        """All 12 fields populated → 12/12."""
        ctx = DKPContext(
            birth_latitude=12.97, birth_longitude=77.59,
            current_residence_country="IN", climate_mahabhuta="kapha",
            birth_date_iso="1990-07-15", age_years=35.0,
            active_mundane_event="none", active_dasha_lord="Mercury",
            ashrama=Ashrama.GRIHASTHA, marital_status="married",
            profession="engineering", prashna="career direction",
        )
        assert context_completeness(ctx) == 12

    def test_partial_context_counts_only_set(self):
        """Mix of populated and None → exact count."""
        ctx = DKPContext(
            ashrama=Ashrama.GRIHASTHA, age_years=35.0, prashna="x",
        )
        assert context_completeness(ctx) == 3


class TestConfidenceLabelling:
    """Confidence label depends on completeness × verdict strength."""

    def test_low_confidence_when_completeness_under_6(self, chart):
        """<6 fields → LOW regardless of verdict label."""
        verdict = judge_bhava(chart, 7)
        mod = apply_dkp_modulation(verdict, DKPContext())
        assert mod.confidence == "LOW"

    def test_high_confidence_full_context_strong_verdict(self, chart):
        """Full context + strong/afflicted verdict → HIGH."""
        full_ctx = DKPContext(
            birth_latitude=12.97, birth_longitude=77.59,
            current_residence_country="IN", climate_mahabhuta="kapha",
            birth_date_iso="1990-07-15", age_years=35.0,
            active_mundane_event="none", active_dasha_lord="Mercury",
            ashrama=Ashrama.GRIHASTHA, marital_status="married",
            profession="engineering", prashna="career",
        )
        verdict_10 = judge_bhava(chart, 10)
        if verdict_10.label in {"strong", "afflicted"}:
            mod = apply_dkp_modulation(verdict_10, full_ctx)
            assert mod.confidence == "HIGH"


class TestReadingFocus:
    """Ashrama selects bhava reading flavour."""

    def test_brahmacharya_5h_reads_as_intellect(self, chart):
        """Student stage → 5H = intellect/study, not children."""
        v = judge_bhava(chart, 5)
        ctx = DKPContext(ashrama=Ashrama.BRAHMACHARYA)
        mod = apply_dkp_modulation(v, ctx)
        assert "intellect" in mod.bhava_reading_focus or "study" in mod.bhava_reading_focus

    def test_grihastha_5h_reads_as_children(self, chart):
        """Householder stage → 5H = children."""
        v = judge_bhava(chart, 5)
        ctx = DKPContext(ashrama=Ashrama.GRIHASTHA)
        mod = apply_dkp_modulation(v, ctx)
        assert "children" in mod.bhava_reading_focus

    def test_vanaprastha_5h_reads_as_grandchildren(self, chart):
        """Retired stage → 5H = lineage/grandchildren."""
        v = judge_bhava(chart, 5)
        ctx = DKPContext(ashrama=Ashrama.VANAPRASTHA)
        mod = apply_dkp_modulation(v, ctx)
        assert "grand" in mod.bhava_reading_focus.lower()

    def test_fallback_focus_when_no_ashrama(self, chart):
        """Without Ashrama → generic significations used."""
        v = judge_bhava(chart, 7)
        mod = apply_dkp_modulation(v, DKPContext())
        assert "spouse" in mod.bhava_reading_focus.lower()


class TestModulationNotes:
    """Context-derived notes for the Reading Composer."""

    def test_widowed_7h_notes_re_partnership(self, chart):
        """Widowed marital status on 7H → re-partnership flavour note."""
        v = judge_bhava(chart, 7)
        ctx = DKPContext(marital_status="widowed", ashrama=Ashrama.GRIHASTHA)
        mod = apply_dkp_modulation(v, ctx)
        full = " ".join(mod.modulation_notes).lower()
        assert "re-partnership" in full or "aftermath" in full

    def test_active_mundane_event_amplifies(self, chart):
        """Eclipse-in-progress → amplification note."""
        v = judge_bhava(chart, 5)
        ctx = DKPContext(active_mundane_event="eclipse_in_progress")
        mod = apply_dkp_modulation(v, ctx)
        assert any("eclipse" in n.lower() for n in mod.modulation_notes)


class TestClarifyingQuestions:
    """When context is sparse, surface specific questions."""

    def test_low_completeness_yields_questions(self, chart):
        """Empty context → clarifying questions appear."""
        v = judge_bhava(chart, 7)
        mod = apply_dkp_modulation(v, DKPContext())
        assert len(mod.clarifying_questions) > 0

    def test_questions_capped_at_4(self, chart):
        """Maximum 4 clarifying questions per verdict."""
        v = judge_bhava(chart, 4)
        mod = apply_dkp_modulation(v, DKPContext())
        assert len(mod.clarifying_questions) <= 4

    def test_full_context_no_questions(self, chart):
        """Completeness ≥9 → no clarifying questions emitted."""
        full_ctx = DKPContext(
            birth_latitude=12.97, birth_longitude=77.59,
            current_residence_country="IN", climate_mahabhuta="kapha",
            birth_date_iso="1990-07-15", age_years=35.0,
            active_mundane_event="none", active_dasha_lord="Mercury",
            ashrama=Ashrama.GRIHASTHA, marital_status="married",
            profession="engineering", prashna="career",
        )
        v = judge_bhava(chart, 7)
        mod = apply_dkp_modulation(v, full_ctx)
        assert len(mod.clarifying_questions) == 0
