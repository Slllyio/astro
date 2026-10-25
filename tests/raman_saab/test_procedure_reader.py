"""Tests for the procedure reader (``app/raman_saab/procedure``).

The reader is a separate instrument: these tests pin its shape (Raman's template order, the
one-step Navamsa, the two-of-three tally and the mother tie-break), one printed timing example
(Chart 64, mother died in Mars Dasa, Saturn Bhukti, HTJAH:4404), that every citation resolves to
the corpus, that every line of a reading passes the report guard, and that nothing outside the
package imports it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.llm.report_explainer import _FORBIDDEN_RE
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.procedure import read_matter, read_procedure
from app.raman_saab.procedure.citations import CITATIONS, cite
from app.raman_saab.procedure.conclusion import conclude
from app.raman_saab.procedure.matters import matter_for
from app.raman_saab.procedure.model import GRADES, TEMPLATE_ORDER, Factor
from app.raman_saab.procedure.reader import stage_zero
from app.raman_saab.procedure.render import to_text

_ROOT = Path(__file__).resolve().parents[2]
_CORPUS = (_ROOT / "data" / "knowledge_library" / "sources" / "how_to_judge_a_horoscope_raman"
           / "chapter_001_full-text-unsplit.md")


@pytest.fixture(scope="module")
def canonical():
    """The canonical baseline chart: Bangalore 1990-07-15 12:00 IST."""
    birth = BirthData("canonical", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    return cast_chart(birth, ayanamsa="raman")


@pytest.fixture(scope="module")
def reading(canonical):
    """The full procedure reading of the canonical chart."""
    return read_procedure(canonical)


@pytest.fixture(scope="module")
def chart64():
    """HTJAH Chart 64 (golden HTJAH-I.h4_01): 1912-08-08 19:35 IST, 13N, 77E35."""
    birth = BirthData("chart64", 1912, 8, 8, 19, 35, 5.5, 13.0, 77.5833)
    return cast_chart(birth, ayanamsa="raman")


def _factor(step: str, grade: str, redeeming: bool = False) -> Factor:
    return Factor(step, f"the {step}", (), grade, 0, "", grade, redeeming)


class TestCitations:
    """Every step's citation points at a real line range of HTJAH."""

    def test_every_snippet_occurs_in_its_line_range(self) -> None:
        """Each CITATIONS snippet occurs (whitespace-normalised) inside its HTJAH line range."""
        if not _CORPUS.exists():
            pytest.skip("HTJAH corpus is git-ignored and absent here")
        lines = _CORPUS.read_text(encoding="utf-8").splitlines()
        norm = lambda s: " ".join(s.split())  # noqa: E731
        bad = []
        for key, (a, b, snip) in CITATIONS.items():
            text = norm(" ".join(lines[a - 1:b]))
            if norm(snip) not in text:
                bad.append(f"{key} {a}-{b}: {snip!r}")
        assert not bad, bad

    def test_cite_formats_htjah_line_range(self) -> None:
        """cite() renders the HTJAH:<first>-<last> form."""
        a, b, _ = CITATIONS["two_of_three"]
        assert cite("two_of_three") == (f"HTJAH:{a}" if a == b else f"HTJAH:{a}-{b}")


class TestTemplateOrder:
    """Raman reads House -> Lord -> Karaka -> Moon -> Conclusion in every chart."""

    def test_every_matter_follows_the_template_order(self, reading) -> None:
        """Every matter's steps are a subsequence of house, lord, karaka, moon, conclusion."""
        for m in reading.matters:
            steps = m.steps
            assert steps[0] == "house" and steps[1] == "lord" and steps[-1] == "conclusion"
            idx = [TEMPLATE_ORDER.index(s) for s in steps]
            assert idx == sorted(idx), (m.house, m.matter, steps)

    def test_every_item_carries_a_citation(self, reading) -> None:
        """Every testimony and every conclusion rule carries an HTJAH citation."""
        for m in reading.matters:
            for f in m.factors:
                for it in f.items:
                    assert it.cite.startswith("HTJAH:"), (m.matter, it)
            assert m.conclusion.rule_cite.startswith("HTJAH:")


class TestNavamsaOneStep:
    """The Navamsa adjusts a grade by one step at most and never reverses it (HTJAH:4688)."""

    def test_navamsa_moves_at_most_one_step(self, reading) -> None:
        """No factor's final grade is more than one step from its Rasi grade."""
        for m in reading.matters:
            for f in m.factors:
                assert abs(f.navamsa_shift) <= 1
                assert abs(GRADES.index(f.grade) - GRADES.index(f.rasi_grade)) <= 1

    def test_navamsa_never_reverses_a_vote(self, reading) -> None:
        """A Rasi grade that votes good never ends bad, and the reverse."""
        def vote(g: str) -> str:
            i = GRADES.index(g)
            return "good" if i >= 3 else ("bad" if i <= 1 else "neutral")
        for m in reading.matters:
            for f in m.factors:
                assert {vote(f.rasi_grade), vote(f.grade)} != {"good", "bad"}


