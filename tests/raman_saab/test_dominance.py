"""Dominance — naming which planet governs a house when its factors disagree.

The tests that matter here are the ones guarding against a confident, well-cited, tautological
answer. The first implementation read the preponderance ledger's testimony leans and let the
`strong` side beat the `weak` side; it looked right and could only ever return "favourable",
because strength and direction are the same axis in that ledger. These tests pin the properties
that catch that class of mistake.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.dominance import STRENGTH_CITE, house_dominance

_CHARTS = [
    ("canonical", BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("scorpio", BirthData("Scorpio", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
    ("mumbai", BirthData("Mumbai", 1975, 3, 3, 4, 30, 5.5, 19.07, 72.87)),
    ("delhi", BirthData("Delhi", 2001, 11, 9, 21, 15, 5.5, 28.61, 77.20)),
]


@pytest.fixture(scope="module")
def reports():
    return {name: build_detailed_report(bd) for name, bd in _CHARTS}


class TestNotTautological:
    def test_dominance_can_return_an_adverse_direction(self, reports):
        """THE regression guard. A rule that can only ever name the favourable side as the
        winner is not reading the chart — it is restating that strength is coded favourable.
        Across a spread of charts, adverse governance must actually occur."""
        directions = {d.direction
                      for r in reports.values() for d in house_dominance(r).values()}
        assert "adverse" in directions, (
            "dominance never returns adverse across five charts — the rule has collapsed into "
            "'the strong side wins' again, which is an optimistic bias, not a judgment")

    def test_direction_follows_the_governing_planet_not_the_contest(self, reports):
        """Direction comes from the winner's functional nature for THAT ascendant, so the same
        planet may govern favourably in one chart and adversely in another."""
        from app.raman_saab.dominance import DIRECTION
        for r in reports.values():
            for d in house_dominance(r).values():
                assert d.nature in DIRECTION, (
                    f"unmapped functional nature {d.nature!r} — it would silently fall through "
                    f"to 'mixed'. yogakaraka was caught exactly this way.")
                assert DIRECTION[d.nature] == d.direction


class TestRestraint:
    def test_declares_nothing_when_the_comparison_does_not_decide(self, reports):
        """Raman's test is a COMPARISON — "the Sun is stronger". A house whose lord and karaka
        are both strong, or both weak, is left to the existing both-poles disclosure rather
        than given a manufactured winner."""
        r = reports["canonical"]
        by_house = {pf.house: pf for pf in r.proformas}
        for house, dom in house_dominance(r).items():
            led = by_house[house].significations[0].ledger
            assert led.lord_strong != led.karaka_strong, (
                f"H{house} resolved though its lord and karaka agree in strength")

    def test_never_resolves_when_lord_and_karaka_are_the_same_planet(self, reports):
        """A planet cannot overrule itself."""
        for r in reports.values():
            by_house = {pf.house: pf for pf in r.proformas}
            for house in house_dominance(r):
                led = by_house[house].significations[0].ledger
                assert led.lord != led.karaka


class TestContract:
    def test_every_resolution_carries_ramans_own_citation(self, reports):
        """The rule is his, not ours: "the Sun is stronger, being in his own sign"."""
        for r in reports.values():
            for d in house_dominance(r).values():
                assert STRENGTH_CITE in d.cites
                assert d.governing and d.yielding and d.governing != d.yielding

    def test_sentences_pass_the_llm_guard(self, reports):
        """Composed prose is held to the same wording contract as every other surface."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for r in reports.values():
            for d in house_dominance(r).values():
                m = _FORBIDDEN_RE.search(d.sentence)
                assert m is None, f"dominance sentence trips the guard: {m.group(0)!r}"

    def test_is_a_pure_re_read(self, reports):
        """PREC-10: dominance names a winner among values the engine already computed. It must
        introduce no planet that is not already this house's lord or karaka."""
        for r in reports.values():
            by_house = {pf.house: pf for pf in r.proformas}
            for house, d in house_dominance(r).items():
                led = by_house[house].significations[0].ledger
                assert {d.governing, d.yielding} == {led.lord, led.karaka}
