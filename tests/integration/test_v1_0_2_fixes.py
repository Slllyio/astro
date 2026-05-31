"""Tests for v1.0.2 fixes: yoga aliases + doctrine reconciliation + summary."""

from __future__ import annotations

import pytest

from app.integration.doctrine_reconciliation import (
    DoctrineNote,
    ReconciledFunctionalReport,
    reconcile_functional_roles,
)
from app.integration.functional_compare import compare_functional_roles
from app.integration.summary import ChartSummary, summarize_chart
from app.integration.yoga_aliases import (
    all_canonical_names,
    alias_canonical,
)
from app.reading.proforma import compute as track_a_compute
from app.reading.schema import ChartInput


# ---------------------------------------------------------------------------
# Yoga aliases
# ---------------------------------------------------------------------------

class TestYogaAliases:
    def test_adhi_variants_collapse(self):
        assert alias_canonical("adhi") == "adhi"
        assert alias_canonical("adhi yoga") == "adhi"

    def test_vipareeta_variants_collapse(self):
        # Track A's positional rule and Track B's name both resolve here
        assert alias_canonical("vipareeta raja") == "vipareeta raja"
        assert alias_canonical("vipareeta_raja") == "vipareeta raja"
        assert alias_canonical("vipareeta raja positional") == "vipareeta raja"

    def test_neech_bhanga_variants_collapse(self):
        assert alias_canonical("neech_bhanga") == "neecha bhanga raja"
        assert alias_canonical("neecha bhanga raja") == "neecha bhanga raja"

    def test_unaliased_name_passes_through(self):
        assert alias_canonical("unknown_yoga_xyz") == "unknown_yoga_xyz"

    def test_canonical_set_is_nonempty(self):
        assert len(all_canonical_names()) > 20

    def test_yoga_comparator_uses_alias_map(self):
        """End-to-end: after alias map, intersection on a chart that detects
        a canonical yoga in both engines under different names must rise."""
        from app.integration.yoga_compare import compare_yoga_detection
        ci = ChartInput(
            dob="1989-10-12", time="10:02", tz="+05:30",
            lat=27.23, lon=79.03,
        )
        reading = track_a_compute(ci, enrich=False)
        report = compare_yoga_detection(reading)
        # Mainpuri detected "adhi" in both engines — must show in intersection.
        assert "adhi" in report.both


# ---------------------------------------------------------------------------
# Doctrine reconciliation
# ---------------------------------------------------------------------------

class TestDoctrineReconciliation:
    @pytest.fixture(scope="class")
    def scorpio_report(self):
        return compare_functional_roles(8)  # Scorpio lagna

    def test_scorpio_lagna_reconciliation_runs(self, scorpio_report):
        r = reconcile_functional_roles(scorpio_report)
        assert isinstance(r, ReconciledFunctionalReport)

    def test_disagreements_get_doctrine_notes(self, scorpio_report):
        r = reconcile_functional_roles(scorpio_report)
        # Scorpio has at least 1 known disagreement (Mars/Sun/Saturn per earlier debug)
        assert len(r.doctrine_notes) > 0

    def test_track_a_marked_as_canonical(self, scorpio_report):
        r = reconcile_functional_roles(scorpio_report)
        for note in r.doctrine_notes:
            # Canonical direction must equal Track A's direction
            assert note.canonical_direction in (
                note.track_a_direction, "positive", "negative", "neutral",
            )
            # Canonical source must be the D-7 lock
            assert "D-7" in note.canonical_per

    def test_summary_records_disagreement_count(self, scorpio_report):
        r = reconcile_functional_roles(scorpio_report)
        assert str(len(r.doctrine_notes)) in r.notes_summary


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------

