"""The report template contract — the section set is FROZEN (append-only).

docs/raman_saab/REPORT_TEMPLATE.md is the human contract; SECTION_CONTRACT in
detailed_report.py is the machine registry. This test is the ratchet: removing, renaming or
reordering any existing section in EITHER renderer fails here. New sections may only be APPENDED
to the registry with a new `since` tag (and this file's frozen v1/v2 lists updated in the same
commit, consciously).
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import (
    HTML_SECTION_ORDER,
    SECTION_CONTRACT,
    build_detailed_report,
    to_markdown,
)
from app.raman_saab.report_html import to_html

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

#: The frozen registry as of the freeze commit — ids AND marker strings, copied here BY HAND so
#: that editing the module's SECTION_CONTRACT alone cannot silently re-freeze the template: any
#: marker change must consciously touch this file too. Append-only: may only ever GROW.
_FROZEN = (
    ("title", "# Detailed reading", 'class="name"'),
    # v5 amendment (2026-07-26, conscious, same-commit as the module): "Your Reading" is the
    # ONE deliberate exception to "append at the end" — it must come FIRST after the title,
    # since it exists specifically to be read before every technical section below it.
    ("plain_reading", "## Your Reading", 'id="plain-reading"'),
    ("now_box", None, 'class="nowbox"'),
    ("info_content", "## Information content of this reading", 'class="infobox"'),
    ("stands_out", "## What stands out in this chart", 'id="stands-out"'),
    ("dashboard", "## The twelve matters at a glance", 'id="dashboard"'),
    ("chart_signature", "## Chart signature", 'class="sig"'),
    ("chart_grids", None, 'id="charts"'),
    ("positions", "## Planetary positions", 'id="positions"'),
    ("shadbala", "## Shadbala", 'id="shadbala"'),
    ("yogas", "## Yogas present in this chart", 'id="yogas"'),
    # v7 amendment (2026-07-26, conscious, same-commit as the module): Yoga x Dasha timing
    # inserted right after Yogas — it directly extends that section with WHEN.
    ("yoga_timing", "## Yoga x Dasha timing", 'id="yoga-timing"'),
    ("ashtakavarga", "## Ashtakavarga", 'id="sav"'),
    ("houses", "## House-by-house reading", 'id="houses"'),
    # v8 amendment (2026-07-26, conscious, same-commit as the module): House strength
    # cross-check inserted right after House-by-house — the natural narrative position.
    ("house_strength", "## House strength cross-check", 'id="house-strength"'),
    ("longevity", "## Longevity", 'id="longevity"'),
    ("maraka", "## The maraka scheme", 'id="maraka"'),
    ("timeline", "## Life-narrative (Vimshottari Dasha)", 'id="timeline"'),
    ("gochara", "## Current transits (Gochara", 'id="gochara"'),
    # v6 amendment (2026-07-26, conscious, same-commit as the module): the Dasha x Transit
    # confluence, inserted right after Gochara — the natural narrative position, since it
    # cross-references the Life-narrative and Gochara sections directly above it.
    ("dasha_transit", "## Dasha x Transit confluence", 'id="dasha-transit"'),
    ("divisional", "## Divisional deep-reads (Shodasavarga)", 'id="vargas"'),
    ("career", "## Career (HTJAH-II", 'id="career"'),
    ("deeptadi", "## Deeptadi avasthas", 'id="deeptadi"'),
    ("karakamsa", "## Jaimini Karakamsa", 'id="karakamsa"'),
    ("soul", "## Soul & destiny", 'id="soul"'),
    ("pitru", "## Pitru dosha", 'id="pitru"'),
    # v3 amendment (2026-07-25, conscious, same-commit as the module): Integrated insights
    # inserted before the glossary so reference material stays last.
    ("synthesis", "## Integrated insights", 'id="synthesis"'),
    ("glossary", "## Glossary", 'id="glossary"'),
    # v4 amendment (2026-07-26, conscious, same-commit as the module): the Nichod capstone,
    # appended LAST — after reference material — since it distils the whole document.
    ("nichod", "## Nichod", 'id="nichod"'),
)
_FROZEN_IDS = tuple(row[0] for row in _FROZEN)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def markdown(report):
    return to_markdown(report)


@pytest.fixture(scope="module")
def html(report):
    return to_html(report)


class TestTemplateContract:
    def test_registry_is_append_only(self):
        """The contract may grow, but the frozen prefix — ids AND markers — can never change."""
        rows = tuple((s.section_id, s.md_marker, s.html_marker) for s in SECTION_CONTRACT)
        assert rows[: len(_FROZEN)] == _FROZEN
        assert set(HTML_SECTION_ORDER) <= {s.section_id for s in SECTION_CONTRACT}

    def test_renderers_emit_the_frozen_markers(self, markdown, html):
        """The OUTPUT (not just the registry) must carry every frozen marker — so changing a
        heading in the renderer without amending this file fails, even if the module's registry
        was edited to match."""
        for _sid, md_marker, html_marker in _FROZEN:
            if md_marker is not None:
                assert md_marker in markdown, f"markdown output lost frozen marker {md_marker!r}"
            if html_marker is not None:
                assert html_marker in html, f"HTML output lost frozen marker {html_marker!r}"

    def test_every_section_has_a_marker_somewhere(self):
        """A contracted section must be observable in at least one renderer."""
        for spec in SECTION_CONTRACT:
            assert spec.md_marker or spec.html_marker, spec.section_id

    def test_markdown_emits_all_sections_in_contract_order(self, markdown):
        """Every markdown marker present, strictly in registry order."""
        pos = -1
        for spec in SECTION_CONTRACT:
            if spec.md_marker is None:
                continue
            i = markdown.find(spec.md_marker)
            assert i >= 0, f"markdown lost section {spec.section_id!r}"
            assert i > pos, f"markdown reordered section {spec.section_id!r}"
            pos = i

    def test_html_emits_all_sections_in_contract_order(self, html):
        """Every HTML marker present, strictly in the HTML document order."""
        by_id = {s.section_id: s for s in SECTION_CONTRACT}
        pos = -1
        for sid in HTML_SECTION_ORDER:
            marker = by_id[sid].html_marker
            if marker is None:
                continue
            i = html.find(marker)
            assert i >= 0, f"HTML lost section {sid!r}"
            assert i > pos, f"HTML reordered section {sid!r}"
            pos = i

    def test_since_tags_are_recorded(self):
        """Every row declares the version that introduced it (v1 freeze, v2 complements,
        v3 cross-feature synthesis, v4 the Nichod capstone, v5 Your Reading, v6 the Dasha x
        Transit confluence, v7 Yoga x Dasha timing, v8 the House strength cross-check)."""
        assert {s.since for s in SECTION_CONTRACT} <= {
            "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8"}
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v1") == 17
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v2") == 6
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v3") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v4") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v5") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v6") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v7") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v8") == 1
