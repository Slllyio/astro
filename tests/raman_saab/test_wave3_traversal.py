"""Wave-3 (2026-08-18) — structure & reading experience.

The report's longest chapter became traversable: a verdict-first 12-row strip above the
twelve deep blocks, the Conclusion promoted to the head of each block (with the
machine-composed evidence chain labelled "Working" where it already stood), one rollup
line above repeating calibration rows, in-block cross-references at the point of
confusion, Yoga x Dasha rows grouped by yoga, the Pitru screen leading with its finding,
and the last maintainer notes routed out of client prose.

Every item is ADD-ONLY or MOVE-ONLY: these tests pin that no row, column, verdict or
sentence was lost, that each conditional pointer appears only when its condition holds,
and that all new prose passes the decree-voice guard.
"""
from __future__ import annotations

import re

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import (
    INVERTED_POINTER,
    SPLIT_POINTER,
    build_detailed_report,
    calibration_rollup_line,
    house_chief_combinations,
    house_dashboard_conflicts,
    house_longevity_pointer,
    house_maintainer_notes,
    house_strip_rows,
    to_markdown,
    yoga_timing_grouped,
)
from app.raman_saab.report_html import to_html

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

#: The encoding-scope markers `monographs._MAINTAINER_MARKERS` routes to fine print.
_MAINTAINER_MARKERS = ("v1-OOS", "owned by H7", "kept in text", "TODO(predicate")
_FINE_PRINT_LABEL = "Encoding-scope notes"


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def markdown(report):
    return to_markdown(report)


@pytest.fixture(scope="module")
def html(report):
    return to_html(report)


def _md_block(markdown: str, house: int) -> str:
    """One house's markdown block, header to the next header (or to the next section)."""
    i = markdown.find(f"### House {house} ")
    assert i >= 0, house
    j = markdown.find(f"### House {house + 1} ", i)
    if j < 0:
        j = markdown.find("## House strength cross-check", i)
    return markdown[i:j if j > i else len(markdown)]


def _html_block(html: str, house: int) -> str:
    i = html.find(f'id="house-{house}"')
    assert i >= 0, house
    j = html.find("</section>", i)
    return html[i:j]


class TestVerdictFirstStrip:
    """Item 1 — a 12-row scanning index above the deep blocks, which stay unchanged."""

    def test_strip_has_twelve_rows_matching_the_deep_blocks(self, report):
        """One row per house, and every cell restates the block it points at."""
        rows = house_strip_rows(report)
        assert [r.house for r in rows] == list(range(1, 13))
        by_house = {mr.house: mr for mr in report.synthesis.matters}
        for row in rows:
            assert row.verdict == by_house[row.house].verdict
            assert row.name == by_house[row.house].name

    def test_markdown_strip_renders_twelve_rows_before_house_one(self, report, markdown):
        """The table sits between the chapter intro and the first deep block, and its
        verdict cell equals the deep block's own headline verdict."""
        head = markdown.find("| # | House | Verdict | Driver | Split status | Running period |")
        first = markdown.find("### House 1 ")
        assert 0 < head < first
        table = markdown[head:first]
        data = [ln for ln in table.splitlines()
                if ln.startswith("| H") and ln.endswith("|")]
        assert len(data) == 12
        for row in house_strip_rows(report):
            line = next(ln for ln in data if ln.startswith(f"| H{row.house} |"))
            assert f"**{row.verdict}**" in line
            block = _md_block(markdown, row.house)
            assert f": {row.verdict.upper()}" in block.splitlines()[0]
            if row.driver:
                assert f"_{row.driver}_" in line
                assert f"driven by _{row.driver}_" in block.splitlines()[0]

    def test_markdown_strip_reports_the_running_period_tier(self, report, markdown):
        """The 'Running period' cell is the same four-tier grade the block's own
        Current-period line states (or 'not lit' when neither period-lord acts)."""
        for row in house_strip_rows(report):
            block = _md_block(markdown, row.house)
            if row.tier:
                assert f"grades {row.tier}" in block
            else:
                assert "neither period-lord influences this house" in block

    def test_html_strip_renders_twelve_linked_rows_before_the_blocks(self, report, html):
        """The HTML twin is built from the same composer and links each row to its
        block; it precedes every house section."""
        head = html.find("<th>running period</th>")
        assert head > 0
        assert head < html.find('id="house-1"')
        for row in house_strip_rows(report):
            assert f'href="#house-{row.house}"' in html
            assert f'id="house-{row.house}"' in html

    def test_strip_flags_the_inverted_driver(self, report, markdown):
        """A house whose driver sits on an atlas-proven inverted channel is flagged in
        the strip too — the honesty device is not lost by scanning."""
        inv = [r.house for r in house_strip_rows(report) if r.inverted]
        assert inv, "the canonical chart carries at least one inverted-channel driver"
        head = markdown.find("| # | House | Verdict | Driver |")
        table = markdown[head:markdown.find("### House 1 ")]
        for h in inv:
            line = next(ln for ln in table.splitlines() if ln.startswith(f"| H{h} |"))
            assert "[INVERTED]" in line


