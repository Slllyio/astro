"""Stage 3: train an XGBoost classifier on the Vedic Tensor parquet, run
SHAP analysis, extract rules, and write a Markdown report.

Pluggable target via `--target <substring>`: matched against the
`categories_lower` column produced by Stage 2. So `--target politician`
matches everything containing "politician" in any category position.

Outputs to `data/ml_runs/{target}_{ISO8601_timestamp}/`:
  - model.json              — XGBoost serialized booster
  - shap_summary.png        — top-20 features by mean |SHAP|
  - shap_dependence_*.png   — per-feature dependence plots for top-3
  - feature_importance.csv  — full ranked feature list
  - rules.csv               — extracted rules above the magnitude threshold
  - report.md               — human-readable summary

CLI:
    python -m app.medini.ml.train_classifier \\
        --features app/medini/data/ml_astro_features.parquet \\
        --target politician \\
        --output data/ml_runs/ \\
        [--min-rule-impact 0.05] [--top-n-features 10] [--seed 42]
"""
from __future__ import annotations

# Force a non-interactive matplotlib backend BEFORE pyplot is imported by SHAP.
# Headless CI machines have no display; the default `qtagg` or `tkagg` would
# fail with "no display" errors. Agg renders to PNG without a window.
import matplotlib
matplotlib.use("Agg")  # noqa: E402

import argparse
import csv
import dataclasses
import datetime as dt
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

from app.medini.ml.report_writer import write_report
from app.medini.ml.shap_rules import Rule, extract_rules, rank_features_by_importance

logger = logging.getLogger(__name__)

# Columns present in the parquet that are NOT model inputs (they're labels
# or traceability metadata).
NON_FEATURE_COLUMNS: tuple[str, ...] = (
    "name", "rodden_rating", "categories_raw", "categories_lower",
    "categories_tokens", "source_url",
)


def derive_binary_target(df: pd.DataFrame, target_substring: str) -> pd.Series:
    """Build a 0/1 column from `categories_lower` substring match.

    `--target politician` matches "vocation : politics : politician",
    "vocation : politics : ex-politician", etc. Lowercase comparison
    against the pre-flattened `categories_lower` column.
    """
    target = target_substring.strip().lower()
    if not target:
        raise ValueError("target substring cannot be empty")
    return df["categories_lower"].fillna("").str.contains(target, regex=False).astype(int)


def select_features(df: pd.DataFrame) -> pd.DataFrame:
    """Drop label/metadata columns and prep dtypes for XGBoost.

    Any non-numeric, non-categorical column gets converted to
    `pd.Categorical` so XGBoost's `enable_categorical=True` can consume
    it directly. This catches both numpy `object` dtype (Windows) and
    pandas `string` dtype (newer pandas/pyarrow on Linux), which would
    otherwise break XGBoost's DMatrix construction.
    """
    feature_df = df.drop(columns=list(NON_FEATURE_COLUMNS), errors="ignore").copy()
    for col in feature_df.columns:
        s = feature_df[col]
        # Skip already-numeric and already-categorical columns.
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
            continue
        if isinstance(s.dtype, pd.CategoricalDtype):
            continue
        # Anything else (object, string, etc.) → Categorical.
        feature_df[col] = s.astype("category")
    return feature_df


def cross_validate_roc_auc(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    seed: int,
    n_splits: int = 5,
) -> tuple[float, float]:
    """5-fold stratified CV ROC-AUC; returns (mean, std)."""
    if y.nunique() < 2:
        raise ValueError(
            f"target has only {y.nunique()} class(es); need both 0 and 1 for CV"
        )
    if int(y.sum()) < n_splits:
        raise ValueError(
            f"only {int(y.sum())} positive sample(s); need at least {n_splits} for "
            f"{n_splits}-fold stratified CV. Use a broader --target token."
        )
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    scores: list[float] = []
    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y), start=1):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        scale_pos = float((y_tr == 0).sum()) / max(int((y_tr == 1).sum()), 1)
        clf = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            scale_pos_weight=scale_pos,
            enable_categorical=True,
            tree_method="hist",
            random_state=seed,
            eval_metric="logloss",
        )
        clf.fit(X_tr, y_tr)
        proba = clf.predict_proba(X_val)[:, 1]
        scores.append(roc_auc_score(y_val, proba))
        logger.debug("CV fold %d ROC-AUC: %.4f", fold, scores[-1])
    return float(np.mean(scores)), float(np.std(scores))


