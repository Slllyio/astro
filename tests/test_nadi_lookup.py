"""Tests for app.core.nadi_lookup — D-5 scaffold."""
from __future__ import annotations

import pytest

from app.core.nadi_lookup import (
    NadiPatternKey, NadiPatternMatch, is_corpus_loaded,
    lookup_nadi_pattern, registry_size,
)


class TestEmptyCorpusContract:
    """The scaffold returns found=False for every key until a corpus loads."""

    def test_registry_empty_by_default(self):
        assert registry_size() == 0
        assert is_corpus_loaded() is False

    def test_lookup_returns_match_not_raise(self):
        """A lookup must NEVER raise — returns NadiPatternMatch always."""
        key = NadiPatternKey(
            asc_sign=6, moon_sign=12, moon_nakshatra=26,
            atmakaraka="Mercury", md_lord="Mercury",
        )
        match = lookup_nadi_pattern(key)
        assert isinstance(match, NadiPatternMatch)

    def test_found_false_when_empty(self):
        """Empty registry -> every lookup returns found=False."""
        key = NadiPatternKey(
            asc_sign=1, moon_sign=1, moon_nakshatra=0,
            atmakaraka="Sun", md_lord="Sun",
        )
        match = lookup_nadi_pattern(key)
        assert match.found is False
        assert match.reading is None
        assert match.tradition is None

    def test_corpus_status_explanatory(self):
        """The corpus_status string explains why nothing matched."""
        key = NadiPatternKey(
            asc_sign=1, moon_sign=1, moon_nakshatra=0,
            atmakaraka="Sun", md_lord="Sun",
        )
        match = lookup_nadi_pattern(key)
        assert "scaffold" in match.corpus_status.lower() or \
               "no digitised" in match.corpus_status.lower()


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
