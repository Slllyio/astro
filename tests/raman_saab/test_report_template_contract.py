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
from app.raman_saab.report_movements import MOVEMENTS, flattened_order, movement_passage

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
    # v32 amendment (2026-08-04, conscious, same-commit as the module, user-requested):
    # the judgment graph — used already in Your Reading (the dominant-planet census
    # sentence) and now shown right beside it, the same non-append exception v5 set.
    ("judgment_graph", "## Judgment graph", 'id="judgment-graph"'),
    ("now_box", None, 'class="nowbox"'),
    ("info_content", "## Information content of this reading", 'class="infobox"'),
    # v18 amendment (2026-08-03, conscious, same-commit as the module, user-requested
    # coherence work): the interpretation guide — the report's own precedence rules
    # collected into one section, placed right after the honesty headline.
    ("interpretation_guide", "## How to read this report", 'id="interpretation-guide"'),
    ("stands_out", "## What stands out in this chart", 'id="stands-out"'),
    # v19 amendment (2026-08-03, conscious, same-commit as the module): the ranked digest,
    # previously JSON/interactive-only — the coherence audit's completeness repair.
    ("digest", "## What matters most (ranked digest)", 'id="digest"'),
    ("dashboard", "## The twelve matters at a glance", 'id="dashboard"'),
    ("chart_signature", "## Chart signature", 'class="sig"'),
    # v13 amendment (2026-07-26, conscious, same-commit as the module): Ruler of the nativity —
    # Raman's own first-impression move — inserted right after the Chart signature it opens from.
    ("ruler", "## Ruler of the nativity", 'id="ruler"'),
    # v20 amendment (2026-08-03, conscious, same-commit as the module, synthesis layer S2):
    # planet biographies — the dominant grahas by judgment-graph census, after the ruler
    # card they generalize.
    ("planet_bios", "## Planet biographies (dominant grahas)", 'id="planet-bios"'),
    # v27 amendment (2026-08-04, conscious, same-commit as the module, user-requested):
    # the psychological profile, after the planet cluster it re-reads.
    ("psych", "## Psychological profile", 'id="psych"'),
    ("chart_grids", None, 'id="charts"'),
    ("positions", "## Planetary positions", 'id="positions"'),
    # v31 amendment (2026-08-04, conscious, same-commit as the module): rectification
    # confidence, with the checkable-inputs cluster.
    ("rect_confidence", "## Rectification confidence", 'id="rect-confidence"'),
    ("shadbala", "## Shadbala", 'id="shadbala"'),
    ("yogas", "## Yogas present in this chart", 'id="yogas"'),
    # v7 amendment (2026-07-26, conscious, same-commit as the module): Yoga x Dasha timing
    # inserted right after Yogas — it directly extends that section with WHEN.
    ("yoga_timing", "## Yoga x Dasha timing", 'id="yoga-timing"'),
    # v21 amendment (2026-08-03, conscious, same-commit as the module, user-requested):
    # the yoga deep-read — every fired yoga as a full study, after the timing companion.
    ("yoga_deep", "## Yoga deep-read", 'id="yoga-deep"'),
    ("ashtakavarga", "## Ashtakavarga", 'id="sav"'),
    ("houses", "## House-by-house reading", 'id="houses"'),
    # v8 amendment (2026-07-26, conscious, same-commit as the module): House strength
    # cross-check inserted right after House-by-house — the natural narrative position.
    ("house_strength", "## House strength cross-check", 'id="house-strength"'),
    # v14 amendment (2026-07-26, conscious, same-commit as the module): Preponderance of
    # testimonies — the full per-house ledger — inserted right after the House strength
    # cross-check it generalizes.
    ("preponderance", "## Preponderance of testimonies", 'id="preponderance"'),
    ("longevity", "## Longevity", 'id="longevity"'),
    ("maraka", "## The maraka scheme", 'id="maraka"'),
    # v11 amendment (2026-07-26, conscious, same-commit as the module): Maraka x Saturn-transit
    # confluence inserted right after The maraka scheme — it cross-references that section's
    # own death-window against transiting Saturn.
    ("maraka_saturn", "## Maraka x Saturn-transit confluence", 'id="maraka-saturn"'),
    # v17 amendment (2026-08-03, conscious, same-commit as the module, user-approved feature):
    # the Health & vulnerability read-out — a pure re-read of the D-30 health core, H12 rollup,
    # maraka tiers and longevity band — closing the longevity/maraka cluster it summarizes.
    ("health_readout", "## Health & vulnerability read-out", 'id="health-readout"'),
    # v22 amendment (2026-08-03, conscious, same-commit as the module, user-requested):
    # Arishta & Bhanga — closes the longevity cluster.
    ("arishta", "## Arishta & Bhanga", 'id="arishta"'),
    ("timeline", "## Life-narrative (Vimshottari Dasha)", 'id="timeline"'),
    # v9 amendment (2026-07-26, conscious, same-commit as the module): Ishta/Kashta outlook
    # inserted right after Life-narrative — a colour-strip companion to that section.
    ("ishta_kashta", "## Ishta/Kashta outlook", 'id="ishta-kashta"'),
    # v10 amendment (2026-07-26, conscious, same-commit as the module): MD-lord condition
    # outlook grouped right after Ishta/Kashta — both are Life-narrative companions.
    ("md_condition", "## MD-lord condition outlook", 'id="md-condition"'),
    # v12 amendment (2026-07-26, conscious, same-commit as the module): the third Life-narrative
    # companion, AV-tier, shown last of the three under Raman's own reliability caveat.
    ("av_dasha_seat", "## AV dasha-seat outlook", 'id="av-dasha-seat"'),
    # v16 (2026-08-03, conscious amendment in the same commit as the section): the ASP-12
    # eightfold Kakshya division of each MD run — the fourth Life-narrative companion.
    ("dasa_kakshya", "## Dasha Kakshya intervals", 'id="dasa-kakshya"'),
    # v15 amendment (2026-07-26, conscious, same-commit as the module): Life-chapters — one
    # woven prose chapter per Mahadasha — placed as the capstone of the Life-narrative
    # companion cluster it merges.
    ("life_chapters", "## Life-chapters", 'id="life-chapters"'),
    # v28 amendment (2026-08-04, conscious, same-commit as the module): the decade
    # INDICATION timeline (renamed from "probability" per Measured-Truth).
    ("decades", "## Decade indication timeline", 'id="decades"'),
    ("gochara", "## Current transits (Gochara", 'id="gochara"'),
    # v6 amendment (2026-07-26, conscious, same-commit as the module): the Dasha x Transit
    # confluence, inserted right after Gochara — the natural narrative position, since it
    # cross-references the Life-narrative and Gochara sections directly above it.
    ("dasha_transit", "## Dasha x Transit confluence", 'id="dasha-transit"'),
    ("divisional", "## Divisional deep-reads (Shodasavarga)", 'id="vargas"'),
    ("career", "## Career (HTJAH-II", 'id="career"'),
    # v23/v24 amendments (2026-08-03, conscious, same-commit as the module,
    # user-requested): the profession synthesis and the wealth chapter, after the
    # Career line they extend.
    ("profession", "## Profession synthesis", 'id="profession"'),
    ("wealth", "## Wealth chapter", 'id="wealth"'),
    # v25/v26 amendments (2026-08-04, conscious, same-commit as the module,
    # user-requested): the marriage monograph and children chapter.
    ("marriage", "## Marriage monograph", 'id="marriage"'),
    ("children", "## Children chapter", 'id="children"'),
    ("deeptadi", "## Deeptadi avasthas", 'id="deeptadi"'),
    ("karakamsa", "## Jaimini Karakamsa", 'id="karakamsa"'),
    ("soul", "## Soul & destiny", 'id="soul"'),
    # v30 amendment (2026-08-04, conscious, same-commit as the module, enabled by the
    # JAIMINI lift): the karmic-evolution chapter, after the soul reading it deepens.
    ("karmic", "## Karmic evolution (Jaimini)", 'id="karmic"'),
    ("pitru", "## Pitru dosha", 'id="pitru"'),
    # v3 amendment (2026-07-25, conscious, same-commit as the module): Integrated insights
    # inserted before the glossary so reference material stays last.
    ("synthesis", "## Integrated insights", 'id="synthesis"'),
    # v29 amendment (2026-08-04, conscious, same-commit as the module): the full life
    # synthesis — the biography-closing chapter, before the reference material.
    ("life_synthesis", "## Full life synthesis", 'id="life-synthesis"'),
    ("glossary", "## Glossary", 'id="glossary"'),
    # v4 amendment (2026-07-26, conscious, same-commit as the module): the Nichod capstone,
    # appended LAST — after reference material — since it distils the whole document.
    ("nichod", "## Nichod", 'id="nichod"'),
    # v34 amendment (2026-08-06, conscious, same-commit as the module, user-requested): the
    # intuition layer — which planet governs a contested house, how firmly each house stands,
    # and which of Raman's own worked charts this one recalls. All three are pure re-reads.
    ("dominance", "## What governs each house", 'id="dominance"'),
    ("restraint", "## How firmly each house stands", 'id="restraint"'),
    ("analogy", "## Charts of Raman's this one recalls", 'id="analogy"'),
)
_FROZEN_IDS = tuple(row[0] for row in _FROZEN)

