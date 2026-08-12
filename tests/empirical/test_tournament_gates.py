"""The holdout freeze, the control arms, and the sham-before-real gate.

The single most important test in this file is
:meth:`TestAntiPeeking.test_real_result_refused_before_sham`. Everything else in
the tournament can be re-run; a result that was read before its gate cleared
cannot be un-read.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.empirical.tournament.controls import (
    check_era_coverage,
    check_min_n,
    check_sham_null,
    check_tier,
    era_strata,
    null_auc_se,
    sham_labels,
    sham_tolerance_for,
)
from app.empirical.tournament.holdout import (
    HOLDOUT_FRACTION,
    HoldoutError,
    HoldoutGuard,
    HoldoutReuseError,
    assign_holdout,
    build_manifest,
    check_person_leak,
    load_manifest,
    write_manifest,
)
from app.empirical.tournament.prereg import MANDATORY_CONTROL_ARMS, Registration, Status
from app.empirical.tournament.scoring import (
    GatedScorer,
    PeekError,
    apply_fdr,
    summarize,
    survivors,
)

_IDS = [f"p{i:05d}" for i in range(4000)]


def _reg(test_id: str = "T001", **overrides) -> Registration:
    base = dict(
        test_id=test_id,
        feature_bank="western",
        target="marriage",
        statistic="auc",
        baseline_model="chartless_v1",
        control_arms=tuple(sorted(MANDATORY_CONTROL_ARMS)),
        min_n=100,
        tier_requirement="A",
        stage="screening",
        direction="greater",
        status=Status.LOCKED,
    )
    base.update(overrides)
    return Registration(**base)


class TestHoldoutAssignment:
    """Deterministic, person-level, and unrerollable."""

    def test_assignment_is_deterministic(self):
        """The same ids and salt must always give the same holdout."""
        assert assign_holdout(_IDS, salt="v1") == assign_holdout(_IDS, salt="v1")

    def test_assignment_is_stable_across_input_order(self):
        """Shuffling the population must not move anyone across the boundary."""
        shuffled = list(reversed(_IDS))
        assert assign_holdout(_IDS, salt="v1") == assign_holdout(shuffled, salt="v1")

    def test_fraction_is_approximately_honoured(self):
        """25% of 4000 persons, within sampling tolerance of the hash."""
        holdout = assign_holdout(_IDS, salt="v1")
        assert 0.22 < len(holdout) / len(_IDS) < 0.28

    def test_changing_the_salt_rerolls_the_split(self):
        """A new salt is a new split — which is why it is a re-registration."""
        assert assign_holdout(_IDS, salt="v1") != assign_holdout(_IDS, salt="v2")

    def test_adding_persons_does_not_move_existing_ones(self):
        """Corpus growth must not reshuffle who was already frozen.

        Otherwise a person could migrate from holdout to train between runs,
        leaking the holdout into training one row at a time.
        """
        first = assign_holdout(_IDS[:2000], salt="v1")
        grown = assign_holdout(_IDS, salt="v1")
        assert first == {pid for pid in grown if pid in set(_IDS[:2000])}

    def test_empty_salt_rejected(self):
        """An unsalted split is not reproducible by intent."""
        with pytest.raises(ValueError, match="salt"):
            assign_holdout(_IDS, salt="")

    def test_out_of_range_fraction_rejected(self):
        """A fraction of 0 or 1 is not a split."""
        with pytest.raises(ValueError, match="fraction"):
            assign_holdout(_IDS, fraction=0.0, salt="v1")


class TestManifest:
    """The split is committed, so a changed corpus is detectable."""

    def test_manifest_round_trip(self, tmp_path):
        """Write then read returns the same commitment."""
        holdout = assign_holdout(_IDS, salt="v1")
        written = write_manifest(tmp_path / "m.json", _IDS, holdout, salt="v1")
        assert load_manifest(tmp_path / "m.json") == written

    def test_population_hash_detects_a_changed_corpus(self):
        """A manifest must not silently describe a different population."""
        holdout = assign_holdout(_IDS, salt="v1")
        a = build_manifest(_IDS, holdout, salt="v1")
        b = build_manifest(_IDS + ["p99999"], holdout, salt="v1")
        assert a.population_sha256 != b.population_sha256

    def test_default_fraction_is_the_registered_quarter(self):
        """The plan freezes 25%."""
        assert HOLDOUT_FRACTION == 0.25


class TestPersonLeak:
    """One person, one side."""

    def test_disjoint_sets_pass(self):
        """The good case is silent."""
        check_person_leak(["a", "b"], ["c", "d"])

    def test_overlap_raises_with_a_count(self):
        """The message must quantify the leak, not merely announce it."""
        with pytest.raises(HoldoutError, match="2 persons in both"):
            check_person_leak(["a", "b", "c"], ["b", "c", "d"])


class TestHoldoutGuard:
    """Touched exactly once — enforced on disk, so restarts do not reset it."""

    def test_first_claim_succeeds(self, tmp_path):
        """One read is the entitlement."""
        HoldoutGuard(tmp_path / "ledger.json").claim("T001")

    def test_second_claim_raises(self, tmp_path):
        """The second read is the one that destroys the holdout."""
        guard = HoldoutGuard(tmp_path / "ledger.json")
        guard.claim("T001")
        with pytest.raises(HoldoutReuseError, match="already read"):
            guard.claim("T001")

    def test_ledger_survives_a_new_guard_instance(self, tmp_path):
        """A fresh process must not grant a fresh read."""
        HoldoutGuard(tmp_path / "ledger.json").claim("T001")
        with pytest.raises(HoldoutReuseError):
            HoldoutGuard(tmp_path / "ledger.json").claim("T001")

    def test_different_tests_claim_independently(self, tmp_path):
        """The budget is per test, not global."""
        guard = HoldoutGuard(tmp_path / "ledger.json")
        guard.claim("T001")
        guard.claim("T002")
        assert guard.claimed() == {"T001", "T002"}


class TestControlArms:
    """Each arm corresponds to a way this corpus has already misled a round."""

    def test_sham_labels_preserve_base_rate(self):
        """Permuting, not regenerating — so a sham AUC cannot blame prevalence."""
        y = np.array([1] * 300 + [0] * 700)
        assert sham_labels(y, seed=3).sum() == y.sum()

    def test_sham_labels_are_actually_shuffled(self):
        """A no-op permutation would make the gate vacuous."""
        y = np.array([1] * 300 + [0] * 700)
        assert not np.array_equal(sham_labels(y, seed=3), y)

    def test_era_strata_are_decade_floors(self):
        """1947 with width 10 bins to 1940."""
        assert list(era_strata([1947, 1950, 1899], width=10)) == [1940, 1950, 1890]

    def test_null_auc_se_shrinks_with_sample_size(self):
        """A bigger test set justifies a tighter sham band."""
        assert null_auc_se(1000, 1000) < null_auc_se(100, 100)

    def test_sham_tolerance_tightens_with_more_permutations(self):
        """Averaging K shams buys sensitivity, not slack."""
        one = sham_tolerance_for(200, 200, n_permutations=1)
        ten = sham_tolerance_for(200, 200, n_permutations=10)
        assert ten < one
        assert ten == pytest.approx(one / np.sqrt(10))

    def test_sham_near_half_passes(self):
        """A healthy pipeline reads ~0.500 on a permuted target."""
        assert check_sham_null(0.502, tolerance=0.03).passed

    def test_sham_far_from_half_fails_with_an_explanation(self):
        """A leaking pipeline must say so in words, not just a flag."""
        outcome = check_sham_null(0.62, tolerance=0.03)
        assert not outcome.passed
        assert "uninterpretable" in outcome.detail

    def test_min_n_below_floor_fails(self):
        """Underpowered tests are excluded before they can be read."""
        assert not check_min_n(80, 100).passed

    def test_tier_violation_is_named(self):
        """The failure must identify the offending tier."""
        outcome = check_tier(["A", "B"], "A")
        assert not outcome.passed
        assert "B" in outcome.detail

    def test_self_reported_tier_allowed_only_under_abs(self):
        """Tier S is exploratory-only, per the lunarastro quarantine precedent."""
        assert not check_tier(["S"], "AB").passed
        assert check_tier(["S"], "ABS").passed

    def test_thin_era_strata_flagged(self):
        """Small strata carry the positive bias that faked Round 11's RR=1.58."""
        strata = np.array([1940] * 50 + [1950] * 3)
        outcome = check_era_coverage(strata, min_per_stratum=30)
        assert not outcome.passed
        assert "1950" in outcome.detail


