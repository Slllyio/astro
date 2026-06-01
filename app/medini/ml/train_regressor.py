"""Continuous-target XGBoost regressor — sibling to train_classifier.py.

For each row in the features parquet, the regression target is looked up
from an external CSV (`--targets-csv`) by name. Rows whose target is
missing/NaN get dropped from training and evaluation.

Output per run: same dir layout as train_classifier
(`data/ml_runs/<target>_<ts>/`) with:
  - model.json
  - feature_columns.json
  - category_levels.json
  - feature_importance.csv
  - shap_summary.png
  - report.md (regression metrics: MAE, RMSE, R²)
  - rules.csv (top features with mean +/- SHAP, no probability shift)

CLI:
    python -m app.medini.ml.train_regressor \\
        --features app/medini/data/ml_astro_with_events.parquet \\
        --targets-csv data/astro_databank/event_regression_targets.csv \\
        --target age_first_marriage \\
        --output data/ml_runs/
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # noqa: E402

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, train_test_split

from app.medini.ml.shap_rules import rank_features_by_importance
from app.medini.ml.train_classifier import (
    _write_inference_schema,
    select_features,
)

logger = logging.getLogger(__name__)


# ---------- Cross-validation ----------

def cross_validate_r2(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    seed: int,
    n_splits: int = 5,
) -> tuple[float, float]:
    """5-fold CV using R² as the score. Returns (mean, std)."""
    if len(y) < n_splits * 2:
        raise ValueError(
            f"only {len(y)} samples; need at least {n_splits * 2} for "
            f"{n_splits}-fold CV. Filter to a richer target."
        )
    cv = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    scores: list[float] = []
    for fold, (train_idx, val_idx) in enumerate(cv.split(X), start=1):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        clf = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            enable_categorical=True,
            tree_method="hist",
            random_state=seed,
            n_jobs=-1,
        )
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_val)
        scores.append(r2_score(y_val, preds))
        logger.debug("CV fold %d R²: %.4f", fold, scores[-1])
    return float(np.mean(scores)), float(np.std(scores))


def fit_final_regressor(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    *,
    seed: int,
) -> xgb.XGBRegressor:
    """Final regressor fit on full training data."""
    clf = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.1,
        enable_categorical=True,
        tree_method="hist",
        random_state=seed,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    return clf


# ---------- Target loading ----------

def load_target_values(
    targets_csv: Path,
    target_column: str,
) -> dict[str, float]:
    """Build {name: target_value} from the targets CSV.

    Rows with empty/NaN values for the target column are silently dropped
    so the regressor only sees rows with a known label. Caller does the
    parquet inner-join.
    """
    if not targets_csv.exists():
        raise FileNotFoundError(f"targets CSV missing: {targets_csv}")
    mapping: dict[str, float] = {}
    with targets_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if target_column not in (reader.fieldnames or []):
            raise ValueError(
                f"target column {target_column!r} not in CSV; available: "
                f"{reader.fieldnames}"
            )
        for row in reader:
            name = (row.get("name") or "").strip()
            raw = (row.get(target_column) or "").strip()
            if not (name and raw):
                continue
            try:
                mapping[name] = float(raw)
            except ValueError:
                continue
    return mapping


# ---------- Reporting ----------

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


def _write_feature_importance_csv(
    ranked: list[tuple[str, float]],
    output_path: Path,
) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "feature", "mean_abs_shap"])
        for rank, (feature, importance) in enumerate(ranked, start=1):
            writer.writerow([rank, feature, f"{importance:.6f}"])


def _write_report(
    output_path: Path,
    *,
    target_name: str,
    n_train: int,
    n_test: int,
    cv_r2_mean: float,
    cv_r2_std: float,
    test_r2: float,
    test_mae: float,
    test_rmse: float,
    target_mean: float,
    target_std: float,
    top_features: list[tuple[str, float]],
) -> None:
    """Markdown report identical in spirit to the classifier's report.md."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Regression target: `{target_name}`",
        "",
        f"_Generated {now}_",
        "",
        "## Run metadata",
        "",
        f"- **Target**: `{target_name}` (continuous regression)",
        f"- **Training samples**: {n_train:,}",
        f"- **Holdout test samples**: {n_test:,}",
        f"- **Target distribution**: mean = {target_mean:.2f}, std = {target_std:.2f}",
        "",
        "## Model performance",
        "",
        f"- **Cross-validation R²** (5-fold): {cv_r2_mean:.4f} ± {cv_r2_std:.4f}",
        f"- **Holdout test R²**: {test_r2:.4f}",
        f"- **Holdout test MAE**: {test_mae:.2f}",
        f"- **Holdout test RMSE**: {test_rmse:.2f}",
        "",
        "R² interpretation: 0 = predicting target mean, 1 = perfect prediction.",
        "Astrological regression targets in the 0.05–0.25 range indicate real",
        "signal; higher values typically suggest leakage or trivial patterns.",
        "",
        "## Top features (by mean |SHAP|)",
        "",
        "| Rank | Feature | Importance |",
        "|---|---|---|",
    ]
    for rank, (feature, imp) in enumerate(top_features[:20], start=1):
        lines.append(f"| {rank} | `{feature}` | {imp:.4f} |")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- Main ----------