class TestConclusionPromoted:
    """Item 2 — the Conclusion leads the block; the run-on is labelled "Working"."""

    def test_conclusion_precedes_the_working_line_in_every_markdown_block(self, markdown):
        """Move only: both lines are present in all twelve blocks, Conclusion first."""
        for h in range(1, 13):
            block = _md_block(markdown, h)
            ci, wi = block.find("**Conclusion**"), block.find("**Working**")
            assert ci > 0, h
            assert wi > 0, h
            assert ci < wi, h

    def test_conclusion_text_is_unchanged_and_rendered_once(self, report, markdown):
        """The promoted line is the same `house_conclusion` prose, not a re-composition,
        and it is not duplicated at its old position."""
        from app.raman_saab.detailed_report import house_conclusion
        from app.raman_saab.render import _ascii
        for h in range(1, 13):
            block = _md_block(markdown, h)
            assert block.count("> **Conclusion**") == 1, h
            expected = _ascii(house_conclusion(report, h))
            assert expected and expected in block, h

    def test_working_line_is_the_untouched_machine_reading(self, report, markdown):
        """The semicolon evidence chain is unchanged in every character — only labelled."""
        from app.raman_saab.render import _ascii
        for mr in report.synthesis.matters:
            block = _md_block(markdown, mr.house)
            assert f"**Working** - {_ascii(mr.reading)}" in block

    def test_html_conclusion_sits_in_the_head_above_the_why_pane(self, html):
        """The standalone HTML mirrors the promotion: the Conclusion div precedes the
        always-open Why pane, whose reading paragraph now carries the Working label."""
        for h in range(1, 13):
            block = _html_block(html, h)
            ci = block.find("<b>Conclusion</b>")
            wi = block.find("<b>Working</b>")
            assert ci > 0 and wi > 0, h
            assert ci < wi, h


class TestDeepBlocksUnchanged:
    """The traversal layer is additive: every element the deep block carried is still
    there, in all twelve blocks."""

    def test_every_block_keeps_all_its_levels(self, report, markdown):
        for mr in report.synthesis.matters:
            block = _md_block(markdown, mr.house)
            for probe in ("**Lord**", "**Karaka**", "**Navamsa**", "_**Frame**",
                          "_**Current period**", "`Evidence ", "**Working**",
                          "**Conclusion**", "_Population context:_"):
                assert probe in block, (mr.house, probe)

    def test_every_calibration_row_and_chief_rule_still_renders(self, report, markdown):
        from app.raman_saab.render import _ascii
        for mr in report.synthesis.matters:
            block = _md_block(markdown, mr.house)
            for e in report.calibration[mr.house].entries:
                assert f"_{e.signification}_:" in block, (mr.house, e.signification)
            for _sig, rid, text, cite in house_chief_combinations(report, mr.house):
                assert f"`{rid}`" in block and cite in block, (mr.house, rid)
                assert _ascii(text)[:40] in block, (mr.house, rid)