class TestAntiPeeking:
    """Sham first. This ordering is the gate."""

    def test_real_result_refused_before_sham(self):
        """The load-bearing test: no real number until the sham has been read."""
        scorer = GatedScorer(_reg())
        with pytest.raises(PeekError, match="before the sham"):
            scorer.record_real(0.80, 0.74, p_value=0.01, n=1000)

    def test_real_result_refused_when_sham_failed(self):
        """A leaking pipeline's real number is not recorded at all."""
        scorer = GatedScorer(_reg(), sham_tolerance=0.03)
        scorer.record_sham(0.65)
        with pytest.raises(PeekError, match="uninterpretable"):
            scorer.record_real(0.80, 0.74, p_value=0.01, n=1000)

    def test_real_result_accepted_after_clean_sham(self):
        """The happy path still works."""
        scorer = GatedScorer(_reg(), sham_tolerance=0.03)
        scorer.record_sham(0.499)
        scorer.record_real(0.80, 0.74, p_value=0.01, n=1000)
        assert scorer.outcome().delta == pytest.approx(0.06)

    def test_sham_cannot_be_re_read(self):
        """Re-rolling the sham until it passes is the obvious circumvention."""
        scorer = GatedScorer(_reg(), sham_tolerance=0.03)
        scorer.record_sham(0.65)
        with pytest.raises(PeekError, match="already recorded"):
            scorer.record_sham(0.50)

    def test_real_cannot_be_re_recorded(self):
        """One registered test, one result."""
        scorer = GatedScorer(_reg(), sham_tolerance=0.03)
        scorer.record_sham(0.50)
        scorer.record_real(0.80, 0.74, p_value=0.01, n=1000)
        with pytest.raises(PeekError, match="already recorded"):
            scorer.record_real(0.90, 0.74, p_value=0.001, n=1000)

    def test_outcome_requires_both_halves(self):
        """An incomplete run yields no outcome rather than a partial one."""
        with pytest.raises(PeekError, match="needs both"):
            GatedScorer(_reg()).outcome()


