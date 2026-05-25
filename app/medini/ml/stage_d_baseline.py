"""Fork-A Stage D — matched-feature cause-specific Cox PH baseline.

For each qualifying event class, fit lifelines.CoxPHFitter with L1
penalty on the SAME features as Stage D. Per-class C-index is the
metric the gate compares against. 30 fits per seed; parallelized via
ProcessPoolExecutor (added in Task 9).

See docs/superpowers/specs/2026-05-24-fork-a-stage-d-design.md §4.
"""
from __future__ import annotations

import logging
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.exceptions import ConvergenceError
from lifelines.utils import concordance_index
from sklearn.model_selection import GroupShuffleSplit

from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

logger = logging.getLogger(__name__)

PENALIZER: float = 0.01  # L1; locked, no tune.
DEFAULT_TEST_SIZE: float = 0.20

_CATEGORICAL_COLS: tuple[str, ...] = ("md_lord", "ad_lord", "pd_lord")
_NON_FEATURE_PREFIXES: tuple[str, ...] = ("event_",)  # includes event_jd_*, event_*
_NON_FEATURE_EXACT: frozenset[str] = frozenset({
    "name", "name_norm", "birth_jd", "moon_longitude",
    "md_seq_idx", "ad_seq_idx", "pd_seq_idx",
    "window_start_jd", "window_end_jd",
    "window_duration_days", "window_duration_years",  # `T` is fed separately
    "n_events_in_window",
    "md_lord", "ad_lord", "pd_lord",  # replaced by ordinal versions
})


@dataclass(frozen=True, slots=True)
class CoxFitResult:
    event_class: str
    seed: int
    c_index: float
    n_train: int
    n_test: int
    n_train_positives: int
    n_test_positives: int
    converged: bool
    convergence_msg: str = ""


def _feature_columns(df: pd.DataFrame) -> list[str]:
    """Return numeric, non-label, non-id columns suitable for Cox.

    Filters to numeric dtypes (drops object/string/list columns that
    Cox can't handle): tattva_*, dispositor_*, panchanga_paksha,
    final_dispositor (string categoricals — could one-hot in future)
    and rules_*/aspects_* (list-typed Stage-E cols — see Task 5 TODO
    for an encoding strategy).
    """
    numeric_dtypes = ("int8", "int16", "int32", "int64",
                      "uint8", "uint16", "uint32", "uint64",
                      "float16", "float32", "float64", "bool")
    return [
        c for c in df.columns
        if c not in _NON_FEATURE_EXACT
        and not any(c.startswith(p) for p in _NON_FEATURE_PREFIXES)
        and str(df[c].dtype) in numeric_dtypes
    ]


def _ordinal_encode_lords(df: pd.DataFrame) -> pd.DataFrame:
    """Replace md/ad/pd_lord with ordinal-encoded versions for lifelines."""
    from app.medini.ml.stage_d_features import _DASHA_LORDS
    lord_to_int = {l: i for i, l in enumerate(_DASHA_LORDS)}
    out = df.copy()
    for col in _CATEGORICAL_COLS:
        out[f"{col}_ord"] = out[col].map(lord_to_int).astype("int8")
    return out


