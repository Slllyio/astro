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

import argparse
import logging
import sys
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
#
# IMPORTANT — points to the FULL-COVERAGE rebuild (10,239 dasha-corpus
# persons; built 2026-05-25 by the regeneration handoff procedure at
# docs/superpowers/specs/2026-05-25-stage-d-data-regeneration-plan.md).
# The original ml_astro_features.parquet (14,070 persons) did not overlap
# with the dasha corpus and caused 100% NaN on Vedic Tensor cols at
# sub-gate D.0 (commit f1d95ec). Do not revert this path without
# verifying the corpus-overlap rate first.
_VEDIC_TENSOR_PARQUET = _DATA_DIR / "ml_astro_features_full.parquet"


def join_natal_vedic_tensor(corpus: pd.DataFrame) -> pd.DataFrame:
    """Left-join the per-person Vedic Tensor onto each (person × window) row.

    The Tensor has ~530 columns produced by app.medini.etl.feature_engineering.
    Two parquet schemas are supported:
      * Legacy `ml_astro_features.parquet` (14,070 persons, no overlap with
        the dasha corpus) — ships with raw `name` only; name_norm derived
        here via str.strip().lower().
      * Full-coverage `ml_astro_features_full.parquet` (10,239 persons,
        100% dasha-corpus overlap; built 2026-05-25 per the regeneration
        handoff at docs/superpowers/specs/2026-05-25-stage-d-data-regeneration-plan.md)
        — already carries name_norm; no derivation needed.

    Either parquet works; the function detects which schema is present.
    Same value across all windows for a given person.
    """
    if not _VEDIC_TENSOR_PARQUET.exists():
        raise FileNotFoundError(
            f"Vedic Tensor parquet not found at {_VEDIC_TENSOR_PARQUET}. "
            "Rebuild via `py -3.12 -m app.medini.etl.databank_etl` OR "
            "the regen procedure in docs/superpowers/specs/"
            "2026-05-25-stage-d-data-regeneration-plan.md."
        )
    tensor = pd.read_parquet(_VEDIC_TENSOR_PARQUET).copy()
    if "name_norm" in tensor.columns:
        # Full-coverage schema — name_norm already present.
        if "name" in tensor.columns:
            tensor = tensor.drop(columns=["name"])
    elif "name" in tensor.columns:
        # Legacy schema — derive name_norm from raw name.
        tensor["name_norm"] = tensor["name"].astype(str).str.lower().str.strip()
        tensor = tensor.drop(columns=["name"])
    else:
        raise ValueError(
            "Vedic Tensor parquet missing both `name` and `name_norm`; "
            "cannot derive a join key."
        )
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
    """Load the (person × MD × AD × PD) leaf-window corpus.

    Smoke mode: if the smoke parquet is schema-stale (missing event label
    columns that exist in the full corpus), rebuild it on the fly by
    filtering the full corpus to the smoke persons and overwrite the stale
    file. This handles the case where the full corpus ETL added new event
    columns after the smoke parquet was last built.
    """
    if not smoke:
        path = _CORPUS_FULL
        logger.info("Loading corpus: %s", path)
        df = pd.read_parquet(path)
        logger.info("Loaded %d windows × %d cols", len(df), len(df.columns))
        return df

    # --- smoke path ---
    if not _CORPUS_SMOKE.exists():
        raise FileNotFoundError(
            f"Smoke corpus not found at {_CORPUS_SMOKE}."
        )
    smoke_df = pd.read_parquet(_CORPUS_SMOKE)
    full_df = pd.read_parquet(_CORPUS_FULL)

    missing_cols = [c for c in full_df.columns if c not in smoke_df.columns]
    if missing_cols:
        logger.warning(
            "Smoke corpus is schema-stale: missing %d cols present in full corpus "
            "(%s …). Rebuilding smoke by filtering full corpus to smoke persons.",
            len(missing_cols), missing_cols[:5],
        )
        smoke_names = set(smoke_df["name_norm"].unique())
        smoke_df = full_df[full_df["name_norm"].isin(smoke_names)].reset_index(drop=True)
        smoke_df.to_parquet(_CORPUS_SMOKE, index=False)
        logger.info(
            "Rebuilt smoke corpus: %d rows × %d cols — saved to %s",
            len(smoke_df), len(smoke_df.columns), _CORPUS_SMOKE,
        )

    logger.info("Loaded smoke corpus: %d windows × %d cols", len(smoke_df), len(smoke_df.columns))
    return smoke_df


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
    # Use the full-coverage yoga parquet built 2026-05-25 by the regen
    # procedure (covers all 10,239 dasha-corpus persons). The legacy
    # screening_career_yogas.parquet only covered 951 career-screening
    # cohort persons (0% dasha-corpus overlap) and was kept as a fallback
    # for backwards compatibility.
    natal_path = _DATA_DIR / "dasha_corpus_yogas.parquet"
    if not natal_path.exists():
        # Fallback to the legacy parquet (will likely show 0% join hit rate
        # on the dasha corpus; the hit-rate log below makes this visible).
        natal_path = _DATA_DIR / "screening_career_yogas.parquet"
    if not natal_path.exists():
        raise FileNotFoundError(
            f"Yoga-augmented parquet not found at {natal_path} nor the "
            "fallback dasha_corpus_yogas.parquet. Run the regen procedure "
            "at docs/superpowers/specs/2026-05-25-stage-d-data-regeneration-plan.md."
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


_STAGE_E_PARQUET = _DATA_DIR / "natal_lord_houses.parquet"  # built by build_natal_lord_houses.py
_DOCTRINE_PARQUET = _DATA_DIR / "doctrine_scores.parquet"   # generated by dasha_doctrine_score.py
                                                              # — currently DOES NOT EXIST; add_doctrine_scores is
                                                              # a documented no-op when missing (see spec §2:
                                                              # doctrine is "Optional pre-computed classical prior")


def add_stage_e_features(df: pd.DataFrame) -> pd.DataFrame:
    """Join Stage-E per-(person, planet) lord-house features.

    Columns: rules_<planet>, occ_<planet>, aspects_<planet>, sign_<planet>
    per planet in the 9-lord set, plus asc_sign. Same value across windows
    for a given person.

    Logs the join hit rate so a substrate-mismatch (e.g., smoke corpus vs
    full-cohort lord-house parquet) surfaces in logs instead of being silent.
    """
    if not _STAGE_E_PARQUET.exists():
        raise FileNotFoundError(
            f"Stage-E parquet not found at {_STAGE_E_PARQUET}. "
            "Run `py -3.12 -m app.medini.etl.build_natal_lord_houses` first."
        )
    stage_e_raw = pd.read_parquet(_STAGE_E_PARQUET)
    if "name_norm" not in stage_e_raw.columns:
        raise ValueError("Stage-E parquet missing `name_norm` join key.")
    # Drop the raw `name` column to avoid merge collision with the corpus.
    drop_cols = [c for c in ("name",) if c in stage_e_raw.columns]
    stage_e = stage_e_raw.drop(columns=drop_cols)
    # De-dupe by name_norm to satisfy validate="many_to_one".
    n_before = len(stage_e)
    stage_e = stage_e.drop_duplicates(subset=["name_norm"], keep="first")
    n_dropped = n_before - len(stage_e)
    if n_dropped:
        logger.warning(
            "Dropped %d duplicate-name_norm rows from Stage-E parquet "
            "(kept first). %d → %d unique persons.",
            n_dropped, n_before, len(stage_e),
        )

    joined = df.merge(stage_e, on="name_norm", how="left", validate="many_to_one")
    assert len(joined) == len(df), "left-join broke row count"

    # Report join hit rate (parity with yoga + Vedic Tensor logging).
    sentinel = "rules_sun" if "rules_sun" in joined.columns else None
    if sentinel:
        n_matched = joined[sentinel].notna().sum()
        logger.info(
            "Stage-E join: %d / %d windows matched a lord-house row (%.1f%%). "
            "Unmatched windows get NaN in Stage-E feature columns.",
            int(n_matched), len(joined), 100.0 * n_matched / max(1, len(joined)),
        )

    # TODO(stage_d_dataset.py / Task 11): The Stage-E parquet contains
    # list-typed columns — `rules_<planet>` is a list[int] of house numbers
    # the planet rules for that asc_sign, `occ_<planet>` is the single
    # occupied house, `aspects_<planet>` is a list[int] of aspected houses.
    # `occ_*` is scalar (safe to cast directly), but `rules_*` and
    # `aspects_*` need an encoding step before they can flow into
    # StageDDataset.features as float32. Options:
    #   (a) Convert each list[int] into a 12-dim binary indicator vector
    #       per planet (rules_sun_h1, rules_sun_h2, ... rules_sun_h12).
    #   (b) Reduce to scalars: count, presence-of-a-specific-house, etc.
    # Decide in Task 11 with the dataset-building code in front of you.
    # For Task 5's scope (parquet join), keeping the raw list columns is
    # correct — encoding is StageDDataset's responsibility.
    return joined


def add_doctrine_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Optionally join doctrine_score_<class> columns (one per qualifying class).

    Per spec §2, doctrine scores are an OPTIONAL warm-prior input to the
    neural net. If the parquet doesn't exist, this function is a no-op:
    it logs a warning and returns the dataframe unchanged. The Stage D
    model will still train without these columns.

    To enable: run `py -3.12 -m app.medini.ml.dasha_doctrine_score`
    and ensure its output lands at the path defined by _DOCTRINE_PARQUET.
    """
    if not _DOCTRINE_PARQUET.exists():
        logger.warning(
            "Optional doctrine parquet not found at %s — add_doctrine_scores "
            "is a no-op. Stage D will train without a doctrine warm-prior. "
            "(Spec §2 marks this input as Optional.)",
            _DOCTRINE_PARQUET,
        )
        return df
    doc = pd.read_parquet(_DOCTRINE_PARQUET)
    keep = ["name_norm"] + [
        f"doctrine_score_{c}" for c in QUALIFYING_EVENT_CLASSES
        if f"doctrine_score_{c}" in doc.columns
    ]
    return df.merge(doc[keep], on="name_norm", how="left", validate="many_to_one")


def _ensure_event_label_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantee all 30 qualifying-class event label columns exist.

    The full corpus carries all 30 `event_<class>` columns; the smoke corpus
    (a stratified 10% sample) may be missing rare classes that had 0 events
    in the sampled windows. Fill with 0 so the downstream schema is always
    complete and consistent regardless of split.
    """
    df = df.copy()
    missing = [
        cls for cls in QUALIFYING_EVENT_CLASSES
        if f"event_{cls}" not in df.columns
    ]
    if missing:
        logger.info(
            "Adding %d missing event label columns (all-zero) for rare classes "
            "absent from this corpus split: %s",
            len(missing), missing,
        )
        for cls in missing:
            df[f"event_{cls}"] = 0
    return df


def _shrink_memory_footprint(df: pd.DataFrame) -> pd.DataFrame:
    """Downcast dtypes + drop object cols to make the materialized parquet
    fit in memory for full-corpus runs.

    Profile on the un-shrunk full materialized parquet (6.17M rows × 726 cols)
    showed 52.91 GB in-memory: object cols 22 GB (string categoricals + list
    columns that _feature_columns drops at Cox-time anyway), int64 17 GB
    (mostly one-hots and small counts), float64 13 GB (Vedic continuous
    features). After this shrink we expect ~10-13 GB in-memory, which
    fits comfortably for the train/test copies the gate evaluation needs.

    Strategy:
      - Object cols: DROP entirely. They're dead weight in the feature
        matrix (Cox's numeric-only filter discards them; the Stage D
        dataset's _select_feature_columns delegates to the same filter).
        The narrative loss is small: the only object cols are tattva_*,
        dispositor_*, panchanga_paksha, final_dispositor (string
        categoricals — could one-hot in a future revision) and rules_*/
        aspects_* (list-typed Stage-E cols — pending encoding strategy
        in the Task 5 TODO).
      - int64 → int8 if values fit in [-128, 127], else int32. Most
        int64 cols here are 0/1 one-hots or small house-numbers in
        [0, 12]; int8 covers them.
      - float64 → float32. ~7 significant digits is plenty for the
        Cox PH + DeepHit pipeline (lifelines internally normalizes
        anyway, killing the last few digits of precision regardless).
    """
    cols_before = len(df.columns)
    mem_before_gb = df.memory_usage(deep=True).sum() / 1e9
    object_cols = [c for c in df.columns if df[c].dtype == "object"
                   and c not in ("name", "name_norm")]
    if object_cols:
        df = df.drop(columns=object_cols)
        logger.info("Dropped %d object-dtype feature cols (string categoricals + "
                    "list-typed Stage-E cols); they're discarded at Cox-time anyway.",
                    len(object_cols))

    for col in df.columns:
        dt = df[col].dtype
        if dt == "int64":
            vmax = df[col].abs().max() if len(df) else 0
            if pd.isna(vmax):
                continue
            if vmax < 128:
                df[col] = df[col].astype("int8")
            elif vmax < 2_147_483_648:
                df[col] = df[col].astype("int32")
        elif dt == "float64":
            df[col] = df[col].astype("float32")

    mem_after_gb = df.memory_usage(deep=True).sum() / 1e9
    logger.info("Memory shrink: %d → %d cols, %.2f GB → %.2f GB (%.0f%% reduction).",
                cols_before, len(df.columns), mem_before_gb, mem_after_gb,
                100 * (1 - mem_after_gb / mem_before_gb))
    return df


def materialize(*, smoke: bool, write: bool = True) -> pd.DataFrame:
    """Compose all feature blocks and (optionally) write the output parquet."""
    df = load_corpus(smoke=smoke)
    df = join_natal_vedic_tensor(df)
    df = add_active_dasha_encoding(df)
    df = add_yoga_features_with_dasha_gating(df)
    df = add_stage_e_features(df)
    df = add_doctrine_scores(df)
    df = _ensure_event_label_columns(df)
    df = _shrink_memory_footprint(df)

    if write:
        out = _DATA_DIR / ("dasha_stage_d_features_smoke.parquet" if smoke
                           else "dasha_stage_d_features.parquet")
        df.to_parquet(out, index=False)
        logger.info("Wrote %s (%d rows × %d cols)", out, len(df), len(df.columns))
    return df


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m app.medini.ml.stage_d_features")
    p.add_argument("--smoke", action="store_true",
                   help="Use the smoke variant of the corpus.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )
    args = _parse_args(argv)
    try:
        materialize(smoke=args.smoke, write=True)
    except Exception:
        logger.exception("Feature materialization failed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
