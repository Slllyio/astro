"""S2 planet biographies — census determinism, tier separation, guard-safe prose."""
from __future__ import annotations

import pytest

from corpus_presence import needs_corpus

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

    def test_all_nine_grahas_are_chaptered_dominant_first(self, bios):
        """The chapter amendment (2026-08-03): every graha, census-ranked."""
        counts = [b.census_count for b in bios]
        assert counts == sorted(counts, reverse=True)
        assert len(bios) == 9
        assert {b.planet for b in bios} == {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                            "Venus", "Saturn", "Rahu", "Ketu"}

    def test_every_field_is_a_re_read(self, report, bios):
        """helps/obstructs must agree with the proforma rollups they re-read."""
        for b in bios:
            for h in b.helps:
                assert report.proformas[h - 1].rollup == "favourable"
            for h in b.obstructs:
                assert report.proformas[h - 1].rollup == "afflicted"

    def test_raman_and_modern_tiers_are_separate(self, bios):
        """The Raman vocation words never mix with the bannered modern keywords; the
        nodes have NO vocation row (an honest absence, HTJAH-II's table excludes them)."""
        for b in bios:
            if b.planet in ("Rahu", "Ketu"):
                assert b.themes_raman == ""
                assert "chayagraha" in b.prose
            else:
                assert b.themes_raman
            assert tuple(b.themes_modern) == tuple(NON_RAMAN_THEMES.get(b.planet, ()))
        assert "no Raman citation" in MODERN_BANNER

    @needs_corpus
    def test_chapter_fields_carry_verbatim_cited_text(self, bios):
        """The graha-chapter fields: every present (text, cite) pair resolves, and the
        seven visible grahas all carry their HPA-21/22 placement paragraphs."""
        from app.raman_saab.doctrine.sources import Citation, verify
        for b in bios:
            for pair in (b.house_text, b.sign_text, b.md_result_now, b.ad_result_now,
                         b.transit_text, b.disease_text):
                if pair is not None:
                    text, cite = pair
                    assert text and len(text) > 10   # shortest: "governs the feet"
                    work, line = cite.rsplit(":", 1)
                    assert verify(Citation(work, int(line))), cite
            if b.planet not in ("Rahu", "Ketu"):
                assert b.house_text is not None, b.planet
                assert b.sign_text is not None, b.planet
                assert b.transit_text is not None, b.planet

    @needs_corpus
    def test_running_pair_carries_dasha_text(self, report, bios):
        """The running MD lord shows its HPA-24 per-sign paragraph; the running AD lord
        its bhukti paragraph — the 'during Mahadasha/Antardasha' chapter requirement."""
        md = report.synthesis.running_md
        ad = report.synthesis.running_ad
        md_bio = next(b for b in bios if b.planet == md)
        ad_bio = next(b for b in bios if b.planet == ad)
        assert md_bio.md_result_now is not None
        assert ad_bio.ad_result_now is not None
        assert "HPA-24" in md_bio.md_result_now[1]

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