def split_train_test(df: pd.DataFrame, *, seed: int,
                     test_size: float = DEFAULT_TEST_SIZE
                     ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Single source of truth for the per-seed split. Use this from BOTH
    stage_d_train._train_one_seed (DeepHit side) and fit_all_classes
    (Cox side) so the gate's delta is computed on identical splits."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(splitter.split(df, groups=df["name_norm"]))
    return (
        df.iloc[train_idx].reset_index(drop=True),
        df.iloc[test_idx].reset_index(drop=True),
    )


def fit_cause_specific_cox(
    train: pd.DataFrame,
    test: pd.DataFrame,
    *,
    event_class: str,
    seed: int,
) -> CoxFitResult:
    """Fit one cause-specific Cox PH model for `event_class` using a
    pre-split train/test pair. Other 29 classes are treated as censoring.
    """
    train = _ordinal_encode_lords(train)
    test = _ordinal_encode_lords(test)
    event_col = f"event_{event_class}"
    if event_col not in train.columns:
        raise ValueError(f"missing label column {event_col}")
    assert set(train["name_norm"]).isdisjoint(set(test["name_norm"])), "person leak"

    features = _feature_columns(train)

    # Drop zero-variance columns: lifelines normalises X by std internally;
    # std==0 produces NaN deltas and immediate ConvergenceError.
    # Use the training set variance only (no leakage from test).
    feat_var = train[features].var()
    features = [c for c in features if feat_var[c] > 0]
    logger.debug("Cox features after var-filter: %d", len(features))

    cph_input_train = train[features + ["window_duration_days", event_col]].copy()
    cph_input_train.rename(
        columns={"window_duration_days": "T", event_col: "E"}, inplace=True,
    )

    cph = CoxPHFitter(penalizer=PENALIZER, l1_ratio=1.0)
    try:
        cph.fit(cph_input_train, duration_col="T", event_col="E", show_progress=False)
    except ConvergenceError as e:
        logger.warning("Cox failed for class=%s seed=%d: %s", event_class, seed, e)
        return CoxFitResult(
            event_class=event_class, seed=seed,
            c_index=float("nan"),
            n_train=len(train), n_test=len(test),
            n_train_positives=int(train[event_col].sum()),
            n_test_positives=int(test[event_col].sum()),
            converged=False, convergence_msg=str(e),
        )

    # Risk score = predicted partial hazard. Pass `-risk` so high risk =>
    # earlier event (lifelines concordance_index convention).
    risk = cph.predict_partial_hazard(test[features])
    try:
        c = concordance_index(test["window_duration_days"], -risk, test[event_col])
    except ZeroDivisionError:
        # No admissible pairs: zero positives in test split for this class.
        logger.warning(
            "Cox concordance undefined for class=%s seed=%d (no test positives)",
            event_class, seed,
        )
        return CoxFitResult(
            event_class=event_class, seed=seed,
            c_index=float("nan"),
            n_train=len(train), n_test=len(test),
            n_train_positives=int(train[event_col].sum()),
            n_test_positives=int(test[event_col].sum()),
            converged=True, convergence_msg="no_test_positives",
        )

    return CoxFitResult(
        event_class=event_class, seed=seed,
        c_index=float(c),
        n_train=len(train), n_test=len(test),
        n_train_positives=int(train[event_col].sum()),
        n_test_positives=int(test[event_col].sum()),
        converged=True,
    )


def fit_all_classes(
    train: pd.DataFrame,
    test: pd.DataFrame,
    *,
    seed: int,
    parallel: bool = True,
) -> list[CoxFitResult]:
    """Fit 30 cause-specific Cox PH models, one per qualifying class.

    Train/test split MUST be the same one passed to the DeepHit model
    in stage_d_train._train_one_seed for the gate's Δ to be valid.

    `parallel=True` uses ProcessPoolExecutor (default; ~Nx faster on
    multi-core). `parallel=False` runs the 30 fits sequentially — useful
    for debugging when a single class fails and you need a clean stack
    trace.
    """
    if parallel:
        return _fit_all_classes_parallel(train, test, seed=seed)
    return [
        fit_cause_specific_cox(train, test, event_class=cls, seed=seed)
        for cls in QUALIFYING_EVENT_CLASSES
    ]


def _fit_one(args: tuple[pd.DataFrame, pd.DataFrame, str, int]) -> CoxFitResult:
    """ProcessPoolExecutor entry point — must be top-level for pickling."""
    train, test, cls, seed = args
    return fit_cause_specific_cox(train, test, event_class=cls, seed=seed)


def _fit_all_classes_parallel(
    train: pd.DataFrame, test: pd.DataFrame, *, seed: int,
) -> list[CoxFitResult]:
    """ProcessPool fan-out across the 30 cause-specific Cox fits.

    NOTE: pickling the (train, test) DataFrames per task is wasteful on
    Windows (no fork). Expected wall-clock: ~8-15 min per seed at smoke
    size (60K × ~250 cols) on 8 cores. For seed-level runs at scale, an
    initializer-based pattern (`ProcessPoolExecutor(initializer=...)`)
    would ship the data once per worker — defer that optimization until
    Task 18's noise-floor measurement times out.
    """
    n_workers = max(1, (os.cpu_count() or 2) - 1)
    args_list = [(train, test, cls, seed) for cls in QUALIFYING_EVENT_CLASSES]
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        results = list(ex.map(_fit_one, args_list))
    return results
