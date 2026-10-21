"""Multi-label target discovery/matching, and its exact equivalence to
single-label matching when a corpus (like Gauquelin's) has no multi-valued
labels — the compatibility property the design leans on.
"""

from __future__ import annotations

import pandas as pd

from app.empirical.tournament.run_screening_lunarastro import (
    candidate_categories,
    has_category,
)


class TestCandidateCategories:
    def test_counts_individual_tags_not_joined_combinations(self):
        """Two rows share 'Writers' but differ on the other tag — the joined
        strings never repeat, so only splitting finds the shared category."""
        labels = pd.Series(["Vocation;Writers", "Family;Writers"])
        assert candidate_categories(labels, min_n=2) == ["Writers"]

    def test_threshold_excludes_rare_tags(self):
        labels = pd.Series(["A;B", "A;C", "A;D"])
        assert candidate_categories(labels, min_n=3) == ["A"]
        assert set(candidate_categories(labels, min_n=1)) == {"A", "B", "C", "D"}

    def test_single_valued_labels_reduce_to_exact_counting(self):
        """When labels never contain ';' (e.g. Gauquelin's profession column
        routed through this reader), splitting is a no-op and this behaves
        exactly like counting the plain label — the backward-compatibility
        property the module docstring claims."""
        labels = pd.Series(["actor", "actor", "writer"])
        assert candidate_categories(labels, min_n=2) == ["actor"]


class TestHasCategory:
    def test_membership_is_independent_of_tag_order(self):
        labels = pd.Series(["Vocation;Writers", "Writers;Vocation"])
        result = has_category(labels, "Writers")
        assert list(result) == [1, 1]

    def test_no_partial_string_match(self):
        """'Writer' must not match a row tagged only 'Writers' — split-based
        membership, never substring containment."""
        labels = pd.Series(["Writers"])
        assert list(has_category(labels, "Writer")) == [0]

    def test_single_valued_label_exact_match_equivalence(self):
        labels = pd.Series(["actor", "writer"])
        assert list(has_category(labels, "actor")) == [1, 0]
