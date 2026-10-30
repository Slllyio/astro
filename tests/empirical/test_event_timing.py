"""The within-person event-timing design.

The tests here pin the properties that make the design worth trusting: controls
come from the same person, they never sit adjacent to the real event, and the
statistic is exactly 0.5 for a model with no information.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.empirical.tournament.run_event_timing import (
    CandidateSet,
    _EXCLUSION_DAYS,
    _MIN_AGE,
    _N_CONTROLS,
    _within_person_auc,
    build_candidates,
)

_YEAR = 365.25


def _corpus(n: int = 50, lifespan_years: float = 70.0) -> dict[str, tuple[float, float]]:
    """n people, all born at JD 2400000, dying after `lifespan_years`."""
    return {f"p{i}": (2400000.0, 2400000.0 + lifespan_years * _YEAR) for i in range(n)}


class TestCandidateConstruction:
    """Each person supplies their own counterfactuals."""

    def test_every_person_gets_the_declared_control_count(self):
        """A short control set would quietly weaken the comparison."""
        for candidate in build_candidates(_corpus(), sample=0):
            assert len(candidate.control_jds) == _N_CONTROLS

    def test_controls_never_land_near_the_real_event(self):
        """A control a week before death is a near-duplicate, not a counterfactual."""
        for candidate in build_candidates(_corpus(), sample=0):
            for control in candidate.control_jds:
                assert abs(control - candidate.true_jd) >= _EXCLUSION_DAYS

    def test_controls_fall_within_the_persons_own_adult_life(self):
        """Out-of-window controls would reintroduce the age confound by the back door."""
        for candidate in build_candidates(_corpus(), sample=0):
            window_start = candidate.natal_jd + _MIN_AGE * _YEAR
            for control in candidate.control_jds:
                assert window_start <= control <= candidate.true_jd

    def test_short_lives_are_dropped_not_squeezed(self):
        """Someone dying at 21 has no room for distinct controls."""
        assert build_candidates(_corpus(lifespan_years=20.5), sample=0) == []

    def test_sampling_is_deterministic(self):
        """The same seed must select the same people, or runs are not comparable."""
        a = build_candidates(_corpus(200), sample=20, seed=3)
        b = build_candidates(_corpus(200), sample=20, seed=3)
        assert [c.person_id for c in a] == [c.person_id for c in b]

    def test_sample_limits_the_person_count(self):
        """The sample argument must actually bound the work."""
        assert len(build_candidates(_corpus(200), sample=20, seed=3)) <= 20


class TestWithinPersonAUC:
    """The statistic: does the real date outrank that person's own controls?"""

    def test_uninformative_scores_give_exactly_half(self):
        """Constant scores are all ties, and ties count as half."""
        scores = np.ones(10)
        labels = np.array([1, 0, 0, 0, 0] * 2)
        persons = np.array([0] * 5 + [1] * 5)
        assert _within_person_auc(scores, labels, persons) == pytest.approx(0.5)

    def test_perfect_ranking_gives_one(self):
        """The true date scoring above every control is a perfect result."""
        scores = np.array([9.0, 1.0, 2.0, 3.0, 4.0])
        labels = np.array([1, 0, 0, 0, 0])
        persons = np.zeros(5, dtype=int)
        assert _within_person_auc(scores, labels, persons) == pytest.approx(1.0)

    def test_inverted_ranking_gives_zero(self):
        """Scoring the true date below every control is the opposite of signal."""
        scores = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        labels = np.array([1, 0, 0, 0, 0])
        persons = np.zeros(5, dtype=int)
        assert _within_person_auc(scores, labels, persons) == pytest.approx(0.0)

    def test_persons_are_scored_independently(self):
        """A person who ranks well must not rescue one who ranks badly.

        Pooling across people would let a between-person effect masquerade as a
        within-person one — the exact confusion this design exists to avoid.
        """
        scores = np.array([9.0, 1.0, 0.0, 5.0])
        labels = np.array([1, 0, 1, 0])
        persons = np.array([0, 0, 1, 1])
        assert _within_person_auc(scores, labels, persons) == pytest.approx(0.5)

    def test_person_with_no_controls_is_skipped(self):
        """An unpaired row contributes nothing rather than breaking the average."""
        scores = np.array([1.0, 2.0, 3.0])
        labels = np.array([1, 1, 0])
        persons = np.array([0, 1, 1])
        assert 0.0 <= _within_person_auc(scores, labels, persons) <= 1.0


class TestDesignConstants:
    """The choices that keep the comparison honest."""

    def test_moon_is_not_a_transit_body(self):
        """Without a birth time the Moon is uncertain by ~13° and cannot be used."""
        from app.empirical.tournament.run_event_timing import _NATAL_BODIES, _TRANSIT_BODIES

        assert "Moon" not in _TRANSIT_BODIES
        assert "Moon" not in _NATAL_BODIES

    def test_controls_start_at_adulthood(self):
        """Childhood dates are far from the event in both age and sky."""
        assert _MIN_AGE >= 18.0


class TestWithinPersonSham:
    """The sham must destroy the association without destroying the design."""

    def _setup(self, n: int = 500):
        y = np.array([1, 0, 0, 0, 0] * n)
        person_index = np.repeat(np.arange(n), 5)
        return y, person_index

    def test_each_person_keeps_exactly_one_true_date(self):
        """The defining property of the design must survive the permutation.

        Found by the sham gate: a GLOBAL permutation leaves 32% of people with no
        true date and 25% with two or more, and that structural damage — not any
        pipeline leak — is what pushed the sham statistic off 0.500.
        """
        from app.empirical.tournament.run_event_timing import within_person_sham

        y, person_index = self._setup()
        shuffled = within_person_sham(y, person_index, seed=7)
        for person in np.unique(person_index):
            assert shuffled[person_index == person].sum() == 1

    def test_global_permutation_would_not_preserve_it(self):
        """Pins the bug this replaced, so it cannot quietly return."""
        from app.empirical.tournament.controls import sham_labels

        y, _ = self._setup()
        per_person = sham_labels(y, seed=7).reshape(-1, 5).sum(axis=1)
        assert not np.all(per_person == 1)

    def test_the_true_date_actually_moves(self):
        """A permutation that left every label in place would be a no-op gate."""
        from app.empirical.tournament.run_event_timing import within_person_sham

        y, person_index = self._setup()
        assert not np.array_equal(within_person_sham(y, person_index, seed=7), y)

    def test_row_count_and_total_positives_are_preserved(self):
        """Same rows, same base rate — only the assignment changes."""
        from app.empirical.tournament.run_event_timing import within_person_sham

        y, person_index = self._setup()
        shuffled = within_person_sham(y, person_index, seed=7)
        assert len(shuffled) == len(y)
        assert shuffled.sum() == y.sum()
