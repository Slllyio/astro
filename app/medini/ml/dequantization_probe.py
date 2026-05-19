"""Round 7 §3.1: Spatial de-quantization probe.

Tests the user's hypothesis from implementation_plan.md §3: "the
traditional systems (12 Houses, 27 Nakshatras, Divisional Charts)
are fundamentally ancient quantization techniques. Modern ML does
not need lossy compression."

The probe: train three classifiers on the same multi-class event
target with three feature subsets:

  A. CONTINUOUS-ONLY: only continuous (raw degrees, distances,
     orbs, declination) features. Strip all discrete buckets
     (house, nakshatra, sign, divisional-sign).
  B. DISCRETE-ONLY: only the classical quantized features (house,
     nakshatra, sign, dispositor, drishti binary, yoga flags).
  C. BOTH (Round-5 baseline): everything.

If A beats B significantly, the user's hypothesis is correct —
ancient quantization sacrificed information that the ML model can
recover from continuous coordinates. If B beats A, the sages'
compression preserved most of the signal. If C beats both, both
representations carry complementary information.

CLI
===
    python -m app.medini.ml.dequantization_probe \\
        --corpus app/medini/data/event_corpus_round5_all.parquet \\
        --output data/ml_runs/dequant_round7/
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

logger = logging.getLogger(__name__)


# Classify Round-5 feature columns as continuous vs discrete.
#
# Continuous: raw geometric coordinates and continuous measurements.
#   lon_*, lat_*, dec_*, vel_*, acc_*, jerk_*, dist_*,
#   aspect_orb_*, house_pos_*, nak_pos_*, lagna_lon, *_deg cols,
#   tithi_angle, yoga_angle, moon_phase_normalized,
#   dasha_start_age_*, first_*_antardasha_after_16,
#   natal_dasha_remaining_years, lagna_degree_in_sign,
#   md_elapsed_years, ad_elapsed_years, pd_elapsed_years,
#   cross_lon_*
#
# Discrete: ancient quantization buckets and binary flags.
#   nak_<planet>, house_<planet>, sign_*, *_sign, d*_sign,
#   tattva_*, dispositor_*, disp_depth_*, final_dispositor,
#   rx_*, oob_*, stationary_*, combust_*, drishti_*,
#   yoga_*, panchanga_tithi, panchanga_paksha, panchanga_karana,
#   panchanga_yoga, panchanga_vara, sade_sati_active,
#   kantaka_shani, ashtama_shani, bav_in_sign_*, sav_house_*,
#   house_from_moon_*, house_from_sun_*,
#   active_md_lord, active_ad_lord, active_pd_lord, transit_bav_*
NON_FEATURE_COLS: frozenset[str] = frozenset({
    "name", "rodden_rating", "categories_raw", "categories_lower",
    "categories_tokens", "source_url", "event_root", "event_subtype",
    "event_date", "event_jd", "birth_jd", "is_event", "_label", "y",
})


def _classify_column(col: str, dtype) -> str:
    """Return 'continuous' / 'discrete' / 'other'. Non-numeric →
    'discrete' (categoricals like dispositor_* are strings)."""
    if col in NON_FEATURE_COLS:
        return "other"
    # Discrete by prefix/suffix
    discrete_prefixes = (
        "house_", "house_from_", "nak_", "tattva_", "dispositor_",
        "disp_depth_", "rx_", "oob_", "stationary_", "drishti_",
        "yoga_", "panchanga_", "active_md_lord", "active_ad_lord",
        "active_pd_lord", "transit_bav_", "bav_in_sign_", "sav_house_",
    )
    discrete_exact = {
        "final_dispositor", "lagna_sign", "sade_sati_active",
        "kantaka_shani", "ashtama_shani",
    }
    if col in discrete_exact:
        return "discrete"
    for p in discrete_prefixes:
        if col.startswith(p):
            return "discrete"
    if col.endswith("_sign"):
        return "discrete"
    # Non-numeric → categorical → discrete
    if not pd.api.types.is_numeric_dtype(dtype):
        return "discrete"
    if pd.api.types.is_bool_dtype(dtype):
        return "discrete"
    # Default: continuous (raw degrees, distances, velocities, etc.)
    return "continuous"


def partition_features(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    continuous_cols: list[str] = []
    discrete_cols: list[str] = []
    for col in df.columns:
        cls = _classify_column(col, df[col].dtype)
        if cls == "continuous":
            continuous_cols.append(col)
        elif cls == "discrete":
            discrete_cols.append(col)
    return continuous_cols, discrete_cols


# Special handling: `nak_pos_*` columns are continuous (position WITHIN
# a nakshatra) — they actually belong in the continuous bucket even
# though their parent `nak_*` is discrete. Fix that in the partition:

def _fix_nak_pos(continuous: list[str], discrete: list[str]) -> tuple[list[str], list[str]]:
    moved = [c for c in discrete if c.startswith("nak_pos_")]
    for c in moved:
        discrete.remove(c)
        continuous.append(c)
    return continuous, discrete


# ---------- Eval helper ----------

def _eval_class(
    X: pd.DataFrame, y: pd.Series, n_classes: int, seed: int = 42,
) -> float:
    """5-fold stratified CV multi-class accuracy."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    scores: list[float] = []
    for train_idx, val_idx in cv.split(X, y):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        clf = xgb.XGBClassifier(
            objective="multi:softprob", num_class=n_classes,
            n_estimators=150, max_depth=4, learning_rate=0.1,
            enable_categorical=True, tree_method="hist",
            random_state=seed, n_jobs=-1, eval_metric="mlogloss",
        )
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_val)
        acc = float((preds == y_val.to_numpy()).mean())
        scores.append(acc)
    return float(np.mean(scores))


