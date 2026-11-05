"""The persona study's own logic — the parts that decide what the result means.

No network, no ephemeris, no answers: everything here is a pure function over small
synthetic inputs. The tests that matter most are the ones checking the study CANNOT report
agreement it has not earned — that a pole is decoded the right way round, that the
cross-chart control is capable of returning zero contrast, and that the coin-flip arm is a
real coin flip rather than something that happens to agree.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from tools.raman_saab.persona_birthdata import BirthRecord
from tools.raman_saab.persona_study import (
    Candidate, PER_STRATUM, ROSTER, _pole, _pole_matches, admit, chart_key_for,
    coinflip_answers, cross_chart, mcnemar, off_vocabulary, option_vocabulary,
    paired_outcomes, permutation_p, reference_date, time_precision)


def _rec(**kw) -> BirthRecord:
    base = dict(slug="s", name="n", year=1950, month=6, day=1, hour=9, minute=30,
                place="Somewhere (X)", rodden="AA", source_note="")
    return BirthRecord(**{**base, **kw})


class TestAPoleIsDecodedTheRightWayRound:
    """A Part C item pairs the chart's own predicate with its exact inverse. Answering the
    key means claiming the chart's pole; answering the other means claiming the opposite.
    Getting this backwards would invert the entire study silently."""

    def test_choosing_the_key_claims_the_charts_own_pole(self):
        assert _pole("favourable", True) == "favourable"
        assert _pole("afflicted", True) == "afflicted"

    def test_choosing_the_other_option_claims_the_inverse(self):
        assert _pole("favourable", False) == "afflicted"
        assert _pole("afflicted", False) == "favourable"

    def test_mixed_pairs_against_one_way_not_against_afflicted(self):
        """`mixed` means both poles at once; its inverse is 'solidly one thing'."""
        assert _pole("mixed", True) == "mixed"
        assert _pole("mixed", False) == "one_way"

    def test_a_verdict_with_no_inverse_yields_no_claim(self):
        assert _pole("insufficient-evidence", True) == ""
        assert _pole("neutral", False) == ""


class TestAPoleIsComparedToAnotherChartHonestly:
    def test_like_matches_like(self):
        assert _pole_matches("favourable", "favourable") is True
        assert _pole_matches("afflicted", "afflicted") is True

    def test_opposites_miss(self):
        assert _pole_matches("favourable", "afflicted") is False
        assert _pole_matches("afflicted", "favourable") is False

    def test_one_way_agrees_with_either_solid_verdict(self):
        """'Solidly one thing or the other' is satisfied by favourable OR afflicted, and
        contradicted by mixed. Treating it as favourable-only would bias the control."""
        assert _pole_matches("one_way", "favourable") is True
        assert _pole_matches("one_way", "afflicted") is True
        assert _pole_matches("one_way", "mixed") is False

    def test_mixed_agrees_only_with_mixed(self):
        assert _pole_matches("mixed", "mixed") is True
        assert _pole_matches("mixed", "favourable") is False

    def test_an_abstained_verdict_is_not_comparable(self):
        """None, not False — counting an abstention as a miss would manufacture a low score
        for charts the engine declined to judge."""
        assert _pole_matches("favourable", "insufficient-evidence") is None
        assert _pole_matches("favourable", "") is None


class TestTheCrossChartControl:
    """PREREG §2a. The control has to be capable of returning a zero contrast, or it is not
    a control — so both a signal case and a no-signal case are checked."""

    _V = {"a": {"marriage": {"verdict": "favourable"}, "wealth": {"verdict": "afflicted"}},
          "b": {"marriage": {"verdict": "afflicted"}, "wealth": {"verdict": "favourable"}},
          "c": {"marriage": {"verdict": "favourable"}, "wealth": {"verdict": "afflicted"}}}

    def test_a_persona_agreeing_with_their_own_chart_scores_matched(self):
        claims = {"a": [("marriage", "favourable"), ("wealth", "afflicted")]}
        out = cross_chart(claims, self._V)
        assert out["matched"] == [2, 2]

    def test_the_mismatched_arm_scores_against_everyone_else(self):
        """One persona, three charts: two donors x two significations = four comparisons."""
        claims = {"a": [("marriage", "favourable"), ("wealth", "afflicted")]}
        out = cross_chart(claims, self._V)
        assert out["mismatched"][1] == 4
        assert out["mismatched"][0] == 2          # agrees with c, disagrees with b

    def test_a_persona_who_carries_no_information_shows_no_contrast(self):
        """`a` and `c` have identical charts, so answers true of one are true of the other:
        matched and mismatched must come out equal and the contrast zero."""
        claims = {"a": [("marriage", "favourable")], "c": [("marriage", "favourable")]}
        out = cross_chart({k: v for k, v in claims.items()},
                          {"a": self._V["a"], "c": self._V["c"]})
        assert out["contrast"] == 0.0

    def test_abstentions_are_dropped_from_both_arms(self):
        verdicts = {"a": {"marriage": {"verdict": "insufficient-evidence"}},
                    "b": {"marriage": {"verdict": "favourable"}}}
        out = cross_chart({"a": [("marriage", "favourable")]}, verdicts)
        assert out["matched"] == [0, 0] and out["mismatched"] == [1, 1]

    def test_a_signification_the_donor_never_judged_is_skipped(self):
        out = cross_chart({"a": [("children", "favourable")]}, self._V)
        assert out["matched"] == [0, 0]


class TestThePermutationTest:
    def test_it_is_deterministic(self):
        """The number goes into a results document, so two runs must agree exactly."""
        claims = {"a": [("marriage", "favourable")], "b": [("marriage", "afflicted")],
                  "c": [("marriage", "favourable")]}
        verdicts = {"a": {"marriage": {"verdict": "favourable"}},
                    "b": {"marriage": {"verdict": "afflicted"}},
                    "c": {"marriage": {"verdict": "favourable"}}}
        assert permutation_p(claims, verdicts, rounds=200) == \
            permutation_p(claims, verdicts, rounds=200)

    def test_it_refuses_a_sample_too_small_to_permute(self):
        assert permutation_p({"a": [("m", "favourable")]},
                             {"a": {"m": {"verdict": "favourable"}}}) is None

    def test_it_is_a_probability(self):
        claims = {s: [("marriage", "favourable")] for s in "abcd"}
        verdicts = {s: {"marriage": {"verdict": "favourable"}} for s in "abcd"}
        p = permutation_p(claims, verdicts, rounds=100)
        assert p is not None and 0.0 < p <= 1.0


class TestTheCoinFlipArm:
    _PAYLOAD = {"instrument": {"parts": [{"questions": [
        {"qid": "inst.v2.C1", "kind": "choice",
         "options": [{"value": "opt1"}, {"value": "opt2"}]},
        {"qid": "inst.v2.C2", "kind": "choice",
         "options": [{"value": "opt1"}, {"value": "opt2"}]},
        {"qid": "inst.v2.A35", "kind": "events", "options": []}]}]}}

    def test_it_is_reproducible(self):
        assert coinflip_answers(self._PAYLOAD, seed="x") == \
            coinflip_answers(self._PAYLOAD, seed="x")

    def test_a_different_seed_gives_a_different_arm(self):
        """Otherwise the 'control' is one fixed pattern and its rate is an accident."""
        seeds = {tuple(sorted(coinflip_answers(self._PAYLOAD, seed=s).items()))
                 for s in ("a", "b", "c", "d", "e", "f")}
        assert len(seeds) > 1

    def test_it_only_answers_questions_that_have_options(self):
        out = coinflip_answers(self._PAYLOAD, seed="x")
        assert set(out) == {"inst.v2.C1", "inst.v2.C2"}


class TestTheAdmissionGate:
    def test_a_missing_page_is_refused(self):
        rec, why = admit(Candidate("x", 1, "UTC"), None)
        assert rec is None and "no nativity" in why

    def test_a_weak_rating_is_refused_with_its_grade_named(self):
        rec, why = admit(Candidate("x", 1, "UTC"), _rec(rodden="C"))
        assert rec is None and "C" in why

    def test_a_noon_default_is_refused(self):
        """Deviation 1 — 12:00 is what a record carries when the hour is unknown."""
        rec, why = admit(Candidate("x", 1, "UTC"), _rec(hour=12, minute=0))
        assert rec is None and "noon default" in why

    def test_a_local_mean_time_birth_is_refused(self):
        rec, why = admit(Candidate("x", 1, "Europe/Berlin"), _rec(year=1879))
        assert rec is None and "standard time" in why


class TestTheReferenceDateSitsInsideTheLife:
    def test_someone_who_reached_forty_is_read_at_forty(self):
        assert reference_date(_rec(year=1926, month=6, day=1),
                              Candidate("x", 1, "UTC")) == (1966, 6, 1)

    def test_someone_who_died_young_is_read_at_the_midpoint_of_their_adult_life(self):
        """Monroe died at 36; halfway between 18 and 36 is 27."""
        got = reference_date(_rec(year=1926, month=6, day=1),
                             Candidate("x", 2, "UTC", died_before_40=1962))
        assert got == (1953, 6, 1)

    def test_a_death_before_eighteen_still_yields_a_date_after_birth(self):
        got = reference_date(_rec(year=1950, month=1, day=1),
                             Candidate("x", 2, "UTC", died_before_40=1960))
        assert got[0] >= 1968


class TestBookkeeping:
    def test_time_precision_is_recorded(self):
        assert time_precision(_rec(minute=0)) == "round_hour"
        assert time_precision(_rec(minute=30)) == "quarter"
        assert time_precision(_rec(minute=47)) == "minute"

    def test_the_chart_key_matches_the_servers_own_format(self):
        """The server builds this from the request; a submission and a score must agree on
        which nativity they are talking about, to the digit."""
        key = chart_key_for({"year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
                             "tz_offset": 5.5, "latitude": 12.97, "longitude": 77.59})
        assert key == "1990-07-15T12:00+5.50@12.9700,77.5900"

    def test_the_roster_is_registered_in_full_strata(self):
        from collections import Counter
        counts = Counter(c.stratum for c in ROSTER)
        assert set(counts) == {1, 2, 3, 4, 5, 6}
        assert all(n >= PER_STRATUM for n in counts.values()), \
            "a stratum registered fewer candidates than it needs to fill"

    def test_no_person_is_registered_twice(self):
        slugs = [c.slug for c in ROSTER]
        assert len(slugs) == len(set(slugs))


class TestTheAnswerVocabularyGate:
    """An option code no question offered does not crash anything — it simply never matches,
    so the study reports a colder number for a reason recorded nowhere. `verify` is the last
    point at which that is still cheap to see, and it runs before any key is computed.
    """

    payload = {"instrument": {"parts": [{"part": "A", "questions": [
        {"qid": "inst.v2.A18", "kind": "multi", "options": [
            {"value": "law"}, {"value": "transport"}]},
        {"qid": "inst.v2.A25", "kind": "year", "options": []},
        {"qid": "inst.v2.A35", "kind": "events", "options": [
            {"value": "marriage"}, {"value": "job_start"}]},
        {"qid": "inst.v2.C1", "kind": "choice", "options": [
            {"value": "opt1"}, {"value": "opt2"}]},
    ]}]}}

    def _stray(self, answers: dict) -> dict:
        return off_vocabulary(answers, option_vocabulary(self.payload))

    def test_every_code_the_question_offered_passes_silently(self):
        """A multi answer drawn wholly from its own option bank raises nothing."""
        assert self._stray({"inst.v2.A18": "law,transport"}) == {}

    def test_a_code_belonging_to_another_question_is_named(self):
        """`manual` is a work-MODE code; on the trade question it can only ever miss."""
        assert self._stray({"inst.v2.A18": "law,manual"}) == {"inst.v2.A18": ("manual",)}

    def test_a_repeat_row_is_checked_against_its_base_question(self):
        """Event rows arrive as `A35#3`; the vocabulary belongs to `A35`."""
        assert self._stray({"inst.v2.A35#3": "1990-06:marriage"}) == {}
        assert self._stray({"inst.v2.A35#3": "1990:divorce"}) == {"inst.v2.A35#3": ("divorce",)}

    def test_a_question_with_no_options_is_left_alone(self):
        """A year is a year — there is no bank to check it against."""
        assert self._stray({"inst.v2.A25": "1959"}) == {}

    def test_a_confidence_carries_no_option_code(self):
        """`C1.confidence` is 1..5, not one of C1's two poles."""
        assert self._stray({"inst.v2.C1": "opt2", "inst.v2.C1.confidence": "4"}) == {}

    def test_an_answer_to_a_question_that_does_not_exist_is_named(self):
        """A qid the payload never carried is a worse error than a stray code, not a lesser one."""
        assert self._stray({"inst.v2.A99": "yes"}) == {"inst.v2.A99": ("<no such question>",)}


