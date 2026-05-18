"""Multi-class XGBoost classifier — predicts primary vocation root.

Sibling to train_classifier.py (binary) and train_regressor.py (continuous).
Target labels come from `event_vocation_multiclass.csv` — one label per
person (politics / sports / writers / entertainment / business / art /
science / military / education / law / medical / beauty / religion /
occult / other).

This is one-of-K softmax classification; XGBoost handles it natively
with `objective="multi:softprob"`. Per-class AUCs are reported via
one-vs-rest decomposition for comparison against the existing binary
classifiers.

Output per run: same dir layout as the binary trainer
(`data/ml_runs/multiclass_<target>_<ts>/`) with:
  - model.json
  - feature_columns.json, category_levels.json
  - feature_importance.csv (mean |SHAP| across all classes)
  - per_class_auc.csv  (one-vs-rest AUC per class)
  - confusion_matrix.csv
  - report.md
  - shap_summary.png

CLI:
    python -m app.medini.ml.train_multiclass \\
        --features app/medini/data/ml_astro_with_events.parquet \\
        --targets-csv data/astro_databank/event_vocation_multiclass.csv \\
        --target-column vocation_root \\
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
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

from app.medini.ml.train_classifier import (
    _write_inference_schema,
    select_features,
)

logger = logging.getLogger(__name__)


# ---------- Label loading ----------

def load_label_map(targets_csv: Path, label_column: str) -> dict[str, str]:
    """Build {name: label_string} for multi-class."""
    if not targets_csv.exists():
        raise FileNotFoundError(f"targets CSV missing: {targets_csv}")
    mapping: dict[str, str] = {}
    with targets_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            label = (row.get(label_column) or "").strip()
            if name and label:
                mapping[name] = label
    return mapping


# ---------- CV ----------

def cross_validate_macro_f1(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    seed: int,
    n_splits: int = 5,
    num_class: int,
) -> tuple[float, float]:
    """5-fold stratified CV using accuracy as the primary metric.

    Multi-class AUC is one-vs-rest; we report mean accuracy here.
    Std across folds quantifies stability.
    """
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    scores: list[float] = []
    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y), start=1):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        clf = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=num_class,
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            enable_categorical=True,
            tree_method="hist",
            random_state=seed,
            n_jobs=-1,
            eval_metric="mlogloss",
        )
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_val)
        acc = float((preds == y_val.to_numpy()).mean())
        scores.append(acc)
        logger.debug("CV fold %d accuracy: %.4f", fold, acc)
    return float(np.mean(scores)), float(np.std(scores))


def fit_final_multiclass(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    *,
    seed: int,
    num_class: int,
) -> xgb.XGBClassifier:
    """Final softmax classifier fit on full training data."""
    clf = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=num_class,
        n_estimators=300,
        max_depth=4,
        learning_rate=0.1,
        enable_categorical=True,
        tree_method="hist",
        random_state=seed,
        n_jobs=-1,
        eval_metric="mlogloss",
    )
    clf.fit(X_train, y_train)
    return clf


# ---------- Reporting ----------

def _per_class_auc(
    y_true: np.ndarray,
    proba: np.ndarray,
    class_names: list[str],
) -> dict[str, float]:
    """One-vs-rest AUC per class. NaN if class has only one label in y_true."""
    out: dict[str, float] = {}
    for i, name in enumerate(class_names):
        y_binary = (y_true == i).astype(int)
        if y_binary.sum() == 0 or y_binary.sum() == len(y_binary):
            out[name] = float("nan")
            continue
        out[name] = float(roc_auc_score(y_binary, proba[:, i]))
    return out


def _save_summary_plot(
    shap_values: np.ndarray | list[np.ndarray],
    X_test: pd.DataFrame,
    output_path: Path,
) -> None:
    """For multi-class, shap.summary_plot averages |SHAP| across classes
    when given a list of per-class arrays."""
    fig = plt.figure(figsize=(10, 8))
    shap.summary_plot(
        shap_values, X_test, max_display=20, show=False, plot_size=None,
    )
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def _aggregate_shap_importance(
    shap_values_per_class: list[np.ndarray] | np.ndarray,
    feature_names: list[str],
) -> list[tuple[str, float]]:
    """Mean |SHAP| across all classes — global importance ranking."""
    if isinstance(shap_values_per_class, list):
        stacked = np.stack(shap_values_per_class, axis=0)  # (K, N, F)
        global_imp = np.abs(stacked).mean(axis=(0, 1))      # (F,)
    else:
        # Some shap versions return (N, F, K); reduce over both samples + classes
        arr = np.asarray(shap_values_per_class)
        if arr.ndim == 3:
            global_imp = np.abs(arr).mean(axis=(0, 2))
        else:
            global_imp = np.abs(arr).mean(axis=0)
    indexed = list(zip(feature_names, global_imp.tolist(), strict=True))
    return sorted(indexed, key=lambda x: x[1], reverse=True)


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def _write_report(
    output_path: Path,
    *,
    target_label: str,
    n_train: int,
    n_test: int,
    class_names: list[str],
    class_counts: dict[str, int],
    cv_acc_mean: float,
    cv_acc_std: float,
    test_acc: float,
    per_class_auc: dict[str, float],
    top_features: list[tuple[str, float]],
) -> None:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Multi-class target: `{target_label}`",
        "",
        f"_Generated {now}_",
        "",
        "## Run metadata",
        "",
        f"- **Target**: `{target_label}` (one-of-K softmax classification)",
        f"- **Classes**: {len(class_names)}",
        f"- **Training samples**: {n_train:,}",
        f"- **Holdout test samples**: {n_test:,}",
        "",
        "### Class distribution (training set)",
        "",
        "| Class | Count | Share |",
        "|---|---|---|",
    ]
    total = sum(class_counts.values())
    for name in class_names:
        c = class_counts.get(name, 0)
        lines.append(f"| `{name}` | {c} | {100 * c / total:.1f}% |")
    lines.extend([
        "",
        "## Model performance",
        "",
        f"- **CV accuracy** (5-fold stratified): {cv_acc_mean:.4f} ± {cv_acc_std:.4f}",
        f"- **Holdout test accuracy**: {test_acc:.4f}",
        "",
        "Random baseline accuracy = 1 / num_classes. Anything above that is signal.",
        "Class-weighted argmax favours majority classes — see per-class AUC below",
        "for a fairer view of model performance on rare classes.",
        "",
        "### Per-class one-vs-rest AUC",
        "",
        "| Class | AUC |",
        "|---|---|",
    ])
    for name in class_names:
        auc = per_class_auc.get(name, float("nan"))
        auc_str = "n/a" if np.isnan(auc) else f"{auc:.4f}"
        lines.append(f"| `{name}` | {auc_str} |")

    lines.extend([
        "",
        "## Top features (global, mean |SHAP| across classes)",
        "",
        "| Rank | Feature | Importance |",
        "|---|---|---|",
    ])
    for rank, (feature, imp) in enumerate(top_features[:20], start=1):
        lines.append(f"| {rank} | `{feature}` | {imp:.4f} |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- Main ----------

def run_training(
    *,
    features_parquet: Path,
    targets_csv: Path | None,
    target_column: str,
    output_root: Path,
    seed: int = 42,
    drop_other: bool = False,
    in_parquet_label: bool = False,
    min_class_count: int = 50,
) -> Path:
    """End-to-end multi-class softmax classifier.

    Two label-source modes:

    - ``in_parquet_label=False`` (legacy): ``targets_csv`` is joined on
      ``name`` to populate the label column.
    - ``in_parquet_label=True`` (per-event corpus): ``target_column``
      already exists in the parquet (e.g. ``event_root`` for the per-event
      corpus). Rare classes with fewer than ``min_class_count`` samples
      are collapsed into "other".
    """
    if not features_parquet.exists():
        raise FileNotFoundError(f"features parquet missing: {features_parquet}")

    logger.info("loading features from %s", features_parquet)
    df = pd.read_parquet(features_parquet)
    logger.info("loaded %d rows × %d columns", len(df), len(df.columns))

    if in_parquet_label:
        if target_column not in df.columns:
            raise ValueError(
                f"target_column={target_column!r} not in parquet; "
                f"available: {sorted(df.columns)[:20]}..."
            )
        # Normalise the label and collapse rare classes
        df["_label"] = df[target_column].astype(str).str.strip().str.lower()
        counts = df["_label"].value_counts()
        rare = set(counts[counts < min_class_count].index)
        if rare:
            logger.info(
                "collapsing %d rare classes (<%d samples) into 'other'",
                len(rare), min_class_count,
            )
            df.loc[df["_label"].isin(rare), "_label"] = "other"
    else:
        if targets_csv is None:
            raise ValueError("targets_csv required when in_parquet_label=False")
        label_map = load_label_map(targets_csv, target_column)
        # Match the regressor's case-insensitive join — derived CSVs use
        # original names but the multiclass derivation kept original case;
        # do the lowercase join defensively in case derivation conventions
        # diverge between scripts.
        df["_label"] = (
            df["name"].astype(str).str.strip().str.lower()
            .map({k.strip().lower(): v for k, v in label_map.items()})
        )

    before_drop = len(df)
    df = df.dropna(subset=["_label"]).copy()
    if drop_other:
        df = df.loc[df["_label"] != "other"].copy()
    logger.info("after target join: %d rows (dropped %d)", len(df), before_drop - len(df))

    if len(df) < 100:
        raise ValueError(f"only {len(df)} labelled rows; aborting")

    # Label-encode strings → integer class indices for XGBoost
    class_names: list[str] = sorted(df["_label"].unique().tolist())
    label_to_idx = {name: idx for idx, name in enumerate(class_names)}
    y = df["_label"].map(label_to_idx).astype(int)
    class_counts = df["_label"].value_counts().to_dict()
    logger.info("class distribution: %s", class_counts)

    X = select_features(df.drop(columns=["_label"]))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed,
    )

    num_class = len(class_names)
    cv_mean, cv_std = cross_validate_macro_f1(
        X_train, y_train, seed=seed, num_class=num_class,
    )
    logger.info("CV accuracy: %.4f ± %.4f", cv_mean, cv_std)

    model = fit_final_multiclass(
        X_train, y_train, seed=seed, num_class=num_class,
    )
    test_preds = model.predict(X_test)
    test_proba = model.predict_proba(X_test)
    test_acc = float((test_preds == y_test.to_numpy()).mean())
    logger.info("holdout test accuracy: %.4f", test_acc)

    per_class_auc = _per_class_auc(y_test.to_numpy(), test_proba, class_names)
    logger.info("per-class AUC: %s", per_class_auc)

    # Confusion matrix
    cm = confusion_matrix(y_test, test_preds, labels=list(range(num_class)))

    # SHAP — for multi-class, TreeExplainer returns a list of (n_samples, n_features)
    # arrays, one per class.
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    feature_names = list(X.columns)
    ranked = _aggregate_shap_importance(shap_values, feature_names)

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_target = "".join(c if c.isalnum() else "_" for c in target_column)
    run_dir = output_root / f"multiclass_{safe_target}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    model.save_model(str(run_dir / "model.json"))
    _write_inference_schema(X, run_dir)
    _write_csv(
        run_dir / "feature_importance.csv",
        ["rank", "feature", "mean_abs_shap"],
        [[i + 1, f, f"{imp:.6f}"] for i, (f, imp) in enumerate(ranked)],
    )
    _write_csv(
        run_dir / "per_class_auc.csv",
        ["class", "auc", "support"],
        [
            [name, per_class_auc.get(name, float("nan")), class_counts.get(name, 0)]
            for name in class_names
        ],
    )
    _write_csv(
        run_dir / "confusion_matrix.csv",
        ["true_class", *class_names],
        [[name, *row.tolist()] for name, row in zip(class_names, cm, strict=True)],
    )
    _save_summary_plot(shap_values, X_test, run_dir / "shap_summary.png")
    _write_report(
        run_dir / "report.md",
        target_label=target_column,
        n_train=len(X_train),
        n_test=len(X_test),
        class_names=class_names,
        class_counts=class_counts,
        cv_acc_mean=cv_mean,
        cv_acc_std=cv_std,
        test_acc=test_acc,
        per_class_auc=per_class_auc,
        top_features=ranked,
    )

    # Save the sklearn classification report as a sidecar text file too
    cr = classification_report(
        y_test, test_preds,
        target_names=class_names,
        zero_division=0,
    )
    (run_dir / "classification_report.txt").write_text(cr, encoding="utf-8")

    logger.info("run complete; artifacts in %s", run_dir)
    return run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.train_multiclass",
        description="Train an XGBoost softmax classifier on a Vedic Tensor parquet.",
    )
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument(
        "--targets-csv", type=Path, default=None,
        help="External labels CSV joined by name. Omit when "
             "--in-parquet-label is set.",
    )
    parser.add_argument("--target-column", type=str, default="vocation_root")
    parser.add_argument(
        "--in-parquet-label", action="store_true",
        help="Read target-column directly from the parquet (e.g. "
             "event_root for the per-event corpus). When set, --targets-csv "
             "must be omitted.",
    )
    parser.add_argument(
        "--min-class-count", type=int, default=50,
        help="When --in-parquet-label is set, collapse classes with fewer "
             "than this many samples into 'other'.",
    )
    parser.add_argument("--output", type=Path, default=Path("data/ml_runs"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--drop-other", action="store_true",
        help="Exclude the 'other' catch-all class so the model only sees "
             "rows with a real label.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.in_parquet_label and args.targets_csv is not None:
        parser.error("--in-parquet-label is incompatible with --targets-csv")
    if not args.in_parquet_label and args.targets_csv is None:
        parser.error("--targets-csv is required unless --in-parquet-label is set")

    try:
        run_dir = run_training(
            features_parquet=args.features,
            targets_csv=args.targets_csv,
            target_column=args.target_column,
            output_root=args.output,
            seed=args.seed,
            drop_other=args.drop_other,
            in_parquet_label=args.in_parquet_label,
            min_class_count=args.min_class_count,
        )
    except Exception as exc:
        logger.error("training failed: %s", exc)
        return 1

    print(f"Run artifacts in: {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
