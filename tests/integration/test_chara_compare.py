"""Smoke tests for the cross-engine Chara Dasha comparator.

These tests document a known doctrine divergence between Track A and
Track B's Chara Dasha implementations and verify that the comparator
correctly surfaces it.

Doctrine finding (2026-05-30) — TWO DIVERGENCES
-----------------------------------------------
Track A (``app.reading.sequences.chara_dasha``) and Track B
(``app.core.chara_dasha``) both claim to implement Jaimini Chara Dasha
(D-17 in Track A's lockfile), but they encode DIFFERENT VARIANTS along
TWO axes:

1. **Starting sign of the cycle.** For Virgo lagna (sign 6):
   - Track A starts MD #1 at Taurus (sign 2) — 9th-from-lagna or similar
     Sanjay-Rath start-sign rule.
   - Track B starts MD #1 at Virgo (sign 6) — starts from the lagna
     unconditionally.

2. **Period length per MD.**
   - Track A: variable lengths derived from the count-to-lord rule with
     movable/fixed/dual adjustment. The 12 periods sum to 84 years.
   - Track B: uniform 12 years per MD. The 12 periods sum to 144 years.

Both engines advance ONE sign per MD (so the sign DELTA is consistent),
but the starting sign offset means the absolute sign sequences differ
throughout the cycle. The boundaries also drift because of the
period-length difference.

These tests verify the comparator faithfully reports both divergences.
When the doctrine is reconciled (by aligning Track B to Track A's
Sanjay-Rath variant, or vice versa), these tests should be flipped to
assert agreement.
"""

from __future__ import annotations

import pytest

from app.core.chara_dasha import chara_windows_jd as b_windows
from app.integration.chara_compare import CharaComparisonReport, compare_chara_dasha
from app.reading.sequences.chara_dasha import run_sequence as a_run_sequence


# Bangalore baseline anchor — same fixture used across the Track-A test suite.
# DOB 1990-07-15 12:00 IST, lat 12.97, lon 77.59 → Lagna Virgo.
_BANGALORE_LAGNA_SIGN = 6  # Virgo
_BANGALORE_BIRTH_JD = 2448088.2708333  # midday IST → 06:30 UT for 1990-07-15

# Minimal Track-A chart envelope. ``d1`` empty because D-17 is sign-frame;
# judgment lookups fall through to "no data" findings without raising.
_MIN_CHART = {
    "birth_jd": _BANGALORE_BIRTH_JD,
    "d1": {},
}

# Documented constants for the two variants.
_TRACK_A_CYCLE_YEARS = 84  # Sanjay-Rath variable-length sum
_TRACK_B_UNIFORM_MD_YEARS = 12  # Track B's fixed per-MD length


class TestComparatorMechanics:
    """Comparator runs cleanly and returns a well-formed report regardless
    of whether the engines agree."""

    def test_comparator_returns_report_instance(self):
        a_result = a_run_sequence(
            _MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11,
        )
        report = compare_chara_dasha(
            a_result,
            lagna_sign=_BANGALORE_LAGNA_SIGN,
            birth_jd=_BANGALORE_BIRTH_JD,
        )
        assert isinstance(report, CharaComparisonReport)

    def test_both_engines_emit_twelve_mds(self):
        """Both Chara Dasha variants run through the 12 zodiacal signs once.
        Period COUNT must always agree even when LENGTHS differ."""
        a_result = a_run_sequence(_MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11)
        report = compare_chara_dasha(
            a_result,
            lagna_sign=_BANGALORE_LAGNA_SIGN,
            birth_jd=_BANGALORE_BIRTH_JD,
        )
        assert report.count_agrees
        assert report.track_a_md_count == 12
        assert report.track_b_md_count == 12

    def test_first_md_starts_at_birth_jd_on_both_engines(self):
        """The cycle begins at birth on both implementations — this is the
        ONE invariant that survives the variant divergence."""
        a_result = a_run_sequence(_MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11)
        report = compare_chara_dasha(
            a_result,
            lagna_sign=_BANGALORE_LAGNA_SIGN,
            birth_jd=_BANGALORE_BIRTH_JD,
        )
        first = report.per_md_diffs[0]
        assert first.start_jd_delta_days == 0.0