def fit_final_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    *,
    seed: int,
) -> xgb.XGBClassifier:
    """Final model fit on full training data with class-imbalance scaling."""
    scale_pos = float((y_train == 0).sum()) / max(int((y_train == 1).sum()), 1)
    clf = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=scale_pos,
        enable_categorical=True,
        tree_method="hist",
        random_state=seed,
        eval_metric="logloss",
    )
    clf.fit(X_train, y_train)
    return clf


def shap_values_for_test(
    model: xgb.XGBClassifier,
    X_test: pd.DataFrame,
) -> np.ndarray:
    """Compute per-sample SHAP values via TreeExplainer."""
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X_test)
    # XGBoost binary models return a single (n, k) array; multiclass returns list.
    return np.asarray(sv) if isinstance(sv, list) is False else np.asarray(sv[1])


def _save_summary_plot(
    shap_values: np.ndarray,
    X_test: pd.DataFrame,
    output_path: Path,
) -> None:
    fig = plt.figure(figsize=(10, 7))
    shap.summary_plot(
        shap_values, X_test, max_display=20, show=False, plot_size=None,
    )
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def _save_dependence_plots(
    shap_values: np.ndarray,
    X_test: pd.DataFrame,
    feature_names: list[str],
    output_dir: Path,
    top_n: int = 3,
) -> list[Path]:
    """Dependence plot for the top-N features. SHAP picks an interaction
    feature automatically when available."""
    ranked = rank_features_by_importance(shap_values, feature_names)
    paths: list[Path] = []
    for feature, _importance in ranked[:top_n]:
        try:
            col_idx = feature_names.index(feature)
            fig = plt.figure(figsize=(8, 5))
            shap.dependence_plot(
                col_idx, shap_values, X_test, feature_names=feature_names,
                show=False, ax=plt.gca(),
            )
            path = output_dir / f"shap_dependence_{feature}.png"
            fig.savefig(path, dpi=120, bbox_inches="tight")
            plt.close(fig)
            paths.append(path)
        except Exception:  # noqa: BLE001
            logger.exception("dependence plot failed for %s; skipping", feature)
    return paths


def _write_feature_importance_csv(
    ranked: list[tuple[str, float]],
    output_path: Path,
) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "feature", "mean_abs_shap"])
        for rank, (feature, importance) in enumerate(ranked, start=1):
            writer.writerow([rank, feature, f"{importance:.6f}"])


def _write_rules_csv(rules: list[Rule], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "feature", "range_low", "range_high", "direction",
            "probability_delta", "sample_count", "feature_importance",
        ])
        writer.writeheader()
        for rule in rules:
            writer.writerow(dataclasses.asdict(rule))