#: The v33 READING ORDER, copied here BY HAND for the same reason `_FROZEN` is: the registry
#: derives its sequence from `report_movements.MOVEMENTS`, so a test that only compared those
#: two would pass silently when both were edited together. Re-sequencing the report means
#: editing this tuple too, consciously, in the same commit.
_ORDER_V34: tuple[str, ...] = (
    # I. Who this is
    "title", "plain_reading", "chart_signature", "now_box", "ruler", "planet_bios", "psych",
    # II. How to read it honestly
    "info_content", "interpretation_guide", "judgment_graph", "stands_out", "digest",
    "dashboard",
    # III. The instrument
    "chart_grids", "positions", "rect_confidence", "shadbala", "ashtakavarga", "divisional",
    # IV. The twelve fields
    "houses", "house_strength", "preponderance", "dominance", "restraint",
    "yogas", "yoga_deep", "deeptadi",
    # V. The matters of life
    "career", "profession", "wealth", "marriage", "children", "health_readout", "arishta",
    "longevity", "maraka", "maraka_saturn",
    # VI. In time
    "timeline", "yoga_timing", "ishta_kashta", "md_condition", "av_dasha_seat", "dasa_kakshya",
    "life_chapters", "decades", "gochara", "dasha_transit",
    # VII. The summing up
    "karakamsa", "soul", "karmic", "pitru", "analogy", "synthesis", "life_synthesis",
    "glossary", "nichod",
)


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
    def test_section_set_is_append_only(self):
        """COMPLETENESS — the frozen SET of (id, markers) may grow, but never change or shrink.

        v33 split what used to be one assertion in two. Until then a single ordered-prefix
        comparison enforced both "no section is ever lost" (correct, permanent) and "the order
        never changes" (accidental) — so the only legal move for 32 versions was to append,
        and the registry became a build log rather than a reading order. Set equality keeps
        the completeness guarantee at full strength; :meth:`test_reading_order_is_the_reviewed_arc`
        governs sequence separately.
        """
        rows = {(s.section_id, s.md_marker, s.html_marker) for s in SECTION_CONTRACT}
        assert rows == set(_FROZEN)

    def test_html_order_carries_every_section(self):
        """Tightened from `<=` to `==` at v33: a subset would have let a section be dropped
        from the HTML order entirely while every test still passed."""
        assert set(HTML_SECTION_ORDER) == {s.section_id for s in SECTION_CONTRACT}

    def test_reading_order_is_the_reviewed_arc(self):
        """ORDER — pinned to a sequence copied BY HAND, for the same reason `_FROZEN` is.

        `SECTION_CONTRACT` derives its order from `report_movements.MOVEMENTS`, so comparing
        the two would be near-tautological: editing the arc and the registry together would
        pass silently. `_ORDER_V34` lives here so re-sequencing stays as deliberate an act as
        changing a marker.
        """
        assert tuple(s.section_id for s in SECTION_CONTRACT) == _ORDER_V34
        assert tuple(HTML_SECTION_ORDER) == _ORDER_V34
        assert flattened_order() == _ORDER_V34

    def test_movements_partition_the_contract(self):
        """Every section sits in exactly one movement — no section lost, none duplicated."""
        placed = [sid for mv in MOVEMENTS for sid in mv.section_ids]
        assert len(placed) == len(set(placed)) == len(SECTION_CONTRACT)
        assert set(placed) == {s.section_id for s in SECTION_CONTRACT}

    def test_nichod_stays_last_and_the_header_trio_stays_together(self):
        """Two structural constraints the arc may never violate.

        `nichod` is the capstone and must close the document. `title`/`plain_reading`/
        `chart_signature` are one `<header>` element in the HTML and are emitted as a single
        chunk, so they must remain adjacent in that internal order.
        """
        assert _ORDER_V34[-1] == "nichod"
        assert _ORDER_V34[:3] == ("title", "plain_reading", "chart_signature")

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
        Transit confluence, v7 Yoga x Dasha timing, v8 the House strength cross-check, v9 the
        Ishta/Kashta outlook, v10 the MD-lord condition outlook, v11 the Maraka x Saturn-transit
        confluence, v12 the AV dasha-seat outlook, v13 the Ruler of the nativity, v14 the
        Preponderance of testimonies, v15 the Life-chapters, v16 the Dasha Kakshya intervals,
        v17 the Health & vulnerability read-out, v18 the interpretation guide, v19 the
        ranked digest, v20 the planet biographies, v21 the yoga deep-read, v22 Arishta &
        Bhanga, v23 the profession synthesis, v24 the wealth chapter, v25 the marriage
        monograph, v26 the children chapter, v27 the psychological profile — the
        higher-order synthesis sections)."""
        assert {s.since for s in SECTION_CONTRACT} <= {
            "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10", "v11", "v12", "v13",
            "v14", "v15", "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23", "v24",
            "v25", "v26", "v27", "v28", "v29", "v30", "v31", "v32",
            # v33 was the reading arc — a re-ORDERING, so it added no section and needs no tag.
            # v34 adds the intuition layer: dominance, restraint and analogy.
            "v34"}
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v1") == 17
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v2") == 6
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v3") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v4") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v5") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v6") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v7") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v8") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v9") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v10") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v11") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v12") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v13") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v14") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v15") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v16") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v17") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v18") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v19") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v20") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v21") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v22") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v23") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v24") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v25") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v26") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v27") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v28") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v29") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v30") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v31") == 1
        assert sum(1 for s in SECTION_CONTRACT if s.since == "v32") == 1


class TestRectConfidence:
    """v31 — sensitivity measured as a bidirectional minute RANGE, never a percentage."""

    def test_renders_with_ten_pillars_and_a_count_verdict(self, report, markdown, html):
        from app.raman_saab.report_json import to_report_dict
        rc = report.rect_confidence
        assert rc is not None
        assert rc.total_count == 10          # lagna + nav lagna + moon nak + 7 houses
        assert 0 <= rc.stable_count <= rc.total_count
        assert "%" not in rc.label
        assert "## Rectification confidence" in markdown
        assert 'id="rect-confidence"' in html
        assert to_report_dict(report)["rect_confidence"] is not None

    def test_flips_carry_an_offset_within_the_scan_window(self, report):
        rc = report.rect_confidence
        for pl in rc.pillars:
            for off, _v in filter(None, (pl.flip_minus, pl.flip_plus)):
                assert 1 <= abs(off) <= rc.scan_window

    def test_stable_range_bounded_by_scan_window(self, report):
        rc = report.rect_confidence
        for pl in rc.pillars:
            assert 0 <= pl.stable_minus <= rc.scan_window
            assert 0 <= pl.stable_plus <= rc.scan_window
            # a flip just past the stable edge, or no flip found within the window
            if pl.flip_minus is not None:
                assert abs(pl.flip_minus[0]) == pl.stable_minus + 1
            else:
                assert pl.stable_minus == rc.scan_window
            if pl.flip_plus is not None:
                assert pl.flip_plus[0] == pl.stable_plus + 1
            else:
                assert pl.stable_plus == rc.scan_window

    def test_overall_window_is_the_tightest_pillar(self, report):
        rc = report.rect_confidence
        assert rc.overall_stable_minus == min(pl.stable_minus for pl in rc.pillars)
        assert rc.overall_stable_plus == min(pl.stable_plus for pl in rc.pillars)
        assert 0 <= rc.overall_stable_minus <= rc.scan_window
        assert 0 <= rc.overall_stable_plus <= rc.scan_window


def _html_section(html: str, section_id: str) -> str:
    """One section's HTML — from its own marker to whichever section follows it.

    Slicing to a HARDCODED next section is what broke when v33 re-sequenced the document: the
    old `html[index("judgment-graph"):index("ruler")]` silently produced an empty string once
    `ruler` moved ahead of it, and an assertion against "" fails for the wrong reason. Deriving
    the neighbour from the contract keeps these assertions order-independent.
    """
    by = {s.section_id: s.html_marker for s in SECTION_CONTRACT}
    order = [sid for sid in HTML_SECTION_ORDER if by[sid]]
    i = order.index(section_id)
    start = html.index(by[section_id])
    end = html.index(by[order[i + 1]]) if i + 1 < len(order) else len(html)
    assert end > start, f"{section_id!r} slice is empty — marker order broke"
    return html[start:end]


class TestJudgmentGraphSection:
    """v32 — the judgment graph; v33 moves it into Movement II, the how-to-read-it frame."""

    def test_renders_in_the_how_to_read_movement(self, markdown, html):
        """It explains how the report reaches its readings, so it belongs to the frame rather
        than to the reading — v33 groups it with the honesty headline and the guide."""
        assert "## Judgment graph" in markdown
        assert 'id="judgment-graph"' in html
        assert markdown.index("## Your Reading") < markdown.index("## Judgment graph")
        assert markdown.index("## Judgment graph") < markdown.index("## What stands out")
        assert html.index('id="plain-reading"') < html.index('id="judgment-graph"')
        mv = next(m for m in MOVEMENTS if "judgment_graph" in m.section_ids)
        assert mv.numeral == "II"

    def test_counts_match_a_direct_graph_build(self, report, markdown):
        from app.raman_saab.judgment_graph import build_judgment_graph
        jg = build_judgment_graph(report)
        assert f"{len(jg.nodes)} nodes, {len(jg.edges)} edges" in markdown

    def test_dominant_planet_and_a_house_appear_in_the_html_svg(self, report, html):
        assert report.planet_bios, "canonical chart should have at least one dominant planet"
        dom = report.planet_bios[0].planet
        seg = _html_section(html, "judgment_graph")
        assert dom in seg
        assert "<svg" in seg

    def test_all_twelve_house_cards_render_in_both_surfaces(self, report, markdown, html):
        """The reader-facing view: one card per house, on every surface."""
        from app.raman_saab.judgment_graph import (build_judgment_graph, house_facts,
                                                   house_sentence)
        seg = _html_section(html, "judgment_graph")
        assert seg.count('class="jg-house"') == 12
        facts = house_facts(build_judgment_graph(report))
        assert len(facts) == 12
        # every house's composed sentence must actually appear, in BOTH renderers
        for _h, f in facts.items():
            sentence = house_sentence(f)
            assert sentence in markdown, f"markdown lost H{_h}'s summary"
            assert sentence in seg, f"HTML lost H{_h}'s summary"

    def test_planet_names_are_never_truncated(self, html):
        """The old aspect network sliced names to 4 chars ('Satu 20', 'Jupi 25'). Gone."""
        seg = _html_section(html, "judgment_graph")
        for stub in ("Satu ", "Jupi ", "Merc ", "Venu ", "Satu<", "Jupi<"):
            assert stub not in seg, f"truncated planet name {stub!r} reappeared"

    def test_doctrine_constant_relations_are_not_drawn_as_personal(self, report, markdown):
        """61% of graph edges are identical across unrelated charts (measured). The
        section->section doctrine edges describe the METHOD, so they are named and
        attributed to 'How to read this report' — never rendered as this chart's own."""
        from app.raman_saab.judgment_graph import (DOCTRINE_CONSTANT_RELATIONS,
                                                   build_judgment_graph, house_facts)
        jg = build_judgment_graph(report)
        # they must not leak into the per-house reader view
        for f in house_facts(jg).values():
            assert not (set(f.roles) & DOCTRINE_CONSTANT_RELATIONS)
        n = sum(1 for e in jg.edges if e.relation in DOCTRINE_CONSTANT_RELATIONS)
        if n:
            assert f"**{n}** edges record how the report's own sections relate" in markdown
            assert "How to read this report" in markdown

    def test_timer_grade_is_the_peak_not_whichever_bhukti_came_first(self, report):
        """A Mahadasha lights a house at different tiers in different bhuktis (measured: 24
        of 36 pairs on the canonical chart). One grade per MD is a summary, so it must be
        the STRONGEST the house reaches — the earlier `setdefault` kept whichever bhukti
        happened to come first and understated 7 of them (Saturn/H2 read 'limited' when it
        actually reaches 'par excellence'). Every surface labels it 'at best'."""
        from app.raman_saab.judgment_graph import (PLAIN_TIER, _tier_rank,
                                                   build_judgment_graph, house_facts)
        best: dict[tuple[int, str], str] = {}
        run, cur = -1, None
        for tp in report.timeline.periods:
            if tp.period.maha != cur:
                run, cur = run + 1, tp.period.maha
            for a in tp.activated:
                key = (run, a.house)
                if key not in best or _tier_rank(a.grade) < _tier_rank(best[key]):
                    best[key] = a.grade
        peaks: dict[int, set[str]] = {}
        for (_run, h), g in best.items():
            peaks.setdefault(h, set()).add(PLAIN_TIER.get(g.replace("_", " "),
                                                          g.replace("_", " ")))
        for h, f in house_facts(build_judgment_graph(report)).items():
            for _lord, grade in f.timers:
                assert grade in peaks.get(h, set()), (
                    f"H{h} timer grade {grade!r} is not a peak grade for that house")

    def test_unknown_tier_never_ranks_as_strongest(self):
        """A grade the scheme does not know must sort LAST, never silently 'best'."""
        from app.raman_saab.judgment_graph import _tier_rank
        assert _tier_rank("par excellence") == 0
        assert _tier_rank("par_excellence") == 0          # underscore form from provenance
        assert _tier_rank("bogus") > _tier_rank("feeble")
        assert _tier_rank("") > _tier_rank("feeble")

    def test_house_sentence_uses_only_chart_specific_roles(self, report):
        """Karaka is ~39% chart-specific (Venus is karaka of the 7th in EVERY chart), so it
        is reported separately rather than repeated through the sentence."""
        from app.raman_saab.judgment_graph import (build_judgment_graph, house_facts,
                                                   house_sentence)
        for f in house_facts(build_judgment_graph(report)).values():
            assert "natural significator" not in house_sentence(f) or not f.roles