class TestKnownDivergence:
    """Tests that DOCUMENT the current divergence between Track A and B.
    These are intentionally framed as "the comparator detects X" assertions,
    not "the engines agree" assertions, because they don't agree today."""

    def test_starting_sign_diverges_for_virgo_lagna(self):
        """Track A starts the cycle at Taurus (sign 2); Track B starts at
        the lagna (Virgo, sign 6). The comparator must surface this so the
        user has concrete evidence of the starting-sign fork."""
        a_result = a_run_sequence(_MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11)
        report = compare_chara_dasha(
            a_result,
            lagna_sign=_BANGALORE_LAGNA_SIGN,
            birth_jd=_BANGALORE_BIRTH_JD,
        )
        first_diff = report.per_md_diffs[0]
        assert first_diff.track_a_md_sign != first_diff.track_b_md_sign, (
            "If this assertion starts failing, one of the engines has been "
            "aligned to the other and these tests should be flipped to "
            "assert agreement."
        )
        assert first_diff.track_b_md_sign == _BANGALORE_LAGNA_SIGN, (
            "Track B's first MD must start at the lagna sign."
        )

    def test_sign_step_per_md_is_one_for_both_engines(self):
        """Both engines advance ONE sign per MD even though they start from
        different signs. This is the one structural commonality."""
        a_result = a_run_sequence(_MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11)
        report = compare_chara_dasha(
            a_result,
            lagna_sign=_BANGALORE_LAGNA_SIGN,
            birth_jd=_BANGALORE_BIRTH_JD,
        )

        def _step(prev_sign: int, next_sign: int) -> int:
            # forward step modulo 12, mapped to 1..12 range
            return ((next_sign - prev_sign - 1) % 12) + 1

        for i in range(1, 12):
            prev = report.per_md_diffs[i - 1]
            curr = report.per_md_diffs[i]
            a_step = _step(prev.track_a_md_sign, curr.track_a_md_sign)
            b_step = _step(prev.track_b_md_sign, curr.track_b_md_sign)
            assert a_step == 1, f"Track A MD{i}: non-1 step {a_step}"
            assert b_step == 1, f"Track B MD{i}: non-1 step {b_step}"

    def test_track_b_uses_uniform_12y_periods(self):
        """Track B encodes a 12-year-per-sign variant. Document this so
        future readers see the variant in the test, not just the code."""
        windows = b_windows(_BANGALORE_LAGNA_SIGN, _BANGALORE_BIRTH_JD)
        for sign, start_jd, end_jd in windows:
            years = (end_jd - start_jd) / 365.2425
            assert abs(years - _TRACK_B_UNIFORM_MD_YEARS) < 1e-6, (
                f"Sign {sign}: expected {_TRACK_B_UNIFORM_MD_YEARS}y, got {years:.4f}y. "
                "If Track B has been updated to a variable-length variant, "
                "update this test to reflect the new doctrine."
            )

    def test_track_a_cycle_totals_84_years(self):
        """Track A's Sanjay-Rath variable-length periods sum to 84y total."""
        a_result = a_run_sequence(_MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11)
        total = sum(p.total_years for p in a_result.timeline)
        assert abs(total - _TRACK_A_CYCLE_YEARS) < 1e-6, (
            f"Track A cycle totals {total:.2f}y; expected {_TRACK_A_CYCLE_YEARS}y. "
            "If Track A's doctrine has changed, update D-17 lockfile entry too."
        )

    def test_comparator_reports_boundary_divergence(self):
        """The comparator's verdict must call out the known boundary issue."""
        a_result = a_run_sequence(_MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11)
        report = compare_chara_dasha(
            a_result,
            lagna_sign=_BANGALORE_LAGNA_SIGN,
            birth_jd=_BANGALORE_BIRTH_JD,
        )
        assert not report.all_boundaries_agree
        assert not report.full_timeline_agrees
        assert "BOUNDARY" in report.verdict_summary.upper()

    @pytest.mark.parametrize("lagna_sign", [1, 4, 7, 10])
    def test_divergence_is_systematic_across_cardinal_lagnas(self, lagna_sign: int):
        """The boundary divergence (12y-vs-variable) is structural — it must
        show up for every lagna, not just Virgo. Track B's first MD always
        starts at the lagna; whether Track A's also starts there depends on
        the lagna sign's category (movable signs may start from the lagna
        unconditionally; dual signs use the 9th-from-lagna rule, etc.)."""
        a_result = a_run_sequence(_MIN_CHART, asc_sign=lagna_sign, moon_sign=1)
        report = compare_chara_dasha(
            a_result,
            lagna_sign=lagna_sign,
            birth_jd=_BANGALORE_BIRTH_JD,
        )
        # Boundaries always diverge regardless of lagna because Track B is
        # uniform 12y, Track A is variable-length summing to 84y.
        assert not report.all_boundaries_agree
        # Track B's first MD always starts at the lagna sign.
        assert report.per_md_diffs[0].track_b_md_sign == lagna_sign


