"""Synthetic corpora for validating the machinery before it touches real data.

The plan's requirement is two-sided, and both sides are tests: the pipeline
**must recover a planted signal** and **must return null on noise**. A harness
that only proves the first is a harness that will report signal on anything; one
that only proves the second is indistinguishable from a harness that is broken.

The generator deliberately mimics the corpus's actual failure mode. Chartless
demographic features (birth era, geography) carry *real* predictive power on
their own — that is why the standing bar is AUC 0.744 rather than 0.500. Chart
features are pure noise unless ``planted_effect`` is non-zero. So a pipeline that
naively reports the chart model's raw AUC looks impressive on a null corpus, and
only the delta over the chartless twin exposes it.

Usage:
    from app.empirical.tournament.synthetic import make_corpus, run_test
    corpus = make_corpus(n_persons=1500, planted_effect=0.0, seed=7)   # null corpus
    outcome = run_test(registration, corpus, seed=7)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from app.empirical.tournament.controls import (
    check_chartless_baseline_arm,
    check_era_coverage,
    check_min_n,
    check_person_leak_arm,
    check_tier,
    era_strata,
    sham_labels,
    sham_tolerance_for,
)
from app.empirical.tournament.holdout import assign_holdout, check_person_leak
from app.empirical.tournament.prereg import Registration
from app.empirical.tournament.scoring import GatedScorer, TestOutcome

logger = logging.getLogger(__name__)

__all__ = [
    "SyntheticCorpus",
    "make_corpus",
    "fit_auc",
    "bootstrap_delta_p",
    "run_test",
]

_N_BOOTSTRAP: Final[int] = 200


@dataclass(frozen=True, slots=True)
class SyntheticCorpus:
    """A generated corpus plus the column roles the harness needs.

    Attributes:
      frame: One row per person.
      chart_features: Columns belonging to the chart feature bank.
      chartless_features: The demographic twin's columns.
      person_col, target_col, tier_col, year_col: Role columns.
      planted_effect: What was planted, so a test can assert against the truth.
    """

    frame: pd.DataFrame
    chart_features: tuple[str, ...]
    chartless_features: tuple[str, ...]
    person_col: str
    target_col: str
    tier_col: str
    year_col: str
    planted_effect: float


def make_corpus(
    n_persons: int = 1500,
    *,
    planted_effect: float = 0.0,
    n_chart_features: int = 8,
    seed: int = 7,
    tier: str = "A",
) -> SyntheticCorpus:
    """Generate a corpus with a known ground truth.

    Args:
      n_persons: Rows (one per person).
      planted_effect: Log-odds weight on one chart feature. ``0.0`` gives a corpus
        where the chart bank is pure noise; a positive value plants a real,
        chart-attributable signal for the machinery to find.
      n_chart_features: How many chart columns to generate.
      seed: RNG seed.
      tier: Birth-time tier stamped on every person.

    Returns:
      A :class:`SyntheticCorpus`.
    """
    if n_persons < 100:
        raise ValueError(f"n_persons must be at least 100, got {n_persons}")
    rng = np.random.default_rng(seed)

    # Demographics that genuinely predict — the chartless bar.
    birth_year = rng.integers(1900, 1990, size=n_persons)
    geo_lat = rng.uniform(-55.0, 65.0, size=n_persons)
    era_z = (birth_year - birth_year.mean()) / birth_year.std()
    geo_z = (geo_lat - geo_lat.mean()) / geo_lat.std()
    demographic_logit = 0.9 * era_z + 0.6 * geo_z

    # Chart features: noise by construction.
    chart = rng.standard_normal((n_persons, n_chart_features))
    chart_cols = tuple(f"chart_f{i}" for i in range(n_chart_features))

    # The plant, if any, rides on the first chart column only.
    planted_logit = planted_effect * chart[:, 0] if planted_effect else np.zeros(n_persons)

    logit = demographic_logit + planted_logit
    probability = 1.0 / (1.0 + np.exp(-logit))
    label = (rng.uniform(size=n_persons) < probability).astype(int)

    frame = pd.DataFrame(
        {
            "person_id": [f"p{i:06d}" for i in range(n_persons)],
            "birth_year": birth_year,
            "geo_lat": geo_lat,
            "tier": tier,
            "label": label,
        }
    )
    for i, col in enumerate(chart_cols):
        frame[col] = chart[:, i]

    logger.info(
        "synthetic corpus: n=%d, base_rate=%.3f, planted_effect=%.2f",
        n_persons,
        label.mean(),
        planted_effect,
    )
    return SyntheticCorpus(
        frame=frame,
        chart_features=chart_cols,
        chartless_features=("birth_year", "geo_lat"),
        person_col="person_id",
        target_col="label",
        tier_col="tier",
        year_col="birth_year",
        planted_effect=planted_effect,
    )


def fit_auc(
    frame: pd.DataFrame,
    feature_cols: Sequence[str],
    target_col: str,
    train_mask: np.ndarray,
    *,
    seed: int = 0,
    target_override: np.ndarray | None = None,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Fit on the train mask, score on its complement.

    Args:
      target_override: Use these labels instead of the frame's — how the sham arm
        reuses the identical pipeline on a permuted target.

    Returns:
      ``(auc, y_test, scores_test)``. The latter two are returned so the caller
      can bootstrap the delta without refitting.
    """
    y = np.asarray(frame[target_col]) if target_override is None else np.asarray(target_override)
    features = frame[list(feature_cols)].to_numpy(dtype=float)
    test_mask = ~train_mask

    y_train = y[train_mask]
    if len(np.unique(y_train)) < 2 or len(np.unique(y[test_mask])) < 2:
        # Degenerate split: no discriminable outcome. 0.5 is the honest answer.
        return 0.5, y[test_mask], np.zeros(test_mask.sum())

    model = LogisticRegression(max_iter=1000, random_state=seed)
    model.fit(features[train_mask], y_train)
    scores = model.predict_proba(features[test_mask])[:, 1]
    return float(roc_auc_score(y[test_mask], scores)), y[test_mask], scores