class TestKarmicEvolution:
    """v30 — the walled Jaimini layer: verbatim doctrine, resolving cite, walls hold."""

    def test_renders_in_every_surface_with_a_resolving_cite(self, report, markdown, html):
        from app.raman_saab.doctrine.sources import Citation, verify
        from app.raman_saab.report_json import to_report_dict
        kv = report.karmic
        assert kv is not None
        assert "## Karmic evolution (Jaimini)" in markdown
        assert 'id="karmic"' in html
        assert to_report_dict(report)["karmic"] is not None
        assert len(kv.doctrine_quote) > 200
        work, line = kv.doctrine_cite.rsplit(":", 1)
        assert verify(Citation(work, int(line)))
        assert kv.atmakaraka in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                                 "Saturn")   # the 7-karaka lock: never a node

    def test_natal_verdict_path_never_imports_the_karmic_layer(self):
        import inspect

        from app.raman_saab import proforma, synthesis
        from app.raman_saab.judges import house_judge, house_template
        for mod in (house_template, house_judge, proforma, synthesis):
            assert "karmic_evolution" not in inspect.getsource(mod), mod.__name__


class TestWaveB:
    """v28 decades, v29 life synthesis, and the item-15 support labels."""

    def test_both_sections_render_in_every_surface(self, report, markdown, html):
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        assert "## Decade indication timeline" in markdown
        assert 'id="decades"' in html and d["decades"] is not None
        assert "## Full life synthesis" in markdown
        assert 'id="life-synthesis"' in html and d["life_synthesis"] is not None

    def test_decades_never_use_probability_language(self, markdown):
        s = markdown.find("## Decade indication timeline")
        e = markdown.find("\n## ", s + 1)
        section = markdown[s:e]
        assert "probabilit" not in section.lower() or "never a probability" in section
        from app.llm.report_explainer import _FORBIDDEN_RE
        assert _FORBIDDEN_RE.search(section) is None

    def test_decades_outside_the_window_say_so(self, report):
        outside = [d for d in report.decades.decades if not d.inside_window]
        for d in outside:
            assert "not read" in d.note
            assert not d.md_lords and not d.yogas_ripening

    def test_life_synthesis_only_re_reads(self, report):
        """The defect test: each paragraph's key value must appear in its source."""
        ls = report.life_synthesis
        themes = dict(ls.paragraphs)
        if "Destiny" in themes:
            assert report.nichod.essence in themes["Destiny"]
        if "Marriage" in themes:
            assert report.marriage.verdict in themes["Marriage"]
        if "Children" in themes:
            assert report.children.verdict in themes["Children"]
        if "Dominant themes" in themes:
            assert report.planet_bios[0].planet in themes["Dominant themes"]
        from app.llm.report_explainer import _FORBIDDEN_RE
        for _t, para in ls.paragraphs:
            assert _FORBIDDEN_RE.search(para) is None, para

    def test_dashboard_carries_the_support_column(self, markdown, report):
        assert "| classical support (testimonies) |" in markdown
        from app.raman_saab.report_json import to_report_dict
        ts = to_report_dict(report)["testimony_support"]
        assert ts and all(v["label"] in ("High", "Medium", "Low") for v in ts.values())


