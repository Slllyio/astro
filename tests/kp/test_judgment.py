"""KP judgment: verdict logic, citations wired, stability window, no outcome input."""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.kp.citations import CITATIONS
from app.kp.judgment import (
    DENIED, MATTERS, MIXED, NOT_SIGNIFIED, PROMISED, classify, generic_matter, judge,
)
from tests.kp.test_chart import NATIVE_1922


class TestClassify:
    @pytest.mark.parametrize("fav,den,want", [
        ({7}, set(), PROMISED), (set(), {6}, DENIED), ({2}, {12}, MIXED), (set(), set(), NOT_SIGNIFIED),
    ])
    def test_ruling_r12_table(self, fav, den, want) -> None:
        """Favourable only -> PROMISED, denial only -> DENIED, both -> MIXED (no tie-break)."""
        assert classify(fav, den) == want


class TestMatters:
    def test_every_matter_citation_exists(self) -> None:
        """Every citation key a matter names is in the registry."""
        for m in MATTERS.values():
            assert all(c in CITATIONS for c in m.citations), m.key

    def test_marriage_houses_are_reader4s(self) -> None:
        """KPR4 p.121 promise on 2, 7, 11; p.106 denial on 4, 6, 10, both from the 7th cusp."""
        m = MATTERS["marriage"]
        assert (m.cusp, m.favourable, m.denial) == (7, {2, 7, 11}, {4, 6, 10})

    def test_generic_denial_is_6_8_12_from_house(self) -> None:
        """KPR3-6812: for house 5 the denial houses are 10, 12 and 4."""
        assert generic_matter(5).denial == {10, 12, 4}


class TestVerdict:
    def test_fired_rules_are_csl_significations(self) -> None:
        """Every fired rule is a signification of the cusp sub-lord on a judged house."""
        v = judge(NATIVE_1922, "marriage")
        assert all(s.planet == v.csl for s in v.fired)
        assert {s.house for s in v.fired} == v.csl_houses & (v.matter.favourable | v.matter.denial)

    def test_stability_window_counts_every_minute(self) -> None:
        """A ±3 minute window is scanned at 7 one-minute steps."""
        v = judge(replace(NATIVE_1922, uncertainty_minutes=3), "marriage")
        assert sum(v.stability.values()) == 7

    def test_record_has_no_outcome_field(self) -> None:
        """The engine takes no outcome; the sealed record carries none."""
        d = judge(NATIVE_1922, "wealth").to_dict()
        assert not {"outcome", "actual", "truth", "event"} & set(d)

    def test_markdown_cites_quotes(self) -> None:
        """The reading prints each citation reference and quote."""
        md = judge(NATIVE_1922, "marriage").to_markdown()
        assert "KPR4:p.106" in md and "4, 6, 10th houses" in md

    def test_timing_windows_lords_signify_favourable(self) -> None:
        """Every candidate period's three lords signify a favourable house."""
        from app.kp.chart import cast
        from app.kp.significators import houses_signified
        v = judge(NATIVE_1922, "marriage", timing_years=(15, 30))
        ch = cast(NATIVE_1922)
        for t in v.timing:
            assert all(houses_signified(ch, lord) & v.matter.favourable for lord in t.period.lords)


class TestTieBreak:
    """Ruling R18, as Krishnamurti settles his own case at KPR4 p.106."""

    @staticmethod
    def _sig(planet, house, level, agent=False):
        from app.kp.significators import Signification
        return Signification(planet, house, level, planet, agent)

    def _resolve(self, csl_rows, sub_rows):
        from types import SimpleNamespace
        from app.kp.judgment import resolve
        chart = SimpleNamespace(planets={"Rahu": SimpleNamespace(sub_lord="Saturn")})
        sigs = {"Rahu": tuple(csl_rows), "Saturn": tuple(sub_rows)}
        return resolve(chart, MATTERS["marriage"], "Rahu", sigs)

    def test_krishnamurtis_denial_case(self) -> None:
        """Rahu occupies 6 (B) and stands for the lord of 7 (D): '6th house result is stronger'."""
        v = self._resolve([self._sig("Rahu", 6, "B"), self._sig("Rahu", 7, "D", True)],
                          [self._sig("Saturn", 12, "B")])
        assert v == (DENIED, MIXED, "level")

    def test_stronger_favourable_level_promises(self) -> None:
        """In the star of an occupant of 7 (A) beats lordship of 10 (D)."""
        v = self._resolve([self._sig("Rahu", 7, "A"), self._sig("Rahu", 10, "D")], [])
        assert v == (PROMISED, MIXED, "level")

    def test_same_level_goes_to_sub_lord(self) -> None:
        """Same level on both sides: the CSL's sub-lord decides ('the sub lord ... mainly responsible')."""
        v = self._resolve([self._sig("Rahu", 6, "B"), self._sig("Rahu", 7, "B")],
                          [self._sig("Saturn", 11, "C")])
        assert v == (PROMISED, MIXED, "sub_lord")

    def test_unresolved_stays_mixed(self) -> None:
        """If the sub-lord also touches both groups, nothing is invented."""
        v = self._resolve([self._sig("Rahu", 6, "B"), self._sig("Rahu", 7, "B")],
                          [self._sig("Saturn", 2, "C"), self._sig("Saturn", 4, "C")])
        assert v == (MIXED, MIXED, "unresolved")


class TestChildren:
    def test_children_houses(self) -> None:
        """KPR3:21258-21262: 5th sub-lord on 2, 5, 11 gives a child; on 1, 4, 10 never."""
        m = MATTERS["children"]
        assert (m.cusp, m.favourable, m.denial) == (5, {2, 5, 11}, {1, 4, 10})