def bootstrap_delta_p(
    y_test: np.ndarray,
    chart_scores: np.ndarray,
    chartless_scores: np.ndarray,
    *,
    n_boot: int = _N_BOOTSTRAP,
    seed: int = 11,
) -> float:
    """One-sided p for ``AUC(chart) - AUC(chartless) > 0``, by paired bootstrap.

    Resamples test rows (the same rows for both models, so the comparison stays
    paired) and reports the share of resamples where the delta failed to be
    positive. The ``+1`` correction keeps the p-value away from an impossible
    exact zero.
    """
    rng = np.random.default_rng(seed)
    n = len(y_test)
    if n == 0 or len(np.unique(y_test)) < 2:
        return 1.0
    failures = 0
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        y_b = y_test[idx]
        if len(np.unique(y_b)) < 2:
            failures += 1
            continue
        delta_b = roc_auc_score(y_b, chart_scores[idx]) - roc_auc_score(y_b, chartless_scores[idx])
        if delta_b <= 0.0:
            failures += 1
    return (1.0 + failures) / (1.0 + n_boot)


def run_test(
    registration: Registration,
    corpus: SyntheticCorpus,
    *,
    seed: int = 7,
    salt: str = "synthetic-v1",
    n_sham: int = 10,
) -> TestOutcome:
    """Run one registered test end to end through the real gates.

    This is the harness the machinery-validation tests drive. It uses the same
    :class:`~app.empirical.tournament.scoring.GatedScorer`, the same holdout
    assignment, and the same control arms that a real run would, so a bug in the
    protocol shows up here rather than on the corpus.

    Order is load-bearing: controls, then sham, then real. The scorer refuses any
    other order.
    """
    frame = corpus.frame
    person_ids = frame[corpus.person_col].tolist()
    holdout = assign_holdout(person_ids, salt=salt)
    train_mask = np.array([pid not in holdout for pid in person_ids])

    train_ids = [p for p, keep in zip(person_ids, train_mask) if keep]
    test_ids = [p for p, keep in zip(person_ids, train_mask) if not keep]
    check_person_leak(train_ids, test_ids)

    # n is the number of rows the statistic was actually computed on, which is
    # the evaluation split — NOT the corpus size. Using len(frame) here would
    # overstate the evidence fourfold under a 25% holdout and let an
    # underpowered result clear its registered min_n.
    n_scored = int((~train_mask).sum())

    all_features = list(corpus.chartless_features) + list(corpus.chart_features)

    # Sham first — the gate. Same features, same split, permuted target.
    # Averaged over several permutations: a single sham on a few-hundred-row test
    # set has a null SE near 0.03, so one draw cannot distinguish a broken
    # pipeline from ordinary noise. The tolerance is derived from that same SE.
    y_test_true = np.asarray(frame[corpus.target_col])[~train_mask]
    n_pos = int((y_test_true == 1).sum())
    n_neg = int((y_test_true == 0).sum())
    tolerance = sham_tolerance_for(n_pos, n_neg, n_permutations=n_sham)

    sham_aucs = [
        fit_auc(
            frame,
            all_features,
            corpus.target_col,
            train_mask,
            seed=seed,
            target_override=sham_labels(frame[corpus.target_col], seed=seed + 101 + k),
        )[0]
        for k in range(n_sham)
    ]
    sham_auc = float(np.mean(sham_aucs))

    scorer = GatedScorer(registration, sham_tolerance=tolerance)
    scorer.record_controls(
        [
            check_min_n(n_scored, registration.min_n),
            check_tier(frame[corpus.tier_col], registration.tier_requirement),
            check_era_coverage(era_strata(frame[corpus.year_col])),
            check_person_leak_arm(train_ids, test_ids),
        ]
    )
    sham_outcome = scorer.record_sham(sham_auc)
    if not sham_outcome.passed:
        # Leave the real result unread. This is the protocol working.
        raise RuntimeError(f"{registration.test_id}: {sham_outcome.detail}")

    chart_auc, y_test, chart_scores = fit_auc(
        frame, all_features, corpus.target_col, train_mask, seed=seed
    )
    chartless_auc, _, chartless_scores = fit_auc(
        frame, corpus.chartless_features, corpus.target_col, train_mask, seed=seed
    )
    p_value = bootstrap_delta_p(y_test, chart_scores, chartless_scores, seed=seed + 7)

    scorer.record_controls([check_chartless_baseline_arm(chart_auc, chartless_auc)])
    scorer.record_real(chart_auc, chartless_auc, p_value=p_value, n=n_scored)
    return scorer.outcome()
