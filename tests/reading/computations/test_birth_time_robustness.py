"""Tests for ``app.reading.computations.birth_time_robustness`` (Tier-3).

Phase 6 Wave B — birth-time sensitivity scoring.

Discipline asserted by this test file (Spec Section 14):

1.  **Methodology docstring block** — Section 14 mandate.
2.  **Direct ``_run_core_pipeline`` import** — the module MUST call
    ``app.reading.proforma._run_core_pipeline`` directly to avoid
    infinite recursion through ``compute(..., enrich=True)``.
3.  **Recursion-bounded** — running the scorer must terminate within
    a small bounded budget (here, 5 sub-runs are expected: base +
    ±5min + ±10min).
4.  **RobustnessScore numerics** — ``flip_rate_at_5min`` and
    ``flip_rate_at_10min`` are raw numerics in [0.0, 1.0].
5.  **EXPERIMENTAL flag** — the ``sensitive_to_birth_time`` boolean is
    labelled EXPERIMENTAL until a methodology is published.
6.  **Lazy-import discipline** — no heavy ML stack at module top.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bangalore_chart_input():
    """Canonical Bangalore baseline ChartInput (per CLAUDE.md)."""
    from app.reading.schema import ChartInput

    return ChartInput(
        dob="1990-07-15",
        time="12:00",
        tz="+05:30",
        lat=12.97,
        lon=77.59,
    )


@pytest.fixture
def make_finding():
    """Factory for a minimal Finding."""
    from app.reading.schema import ConfidenceScore, Finding

    def _make(
        *,
        id: str,
        direction: str = "positive",
    ) -> Finding:
        return Finding(
            id=id,
            rule="placeholder",
            source_sequence=None,
            classification="trigger",
            direction=direction,  # type: ignore[arg-type]
            verdict="placeholder",
            evidence=[],
            confidence=ConfidenceScore(
                score=0.5,
                votes={"house": True, "lord": False, "karaka": True},
                band="medium",
            ),
        )

    return _make


@pytest.fixture
def base_output_with_findings(make_finding):
    """A reading_output-shaped dict with a known finding-by-id index."""

    def _make(finding_directions: dict[str, str]) -> dict:
        findings = []
        for fid, direction in finding_directions.items():
            f = make_finding(id=fid, direction=direction)
            findings.append(f.model_dump(mode="json"))
        return {"_all_findings": findings}

    return _make


# ---------------------------------------------------------------------------
# Spec Section 14 — methodology block
# ---------------------------------------------------------------------------


class TestMethodologyBlock:
    """Auditable docstring block required by Spec Section 14."""

    def test_module_has_methodology_block(self):
        from app.reading.computations import birth_time_robustness

        doc = birth_time_robustness.__doc__ or ""
        assert "Methodology:" in doc

    def test_module_publishes_prediction_trap_declaration(self):
        from app.reading.computations import birth_time_robustness

        doc = birth_time_robustness.__doc__ or ""
        assert "Prediction-trap declaration:" in doc

    def test_module_publishes_famous_chart_anti_contamination(self):
        from app.reading.computations import birth_time_robustness

        doc = birth_time_robustness.__doc__ or ""
        assert "Famous-chart anti-contamination:" in doc

    def test_module_declares_experimental_status_of_boolean(self):
        """``sensitive_to_birth_time`` is EXPERIMENTAL until a methodology lands."""
        from app.reading.computations import birth_time_robustness

        doc = birth_time_robustness.__doc__ or ""
        assert "EXPERIMENTAL" in doc

    def test_module_declares_uses_private_pipeline_to_avoid_recursion(self):
        """``_run_core_pipeline`` is the only safe entry point for nudge runs."""
        from app.reading.computations import birth_time_robustness

        doc = birth_time_robustness.__doc__ or ""
        assert "_run_core_pipeline" in doc
        assert "recursion" in doc.lower()


# ---------------------------------------------------------------------------
# Time-shift helper
# ---------------------------------------------------------------------------


class TestShiftHelper:
    """The local ``_shift_chart_input`` helper preserves the chart envelope."""

    def test_shift_plus_5_minutes(self, bangalore_chart_input):
        from app.reading.computations.birth_time_robustness import (
            _shift_chart_input,
        )

        shifted = _shift_chart_input(bangalore_chart_input, 5)
        assert shifted.dob == "1990-07-15"
        assert shifted.time == "12:05"
        assert shifted.tz == bangalore_chart_input.tz
        assert shifted.lat == bangalore_chart_input.lat
        assert shifted.lon == bangalore_chart_input.lon

    def test_shift_minus_10_minutes(self, bangalore_chart_input):
        from app.reading.computations.birth_time_robustness import (
            _shift_chart_input,
        )

        shifted = _shift_chart_input(bangalore_chart_input, -10)
        assert shifted.time == "11:50"

    def test_shift_across_midnight(self):
        from app.reading.computations.birth_time_robustness import (
            _shift_chart_input,
        )
        from app.reading.schema import ChartInput

        ci = ChartInput(
            dob="1990-07-15",
            time="00:03",
            tz="+05:30",
            lat=12.97,
            lon=77.59,
        )
        shifted = _shift_chart_input(ci, -5)
        # 00:03 - 5min = 23:58 the previous day
        assert shifted.dob == "1990-07-14"
        assert shifted.time == "23:58"


# ---------------------------------------------------------------------------
# Recursion-safety: uses _run_core_pipeline, terminates within bounded budget
# ---------------------------------------------------------------------------


class TestRecursionSafety:
    """The scorer must call ``_run_core_pipeline``, not ``compute``."""

    def test_score_robustness_does_not_call_compute(
        self, bangalore_chart_input, base_output_with_findings, monkeypatch
    ):
        """The module must NOT trigger Tier-3 enrichment in its nudge runs.

        We monkeypatch ``compute`` to fail loudly; if the robustness
        scorer accidentally calls ``compute`` (which would re-enter
        Tier-3 and recurse), the test fails immediately.
        """
        from app.reading import proforma
        from app.reading.computations import birth_time_robustness

        def _bomb(*args, **kwargs):
            raise AssertionError(
                "birth_time_robustness must call _run_core_pipeline, "
                "not compute, to avoid recursion."
            )

        monkeypatch.setattr(proforma, "compute", _bomb)
        # Should run without invoking ``compute`` at all.
        out = birth_time_robustness.score_robustness(
            bangalore_chart_input,
            base_output_with_findings({"domain.career.10l_strong": "positive"}),
        )
        assert isinstance(out, list)

    def test_score_robustness_runs_bounded_number_of_core_pipelines(
        self, bangalore_chart_input, base_output_with_findings, monkeypatch
    ):
        """The scorer must call ``_run_core_pipeline`` a small, bounded
        number of times (base + ±5min + ±10min = up to 5 invocations).

        Anything beyond that range would indicate a runaway loop or
        accidental recursion.
        """
        from app.reading import proforma
        from app.reading.computations import birth_time_robustness

        call_count = {"n": 0}
        real_core = proforma._run_core_pipeline

        def _counting_core(chart_input):
            call_count["n"] += 1
            # Return a minimal valid output: each nudge has a finding with the
            # same id but possibly a different direction, mocked here as
            # always "positive" (matches base).
            return real_core(chart_input)

        monkeypatch.setattr(
            birth_time_robustness,
            "_run_core_pipeline",
            _counting_core,
        )
        birth_time_robustness.score_robustness(
            bangalore_chart_input,
            base_output_with_findings({"domain.career.10l_strong": "positive"}),
        )
        # At most 5 sub-runs (base + 4 nudges); base itself may be re-run
        # by the helper for parity which is fine.
        assert call_count["n"] <= 5, (
            f"_run_core_pipeline invoked {call_count['n']} times — "
            "indicates runaway loop or accidental recursion."
        )


# ---------------------------------------------------------------------------
# RobustnessScore numerics
# ---------------------------------------------------------------------------


class TestRobustnessScoreNumerics:
    """flip_rate values are raw numerics in [0.0, 1.0]."""

    def test_score_robustness_returns_findings_with_robustness(
        self, bangalore_chart_input, base_output_with_findings, monkeypatch
    ):
        from app.reading.computations import birth_time_robustness
        from app.reading.schema import RobustnessScore

        # Make every nudge run yield the same direction (no flips).
        def _mock_core(chart_input):
            return {
                "_all_findings": [
                    {
                        "id": "domain.career.10l_strong",
                        "direction": "positive",
                    }
                ],
            }

        monkeypatch.setattr(
            birth_time_robustness, "_run_core_pipeline", _mock_core
        )
        out = birth_time_robustness.score_robustness(
            bangalore_chart_input,
            base_output_with_findings({"domain.career.10l_strong": "positive"}),
        )
        assert len(out) >= 1
        finding = out[0]
        assert finding.robustness is not None
        assert isinstance(finding.robustness, RobustnessScore)
        assert 0.0 <= finding.robustness.flip_rate_at_5min <= 1.0
        assert 0.0 <= finding.robustness.flip_rate_at_10min <= 1.0

    def test_no_flips_yields_zero_flip_rate(
        self, bangalore_chart_input, base_output_with_findings, monkeypatch
    ):
        """If every nudge agrees with base, flip_rates are 0.0."""
        from app.reading.computations import birth_time_robustness

        def _mock_core(chart_input):
            return {
                "_all_findings": [
                    {"id": "domain.career.10l_strong", "direction": "positive"},
                ],
            }

        monkeypatch.setattr(
            birth_time_robustness, "_run_core_pipeline", _mock_core
        )
        out = birth_time_robustness.score_robustness(
            bangalore_chart_input,
            base_output_with_findings({"domain.career.10l_strong": "positive"}),
        )
        finding = out[0]
        assert finding.robustness.flip_rate_at_5min == 0.0
        assert finding.robustness.flip_rate_at_10min == 0.0
        assert finding.robustness.sensitive_to_birth_time is False

    def test_full_flips_yields_one_flip_rate(
        self, bangalore_chart_input, base_output_with_findings, monkeypatch
    ):
        """If every nudge disagrees with base, flip_rates are 1.0."""
        from app.reading.computations import birth_time_robustness

        def _mock_core(chart_input):
            return {
                "_all_findings": [
                    {"id": "domain.career.10l_strong", "direction": "negative"},
                ],
            }

        monkeypatch.setattr(
            birth_time_robustness, "_run_core_pipeline", _mock_core
        )
        out = birth_time_robustness.score_robustness(
            bangalore_chart_input,
            base_output_with_findings({"domain.career.10l_strong": "positive"}),
        )
        finding = out[0]
        assert finding.robustness.flip_rate_at_5min == 1.0
        assert finding.robustness.flip_rate_at_10min == 1.0
        assert finding.robustness.sensitive_to_birth_time is True


# ---------------------------------------------------------------------------
# Empty / pass-through behaviour
# ---------------------------------------------------------------------------


class TestEmptyInputs:
    """The scorer handles empty / minimal inputs gracefully."""

    def test_empty_findings_returns_empty_list(
        self, bangalore_chart_input, monkeypatch
    ):
        from app.reading.computations import birth_time_robustness

        def _mock_core(chart_input):
            return {"_all_findings": []}

        monkeypatch.setattr(
            birth_time_robustness, "_run_core_pipeline", _mock_core
        )
        out = birth_time_robustness.score_robustness(
            bangalore_chart_input, {"_all_findings": []}
        )
        assert out == []


# ---------------------------------------------------------------------------
# Lazy-import regression
# ---------------------------------------------------------------------------


class TestLazyImportDiscipline:
    """No sentence_transformers / torch / knowledge_search at module top."""

    def test_sentence_transformers_not_imported_at_module_top(self):
        import inspect

        from app.reading.computations import birth_time_robustness

        src = inspect.getsource(birth_time_robustness)
        lines = src.splitlines()
        top_lines: list[str] = []
        in_doc = False
        doc_closed = False
        for line in lines:
            stripped = line.strip()
            if not doc_closed:
                if stripped.startswith('"""') and not in_doc:
                    in_doc = True
                    if stripped.endswith('"""') and len(stripped) > 3:
                        in_doc = False
                        doc_closed = True
                    continue
                if in_doc and stripped.endswith('"""'):
                    in_doc = False
                    doc_closed = True
                    continue
                if in_doc:
                    continue
                doc_closed = True
            if stripped.startswith(("def ", "class ", "async def ")):
                break
            top_lines.append(line)
        top_src = "\n".join(top_lines)
        assert "sentence_transformers" not in top_src
        assert "from app.medini.services" not in top_src
