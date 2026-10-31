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

    def test_marriage_houses_are_krishnamurtis(self) -> None:
        """KPR3:14306 houses 2, 7, 11; KPR3:21495 denial 1, 6, 10, 12 on the 7th cusp."""
        m = MATTERS["marriage"]
        assert (m.cusp, m.favourable, m.denial) == (7, {2, 7, 11}, {1, 6, 10, 12})

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
        assert "KPR3:14306-14307" in md and "1 1 are examined" in md

    def test_timing_windows_lords_signify_favourable(self) -> None:
        """Every candidate period's three lords signify a favourable house."""
        from app.kp.chart import cast
        from app.kp.significators import houses_signified
        v = judge(NATIVE_1922, "marriage", timing_years=(15, 30))
        ch = cast(NATIVE_1922)
        for t in v.timing:
            assert all(houses_signified(ch, lord) & v.matter.favourable for lord in t.period.lords)
