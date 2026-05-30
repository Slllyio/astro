"""Tests for `app.reading.narrative.section_builders`.

Locks the deterministic skeleton contract:

- Each builder produces a non-empty string for a real Bangalore reading.
- Each builder handles missing/empty inputs without raising.
- All 6 domain skeletons are produced for the canonical reading.
- The safe-language word policy holds in every skeleton (no "will",
  "guaranteed", "definitely", "certainly" as standalone words).
"""
from __future__ import annotations

import re

import pytest

from app.reading.narrative.prompts import FORBIDDEN_WORDS
from app.reading.narrative.section_builders import (
    DOMAIN_SECTIONS,
    NARRATIVE_SECTIONS,
    build_chart_overview,
    build_contradictions_section,
    build_current_antardasha,
    build_current_mahadasha,
    build_domain_section,
    build_yogas_section,
)


_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_WORDS) + r")\b",
    flags=re.IGNORECASE,
)


def _assert_safe(text: str) -> None:
    """Hard assertion that prose obeys safe-language doctrine."""
    match = _FORBIDDEN_RE.search(text)
    assert match is None, (
        f"forbidden predictive word {match.group(0)!r} found in prose: {text!r}"
    )


class TestChartOverviewBuilder:
    """Chart overview skeleton — ascendant + day/night + panchanga + primitives count."""

    def test_returns_non_empty_for_real_reading(self, bangalore_reading):
        """The Bangalore reading must produce a populated chart overview."""
        text = build_chart_overview(
            bangalore_reading.get("chart"), bangalore_reading.get("primitives")
        )
        assert text.strip()
        _assert_safe(text)

    def test_mentions_ascendant_when_present(self, bangalore_reading):
        """When the chart has an ascendant, the prose references it."""
        text = build_chart_overview(
            bangalore_reading.get("chart"), bangalore_reading.get("primitives")
        )
        # Bangalore noon 1990-07-15 → Virgo lagna (per CLAUDE.md baseline).
        assert "ascendant" in text.lower()

    def test_handles_missing_inputs_gracefully(self):
        """Builder must not raise when both inputs are None."""
        text = build_chart_overview(None, None)
        assert text.strip()
        _assert_safe(text)

    def test_handles_empty_dicts_gracefully(self):
        """Empty dicts → graceful fallback prose, not a crash."""
        text = build_chart_overview({}, {})
        assert text.strip()
        _assert_safe(text)


class TestCurrentMahadashaBuilder:
    """Current mahadasha skeleton — pulls the is_current MD from sequences."""

    def test_returns_non_empty_for_real_reading(self, bangalore_reading):
        """The Bangalore reading has md_judgments with one is_current=True."""
        text = build_current_mahadasha(bangalore_reading.get("sequences"))
        assert text.strip()
        _assert_safe(text)

    def test_mentions_md_lord_when_present(self, bangalore_reading):
        """The MD lord name must appear in the prose."""
        text = build_current_mahadasha(bangalore_reading.get("sequences"))
        # Bangalore 1990-07-15 → currently in Mercury MD (per the live pipeline).
        # Use lowercase to be lenient about title-casing.
        assert "mercury" in text.lower()

    def test_graceful_when_no_active_md(self):
        """No is_current → fallback prose, not a KeyError."""
        text = build_current_mahadasha({"md_judgments": []})
        assert "no active mahadasha" in text.lower()
        _assert_safe(text)

    def test_graceful_when_seq_block_none(self):
        text = build_current_mahadasha(None)
        assert text.strip()
        _assert_safe(text)


class TestCurrentAntardashaBuilder:
    """Current antardasha skeleton — pulls the is_current AD from sequences."""

    def test_returns_non_empty_for_real_reading(self, bangalore_reading):
        text = build_current_antardasha(bangalore_reading.get("sequences"))
        assert text.strip()
        _assert_safe(text)

    def test_graceful_when_no_active_ad(self):
        text = build_current_antardasha({"ad_judgments": []})
        assert "no active antardasha" in text.lower()
        _assert_safe(text)


class TestDomainBuilder:
    """Domain skeleton — 6 domains rendered uniformly."""

    @pytest.mark.parametrize("domain", DOMAIN_SECTIONS)
    def test_each_of_six_domains_renders(self, bangalore_reading, domain):
        """All 6 named domains must produce non-empty safe-language prose."""
        domain_reading = (bangalore_reading.get("domains") or {}).get(domain)
        text = build_domain_section(domain, domain_reading)
        assert text.strip()
        assert domain in text.lower()
        _assert_safe(text)

    def test_graceful_when_domain_reading_none(self):
        text = build_domain_section("career", None)
        assert "no domain reading" in text.lower()
        _assert_safe(text)


class TestYogasBuilder:
    """Yogas skeleton — sourced from practitioner.findings classification=yoga."""

    def test_returns_non_empty_for_real_reading(self, bangalore_reading):
        text = build_yogas_section(
            (bangalore_reading.get("practitioner") or {}).get("findings")
        )
        assert text.strip()
        _assert_safe(text)

    def test_no_yogas_message(self):
        """Empty findings list → explicit 'no notable yogas' wording."""
        text = build_yogas_section([])
        assert "no notable yogas" in text.lower()
        _assert_safe(text)

    def test_ignores_non_yoga_findings(self):
        """A primitive-classification finding must be filtered out."""
        text = build_yogas_section([
            {"classification": "primitive", "verdict": "noise", "direction": "neutral"},
        ])
        assert "no notable yogas" in text.lower()


class TestContradictionsBuilder:
    """Contradictions skeleton — Tier-3 cross-finding disagreements."""

    def test_no_contradictions_message(self):
        text = build_contradictions_section([])
        assert "no contradictions" in text.lower()
        _assert_safe(text)

    def test_handles_none(self):
        text = build_contradictions_section(None)
        assert text.strip()
        _assert_safe(text)

    def test_renders_soft_and_hard(self):
        """When both severities present, both counts appear in the prose."""
        text = build_contradictions_section([
            {"severity": "soft", "domain": "career", "finding_ids": ["a", "b"],
             "description": "x"},
            {"severity": "hard", "domain": "marriage", "finding_ids": ["c", "d"],
             "description": "y"},
        ])
        assert "soft" in text.lower()
        assert "hard" in text.lower()
        assert "career" in text.lower()
        _assert_safe(text)


class TestVocabularyContract:
    """Locks the public NARRATIVE_SECTIONS / DOMAIN_SECTIONS contract."""

    def test_narrative_sections_contains_six_domains(self):
        for d in DOMAIN_SECTIONS:
            assert d in NARRATIVE_SECTIONS

    def test_narrative_sections_contains_dasha_and_overview(self):
        for required in (
            "chart_overview", "current_mahadasha", "current_antardasha",
            "yogas", "contradictions",
        ):
            assert required in NARRATIVE_SECTIONS

    def test_domain_sections_are_exactly_six(self):
        """The 6-domain block is canonical; locking the count guards drift."""
        assert len(DOMAIN_SECTIONS) == 6
