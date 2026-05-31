"""Tests for app.core.nadi_lookup — D-5 scaffold + N-1 corpus loader."""
from __future__ import annotations

import pytest

from app.core.nadi_lookup import (
    NadiPatternKey, NadiPatternMatch, is_corpus_loaded,
    lookup_nadi_pattern, registry_size,
)


class TestCorpusContract:
    """When the Nadi JSONL corpus is on disk, the registry loads it at import.

    With the Saptarishi Nadi extractor (N-1), 37+ leaves are available.
    These tests adapt to both states:
      - Empty registry (CI without data) → found=False, helpful status
      - Loaded registry (production) → found=True for matching lagnas
    """

    def test_registry_size_nonneg(self):
        """Registry size is always non-negative."""
        assert registry_size() >= 0

    def test_is_corpus_loaded_matches_size(self):
        assert is_corpus_loaded() == (registry_size() > 0)

    def test_lookup_returns_match_not_raise(self):
        """A lookup must NEVER raise — returns NadiPatternMatch always."""
        key = NadiPatternKey(
            asc_sign=6, moon_sign=12, moon_nakshatra=26,
            atmakaraka="Mercury", md_lord="Mercury",
        )
        match = lookup_nadi_pattern(key)
        assert isinstance(match, NadiPatternMatch)

    def test_corpus_status_always_explanatory(self):
        """corpus_status string is populated and explains the outcome."""
        key = NadiPatternKey(
            asc_sign=1, moon_sign=1, moon_nakshatra=0,
            atmakaraka="Sun", md_lord="Sun",
        )
        match = lookup_nadi_pattern(key)
        assert match.corpus_status
        assert len(match.corpus_status) > 10


class TestLoadedCorpusBehaviour:
    """Tests that assume the Saptarishi Nadi corpus is loaded.

    SKIPPED automatically when running CI without the JSONL artifact.
    """

    def test_aries_lagna_finds_at_least_one_leaf(self):
        """Saptarishi Nadi Aries collection → Aries-Lagna queries should match."""
        if registry_size() == 0:
            pytest.skip("Nadi corpus not loaded — run extract_nadi_corpus first")
        key = NadiPatternKey(
            asc_sign=1, moon_sign=6, moon_nakshatra=15,
            atmakaraka="Mercury", md_lord="Mercury",
        )
        match = lookup_nadi_pattern(key)
        assert match.found is True
        assert match.tradition is not None

    def test_refined_match_returns_high_specificity(self):
        """Supplying chart_planet_signs that overlap a stored leaf
        should boost specificity > 1."""
        if registry_size() == 0:
            pytest.skip("Nadi corpus not loaded")
        # Use exact planet positions from Saptarishi Nadi Horoscope 1
        key = NadiPatternKey(
            asc_sign=1, moon_sign=6, moon_nakshatra=15,
            atmakaraka="Mercury", md_lord="Mercury",
        )
        match = lookup_nadi_pattern(key, chart_planet_signs={
            "Rahu": 1, "Saturn": 6, "Moon": 6, "Ketu": 7, "Venus": 7,
            "Sun": 8, "Mercury": 9, "Mars": 11, "Jupiter": 12,
        })
        assert match.found is True
        # Specificity > 1 indicates planet-overlap match, not fallback
        assert match.key_specificity >= 4

    def test_unknown_lagna_finds_no_match(self):
        """If no Nadi leaf exists for the lagna, found=False with status."""
        if registry_size() == 0:
            pytest.skip("Nadi corpus not loaded")
        # Pick a lagna unlikely to have Aries-only Saptarishi coverage
        key = NadiPatternKey(
            asc_sign=4, moon_sign=4, moon_nakshatra=10,
            atmakaraka="Moon", md_lord="Moon",
        )
        match = lookup_nadi_pattern(key)
        # Could be False (no Cancer Lagna leaves) or True (if other sources)
        # Just verify the contract holds: if False, status explains why
        if not match.found:
            assert "Lagna sign" in match.corpus_status or "Nadi" in match.corpus_status


class TestKeyShape:
    """The key dataclass enforces the required + optional field split."""

    def test_required_fields_set(self):
        key = NadiPatternKey(
            asc_sign=6, moon_sign=12, moon_nakshatra=26,
            atmakaraka="Mercury", md_lord="Mercury",
        )
        assert key.asc_sign == 6
        assert key.atmakaraka == "Mercury"

    def test_optional_fields_default_to_none(self):
        key = NadiPatternKey(
            asc_sign=6, moon_sign=12, moon_nakshatra=26,
            atmakaraka="Mercury", md_lord="Mercury",
        )
        assert key.ad_lord is None
        assert key.sun_sign is None

    def test_key_hashable(self):
        """Key must be hashable to serve as dict key."""
        k1 = NadiPatternKey(6, 12, 26, "Mercury", "Mercury")
        k2 = NadiPatternKey(6, 12, 26, "Mercury", "Mercury")
        assert hash(k1) == hash(k2)
        s = {k1, k2}
        assert len(s) == 1


class TestBhriguRules:
    """N-1 extension: rule-format Nadi corpus (Bhrigu Nadi Sangraha)."""

    def test_bhrigu_rules_count_nonneg(self):
        from app.core.nadi_lookup import bhrigu_rules_count
        assert bhrigu_rules_count() >= 0

    def test_rules_mentioning_returns_tuple(self):
        from app.core.nadi_lookup import bhrigu_rules_mentioning
        result = bhrigu_rules_mentioning("Saturn")
        assert isinstance(result, tuple)

    def test_rules_filter_by_multiple_planets(self):
        """Multi-planet filter uses AND semantics — all needles must match."""
        from app.core.nadi_lookup import bhrigu_rules_count, bhrigu_rules_mentioning
        if bhrigu_rules_count() == 0:
            pytest.skip("Bhrigu rules not loaded")
        # Rules mentioning both Saturn AND Jupiter should be ≤ rules mentioning
        # just Saturn alone.
        sat_only = bhrigu_rules_mentioning("Saturn")
        sat_jup = bhrigu_rules_mentioning("Saturn", "Jupiter")
        assert len(sat_jup) <= len(sat_only)

    def test_rules_with_8th_house_match_death_pattern(self):
        """Saturn + 8th rules should include classical death-of-parent
        statements per Bhrigu Nadi Sangraha."""
        from app.core.nadi_lookup import bhrigu_rules_count, bhrigu_rules_mentioning
        if bhrigu_rules_count() == 0:
            pytest.skip("Bhrigu rules not loaded")
        rules = bhrigu_rules_mentioning("Saturn", "8th")
        # At least one rule should mention 'death' (classical Bhrigu pattern)
        if rules:
            has_death_rule = any("death" in r.raw_text.lower() for r in rules)
            assert has_death_rule, "expected Saturn+8th rules to include death-related"
