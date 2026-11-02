"""Tin Win's House Grouping rows (rulings LR8-LR10)."""

from __future__ import annotations

import re

from app.kp.chart import Birth, cast
from app.kp.later.citations import LATER_CITATIONS
from app.kp.later.tin_win import (
    CITATION,
    TIN_WIN_ROWS,
    TinWinRow,
    row_holds,
    tin_win_indications,
)

BANGALORE = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)


def _row(groups, two=False, no=()) -> TinWinRow:
    return TinWinRow(0, 79, 7, "test", groups, two, no, "natal")


class TestRows:
    def test_row_count_and_cusps(self) -> None:
        """316 of the 457 transcribed rows are encoded; every cusp is 1-12 and every page 70-91."""
        assert len(TIN_WIN_ROWS) == 316
        assert all(1 <= r.cusp <= 12 and 70 <= r.page <= 91 for r in TIN_WIN_ROWS)

    def test_marriage_row_is_the_authors_example(self) -> None:
        """KNR p.79 row 'Marriage' under cusp 7 is 7,11,2: his own example of 2 or 7 or 11."""
        m = [r for r in TIN_WIN_ROWS if r.cusp == 7 and r.event == "Marriage"]
        assert len(m) == 1 and m[0].groups == ((7, 11, 2),) and not m[0].at_least_two

    def test_no_death_or_moral_rows(self) -> None:
        """Rulings LR3/LR7: no death, lifespan, danger to life or moral-character rows are encoded."""
        bad = re.compile(r"death|suicide|long life|short life|danger to life|illicit|dacoit|raping", re.I)
        assert not [r.event for r in TIN_WIN_ROWS if bad.search(r.event)]

    def test_citation_registered(self) -> None:
        """The method quote is registered under KNR, scan 172."""
        assert LATER_CITATIONS[CITATION].source == "KNR" and LATER_CITATIONS[CITATION].page == 172


class TestGroupLogic:
    def test_any_house_per_group(self) -> None:
        """LR9: '2,7,11' needs one of them."""
        assert row_holds(_row(((2, 7, 11),)), frozenset({11}))
        assert not row_holds(_row(((2, 7, 11),)), frozenset({6}))

    def test_ampersand_needs_both_groups(self) -> None:
        """LR9: '2 & 11' needs 2 and 11."""
        assert not row_holds(_row(((2,), (11,))), frozenset({2}))
        assert row_holds(_row(((2,), (11,))), frozenset({2, 11}))

    def test_jointly_needs_two(self) -> None:
        """LR9: 'should operate jointly, not separately' needs two or more of the houses."""
        assert not row_holds(_row(((2, 6, 10, 11),), two=True), frozenset({10}))
        assert row_holds(_row(((2, 6, 10, 11),), two=True), frozenset({6, 10}))

    def test_not_connected_blocks(self) -> None:
        """LR9: 'Not connected to 5,8,12' fails on any of them."""
        assert not row_holds(_row(((2, 6, 10, 11),), no=(5, 8, 12)), frozenset({2, 8}))


class TestOnChart:
    def test_fired_rows_carry_framing(self) -> None:
        """Every fired row names Tin Win and the later-author framing."""
        fired = tin_win_indications(cast(BANGALORE))
        assert fired
        d = fired[0].to_dict()
        assert d["author"] == "Tin Win" and "not Krishnamurti" in d["framing"]
