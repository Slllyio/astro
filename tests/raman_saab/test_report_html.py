"""Tests for the HTML presenter of the detailed report (two-voice, theme-aware, safe)."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.report_html import standalone_html, to_html

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def body(report):
    return to_html(report)


class TestReportHtml:
    def test_has_style_and_all_house_sections(self, body):
        """One inline stylesheet and a section for each of the 12 bhavas."""
        assert body.count("<style>") == 1
        assert body.count('class="house"') == 12

    def test_designs_both_themes(self, body):
        """Palette is token-driven with an OS-dark media query and a data-theme override."""
        assert "@media (prefers-color-scheme: dark)" in body
        assert ':root[data-theme="dark"]' in body

    def test_two_voices_and_provenance(self, body):
        """The doctrine/instrument duality and the not-Raman provenance are present."""
        assert 'class="doctrine"' in body
        assert 'class="instrument"' in body
        assert "EMPIRICAL_ASTRODATABANK" in body

    def test_inverted_channel_tagged(self, body):
        """H12 incarceration, an atlas-proven inverted channel, carries the warning tag."""
        assert "tag--warn" in body
        assert "inverted channel" in body

    def test_divisional_and_timeline_rendered(self, body):
        """Divisional <details> blocks and the Dasha timeline both render."""
        assert body.count('class="varga"') >= 5
        assert body.count('class="period"') >= 5

    def test_html_escapes_untrusted_name(self):
        """A name with markup is escaped, never injected as live HTML."""
        evil = BirthData("<script>alert(1)</script>", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
        out = to_html(build_detailed_report(evil))
        assert "<script>alert(1)</script>" not in out
        assert "&lt;script&gt;" in out

    def test_standalone_wraps_document(self, report):
        """The standalone wrapper is a full, titled UTF-8 document."""
        doc = standalone_html(report, title="My Reading")
        assert doc.startswith("<!doctype html>")
        assert "<title>My Reading</title>" in doc
        assert 'charset="utf-8"' in doc
