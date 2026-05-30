"""Tests for ``app.reading.sequences.career_executive``.

Doctrine source: notebook NotebookLM proforma — "The Varga System
Handbook: Blueprint for Professional Destiny" (Executive Consulting
Methodology). The sequence runs 4 named checks in fixed order and
emits a :class:`CareerExecutiveResult` whose ``steps`` dict must match
:data:`CAREER_EXECUTIVE_KEYS` exactly.

Bangalore baseline (1990-07-15 12:00 IST / 12.97 N, 77.59 E) is the
canonical fixture (CLAUDE.md test-pinning policy). 1990-07-15 was a
Sunday — ``datetime.date(1990,7,15).weekday() == 6`` under Mon=0
convention, but ``app.core.panchanga`` uses 0=Sunday so we pass
``weekday=0``.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Bangalore baseline fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def baseline_inputs(bangalore_chart) -> dict:
    md = bangalore_chart["current_mahadasha"]
    return {
        "chart": bangalore_chart,
        "asc_sign": bangalore_chart["ascendant"]["sign"],
        "moon_sign": bangalore_chart["d1"]["Moon"]["sign"],
        "current_md_lord": md["mahadasha_lord"],
        "birth_jd": bangalore_chart["birth_jd"],
        "birth_lat": 12.97,
        "birth_lon": 77.59,
        "is_daytime": True,
        "weekday": 0,  # 0=Sunday convention (panchanga)
    }


# ---------------------------------------------------------------------------
# Public-API + structural conformance
# ---------------------------------------------------------------------------


class TestRunSequence:

    def test_returns_career_executive_result(self, baseline_inputs):
        from app.reading.schema import CareerExecutiveResult
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        assert isinstance(result, CareerExecutiveResult)

    def test_steps_dict_keys_match_enum(self, baseline_inputs):
        from app.reading.schema import CAREER_EXECUTIVE_KEYS
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        assert set(result.steps.keys()) == set(CAREER_EXECUTIVE_KEYS)

    def test_all_steps_are_findings(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        for key, finding in result.steps.items():
            assert isinstance(finding, Finding), f"step {key} not a Finding"

    def test_overall_verdict_is_finding(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        assert isinstance(result.overall_verdict, Finding)

    def test_finding_ids_use_sequence_grammar(self, baseline_inputs):
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        for key, finding in result.steps.items():
            assert finding.id.startswith("seq_2."), (
                f"step {key} id {finding.id!r} must start with 'seq_2.'"
            )
        assert result.overall_verdict.id.startswith("seq_2.")

    def test_source_sequence_tagged(self, baseline_inputs):
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        for finding in result.steps.values():
            assert finding.source_sequence == "career_executive"


class TestPerStepDelegation:

    def test_vargottama_amatya_karaka_mentions_amk(self, baseline_inputs):
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        evidence = " ".join(result.steps["vargottama_amatya_karaka"].evidence)
        # Either AmK label or "amatya" / "vargottama" referenced.
        assert (
            "amatyakaraka" in evidence.lower()
            or "amatya" in evidence.lower()
        )

    def test_gandanta_knots_step_emits(self, baseline_inputs):
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        evidence = " ".join(result.steps["gandanta_knots"].evidence)
        assert "gandanta" in evidence.lower() or "Gandanta" in evidence

    def test_vimsopaka_strength_mentions_score(self, baseline_inputs):
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        evidence = " ".join(result.steps["vimsopaka_strength"].evidence)
        assert "vimsopaka" in evidence.lower() or "score" in evidence.lower()

    def test_gulika_saturn_bottlenecks_mentions_saturn_or_gulika(
        self, baseline_inputs,
    ):
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        evidence = " ".join(
            result.steps["gulika_saturn_bottlenecks"].evidence
        )
        assert (
            "saturn" in evidence.lower()
            or "gulika" in evidence.lower()
        )


class TestVimsopakaGate:
    """Step 3's Vimsopaka score (range [0, 20]) must appear in evidence."""

    def test_vimsopaka_score_in_bounds(self, baseline_inputs):
        from app.reading.sequences.career_executive import run_sequence

        result = run_sequence(**baseline_inputs)
        score_line = next(
            (
                line
                for line in result.steps["vimsopaka_strength"].evidence
                if line.startswith("md_lord_vimsopaka_score=")
            ),
            None,
        )
        assert score_line is not None, "vimsopaka_strength must emit md_lord_vimsopaka_score=N"
        score = float(score_line.split("=", 1)[1])
        assert 0.0 <= score <= 20.0