class TestCalibrationRollup:
    """Item 3 — one summary line above repeating rows; every row still rendered."""

    def test_h1_and_h6_get_a_rollup_line_with_every_row_kept(self, report, markdown):
        """The critique's two motivating houses: H1's three verbatim-identical rows and
        H6's five near-universal rows. Add-only — the rows stay."""
        for h in (1, 6):
            block = _md_block(markdown, h)
            assert "_Rollup:" in block, h
            assert "Every individual row is kept below." in block, h
            for e in report.calibration[h].entries:
                assert f"_{e.signification}_:" in block, (h, e.signification)

    def test_rollup_counts_match_the_entries(self, report):
        """The counts are re-reads, never re-judgments."""
        line = calibration_rollup_line(report.calibration[1])
        assert line.startswith("Rollup: 3 of 3 sub-readings return the same favourable")
        line6 = calibration_rollup_line(report.calibration[6])
        assert "5 of 5 are near-universal" in line6

    def test_no_rollup_when_the_rows_do_not_repeat(self, report):
        """A house whose sub-readings differ gets no rollup line — the device fires only
        where it says something."""
        fired = {h: bool(calibration_rollup_line(report.calibration[h]))
                 for h in range(1, 13)}
        assert any(fired.values()) and not all(fired.values()), fired

    def test_rollup_is_empty_below_three_rows(self, report):
        """Fewer than three calibrated rows can never trigger a rollup."""
        import dataclasses
        cal = report.calibration[1]
        trimmed = dataclasses.replace(cal, entries=tuple(cal.entries[:2]))
        assert calibration_rollup_line(trimmed) == ""

    def test_html_rollup_precedes_the_population_rows(self, html):
        """Same line, same place, in the standalone HTML."""
        block = _html_block(html, 1)
        i = block.find("Rollup:")
        j = block.find('<div class="cal-row"')
        assert 0 < i < j


class TestInBlockCrossReferences:
    """Item 4 — each pointer appears only where its condition actually holds."""

    def test_dashboard_conflict_pointer_only_where_the_verdicts_differ(
            self, report, markdown):
        """H10 (dashboard career favourable vs bhava afflicted) carries the PREC-1
        pointer; a house whose matter agrees carries none."""
        assert house_dashboard_conflicts(report, 10), "canonical H10 is the flagship case"
        assert "PREC-1 in \"How to read this report\" governs" in _md_block(markdown, 10)
        quiet = [h for h in range(1, 13) if not house_dashboard_conflicts(report, h)]
        assert quiet, "not every house disagrees with its dashboard matter"
        for h in quiet:
            assert "the dashboard reads" not in _md_block(markdown, h), h

    def test_longevity_pointer_only_on_the_house_that_defers_metadata(
            self, report, markdown):
        """The pointer is conditional on the deferred death_window / decanate_cause
        metadata having actually been computed — H8 only."""
        assert house_longevity_pointer(report, 8)
        assert "carried in the Longevity chapter below" in _md_block(markdown, 8)
        for h in range(1, 13):
            if h == 8:
                continue
            assert house_longevity_pointer(report, h) == "", h
            assert "carried in the Longevity chapter below" not in _md_block(markdown, h)

    def test_inverted_pointer_travels_with_the_warning_and_only_with_it(
            self, report, markdown):
        """Every INVERTED-channel WARNING points at Information content; no other block
        does."""
        from app.raman_saab.detailed_report import driver_entry
        from app.raman_saab.render import _ascii
        probe = _ascii(INVERTED_POINTER)[:60]
        for mr in report.synthesis.matters:
            block = _md_block(markdown, mr.house)
            drv = driver_entry(report.calibration[mr.house], mr.verdict)
            warned = drv is not None and drv.inverted_warning
            assert ("**WARNING**" in block) == bool(warned), mr.house
            assert (probe in block) == bool(warned), mr.house

    def test_split_pointer_travels_with_the_split_note_and_only_with_it(
            self, report, markdown):
        """The precedence pointer fires exactly where a split-status note fires."""
        from app.raman_saab.detailed_report import (signification_tenor_split,
                                                    tenor_note)
        from app.raman_saab.render import _ascii
        probe = _ascii(SPLIT_POINTER)[:60]
        for mr in report.synthesis.matters:
            block = _md_block(markdown, mr.house)
            split = signification_tenor_split(report.calibration[mr.house])
            has = bool(tenor_note(split, mr.verdict))
            assert ("**Split status**" in block) == has, mr.house
            assert (probe in block) == has, mr.house

    def test_html_carries_the_same_conditional_pointers(self, report, html):
        """Both surfaces are fed by the same composers, so both branches hold there."""
        assert "ask the dashboard for a matter" in _html_block(html, 10)
        assert "ask the dashboard for a matter" not in _html_block(html, 1)
        assert "carried in the Longevity chapter below" in _html_block(html, 8)
        assert "carried in the Longevity chapter below" not in _html_block(html, 1)


