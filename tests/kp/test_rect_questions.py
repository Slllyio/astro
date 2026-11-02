"""Tests for chart-chosen rectification questions (app.kp.rect_questions) and the session tool."""

from __future__ import annotations

import math

import numpy as np
import pytest

pytest.importorskip("swisseph")

from app.kp.chart import Birth  # noqa: E402
from app.kp.rect_questions import (EITHER, FACT_BY_KEY, NO, R_FACT, YES, Built, answer_probs, build,  # noqa: E402
                                   credible, info_gain, interval_likelihood, likelihood, rank,
                                   resolution_classes, uniform, update)

B = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)  # canonical baseline (CLAUDE.md)


def _toy(preds: dict[str, dict[str, list[int]]], n: int) -> Built:
    return Built(B, list(range(n)), (0.0, 1.0), preds, {})


class TestLikelihoods:
    def test_yes_no_reliability_maps_predictions(self):
        """A rule predicting yes gives P(yes) = r, no gives 1 - r, no opinion gives 0.5."""
        q = _toy({"married": {"kp": [YES, NO, EITHER]}}, 3)
        p = answer_probs(q, "married")[:, 1]
        assert p == pytest.approx([R_FACT, 1 - R_FACT, 0.5])

    def test_two_engines_are_averaged_not_multiplied(self):
        """When KP says yes and Raman says no, one answer must not count twice: P(yes) = 0.5."""
        q = _toy({"children": {"kp": [YES, YES], "raman": [NO, YES]}}, 2)
        p = answer_probs(q, "children")[:, 1]
        assert p == pytest.approx([0.5, R_FACT])

    def test_choice_puts_r_on_predicted_option(self):
        """Speech style: predicted option gets r, the others share 1 - r, no opinion is uniform."""
        q = _toy({"speech_style": {"kp": [0, EITHER]}}, 2)
        P = answer_probs(q, "speech_style")
        k = len(FACT_BY_KEY["speech_style"].options)
        assert P[0, 0] == pytest.approx(FACT_BY_KEY["speech_style"].reliability)
        assert P[1] == pytest.approx(np.full(k, 1 / k))
        assert P.sum(axis=1) == pytest.approx([1.0, 1.0])


class TestInformation:
    def test_constant_fact_carries_no_information(self):
        """A fact predicted the same at every minute cannot split the window: 0 bits."""
        q = _toy({"married": {"kp": [YES] * 5}}, 5)
        assert info_gain(q, "married", uniform(q)) == pytest.approx(0.0, abs=1e-12)

    def test_splitting_fact_is_positive_and_bounded(self):
        """A half-yes, half-no fact gains between 0 and 1 bit (binary answer)."""
        q = _toy({"married": {"kp": [YES] * 5 + [NO] * 5}}, 10)
        ig = info_gain(q, "married", uniform(q))
        assert 0.2 < ig < 1.0

    def test_update_moves_mass_to_agreeing_minutes(self):
        """Answering yes raises the minutes that predicted yes by the factor r / (1 - r)."""
        q = _toy({"married": {"kp": [YES, NO]}}, 2)
        post = update(q, uniform(q), "married", True)
        assert post.sum() == pytest.approx(1.0)
        assert post[0] / post[1] == pytest.approx(R_FACT / (1 - R_FACT))


class TestDates:
    def test_narrow_window_hit_outweighs_wide_window_hit(self):
        """A date inside a window covering ~10 % of the span is stronger evidence than one covering ~90 %."""
        q = Built(B, [0, 1], (0.0, 20000.0), {}, {"date_job": [[(6000.0, 7500.0)], [(5500.0, 18500.0)]]})
        lk = interval_likelihood(q, "date_job", 6500.0, 6501.0)
        assert lk[0] > 5 * lk[1]

    def test_window_wider_than_reliability_cannot_be_confirmed(self):
        """If a minute's windows cover more of life than r, a date inside them is LESS likely there than outside."""
        q = Built(B, [0, 1], (0.0, 20000.0), {}, {"date_job": [[(6000.0, 7500.0)], [(5500.0, 18500.0)]]})
        hit = interval_likelihood(q, "date_job", 6500.0, 6501.0)
        miss = interval_likelihood(q, "date_job", 19000.0, 19001.0)
        assert hit[0] > miss[0]          # narrow window: a hit beats a miss
        assert hit[1] < miss[1]          # ~90 % coverage > r = 0.8: a hit is weaker than a miss


class TestRealChart:
    @pytest.fixture(scope="class")
    def q(self):
        return build(B, range(-10, 11), today=(2026, 11, 2), engines=("kp",))

    def test_month_mass_rows_are_distributions(self, q):
        """Each minute's date likelihood over month bins sums to one."""
        for k, m in q.month_mass.items():
            assert m.sum(axis=1) == pytest.approx(np.ones(len(q.offsets))), k

    def test_rank_is_sorted_and_bounded(self, q):
        """Ranked questions come in decreasing bits, none above the window's total entropy."""
        r = rank(q, uniform(q))
        bits = [x.bits for x in r]
        assert bits == sorted(bits, reverse=True)
        assert max(bits) <= math.log2(len(q.offsets)) + 1e-9

    def test_resolution_classes_tile_the_window(self, q):
        """Indistinguishable-minute runs cover every candidate minute exactly once."""
        cls = resolution_classes(q, dates=False)
        assert cls[0][0] == -10 and cls[-1][1] == 10
        assert all(b[0] == a[1] + 1 for a, b in zip(cls, cls[1:]))

    def test_date_answer_list_and_credible_band(self, q):
        """Several dates for one repeatable event combine; the 90 % band is a set of runs inside the window."""
        post = update(q, uniform(q), "date_move", [[2016, 12, 7], [2018, 5, 14]])
        assert post.sum() == pytest.approx(1.0)
        band = credible(q, post, 0.9)
        assert all(-10 <= a <= z <= 10 for a, z in band)
        assert likelihood(q, "date_move", [2016, 12]).shape == (21,)


class TestSession:
    def test_round_zero_offers_distinct_questions(self):
        """With no answers the session prints a questionnaire of distinct, chart-chosen questions."""
        from tools.kp.rectify_session import batch_questions
        q = build(B, range(-5, 6), today=(2026, 11, 2), engines=("kp",))
        picks = batch_questions(q, uniform(q), 5, set())
        keys = [k for k, _ in picks]
        assert len(keys) == len(set(keys)) == 5


class TestShiftedMidnight:
    def test_shift_landing_on_midnight_rolls_the_date(self):
        """A shift whose rounded time reaches 24:00 must become 00:00 of the next day, never hour 24."""
        import swisseph as swe
        b = Birth(2000, 1, 1, 0, 0, tz=5.5, lat=28.0, lon=77.0)
        for k in range(-3000, 3000, 7):
            s = b.shifted(k + 1e-7)
            assert 0 <= s.hour <= 23
            j = swe.julday(s.year, s.month, s.day, s.hour + s.minute / 60 + s.second / 3600 - s.tz)
            assert abs(j - (b.jd_ut() + (k + 1e-7) / 1440)) < 1e-6
