"""v43 — "For and against, matter by matter" (app/raman_saab/for_against.py): a pure re-read."""
from __future__ import annotations

import dataclasses

import pytest

from app.raman_saab.detailed_report import BirthData, build_detailed_report, to_markdown
from app.raman_saab.for_against import (LEAN_AGAINST, LEAN_EVEN, LEAN_FOR, LEAN_SILENT, NOTICE,
                                        for_against, lean_of)

_MAINPURI = BirthData("Native of Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.02)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_MAINPURI)


def test_lean_is_the_plain_count() -> None:
    assert lean_of(3, 1) == LEAN_FOR
    assert lean_of(1, 3) == LEAN_AGAINST
    assert lean_of(2, 2) == LEAN_EVEN
    assert lean_of(0, 0) == LEAN_SILENT


def test_every_reason_carries_a_citation(report) -> None:
    fa = report.for_against
    assert fa.matters
    for m in fa.matters:
        for x in m.reasons_for + m.reasons_against:
            assert ":" in x.cite and x.rule_id


def test_counts_match_the_ledgers(report) -> None:
    by = {(m.house, m.matter): m for m in report.for_against.matters}
    for pf in report.proformas:
        for sv in pf.significations:
            m = by[(pf.house, sv.signification.replace("_", " "))]
            assert len(m.reasons_for) == len({f.rule.id for f in sv.ledger.fired_benefic})
            assert len(m.reasons_against) == len({f.rule.id for f in sv.ledger.fired_malefic})


def test_it_changes_no_verdict(report) -> None:
    before = [(pf.house, sv.signification, sv.verdict)
              for pf in report.proformas for sv in pf.significations]
    for_against(dataclasses.replace(report))
    after = [(pf.house, sv.signification, sv.verdict)
             for pf in report.proformas for sv in pf.significations]
    assert before == after


def test_section_renders_with_the_notice(report) -> None:
    md = to_markdown(report)
    assert "## For and against, matter by matter" in md
    assert NOTICE in md