def _prep_features(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Subset df to cols, convert non-numeric to pandas Categorical so
    XGBoost can handle categoricals natively (matches Round-5 setup)."""
    sub = df[cols].copy()
    for c in sub.columns:
        s = sub[c]
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
            continue
        if isinstance(s.dtype, pd.CategoricalDtype):
            continue
        sub[c] = s.astype("category")
    return sub


def run_probe(
    *,
    corpus_parquet: Path, output_dir: Path,
    min_class_count: int = 100, seed: int = 42,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("loading event corpus ...")
    df = pd.read_parquet(corpus_parquet)
    df["_label"] = df["event_root"].astype(str).str.lower().str.strip()
    counts = df["_label"].value_counts()
    rare = set(counts[counts < min_class_count].index)
    if rare:
        df.loc[df["_label"].isin(rare), "_label"] = "other"
    class_names = sorted(df["_label"].unique().tolist())
    y = df["_label"].map({n: i for i, n in enumerate(class_names)}).astype(int)
    n_classes = len(class_names)
    logger.info("rows=%d  classes=%d", len(df), n_classes)

    continuous_cols, discrete_cols = partition_features(df)
    continuous_cols, discrete_cols = _fix_nak_pos(continuous_cols, discrete_cols)
    both_cols = continuous_cols + discrete_cols
    logger.info(
        "feature partition: continuous=%d  discrete=%d  both=%d",
        len(continuous_cols), len(discrete_cols), len(both_cols),
    )

    # Run three experiments
    results = {}
    for name, cols in (
        ("A_continuous_only", continuous_cols),
        ("B_discrete_only", discrete_cols),
        ("C_both_round5", both_cols),
    ):
        logger.info("=== %s (n_cols=%d) ===", name, len(cols))
        X = _prep_features(df, cols)
        acc = _eval_class(X, y, n_classes, seed=seed)
        logger.info("  5-fold CV accuracy: %.4f", acc)
        results[name] = {"n_cols": len(cols), "cv_accuracy": acc}

    # Write CSV
    csv_path = output_dir / "dequantization_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["experiment", "n_cols", "cv_accuracy"])
        for k, v in results.items():
            writer.writerow([k, v["n_cols"], v["cv_accuracy"]])

    # Report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = output_dir / "report.md"
    a = results["A_continuous_only"]["cv_accuracy"]
    b = results["B_discrete_only"]["cv_accuracy"]
    c = results["C_both_round5"]["cv_accuracy"]
    lines = [
        "# Round 7 §3.1 — Spatial de-quantization probe",
        "",
        f"_Generated {now}_",
        "",
        "## Hypothesis (from implementation_plan.md §3)",
        "",
        "Classical Vedic quantizations (houses, nakshatras, signs) are",
        "lossy compressions. Modern ML can use raw continuous coordinates",
        "and should outperform — or at least match — the quantized features.",
        "",
        "## Method",
        "",
        f"- Multi-class event_root prediction over {n_classes} classes",
        "- 5-fold stratified CV accuracy",
        "- Three feature subsets:",
        f"  * A. Continuous-only ({results['A_continuous_only']['n_cols']} cols)",
        f"  * B. Discrete-only   ({results['B_discrete_only']['n_cols']} cols)",
        f"  * C. Both (Round-5)  ({results['C_both_round5']['n_cols']} cols)",
        "",
        "## Results",
        "",
        "| Experiment | N cols | CV Accuracy |",
        "|---|---|---|",
        f"| A. Continuous-only | {results['A_continuous_only']['n_cols']} | {a:.4f} |",
        f"| B. Discrete-only   | {results['B_discrete_only']['n_cols']} | {b:.4f} |",
        f"| C. Both (Round-5)  | {results['C_both_round5']['n_cols']} | {c:.4f} |",
        "",
        f"Random baseline: 1 / {n_classes} = {1 / n_classes:.4f}",
        "",
        "## Verdict",
        "",
    ]
    if abs(a - b) < 0.005 and abs(c - max(a, b)) < 0.005:
        lines.append(
            "Continuous and discrete representations are within noise — "
            "they encode the SAME information; the sages' quantization "
            "didn't lose anything material at this scale."
        )
    elif a > b + 0.01:
        lines.append(
            f"**Continuous wins** over discrete by {a - b:+.4f}. "
            f"Hypothesis CONFIRMED: ML on raw continuous coordinates "
            f"beats the ancient quantized buckets."
        )
    elif b > a + 0.01:
        lines.append(
            f"**Discrete wins** over continuous by {b - a:+.4f}. "
            f"The sages' compression preserved more event-relevant "
            f"structure than raw coordinates alone — the discrete "
            f"buckets are not lossy at the ML scale we have."
        )
    else:
        lines.append("Marginal differences only.")
    if c > max(a, b) + 0.005:
        lines.append(
            f" The Round-5 combined set adds another {c - max(a, b):+.4f} "
            f"on top — they encode complementary information."
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report to %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dequantization_probe",
    )
    parser.add_argument(
        "--corpus", type=Path,
        default=Path("app/medini/data/event_corpus_round5_all.parquet"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/dequant_round7/"),
    )
    parser.add_argument("--min-class-count", type=int, default=100)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_probe(
        corpus_parquet=args.corpus,
        output_dir=args.output,
        min_class_count=args.min_class_count,
    )
    print(f"De-quantization probe artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
