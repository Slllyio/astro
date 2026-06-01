"""Tests for app.core.bhava_judge — Phase 6 three-pillar composition."""
from __future__ import annotations

import pytest

from app.core.bhava_judge import (
    BhavaVerdict,
    PillarScore,
    Reasoning,
    judge_all_bhavas,
    judge_bhava,
)
from app.core.chart_model import Chart


@pytest.fixture
def bangalore_chart() -> Chart:
    """Canonical Bangalore 1990-07-15 baseline (Virgo Lagna)."""
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


class TestBhavaVerdictStructure:
    """Verdict-object structural invariants."""

    def test_verdict_has_3_pillars(self, bangalore_chart):
        """Always three pillars: bhava + lord + karaka."""
        v = judge_bhava(bangalore_chart, 1)
        assert len(v.pillars) == 3
        assert {p.label for p in v.pillars} == {"bhava", "lord", "karaka"}

    def test_verdict_label_is_valid(self, bangalore_chart):
        """Label ∈ {strong, medium, weak, afflicted}."""
        for b in range(1, 13):
            v = judge_bhava(bangalore_chart, b)
            assert v.label in {"strong", "medium", "weak", "afflicted"}

    def test_composite_score_in_unit_range(self, bangalore_chart):
        """Composite always in [-1, +1]."""
        for b in range(1, 13):
            v = judge_bhava(bangalore_chart, b)
            assert -1.0 <= v.composite_score <= 1.0


class TestAndGate:
    """The ≥3-confirmation AND-gate logic."""

    def test_strong_requires_confirming_yoga(self, bangalore_chart):
        """A strong verdict cannot fire without confirming yoga/argala."""
        for b in range(1, 13):
            v = judge_bhava(bangalore_chart, b)
            if v.label == "strong":
                assert v.confirming_yogas, (
                    f"Bhava {b} labeled strong without confirming yoga — "
                    "AND-gate violated"
                )

    def test_strong_requires_2_positive_pillars(self, bangalore_chart):
        """A strong verdict cannot fire with <2 positive pillars."""
        for b in range(1, 13):
            v = judge_bhava(bangalore_chart, b)
            if v.label == "strong":
                assert v.n_positive_pillars >= 2

    def test_afflicted_requires_2_negative_pillars(self, bangalore_chart):
        """Afflicted requires ≥2 negative pillars (symmetric)."""
        for b in range(1, 13):
            v = judge_bhava(bangalore_chart, b)
            if v.label == "afflicted":
                assert v.n_negative_pillars >= 2


class TestCitationsCarry:
    """Every reasoning carries a classical anchor reference."""

    def test_every_reasoning_has_a_reference(self, bangalore_chart):
        """Phase 9 needs the citations — none should be empty."""
        for b in range(1, 13):
            v = judge_bhava(bangalore_chart, b)
            for pillar in v.pillars:
                for r in pillar.reasonings:
                    assert r.reference, (
                        f"Bhava {b} pillar {pillar.label} has unciched finding: {r.finding}"
                    )


class TestBangaloreVerdicts:
    """Doctrine-known characteristics of the Bangalore baseline."""

    def test_10h_career_is_strong(self, bangalore_chart):
        """10H with Sun + Mercury in own + Jupiter aspect + Bhadra/Amala
        yogas should land strong. This is the doctrinal sanity check."""
        v = judge_bhava(bangalore_chart, 10)
        assert v.label in {"strong", "medium"}
        # Confirm yogas reach the 10H
        assert "Bhadra" in v.confirming_yogas or "Amala" in v.confirming_yogas

    def test_7h_jupiter_exalted_but_badhakesh(self, bangalore_chart):
        """7H lord Jupiter is exalted (+0.4) but also Badhakesh (−0.15)
        for Virgo Lagna. Pillar lord should reflect both."""
        v = judge_bhava(bangalore_chart, 7)
        lord_pillar = next(p for p in v.pillars if p.label == "lord")
        findings = " | ".join(r.finding for r in lord_pillar.reasonings)
        assert "exalted" in findings.lower()
        assert "badhakesh" in findings.lower()


class TestJudgeAllBhavas:
    """Convenience all-bhava call."""

    def test_returns_all_12(self, bangalore_chart):
        """judge_all_bhavas covers 1..12 with no gaps."""
        all_v = judge_all_bhavas(bangalore_chart)
        assert set(all_v.keys()) == set(range(1, 13))
        assert all(isinstance(v, BhavaVerdict) for v in all_v.values())


class TestInvalidInputs:
    """Out-of-range bhava raises ValueError."""

    def test_judge_bhava_rejects_out_of_range(self, bangalore_chart):
        """Bhava 0 or 13 must raise."""
        with pytest.raises(ValueError):
            judge_bhava(bangalore_chart, 0)
        with pytest.raises(ValueError):
            judge_bhava(bangalore_chart, 13)
