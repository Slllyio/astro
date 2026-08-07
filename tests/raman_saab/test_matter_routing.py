"""Matter routing — naming the house a question is about, without answering a different one.

`/report/ask` grounds every question in the whole chart, which gives each house a single
headline line. A reader asking about marriage got "House 7 (Venus lord) reads 'mixed'" and
nothing more, competing with fifty other facts. Routing adds that house's full breakdown.

Two properties carry the whole design and both are pinned here:

* **It ADDS.** Focusing must never remove a fact the question would otherwise have seen —
  narrowing a marriage question to the 7th would hide the dasha, the 2nd and the 8th, which is
  the REPORT COMPLETENESS failure wearing new clothes.
* **It refuses to guess.** No matter named, or several named, changes nothing. Answering for
  one of two matters a reader mentioned is worse than answering generally for both.

It is DOCTRINE — Raman's own house assignment for each matter — and never a measured ranking.
`golden_attention` cannot validate a claim of that kind: all 48 of its significations map to
exactly one house, so a topic->house model scores p@1 = 1.000 by reading its own label
(SALIENCE_BASELINE Phase 5). These tests assert behaviour, never superiority.
"""
from __future__ import annotations

import pytest

from app.llm.report_explainer import build_evidence
from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.matter_routing import explicit_house, focus_house, matters_in
from app.raman_saab.report_json import to_report_dict


class TestTheQuestionsThatMustRoute:
    @pytest.mark.parametrize("question, house", [
        ("will my marriage work out?", 7),
        ("what does my chart say about children", 5),
        ("how is my career looking", 10),
        ("tell me about my health", 6),
        ("will I have money", 2),
        ("what about my mother", 4),
        ("is my father well", 9),
        ("do I have enemies", 6),
    ])
    def test_a_plainly_named_matter_routes_to_its_house(self, question, house):
        assert focus_house(question) == house


class TestTheQuestionsThatMustNOTRoute:
    """Every one of these was a real misroute or a trap that produced one."""

    @pytest.mark.parametrize("question, why", [
        ("tell me about my life", "names no matter — the whole chart already answers it"),
        ("what about money and marriage?", "two matters; picking one drops the other"),
        ("my workout routine", "'workout' is not 'work'; substring matching would route it"),
        ("how does this work", "'work' was dropped from career for exactly this"),
        ("", "empty"),
    ])
    def test_ambiguous_or_empty_changes_nothing(self, question, why):
        assert focus_house(question) is None, why

    def test_marriage_work_out_is_not_a_career_question(self):
        """THE regression. 'will my marriage work out?' matched career AND marriage while
        'work' was a career keyword, so the single most likely question this feature exists
        for routed nowhere. Dropping the word cost 'how is my work going', which degrades to
        the whole-chart answer — the safe direction to fail in."""
        assert "career" not in matters_in("will my marriage work out?")
        assert focus_house("will my marriage work out?") == 7


class TestExplicitBhavaReferences:
    """'house' is a dwelling to a reader and a bhava to this method. In a question about a
    chart the jargon wins, so it is matched precisely rather than left in the `happiness`
    vocabulary — where 'tell me about my 7th house' routed to the 4th."""

    @pytest.mark.parametrize("question, house", [
        ("tell me about my 7th house", 7),
        ("what about house 5", 5),
        ("my 10th bhava", 10),
        ("read my 1st house", 1),
    ])
    def test_a_named_bhava_wins(self, question, house):
        assert focus_house(question) == house

    @pytest.mark.parametrize("question", ["what does my 13th house say", "house 0", "house 99"])
    def test_an_impossible_bhava_is_refused(self, question):
        assert explicit_house(question) is None

    def test_the_regex_actually_has_word_boundaries(self):
        """It once did not. A heredoc turned the `\\b` escapes into literal BACKSPACE
        characters (0x08), producing a pattern that could never match and printed as if it
        were correct — only `repr` revealed it. Assert on the compiled pattern, not on output
        that happens to look right."""
        from app.raman_saab.matter_routing import _EXPLICIT_HOUSE
        assert "\x08" not in _EXPLICIT_HOUSE.pattern, "backspace char, not a word boundary"
        assert _EXPLICIT_HOUSE.pattern.startswith("\\b")


class TestFocusAddsAndNeverNarrows:
    """The property the whole design rests on."""

    @pytest.fixture(scope="class")
    def report_dict(self):
        return to_report_dict(build_detailed_report(
            BirthData("Akash", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)))

    def test_no_fact_is_lost_by_focusing(self, report_dict):
        base = build_evidence(report_dict, "whole")
        focused = build_evidence(report_dict, "whole", focus_house=7)
        lost = {f.text for f in base.facts} - {f.text for f in focused.facts}
        assert not lost, (
            f"focusing dropped {len(lost)} fact(s) — it must ADD. Narrowing a marriage "
            f"question to the 7th hides the dasha, the 2nd and the 8th")

    def test_focusing_adds_the_house_detail(self, report_dict):
        base = build_evidence(report_dict, "whole")
        focused = build_evidence(report_dict, "whole", focus_house=7)
        assert len(focused.facts) > len(base.facts)
        assert "House 7" in focused.facts[0].text, "the focused house should lead the evidence"

    def test_numbering_stays_contiguous(self, report_dict):
        """A Fact's `n` is what the answer cites, so a gap or a duplicate surfaces as a broken
        citation in the reader's answer."""
        for focus in (None, 7, 10):
            ev = build_evidence(report_dict, "whole", focus_house=focus)
            ns = [f.n for f in ev.facts]
            assert ns == list(range(1, len(ns) + 1)), f"focus={focus}: numbering {ns[:6]}..."

    def test_no_duplicate_facts(self, report_dict):
        ev = build_evidence(report_dict, "whole", focus_house=7)
        texts = [f.text for f in ev.facts]
        assert len(texts) == len(set(texts)), "the house detail was merged without deduping"

    def test_focus_none_is_byte_identical_to_before(self, report_dict):
        """The default path must be untouched — most questions name no single matter."""
        a = build_evidence(report_dict, "whole")
        b = build_evidence(report_dict, "whole", focus_house=None)
        assert [(f.n, f.text, f.cite) for f in a.facts] == [(f.n, f.text, f.cite) for f in b.facts]
