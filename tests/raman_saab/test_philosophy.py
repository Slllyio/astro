"""v42 — "How Raman would weigh this chart" (app/raman_saab/philosophy.py): a pure re-read."""
from __future__ import annotations

import dataclasses

import pytest

from app.raman_saab.detailed_report import BirthData, build_detailed_report, to_markdown
from app.raman_saab.philosophy import FRAME, PRINCIPLES, chart_philosophy

_MAINPURI = BirthData("Native of Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.02)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_MAINPURI)


def test_every_frame_and_principle_carries_a_citation() -> None:
    for _h, quote, cite, _m in FRAME:
        assert quote and ":" in cite
    for _t, _how, quote, cite in PRINCIPLES.values():
        assert quote and ":" in cite


def test_it_changes_no_verdict(report) -> None:
    before = [(pf.house, sv.signification, sv.verdict)
              for pf in report.proformas for sv in pf.significations]
    chart_philosophy(dataclasses.replace(report))
    after = [(pf.house, sv.signification, sv.verdict)
             for pf in report.proformas for sv in pf.significations]
    assert before == after


def test_dusthana_matters_never_read_as_good_withheld(report) -> None:
    ph = report.philosophy
    for w in ph.houses:
        if w.principle in ("weakness-not-evil", "two-of-three", "strength-carries"):
            assert all(h not in (6, 8, 12) for h, _ms in w.houses)


def test_section_renders(report) -> None:
    md = to_markdown(report)
    assert "## How Raman would weigh this chart" in md
    assert "HTJAH-I:3871-3878" in md