class TestThePairedComparisonBetweenArms:
    """The blind and contaminated arms answer the SAME items for the same charts, so the two
    rates are paired, not independent. Items both arms get right — or both get wrong — say
    nothing about which arm is better; only the discordant pairs do. Comparing two unpaired
    proportions here would throw away that structure and overstate its own confidence.
    """

    def test_only_discordant_pairs_are_counted(self):
        """Agreement carries no signal, however much of it there is."""
        first = {("a", "q1"): True, ("a", "q2"): True, ("a", "q3"): False}
        second = {("a", "q1"): True, ("a", "q2"): True, ("a", "q3"): False}
        b, c, p = mcnemar(first, second)
        assert (b, c) == (0, 0) and p is None

    def test_an_arm_that_is_right_where_the_other_is_wrong_is_counted_once_each_way(self):
        """b is first-only, c is second-only — the two directions are kept apart."""
        first = {("a", "q1"): True, ("a", "q2"): False, ("a", "q3"): True}
        second = {("a", "q1"): False, ("a", "q2"): True, ("a", "q3"): True}
        b, c, _ = mcnemar(first, second)
        assert (b, c) == (1, 1)

    def test_a_one_sided_advantage_becomes_a_small_p(self):
        """Eight discordant pairs all favouring one arm is 2 * 0.5**8."""
        first = {("a", f"q{i}"): True for i in range(8)}
        second = {("a", f"q{i}"): False for i in range(8)}
        b, c, p = mcnemar(first, second)
        assert (b, c) == (8, 0)
        assert p is not None and abs(p - 2 * 0.5 ** 8) < 1e-9

    def test_an_even_split_is_not_evidence(self):
        """Four each way is exactly what no difference looks like."""
        first = {("a", f"q{i}"): i < 4 for i in range(8)}
        second = {("a", f"q{i}"): i >= 4 for i in range(8)}
        b, c, p = mcnemar(first, second)
        assert (b, c) == (4, 4) and p == 1.0

    def test_items_only_one_arm_answered_are_dropped(self):
        """An unpaired item has no pair; including it would be comparing unlike things."""
        first = {("a", "q1"): True, ("a", "q2"): True}
        second = {("a", "q1"): False}
        b, c, _ = mcnemar(first, second)
        assert (b, c) == (1, 0)

    def test_the_same_qid_on_different_charts_stays_separate(self):
        """Keys are (slug, qid): two personas answering C1 are two items, not one."""
        first = {("a", "q1"): True, ("b", "q1"): True}
        second = {("a", "q1"): False, ("b", "q1"): False}
        b, c, _ = mcnemar(first, second)
        assert (b, c) == (2, 0)