def run_training(
    *,
    features_parquet: Path,
    targets_csv: Path,
    target_column: str,
    output_root: Path,
    seed: int = 42,
    top_n_features: int = 20,
) -> Path:
    """End-to-end regressor training. Returns the run directory."""
    if not features_parquet.exists():
        raise FileNotFoundError(f"features parquet missing: {features_parquet}")

    logger.info("loading features from %s", features_parquet)
    df = pd.read_parquet(features_parquet)
    logger.info("loaded %d rows × %d columns", len(df), len(df.columns))

    target_map = load_target_values(targets_csv, target_column)
    logger.info("target_map size for %r: %d", target_column, len(target_map))

    # The derived-targets CSV stores lowercased name keys (case-insensitive
    # join from events_all.csv). Match by lowercasing the parquet's name too.
    df["_target"] = (
        df["name"].astype(str).str.strip().str.lower()
        .map({k.strip().lower(): v for k, v in target_map.items()})
    )
    before_drop = len(df)
    df = df.dropna(subset=["_target"]).copy()
    logger.info(
        "joined target=%r: %d/%d rows have a known value",
        target_column, len(df), before_drop,
    )
    if len(df) < 50:
        raise ValueError(
            f"only {len(df)} rows have a known target value; need ≥50."
        )

    y = df["_target"].astype(float)
    target_mean = float(y.mean())
    target_std = float(y.std())
    logger.info(
        "target stats: mean=%.2f std=%.2f min=%.2f max=%.2f",
        target_mean, target_std, float(y.min()), float(y.max()),
    )

    X = select_features(df.drop(columns=["_target"]))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed,
    )

    cv_mean, cv_std = cross_validate_r2(X_train, y_train, seed=seed)
    logger.info("CV R²: %.4f ± %.4f", cv_mean, cv_std)

    model = fit_final_regressor(X_train, y_train, seed=seed)
    test_preds = model.predict(X_test)
    test_r2 = float(r2_score(y_test, test_preds))
    test_mae = float(mean_absolute_error(y_test, test_preds))
    test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
    logger.info(
        "holdout test R²=%.4f MAE=%.2f RMSE=%.2f", test_r2, test_mae, test_rmse,
    )

    # SHAP
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X_test)
    shap_values = np.asarray(sv if not isinstance(sv, list) else sv[1])
    feature_names = list(X.columns)
    ranked = rank_features_by_importance(shap_values, feature_names)

    # Output dir
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_target = "".join(c if c.isalnum() else "_" for c in target_column)
    run_dir = output_root / f"regression_{safe_target}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    model.save_model(str(run_dir / "model.json"))
    _write_inference_schema(X, run_dir)
    _write_feature_importance_csv(ranked, run_dir / "feature_importance.csv")
    _save_summary_plot(shap_values, X_test, run_dir / "shap_summary.png")
    _write_report(
        run_dir / "report.md",
        target_name=target_column,
        n_train=len(X_train),
        n_test=len(X_test),
        cv_r2_mean=cv_mean,
        cv_r2_std=cv_std,
        test_r2=test_r2,
        test_mae=test_mae,
        test_rmse=test_rmse,
        target_mean=target_mean,
        target_std=target_std,
        top_features=ranked[:top_n_features],
    )

    logger.info("run complete; artifacts in %s", run_dir)
    return run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.train_regressor",
        description="Train an XGBoost regressor on a Vedic Tensor parquet target column.",
    )
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--targets-csv", type=Path, required=True)
    parser.add_argument("--target", type=str, required=True,
                        help="Target COLUMN name in the targets CSV (e.g. "
                             "age_first_marriage, age_at_death).")
    parser.add_argument("--output", type=Path, default=Path("data/ml_runs"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        run_dir = run_training(
            features_parquet=args.features,
            targets_csv=args.targets_csv,
            target_column=args.target,
            output_root=args.output,
            seed=args.seed,
        )
    except Exception as exc:
        logger.error("training failed: %s", exc)
        return 1

    print(f"Run artifacts in: {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
