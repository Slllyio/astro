"""Analogy — recognising which of Raman's own charts a nativity recalls.

A resemblance engine fails in a characteristic way: it always finds something. Cosine similarity
over enough features will rank *some* chart highest for every query, and the output reads as
insight while carrying none. These tests pin the three properties that separate recognition from
coincidence generation — it must be able to find nothing, different charts must recall different
examples, and every claim must be itemised so a reader can check it.
"""
from __future__ import annotations

import pytest

from app.raman_saab.analogy import FLOOR, resembles
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData

_CHARTS = [
    ("canonical", BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("scorpio", BirthData("Scorpio", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
    ("mumbai", BirthData("Mumbai", 1975, 3, 3, 4, 30, 5.5, 19.07, 72.87)),
    ("delhi", BirthData("Delhi", 2001, 11, 9, 21, 15, 5.5, 28.61, 77.20)),
    ("kolkata", BirthData("Kolkata", 1960, 6, 1, 9, 0, 5.5, 22.57, 88.36)),
]


@pytest.fixture(scope="module")
def charts():
    return {name: cast_chart(bd) for name, bd in _CHARTS}


class TestNotACoincidenceGenerator:
    def test_some_charts_resemble_nothing(self, charts):
        """THE guard. An engine that always finds a match has found nothing — it has only
        ranked. Across a spread of charts, some must come back empty."""
        empty = [n for n, c in charts.items() if not resembles(c)]
        assert empty, ("every chart matched something — the floor is too low and this is "
                       "ranking noise, not recognition")

    def test_different_charts_recall_different_examples(self, charts):
        """If one worked example is the nearest neighbour of everything, the metric is measuring
        that chart's typicality, not any resemblance."""
        tops = [ms[0].chart_id for c in charts.values() if (ms := resembles(c))]
        assert len(set(tops)) > 1, f"all charts collapse onto {tops[:1]} — degenerate metric"

    def test_nothing_below_the_floor_is_offered(self, charts):
        for c in charts.values():
            for m in resembles(c):
                assert m.score >= FLOOR


class TestItemised:
    def test_every_match_says_what_is_shared(self, charts):
        """A bare score is unfalsifiable. Each match must name the respects, so a reader can
        disagree with it."""
        for c in charts.values():
            for m in resembles(c):
                assert m.shared, f"{m.chart_id} matched with no stated respects"
                assert all(isinstance(s, str) and s.strip() for s in m.shared)

    def test_every_match_points_at_something_raman_wrote(self, charts):
        """A resemblance is an invitation to go and read him. It is worthless if it does not
        say where to look."""
        for c in charts.values():
            for m in resembles(c):
                assert m.citations or m.pronounced_houses, (
                    f"{m.chart_id} points at no citation and no pronounced house")
                assert m.book and m.name


class TestContract:
    def test_ordered_strongest_first(self, charts):
        for c in charts.values():
            scores = [m.score for m in resembles(c)]
            assert scores == sorted(scores, reverse=True)

    def test_respects_the_limit(self, charts):
        for c in charts.values():
            assert len(resembles(c, limit=2)) <= 2

    def test_transfers_no_verdict(self, charts):
        """PREC-10. A resemblance carries the neighbour's IDENTITY and citation, never its
        judgment — the reader is pointed at what Raman wrote, not told it applies here."""
        for c in charts.values():
            for m in resembles(c):
                fields = set(vars(m))
                assert "verdict" not in fields and "rollup" not in fields