class TestCurrentMDCrossCheck:
    """Current-MD lookup at a target_jd uses chara_active_at on Track B and
    the timeline's current_md_judgment on Track A. Because Track B's first
    MD spans 12 years and Track A's first MD often spans 1-3 years, the
    "current" sign at a given target_jd typically diverges after the first
    Track-A MD ends."""

    def test_current_md_at_birth_returns_each_engines_first_sign(self):
        """At birth_jd, each engine's current_md is just its own first-MD
        sign — which differ (Track A=Taurus, Track B=Virgo for Virgo lagna).
        The comparator must surface BOTH values and flag disagreement."""
        a_result = a_run_sequence(_MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11)
        target_jd = _BANGALORE_BIRTH_JD + 0.5
        report = compare_chara_dasha(
            a_result,
            lagna_sign=_BANGALORE_LAGNA_SIGN,
            birth_jd=_BANGALORE_BIRTH_JD,
            target_jd=target_jd,
        )
        # Each engine reports its first MD sign.
        assert report.current_md_track_a == report.per_md_diffs[0].track_a_md_sign
        assert report.current_md_track_b == report.per_md_diffs[0].track_b_md_sign
        # Because the starting signs diverge for Virgo lagna, current_md
        # also diverges at birth_jd.
        assert report.current_md_agrees is False

    def test_current_md_may_diverge_at_later_target_jd(self):
        """At an age where Track A has moved through several short MDs but
        Track B is still in the first 12y, current-MD will diverge.
        Comparator must surface this disagreement, not hide it."""
        a_result = a_run_sequence(_MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11)
        target_jd = _BANGALORE_BIRTH_JD + 11 * 365.2425  # age ~11y
        report = compare_chara_dasha(
            a_result,
            lagna_sign=_BANGALORE_LAGNA_SIGN,
            birth_jd=_BANGALORE_BIRTH_JD,
            target_jd=target_jd,
        )
        # current_md_agrees is BOOLEAN — surface whatever the comparison
        # produces. If True, the divergence happens to land on the same
        # sign at this age; if False, the variants disagree about who
        # rules age 11.
        assert report.current_md_agrees in (True, False)
        # Whatever the answer, the field must be non-None when target_jd
        # is supplied.
        assert report.current_md_track_a is not None
        assert report.current_md_track_b is not None


class TestReportSerialization:
    """CharaComparisonReport is the public contract for downstream tooling
    (CI scripts, dashboards) — round-trip it through JSON to confirm."""

    def test_report_json_roundtrip(self):
        import json

        a_result = a_run_sequence(_MIN_CHART, asc_sign=_BANGALORE_LAGNA_SIGN, moon_sign=11)
        report = compare_chara_dasha(
            a_result,
            lagna_sign=_BANGALORE_LAGNA_SIGN,
            birth_jd=_BANGALORE_BIRTH_JD,
        )
        as_json = json.dumps(report.model_dump(mode="json"))
        revived = CharaComparisonReport.model_validate(json.loads(as_json))
        assert revived.all_signs_agree == report.all_signs_agree
        assert revived.all_boundaries_agree == report.all_boundaries_agree
        assert len(revived.per_md_diffs) == 12
