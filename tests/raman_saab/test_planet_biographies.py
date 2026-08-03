"""S2 planet biographies — census determinism, tier separation, guard-safe prose."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.judgment_graph import build_judgment_graph
from app.raman_saab.planet_biographies import (
    MODERN_BANNER, NON_RAMAN_THEMES, build_planet_biographies, planet_census)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def graph(report):
    return build_judgment_graph(report)


@pytest.fixture(scope="module")
def bios(report, graph):
    return build_planet_biographies(report, graph)


class TestPlanetBiographies:
    def test_census_is_deterministic_and_nonzero(self, graph):
        a, b = planet_census(graph), planet_census(graph)
        assert a == b
        assert sum(sum(v.values()) for v in a.values()) > 0

    def test_top_n_are_ranked_by_census(self, bios):
        counts = [b.census_count for b in bios]
        assert counts == sorted(counts, reverse=True)
        assert len(bios) == 4

    def test_every_field_is_a_re_read(self, report, bios):
        """helps/obstructs must agree with the proforma rollups they re-read."""
        for b in bios:
            for h in b.helps:
                assert report.proformas[h - 1].rollup == "favourable"
            for h in b.obstructs:
                assert report.proformas[h - 1].rollup == "afflicted"

    def test_raman_and_modern_tiers_are_separate(self, bios):
        """The Raman vocation words never mix with the bannered modern keywords."""
        for b in bios:
            assert b.themes_raman                       # HTJAH-II table, always present
            assert tuple(b.themes_modern) == tuple(NON_RAMAN_THEMES.get(b.planet, ()))
        assert "no Raman citation" in MODERN_BANNER

    def test_prose_ends_with_a_conclusion_and_passes_the_guard(self, bios):
        from app.llm.report_explainer import _FORBIDDEN_RE
        for b in bios:
            assert "Conclusion:" in b.prose
            m = _FORBIDDEN_RE.search(b.prose)
            assert m is None, f"{b.planet}: {m.group(0)!r}"

    def test_section_renders_in_every_surface(self, report):
        from app.raman_saab.detailed_report import to_markdown
        from app.raman_saab.report_html import to_html
        from app.raman_saab.report_json import to_report_dict
        assert report.planet_bios
        assert "## Planet biographies (dominant grahas)" in to_markdown(report)
        assert 'id="planet-bios"' in to_html(report)
        assert to_report_dict(report)["planet_bios"]
