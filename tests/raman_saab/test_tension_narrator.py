"""S3 tension narrator — both poles visible, guard-safe, rendered in the surfaces."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report, to_markdown
from app.raman_saab.tension_narrator import narrate_tensions

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


class TestTensionNarrator:
    def test_the_contested_house_sentence_names_both_poles(self, report):
        """PREC-3 narration: the headline verdict AND the witness split both appear —
        nothing suppressed (the user decision: narrate, never hide)."""
        recs = narrate_tensions(report)
        mc = report.preponderance.most_contested
        if mc is None:
            pytest.skip("no contested house on this chart")
        sent = next(s for s in recs if f"House {mc}" in s)
        ht = next(t for t in report.preponderance.houses if t.house == mc)
        assert ht.verdict in sent
        assert str(ht.favourable) in sent and str(ht.adverse) in sent
        assert "PREC-3" in sent

    def test_grain_sentences_name_both_verdicts(self, report):
        """PREC-1 narration: the matter verdict AND the house rollup both appear."""
        for s in narrate_tensions(report):
            if "PREC-1" in s:
                assert "favourable" in s and "afflicted" in s

    def test_every_sentence_passes_the_guard(self, report):
        from app.llm.report_explainer import _FORBIDDEN_RE
        for s in narrate_tensions(report):
            m = _FORBIDDEN_RE.search(s)
            assert m is None, f"{s!r} trips {m.group(0)!r}"

    def test_reconciliations_render_in_your_reading(self, report):
        assert report.plain_reading.reconciliations
        md = to_markdown(report)
        assert "Where readings pull in different directions" in md
        from app.raman_saab.report_html import to_html
        assert "Where readings pull in different directions" in to_html(report)
        from app.raman_saab.report_json import to_report_dict
        assert to_report_dict(report)["plain_reading"]["reconciliations"]

    def test_narration_is_deterministic(self, report):
        assert narrate_tensions(report) == narrate_tensions(report)


class TestMatterHouseCoverage:
    """REPORT_CRITIQUE_2026-08-17 — 7 of the 12 dashboard matters printed '-' in the
    support column because `_MATTER_HOUSE` mapped only the legacy per-house keys."""

    def test_every_dashboard_matter_resolves_to_a_house(self, report):
        """Every dashboard matter key maps to the house its dedicated deep reader judges
        (spiritual is DHARMA -> 9, per `matter_varga_reading._SPECS`, not moksha/12)."""
        from app.raman_saab.judges.matter_varga_dashboard import _DISPATCH
        from app.raman_saab.tension_narrator import _MATTER_HOUSE
        for en in report.dashboard.entries:
            assert en.matter in _MATTER_HOUSE, f"dead support cell: {en.matter}"
            assert _MATTER_HOUSE[en.matter] in range(1, 13)
        assert {m for m, *_ in _DISPATCH} <= set(_MATTER_HOUSE)
        assert _MATTER_HOUSE["spiritual"] == 9
        # the mapping mirrors detailed_report's own documented anchors, key for key
        from app.raman_saab.detailed_report import _MATTER_HOUSE as _dr_map
        assert all(_MATTER_HOUSE[m] == h for m, h in _dr_map.items())

    def test_dashboard_support_cells_are_live_in_markdown(self, report):
        """The twelve-matters-at-a-glance table renders a real support readout (High/
        Medium/Low + testimony counts) for every matter — no '-' cells."""
        md = to_markdown(report)
        block = md.split("## The twelve matters at a glance")[1].split("\n## ")[0]
        rows = [ln for ln in block.splitlines()
                if ln.startswith("| ") and "**" in ln]
        assert len(rows) == 12
        for row in rows:
            assert not row.rstrip().endswith("| - |"), f"dead support cell: {row}"


class TestPipelineConsumption:
    """The diagram's arrows, enforced by consumption: prose naming census values can only
    exist because the census ran upstream of the narrative engine."""

    def test_the_opening_names_the_census_dominant_planet(self, report):
        dom = report.planet_bios[0]
        opening = report.plain_reading.opening
        assert dom.planet in opening
        assert str(dom.census_count) in opening and "HTJAH-II:10249" in opening

    def test_the_dominant_planets_own_chapter_carries_the_sentence(self, report):
        dom = report.planet_bios[0].planet
        own = [c for c in report.life_chapters.chapters if c.maha == dom]
        if not own:
            pytest.skip("dominant planet's MD not inside this chart's window")
        assert any("drives more of this chart's computed readings" in c.narrative
                   for c in own)

    def test_the_graph_no_longer_reads_life_chapters(self):
        """The backwards arrow is gone: the graph builds from first-pass objects only."""
        import inspect

        from app.raman_saab import judgment_graph
        assert "life_chapters" not in inspect.getsource(judgment_graph)

    def test_timer_edges_carry_the_activation_grade(self, report):
        from app.raman_saab.judgment_graph import build_judgment_graph
        g = build_judgment_graph(report)
        timer = [e for e in g.edges if e.relation == "timer_of"]
        assert timer and all("grade=" in e.provenance for e in timer)


class TestTurningPoints:
    """S5 — MD boundaries where the Ishta/Kashta lean flips, on the Nichod."""

    def test_turning_points_are_lean_flips_only(self, report):
        tps = report.nichod.turning_points
        for _when, what in tps:
            assert "gives way to" in what and "lean changes" in what

    def test_turning_points_render_and_pass_the_guard(self, report):
        from app.llm.report_explainer import _FORBIDDEN_RE
        n = report.nichod
        if not n.turning_points:
            pytest.skip("no lean flip inside this chart's window")
        md = to_markdown(report)
        assert "Turning points" in md
        joined = "; ".join(f"{w}: {x}" for w, x in n.turning_points)
        assert _FORBIDDEN_RE.search(joined) is None


class TestMatterHouseMapsCannotDrift:
    """Two `_MATTER_HOUSE` maps exist on purpose and must never disagree.

    `detailed_report._MATTER_HOUSE` is the DASHBOARD-matter map: it is *iterated*
    (theme houses, per-house matter lists), so it must contain dashboard matters only.
    `tension_narrator._MATTER_HOUSE` is a *lookup* superset that also carries the legacy
    per-house keys (courage, happiness, fortune...). The adversarial review of the audit
    waves (2026-08-18) flagged the pair as a drift hazard: `house_dashboard_conflicts`
    lives in detailed_report but imports tension_narrator's map. These tests pin the
    invariant instead of merging maps with different jobs."""

    def test_shared_keys_agree_on_the_house(self):
        """A matter judged by house N in one map is judged by house N in the other."""
        from app.raman_saab.detailed_report import _MATTER_HOUSE as dashboard_map
        from app.raman_saab.tension_narrator import _MATTER_HOUSE as lookup_map
        for matter in set(dashboard_map) & set(lookup_map):
            assert dashboard_map[matter] == lookup_map[matter], (
                f"{matter}: detailed_report says {dashboard_map[matter]}, "
                f"tension_narrator says {lookup_map[matter]}")

    def test_lookup_map_covers_every_dashboard_matter(self):
        """The lookup map is a superset — no dashboard matter can miss its support cell."""
        from app.raman_saab.detailed_report import _MATTER_HOUSE as dashboard_map
        from app.raman_saab.tension_narrator import _MATTER_HOUSE as lookup_map
        assert not set(dashboard_map) - set(lookup_map)
