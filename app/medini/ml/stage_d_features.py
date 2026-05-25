"""Fork-A Stage D — feature pipeline.

Joins four feature blocks (natal Vedic Tensor + active dasha encoding +
active yogas + Stage-E lord-house features + doctrine score) onto the
(person × MD × AD × PD) leaf-window corpus, producing the input matrix
that Stage D's Dynamic-DeepHit model and the matched Cox baseline both
consume.

Output: app/medini/data/dasha_stage_d_features.parquet (+ _smoke variant).

Usage:
    py -3.12 -m app.medini.ml.stage_d_features \\
        --input app/medini/data/dasha_mdadpd_corpus.parquet \\
        --output app/medini/data/dasha_stage_d_features.parquet \\
        [--smoke]

See docs/superpowers/specs/2026-05-24-fork-a-stage-d-design.md §2.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Spec Appendix A — sorted descending by total positives.
# DO NOT REORDER. The class-id ↔ index mapping is consumed by
# stage_d_dataset.py and stage_d_model.py.
QUALIFYING_EVENT_CLASSES: tuple[str, ...] = (
    "fame", "career", "death_cause_unspecified", "health", "relationships",
    "personal", "education", "legal", "finance", "marriage",
    "relationship", "work", "agriculture", "business", "medical",
    "property", "death_by_disease", "general", "travel", "family",
    "children", "spirituality", "accidents", "crime", "death_by_heart_attack",
    "social", "death_of_mate", "death_by_accident", "death_of_father", "other_death",
)
assert len(QUALIFYING_EVENT_CLASSES) == 30

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CORPUS_FULL = _DATA_DIR / "dasha_mdadpd_corpus.parquet"
_CORPUS_SMOKE = _DATA_DIR / "dasha_mdadpd_smoke.parquet"


# Path to the canonical natal Vedic Tensor parquet. If the ETL writes
# elsewhere, update this constant — do NOT silently fail.
_VEDIC_TENSOR_PARQUET = _DATA_DIR / "ml_astro_features.parquet"


def join_natal_vedic_tensor(corpus: pd.DataFrame) -> pd.DataFrame:
    """Left-join the per-person Vedic Tensor onto each (person × window) row.

    The Tensor has ~193 columns produced by app.medini.etl.feature_engineering.
    The parquet ships with `name` (raw) but not `name_norm`, so we derive
    `name_norm` here using the project-wide convention from
    app.medini.etl.build_screening_cohort._norm_name (just str.strip()).

    Same value across all windows for a given person.
    """
    if not _VEDIC_TENSOR_PARQUET.exists():
        raise FileNotFoundError(
            f"Vedic Tensor parquet not found at {_VEDIC_TENSOR_PARQUET}. "
            "Rebuild via `py -3.12 -m app.medini.etl.databank_etl`."
        )
    tensor = pd.read_parquet(_VEDIC_TENSOR_PARQUET)
    if "name" not in tensor.columns:
        raise ValueError("Vedic Tensor parquet missing `name` column.")
    # Derive name_norm from name (project convention: just strip whitespace).
    tensor = tensor.copy()
    tensor["name_norm"] = tensor["name"].astype(str).str.strip()
    # Drop the raw `name` column to avoid a column collision with the corpus.
    tensor = tensor.drop(columns=["name"])
    # The tensor may carry duplicates by name (e.g., Einstein × 2 from
    # different rodden ratings). De-dupe by name_norm, keep first.
    tensor = tensor.drop_duplicates(subset=["name_norm"], keep="first")
    logger.info(
        "Joining Vedic Tensor (%d persons × %d cols) onto %d windows",
        len(tensor), len(tensor.columns), len(corpus),
    )
    joined = corpus.merge(tensor, on="name_norm", how="left", validate="many_to_one")
    assert len(joined) == len(corpus), "left-join broke row count"
    return joined


def load_corpus(*, smoke: bool = False) -> pd.DataFrame:
    """Load the (person × MD × AD × PD) leaf-window corpus."""
    path = _CORPUS_SMOKE if smoke else _CORPUS_FULL
    logger.info("Loading corpus: %s", path)
    df = pd.read_parquet(path)
    logger.info("Loaded %d windows × %d cols", len(df), len(df.columns))
    return df