class TestYogaTimingGrouping:
    """Item 5 — grouped by yoga, with every row retained."""

    def test_grouping_loses_no_row(self, report):
        """Every YogaTiming row appears in exactly one group, in its original order."""
        groups = yoga_timing_grouped(report)
        flat = [t for _name, rows in groups for t in rows]
        assert len(flat) == len(report.yoga_timing)
        assert set(id(t) for t in flat) == set(id(t) for t in report.yoga_timing)
        for _name, rows in groups:
            assert list(rows) == sorted(rows, key=lambda t: t.period_start_jd)

    def test_markdown_renders_one_labelled_table_per_yoga_with_every_row(
            self, report, markdown):
        """Row count before == row count after; each group carries its own label."""
        i = markdown.find("## Yoga x Dasha timing")
        j = markdown.find("## Yoga deep-read")
        section = markdown[i:j]
        data = [ln for ln in section.splitlines()
                if ln.startswith("| ") and "---" not in ln
                and not ln.startswith("| Yoga | Period |")]
        assert len(data) == len(report.yoga_timing)
        from app.raman_saab.render import _ascii
        for name, rows in yoga_timing_grouped(report):
            label = _ascii(f"**{name}** - {len(rows)} constituent-lord window")
            assert label in section, name

    def test_html_renders_a_group_band_per_yoga_with_every_row(self, report, html):
        """The HTML table keeps one row per window and adds a band row per yoga."""
        i = html.find('id="yoga-timing"')
        j = html.find('id="yoga-deep"')
        section = html[i:j]
        groups = yoga_timing_grouped(report)
        assert section.count('<tr class="yoga-group">') == len(groups)
        # header row + one band row per group + one row per window
        assert section.count("<tr") == 1 + len(groups) + len(report.yoga_timing)


class TestPitruLeadsWithItsFinding:
    """Item 6 — the answer first, the five caveats after it (move only)."""

    def test_finding_is_the_first_line_of_the_screen(self, report, markdown):
        i = markdown.find("## Pitru dosha screen")
        j = markdown.find("## Integrated insights")
        section = markdown[i:j]
        body = section[section.find("```") + 3:]
        lines = [ln for ln in body.splitlines() if ln.strip()]
        assert lines[0].startswith("PITR-DOSA")
        assert lines[1].startswith("FINDING:"), lines[:3]

    def test_finding_states_the_screen_result(self, report):
        from app.raman_saab.render_pitru import finding
        line = finding(report.pitru)
        if report.pitru.curse_yogas:
            assert "classical ancestral-curse yoga" in line
        else:
            assert "no classical ancestral-curse yoga fires" in line

    def test_every_caveat_bullet_survives_below_the_finding(self, report, markdown):
        """Nothing was traded for the promotion: all notes still render."""
        from app.raman_saab.detailed_report import _fold_ascii
        i = markdown.find("## Pitru dosha screen")
        section = markdown[i:markdown.find("## Integrated insights")]
        assert section.count("* [") == len(report.pitru.notes)
        for n in report.pitru.notes:
            assert _fold_ascii(n.text)[:50] in section