class TestMonographsV25toV27:
    """Wave A: marriage, children, psychology — verbatim quotes resolve, walls hold."""

    def test_all_three_render_in_every_surface(self, report, markdown, html):
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        for marker, anchor, key in (
                ("## Marriage monograph", 'id="marriage"', "marriage"),
                ("## Children chapter", 'id="children"', "children"),
                ("## Psychological profile", 'id="psych"', "psych")):
            assert marker in markdown, marker
            assert anchor in html, anchor
            assert d[key] is not None, key

    def test_marriage_quotes_and_fired_rules(self, report):
        m = report.marriage
        assert m is not None
        assert len(m.seventh_covers) > 100          # the scope quote
        assert len(m.separation_quote) > 100        # the labeled verbatim block
        assert m.verdict                            # unchanged H7 rollup
        for _b, _t, cite in m.fired_kalatra:
            from app.raman_saab.doctrine.sources import Citation, verify
            work, line = cite.rsplit(":", 1)
            assert verify(Citation(work, int(line))), cite

    def test_children_combos_quoted_whole(self, report):
        c = report.children
        assert c is not None and len(c.combos_quote) > 200
        assert c.significations and c.verdict

    def test_psych_lagna_quote_matches_the_ascendant(self, report):
        ps = report.psych
        assert ps is not None
        from app.raman_saab.doctrine.sources import Citation, verify
        work, line = ps.lagna_quote[1].rsplit(":", 1)
        assert verify(Citation(work, int(line)))
        from app.raman_saab.monographs import LAGNA_BLOCKS
        assert int(line) == LAGNA_BLOCKS[report.chart.asc_sign][0]

    def test_composed_prose_passes_the_guard(self, report):
        """The woven/composed strings (not the labeled verbatim quotes) are guard-safe."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        ps = report.psych
        assert _FORBIDDEN_RE.search(ps.woven) is None


class TestChaptersV22toV24:
    """The three user-requested chapters: populated, cited, guard-safe."""

    def test_all_three_render_in_every_surface(self, report, markdown, html):
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        for marker, anchor, key in (
                ("## Arishta & Bhanga", 'id="arishta"', "arishta"),
                ("## Profession synthesis", 'id="profession"', "profession"),
                ("## Wealth chapter", 'id="wealth"', "wealth")):
            assert marker in markdown, marker
            assert anchor in html, anchor
            assert d[key] is not None, key

    def test_arishta_quotes_ramans_antidotes(self, report):
        a = report.arishta
        assert a is not None and len(a.antidote_quote) > 100
        assert a.antidote_cite.startswith("HPA-14:")

    def test_profession_derives_from_multiple_angles(self, report):
        pf = report.profession
        assert pf is not None and len(pf.sources) >= 3
        assert all(src.cite for src in pf.sources)
        ak_rows = [s for s in pf.sources if s.source == "The Atmakaraka"]
        for s in ak_rows:
            assert "Jaimini" in s.note    # the scope note is mandatory

    def test_wealth_rows_are_channels_not_one_verdict(self, report):
        w = report.wealth
        assert w is not None and len(w.rows) >= 8
        channels = {row.channel.split(" (")[0] for row in w.rows}
        assert len(channels) >= 6         # genuinely different channels
        assert all(row.cite for row in w.rows)

    def test_chapters_pass_the_guard(self, markdown):
        """The composed prose (not the verbatim Raman quotes, which are labeled quotes)
        must never trip the decree/forecast tripwire — checked over the profession and
        wealth sections whose text is engine-composed."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for start_marker in ("## Profession synthesis", "## Wealth chapter"):
            s = markdown.find(start_marker)
            e = markdown.find("\n## ", s + 1)
            section = markdown[s:e if e > 0 else None]
            m = _FORBIDDEN_RE.search(section)
            assert m is None, f"{start_marker}: {m.group(0)!r}"


