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


class TestPortraitFields:
    """Wave-2 foundation additions (REPORT_CRITIQUE_2026-08-17): role-first openers,
    the condition header (Shadbala + functional nature), itemized drishti, avastha
    consequences, named karakatvas, node-safe wording and the census demoted to a
    trailing receipts line — all pure re-reads of already-computed primitives."""

    def test_jupiter_carries_its_functional_nature_and_condition(self, bios):
        """Canonical pin: Jupiter is a functional malefic for Virgo and meets its
        Shadbala minimum — the bio must carry both so it cannot clash in tone with
        the Chart signature's functional-nature row."""
        jup = next(b for b in bios if b.planet == "Jupiter")
        assert jup.functional_nature == "malefic"
        assert jup.rupas == pytest.approx(8.72, abs=0.01)
        assert jup.powerful is True
        assert jup.avastha_result.startswith("combust ->")

    def test_jupiter_markdown_names_functional_malefic_for_virgo(self, report):
        """The rendered bio states the functional nature for THIS Lagna with the
        citation the overview already records (HTJAH-I:523-604)."""
        from app.raman_saab.detailed_report import to_markdown
        md = to_markdown(report)
        i = md.find("### Jupiter")
        sec = md[i:md.find("### ", i + 4)]
        assert "functional malefic for Virgo (HTJAH-I:523-604)" in sec

    def test_drishti_is_itemized_both_ways(self, bios):
        """Casts/receives lists re-read the whole-sign drishti engine: Jupiter casts
        its 5/7/9 and receives Saturn's 7th on the canonical chart."""
        jup = next(b for b in bios if b.planet == "Jupiter")
        assert any(x.startswith("H4 (7th aspect") for x in jup.casts_drishti)
        assert "Saturn (7th aspect)" in jup.receives_drishti
        mer = next(b for b in bios if b.planet == "Mercury")
        assert {x.split(" ", 1)[0] for x in mer.receives_drishti} == {"Mars", "Rahu"}

    def test_named_karakatvas_reuse_the_house_label_map(self, bios):
        """Karaka duties carry the topic labels, never bare house numbers alone."""
        jup = next(b for b in bios if b.planet == "Jupiter")
        assert "house 2 (Wealth/Family)" in jup.family_role_named
        assert "house 4 (Mother/Home)" in jup.family_role_named

    def test_node_bios_never_claim_lordship(self, bios):
        """LOCKED doctrine: the nodes rule nothing — their prose must read tenancy,
        never lordship, and their lord_of stays empty."""
        for b in bios:
            if b.planet in ("Rahu", "Ketu"):
                assert b.lord_of == ()
                assert "its lordship" not in b.prose
                if b.helps:
                    assert "its tenancy and aspects reach" in b.prose

    def test_role_lines_come_from_computed_roles(self, report, bios):
        """Mercury opens as the Lagna lord under strain (below-minimum + Deena); the
        strongest planet names itself; a yoga participant lists its yogas."""
        by = {b.planet: b for b in bios}
        assert by["Mercury"].role_line.startswith("the Lagna lord under strain")
        assert "strongest planet" in by[report.ruler.strongest].role_line
        assert "yoga-giver" in by["Jupiter"].role_line

    def test_census_is_demoted_to_a_receipts_line(self, report):
        """The chapter header opens on the role; the census survives IN FULL as a
        trailing receipts bullet (add-only: same data, new position)."""
        from app.raman_saab.detailed_report import to_markdown
        md = to_markdown(report)
        i = md.find("## Planet biographies")
        sec = md[i:md.find("## Psychological profile")]
        for ln in sec.splitlines():
            if ln.startswith("### "):
                assert "graph appearances" not in ln
        assert sec.count("- **Receipts** - ") == len(report.planet_bios)
        assert "graph appearances" in sec        # the data itself is still shown

    def test_new_portrait_prose_passes_the_guard(self, bios):
        """Descriptive idiom only — the decree-voice tripwire must stay silent on
        every new portrait field."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for b in bios:
            for text in (b.role_line, b.functional_nature, b.avastha_result,
                         b.family_role_named, *b.casts_drishti, *b.receives_drishti):
                m = _FORBIDDEN_RE.search(text)
                assert m is None, f"{b.planet}: {m.group(0)!r}"
