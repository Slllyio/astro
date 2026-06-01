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
    "md_lord", "ad_lord", "pd_lord",          # v1: replaced by ordinal versions
    "md_lord_at_event", "ad_lord_at_event",   # v2: replaced by one-hot columns
    "event_class",                             # v2: label, not feature
    "person_id",                               # v2: identity column
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
    """Replace md/ad/pd_lord with ordinal-encoded versions for lifelines.

    Silently skips any column in _CATEGORICAL_COLS that is absent from
    ``df`` (e.g., the v2 dataset uses ``md_lord_at_event`` / ``ad_lord_at_event``
    which are already one-hot encoded; the original string columns are absent).
    """
    from app.medini.ml.stage_d_features import _DASHA_LORDS
    lord_to_int = {l: i for i, l in enumerate(_DASHA_LORDS)}
    out = df.copy()
    for col in _CATEGORICAL_COLS:
        if col not in out.columns:
            continue
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
    # fillna(0.0) handles censored persons whose dasha timing features are NaN
    # (v2 dataset: censored persons have no active dasha at event time).
    cph_input_train[features] = cph_input_train[features].fillna(0.0)
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
    # fillna(0.0) mirrors the training-set treatment for censored persons
    # whose dasha timing features are NaN (v2 dataset).
    risk = cph.predict_partial_hazard(test[features].fillna(0.0))
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


# Module-level globals populated per-worker by `_init_worker_data` (via
# ProcessPoolExecutor's `initializer` argument). Keeping them at module
# scope means each worker only deserializes the (train, test) DataFrames
# ONCE rather than 30 times (was ~30s × 30 wasted on Windows pickling).
_WORKER_TRAIN: pd.DataFrame | None = None
_WORKER_TEST: pd.DataFrame | None = None


def _init_worker_data(train_pickle: bytes, test_pickle: bytes) -> None:
    """ProcessPool initializer — ships (train, test) to each worker ONCE.

    Both args are pre-pickled bytes (not DataFrames) so the initializer
    payload is the wire-format we want, not a deepcopied object that
    multiprocessing would re-pickle anyway.

    Used by the small-payload path (<~1.5 GB pickle total). Larger payloads
    use `_init_worker_data_from_paths` because Windows pipes can't carry
    pickled data >2^31 bytes through a single WriteFile.
    """
    import pickle
    global _WORKER_TRAIN, _WORKER_TEST
    _WORKER_TRAIN = pickle.loads(train_pickle)
    _WORKER_TEST = pickle.loads(test_pickle)


def _init_worker_data_from_paths(train_path: str, test_path: str) -> None:
    """ProcessPool initializer — workers read (train, test) from parquet.

    Used when the in-memory pickle path would exceed the Windows 2 GB
    pipe write limit (OSError errno 22). The orchestrator writes the
    split to a temp parquet ONCE per seed; each worker reads it lazily.
    Pyarrow parquet read is ~3-5x slower than pickle.loads but bypasses
    the pipe entirely.
    """
    global _WORKER_TRAIN, _WORKER_TEST
    _WORKER_TRAIN = pd.read_parquet(train_path)
    _WORKER_TEST = pd.read_parquet(test_path)


def _fit_one_shared(args: tuple[str, int]) -> CoxFitResult:
    """ProcessPool entry point — reads (train, test) from worker globals."""
    cls, seed = args
    if _WORKER_TRAIN is None or _WORKER_TEST is None:
        raise RuntimeError(
            "_fit_one_shared called without _init_worker_data; "
            "ProcessPoolExecutor must be constructed with the initializer."
        )
    return fit_cause_specific_cox(
        _WORKER_TRAIN, _WORKER_TEST, event_class=cls, seed=seed,
    )


def _fit_one(args: tuple[pd.DataFrame, pd.DataFrame, str, int]) -> CoxFitResult:
    """Legacy entry point — kept for the sequential parity test only.

    Pickles (train, test) per call; do NOT use in the production parallel
    path (use `_fit_one_shared` via `_init_worker_data` instead).
    """
    train, test, cls, seed = args
    return fit_cause_specific_cox(train, test, event_class=cls, seed=seed)


# Windows multiprocessing pipe uses WriteFile with a 32-bit count argument,
# so initargs containing pickled bytes >= 2 GiB raise OSError(22). Trigger
# the disk-spill path well below the hard limit to leave headroom for
# overhead and tooling reads.
_PIPE_PICKLE_LIMIT_BYTES: int = 1_500_000_000


def _fit_all_classes_parallel(
    train: pd.DataFrame, test: pd.DataFrame, *, seed: int,
) -> list[CoxFitResult]:
    """ProcessPool fan-out across the 30 cause-specific Cox fits.

    Two transport modes for shipping (train, test) to workers:
    1. Pickle-in-pipe (default, small data): pre-pickle each DataFrame in
       the orchestrator and pass the bytes through initargs.
    2. Parquet-on-disk (large data): write the split to temp parquet files
       and pass the paths. Used when the combined pickle exceeds the
       Windows pipe limit (~2 GB).

    Triggered automatically by inspecting `train.memory_usage(deep=True).sum()`
    (cheap; doesn't actually pickle). At subsample scale (1.2M rows) the
    in-memory footprint is ~2.5 GB so we always take path 2.
    """
    import pickle
    import tempfile

    n_workers = max(1, (os.cpu_count() or 2) - 1)
    args_list = [(cls, seed) for cls in QUALIFYING_EVENT_CLASSES]

    # Cheap proxy for the eventual pickle size: deep memory usage is an
    # upper bound on pickle output for primitive-dtype DataFrames. Using
    # this avoids pickling twice (once to measure, once to send).
    payload_estimate = int(
        train.memory_usage(deep=True).sum() + test.memory_usage(deep=True).sum()
    )

    if payload_estimate < _PIPE_PICKLE_LIMIT_BYTES:
        train_p = pickle.dumps(train)
        test_p = pickle.dumps(test)
        with ProcessPoolExecutor(
            max_workers=n_workers,
            initializer=_init_worker_data,
            initargs=(train_p, test_p),
        ) as ex:
            return list(ex.map(_fit_one_shared, args_list))

    # Large payload: spill to temp parquet, pass paths through the pipe.
    # NamedTemporaryFile auto-cleans on context exit; workers MUST finish
    # before we leave the `with tempfile.TemporaryDirectory` block.
    #
    # Cap workers at 4 when spilling because each worker's pyarrow read
    # malloc's ~2-3x the final DataFrame size transiently. Pre-cap with
    # 7 workers OOMed (ArrowMemoryError: malloc of size 1024358592 failed).
    # 4 workers gives ~5-7 GB peak Cox-side; combined with the
    # post-DeepHit orchestrator (~3 GB after gc) this fits comfortably.
    spill_workers = min(4, n_workers)
    logger.info(
        "Cox parallel: payload ~%.2f GB exceeds pipe limit; "
        "spilling to temp parquet (workers=%d)",
        payload_estimate / 1e9,
        spill_workers,
    )
    with tempfile.TemporaryDirectory(prefix="stage_d_cox_") as td:
        train_path = os.path.join(td, "train.parquet")
        test_path = os.path.join(td, "test.parquet")
        train.to_parquet(train_path, index=False)
        test.to_parquet(test_path, index=False)
        with ProcessPoolExecutor(
            max_workers=spill_workers,
            initializer=_init_worker_data_from_paths,
            initargs=(train_path, test_path),
        ) as ex:
            return list(ex.map(_fit_one_shared, args_list))
