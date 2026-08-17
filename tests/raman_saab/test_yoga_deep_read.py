"""v21 yoga deep-read — quoted definitions, computation trees, measured strength."""
from __future__ import annotations

import pytest

from corpus_presence import HAS_CORPUS, needs_corpus

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report, to_markdown
from app.raman_saab.yoga_deep_read import NH_EXAMPLES, describe, participants

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


class TestWalkers:
    def test_describe_renders_combinators_readably(self):
        from app.raman_saab.doctrine import conditions as C
        cond = C.Or(C.Conjunct("Sun", "Mercury"), C.Not(C.InRashiHouse("Mars", 8)))
        s = describe(cond)
        assert " OR " in s and "NOT " in s and "Conjunct(a=Sun, b=Mercury)" in s

    def test_participants_collects_grahas_in_order(self):
        from app.raman_saab.doctrine import conditions as C
        cond = C.And(C.Conjunct("Sun", "Mercury"), C.Aspects("Jupiter", "Sun"))
        assert participants(cond) == ("Sun", "Mercury", "Jupiter")


class TestYogaDeepRead:
    def test_every_fired_yoga_gets_a_deep_read(self, report):
        assert report.yogas, "canonical chart fires yogas"
        assert len(report.yoga_deep) == len(report.yogas)

    @needs_corpus
    def test_definitions_are_quoted_verbatim_with_resolving_cites(self, report):
        from app.raman_saab.doctrine.sources import Citation, verify
        for y in report.yoga_deep:
            assert y.definition_quote and len(y.definition_quote) > 30
            work, line = y.cite.rsplit(":", 1)
            assert verify(Citation(work, int(line))), y.cite

    def test_strength_is_measured_never_a_percentage(self, report):
        for y in report.yoga_deep:
            assert "%" not in y.strength_note
            assert ("rupas" in y.strength_note
                    or "unavailable" in y.strength_note
                    or "could not be resolved" in y.strength_note)

    def test_comparison_ranks_are_a_permutation(self, report):
        ranks = sorted(y.comparison_rank for y in report.yoga_deep)
        assert ranks == list(range(1, len(report.yoga_deep) + 1))

    def test_participants_carry_chart_facts(self, report):
        for y in report.yoga_deep:
            for f in y.participants:
                assert 1 <= f.house <= 12 and 1 <= f.sign <= 12
                assert f.dignity and f.effective_dignity

    @needs_corpus
    def test_nh_example_cites_resolve(self):
        from app.raman_saab.doctrine.sources import Citation, verify
        for cites in NH_EXAMPLES.values():
            for cite in cites:
                work, line = cite.rsplit(":", 1)
                assert verify(Citation(work, int(line))), cite

    def test_section_renders_in_every_surface(self, report):
        from app.raman_saab.report_html import to_html
        from app.raman_saab.report_json import to_report_dict
        assert "## Yoga deep-read" in to_markdown(report)
        assert 'id="yoga-deep"' in to_html(report)
        assert to_report_dict(report)["yoga_deep"]


def _yoga_section(md: str) -> str:
    """The '## Yoga deep-read' slice of the rendered markdown."""
    body = md.split("## Yoga deep-read", 1)[1]
    return body.split("\n## ", 1)[0]


class TestCritiqueFixes:
    """REPORT_CRITIQUE_2026-08-17 'yoga_strength' appendix — the four verified defects."""

    def _deep(self, report, fragment: str):
        hits = [y for y in report.yoga_deep if fragment.lower() in y.name.lower()]
        assert hits, f"canonical chart fires a {fragment} yoga"
        return hits[0]

    def test_sunapha_participants_are_the_second_from_moon_occupants(self, report):
        """3HC: Sunapha is caused by the planet IN the 2nd from the Moon, not all five candidates."""
        y = self._deep(report, "Sunapha")
        moon = report.chart.planets["Moon"]
        second = (moon.rasi_house % 12) + 1
        expected = {p for p in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
                    if report.chart.planets[p].rasi_house == second}
        assert {f.planet for f in y.participants} == expected
        assert expected == {"Mars"}, "canonical chart: Mars alone occupies 2nd from Moon"

    def test_gajakesari_participants_include_moon_and_jupiter(self, report):
        """3HC:1589 grades the Jupiter-Moon pair; the Moon must not be dropped."""
        y = self._deep(report, "Gajakesari")
        assert {"Jupiter", "Moon"} <= {f.planet for f in y.participants}

    def test_vesi_and_amala_resolve_nonempty_participants(self, report):
        """The semantic resolver names the actual flank/10th occupant for Vesi and Amala."""
        for frag in ("Vesi", "Amala"):
            y = self._deep(report, frag)
            assert y.participants, frag
            assert "could not be resolved" not in y.strength_note
            assert "no Shadbala on this chart" not in y.strength_note

    def test_resolved_yogas_never_rank_below_unresolved(self, report):
        """The -1.0 sentinel must not sink a yoga whose participants resolved."""
        with_parts = [y.comparison_rank for y in report.yoga_deep if y.participants]
        without = [y.comparison_rank for y in report.yoga_deep if not y.participants]
        if with_parts and without:
            assert max(with_parts) < min(without)

    def test_unresolved_yogas_say_so_not_no_shadbala(self, report):
        """A chart WITH a Shadbala table must never be told it has none."""
        for y in report.yoga_deep:
            if not y.participants:
                assert "could not be resolved" in y.strength_note
                assert "no Shadbala on this chart" not in y.strength_note

    def test_no_dataclass_repr_leaks_into_rendered_output(self, report):
        """Operating-period quality renders as prose, never LordQuality(...)."""
        assert "LordQuality(" not in to_markdown(report)
        for y in report.yoga_deep:
            for line in y.periods:
                assert "LordQuality(" not in line

    @pytest.mark.skipif(HAS_CORPUS,
                        reason="absence line only renders where the corpus is absent")
    def test_corpus_absent_definition_is_honest_absence_not_empty_quote(self, report):
        """passage() returning None must yield an absence line + paraphrase, not an empty quote."""
        for y in report.yoga_deep:
            assert y.definition_quote, y.id
            assert "source corpus not mounted" in y.definition_quote
            assert y.cite in y.definition_quote
            assert y.effect.strip()[:40] in y.definition_quote
        assert '""' not in _yoga_section(to_markdown(report))

    def test_cancellation_wording_claims_only_encoded_checks(self, report):
        """Only neecha-bhanga is graded; the not-graded modifiers are disclosed with their cites."""
        for y in report.yoga_deep:
            assert "no cancellation Raman states applies" not in y.cancellation_note
            if "neecha bhanga" not in y.cancellation_note:
                assert "encoded Raman-stated cancellations" in y.cancellation_note
                assert "HTJAH-I:2948-2956" in y.cancellation_note
                assert "HTJAH-I:15903" in y.cancellation_note
