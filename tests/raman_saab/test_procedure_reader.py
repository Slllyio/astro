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


# -- Round 2 (2026-10-25): fixes from the mismatch review ------------------------------------

def _stated(positions: dict[str, float], asc_lon: float):
    """A chart from stated longitudes; each planet's Bhava is its whole-sign house."""
    from app.raman_saab.chart.model import RamanChart
    asc_sign = int(asc_lon // 30) + 1
    pos = {n: {"lon": lon, "bhava": (int(lon // 30) + 1 - asc_sign) % 12 + 1}
           for n, lon in positions.items()}
    return RamanChart.from_stated_positions(pos, asc_lon=asc_lon, ayanamsa="raman")


def _planet_factor(step: str, planet: str, grade: str) -> Factor:
    return Factor(step, f"the {step} {planet}", (), grade, 0, "", grade, False)


class TestFatherKarakaDirection:
    """Afflictions to the Sun decide the father; a strong Sun rescues nothing (HTJAH:13126-13127)."""

    def test_strong_sun_does_not_rescue_afflicted_house_and_lord(self) -> None:
        """Chart 90 shape: 9th house and lord afflicted, Sun strong -> afflicted, not favourable."""
        m = matter_for(9, "father")
        f = {"house": _factor("house", "afflicted"), "lord": _factor("lord", "blemished"),
             "karaka": _factor("karaka", "strong"), "moon": _factor("moon", "moderate")}
        c = conclude(m, f)
        assert c.verdict == "afflicted"
        assert c.rule_cite == cite("two_of_three")

    def test_afflicted_sun_decides_against_good_house_and_lord(self) -> None:
        """9th house and lord good, Sun afflicted -> afflicted: the karaka's affliction decides."""
        m = matter_for(9, "father")
        f = {"house": _factor("house", "strong"), "lord": _factor("lord", "fairly strong"),
             "karaka": _factor("karaka", "afflicted"), "moon": _factor("moon", "moderate")}
        c = conclude(m, f)
        assert c.verdict == "afflicted" and c.rule_cite == cite("father_karaka_decides")


class TestLongevitySameLord:
    """For Aries and Libra the Lagna lord is the 8th lord; the comparison does not apply."""

    def test_same_planet_falls_back_to_the_tally(self) -> None:
        """Libra: Venus is both lords, so the verdict is the plain two-of-three tally."""
        m = matter_for(8, "longevity")
        f = {"house": _factor("house", "strong"), "lord": _planet_factor("lord", "Venus", "afflicted"),
             "karaka": _factor("karaka", "fairly strong"), "moon": _factor("moon", "moderate")}
        c = conclude(m, f, lagna_lord=_planet_factor("lord", "Venus", "afflicted"))
        assert c.verdict == "favourable" and c.verdict == c.tally

    def test_two_lords_are_still_compared(self) -> None:
        """Different Lagna and 8th lords: a stronger Lagna lord gives the long band."""
        m = matter_for(8, "longevity")
        f = {"house": _factor("house", "afflicted"), "lord": _planet_factor("lord", "Mars", "afflicted"),
             "karaka": _factor("karaka", "moderate"), "moon": _factor("moon", "moderate")}
        c = conclude(m, f, lagna_lord=_planet_factor("lord", "Venus", "strong"))
        assert c.verdict == "favourable" and c.rule_cite.startswith(cite("longevity_lords"))


class TestRamanNeechabhanga:
    """Only Raman's printed cancellations count (HTJAH:16178-16181)."""

    _BASE = {"Sun": 190.0, "Venus": 200.0, "Saturn": 100.0, "Mars": 10.0, "Mercury": 175.0,
             "Jupiter": 40.0, "Rahu": 50.0, "Ketu": 230.0}

    def test_dispositor_conjunction_alone_does_not_cancel(self) -> None:
        """Sun debilitated in Libra with Venus, neither Venus nor Saturn in a kendra: no relief."""
        from app.raman_saab.primitives.bhangas import neecha_bhanga
        from app.raman_saab.procedure.grading import raman_neecha_bhanga
        ch = _stated({**self._BASE, "Moon": 70.0}, asc_lon=35.0)
        assert neecha_bhanga("Sun", ch)            # the engine's conjunction clause fires
        assert not raman_neecha_bhanga("Sun", ch)  # Raman prints no such condition

    def test_dispositor_in_kendra_from_moon_cancels(self) -> None:
        """Venus, lord of Libra, in the 10th from a Capricorn Moon cancels the Sun's debility."""
        from app.raman_saab.procedure.grading import raman_neecha_bhanga
        ch = _stated({**self._BASE, "Moon": 280.0}, asc_lon=35.0)
        assert raman_neecha_bhanga("Sun", ch)


class TestSignRelation:
    """Raman's "friendly" and "inimical" sign follow the natural relation."""

    def test_jupiter_in_libra_is_inimical(self) -> None:
        """Chart 48: Jupiter in Libra is "placed in an inimical sign" (HTJAH:2930-2931)."""
        from app.raman_saab.procedure.grading import sign_relation
        assert sign_relation("Jupiter", 7) == "enemy"

    def test_mars_and_venus_in_gemini(self) -> None:
        """Chart 60: Mars in Gemini is "the sign of an enemy"; Chart 59: Venus there is friendly."""
        from app.raman_saab.procedure.grading import sign_relation
        assert sign_relation("Mars", 3) == "enemy"
        assert sign_relation("Venus", 3) == "friend"


class TestEmptyHouse:
    """An unoccupied, unaspected house is fairly strong (HTJAH:3669-3670, 2809-2810)."""

    def test_empty_house_counts_one_good_step(self) -> None:
        """Every house with no occupant and no aspect carries a +1 testimony citing Chart 52."""
        from app.raman_saab.procedure.grading import grade_house
        ch = _stated({"Sun": 5.0, "Moon": 8.0, "Mars": 12.0, "Mercury": 15.0, "Jupiter": 18.0,
                      "Venus": 21.0, "Saturn": 25.0, "Rahu": 28.0, "Ketu": 208.0}, asc_lon=2.0)
        empty = [h for h in range(1, 13) for it in grade_house(ch, h).items
                 if "neither occupied nor aspected" in it.text]
        assert empty, "the stated chart should leave some house empty"
        for h in empty:
            it = next(i for i in grade_house(ch, h).items if "neither occupied" in i.text)
            assert it.weight == 1 and it.cite == cite("empty_house_fairly_strong")


class TestLordInEighthFromOwnHouse:
    """Chart 61: Mars in a kendra and own sign, but 8th from the 3rd, is weak (HTJAH:3826-3828)."""

    def test_eighth_from_third_and_sixth_lord_moon(self) -> None:
        """Aquarius Lagna, Mars and the Moon (6th lord) in Scorpio: both testimonies are -1."""
        from app.raman_saab.procedure.grading import grade_planet
        ch = _stated({"Sun": 280.0, "Moon": 215.0, "Mars": 220.0, "Mercury": 290.0,
                      "Jupiter": 120.0, "Venus": 300.0, "Saturn": 10.0, "Rahu": 160.0,
                      "Ketu": 340.0}, asc_lon=305.0)
        f = grade_planet(ch, "Mars", step="lord", house=3, role="the 3rd lord")
        eighth = [i for i in f.items if "8th from the 3rd" in i.text]
        assert eighth and eighth[0].weight == -1
        assert eighth[0].cite == cite("eighth_from_own_house")
        moon = [i for i in f.items if i.text.startswith("Moon") and i.substep == "associates"]
        assert moon and moon[0].weight == -1 and "lord of the 6th" in moon[0].text


class TestBeneficSixthLord:
    """A natural benefic owning the 6th afflicts by contact, unless it owns the Lagna or a trine."""

    def test_which_benefics_count(self) -> None:
        """Moon for Aquarius and Mercury for Aries count; Jupiter for Cancer (6th and 9th) does not."""
        from app.raman_saab.procedure.grading import _benefic_sixth_lord
        pos = {"Sun": 0.5, "Moon": 40.0, "Mars": 80.0, "Mercury": 120.0, "Jupiter": 160.0,
               "Venus": 200.0, "Saturn": 240.0, "Rahu": 280.0, "Ketu": 100.0}
        assert _benefic_sixth_lord(_stated(pos, asc_lon=305.0), "Moon")
        assert _benefic_sixth_lord(_stated(pos, asc_lon=5.0), "Mercury")
        assert not _benefic_sixth_lord(_stated(pos, asc_lon=95.0), "Jupiter")
        assert not _benefic_sixth_lord(_stated(pos, asc_lon=5.0), "Saturn")


# -- 2026-10-28: fixes from the Mainpuri hand reading (PROCEDURE_READER_FIXES_PREREG) ---------

@pytest.fixture(scope="module")
def mainpuri():
    """Mainpuri 1989-10-12 10:02 IST, 27N14, 79E02: Scorpio Lagna, Rahu at Aquarius 0 deg 28'."""
    birth = BirthData("mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)
    return cast_chart(birth, ayanamsa="raman")


def _items(reading_, step: str) -> list:
    return [i for f in reading_.factors if f.step == step for i in f.items]


class TestMainpuriFixes:
    """The fixes that passed the pre-registered rule, and the switches of those that failed."""

    def test_switches_match_the_preregistered_results(self) -> None:
        """F1 and F2 passed (153/298/91 against 152/295/94); F3, F4 and F5 failed and stay off."""
        from app.raman_saab.procedure.grading import FIXES
        assert FIXES == {"F1_lagna_lord_balanced": True,
                         "F2_lord_in_own_house_aspect_once": True,
                         "F3_node_aspect_from_bhava": False,
                         "F4_navamsa_own_sign_malefic": False,
                         "F5_span_decides_longevity": False}

    def test_lagna_lord_mars_is_balanced_not_malefic(self, mainpuri) -> None:
        """F1: Mars, Scorpio's Lagna lord, in the 11th counts 0, not as a malefic (HTJAH:575-578)."""
        mars = [i for i in _items(read_matter(mainpuri, 11, "gains", with_timing=False), "house")
                if i.text.startswith("Mars")]
        assert mars and mars[0].weight == 0 and "the Lagna lord" in mars[0].text

    def test_saturn_aspect_counted_once_for_lord_in_own_house(self, mainpuri) -> None:
        """F2: Mercury rules and occupies the 11th; Saturn's aspect is charged on the house only."""
        r = read_matter(mainpuri, 11, "gains", with_timing=False)
        on_house = [i for i in _items(r, "house") if i.text.startswith("Saturn")]
        on_lord = [i for i in _items(r, "lord") if i.text.startswith("Saturn")]
        assert on_house[0].weight == -1
        assert on_lord[0].weight == 0 and "already weighed on the house" in on_lord[0].text

    def test_children_not_denied_when_a_benefic_redeems(self) -> None:
        """T1: afflicted house and lord, a redeeming view from the Moon: few or delayed."""
        m = matter_for(5, "children")
        f = {"house": _factor("house", "afflicted"), "lord": _factor("lord", "blemished"),
             "karaka": _factor("karaka", "moderate"),
             "moon": _factor("moon", "fairly strong", redeeming=True)}
        assert conclude(m, f).outcome.startswith("few or delayed")
        f["moon"] = _factor("moon", "moderate")
        assert conclude(m, f).outcome == "none: children denied"

    def test_mainpuri_children_not_denied(self, mainpuri) -> None:
        """T1 on the chart that showed it: Jupiter in the 5th from the Moon redeems."""
        c = read_matter(mainpuri, 5, "children", with_timing=False).conclusion
        assert "denied" not in c.outcome

    def test_longevity_shows_the_computed_span(self, mainpuri) -> None:
        """T2: the 84-year Pindayu is shown beside the lords' band, and the disagreement named."""
        subs = dict(read_matter(mainpuri, 8, "longevity", with_timing=False)
                    .conclusion.sub_answers)
        span = subs["the computed span (stage zero)"]
        assert span.startswith("84.") and "Purnayu" in span and "disagrees" in span

    def test_special_features_open_the_reading(self, mainpuri) -> None:
        """T3: vargottama Lagna, Mercury's Navamsa fall, Kemadruma cancelled, the sandhi margin."""
        feats = " ".join(stage_zero(mainpuri).special_features)
        assert "The Lagna is vargottama" in feats
        assert "Mercury is exalted in Virgo but debilitated in the Navamsa" in feats
        assert "Kemadruma is present" in feats and "cancelled" in feats
        assert re.search(r"Mercury is 0\.\d\d degrees from a Bhava-sandhi", feats)

    def test_node_aspect_moves_with_the_bhava_when_switched_on(self, mainpuri, monkeypatch) -> None:
        """F3 (held): Rahu in the 4th sign but the 3rd Bhava aspects the 9th, not the 10th."""
        from app.raman_saab.procedure import grading
        assert "Rahu" in grading.aspecting_house(mainpuri, 10)
        monkeypatch.setitem(grading.FIXES, "F3_node_aspect_from_bhava", True)
        assert "Rahu" not in grading.aspecting_house(mainpuri, 10)
        assert "Rahu" in grading.aspecting_house(mainpuri, 9)

    def test_features_and_outcomes_pass_the_guard(self, mainpuri) -> None:
        """Every new line passes _FORBIDDEN_RE."""
        text = to_text(read_procedure(mainpuri, with_timing=False))
        hits = [ln for ln in text.splitlines() if _FORBIDDEN_RE.search(ln)]
        assert not hits, hits[:5]
