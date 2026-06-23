"""Tests for the person-attributes extractor's pure parsing/label logic."""
from __future__ import annotations

from app.medini.etl.build_person_attributes import _derive_labels, _parse_tags

_CATS = (
    "Vocation : Entertain/Music : Vocalist;"
    "Vocation : Entertainment : Actor;"
    "Notable : Famous : Top 5% of Profession;"
    "Notable : Awards : Grammy;"
    "Lifestyle : Financial : Rags to riches;"
    "Family : Relationship : Marriage - Very happy;"
    "Diagnoses : Psychological : Abuse Drugs;"
    "1901 births;"                      # noise: no root colon-structure
    "Birthplace New Orleans, LA (US);"  # noise: not a whitelisted root
    "Pages with broken file links"      # noise
)


class TestParseTags:
    def test_keeps_only_whitelisted_structured_tags(self) -> None:
        tags = _parse_tags(_CATS)
        roots = {r for r, _, _ in tags}
        assert roots == {"Vocation", "Notable", "Lifestyle", "Family", "Diagnoses"}
        # noise dropped
        assert all("Birthplace" not in r for r, _, _ in tags)
        assert len(tags) == 7

    def test_handles_two_part_tags(self) -> None:
        tags = _parse_tags("Traits : Body")  # root:field, no detail
        assert tags == [("Traits", "Body", "")]

    def test_empty(self) -> None:
        assert _parse_tags("") == []


class TestDeriveLabels:
    def test_primary_vocation_is_most_frequent_field(self) -> None:
        tags = _parse_tags(
            "Vocation : Politics : Senator;Vocation : Politics : Governor;"
            "Vocation : Law : Lawyer"
        )
        lab = _derive_labels(tags)
        assert lab["primary_vocation"] == "Politics"
        assert lab["n_vocation_fields"] == 2

    def test_presence_flags(self) -> None:
        lab = _derive_labels(_parse_tags(_CATS))
        assert lab["is_famous"] is True
        assert lab["has_award"] is True
        assert lab["has_major_disease"] is False
        assert lab["has_psychological_dx"] is True
        assert lab["has_marriage"] is True
        assert lab["financial_gain"] is True

    def test_no_vocation(self) -> None:
        lab = _derive_labels(_parse_tags("Notable : Famous : X"))
        assert lab["primary_vocation"] is None
        assert lab["n_vocation_fields"] == 0