class TestWhichItemsAreScoredAsForcedChoice:
    """The primary measure is the Part C forced choice, whose null is exactly 0.5 by
    construction. Anything else in the instrument has a null nobody knows, so it must not
    reach this pool."""

    key = {"answers": {"inst.v2.C1": "opt1", "inst.v2.C2": "opt2", "inst.v2.A7": "robust"},
           "meta": {"inst.v2.C1": {"kind": "forced_choice", "verdict": "favourable"},
                    "inst.v2.C2": {"kind": "forced_choice", "verdict": "afflicted"},
                    "inst.v2.A7": {"kind": "life_fact"}}}

    def test_a_forced_choice_answered_with_the_key_is_a_hit(self):
        assert paired_outcomes(self.key, {"inst.v2.C1": "opt1"}) == {"inst.v2.C1": True}

    def test_a_forced_choice_answered_the_other_way_is_a_miss(self):
        assert paired_outcomes(self.key, {"inst.v2.C1": "opt2"}) == {"inst.v2.C1": False}

    def test_a_life_fact_never_enters_the_forced_choice_pool(self):
        """A7 has no 0.5 null — pooling it would silently change what the p-value means."""
        assert paired_outcomes(self.key, {"inst.v2.A7": "robust"}) == {}

    def test_an_unanswered_item_contributes_nothing(self):
        assert paired_outcomes(self.key, {}) == {}