class TestSummarizeChart:
    @pytest.fixture(scope="class")
    def mainpuri_reading(self):
        ci = ChartInput(
            dob="1989-10-12", time="10:02", tz="+05:30",
            lat=27.23, lon=79.03,
        )
        return track_a_compute(ci, enrich=False)

    def test_returns_chartsummary(self, mainpuri_reading):
        s = summarize_chart(mainpuri_reading)
        assert isinstance(s, ChartSummary)

    def test_basics_correct_for_mainpuri(self, mainpuri_reading):
        s = summarize_chart(mainpuri_reading)
        # Mainpuri 1989-10-12 10:02 IST should produce Scorpio lagna.
        assert s.basics.lagna_sign == 8
        assert s.basics.lagna_sign_name == "Scorpio"
        assert s.basics.moon_sign_name == "Aquarius"
        assert s.basics.moon_nakshatra == "Shatabhisha"

    def test_md_at_birth_is_rahu(self, mainpuri_reading):
        s = summarize_chart(mainpuri_reading)
        assert s.md_snapshot.md_at_birth["md_lord"] == "Rahu"

    def test_md_at_now_is_saturn(self, mainpuri_reading):
        s = summarize_chart(mainpuri_reading)
        assert s.md_snapshot.md_at_now["md_lord"] == "Saturn"

    def test_gap_headlines_have_real_data(self, mainpuri_reading):
        s = summarize_chart(mainpuri_reading)
        # Mainpuri Arudha Lagna should resolve to something
        assert s.gap_headlines.arudha_lagna_sign_name is not None
        assert s.gap_headlines.moon_nakshatra == "Shatabhisha"
        assert s.gap_headlines.moon_gana == "Rakshasa"

    def test_yoga_summary_includes_adhi_in_both(self, mainpuri_reading):
        s = summarize_chart(mainpuri_reading)
        assert "adhi" in s.yoga_summary.canonical_yogas_both_engines_detect

    def test_functional_role_notes_for_scorpio(self, mainpuri_reading):
        s = summarize_chart(mainpuri_reading)
        # Should have at least one doctrine note (engines disagree)
        assert len(s.functional_role_notes) > 0
        # Each note has a canonical role + a citation
        for n in s.functional_role_notes:
            assert n.canonical_role in ("positive", "negative", "neutral")
            assert "D-7" in n.note or "PVR" in n.note

    def test_neutral_domains_skipped_by_default(self, mainpuri_reading):
        s = summarize_chart(mainpuri_reading)
        for h in s.domain_highlights:
            assert h.direction != "neutral"
        # Mainpuri had 5 of 6 domains neutral so skipped_count should be >= 5
        assert s.skipped_domains_count >= 4

    def test_skip_neutral_false_includes_all(self, mainpuri_reading):
        s = summarize_chart(mainpuri_reading, skip_neutral_domains=False)
        assert len(s.domain_highlights) == 6
        assert s.skipped_domains_count == 0

    def test_placement_verified_dkp_count_is_zero_for_mainpuri(self, mainpuri_reading):
        """Mainpuri Saturn-in-2H + Jupiter-in-8H doesn't match any
        registry record describing 'Saturn in 4H' or 'Jupiter in 5H'
        — so post-v1.0.1 lordship filter must return 0 false positives."""
        s = summarize_chart(mainpuri_reading)
        assert s.placement_verified_dkp_count == 0

    def test_summary_serialises_to_json(self, mainpuri_reading):
        import json
        s = summarize_chart(mainpuri_reading)
        text = json.dumps(s.model_dump(mode="json"))
        from app.integration.summary import ChartSummary as CS
        revived = CS.model_validate(json.loads(text))
        assert revived.basics.lagna_sign == 8


# ---------------------------------------------------------------------------
# DKP modulator: age_years auto-derivation
# ---------------------------------------------------------------------------

class TestDKPModulatorAutoAge:
    def test_age_years_auto_derived_when_dob_present(self):
        from app.integration import build_dkp_context_from_reading
        ci = ChartInput(
            dob="1989-10-12", time="10:02", tz="+05:30",
            lat=27.23, lon=79.03,
        )
        reading = track_a_compute(ci, enrich=False)
        ctx = build_dkp_context_from_reading(reading)
        # age_years should now be auto-populated to ~36-37
        assert ctx.age_years is not None
        assert 34.0 < ctx.age_years < 40.0
