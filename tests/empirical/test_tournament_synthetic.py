"""Machinery validation — the two-sided requirement.

The pipeline must **recover a planted signal** and **return null on noise**, and
both are tests. A harness proving only the first will report signal on anything;
one proving only the second is indistinguishable from a harness that is simply
broken.

Both directions are checked across several seeds, because a single seed proves
nothing about a stochastic pipeline — that lesson is the whole content of the
K=20 → K=100 collapse in ``round11_combined_k100/K100_VERDICT.md``, where a
z=1.07 "hint" turned out to be sampling-fortunate and settled at z=0.55.
"""

from __future__ import annotations

import pytest

from app.empirical.tournament.prereg import MANDATORY_CONTROL_ARMS, Registration, Status
from app.empirical.tournament.scoring import survivors
from app.empirical.tournament.synthetic import make_corpus, run_test

_SEEDS = (7, 21, 99)


def _reg(test_id: str = "T001") -> Registration:
    return Registration(
        test_id=test_id,
        feature_bank="western",
        target="marriage",
        statistic="auc",
        baseline_model="chartless_v1",
        control_arms=tuple(sorted(MANDATORY_CONTROL_ARMS)),
        min_n=500,
        tier_requirement="A",
        stage="screening",
        direction="greater",
        status=Status.LOCKED,
    )


class TestNullRecovery:
    """On a corpus where the chart bank is pure noise, the answer must be null."""

    @pytest.mark.parametrize("seed", _SEEDS)
    def test_null_corpus_yields_no_survivor(self, seed: int):
        """No planted effect, no survivor — at every seed."""
        corpus = make_corpus(n_persons=1500, planted_effect=0.0, seed=seed)
        outcome = run_test(_reg(), corpus, seed=seed)
        assert survivors([outcome]) == ()

    @pytest.mark.parametrize("seed", _SEEDS)
    def test_null_corpus_delta_is_near_zero(self, seed: int):
        """The chart bank adds nothing over its chartless twin."""
        corpus = make_corpus(n_persons=1500, planted_effect=0.0, seed=seed)
        outcome = run_test(_reg(), corpus, seed=seed)
        assert abs(outcome.delta) < 0.03, f"null corpus delta {outcome.delta:+.4f}"

    @pytest.mark.parametrize("seed", _SEEDS)
    def test_null_corpus_raw_auc_still_looks_impressive(self, seed: int):
        """The trap, demonstrated: a meaningless model still reads ~0.77 raw.

        This is why the chartless twin is mandatory rather than advisory. Anyone
        reporting the chart model's raw AUC on this corpus would announce a
        strong result from pure noise.
        """
        corpus = make_corpus(n_persons=1500, planted_effect=0.0, seed=seed)
        outcome = run_test(_reg(), corpus, seed=seed)
        assert outcome.chart_statistic > 0.70
        assert survivors([outcome]) == ()


class TestSignalRecovery:
    """A planted signal must be found, or the machinery is blind."""

    @pytest.mark.parametrize("seed", _SEEDS)
    def test_planted_signal_survives(self, seed: int):
        """A real chart-attributable effect clears every gate."""
        corpus = make_corpus(n_persons=1500, planted_effect=1.2, seed=seed)
        outcome = run_test(_reg(), corpus, seed=seed)
        assert survivors([outcome]) == (outcome,)

    @pytest.mark.parametrize("seed", _SEEDS)
    def test_planted_signal_shows_a_positive_delta(self, seed: int):
        """The delta, not the raw statistic, is what moves."""
        corpus = make_corpus(n_persons=1500, planted_effect=1.2, seed=seed)
        outcome = run_test(_reg(), corpus, seed=seed)
        assert outcome.delta > 0.05, f"planted delta only {outcome.delta:+.4f}"

    def test_larger_plant_gives_a_larger_delta(self):
        """The measurement is monotone in the truth it is measuring."""
        weak = run_test(_reg(), make_corpus(n_persons=1500, planted_effect=0.6, seed=7), seed=7)
        strong = run_test(_reg(), make_corpus(n_persons=1500, planted_effect=1.6, seed=7), seed=7)
        assert strong.delta > weak.delta


class TestShamBehaviour:
    """The gate itself must read null on both corpora."""

    @pytest.mark.parametrize("planted", (0.0, 1.2))
    def test_sham_reads_null_regardless_of_planted_signal(self, planted: float):
        """A permuted target carries no signal even when the real one does.

        If the sham moved with the plant, the gate would be measuring the
        pipeline's capacity to overfit rather than its integrity.
        """
        corpus = make_corpus(n_persons=1500, planted_effect=planted, seed=7)
        outcome = run_test(_reg(), corpus, seed=7)
        assert abs(outcome.sham_statistic - 0.5) < 0.05


class TestProtocolIntegration:
    """The end-to-end harness must actually exercise the gates."""

    def test_all_control_arms_are_reported(self):
        """Every declared arm produces an outcome, not just the ones that fail."""
        corpus = make_corpus(n_persons=1500, planted_effect=0.0, seed=7)
        outcome = run_test(_reg(), corpus, seed=7)
        assert {"sham_target", "min_n", "tier_requirement", "era_stratification"} <= {
            a.name for a in outcome.arms
        }

    def test_underpowered_test_is_not_admitted(self):
        """A registered floor of 5000 excludes a 1500-person corpus."""
        import dataclasses

        corpus = make_corpus(n_persons=1500, planted_effect=1.2, seed=7)
        outcome = run_test(dataclasses.replace(_reg(), min_n=5000), corpus, seed=7)
        assert not outcome.admitted
        assert survivors([outcome]) == ()

    def test_holdout_is_person_disjoint(self):
        """The harness would raise on a leak; reaching an outcome proves it did not."""
        corpus = make_corpus(n_persons=1500, planted_effect=0.0, seed=7)
        assert run_test(_reg(), corpus, seed=7).n == 1500