class TestDeltaScoring:
    """A chart model's score is its delta over its own chartless twin."""

    def _outcome(self, chart, chartless, p, *, test_id="T001", n=1000, admitted=True):
        scorer = GatedScorer(_reg(test_id=test_id, min_n=1 if admitted else n + 1), sham_tolerance=0.03)
        scorer.record_sham(0.50)
        scorer.record_real(chart, chartless, p_value=p, n=n)
        return scorer.outcome()

    def test_high_raw_auc_with_zero_delta_is_not_a_survivor(self):
        """AUC 0.78 that only matches the chartless twin has beaten nothing.

        This is the exact trap the chartless bar exists for: lat/lon/date alone
        reach 0.744 on marriage, so a raw 0.78 reads as impressive and means
        nothing on its own.
        """
        outcome = self._outcome(0.780, 0.779, 0.5)
        assert outcome.chart_statistic > 0.74
        assert survivors([outcome]) == ()

    def test_positive_delta_with_small_p_survives(self):
        """The genuine case clears."""
        outcome = self._outcome(0.800, 0.744, 0.001)
        assert survivors([outcome]) == (outcome,)

    def test_negative_delta_never_survives(self):
        """Doing worse than chartless is a finding, not a survivor."""
        outcome = self._outcome(0.700, 0.744, 0.001)
        assert survivors([outcome]) == ()

    def test_unadmitted_tests_excluded_from_the_fdr_family(self):
        """Padding the family with failed tests would make survival easier."""
        good = self._outcome(0.80, 0.744, 0.001, test_id="T001")
        failed = self._outcome(0.90, 0.744, 0.0001, test_id="T002", n=10, admitted=False)
        flags = apply_fdr([good, failed])
        assert flags["T002"] is False

    def test_marginal_result_passes_alone(self):
        """p=0.04 on its own family of one clears q=0.10."""
        alone = self._outcome(0.80, 0.744, 0.04, test_id="T000")
        assert survivors([alone]) == (alone,)

    def test_same_marginal_result_fails_inside_a_family_of_nulls(self):
        """The multiplicity correction, demonstrated.

        The identical p=0.04 that survives alone is rejected once it sits in a
        family of twenty, because BH requires the smallest p to clear q/m.
        Registering twenty tests and reporting the best one is exactly the
        garden of forking paths this corrects.
        """
        marginal = self._outcome(0.80, 0.744, 0.04, test_id="T000")
        nulls = [self._outcome(0.75, 0.744, 0.9, test_id=f"T{i:03d}") for i in range(1, 20)]
        assert survivors([marginal, *nulls]) == ()

    def test_a_strong_result_still_survives_the_family(self):
        """Correction must not be so blunt that nothing can ever pass."""
        strong = self._outcome(0.85, 0.744, 0.0001, test_id="T000")
        nulls = [self._outcome(0.75, 0.744, 0.9, test_id=f"T{i:03d}") for i in range(1, 20)]
        assert survivors([strong, *nulls]) == (strong,)


class TestSummary:
    """The honest empty state is a designed result, not an error."""

    def test_null_verdict_is_explicit(self):
        """No survivors must read as a measured null, with the wording to match."""
        scorer = GatedScorer(_reg(), sham_tolerance=0.03)
        scorer.record_sham(0.50)
        scorer.record_real(0.70, 0.744, p_value=0.9, n=1000)
        report = summarize([scorer.outcome()])
        assert report["n_survivors"] == 0
        assert report["verdict"].startswith("NULL")

    def test_summary_lists_what_failed_and_why(self):
        """A null must disclose what was tested and which arms it failed."""
        scorer = GatedScorer(_reg(min_n=5000), sham_tolerance=0.03)
        scorer.record_sham(0.50)
        scorer.record_real(0.80, 0.744, p_value=0.001, n=1000)
        report = summarize([scorer.outcome()])
        assert report["not_admitted"][0]["test_id"] == "T001"

    def test_empty_family_summarizes_without_error(self):
        """Zero registered tests is a legal, reportable state."""
        assert summarize([])["n_survivors"] == 0
