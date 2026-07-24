"""Tests for the unified detailed report composer (report + honesty overlay)."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report, to_markdown

# Canonical pin (CLAUDE.md): Bangalore 1990-07-15 12:00 IST -> Virgo Lagna, purna longevity.
_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def markdown(report):
    return to_markdown(report)


class TestDetailedReport:
    def test_covers_all_twelve_houses(self, report):
        """Calibration is attached for every one of the 12 bhavas."""
        assert set(report.calibration) == set(range(1, 13))
        assert all(hr.entries for hr in report.calibration.values())

    def test_canonical_lagna_is_virgo(self, report):
        """The pinned Bangalore chart rises in Virgo (astronomical regression guard)."""
        assert report.synthesis.lagna == "Virgo"

    def test_longevity_is_positive_and_classed(self, report):
        """Numeric Ayurdaya yields a positive span and a named longevity class."""
        assert report.longevity_years > 0
        assert report.longevity_class in {"alpa", "madhya", "purna"}

    def test_markdown_has_all_sections(self, markdown):
        """The document carries every top-level section header."""
        for header in ("# Detailed reading", "## Chart signature", "## Longevity",
                       "## House-by-house reading", "### House 1 ", "### House 12 "):
            assert header in markdown

    def test_inverted_channel_is_flagged(self, markdown):
        """H12 incarceration is an atlas-proven inverted channel and must warn."""
        assert "INVERTED channel" in markdown

    def test_two_voices_present(self, markdown):
        """Both the doctrine verdict and the empirical disclosure appear."""
        assert "_Population context:_" in markdown
        assert "EMPIRICAL_ASTRODATABANK" in markdown
        assert "not a validated prediction" in markdown

    def test_output_is_ascii_safe(self, markdown):
        """Rendered like every other renderer: ASCII-safe for CP1252 consoles."""
        assert markdown.isascii()

    def test_divisional_deep_reads_present(self, report, markdown):
        """The Shodasavarga deep-reads (D9/D10/D7/D12/D30/D24) are composed and rendered."""
        assert len(report.divisional) >= 5
        assert "## Divisional deep-reads (Shodasavarga)" in markdown
        assert "### D-9 Marriage (Navamsa)" in markdown
        assert "### D-10 Career (Dasamsa)" in markdown
        assert "RAMAN CORE" in markdown          # the authoritative core block

    def test_life_narrative_is_windowed_md_ad(self, report, markdown):
        """The narrative is MD -> AD and clipped to [now-back, now+forward] with a 'now' marker."""
        assert len(report.timeline.periods) >= 5
        # every shown period is an Antardasha (has an antar lord) inside the window
        lo = report.ref_jd - report.window_back * 365.2425
        hi = report.ref_jd + report.window_forward * 365.2425
        for tp in report.timeline.periods:
            assert tp.period.antar is not None
            assert tp.period.end_jd >= lo and tp.period.start_jd <= hi
        assert "## Life-narrative (Vimshottari Dasha) -" in markdown
        assert "Mahadasha" in markdown and " AD** (" in markdown
        # the HTJAH-I four-tier grading vocabulary all appears across the window
        for tier in ("par excellence", "ordinary", "limited (bhukti lord only)",
                     "feeble (MD lord only)"):
            assert tier in markdown
        assert "associated with MD" in markdown
        assert "<- now**" in markdown          # the current AD is flagged

    def test_lords_associated_conjunction_and_self(self):
        """Sun/Jupiter/Venus conjoin in H10 on the canonical chart -> associated; a lord is
        trivially associated with itself (own bhukti)."""
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.primitives.vimshottari import lords_associated
        ch = cast_chart(_CANONICAL, ayanamsa="lahiri")
        assert lords_associated(ch, "Sun", "Jupiter") is True    # co-located in the 10th
        assert lords_associated(ch, "Sun", "Sun") is True        # own bhukti

    def test_bhukti_tier_is_the_four_grade_scheme(self):
        """The HTJAH-I four grades map exactly (uniform for every house)."""
        from app.raman_saab.primitives.vimshottari import bhukti_tier
        assert bhukti_tier(True, True, associated=True) == "par excellence"
        assert bhukti_tier(True, True, associated=False) == "ordinary"
        assert bhukti_tier(False, True, associated=False) == "limited"   # bhukti lord only
        assert bhukti_tier(True, False, associated=False) == "feeble"    # MD lord only
        assert bhukti_tier(False, False, associated=True) is None        # neither influences

    def test_diacritics_folded_not_blanked(self, markdown):
        """Sanskrit IAST from the varga renderers folds to base letters, never '?' mojibake."""
        assert "Navamsa" in markdown
        assert "Nav?" not in markdown and "k?raka" not in markdown

    def test_verdict_authority_invariant(self, report):
        """The overlay never alters a verdict — every calibrated verdict is a Raman verdict.

        Compared positionally against a lahiri-cast chart (entries are 1:1 in order with
        judge_house significations), so duplicate signification names cannot mask a drift.
        """
        from app.raman_saab.judges import house_template as ht
        from app.raman_saab.chart.adapter import cast_chart
        chart = cast_chart(_CANONICAL, ayanamsa="lahiri")
        for house, hr in report.calibration.items():
            raman = ht.judge_house(chart, house).significations
            assert len(raman) == len(hr.entries)
            for sv, e in zip(raman, hr.entries):
                assert e.signification == sv.signification
                assert e.verdict == sv.verdict
