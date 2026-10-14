"""Saravali ch.45 — the "N planets share a dignity" concentration verdicts.

Pins the full 5-dignity x count-2..7 ladder, citation resolution, the count-word parse (incl. 7 as
both "seven" and "all"), the single-highest-dignity partition used for counting, and that a chart
with two grahas in a dignity surfaces the verdict.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.saravali_dignity import (
    active_concentrations,
    all_concentration_effects,
    concentration_effect,
    dignity_counts,
    graha_dignity,
)
from app.parashara.doctrine.sources import verify

_DIGNITIES = ("exalted", "moolatrikona", "own", "friendly", "debilitated")


class TestConcentrationGrid:
    def test_full_ladder_every_dignity(self):
        g = all_concentration_effects()
        assert len(g) == 30                      # 5 dignities x counts 2..7
        for d in _DIGNITIES:
            for c in range(2, 8):
                assert (d, c) in g, (d, c)

    def test_every_citation_resolves(self):
        for s in all_concentration_effects().values():
            assert verify(s.source) and s.source.work == "SARAVALI-45"

    def test_all_seven_exalted_is_the_emperor_verdict(self):
        assert "emperor" in concentration_effect("exalted", 7).text.lower()

    def test_two_exalted_is_rich_and_famous(self):
        assert "famous" in concentration_effect("exalted", 2).text.lower()

    def test_each_rung_speaks_of_its_own_count(self):
        # the parsed sentence for count N must not be the sentence for a different count
        for d in _DIGNITIES:
            texts = {c: concentration_effect(d, c).text for c in range(2, 8)}
            assert len(set(texts.values())) == 6, d      # all six rungs distinct

    def test_bad_dignity_raises(self):
        with pytest.raises(ValueError):
            concentration_effect("combust", 2)

    def test_count_out_of_range_raises(self):
        with pytest.raises(ValueError):
            concentration_effect("exalted", 1)


class TestDignityPartition:
    def test_exalted(self):
        assert graha_dignity("Sun", 1) == "exalted"        # Sun in Aries

    def test_moolatrikona_wins_over_own(self):
        assert graha_dignity("Sun", 5) == "moolatrikona"   # Leo is Sun's MT sign (and own)

    def test_own_when_not_mt(self):
        assert graha_dignity("Moon", 4) == "own"           # Cancer, Moon's own (MT is Taurus)

    def test_debilitated(self):
        assert graha_dignity("Sun", 7) == "debilitated"    # Libra

    def test_neutral_or_friendly_is_returned_for_other_signs(self):
        assert graha_dignity("Sun", 3) in {"friendly", "neutral"}


class TestChartFacing:
    def test_counts_partition_the_seven(self):
        # every graha lands in exactly one bucket; counts never exceed 7
        signs = {"Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6, "Jupiter": 4, "Venus": 12, "Saturn": 7}
        counts = dignity_counts(signs)
        assert counts["exalted"] == 7            # all placed in exaltation signs above
        assert sum(counts.values()) <= 7

    def test_two_sharing_a_dignity_surfaces_a_verdict(self):
        hits = active_concentrations({"Sun": 1, "Moon": 2})   # both exalted
        assert hits["exalted"][0] == 2
        assert verify(hits["exalted"][1].source)

    def test_no_concentration_is_empty(self):
        # a single exalted graha is not a concentration
        assert active_concentrations({"Sun": 1, "Moon": 4}) == {}
