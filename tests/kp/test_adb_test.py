"""Addendum A helpers: published-Ascendant parsing, groups, Fisher test, digest guard."""

from __future__ import annotations

import math

import pytest

from tools.kp import adb_test as t


class TestHelpers:
    def test_published_ascendant_is_mid_degree(self) -> None:
        """'Asc 18 Aquarius' is 300 + 18 + 0.5 degrees."""
        assert t.published_asc("1961 births;Asc 18 Aquarius;Moon 3 Gemini") == 318.5
        assert t.published_asc("no ascendant here") is None

    def test_fisher_matches_textbook_value(self) -> None:
        """Lady tasting tea table [[3, 1], [1, 3]]: one-sided p = 17/70."""
        assert math.isclose(t.fisher_one_sided(3, 1, 1, 3, greater=True), 17 / 70, rel_tol=1e-9)
        assert math.isclose(t.fisher_one_sided(3, 1, 1, 3, greater=False), 69 / 70, rel_tol=1e-9)

    def test_groups_exclude_contradictory_tags(self) -> None:
        """A person tagged both 'Kids none' and 'Kids 1-3' is in neither T1 group."""
        both = {"Family : Parenting : Kids none", "Family : Parenting : Kids 1-3"}
        assert "T1" not in t.trait_groups(both)
        assert t.trait_groups({"Family : Parenting : Kids none"})["T1"] == "case"
        assert t.trait_groups(set())["T3"] == "control"

    def test_changed_lock_is_void(self) -> None:
        """Editing a locked rule list after locking voids the trait test."""
        locked = {"digest": "0" * 64, "people": {}}
        with pytest.raises(SystemExit):
            t._verify(locked)