class TestMaintainerNotesRouted:
    """Item 7 — encoding-scope artifacts leave client prose (routed, never dropped)."""

    def test_no_marker_outside_the_fine_print_line_in_markdown(self, markdown):
        for line in markdown.splitlines():
            if any(mk in line for mk in _MAINTAINER_MARKERS):
                assert _FINE_PRINT_LABEL in line, line[:160]

    def test_no_marker_outside_the_fine_print_paragraph_in_html(self, html):
        for mk in _MAINTAINER_MARKERS:
            start = 0
            while True:
                i = html.find(mk, start)
                if i < 0:
                    break
                head = html[:i]
                assert head.rfind(_FINE_PRINT_LABEL) > head.rfind("</p>"), mk
                start = i + 1

    def test_chief_combination_prose_is_clean_and_notes_are_reemitted(self, report):
        """The client sentence loses the artifact; `house_maintainer_notes` carries it."""
        h7 = house_chief_combinations(report, 7)
        assert h7
        for _sig, _rid, text, _cite in h7:
            assert not any(mk in text for mk in _MAINTAINER_MARKERS), text
        notes = house_maintainer_notes(report, 7)
        assert "v1-OOS" in notes and "owned by H7.C.60" in notes

    def test_the_shared_helper_is_reused_not_reimplemented(self):
        """One splitter (monographs.split_maintainer_notes), used by both composers."""
        import inspect
        from app.raman_saab import detailed_report as dr
        for fn in (dr.house_chief_combinations, dr.house_maintainer_notes):
            assert "split_maintainer_notes" in inspect.getsource(fn), fn.__name__

    def test_houses_without_artifacts_emit_no_fine_print(self, report, markdown):
        for h in range(1, 13):
            if not house_maintainer_notes(report, h):
                assert _FINE_PRINT_LABEL not in _md_block(markdown, h), h


class TestGuardSweep:
    """All Wave-3 prose passes the decree-voice guard (_FORBIDDEN_RE)."""

    def test_new_prose_carries_no_decree_voice(self, report, markdown):
        from app.llm.report_explainer import _FORBIDDEN_RE
        from app.raman_saab.render_pitru import finding
        probes: list[str] = [SPLIT_POINTER, INVERTED_POINTER, finding(report.pitru)]
        for h in range(1, 13):
            probes += list(house_dashboard_conflicts(report, h))
            probes.append(house_longevity_pointer(report, h))
            probes.append(calibration_rollup_line(report.calibration[h]))
            probes.append(house_maintainer_notes(report, h))
        for row in house_strip_rows(report):
            probes.append(f"{row.name} {row.verdict} {row.driver} {row.split} {row.tier}")
        for marker in ("The twelve houses at a glance", "Running period\" is this house",
                       "_Every window below is retained", "**Working** -"):
            probes += [ln for ln in markdown.splitlines() if marker in ln]
        for text in probes:
            assert not _FORBIDDEN_RE.search(text or ""), text

    def test_markdown_stays_ascii(self, markdown):
        """render._fold_ascii must still round-trip every new sentence."""
        assert markdown.isascii()

    def test_no_new_h2_heading_inside_the_frozen_house_section(self, markdown):
        """Wave-3 adds structure with tables/bold/blockquotes only — the frozen `## `
        markers and their order are untouched."""
        i = markdown.find("## House-by-house reading")
        j = markdown.find("## House strength cross-check")
        section = markdown[i + 3:j]
        assert not re.search(r"^## ", section, re.MULTILINE)