class TestInterpretationGuide:
    """v18 — the guide renders in every surface and its structure is machine-consumable."""

    def test_guide_renders_in_every_surface(self, report, markdown, html):
        from app.raman_saab.report_json import to_report_dict
        assert "## How to read this report" in markdown
        assert 'id="interpretation-guide"' in html
        d = to_report_dict(report)["interpretation_guide"]
        assert d["version"] == "v18" and d["precedence"] and d["reading_order"]

    def test_relation_vocabulary_is_closed(self):
        """report_explainer must be able to branch deterministically — every relation
        value belongs to the declared closed vocabulary."""
        from app.raman_saab.interpretation_guide import INTERPRETATION_GUIDE as ig
        vocab = set(ig["relation_vocabulary"])
        for prec in ig["precedence"]:
            assert prec["relation"] in vocab, prec["id"]

    def test_precedence_sections_exist_in_the_contract(self):
        """Every section id the guide names must be a real contract section — the guide
        can never dangle."""
        from app.raman_saab.interpretation_guide import INTERPRETATION_GUIDE as ig
        ids = {s.section_id for s in SECTION_CONTRACT}
        for prec in ig["precedence"]:
            for sid in (*prec["sections"], *prec["governs"], *prec["subordinate"]):
                assert sid in ids, f"{prec['id']} names unknown section {sid!r}"
        for par in ig["parallel_lenses"]:
            for sid in par["sections"]:
                assert sid in ids, f"{par['id']} names unknown section {sid!r}"

    def test_guide_citations_resolve(self):
        """Every corpus citation the guide prints must verify against the sources."""
        from app.raman_saab.doctrine.sources import Citation, verify
        from app.raman_saab.interpretation_guide import INTERPRETATION_GUIDE as ig
        cites = [c for prec in ig["precedence"] for c in prec["citations"]]
        cites += [a["citation"] for a in ig["axes"]]
        for cite in cites:
            work, line = cite.rsplit(":", 1)
            assert verify(Citation(work, int(line))), cite


