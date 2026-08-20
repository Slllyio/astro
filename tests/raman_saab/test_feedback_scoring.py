"""Scoring the feedback instrument — the measurement, and the ways it could flatter itself.

The tests that matter most are the ones that check the scorer CANNOT report a good result it
has not earned: a perfect run must score perfect and a wrong run must score zero, the null for
the dated spine must be computed rather than assumed, submissions answered after the reading
must not pool with blind ones, and agreement on the inverted channels must never be counted as
accuracy.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.feedback_instrument import (
    build_feedback_instrument, instrument_key)
from app.raman_saab.feedback_scoring import (
    SPINE_TOLERANCE_MONTHS, aggregate, binomial_p_two_sided, parse_answers, parse_chart_key,
    render_aggregate, score_chart)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


def _report(birth: BirthData = _CANONICAL) -> dict:
    from app.raman_saab.detailed_report import build_detailed_report
    from app.raman_saab.report_json import to_report_dict
    return to_report_dict(build_detailed_report(birth))


@pytest.fixture(scope="module")
def report() -> dict:
    return _report()


@pytest.fixture(scope="module")
def inst(report) -> dict:
    return build_feedback_instrument(report)


@pytest.fixture(scope="module")
def key(report) -> dict:
    return instrument_key(report)


def _forced_rows(key: dict, *, correct: bool, inverted: bool = False):
    """Answer every forced choice, either all right or all wrong."""
    rows = []
    for qid, expected in key["answers"].items():
        if key["meta"].get(qid, {}).get("kind") != "forced_choice":
            continue
        if (qid in key["inverted"]) != inverted:
            continue
        other = "opt2" if expected == "opt1" else "opt1"
        rows.append((qid, expected if correct else other, None))
    return rows


class TestStatistics:
    def test_the_binomial_is_exact_and_two_sided(self):
        """The forced-choice design's whole value is that its null is known exactly, so the
        p-value is computed rather than approximated."""
        assert binomial_p_two_sided(10, 10) == pytest.approx(2 / 1024)
        assert binomial_p_two_sided(5, 10) == pytest.approx(1.0)
        assert binomial_p_two_sided(0, 10) == pytest.approx(2 / 1024)
        assert binomial_p_two_sided(0, 0) is None

    def test_a_biased_null_is_honoured(self):
        """The spine's null is not 0.5 — it is whatever fraction of the span the tolerance
        windows actually cover, so the test must accept an arbitrary p."""
        assert binomial_p_two_sided(8, 10, 0.25) < 0.01
        assert binomial_p_two_sided(2, 10, 0.25) > 0.5


class TestForcedChoice:
    def test_a_perfect_run_scores_perfect(self, report, key):
        card = score_chart(report, _forced_rows(key, correct=True))
        assert card.forced.n >= 8
        assert card.forced.hits == card.forced.n
        assert card.forced.rate == 1.0
        assert card.forced.p_value < 0.05

    def test_a_wrong_run_scores_zero(self, report, key):
        card = score_chart(report, _forced_rows(key, correct=False))
        assert card.forced.hits == 0
        assert card.forced.p_value < 0.05          # significantly WRONG is also a finding

    def test_unanswered_items_are_not_counted_as_misses(self, report, key):
        """A part-filled form is the normal case. Scoring a blank as wrong would drag every
        real result toward zero and make an honest partial submission look damning."""
        rows = _forced_rows(key, correct=True)[:3]
        card = score_chart(report, rows)
        assert card.forced.n == 3 and card.forced.hits == 3

    def test_rarity_weighting_favours_the_rare_reading(self, report, key):
        """A reading 4% of charts carry discriminates; one 45% carry barely can. The weighted
        rate must therefore differ from the flat rate when the hits are not uniform."""
        rows = _forced_rows(key, correct=True)
        card = score_chart(report, rows)
        weights = {w for _q, _s, _h, w in card.forced.per_item}
        assert len(weights) > 1, "all items weighted the same — rarity is not being read"
        assert all(0.0 < w <= 1.0 for w in weights)

    def test_the_inverted_channels_are_pooled_separately(self, report, key):
        """Agreement on a channel the atlas proved runs backwards is evidence AGAINST. Pooling
        it with the rest would launder acquiescence into accuracy."""
        if not key["inverted"]:
            pytest.skip("no inverted-channel item on this chart")
        rows = _forced_rows(key, correct=True) + _forced_rows(
            key, correct=True, inverted=True)
        card = score_chart(report, rows)
        assert card.inverted.n == len(key["inverted"])
        main_ids = {q for q, _s, _h, _w in card.forced.per_item}
        assert not (main_ids & set(key["inverted"]))


class TestLifeFacts:
    def test_an_answer_matching_the_engine_scores_a_hit(self, report, inst):
        """H6 debts on the canonical chart has a verdict; answering in the same direction is a
        hit and the opposite is a miss. Both directions are checked, so a scorer that always
        said 'hit' would fail."""
        verdict = None
        for e in report["calibration"]["6"]["entries"]:
            if e["signification"] == "debts":
                verdict = e["verdict"]
        assert verdict in ("favourable", "afflicted")
        agreeing = "none" if verdict == "favourable" else "serious_now"
        opposing = "serious_now" if verdict == "favourable" else "none"
        qid = next(q["qid"] for p in inst["parts"] for q in p["questions"]
                   if q.get("maps_to") == "h6.debts")
        hit = score_chart(report, [(qid, agreeing, None)])
        miss = score_chart(report, [(qid, opposing, None)])
        assert [i.verdict for i in hit.life if i.qid == qid] == ["hit"]
        assert [i.verdict for i in miss.life if i.qid == qid] == ["miss"]

    def test_body_regions_are_compared_code_against_code(self, report, inst):
        """The reader picks from the same vocabulary HPA-29's table emits, so the comparison
        needs no interpretation step — which is what makes it a measurement."""
        qid = next(q["qid"] for p in inst["parts"] for q in p["questions"]
                   if q.get("maps_to") == "medical.regions")
        card = score_chart(report, [(qid, "throat_neck,skin,legs_feet", None)])
        item = next(i for i in card.life if i.qid == qid)
        assert item.verdict in ("hit", "partial", "miss", "not_scoreable")
        assert item.engine, "the engine side of the comparison is empty"
        assert "regions are marked" in item.note

    def test_an_unmapped_engine_region_is_reported_not_hidden(self, report, inst):
        """If HPA-29's table grows a word the keyword map does not know, that is coverage loss
        and must be visible — otherwise it silently reads as a miss."""
        qid = next(q["qid"] for p in inst["parts"] for q in p["questions"]
                   if q.get("maps_to") == "medical.regions")
        card = score_chart(report, [(qid, "skin", None)])
        item = next(i for i in card.life if i.qid == qid)
        assert "had no code" in item.note

    def test_informational_answers_are_not_scored(self, report, inst):
        """Build, birth order and the like exist for rectification, not for accuracy. Counting
        them as hits would inflate every scorecard with things the engine never claimed."""
        qid = next(q["qid"] for p in inst["parts"] for q in p["questions"]
                   if q.get("maps_to") == "rect.build")
        card = score_chart(report, [(qid, "medium", None)])
        item = next(i for i in card.life if i.qid == qid)
        assert item.verdict == "informational" and item.weight == 0.0


class TestTheDatedSpine:
    def test_the_chance_rate_is_computed_from_the_actual_windows(self, report, inst):
        """The period changes cluster, so summing the tolerance windows would roughly double
        the apparent denominator and make a coin-flip look like a finding. The union over the
        reported span is what is used, and it must land in a sane open interval."""
        boundaries = inst["boundaries"]
        assert boundaries
        y, m, _d = boundaries[0]["date"].split("-")
        rows = [(f"inst.{inst['version']}.A35#1", f"{y}-{m}:job_start", None),
                (f"inst.{inst['version']}.A35#2", "2005-01:move_home", None)]
        card = score_chart(report, rows)
        assert card.spine.events == 2
        assert card.spine.near_boundary >= 1
        assert card.spine.chance_rate is not None
        assert 0.0 < card.spine.chance_rate < 1.0
        assert card.spine.tolerance_months == SPINE_TOLERANCE_MONTHS

    def test_an_event_far_from_every_boundary_does_not_count(self, report, inst):
        rows = [(f"inst.{inst['version']}.A35#1", "1991-01:move_home", None)]
        card = score_chart(report, rows)
        assert card.spine.events == 1 and card.spine.near_boundary == 0

    def test_a_year_without_a_month_is_still_usable(self, report, inst):
        """People remember the year and not the month. Dropping those rows would throw away
        most of the answer, so an undated month is read as mid-year and still scored."""
        rows = [(f"inst.{inst['version']}.A35#1", "2005:move_home", None)]
        card = score_chart(report, rows)
        assert card.spine.events == 1


class TestReadingOrderIsNeverLost:
    def test_a_submission_defaults_to_after_reading(self, report, key):
        card = score_chart(report, _forced_rows(key, correct=True))
        assert card.context == "after_reading"
        assert "ANSWERED AFTER READING" in card.headline

    def test_the_context_row_is_read_back(self, report, key, inst):
        rows = _forced_rows(key, correct=True) + [
            (f"inst.{inst['version']}.meta.context", "before_reading", None)]
        card = score_chart(report, rows)
        assert card.context == "before_reading"
        assert "ANSWERED AFTER READING" not in card.headline

    def test_the_aggregate_keeps_blind_submissions_in_their_own_pool(self, report, key, inst):
        """Pooling a satisfaction survey with blind evidence is the one mistake that would
        make every number here meaningless, so the split is structural."""
        blind = score_chart(report, _forced_rows(key, correct=True) + [
            (f"inst.{inst['version']}.meta.context", "before_reading", None)], chart_key="a")
        sighted = score_chart(report, _forced_rows(key, correct=True), chart_key="b")
        agg = aggregate([blind, sighted])
        assert agg.charts == 2 and agg.blind_charts == 1
        assert agg.forced.n == blind.forced.n + sighted.forced.n
        assert agg.forced_blind_only.n == blind.forced.n

    def test_the_aggregate_says_so_when_nothing_was_answered_blind(self, report, key):
        agg = aggregate([score_chart(report, _forced_rows(key, correct=True))])
        assert any("NO submission was answered before the reading" in n for n in agg.notes)
        assert any("too few to conclude" in n for n in agg.notes)


class TestAggregateIsAWorkList:
    def test_it_reports_per_reading_hit_rates(self, report, key):
        """The point of aggregating is to name WHICH readings carry information — that is the
        improvement list, and it is what the scorer exists to produce."""
        agg = aggregate([score_chart(report, _forced_rows(key, correct=True))])
        assert agg.per_signification
        for _sig, (h, n) in agg.per_signification.items():
            assert 0 <= h <= n

    def test_chapter_complaints_are_counted(self, report, inst):
        qid = next(q["qid"] for p in inst["parts"] for q in p["questions"]
                   if q.get("maps_to") == "reaction.wrong")
        card = score_chart(report, [(qid, "marriage,wealth", None)])
        agg = aggregate([card])
        assert agg.chapter_wrong == {"marriage": 1, "wealth": 1}

    def test_a_harm_report_is_raised_above_the_accuracy_numbers(self, report, inst):
        qid = next(q["qid"] for p in inst["parts"] for q in p["questions"]
                   if q.get("maps_to") == "reaction.harm")
        agg = aggregate([score_chart(report, [(qid, "yes", None)])])
        assert agg.harm_reports == 1
        assert any("upsetting or frightening" in n for n in agg.notes)

    def test_the_rendered_report_leads_with_its_caveats(self, report, key):
        text = render_aggregate(aggregate([score_chart(report, _forced_rows(key, correct=True))]))
        assert text.index("!") < text.index("FORCED CHOICE")
        assert "chance 0.5" in text


class TestChartKeyRoundTrip:
    def test_a_key_parses_back_to_the_birth_data(self):
        b = parse_chart_key("1990-07-15T12:00+5.50@12.9700,77.5900")
        assert (b.year, b.month, b.day, b.hour, b.minute) == (1990, 7, 15, 12, 0)
        assert b.tz_offset == 5.5 and b.latitude == 12.97 and b.longitude == 77.59

    def test_a_malformed_key_is_refused_rather_than_guessed(self):
        assert parse_chart_key("not a key") is None
        assert parse_chart_key("") is None

    def test_the_recast_chart_reproduces_the_shuffle_the_reader_answered(self):
        """The key keeps four decimal places. If the shuffle depended on anything finer — it
        depended on the ascendant longitude to six — the recast would deal the options the
        other way round and every stored answer would silently invert."""
        precise = _report(BirthData("x", 1990, 7, 15, 12, 0, 5.5, 12.97000091, 77.59000042))
        recast = _report(parse_chart_key("1990-07-15T12:00+5.50@12.9700,77.5900"))
        assert instrument_key(precise)["answers"] == instrument_key(recast)["answers"]


class TestAnswerParsing:
    def test_multi_selects_events_and_confidence_are_told_apart(self):
        ans = parse_answers([
            ("inst.v2.A6", "skin,eyes", None),
            ("inst.v2.A35#1", "2019-03:job_start", None),
            ("inst.v2.C1", "opt1", "because X"),
            ("inst.v2.C1.confidence", "4", None),
            ("inst.v2.meta.context", "before_reading", None),
        ])
        assert ans.multi["inst.v2.A6"] == ("skin", "eyes")
        assert ans.events["inst.v2.A35"] == ((2019, 3, "job_start"),)
        assert ans.by_qid["inst.v2.C1"] == "opt1"
        assert ans.confidence["inst.v2.C1"] == 4
        assert ans.free_text["inst.v2.C1"] == "because X"
        assert ans.context == "before_reading"


class TestEventsAgainstTheirOwnHouse:
    """The strongest test the instrument runs: the reader supplies both halves blind — they
    date the event before reading anything, and the house each kind of event is read from is
    fixed doctrine rather than a choice made afterwards."""

    def test_it_grades_rather_than_asking_whether_the_house_was_lit_at_all(self, report):
        """Measured on a real chart, every house is activated in 74-100% of periods (mean
        ~88%) — Raman's timer_set is deliberately broad. A was-it-lit test would score ~88% by
        construction. The GRADE discriminates, so that is what is scored, and the base rates
        must land well away from 1.0 for the test to mean anything."""
        from app.raman_saab.feedback_scoring import _house_top_grade_base_rate
        base = _house_top_grade_base_rate(report)
        assert base, "no timeline to derive a base rate from"
        assert all(0.0 <= v <= 1.0 for v in base.values())
        assert min(base.values()) < 0.8, (
            f"every house is at top grade almost always ({base}) — this test cannot "
            f"discriminate on this chart and the scorer must not pretend otherwise")

    def test_the_base_rate_is_duration_weighted_not_period_counted(self):
        """Bhuktis differ in length by years. Counting periods would let a run of short ones
        outvote one long one and bias the null."""
        from app.raman_saab.feedback_scoring import _house_top_grade_base_rate
        rep = {"timeline": [
            {"start_jd": 0.0, "end_jd": 900.0,
             "activated": [{"house": 7, "grade": "limited"}]},
            {"start_jd": 900.0, "end_jd": 1000.0,
             "activated": [{"house": 7, "grade": "par_excellence"}]},
        ]}
        # one period each way, but the top-grade one is a tenth of the span
        assert _house_top_grade_base_rate(rep)[7] == pytest.approx(0.1)

    def test_an_event_in_a_top_graded_period_counts_and_one_below_does_not(self, report):
        """Both directions, so a scorer that always said 'hit' fails."""
        from app.raman_saab.feedback_scoring import _house_top_grade_base_rate
        import swisseph as swe
        wanted = {}
        for p in report["timeline"]:
            for a in p["activated"]:
                if a["house"] == 7 and a["grade"] not in wanted:
                    y, m, _d, _h = swe.revjul((p["start_jd"] + p["end_jd"]) / 2,
                                              swe.GREG_CAL)
                    wanted[a["grade"]] = f"{int(y):04d}-{int(m):02d}:marriage"
        if len(wanted) < 2:
            pytest.skip("H7 never changes grade on this chart")
        top = next(v for k, v in wanted.items() if k == "par_excellence")
        low = next(v for k, v in wanted.items() if k != "par_excellence")
        hit = score_chart(report, [("inst.v2.A35#1", top, None)])
        miss = score_chart(report, [("inst.v2.A35#1", low, None)])
        assert hit.event_houses.top_grade == 1 and hit.event_houses.events == 1
        assert miss.event_houses.top_grade == 0 and miss.event_houses.events == 1

    def test_an_event_outside_the_timeline_is_reported_not_counted(self, report):
        """The timeline covers a window. Scoring an event the engine never spoke about would
        be inventing a result; dropping it silently would hide how much was unscoreable."""
        card = score_chart(report, [("inst.v2.A35#1", "1900-01:marriage", None)])
        assert card.event_houses.outside_window == 1
        assert card.event_houses.events == 0

    def test_a_neutral_event_is_not_direction_scored(self, report):
        """Moving abroad is an opportunity to some people and an upheaval to others. Forcing a
        sign on it would manufacture agreement out of the labelling."""
        from app.raman_saab.feedback_instrument import EVENT_VALENCE
        assert EVENT_VALENCE["moved_abroad"] == "neutral"
        card = score_chart(report, [("inst.v2.A35#1", "2024-06:moved_abroad", None)])
        assert card.event_houses.direction_scored == 0

    def test_the_rectification_grid_is_not_pooled_with_the_turning_points(self, report):
        """Part B collects anchor events for rectification, in the same row format. They are a
        different question and must not inflate this measurement."""
        card = score_chart(report, [("inst.v2.B6#1", "2024-06:marriage", None)])
        assert card.event_houses.events == 0


class TestThePoissonBinomialNull:
    def test_it_matches_the_plain_binomial_when_every_rate_is_equal(self):
        """Sanity anchor: with identical probabilities it must reduce to the ordinary case."""
        from app.raman_saab.feedback_scoring import poisson_binomial_tail
        assert poisson_binomial_tail([0.5] * 5, 5) == pytest.approx(0.5 ** 5)
        assert poisson_binomial_tail([0.5] * 5, 0) == pytest.approx(1.0)

    def test_unequal_rates_are_honoured(self):
        """The whole reason for it: a house at top grade 90% of the time and one at 10% are
        not the same trial, and averaging them would be an approximation dressed as exact."""
        from app.raman_saab.feedback_scoring import poisson_binomial_tail
        assert poisson_binomial_tail([0.9, 0.1], 2) == pytest.approx(0.09)
        assert poisson_binomial_tail([0.9, 0.1], 1) == pytest.approx(0.9 + 0.1 - 0.09)

    def test_a_certain_house_cannot_manufacture_a_finding(self):
        """A house at top grade for the whole timeline gives a guaranteed hit. The null must
        absorb it — p stays 1.0 — rather than counting it as evidence."""
        from app.raman_saab.feedback_scoring import poisson_binomial_tail
        assert poisson_binomial_tail([1.0, 1.0], 2) == pytest.approx(1.0)


class TestConfidenceIsScored:
    def test_sure_and_unsure_are_split_and_the_middle_is_left_out(self, report, key):
        """A 3 out of 5 is neither, and pushing it to whichever side flatters the numbers is
        exactly the sort of choice that makes a measurement worthless."""
        rows = _forced_rows(key, correct=True)
        graded = []
        for i, (qid, ans, _f) in enumerate(rows):
            graded.append((qid, ans, None))
            graded.append((qid + ".confidence", ("5", "3", "1")[i % 3], None))
        card = score_chart(report, graded)
        assert card.confident.n + card.unsure.n < card.forced.n
        assert card.confident.n and card.unsure.n

    def test_the_scorecard_says_so_when_certainty_buys_nothing(self, report, key):
        """A reader who scores no better where they were most certain is agreeing with
        whatever is shown. That has to be said in words, not left in a table."""
        rows = []
        for i, (qid, expected, _f) in enumerate(_forced_rows(key, correct=True)):
            wrong = "opt2" if expected == "opt1" else "opt1"
            rows.append((qid, wrong if i % 2 == 0 else expected, None))
            rows.append((qid + ".confidence", "5" if i % 2 == 0 else "1", None))
        text = render_aggregate(aggregate([score_chart(report, rows)]))
        if "answered SURE" in text:
            assert "MORE certain" in text


class TestFreeTextReachesTheOperator:
    def test_it_is_quoted_verbatim_and_grouped_by_question(self, report):
        card = score_chart(report, [("inst.v2.D8", "", "the marriage chapter was uncanny")])
        agg = aggregate([card])
        assert agg.free_text.get("D8") == ("the marriage chapter was uncanny",)
        assert "the marriage chapter was uncanny" in render_aggregate(agg)

    def test_blank_supplements_are_not_carried(self, report):
        card = score_chart(report, [("inst.v2.D8", "", "   ")])
        assert aggregate([card]).free_text == {}


class TestTheOperatorScorecardIsAFileNotARoute:
    def test_no_scoring_route_is_registered(self):
        """There is no admin role in this codebase, so a live scorecard would be readable by
        any signed-in user — and a reader who can see which readings score well can infer the
        key for their own chart, poisoning every later submission."""
        import ast
        import pathlib
        src = (pathlib.Path(__file__).resolve().parents[2] / "app" / "api"
               / "report_routes.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        # Checked against the PARSED module, not the text: `report_routes` mentions
        # `instrument_key` in a docstring, explaining why the submit endpoint deliberately does
        # not score back. A substring check would fail on that comment — punishing the file for
        # documenting the rule it obeys.
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "feedback_scoring" in node.module:
                    imported.add(node.module)
                for alias in node.names:
                    if alias.name in ("instrument_key", "score_chart", "aggregate"):
                        imported.add(alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "feedback_scoring" in alias.name:
                        imported.add(alias.name)
        assert not imported, f"the routes reach the scorer: {sorted(imported)}"

    def test_the_reason_is_recorded_where_someone_would_add_one(self):
        import inspect
        from app.raman_saab.feedback_scoring import render_aggregate_html
        doc = inspect.getdoc(render_aggregate_html) or ""
        assert "not a route" in doc and "admin role" in doc

    def test_the_page_is_self_contained_and_well_formed(self, report, key):
        import html.parser
        from app.raman_saab.feedback_scoring import render_aggregate_html
        cards = [score_chart(report, _forced_rows(key, correct=True), chart_key="k")]
        page = render_aggregate_html(aggregate(cards), cards)
        assert "<script" not in page and "http://" not in page and "https://" not in page

        void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
                "meta", "param", "source", "track", "wbr"}

        class P(html.parser.HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.stack: list[str] = []
                self.errors: list[str] = []

            def handle_starttag(self, tag, attrs):
                if tag not in void:
                    self.stack.append(tag)

            def handle_endtag(self, tag):
                if tag in void:
                    return
                if not self.stack or self.stack[-1] != tag:
                    self.errors.append(tag)
                else:
                    self.stack.pop()

        p = P()
        p.feed(page)
        assert not p.errors and not p.stack, (p.errors, p.stack)

    def test_the_caveats_render_above_the_numbers(self, report, key):
        from app.raman_saab.feedback_scoring import render_aggregate_html
        cards = [score_chart(report, _forced_rows(key, correct=True), chart_key="k")]
        page = render_aggregate_html(aggregate(cards), cards)
        assert page.index('class="notes"') < page.index("Forced choice")


class TestEveryAnsweredQuestionReachesTheScorecard:
    """Three Part A questions were stored and then silently dropped at scoring.

    All three shared one cause: `_score_life` dispatches on `maps_to`, but `maps_to` is not
    unique. A10 and A11 both carry `h9.father`, A28 and A29 both carry `h5.children`, and
    `_POLARITY_MAP` held only the FIRST question's vocabulary — so the second question's
    answers matched neither the good nor the bad tuple and fell out as `not_scoreable`
    forever. A31 had no entry at all and produced no `Item` whatsoever.

    A reader who answers a question is owed its appearance in the scorecard. Silently
    discarding the answer is the same defect class as a report section that renders a count
    instead of its rows.
    """

    @staticmethod
    def _qid(inst: dict, sid: str) -> str:
        """Look up by question id, not by `maps_to` — `maps_to` is what was ambiguous."""
        return next(q["qid"] for p in inst["parts"] for q in p["questions"]
                    if q["qid"].endswith("." + sid))

    @pytest.mark.parametrize("sid,answer", [("A11", "prospered"), ("A11", "reversal"),
                                            ("A29", "no"), ("A29", "yes")])
    def test_the_second_question_on_a_shared_topic_is_scored(self, report, inst, sid, answer):
        """`prospered`/`reversal` are H9 father and `no`/`yes` are H5 children just as surely
        as the vocabularies that were already mapped."""
        qid = self._qid(inst, sid)
        item = next(i for i in score_chart(report, [(qid, answer, None)]).life if i.qid == qid)
        assert item.verdict in ("hit", "miss"), \
            f"{sid}={answer} scored {item.verdict!r}, so the answer never reached the reader"

    def test_the_two_poles_of_a_shared_topic_disagree_with_each_other(self, report, inst):
        """The real check: opposite answers must not both be hits. A mapping that put every
        value in the good tuple would satisfy the test above and still measure nothing."""
        for sid, good, bad in (("A11", "prospered", "reversal"), ("A29", "no", "yes")):
            qid = self._qid(inst, sid)
            a = next(i for i in score_chart(report, [(qid, good, None)]).life if i.qid == qid)
            b = next(i for i in score_chart(report, [(qid, bad, None)]).life if i.qid == qid)
            assert a.verdict != b.verdict, f"{sid}: both poles scored {a.verdict!r}"

    def test_the_first_question_on_a_shared_topic_still_works(self, report, inst):
        """The fix widens the vocabulary; it must not disturb what already scored."""
        for sid, answer in (("A10", "close"), ("A28", "none")):
            qid = self._qid(inst, sid)
            item = next(i for i in score_chart(report, [(qid, answer, None)]).life
                        if i.qid == qid)
            assert item.verdict in ("hit", "miss")

    def test_the_mental_health_question_is_recorded_but_never_scored(self, report, inst):
        """A31 asks about periods of low mood or anxiety. The engine's mind screen is
        explicitly present-or-absent and carries its own caution that it is not a diagnosis
        (`psych.mind_caution`), so scoring this as a hit would have the scorecard claim the
        engine diagnoses mental illness. It must appear — the answer was given — as
        informational, at weight zero, alongside build and birth order."""
        qid = self._qid(inst, "A31")
        item = next((i for i in score_chart(report, [(qid, "brief", None)]).life
                     if i.qid == qid), None)
        assert item is not None, "A31 produced no Item at all — the answer vanished"
        assert item.verdict == "informational" and item.weight == 0.0


class TestThePooledSpineNullIsTheOneThatWasComputed:
    """`_score_spine` derives each chart's chance rate from the reader's own event span and
    the Mahadasha boundaries inside it. `aggregate` then threw that away and tested the pooled
    count against a hard-coded 0.25, which is nobody's chance rate — it is the fraction a
    +/-3-month window would cover if boundaries fell every two years, which they do not.

    The pooled p-value is therefore reported against a null the data never had.
    """

    def test_the_pooled_null_is_the_mean_of_the_per_chart_rates(self, report, key, inst):
        qid = next(q["qid"] for p in inst["parts"] for q in p["questions"]
                   if q.get("maps_to") == "spine.events")
        boundaries = [b["date"] for b in inst["boundaries"]]
        assert boundaries, "the canonical chart has no Mahadasha boundary in its window"
        rows = _forced_rows(key, correct=True)
        rows += [(f"{qid}#1", f"{boundaries[0][:7]}:marriage", None),
                 (f"{qid}#2", "1998-04:job_start", None)]
        card = score_chart(report, rows)
        agg = aggregate([card])
        assert card.spine.chance_rate is not None
        assert agg.spine_chance is not None, "the pooled null is not reported at all"
        assert abs(agg.spine_chance - card.spine.chance_rate) < 1e-9, (
            f"pooled null {agg.spine_chance} ignores this chart's computed "
            f"{card.spine.chance_rate}")

    def test_the_hard_coded_quarter_is_gone(self):
        """Named explicitly so a later refactor cannot quietly reintroduce it."""
        import inspect
        from app.raman_saab import feedback_scoring as fs
        src = inspect.getsource(fs.aggregate)
        assert "0.25" not in src, "aggregate still carries a hard-coded spine null"
