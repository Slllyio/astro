"""Saravali ch.15 — two-planet conjunction effects (the 21-pair grid).

Pins full C(7,2) coverage, citation resolution, recovery of the OCR-mangled "II." sloka
(Moon-Venus) via header parsing, order-independent lookup, and the chart-facing detector (grahas
sharing a sign, three-in-a-sign yielding all three pairs).
"""
from __future__ import annotations

from itertools import combinations

import pytest

from app.parashara.doctrine.saravali_conjunctions import (
    active_conjunctions,
    all_conjunctions,
    conjunction_effect,
)
from app.parashara.doctrine.sources import verify

_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


class TestGrid:
    def test_all_21_pairs_present(self):
        g = all_conjunctions()
        assert len(g) == 21
        for a, b in combinations(_GRAHAS, 2):
            assert frozenset({a, b}) in g, (a, b)

    def test_every_citation_resolves(self):
        for s in all_conjunctions().values():
            assert verify(s.source) and s.source.work == "SARAVALI-15"

    def test_moon_venus_recovered_despite_ocr_number(self):
        # its sloka number scanned as roman "II."; the header recovered it
        eff = conjunction_effect("Moon", "Venus")
        assert eff is not None and "MOON-VENUS" in eff.text.upper()

    def test_lookup_is_order_independent(self):
        assert conjunction_effect("Sun", "Moon") is conjunction_effect("Moon", "Sun")

    def test_bad_args_raise(self):
        with pytest.raises(ValueError):
            conjunction_effect("Sun", "Sun")
        with pytest.raises(ValueError):
            conjunction_effect("Rahu", "Moon")


class TestChartDetector:
    def test_no_conjunction_when_all_apart(self):
        lons = {g: (i * 40.0) for i, g in enumerate(_GRAHAS)}   # each in a distinct sign
        assert active_conjunctions(lons) == []

    def test_two_in_a_sign_is_one_pair(self):
        lons = {"Sun": 5.0, "Moon": 8.0, "Mars": 100.0, "Mercury": 130.0,
                "Jupiter": 200.0, "Venus": 250.0, "Saturn": 300.0}
        ac = active_conjunctions(lons)
        assert len(ac) == 1 and ac[0][0] == frozenset({"Sun", "Moon"})

    def test_three_in_a_sign_yields_all_three_pairs(self):
        lons = {"Sun": 5.0, "Moon": 8.0, "Mars": 12.0, "Mercury": 130.0,
                "Jupiter": 200.0, "Venus": 250.0, "Saturn": 300.0}
        pairs = {p for p, _ in active_conjunctions(lons)}
        assert pairs == {frozenset({"Sun", "Moon"}), frozenset({"Sun", "Mars"}),
                         frozenset({"Moon", "Mars"})}
