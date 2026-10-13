"""The Parashara store builder must never resume into, or overwrite, a store built for another
population (DOUBLE_TRANSIT_PREREG_AMENDMENT_1 repair)."""
from __future__ import annotations

import pytest

from tools.parashara.astrobank.build_store import _guard_population

A = [{"person_id": "a"}, {"person_id": "b"}]
B = [{"person_id": "c"}]


class TestPopulationGuard:
    def test_same_population_resumes(self, tmp_path):
        """A resumed build of the same people is allowed."""
        _guard_population(tmp_path, A, extension=False)
        _guard_population(tmp_path, list(reversed(A)), extension=False)   # order-insensitive

    def test_different_population_refused(self, tmp_path):
        """A different population in the same --out is refused."""
        _guard_population(tmp_path, A, extension=False)
        with pytest.raises(SystemExit):
            _guard_population(tmp_path, B, extension=True)

    def test_unmarked_legacy_store_refuses_extension(self, tmp_path):
        """An unmarked store with finished chunks is the primary store; an extension run must not adopt it."""
        (tmp_path / "part_00000.done").write_text("ok")
        with pytest.raises(SystemExit):
            _guard_population(tmp_path, B, extension=True)

    def test_unmarked_legacy_store_adopted_by_primary(self, tmp_path):
        """The primary rebuild (RESULTS.md reproduce command) may adopt an unmarked legacy store."""
        (tmp_path / "part_00000.done").write_text("ok")
        _guard_population(tmp_path, A, extension=False)
        assert (tmp_path / "population_sha.txt").exists()


class TestAmendmentPopulations:
    def test_populations_partition_correctly(self):
        """store/extension split A+B by store membership; tierC never overlaps A+B."""
        from tools.parashara.astrobank.transit_tests import select_people
        tier = {"s1": "A", "s2": "C", "e1": "B", "e2": "C", "x": "A"}
        cast, store = {"s1", "s2", "e1", "e2"}, {"s1", "s2", "x"}
        assert select_people("store", cast, store, tier) == {"s1"}
        assert select_people("extension", cast, store, tier) == {"e1"}
        assert select_people("pooled", cast, store, tier) == {"s1", "e1"}
        assert select_people("tierC", cast, store, tier) == {"s2", "e2"}   # in or out of store
