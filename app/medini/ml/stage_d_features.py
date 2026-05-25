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
    # different rodden ratings). De-dupe by name_norm, keep first; log
    # the count so silent data-quality issues surface.
    n_before = len(tensor)
    tensor = tensor.drop_duplicates(subset=["name_norm"], keep="first")
    n_dropped = n_before - len(tensor)
    if n_dropped:
        logger.warning(
            "Dropped %d duplicate-name_norm rows from Vedic Tensor "
            "(kept first). %d → %d unique persons.",
            n_dropped, n_before, len(tensor),
        )
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


# Vimshottari 9 lords in canonical project order.
_DASHA_LORDS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)

# Classical attributions from app/medini/ml/dasha_hazard_md_poisson.py.
# When the chain (MD, AD, PD) contains more of these lords, the
# classical hypothesis is that the per-day event rate goes up.
# Stage B+ verified this for several classes. Sourced as the
# rate-ladder feature here.
_CLASSICAL_LORD_ATTRIBUTIONS: dict[str, tuple[str, ...]] = {
    "career":      ("Saturn", "Sun"),
    "fame":        ("Sun", "Jupiter"),
    "work":        ("Saturn", "Mercury"),
    "marriage":    ("Venus", "Jupiter"),
    "relationship": ("Venus",),
    "relationships": ("Venus",),
    "death_cause_unspecified": ("Saturn", "Mars"),
    "death_by_disease":  ("Saturn",),
    "death_by_heart_attack": ("Mars", "Sun"),
    "health":      ("Sun", "Saturn"),
    "medical":     ("Sun", "Saturn"),
    "legal":       ("Mars", "Saturn"),
    "finance":     ("Jupiter", "Venus"),
    "business":    ("Mercury", "Jupiter"),
    "education":   ("Mercury", "Jupiter"),
    "children":    ("Jupiter",),
    "family":      ("Moon",),
    "travel":      ("Mercury", "Moon"),
    "spirituality": ("Jupiter", "Ketu"),
    "agriculture": ("Mars", "Moon"),
    "property":    ("Mars", "Saturn"),
    "personal":    (),       # no classical attribution; column still emitted, all 0
    "general":     (),
    "social":      ("Venus", "Mercury"),
    "accidents":   ("Mars", "Rahu"),
    "crime":       ("Mars", "Saturn"),
    "death_of_mate":     ("Venus",),
    "death_by_accident": ("Mars", "Rahu"),
    "death_of_father":   ("Sun",),
    "other_death":       ("Saturn", "Mars"),
}
# Sanity: every qualifying class has an entry.
assert set(_CLASSICAL_LORD_ATTRIBUTIONS.keys()) == set(QUALIFYING_EVENT_CLASSES)


def add_active_dasha_encoding(df: pd.DataFrame) -> pd.DataFrame:
    """Append MD/AD/PD lord one-hots + per-class n-relevant-lords rate-ladder.

    Adds ~9×3 + 30 = 57 columns. Spec §2 says "~25"; the exact count is
    the sum of one-hot dims (some lords may not appear in some chains)
    plus the rate-ladder columns.
    """
    df = df.copy()
    # One-hots — fixed column set (one per lord per level) to keep schema stable.
    for level in ("md", "ad", "pd"):
        col = f"{level}_lord"
        for lord in _DASHA_LORDS:
            df[f"{level}_lord_is_{lord.lower()}"] = (df[col] == lord).astype("int8")
    # Rate-ladder: count of (MD, AD, PD) lords that are in the class's
    # classical attribution set.
    chain_cols = ["md_lord", "ad_lord", "pd_lord"]
    for cls in QUALIFYING_EVENT_CLASSES:
        relevant = set(_CLASSICAL_LORD_ATTRIBUTIONS[cls])
        if not relevant:
            df[f"n_relevant_lords_{cls}"] = 0
            continue
        # Vectorized: per-cell isin → sum across the 3 chain cols.
        # ~200× faster than row-wise apply on full corpus.
        df[f"n_relevant_lords_{cls}"] = (
            df[chain_cols].isin(relevant).sum(axis=1).astype("int8")
        )
    return df


# The 16 yogas present in screening_career_yogas.parquet (verified by
# controller against the actual parquet on 2026-05-24). The order here
# is hardcoded so a parquet column-set drift doesn't silently shift
# downstream column positions.
YOGA_NAMES: tuple[str, ...] = (
    "vipareeta_harsha", "vipareeta_sarala", "vipareeta_vimala",
    "sunapha", "anapha", "durudhura", "kemadruma",
    "ruchaka", "bhadra", "hamsa", "malavya", "sasa",
    "gajakesari", "budha_aditya", "raja_yoga", "dhana_yoga",
)
assert len(YOGA_NAMES) == 16

