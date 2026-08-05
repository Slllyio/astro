"""The interactive report page's v33 movement structure.

The manuscript at GET /report/page renders client-side from the `/report` JSON, so the
Python contract test cannot see it. These tests pin the template itself: one folio per
movement, every rendered section routed to the movement that owns it, and the connective
passages reaching the page through the report JSON.

They also RECORD the interactive page's coverage gap — it renders 28 of the 53 contracted
sections — so that the number can only ever move in the direction REPORT COMPLETENESS wants.
The gap predates v33; the movement grouping is simply what made it measurable.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import SECTION_CONTRACT, build_detailed_report
from app.raman_saab.report_json import to_report_dict
from app.raman_saab.report_movements import MOVEMENTS, movement_of

_TEMPLATE = pathlib.Path(__file__).resolve().parents[2] / "app" / "medini" / "templates" / "report.html"
_PAGE_ONLY = {"_muhurtha"}


@pytest.fixture(scope="module")
def template() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def routed(template: str) -> tuple[str, ...]:
    """Every section id the page routes with a sec('...') marker, in source order."""
    return tuple(re.findall(r"sec\('([a-z_]+)'\); add\(H2", template))


class TestManuscriptFolios:
    def test_one_folio_per_movement_plus_the_colophon(self, template: str) -> None:
        """Seven chapter folios (one per movement) — the colophon keeps `nichod` last."""
        pages = re.findall(r'<div class="leaf" data-page="(\d+)"', template)
        assert pages == [str(i) for i in range(len(MOVEMENTS) + 3)], pages
        for i, mv in enumerate(MOVEMENTS, start=2):
            assert f'id="leaf{i}-body"' in template, f"no folio for movement {mv.numeral}"
            assert f"folio {mv.numeral} · {mv.title.lower()}" in template

    def test_nav_labels_match_the_folios(self, template: str) -> None:
        """manuscript.js indexes by DOM order, so the label list must be the same length."""
        raw = re.search(r"window\.MANUSCRIPT_LABELS = \[(.*?)\];", template, re.S).group(1)
        labels = [x.strip().strip("'") for x in raw.split(",")]
        pages = re.findall(r'<div class="leaf" data-page="\d+"', template)
        assert len(labels) == len(pages)
        assert labels[0] == "COVER" and labels[-1] == "NICHOD"
        for i, mv in enumerate(MOVEMENTS, start=2):
            assert labels[i] == f"{mv.numeral}. {mv.title.upper()}"

    def test_every_routed_section_is_real_and_unique(self, routed: tuple[str, ...]) -> None:
        """A typo in a sec('...') id would silently drop that section off the page."""
        known = {s.section_id for s in SECTION_CONTRACT} | _PAGE_ONLY
        unknown = [s for s in routed if s not in known]
        assert not unknown, f"sec() ids not in the contract: {unknown}"
        assert len(routed) == len(set(routed)), "a section is routed twice"

    def test_every_routed_section_belongs_to_a_movement(self, routed: tuple[str, ...]) -> None:
        """The flush walks R.movements, so an unplaced section would never be appended."""
        for sid in routed:
            if sid in _PAGE_ONLY:
                continue
            assert movement_of(sid) is not None, f"{sid!r} is routed but not in any movement"

    def test_the_old_folio_machinery_is_gone(self, template: str) -> None:
        """chapter()/MOVEMENT_OF_FOLIO grouped by folio; v33 groups by movement instead.
        Leaving either behind would mean two competing orders in one file."""
        assert "MOVEMENT_OF_FOLIO" not in template
        assert not re.search(r"\bchapter\(\d+\)", template)

    def test_page_builds_nodes_with_safe_dom_only(self, template: str) -> None:
        """Locked project rule: createElement/textContent, never innerHTML, in this code."""
        flush = template[template.index("const PAGE_ONLY="):]
        flush = flush[:flush.index("function ") if "function " in flush else len(flush)]
        assert "innerHTML" not in flush


class TestMovementDataReachesThePage:
    def test_report_json_carries_every_movement_and_passage(self) -> None:
        """The page reads the arc from the JSON — without this key it renders nothing."""
        r = build_detailed_report(BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59))
        movements = to_report_dict(r)["movements"]
        assert len(movements) == len(MOVEMENTS)
        for got, mv in zip(movements, MOVEMENTS):
            assert got["numeral"] == mv.numeral and got["title"] == mv.title
            assert tuple(got["sections"]) == mv.section_ids
            assert got["passage"].strip(), f"movement {mv.numeral} reached the page mute"


class TestCoverageGap:
    """The interactive page renders a SUBSET of the report. Recorded, not endorsed."""

    #: measured 2026-08-05, immediately after the v33 folio unification.
    _KNOWN_RENDERED = 28

    def test_gap_is_recorded_and_may_only_shrink(self, routed: tuple[str, ...]) -> None:
        """REPORT COMPLETENESS says every surface shows everything the report computes. The
        page is at 28/53 — a gap that predates v33. This test fails if it WIDENS, and fails
        (asking to be updated) if it closes, so the number can never drift unnoticed."""
        rendered = {s for s in routed if s not in _PAGE_ONLY}
        assert len(rendered) >= self._KNOWN_RENDERED, (
            f"the interactive page now renders {len(rendered)} sections, down from "
            f"{self._KNOWN_RENDERED} — a section was dropped from a surface")
        if len(rendered) > self._KNOWN_RENDERED:
            pytest.fail(
                f"good news: the page now renders {len(rendered)} of {len(SECTION_CONTRACT)} "
                f"sections. Raise _KNOWN_RENDERED to {len(rendered)} and record which sections "
                f"were added.")

    def test_the_missing_sections_are_named(self, routed: tuple[str, ...]) -> None:
        """Name them, so the gap is a list someone can work through rather than a number.
        Movement V is the worst hit: career, wealth, marriage and children — the matters a
        reader most wants — are computed by the engine but never shown on this surface."""
        rendered = {s for s in routed if s not in _PAGE_ONLY}
        missing = [s.section_id for s in SECTION_CONTRACT if s.section_id not in rendered]
        assert "career" in missing and "marriage" in missing, (
            "these were missing when the gap was recorded; if they now render, update this "
            "test and _KNOWN_RENDERED together")
        assert len(missing) == len(SECTION_CONTRACT) - len(rendered)