class TestConclusion:
    """Two of three carry the verdict (HTJAH:2111-2113), with the matter tie-breaks."""

    def test_two_good_of_three_is_favourable(self) -> None:
        """House and lord good against a bad karaka: the 2nd's wealth reads favourable."""
        m = matter_for(2, "wealth")
        f = {"house": _factor("house", "strong"), "lord": _factor("lord", "fairly strong"),
             "karaka": _factor("karaka", "afflicted"), "moon": _factor("moon", "moderate")}
        c = conclude(m, f)
        assert c.tally == "favourable" and c.verdict == "favourable"
        assert dict(c.votes) == {"house": "good", "lord": "good", "karaka": "bad"}

    def test_two_bad_of_three_is_afflicted_with_floor(self) -> None:
        """House and lord bad, a benefic present: afflicted, but the matter comes and suffers."""
        m = matter_for(2, "wealth")
        f = {"house": _factor("house", "blemished", redeeming=True),
             "lord": _factor("lord", "afflicted"), "karaka": _factor("karaka", "strong"),
             "moon": _factor("moon", "moderate")}
        c = conclude(m, f)
        assert c.verdict == "afflicted" and "comes but suffers" in c.outcome

    def test_mother_moon_decides_early_loss(self) -> None:
        """Strong 4th house and lord but an afflicted Moon: early loss (HTJAH:4435-4436)."""
        m = matter_for(4, "mother")
        f = {"house": _factor("house", "strong"), "lord": _factor("lord", "fairly strong"),
             "karaka": _factor("karaka", "afflicted"), "moon": _factor("moon", "moderate")}
        c = conclude(m, f)
        assert c.tally == "favourable"
        assert c.verdict == "afflicted"
        subs = dict(c.sub_answers)
        assert subs["early loss (the Moon decides)"] == "early loss of the mother is indicated"
        assert subs["how long (the house and lord decide)"].endswith("lengthen her life")

    def test_sentence_follows_raman_formula(self) -> None:
        """The sentence reads "[house]; [lord]; [karaka]. Hence ..."."""
        m = matter_for(2, "wealth")
        f = {"house": _factor("house", "strong"), "lord": _factor("lord", "fairly strong"),
             "karaka": _factor("karaka", "afflicted"), "moon": _factor("moon", "moderate")}
        s = conclude(m, f).sentence
        assert s.startswith("The house is strong; the lord is fairly strong; the karaka is")
        assert ". Hence the indications for" in s


class TestRelativeDeathTiming:
    """Chart 64: the mother died in Mars Dasa, Saturn Bhukti (HTJAH:4404)."""

    def test_chart64_mars_saturn_among_mother_death_periods(self, chart64) -> None:
        """Mars Mahadasha / Saturn Bhukti is a candidate period for the mother's death."""
        s0 = stage_zero(chart64)
        m = read_matter(chart64, 4, "mother", span=s0.span_years, span_class=s0.span_class)
        rule = next(t for t in m.timing if t.kind == "relative_death")
        pairs = {(c.maha, c.antar) for c in rule.candidates}
        assert ("Mars", "Saturn") in pairs
        quals = dict(rule.qualifiers)
        assert "Mars" in quals and "Saturn" in quals

    def test_printed_position_chart_has_no_timing(self) -> None:
        """A chart without a birth time gets verdicts but no periods."""
        from app.raman_saab.chart.model import RamanChart
        ch = RamanChart.from_stated_positions(
            {"Sun": {"lon": 10.0, "bhava": 1}, "Moon": {"lon": 100.0, "bhava": 4},
             "Mars": {"lon": 200.0, "bhava": 7}, "Mercury": {"lon": 20.0, "bhava": 1},
             "Jupiter": {"lon": 130.0, "bhava": 5}, "Venus": {"lon": 40.0, "bhava": 2},
             "Saturn": {"lon": 280.0, "bhava": 10}, "Rahu": {"lon": 300.0, "bhava": 11},
             "Ketu": {"lon": 120.0, "bhava": 5}}, asc_lon=5.0, ayanamsa="raman")
        r = read_procedure(ch)
        assert all(m.timing == () for m in r.matters)


class TestGuardAndSerialisation:
    """Every reading speaks in the classical indication idiom and serialises to JSON."""

    def test_every_line_passes_the_report_guard(self, reading) -> None:
        """No line of the canonical reading (text form) matches _FORBIDDEN_RE."""
        hits = [ln for ln in to_text(reading).splitlines() if _FORBIDDEN_RE.search(ln)]
        assert not hits, hits[:5]

    def test_every_conclusion_sentence_passes_the_guard(self, reading) -> None:
        """Every conclusion sentence passes _FORBIDDEN_RE."""
        for m in reading.matters:
            assert not _FORBIDDEN_RE.search(m.conclusion.sentence), m.conclusion.sentence

    def test_reading_is_json_serialisable(self, reading) -> None:
        """to_dict() round-trips through json."""
        d = json.loads(json.dumps(reading.to_dict()))
        assert d["stage_zero"]["lagna"].startswith("Virgo")
        assert len(d["matters"]) == len(reading.matters)


class TestIndependence:
    """The reader is a separate instrument: nothing outside it imports it."""

    def test_no_module_outside_the_package_imports_the_reader(self) -> None:
        """Only the package, its CLI, its measurement tool and this test import it."""
        pat = re.compile(r"(from|import)\s+app\.raman_saab\.procedure(\.|\s|$)", re.M)
        allowed = {_ROOT / "tools" / "raman_saab" / "procedure_reader_measure.py",
                   Path(__file__).resolve()}
        pkg = _ROOT / "app" / "raman_saab" / "procedure"
        offenders = []
        for base in ("app", "tools", "tests"):
            for py in (_ROOT / base).rglob("*.py"):
                if pkg in py.parents or py.resolve() in allowed:
                    continue
                if pat.search(py.read_text(encoding="utf-8", errors="ignore")):
                    offenders.append(str(py.relative_to(_ROOT)))
        assert not offenders, offenders
