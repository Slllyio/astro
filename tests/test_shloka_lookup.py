"""Tests for app.core.shloka_lookup — harvested classical-rule corpus."""
from __future__ import annotations

import pytest

from app.core.shloka_lookup import (
    ShlokaRule, corpus_size, is_corpus_loaded, reload_corpus,
    rules_for_domain_and_planet, rules_for_source, rules_for_topic,
    rules_mentioning, sources_present, topics_present,
)


class TestCorpusContract:
    """Both empty-corpus and loaded-corpus cases must be handled gracefully."""

    def test_corpus_size_nonneg(self):
        assert corpus_size() >= 0

    def test_is_loaded_matches_size(self):
        assert is_corpus_loaded() == (corpus_size() > 0)

    def test_sources_present_is_tuple(self):
        result = sources_present()
        assert isinstance(result, tuple)

    def test_topics_present_is_tuple(self):
        result = topics_present()
        assert isinstance(result, tuple)


class TestLookups:
    """Lookup functions never raise; return tuples (possibly empty)."""

    def test_rules_for_topic_returns_tuple(self):
        result = rules_for_topic("marriage")
        assert isinstance(result, tuple)
        for r in result:
            assert isinstance(r, ShlokaRule)
            assert "marriage" in r.topics

    def test_rules_for_source_returns_tuple(self):
        result = rules_for_source("brihat_jataka")
        assert isinstance(result, tuple)
        for r in result:
            assert r.source == "brihat_jataka"

    def test_rules_mentioning_returns_tuple(self):
        result = rules_mentioning("Saturn")
        assert isinstance(result, tuple)

    def test_rules_mentioning_and_semantics(self):
        """Multi-needle filter uses AND — every needle must appear."""
        sat_only = rules_mentioning("Saturn")
        sat_jup = rules_mentioning("Saturn", "Jupiter")
        # AND-filter narrows the set
        assert len(sat_jup) <= len(sat_only)

    def test_limit_caps_results(self):
        result = rules_mentioning("the", limit=5)
        assert len(result) <= 5


class TestLoadedCorpusBehaviour:
    """Tests assuming the JSONL corpus is on disk (skip if absent)."""

    def test_corpus_has_2k_plus_rules(self):
        """After running harvest_shlokas, expect 2000+ rules."""
        if corpus_size() == 0:
            pytest.skip("Shloka corpus not loaded — run harvest_shlokas first")
        assert corpus_size() >= 2000

    def test_multiple_sources_loaded(self):
        if corpus_size() == 0:
            pytest.skip("Corpus not loaded")
        sources = sources_present()
        # We expect at least a few foundational sources
        assert len(sources) >= 5

    def test_brihat_jataka_present(self):
        if corpus_size() == 0:
            pytest.skip("Corpus not loaded")
        assert "brihat_jataka" in sources_present()

    def test_marriage_topic_has_rules(self):
        if corpus_size() == 0:
            pytest.skip("Corpus not loaded")
        marriage_rules = rules_for_topic("marriage", limit=100)
        # At least some should have fired (marriage is a common domain)
        assert len(marriage_rules) >= 5

    def test_planet_topics_tagged(self):
        if corpus_size() == 0:
            pytest.skip("Corpus not loaded")
        # Planets are also topic tags
        sun_rules = rules_for_topic("Sun")
        assert len(sun_rules) > 0


class TestComposability:
    """rules_for_domain_and_planet returns rules tagged both ways."""

    def test_domain_and_planet_returns_intersection(self):
        if corpus_size() == 0:
            pytest.skip("Corpus not loaded")
        result = rules_for_domain_and_planet("marriage", "Venus", limit=10)
        for r in result:
            assert "marriage" in r.topics
            assert "Venus" in r.topics
