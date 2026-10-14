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
    """Every section id the page routes with a sec('...') marker, in source order.

    Matches the marker alone, NOT `sec('x'); add(H2(` — a section whose heading sits on the
    next line, or inside a conditional, is routed just as much as one written inline, and an
    over-strict pattern here reports a completeness gap that does not exist.
    """
    return tuple(re.findall(r"\bsec\('([a-z_]+)'\)", template))


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

    def test_every_routed_section_is_real(self, routed: tuple[str, ...]) -> None:
        """A typo in a sec('...') id would silently drop that section off the page: the
        buffer would fill under a name the movement flush never asks for."""
        known = {s.section_id for s in SECTION_CONTRACT} | _PAGE_ONLY
        unknown = [s for s in routed if s not in known]
        assert not unknown, f"sec() ids not in the contract: {unknown}"

    def test_only_documented_ids_are_routed_more_than_once(self, routed: tuple[str, ...]) -> None:
        """Re-selecting a bucket is legal — `sec('nichod')` is issued a second time so the
        feedback card lands on the colophon beside the Nichod. Any OTHER repeat means two
        blocks are writing the same section, which is how a section silently doubles."""
        repeated = {s for s in routed if routed.count(s) > 1}
        assert repeated <= {"nichod"}, f"unexpected repeated routes: {sorted(repeated)}"

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


class TestCoverageIsComplete:
    """REPORT COMPLETENESS on the interactive surface: every contracted section renders.

    History worth keeping: unifying the folios to the movements made the page's coverage
    countable for the first time, and the count was **28 of 53**. Movement V — the matters a
    reader actually opens the page for — was 2/10: career, profession, wealth, marriage,
    children, arishta, maraka and maraka_saturn were all computed by the engine and shown on
    no surface here. The gap was closed in the same arc (2026-08-05).
    """

    def test_every_contracted_section_is_rendered(self, routed: tuple[str, ...]) -> None:
        """The whole point of the directive: no section may be computed and then hidden."""
        rendered = {s for s in routed if s not in _PAGE_ONLY}
        missing = [s.section_id for s in SECTION_CONTRACT if s.section_id not in rendered]
        assert not missing, (
            f"the interactive page renders {len(rendered)} of {len(SECTION_CONTRACT)} "
            f"sections; REPORT COMPLETENESS forbids hiding these: {missing}")

    def test_every_movement_is_fully_covered(self, routed: tuple[str, ...]) -> None:
        """Reported per movement, because that is how the gap became visible in the first
        place — a bare total hid that one movement was at 2/10 while others were near-full."""
        rendered = {s for s in routed if s not in _PAGE_ONLY}
        short = {mv.numeral: [s for s in mv.section_ids if s not in rendered]
                 for mv in MOVEMENTS}
        short = {k: v for k, v in short.items() if v}
        assert not short, f"movements with unrendered sections: {short}"

    def test_the_matters_of_life_are_all_present(self, routed: tuple[str, ...]) -> None:
        """A named regression guard for the eight that were missing. These are the sections a
        reader came for; losing them again should fail loudly and by name."""
        for sid in ("career", "profession", "wealth", "marriage", "children",
                    "arishta", "maraka", "maraka_saturn"):
            assert sid in routed, f"{sid!r} dropped off the interactive page again"