# Map each yoga to the planet set whose membership in the active dasha
# chain (MD/AD/PD lord) flips dasha_active=1. Sourced from
# app/core/yogas.py docstrings (e.g., detect_sunapha line 576+).
#
# Configurational yogas (Sunapha/Anapha/Durudhura/Kemadruma) are defined
# by what's in 2nd/12th from Moon — there is no single-planet activation.
# Their planet set is intentionally empty; dasha_active is always 0.
# The natal_strength column still carries useful signal for these yogas.
_YOGA_PLANETS: dict[str, frozenset[str]] = {
    "vipareeta_harsha": frozenset({"Saturn", "Mars", "Jupiter"}),
    "vipareeta_sarala": frozenset({"Saturn", "Mars"}),
    "vipareeta_vimala": frozenset({"Saturn"}),
    "sunapha":     frozenset(),  # Moon-configurational
    "anapha":      frozenset(),  # Moon-configurational
    "durudhura":   frozenset(),  # Moon-configurational
    "kemadruma":   frozenset(),  # Moon-configurational (anti-yoga)
    "ruchaka":     frozenset({"Mars"}),
    "bhadra":      frozenset({"Mercury"}),
    "hamsa":       frozenset({"Jupiter"}),
    "malavya":     frozenset({"Venus"}),
    "sasa":        frozenset({"Saturn"}),
    "gajakesari":  frozenset({"Moon", "Jupiter"}),
    "budha_aditya": frozenset({"Sun", "Mercury"}),
    "raja_yoga":   frozenset({"Sun", "Jupiter", "Saturn"}),  # kendra/trikona lord proxy
    "dhana_yoga":  frozenset({"Jupiter", "Venus"}),           # wealth significators
}
assert set(_YOGA_PLANETS.keys()) == set(YOGA_NAMES)


def add_yoga_features_with_dasha_gating(df: pd.DataFrame) -> pd.DataFrame:
    """Join Phase-3B yoga natal strengths + add per-yoga dasha_active flags.

    Adds 32 columns: 16 `<yoga>_natal_strength` (from
    screening_career_yogas.parquet) + 16 `<yoga>_dasha_active` (computed
    here from _YOGA_PLANETS). Vectorized for full-corpus scale.
    """
    natal_path = _DATA_DIR / "screening_career_yogas.parquet"
    if not natal_path.exists():
        raise FileNotFoundError(
            f"Yoga-augmented parquet not found at {natal_path}. "
            "Run `py -3.12 -m app.medini.etl.add_yoga_features` first."
        )
    yoga_df = pd.read_parquet(natal_path)
    natal_strength_cols = [c for c in yoga_df.columns if c.endswith("_natal_strength")]
    yoga_subset_raw = yoga_df[["name_norm", *natal_strength_cols]]
    yoga_subset = yoga_subset_raw.drop_duplicates("name_norm")
    n_dropped = len(yoga_subset_raw) - len(yoga_subset)
    if n_dropped:
        logger.warning(
            "Dropped %d duplicate-name_norm rows from yoga parquet "
            "(kept first). %d → %d unique persons.",
            n_dropped, len(yoga_subset_raw), len(yoga_subset),
        )

    df = df.merge(yoga_subset, on="name_norm", how="left", validate="many_to_one")
    # Report join hit rate so a substrate-mismatch (e.g., smoke corpus
    # vs full-cohort yoga parquet) surfaces in logs instead of being
    # silently masked by the fillna(0.0) below.
    n_matched = df[natal_strength_cols[0]].notna().sum() if natal_strength_cols else 0
    logger.info(
        "Yoga join: %d / %d windows matched a yoga row (%.1f%%). "
        "Unmatched windows get natal_strength=0.0.",
        int(n_matched), len(df), 100.0 * n_matched / max(1, len(df)),
    )
    # Fill NaN natal-strength values with 0.0 (person had no yoga score row).
    for col in natal_strength_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(0.0)

    # Dasha-active flags — VECTORIZED (~200× faster than .apply on full corpus).
    chain_cols = ["md_lord", "ad_lord", "pd_lord"]
    for yoga in YOGA_NAMES:
        planets = _YOGA_PLANETS[yoga]
        if not planets:
            df[f"{yoga}_dasha_active"] = 0
            continue
        df[f"{yoga}_dasha_active"] = (
            df[chain_cols].isin(planets).any(axis=1).astype("int8")
        )
    return df
