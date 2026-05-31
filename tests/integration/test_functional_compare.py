"""Smoke tests for the functional benefic/malefic comparator.

These tests document the divergence between Track A's D-7 PVR Narasimha
Rao functional classification and Track B's flag-set system. Track B
omits Rahu/Ketu entirely; the two engines also disagree on the
benefic/malefic/neutral label for several of the classical 7 planets,
especially for dual lagnas.
"""

from __future__ import annotations

import json

import pytest

from app.integration.functional_compare import (
    FunctionalComparisonReport,
    TrackBRolesView,
    compare_functional_roles,
)


class TestComparatorMechanics:
    """Comparator runs cleanly and returns a well-formed report."""

    def test_virgo_runs_without_error(self):
        report = compare_functional_roles(6)
        assert isinstance(report, FunctionalComparisonReport)
        assert report.lagna_sign == 6

    def test_track_a_covers_nine_planets(self):
        """Track A always reports on all 9 planets including Rahu+Ketu."""
        report = compare_functional_roles(6)
        # planets_in_both + planets_only_in_a should equal 9
        assert len(report.planets_in_both) + len(report.planets_only_in_a) == 9

    def test_per_planet_length_matches_nine_planet_universe(self):
        """per_planet list always contains all 9 planet positions even
        when one side is absent. Absent planets get agrees=None."""
        report = compare_functional_roles(1)
        assert len(report.per_planet) == 9


class TestKnownAbsence:
    """Track B's functional_roles() does not emit Rahu/Ketu records.
    These must surface as None-side entries in the comparator output."""

    def test_rahu_and_ketu_are_only_in_track_a(self):
        report = compare_functional_roles(6)
        assert "Rahu" in report.planets_only_in_a
        assert "Ketu" in report.planets_only_in_a

    def test_rahu_diff_has_agrees_none(self):
        report = compare_functional_roles(6)
        rahu_diff = next(d for d in report.per_planet if d.planet == "Rahu")
        assert rahu_diff.agrees is None
        assert rahu_diff.track_b_roles is None
        assert rahu_diff.disagreement_note == "absent in Track B"


class TestProjectionRule:
    """The Track B → direction projection has a defined precedence:
    yogakaraka > benefic/malefic-flag > lagna-lord-default > neutral."""

    def test_yogakaraka_projects_to_positive(self):
        view = TrackBRolesView(
            houses_ruled=(1, 10), is_lagna_lord=False, is_yogakaraka=True,
            is_maraka=False, is_badhakesh=False,
            is_functional_benefic=False, is_functional_malefic=False,
        )
        assert view.to_direction() == "positive"

    def test_pure_malefic_flag_projects_to_negative(self):
        view = TrackBRolesView(
            houses_ruled=(8,), is_lagna_lord=False, is_yogakaraka=False,
            is_maraka=False, is_badhakesh=False,
            is_functional_benefic=False, is_functional_malefic=True,
        )
        assert view.to_direction() == "negative"

    def test_lagna_lord_alone_projects_to_positive(self):
        view = TrackBRolesView(
            houses_ruled=(1, 10), is_lagna_lord=True, is_yogakaraka=False,
            is_maraka=False, is_badhakesh=False,
            is_functional_benefic=False, is_functional_malefic=False,
        )
        assert view.to_direction() == "positive"

    def test_no_flags_projects_to_neutral(self):
        view = TrackBRolesView(
            houses_ruled=(11,), is_lagna_lord=False, is_yogakaraka=False,
            is_maraka=False, is_badhakesh=False,
            is_functional_benefic=False, is_functional_malefic=False,
        )
        assert view.to_direction() == "neutral"


class TestKnownDisagreementForVirgoLagna:
    """For Virgo lagna specifically, document the known disagreements
    between Track A (D-7 PVR) and Track B's flag system."""

    def test_virgo_has_at_least_one_classical_disagreement(self):
        """The two engines disagree on at least one classical-7 planet for
        Virgo. If this assertion starts failing, the comparator or one of
        the engines was aligned and these tests should be relaxed."""
        report = compare_functional_roles(6)
        assert report.disagreement_count >= 1, (
            "Expected at least one disagreement on Virgo lagna — if zero, "
            "doctrine alignment has happened and tests should be updated."
        )

    def test_virgo_mars_agreement_is_consistent(self):
        """Both engines classify Mars as malefic for Virgo (3L + 8L = both
        dusthana-lord rulers). This is the most robust shared verdict."""
        report = compare_functional_roles(6)
        mars_diff = next(d for d in report.per_planet if d.planet == "Mars")
        assert mars_diff.track_a_direction == "negative"
        assert mars_diff.track_b_projected_direction == "negative"
        assert mars_diff.agrees is True


class TestParametricAcrossAllLagnas:
    """Comparator must run cleanly for every Lagna 1..12 without raising."""

    @pytest.mark.parametrize("lagna_sign", list(range(1, 13)))
    def test_no_crash_for_any_lagna(self, lagna_sign: int):
        report = compare_functional_roles(lagna_sign)
        assert report.lagna_sign == lagna_sign
        # Always 9 entries in per_planet list
        assert len(report.per_planet) == 9


class TestReportSerialization:
    """FunctionalComparisonReport round-trips through JSON for downstream."""

    def test_json_roundtrip(self):
        report = compare_functional_roles(6)
        as_json = json.dumps(report.model_dump(mode="json"))
        revived = FunctionalComparisonReport.model_validate(json.loads(as_json))
        assert revived.lagna_sign == 6
        assert len(revived.per_planet) == 9
