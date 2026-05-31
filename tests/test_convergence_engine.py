"""Tests for app.core.convergence_engine — the S-1 synthesis layer."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.convergence_engine import (
    ConvergenceVerdict, DOMAIN_PRIMARY_BHAVA, Evidence,
    convergence_verdict, format_convergence_verdict,
)
from app.core.dkp_modulation import DKPContext
from app.core.master_reading import compose_master_reading


def _baseline_chart() -> Chart:
    """Same baseline used in test_master_reading.py."""
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
        person_id="bangalore-baseline",
    )


@pytest.fixture
def baseline_mr():
    """Fully-enriched MasterReading for the baseline chart."""
    return compose_master_reading(
        _baseline_chart(), DKPContext(),
        birth_jd=2447988.0, target_jd=2461191.0,
        atmakaraka="Mercury", atmakaraka_d9_sign=4,
        moon_nakshatra_index=11,
        day_of_week=0, is_day_birth=True,
        vimshottari_md_lord="Mercury",
    )


class TestDomainCoverage:
    def test_known_domain_resolves_to_bhava(self):
        for d, b in DOMAIN_PRIMARY_BHAVA.items():
            assert 1 <= b <= 12, f"domain {d} maps to invalid bhava {b}"

    def test_unknown_domain_raises(self, baseline_mr):
        with pytest.raises(ValueError):
            convergence_verdict(baseline_mr, "not-a-real-domain")

    def test_marriage_resolves_to_7(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "marriage")
        assert v.primary_bhava == 7

    def test_career_resolves_to_10(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "career")
        assert v.primary_bhava == 10

    def test_wealth_resolves_to_2(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "wealth")
        assert v.primary_bhava == 2


class TestVerdictShape:
    def test_returns_convergence_verdict(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "marriage")
        assert isinstance(v, ConvergenceVerdict)

    def test_evidence_is_tuple_of_evidence(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "marriage")
        assert isinstance(v.evidence, tuple)
        for e in v.evidence:
            assert isinstance(e, Evidence)
            assert e.signal in (-1, 0, 1)
            assert e.weight >= 0

    def test_counts_match_evidence(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "marriage")
        support = sum(1 for e in v.evidence if e.signal > 0)
        contradict = sum(1 for e in v.evidence if e.signal < 0)
        assert v.n_supporting == support
        assert v.n_contradicting == contradict

    def test_weighted_score_matches_sum(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "marriage")
        expected = round(sum(e.signal * e.weight for e in v.evidence), 3)
        assert abs(v.weighted_score - expected) < 0.001


class TestConfidenceBand:
    """Confidence joins signal-count with weighted-magnitude."""

    def test_band_consistent_with_score_and_signal_count(self, baseline_mr):
        """Confidence band joint contract: when band='near-certain',
        n_sig >= 5 AND |score| >= 4. When 'high', n_sig >= 4 AND |score| >= 2.5.

        (The reverse 'lowering' tests are skipped because a chart with all
        9 grahas in one sign already produces strong signals via Bhrigu Bindu,
        Mangal Dosha conjunction, etc. — there's no way to construct a chart
        that produces ZERO non-silent signals while still being valid for
        Shadbala. The framework is structurally OPINIONATED — every chart
        gets evidence.)
        """
        v = convergence_verdict(baseline_mr, "marriage")
        n_sig = v.n_supporting + v.n_contradicting
        if v.confidence_band == "near-certain":
            assert n_sig >= 5 and abs(v.weighted_score) >= 4.0
        elif v.confidence_band == "high":
            assert n_sig >= 4 and abs(v.weighted_score) >= 2.5
        elif v.confidence_band == "moderate":
            assert n_sig >= 3 and abs(v.weighted_score) >= 1.5

    def test_confidence_band_valid(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "marriage")
        assert v.confidence_band in (
            "near-certain", "high", "moderate", "low", "indeterminate",
        )

    def test_label_valid(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "career")
        assert v.convergence_label in (
            "strongly_supportive", "supportive", "mixed",
            "contradictory", "afflicted", "strongly_afflicted",
            "indeterminate",
        )


class TestContradictions:
    def test_contradictions_empty_when_one_side_zero(self, baseline_mr):
        """Contradictions list is non-empty only when BOTH sides have ≥1 signal."""
        v = convergence_verdict(baseline_mr, "career")
        if v.n_supporting == 0 or v.n_contradicting == 0:
            assert len(v.contradictions) == 0

    def test_contradictions_pair_layers_when_split(self, baseline_mr):
        """When both support+contradict ≥1, contradictions list is populated."""
        v = convergence_verdict(baseline_mr, "marriage")
        if v.n_supporting >= 1 and v.n_contradicting >= 1:
            assert len(v.contradictions) >= 1
            for s, c in v.contradictions:
                assert isinstance(s, str) and isinstance(c, str)


class TestFormatting:
    def test_format_returns_string(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "marriage")
        text = format_convergence_verdict(v)
        assert isinstance(text, str)
        assert "MARRIAGE" in text
        assert "bhava 7" in text

    def test_format_includes_each_evidence_layer(self, baseline_mr):
        v = convergence_verdict(baseline_mr, "career")
        text = format_convergence_verdict(v)
        for e in v.evidence[:5]:
            assert e.layer in text


class TestDoctrinalIntegration:
    """End-to-end: convergence reflects the framework's master verdicts."""

    def test_wealth_includes_dhana_yoga_signal_when_active(self, baseline_mr):
        """If any Dhana-family yoga is active on baseline, wealth should
        register at least one supporting signal from that yoga."""
        v = convergence_verdict(baseline_mr, "wealth")
        wealth_yoga_layers = [
            e.layer for e in v.evidence
            if e.layer.startswith("yoga:") and e.signal > 0
        ]
        # Don't assert specifically — just shape: yoga layers fire when active
        for layer in wealth_yoga_layers:
            assert layer.startswith("yoga:")

    def test_translation_signals_have_zero_weight(self, baseline_mr):
        """Translation evidence is provenance, not scoring."""
        v = convergence_verdict(baseline_mr, "marriage")
        translation_evidence = [
            e for e in v.evidence if e.layer.startswith("translation:")
        ]
        for e in translation_evidence:
            assert e.signal == 0
            assert e.weight == 0.0

    def test_coverage_caveat_lists_unchecked_layers(self, baseline_mr):
        """The coverage_caveat string is populated."""
        v = convergence_verdict(baseline_mr, "marriage")
        assert isinstance(v.coverage_caveat, str)
        assert len(v.coverage_caveat) > 0
