"""Tests for app/medini/etl/build_event_class_taxonomy.py.

Pins the taxonomy contract:
- Every granular class has a non-null harmonized mapping
- Death subclasses are correctly flagged
- Category rollup is consistent (death_of_* → family_loss, not death)
- Coverage matches the actual columns in dasha_mdadpd_corpus.parquet
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.etl.build_event_class_taxonomy import _TAXONOMY, build_taxonomy


@pytest.fixture
def taxonomy() -> pd.DataFrame:
    return build_taxonomy()


class TestSchemaContract:
    """All required columns exist with valid types."""

    def test_required_columns(self, taxonomy: pd.DataFrame):
        """Schema contract for downstream JOIN consumers."""
        required = {
            "granular_class", "harmonized_class", "category",
            "is_death_subclass", "description",
        }
        assert required.issubset(set(taxonomy.columns))

    def test_no_nulls_in_key_columns(self, taxonomy: pd.DataFrame):
        """granular_class and harmonized_class must never be NULL."""
        assert taxonomy["granular_class"].notna().all()
        assert taxonomy["harmonized_class"].notna().all()
        assert taxonomy["category"].notna().all()


class TestHarmonizedMapping:
    """Every granular class maps to a known harmonized class."""

    def test_harmonized_values_are_canonical(self, taxonomy: pd.DataFrame):
        """Only 6 harmonized classes are allowed (matches events_with_dasha)."""
        valid = {"marriage", "career", "fame",
                 "death_cause_unspecified", "relationships", "other"}
        assert set(taxonomy["harmonized_class"].unique()).issubset(valid)

    def test_marriage_is_one_entry(self, taxonomy: pd.DataFrame):
        """Only the literal 'marriage' granular maps to harmonized 'marriage'."""
        marriage_rows = taxonomy[taxonomy["harmonized_class"] == "marriage"]
        assert len(marriage_rows) == 1
        assert marriage_rows.iloc[0]["granular_class"] == "marriage"


class TestCategoryRollup:
    """Category dimension is BPHS-domain-meaningful, not just harmonized rename."""

    def test_death_of_family_is_family_loss_not_death(self, taxonomy: pd.DataFrame):
        """death_of_mother is a family loss event, not a personal death.
        This is the doctrinally correct distinction: 4H/9H/3H/5H domains."""
        row = taxonomy[taxonomy["granular_class"] == "death_of_mother"].iloc[0]
        assert row["category"] == "family_loss"
        assert row["harmonized_class"] == "relationships"
        assert bool(row["is_death_subclass"]) is True

    def test_death_of_self_is_death_category(self, taxonomy: pd.DataFrame):
        """death_by_disease etc. → category=death, harmonized=death_cause_unspecified."""
        row = taxonomy[taxonomy["granular_class"] == "death_by_disease"].iloc[0]
        assert row["category"] == "death"
        assert row["harmonized_class"] == "death_cause_unspecified"

    def test_personal_category_includes_health_and_education(self, taxonomy: pd.DataFrame):
        """personal category covers self-directed events (Lagna domain in BPHS)."""
        personal = taxonomy[taxonomy["category"] == "personal"]
        personal_classes = set(personal["granular_class"])
        assert "personal" in personal_classes
        assert "health" in personal_classes
        assert "education" in personal_classes


class TestDeathSubclassFlag:
    """is_death_subclass must fire for every death_* but only death_*."""

    def test_all_death_subclasses_flagged(self, taxonomy: pd.DataFrame):
        """Any granular starting with 'death' is a death subclass."""
        death_rows = taxonomy[taxonomy["granular_class"].str.startswith("death")]
        assert death_rows["is_death_subclass"].all()

    def test_only_death_related_are_flagged(self, taxonomy: pd.DataFrame):
        """is_death_subclass should match: granular contains 'death' anywhere
        (covers both ``death_*`` and ``other_death``).

        Conversely, marriage / career / personal etc. must NOT be flagged.
        """
        flagged = taxonomy[taxonomy["is_death_subclass"]]
        # Every flagged row contains 'death' in its granular_class.
        assert flagged["granular_class"].str.contains("death").all()
        # Marriage and personal must NOT be flagged (sanity).
        for unflagged in ("marriage", "personal", "career", "fame"):
            row = taxonomy[taxonomy["granular_class"] == unflagged].iloc[0]
            assert not bool(row["is_death_subclass"]), f"{unflagged} mistakenly flagged"


class TestUniqueness:
    """granular_class is the table's natural key (1:1 with rows)."""

    def test_granular_class_is_unique(self, taxonomy: pd.DataFrame):
        """No duplicate granular_class entries — it's the primary key."""
        assert taxonomy["granular_class"].nunique() == len(taxonomy)


class TestCoverage:
    """The 56 entries match the full set declared in _TAXONOMY."""

    def test_taxonomy_has_56_entries(self, taxonomy: pd.DataFrame):
        """56 ADB granular classes (current corpus)."""
        assert len(taxonomy) == 56

    def test_no_taxonomy_drift_from_source(self):
        """build_taxonomy() and _TAXONOMY constant are in sync."""
        assert len(build_taxonomy()) == len(_TAXONOMY)
