"""Tests for app.core.prashna — question → bhava routing."""
from __future__ import annotations

import pytest

from app.core.prashna import (
    PrashnaMatch,
    keywords_for_bhava,
    route_question,
)


class TestRouting:
    """Canonical question → bhava mappings."""

    @pytest.mark.parametrize("question,expected_bhava", [
        ("will i get married this year?", 7),
        ("when will i find a spouse?", 7),
        ("what does my career look like?", 10),
        ("will i be successful at work?", 10),
        ("when will i have children?", 5),
        ("how is my health?", 1),
        ("will i inherit anything?", 8),
        ("am i going to travel abroad?", 9),
        ("what about my mother's health?", 4),
        ("will i make a lot of money?", 2),
        ("how is my dharma path?", 9),
        ("when will i have a child?", 5),
    ])
    def test_routes_to_expected_bhava(self, question, expected_bhava):
        """Canonical phrasings route to their classical bhava."""
        match = route_question(question)
        assert match.bhava == expected_bhava, (
            f"Question {question!r} routed to bhava {match.bhava} "
            f"(matched: {match.matched_keywords}), expected {expected_bhava}"
        )


class TestConfidence:
    """Confidence labelling reflects match strength."""

    def test_specific_question_gets_high_confidence(self):
        """A direct keyword phrase gets HIGH or MEDIUM."""
        match = route_question("when will i get married to my partner?")
        assert match.confidence in ("HIGH", "MEDIUM")

    def test_no_keywords_yields_none_confidence(self):
        """Gibberish question → NONE confidence + bhava=1 default."""
        match = route_question("xyz qrs tuv nothing here")
        assert match.confidence == "NONE"
        assert match.matched_keywords == ()


class TestMatchedKeywords:
    """The match carries which keywords fired — for explainability."""

    def test_match_lists_keywords(self):
        """Spouse question matches 'spouse' or 'married'/'wedding'."""
        match = route_question("i'm thinking about marriage")
        assert any(k in {"marriage", "spouse", "wedding"}
                   for k in match.matched_keywords)

    def test_candidates_considered_includes_top_alternatives(self):
        """Top alternatives ranked + scored for debugging."""
        match = route_question("my career and money situation")
        # Career (10) + wealth (2) should both score
        candidates = dict(match.candidates_considered)
        assert 10 in candidates or 2 in candidates


class TestStructure:
    """Return type contract."""

    def test_returns_prashna_match(self):
        """Always returns a PrashnaMatch."""
        match = route_question("test")
        assert isinstance(match, PrashnaMatch)

    def test_dataclass_is_frozen(self):
        """Result is immutable."""
        match = route_question("marriage")
        with pytest.raises(Exception):
            match.bhava = 99  # type: ignore[misc]


class TestKeywordsAccessor:
    """Public access to keyword sets."""

    def test_keywords_for_bhava_returns_frozenset(self):
        """Returns the configured set; immutable."""
        kws = keywords_for_bhava(7)
        assert isinstance(kws, frozenset)
        assert "marriage" in kws

    def test_keywords_for_bhava_rejects_out_of_range(self):
        """1..12 only."""
        with pytest.raises(ValueError):
            keywords_for_bhava(0)
        with pytest.raises(ValueError):
            keywords_for_bhava(13)