def run_training(
    *,
    features_parquet: Path,
    target_substring: str,
    output_root: Path,
    seed: int = 42,
    top_n_features: int = 10,
    min_rule_impact: float = 0.05,
) -> Path:
    """Execute the Stage 3 pipeline end-to-end. Returns the per-run output dir."""
    if not features_parquet.exists():
        raise FileNotFoundError(f"features parquet not found: {features_parquet}")

    logger.info("loading features from %s", features_parquet)
    df = pd.read_parquet(features_parquet)
    logger.info("loaded %d rows × %d columns", len(df), len(df.columns))

    y = derive_binary_target(df, target_substring)
    n_pos = int(y.sum())
    base_rate = float(y.mean())
    logger.info(
        "target=%r  positives=%d  base_rate=%.4f", target_substring, n_pos, base_rate,
    )
    if n_pos < 5:
        raise ValueError(
            f"insufficient positive class samples: {n_pos} (need ≥ 5). "
            f"Try a broader target substring."
        )

    X = select_features(df)

    # Stratified 80/20 split; CV happens inside the 80% train half.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed,
    )

    cv_mean, cv_std = cross_validate_roc_auc(X_train, y_train, seed=seed)
    logger.info("CV ROC-AUC: %.4f ± %.4f", cv_mean, cv_std)

    model = fit_final_model(X_train, y_train, seed=seed)
    test_proba = model.predict_proba(X_test)[:, 1]
    test_auc = float(roc_auc_score(y_test, test_proba))
    logger.info("holdout test ROC-AUC: %.4f", test_auc)

    # SHAP on the holdout test set
    shap_values = shap_values_for_test(model, X_test)
    feature_names = list(X.columns)

    # Output directory: data/ml_runs/{target}_{timestamp}/
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_target = "".join(c if c.isalnum() else "_" for c in target_substring)
    run_dir = output_root / f"{safe_target}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Persist model
    model.save_model(str(run_dir / "model.json"))

    # Feature importance ranking
    ranked = rank_features_by_importance(shap_values, feature_names)
    _write_feature_importance_csv(ranked, run_dir / "feature_importance.csv")

    # Plots
    _save_summary_plot(shap_values, X_test, run_dir / "shap_summary.png")
    plot_paths = [run_dir / "shap_summary.png"]
    plot_paths.extend(_save_dependence_plots(
        shap_values, X_test, feature_names, run_dir, top_n=3,
    ))

    # Rule extraction (the magnitude-filtered output)
    rules = extract_rules(
        feature_matrix=X_test.select_dtypes(include="number").to_numpy(dtype=float),
        shap_values=_align_numeric_shap(shap_values, X_test),
        feature_names=[c for c in feature_names if X_test[c].dtype.kind in "biufc"],
        base_rate=base_rate,
        top_n_features=top_n_features,
        min_rule_impact=min_rule_impact,
    )
    _write_rules_csv(rules, run_dir / "rules.csv")

    # Markdown report
    write_report(
        run_dir / "report.md",
        target_name=target_substring,
        n_train=len(X_train),
        n_test=len(X_test),
        base_rate=base_rate,
        cv_roc_auc_mean=cv_mean,
        cv_roc_auc_std=cv_std,
        test_roc_auc=test_auc,
        top_features=ranked[:20],
        rules=rules,
        plot_paths=plot_paths,
        min_rule_impact=min_rule_impact,
    )

    logger.info("run complete; artifacts in %s", run_dir)
    return run_dir


def _align_numeric_shap(
    shap_values: np.ndarray, X_test: pd.DataFrame,
) -> np.ndarray:
    """Project SHAP values to numeric-only columns (rule extraction needs
    numeric feature values to bin). Categorical columns still influence the
    model + appear in plots; just not in the threshold-rule output."""
    numeric_mask = [X_test[c].dtype.kind in "biufc" for c in X_test.columns]
    return shap_values[:, numeric_mask]


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.train_classifier",
        description="Train an XGBoost classifier on the Vedic Tensor + extract "
                    "astrological rules via SHAP.",
    )
    parser.add_argument("--features", type=Path,
                        default=Path("app/medini/data/ml_astro_features.parquet"),
                        help="Stage 2 ETL output parquet.")
    parser.add_argument("--target", type=str, required=True,
                        help="Lowercase substring matched against categories_lower "
                             "(e.g. 'politician', 'athlete', 'astronaut').")
    parser.add_argument("--output", type=Path, default=Path("data/ml_runs"),
                        help="Root directory for per-run output folders.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for deterministic runs.")
    parser.add_argument("--top-n-features", type=int, default=10,
                        help="How many top features (by |SHAP|) to scan for rules.")
    parser.add_argument("--min-rule-impact", type=float, default=0.05,
                        help="Minimum |probability shift| to emit a rule (default 0.05 = 5%%).")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        run_dir = run_training(
            features_parquet=args.features,
            target_substring=args.target,
            output_root=args.output,
            seed=args.seed,
            top_n_features=args.top_n_features,
            min_rule_impact=args.min_rule_impact,
        )
    except Exception as exc:
        logger.error("training failed: %s", exc)
        return 1

    print(f"Run artifacts in: {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
