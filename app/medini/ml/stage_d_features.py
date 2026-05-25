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


def load_corpus(*, smoke: bool = False) -> pd.DataFrame:
    """Load the (person × MD × AD × PD) leaf-window corpus."""
    path = _CORPUS_SMOKE if smoke else _CORPUS_FULL
    logger.info("Loading corpus: %s", path)
    df = pd.read_parquet(path)
    logger.info("Loaded %d windows × %d cols", len(df), len(df.columns))
    return df
