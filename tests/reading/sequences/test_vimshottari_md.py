"""Tests for ``app.reading.sequences.vimshottari_md``.

Doctrine source: notebook NotebookLM proforma — "How to Judge a
Mahadasha" by Anil Kumar Jain. The sequence runs **19 named checks**
in fixed order (see D-14 in ``docs/doctrine-decisions.md``) and emits
a :class:`VimshottariMDResult` containing a ``timeline`` list of
:class:`MDJudgment` and the singled-out ``current_md_judgment``.

Bangalore baseline (1990-07-15 12:00 IST / 12.97 N, 77.59 E) is the
canonical fixture per CLAUDE.md test-pinning policy. The baseline
chart is in **Mercury MD** active at the birth date (start 1978-03-26,
end 1995-03-26).
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
    return {
        "chart": bangalore_chart,
        "asc_sign": bangalore_chart["ascendant"]["sign"],
        "moon_sign": bangalore_chart["d1"]["Moon"]["sign"],
    }


# ---------------------------------------------------------------------------
# Public API + structural conformance
# ---------------------------------------------------------------------------


class TestRunSequence:

    def test_returns_vimshottari_md_result(self, baseline_inputs):
        from app.reading.sequences.vimshottari_md import (
            VimshottariMDResult, run_sequence,
        )

        result = run_sequence(**baseline_inputs)
        assert isinstance(result, VimshottariMDResult)

    def test_current_md_judgment_present(self, baseline_inputs):
        from app.reading.schema import MDJudgment
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        assert isinstance(result.current_md_judgment, MDJudgment)
        assert result.current_md_judgment.is_current is True

    def test_timeline_nonempty(self, baseline_inputs):
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        assert len(result.timeline) >= 1

    def test_timeline_contains_current(self, baseline_inputs):
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        currents = [j for j in result.timeline if j.is_current]
        assert len(currents) == 1, "exactly one judgment may be is_current=True"

    def test_all_judgments_have_19_check_keys(self, baseline_inputs):
        from app.reading.schema import MD_CHECK_KEYS
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        expected = set(MD_CHECK_KEYS)
        for j in result.timeline:
            assert set(j.checks.keys()) == expected, (
                f"MD={j.md_lord} checks mismatch: "
                f"missing={expected - set(j.checks.keys())}, "
                f"extra={set(j.checks.keys()) - expected}"
            )

    def test_each_check_is_finding(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        for key, finding in result.current_md_judgment.checks.items():
            assert isinstance(finding, Finding), (
                f"check {key} is not a Finding instance"
            )

    def test_overall_verdict_is_finding(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        assert isinstance(result.current_md_judgment.overall_verdict, Finding)

    def test_check_finding_ids_use_seq_5_grammar(self, baseline_inputs):
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        for key, finding in result.current_md_judgment.checks.items():
            assert finding.id.startswith("seq_5."), (
                f"check {key} id {finding.id!r} must start with 'seq_5.'"
            )

    def test_source_sequence_tagged(self, baseline_inputs):
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        for finding in result.current_md_judgment.checks.values():
            assert finding.source_sequence == "vimshottari_md"


class TestCurrentMDLord:
    """The Bangalore baseline lands in Mercury MD per ephemeris."""

    def test_current_md_lord_is_mercury(self, baseline_inputs):
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        assert result.current_md_judgment.md_lord == "Mercury"


class TestDateFields:

    def test_iso_dates_present(self, baseline_inputs):
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        cm = result.current_md_judgment
        assert len(cm.start_date) == 10 and cm.start_date.count("-") == 2
        assert len(cm.end_date) == 10 and cm.end_date.count("-") == 2

    def test_jd_dates_floats(self, baseline_inputs):
        from app.reading.sequences.vimshottari_md import run_sequence

        result = run_sequence(**baseline_inputs)
        cm = result.current_md_judgment
        assert isinstance(cm.start_jd, float)
        assert isinstance(cm.end_jd, float)
        assert cm.end_jd > cm.start_jd
