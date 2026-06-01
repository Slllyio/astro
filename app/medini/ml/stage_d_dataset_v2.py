"""Fork-A Stage D v2 — PyTorch Dataset with CORRECTED survival target.

Bug in v1 (stage_d_dataset.py line 130):
    durations = sub["window_duration_days"].to_numpy()
This regressed on dasha-window LENGTH (Sun MD=6yr, Venus MD=20yr), not on
time-to-event from birth. The model learned "longer windows → more events"
— a pure exposure-time confound identical to Stage B's Fisher-exact bug.

Fix in v2:
    Load events_with_dasha.parquet (one row per event, event_jd present)
    Survival duration = event_jd - birth_jd (days from birth to event)

Dataset structure:
    One row per person (first qualifying event wins for competing risks).
    Persons with no qualifying events get censored duration = max observed
    event_jd − birth_jd for that person.

Feature set:
    Chart features from charts.parquet (41 cols: planet signs, houses,
    nakshatras, longitudes, asc_lon) joined on person_id.
    Dasha features from events_with_dasha (md_lord_at_event, ad_lord_at_event,
    md_seq, ad_seq, md_elapsed_years, ad_elapsed_years, ad_duration_days).
    NOTE: age_at_event_years is deliberately EXCLUDED — it is a
    monotone transform of the survival target (event_jd − birth_jd / 365.25)
    and would constitute target leakage.

This module is a DROP-IN for stage_d_dataset in stage_d_train.py when
--dataset-v2 is passed. The StageDDataset dtype/shape contract is preserved:
    features  : FloatTensor (N, n_features)
    time_bins : LongTensor  (N,)
    event_classes: LongTensor (N,)   0=censored, 1..30=class index
    durations : np.ndarray  (N,)     raw days from birth to event/censor

Usage (via stage_d_train.py):
    py -3.12 -m app.medini.ml.stage_d_train \\
        --seed 1 --split main --dataset-v2 \\
        --out-dir data/ml_runs/fork_a_stage_d_v2_corrected_target

Building the v2 parquet:
    py -3.12 -m app.medini.ml.stage_d_dataset_v2 \\
        --out-dir app/medini/data
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from app.medini.ml.stage_d_dataset import (
    K_BINS,
    StageDDataset,
    _bin_edges,
    assign_time_bin,
    _CLASS_TO_IDX,
)
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

logger = logging.getLogger(__name__)

_DATA_DIR: Final = Path("app/medini/data")
_CATALOG_DB: Final = _DATA_DIR / "catalog.duckdb"
_V2_PARQUET: Final = _DATA_DIR / "stage_d_v2_person_level.parquet"

# Dasha lord one-hot encoding order (same as stage_d_features._DASHA_LORDS)
_DASHA_LORDS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)

# Chart numeric columns to use as features (from charts.parquet).
# Excludes person_id, birth_jd_used (= survival target), time_precision.
# Includes all 9 planets × (lon, sign, house, nakshatra) + asc_lon + asc_sign.
_CHART_FEATURE_COLS: tuple[str, ...] = (
    "asc_lon", "asc_sign",
    "sun_lon", "sun_sign", "sun_house", "sun_nakshatra",
    "moon_lon", "moon_sign", "moon_house", "moon_nakshatra",
    "mars_lon", "mars_sign", "mars_house", "mars_nakshatra",
    "mercury_lon", "mercury_sign", "mercury_house", "mercury_nakshatra",
    "jupiter_lon", "jupiter_sign", "jupiter_house", "jupiter_nakshatra",
    "venus_lon", "venus_sign", "venus_house", "venus_nakshatra",
    "saturn_lon", "saturn_sign", "saturn_house", "saturn_nakshatra",
    "rahu_lon", "rahu_sign", "rahu_house", "rahu_nakshatra",
    "ketu_lon", "ketu_sign", "ketu_house", "ketu_nakshatra",
)

# Dasha sequence features from events_with_dasha (NOT age_at_event_years
# which is a direct transform of the target duration).
_DASHA_FEATURE_COLS: tuple[str, ...] = (
    "md_seq",
    "ad_seq",
    "md_elapsed_years",
    "ad_elapsed_years",
    "ad_duration_days",
)


def _lord_one_hot_cols() -> list[str]:
    """Generate column names for the md/ad lord one-hot block."""
    cols = []
    for level in ("md", "ad"):
        for lord in _DASHA_LORDS:
            cols.append(f"{level}_lord_at_event_is_{lord.lower()}")
    return cols


def build_v2_parquet(
    catalog_path: Path = _CATALOG_DB,
    out_path: Path = _V2_PARQUET,
    *,
    seed: int = 42,
) -> pd.DataFrame:
    """Build and persist the v2 person-level survival DataFrame.

    Returns the full (pre-subsample) DataFrame. The subsample is applied at
    dataset-build time so that different seeds can draw different subsamples
    from the same base parquet.

    One row per person:
      - Event persons:   first qualifying event; duration = event_jd - birth_jd
      - Censored persons: no qualifying events;  duration = max(event_jd) - birth_jd
    """
    import duckdb

    if not catalog_path.exists():
        raise FileNotFoundError(
            f"DuckDB catalog not found at {catalog_path}. "
            "Run: py -3.12 -m app.medini.etl.build_duckdb_catalog"
        )

    qualifying_csv = ", ".join(f"'{c}'" for c in QUALIFYING_EVENT_CLASSES)

    con = duckdb.connect(str(catalog_path), read_only=True)
    try:
        # ── Event rows: first qualifying event per WD person ─────────────
        event_df = con.execute(f"""
            WITH ranked AS (
                SELECT
                    e.person_id,
                    e.event_class,
                    (e.event_jd - e.birth_jd)   AS window_duration_days,
                    e.md_lord_at_event,
                    e.ad_lord_at_event,
                    e.md_seq,
                    e.ad_seq,
                    e.md_elapsed_years,
                    e.ad_elapsed_years,
                    e.ad_duration_days,
                    ROW_NUMBER() OVER (
                        PARTITION BY e.person_id
                        ORDER BY e.event_jd
                    ) AS rn
                FROM events_with_dasha e
                WHERE e.person_id LIKE 'WD:%'
                  AND e.md_lord_at_event IS NOT NULL
                  AND e.event_jd IS NOT NULL
                  AND e.birth_jd IS NOT NULL
                  AND (e.event_jd - e.birth_jd) > 0
                  AND e.event_class IN ({qualifying_csv})
            )
            SELECT * EXCLUDE(rn) FROM ranked WHERE rn = 1
        """).df()
        logger.info("Event rows (WD, first qualifying event): %d", len(event_df))

        # ── Censored rows: WD persons with events but no qualifying ones ──
        censor_df = con.execute(f"""
            WITH wd_with_any_event AS (
                SELECT DISTINCT e.person_id, e.birth_jd
                FROM events_with_dasha e
                WHERE e.person_id LIKE 'WD:%'
                  AND e.birth_jd IS NOT NULL
            ),
            with_qualifying AS (
                SELECT DISTINCT person_id
                FROM events_with_dasha
                WHERE person_id LIKE 'WD:%'
                  AND md_lord_at_event IS NOT NULL
                  AND event_jd IS NOT NULL
                  AND (event_jd - birth_jd) > 0
                  AND event_class IN ({qualifying_csv})
            ),
            max_jd AS (
                SELECT person_id, MAX(event_jd) AS max_event_jd
                FROM events_with_dasha
                WHERE person_id LIKE 'WD:%'
                  AND event_jd IS NOT NULL
                GROUP BY person_id
            )
            SELECT
                a.person_id,
                NULL                                 AS event_class,
                (m.max_event_jd - a.birth_jd)       AS window_duration_days,
                NULL                                 AS md_lord_at_event,
                NULL                                 AS ad_lord_at_event,
                NULL                                 AS md_seq,
                NULL                                 AS ad_seq,
                NULL                                 AS md_elapsed_years,
                NULL                                 AS ad_elapsed_years,
                NULL                                 AS ad_duration_days
            FROM wd_with_any_event a
            JOIN max_jd m ON a.person_id = m.person_id
            WHERE a.person_id NOT IN (SELECT person_id FROM with_qualifying)
              AND (m.max_event_jd - a.birth_jd) > 0
        """).df()
        logger.info("Censored rows (WD, no qualifying events): %d", len(censor_df))
    finally:
        con.close()

    # ── Combine event + censored ─────────────────────────────────────────
    combined = pd.concat([event_df, censor_df], ignore_index=True)
    logger.info("Combined rows (event + censored): %d", len(combined))

    # ── Add qualifying-class event indicator columns ──────────────────────
    for cls in QUALIFYING_EVENT_CLASSES:
        combined[f"event_{cls}"] = (combined["event_class"] == cls).astype("int8")

    # ── Join chart features ───────────────────────────────────────────────
    charts = pd.read_parquet(_DATA_DIR / "charts.parquet")
    # Keep only WD persons and necessary columns
    chart_cols = ["person_id"] + list(_CHART_FEATURE_COLS)
    charts_wd = charts[charts["person_id"].str.startswith("WD:")][
        [c for c in chart_cols if c in charts.columns]
    ]
    combined = combined.merge(charts_wd, on="person_id", how="left")
    logger.info(
        "Chart join: %d / %d rows matched a chart row (%.1f%%)",
        combined["asc_sign"].notna().sum(),
        len(combined),
        100.0 * combined["asc_sign"].notna().sum() / max(1, len(combined)),
    )

    # ── Add dasha lord one-hot columns ───────────────────────────────────
    for level in ("md", "ad"):
        col = f"{level}_lord_at_event"
        for lord in _DASHA_LORDS:
            combined[f"{col}_is_{lord.lower()}"] = (
                (combined[col] == lord).astype("int8")
            )

    # ── Add name_norm (WD IDs don't map to name_norm; use person_id) ─────
    # The train loop uses name_norm for GroupShuffleSplit. We derive it
    # directly from person_id for the WD corpus so the split is person-level.
    combined["name_norm"] = combined["person_id"].str.lower().str.strip()

    # ── Persist ──────────────────────────────────────────────────────────
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(out_path, index=False)
    logger.info(
        "Wrote v2 parquet: %d rows × %d cols → %s",
        len(combined), len(combined.columns), out_path,
    )
    return combined


def _feature_columns_v2(df: pd.DataFrame) -> list[str]:
    """Return v2-specific feature columns (chart + dasha encodings).

    Explicitly excludes the survival target (window_duration_days),
    event labels (event_*), identity columns (person_id, name_norm,
    event_class), and age_at_event_years (target-leaking transform).
    """
    exclude_exact = frozenset({
        "person_id", "name_norm", "event_class",
        "window_duration_days",        # survival target — must NOT be a feature
        "md_lord_at_event",            # categorical, replaced by one-hots below
        "ad_lord_at_event",
    })
    exclude_prefixes = ("event_",)     # event_{cls} are labels, not features

    numeric_dtypes = (
        "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64",
        "float16", "float32", "float64", "bool",
    )
    return [
        c for c in df.columns
        if c not in exclude_exact
        and not any(c.startswith(p) for p in exclude_prefixes)
        and str(df[c].dtype) in numeric_dtypes
    ]


def build_dataset_v2(
    df: pd.DataFrame,
    *,
    name_norms: set[str] | list[str],
    k_bins: int = K_BINS,
) -> StageDDataset:
    """Build a StageDDataset from the v2 person-level DataFrame.

    Shape contract identical to stage_d_dataset.build_dataset():
        StageDDataset.features     : FloatTensor (N, n_features)
        StageDDataset.time_bins    : LongTensor  (N,)
        StageDDataset.event_classes: LongTensor  (N,)
        StageDDataset.durations    : np.ndarray  (N,)  ← corrected target

    `durations` is now (event_jd − birth_jd) in days, NOT window_duration_days.
    """
    name_norms = set(name_norms)
    sub = df[df["name_norm"].isin(name_norms)].reset_index(drop=True)
    assert set(sub["name_norm"]).issubset(name_norms), "person leak"
    if len(sub) == 0:
        raise ValueError("empty v2 dataset subset")

    feat_cols = _feature_columns_v2(sub)
    if not feat_cols:
        raise ValueError("No numeric feature columns found in v2 DataFrame")

    features = torch.tensor(
        sub[feat_cols].fillna(0.0).to_numpy(np.float32),
        dtype=torch.float32,
    )

    # Corrected survival target: event_jd − birth_jd (already in
    # window_duration_days for the v2 parquet after build_v2_parquet())
    durations = sub["window_duration_days"].to_numpy(dtype=np.float64)

    time_bins = torch.tensor(
        [assign_time_bin(d, k_bins=k_bins) for d in durations],
        dtype=torch.long,
    )

    # Event class index: 0 = censored, 1..N_CLASSES = qualifying class index
    event_classes_list = []
    for _, row in sub.iterrows():
        cls_idx = 0
        for cls in QUALIFYING_EVENT_CLASSES:
            if row.get(f"event_{cls}", 0) == 1:
                cls_idx = _CLASS_TO_IDX[cls]
                break
        event_classes_list.append(cls_idx)
    event_classes = torch.tensor(event_classes_list, dtype=torch.long)

    return StageDDataset(features, time_bins, event_classes, durations)


def main(argv: list[str] | None = None) -> int:
    """CLI: build and persist the v2 person-level parquet.

    Usage:
        py -3.12 -m app.medini.ml.stage_d_dataset_v2 \\
            [--data-dir app/medini/data]
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )
    parser = argparse.ArgumentParser(prog="python -m app.medini.ml.stage_d_dataset_v2")
    parser.add_argument(
        "--data-dir", type=Path, default=_DATA_DIR,
        help="Directory containing catalog.duckdb and charts.parquet",
    )
    args = parser.parse_args(argv)

    catalog = args.data_dir / "catalog.duckdb"
    out = args.data_dir / _V2_PARQUET.name
    build_v2_parquet(catalog_path=catalog, out_path=out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
