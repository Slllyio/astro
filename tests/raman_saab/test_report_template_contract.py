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
            "v25", "v26", "v27", "v28", "v29", "v30", "v31"}
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


class TestRectConfidence:
    """v31 — sensitivity measured, never an invented percentage."""

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

    def test_flips_carry_the_offset_that_flips_them(self, report):
        for pl in report.rect_confidence.pillars:
            for off, _v in pl.flips:
                assert off in (-5, -2, 2, 5)


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
