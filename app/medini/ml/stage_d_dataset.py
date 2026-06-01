"""Fork-A Stage D — PyTorch Dataset for Dynamic-DeepHit training.

Discretizes window durations into K=50 log-spaced bins from 1 day to
100 years. Each row produces (features_vector, time_bin, event_class)
where event_class=0 means censored, 1..30 indexes QUALIFYING_EVENT_CLASSES.

When multiple events fire in a window (rare per pre-flight diagnostic),
the corpus's `event_jd_<class>` columns are used to pick the earliest.
When those JD columns are absent (current dasha_mdadpd_corpus.parquet),
the first qualifying class in QUALIFYING_EVENT_CLASSES enumeration order
wins (deterministic; spec-deviation #2 in the design doc).

See spec §2 and §3.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

logger = logging.getLogger(__name__)

K_BINS: int = 50  # default; overrideable via the k_bins arg below


def _bin_edges(k_bins: int) -> np.ndarray:
    """Log-spaced bin edges from 1 day to 100 years for the requested k."""
    return np.logspace(np.log10(1.0), np.log10(100 * 365.25), k_bins + 1)


def assign_time_bin(duration_days: float, k_bins: int = K_BINS) -> int:
    """Return the bin index (0..k_bins-1) for a window duration.

    `k_bins` defaults to the module-level K_BINS=50; F5 sensitivity
    callers (Task 19.5) override it.
    """
    edges = _bin_edges(k_bins)
    idx = int(np.searchsorted(edges, duration_days, side="right") - 1)
    return max(0, min(k_bins - 1, idx))


_CLASS_TO_IDX: dict[str, int] = {
    cls: i + 1  # 0 = censored
    for i, cls in enumerate(QUALIFYING_EVENT_CLASSES)
}


def _resolve_event_label(row: pd.Series) -> int:
    """Returns 0 (censored) or class index 1..K.

    When event_jd_<class> columns exist, earliest-JD wins.
    When they don't, the first qualifying class in QUALIFYING_EVENT_CLASSES
    enumeration order wins (deterministic; documented as spec-deviation #2).
    """
    earliest_jd = float("inf")
    chosen_cls = 0
    for cls in QUALIFYING_EVENT_CLASSES:
        if row.get(f"event_{cls}", 0) != 1:
            continue
        jd_col = f"event_jd_{cls}"
        if jd_col in row.index:
            jd = row[jd_col]
            if pd.isna(jd):
                jd = float("inf")
            if jd < earliest_jd:
                earliest_jd = jd
                chosen_cls = _CLASS_TO_IDX[cls]
        else:
            # No JD column → first-qualifying-class-wins.
            if chosen_cls == 0:
                chosen_cls = _CLASS_TO_IDX[cls]
    return chosen_cls


def _select_feature_columns(df: pd.DataFrame) -> list[str]:
    """Same exclusion logic as stage_d_baseline (mirrors §6 F3 deny list)."""
    from app.medini.ml.stage_d_baseline import _feature_columns
    return _feature_columns(df)


class StageDDataset(Dataset):
    """Carries features, time bins, event classes, AND raw durations.

    `durations` is a numpy array in the SAME ROW ORDER as `features`,
    `time_bins`, and `event_classes`. This lets the training loop pass
    a consistent durations vector to `lifelines.utils.concordance_index`
    without re-deriving it from the original DataFrame (which has a
    different index after the post-filter `reset_index(drop=True)`).
    """
    def __init__(self, features: torch.Tensor,
                 time_bins: torch.Tensor,
                 event_classes: torch.Tensor,
                 durations: np.ndarray) -> None:
        assert len(features) == len(time_bins) == len(event_classes) == len(durations)
        self.features = features
        self.time_bins = time_bins
        self.event_classes = event_classes
        self.durations = durations  # raw window_duration_days, same row order

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.features[idx], self.time_bins[idx], self.event_classes[idx]


def build_dataset(df: pd.DataFrame, *, name_norms,
                  k_bins: int = K_BINS) -> StageDDataset:
    """Build a Dataset restricted to the given `name_norms` (train OR test side).

    Caller MUST pass the name_norm list for ONE side of the split; this
    function asserts the dataframe rows match (F1 in spec §6).

    `k_bins` MUST match the StageDModel's k_bins (defaults align at 50;
    F5 sensitivity callers override both consistently).
    """
    name_norms = set(name_norms)
    sub = df[df["name_norm"].isin(name_norms)].reset_index(drop=True)
    assert set(sub["name_norm"]).issubset(name_norms), "person leak"
    if len(sub) == 0:
        raise ValueError("empty dataset")

    feat_cols = _select_feature_columns(sub)
    features = torch.tensor(sub[feat_cols].fillna(0.0).to_numpy(np.float32))
    durations = sub["window_duration_days"].to_numpy()
    time_bins = torch.tensor(
        [assign_time_bin(d, k_bins=k_bins) for d in durations],
        dtype=torch.long,
    )
    event_classes = torch.tensor(
        [_resolve_event_label(row) for _, row in sub.iterrows()],
        dtype=torch.long,
    )
    return StageDDataset(features, time_bins, event_classes, durations)