class TestHealthReadout:
    """v17 — the health/vulnerability read-out: populated in every surface, guard-safe prose."""

    def test_section_renders_populated_in_every_surface(self, report, markdown, html):
        """The canonical chart populates the section in md, HTML and JSON alike — the
        REPORT COMPLETENESS rule (every computed field appears in every renderer)."""
        from app.raman_saab.report_json import to_report_dict
        h = report.health_readout
        assert h.rows, "health read-out empty on the canonical chart"
        assert h.caveat
        assert "## Health & vulnerability read-out" in markdown
        assert 'id="health-readout"' in html
        d = to_report_dict(report)["health_readout"]
        assert d["rows"] and d["caveat"] == h.caveat

    def test_prose_passes_the_llm_guard_tripwire(self, markdown):
        """The section's whole rendered prose must never trip _FORBIDDEN_RE — the same
        tripwire that rejects decree/forecast language in LLM answers. This pins the
        wording contract: descriptive idiom only, no death tokens, no dated indications."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        start = markdown.find("## Health & vulnerability read-out")
        assert start >= 0
        end = markdown.find("\n## ", start + 1)
        section = markdown[start:end if end > 0 else None]
        m = _FORBIDDEN_RE.search(section)
        assert m is None, f"health read-out prose trips the guard: {m.group(0)!r}"


class TestMovements:
    """v33 — the reading arc: seven movements, each opening with a connective passage.

    The movements SUPPLEMENT the sections; they never replace them. Every one of the 53
    contracted sections still renders in full underneath its movement heading, which is what
    `TestTemplateContract` above continues to pin.
    """

    def test_every_movement_heads_both_text_surfaces(self, markdown, html):
        """All seven headings reach markdown AND the standalone HTML (REPORT COMPLETENESS:
        a surface that shows fewer movements than another is a dropped surface)."""
        for mv in MOVEMENTS:
            assert f"## {mv.numeral}. {mv.title}" in markdown, f"markdown lost movement {mv.numeral}"
            assert f'id="movement-{mv.numeral.lower()}"' in html, f"HTML lost movement {mv.numeral}"
            assert mv.title in html

    def test_movement_headings_appear_in_arc_order(self, markdown, html):
        """The seven headings must themselves run I -> VII on every surface."""
        md_pos = [markdown.index(f"## {mv.numeral}. {mv.title}") for mv in MOVEMENTS]
        html_pos = [html.index(f'id="movement-{mv.numeral.lower()}"') for mv in MOVEMENTS]
        assert md_pos == sorted(md_pos)
        assert html_pos == sorted(html_pos)

    def test_the_document_still_opens_with_its_own_title(self, markdown, html):
        """Movement I carries `title`, so its heading follows the H1 rather than preceding it —
        a report that opened with '## I. Who this is' above its own name would read wrong."""
        assert markdown.lstrip().startswith("# Detailed reading")
        assert markdown.index("# Detailed reading") < markdown.index("## I. Who this is")
        assert html.index('class="name"') < html.index('id="movement-i"')

    def test_every_movement_carries_a_passage_on_a_full_report(self, report):
        """The passages read defensively from the report, so a sparse chart falls back to
        generic phrasing rather than raising. This pins that a FULLY populated report yields
        real prose at every boundary — otherwise the fallbacks quietly become the norm and the
        movements go mute without any test noticing."""
        for i, mv in enumerate(MOVEMENTS):
            passage = movement_passage(report, i)
            assert passage.strip(), f"movement {mv.numeral} produced no passage"
            assert passage.endswith("."), f"movement {mv.numeral} passage is not a sentence"
            assert len(passage) > 60, f"movement {mv.numeral} passage is suspiciously short"

    def test_passages_reach_both_surfaces(self, report, markdown, html):
        """The composed prose must actually be rendered, not merely computable."""
        from app.raman_saab.detailed_report import _fold_ascii
        for i in range(len(MOVEMENTS)):
            passage = movement_passage(report, i)
            assert _fold_ascii(passage) in markdown, f"markdown dropped passage {i}"

    def test_passages_never_trip_the_llm_guard(self, report):
        """Connective prose is held to the same wording contract as every other composed
        surface: descriptive idiom only, never a decree or a dated forecast. (The guard is a
        blunt denylist and has already caught an innocent 'brings to' here — the rule is to
        write around it, never to widen it.)"""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for i, mv in enumerate(MOVEMENTS):
            m = _FORBIDDEN_RE.search(movement_passage(report, i))
            assert m is None, f"movement {mv.numeral} passage trips the guard: {m.group(0)!r}"

    def test_passage_index_out_of_range_is_empty_not_an_error(self, report):
        """A renderer asking for a movement that does not exist gets "", never an exception."""
        assert movement_passage(report, -1) == ""
        assert movement_passage(report, len(MOVEMENTS)) == ""

    def test_sections_render_under_their_own_movement(self, markdown):
        """Each section must appear after its movement's heading and before the next one —
        the arc has to actually group the document, not merely label it."""
        heads = [markdown.index(f"## {mv.numeral}. {mv.title}") for mv in MOVEMENTS]
        heads.append(len(markdown))
        by_id = {s.section_id: s.md_marker for s in SECTION_CONTRACT}
        for i, mv in enumerate(MOVEMENTS):
            for sid in mv.section_ids:
                marker = by_id[sid]
                if not marker:
                    continue
                at = markdown.index(marker)
                if sid == "title":
                    # documented exception: the document's own H1 precedes Movement I's
                    # heading, so the report does not open with "## I. Who this is".
                    assert at < heads[i]
                    continue
                assert heads[i] < at < heads[i + 1], \
                    f"{sid!r} renders outside movement {mv.numeral}"
