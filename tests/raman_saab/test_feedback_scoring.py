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
