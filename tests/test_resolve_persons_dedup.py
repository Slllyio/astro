"""Tests for app/medini/etl/resolve_persons_dedup.py.

Pins the cross-corpus dedup rules:
- name + birth_date is the match key
- ADB > Wikidata > Lunarastro priority for canonical selection
- Persons missing name OR birth_date are singleton clusters
- Diacritics + punctuation are stripped before matching
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.etl.resolve_persons_dedup import (
    _pick_canonical,
    normalize_name_key,
    resolve,
)


@pytest.fixture
def persons_with_known_overlap() -> pd.DataFrame:
    """Synthetic persons table with known cross-corpus matches.

    - Agatha Christie appears in both ADB and Wikidata (different ID format).
    - Einstein appears in all 3 corpora (full priority chain test).
    - A unique ADB-only person.
    - A row with no birth_date (must be singleton).
    """
    return pd.DataFrame({
        "person_id": [
            "ADB:2411626", "WD:Q35064",         # Agatha Christie
            "ADB:2407422", "WD:Q937", "LA:einstein",  # Einstein x3
            "ADB:2400000",                       # Unique ADB person
            "WD:Q9999",                          # Missing birth_date
        ],
        "name": [
            "agatha christie", "Agatha Christie",
            "albert einstein", "Albert Einstein", "Albert Einstein",
            "isaac newton",
            "Anonymous",
        ],
        "birth_date": [
            "1890-09-15", "1890-09-15",
            "1879-03-14", "1879-03-14", "1879-03-14",
            "1665-01-04",
            None,
        ],
        "source": [
            "astro_databank", "wikidata",
            "astro_databank", "wikidata", "lunarastro",
            "astro_databank",
            "wikidata",
        ],
    })


class TestNameNormalization:
    """The name_key must strip case, diacritics, and punctuation."""

    def test_lowercases_input(self):
        """'Agatha Christie' and 'agatha christie' must produce the same key."""
        assert normalize_name_key("Agatha Christie") == normalize_name_key("agatha christie")

    def test_strips_diacritics(self):
        """'agnès b.' and 'agnes b' must produce the same key."""
        assert normalize_name_key("agnès b.") == normalize_name_key("agnes b")

    def test_strips_punctuation_and_spaces(self):
        """Periods, commas, hyphens, spaces all dissolve."""
        assert normalize_name_key("John F. Kennedy") == normalize_name_key("johnfkennedy")
        assert normalize_name_key("Jean-Paul Sartre") == "jeanpaulsartre"

    def test_none_returns_empty_string(self):
        """A None / NaN input becomes the empty string sentinel."""
        assert normalize_name_key(None) == ""
        assert normalize_name_key(pd.NA) == ""


class TestCanonicalPriority:
    """ADB beats Wikidata beats Lunarastro for canonical_id selection."""

    def test_adb_wins_over_wikidata(self):
        """ADB has time-of-birth precision; it must win."""
        chosen = _pick_canonical(
            ["WD:Q1", "ADB:X"], ["wikidata", "astro_databank"],
        )
        assert chosen == "ADB:X"

    def test_wikidata_wins_over_lunarastro(self):
        """Wikidata is day-precision; Lunarastro is mixed."""
        chosen = _pick_canonical(
            ["LA:1", "WD:Q1"], ["lunarastro", "wikidata"],
        )
        assert chosen == "WD:Q1"

    def test_adb_wins_over_all_three(self):
        """ADB present anywhere in the cluster -> canonical."""
        chosen = _pick_canonical(
            ["LA:1", "WD:Q1", "ADB:X"],
            ["lunarastro", "wikidata", "astro_databank"],
        )
        assert chosen == "ADB:X"


class TestResolve:
    """End-to-end resolution behavior on synthetic overlap fixture."""

    def test_agatha_christie_merges_across_corpora(
        self, persons_with_known_overlap: pd.DataFrame,
    ):
        """ADB + WD rows with same normalized name and date -> 1 cluster."""
        resolved = resolve(persons_with_known_overlap)
        agatha = resolved[resolved["name_key"] == "agathachristie"]
        assert len(agatha) == 1
        assert set(agatha.iloc[0]["source_ids"]) == {"ADB:2411626", "WD:Q35064"}
        assert agatha.iloc[0]["canonical_id"] == "ADB:2411626"

    def test_einstein_merges_three_corpora(
        self, persons_with_known_overlap: pd.DataFrame,
    ):
        """ADB + WD + LA rows for Einstein -> one 3-corpus cluster."""
        resolved = resolve(persons_with_known_overlap)
        einstein = resolved[resolved["name_key"] == "alberteinstein"]
        assert len(einstein) == 1
        assert einstein.iloc[0]["n_corpora"] == 3
        assert einstein.iloc[0]["canonical_id"].startswith("ADB:")

    def test_unique_person_is_own_cluster(
        self, persons_with_known_overlap: pd.DataFrame,
    ):
        """No-overlap person -> singleton cluster of size 1."""
        resolved = resolve(persons_with_known_overlap)
        newton = resolved[resolved["name_key"] == "isaacnewton"]
        assert len(newton) == 1
        assert newton.iloc[0]["n_corpora"] == 1
        assert newton.iloc[0]["source_ids"] == ["ADB:2400000"]

    def test_missing_birth_date_becomes_singleton(
        self, persons_with_known_overlap: pd.DataFrame,
    ):
        """Even if name matched, no birth_date means no merging."""
        resolved = resolve(persons_with_known_overlap)
        # WD:Q9999 has name="Anonymous" but no birth_date.
        anon = resolved[resolved["source_ids"].map(lambda s: "WD:Q9999" in s)]
        assert len(anon) == 1
        assert anon.iloc[0]["source_ids"] == ["WD:Q9999"]


class TestNoFalseMerges:
    """Different-birthdate same-name persons must NOT merge."""

    def test_two_jane_does_different_birthdates(self):
        """Two unrelated humans with the same name must stay separate."""
        persons = pd.DataFrame({
            "person_id": ["ADB:A", "WD:B"],
            "name": ["Jane Doe", "Jane Doe"],
            "birth_date": ["1900-01-01", "2000-01-01"],
            "source": ["astro_databank", "wikidata"],
        })
        resolved = resolve(persons)
        assert len(resolved) == 2  # No merge
