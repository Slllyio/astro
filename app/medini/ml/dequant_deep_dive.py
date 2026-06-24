"""De-quantization deep dive — per-class breakdown + feature-group ablation.

The basic §3.1 probe showed discrete-only (0.348) beats continuous-only
(0.334) by +0.014 on aggregate multi-class accuracy. That's the headline
finding, but it averages across 27 event classes and lumps all
"continuous" features together vs all "discrete" features together.

This deep dive answers:
1. **Per-class breakdown**: are some event classes better with discrete?
   Others with continuous? Or is the +0.014 uniform across classes?
2. **Per-feature-group ablation**: of the discrete buckets (signs,
   nakshatras, houses, dispositors, drishti, yogas, panchanga, ...),
   which actually carry signal? Drop each group; measure the AUC drop.
3. **Per-continuous-group ablation**: of the continuous values
   (raw longitudes, aspect orbs, house_pos, nak_pos, divisional
   degrees, kinematics), which matter most?

The answers determine: should we keep all features, drop redundant
ones, or use continuous-only for specific event classes?

This expands on app/medini/ml/dequantization_probe.py (§3.1).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from app.medini.ml.dequantization_probe import (
    _classify_column,
    _fix_nak_pos,
    _prep_features,
    partition_features,
)
from app.medini.ml.train_classifier import select_features
# Round 8: feature-group definitions now live in feature_groups.py
# (single source of truth for ablation runs + production lean-feature
# drop list applied in train_classifier.select_features).
from app.medini.ml.feature_groups import (
    DISCRETE_GROUPS,
    CONTINUOUS_GROUPS,
    _resolve_group_cols,
)

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


def _eval_multiclass(
    df: pd.DataFrame, cols: list[str], y: pd.Series,
    n_classes: int, seed: int = 42, n_splits: int = 5,
) -> dict[str, float]:
    """5-fold CV accuracy + per-class OvR AUC."""
    if not cols:
        return {"accuracy": 0.0, "n_cols": 0}
    X = _prep_features(df, cols)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    scores: list[float] = []
    per_class_aucs: dict[int, list[float]] = {}
    for train_idx, val_idx in cv.split(X, y):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        clf = xgb.XGBClassifier(
            objective="multi:softprob", num_class=n_classes,
            n_estimators=120, max_depth=4, learning_rate=0.1,
            enable_categorical=True, tree_method="hist",
            random_state=seed, n_jobs=-1, eval_metric="mlogloss",
        )
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_val)
        acc = float((preds == y_val.to_numpy()).mean())
        scores.append(acc)
        proba = clf.predict_proba(X_val)
        for c in range(n_classes):
            y_bin = (y_val.to_numpy() == c).astype(int)
            if y_bin.sum() == 0 or y_bin.sum() == len(y_bin):
                continue
            try:
                auc = float(roc_auc_score(y_bin, proba[:, c]))
            except ValueError:
                continue
            per_class_aucs.setdefault(c, []).append(auc)
    return {
        "accuracy": float(np.mean(scores)),
        "n_cols": len(cols),
        "per_class_auc": {c: float(np.mean(aucs))
                          for c, aucs in per_class_aucs.items()},
    }


def run_deep_dive(
    *,
    corpus_parquet: Path,
    output_dir: Path,
    min_class_count: int = 100,
    seed: int = 42,
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
    class_to_idx = {n: i for i, n in enumerate(class_names)}
    y = df["_label"].map(class_to_idx).astype(int)
    n_classes = len(class_names)
    logger.info("rows=%d  classes=%d", len(df), n_classes)

    cont_cols, disc_cols = partition_features(df)
    cont_cols, disc_cols = _fix_nak_pos(cont_cols, disc_cols)
    both_cols = cont_cols + disc_cols
    logger.info("base partition: cont=%d disc=%d both=%d",
                len(cont_cols), len(disc_cols), len(both_cols))

    # PART A: Per-class breakdown — re-run the §3.1 probe but report
    # per-class OvR AUC instead of just aggregate accuracy
    logger.info("=== PART A: per-class breakdown ===")
    baselines = {}
    for name, cols in (
        ("continuous_only", cont_cols),
        ("discrete_only", disc_cols),
        ("both", both_cols),
    ):
        logger.info("evaluating %s (%d cols) ...", name, len(cols))
        baselines[name] = _eval_multiclass(df, cols, y, n_classes, seed=seed)
        logger.info("  %s: accuracy=%.4f", name, baselines[name]["accuracy"])

    # PART B: per-feature-group ablation on the FULL feature set
    # "drop_group" runs: drop one group, evaluate, measure accuracy drop
    logger.info("=== PART B: drop-one-group ablation (full feature set baseline) ===")
    full_eval = _eval_multiclass(df, both_cols, y, n_classes, seed=seed)
    baseline_acc = full_eval["accuracy"]
    logger.info("full-set baseline accuracy: %.4f", baseline_acc)

    ablation_results = []
    all_groups = list(DISCRETE_GROUPS.keys()) + list(CONTINUOUS_GROUPS.keys())
    for group_name in all_groups:
        group_cols = _resolve_group_cols(group_name, both_cols)
        if not group_cols:
            continue
        remaining = [c for c in both_cols if c not in group_cols]
        eval_result = _eval_multiclass(df, remaining, y, n_classes, seed=seed)
        delta = eval_result["accuracy"] - baseline_acc
        ablation_results.append({
            "group": group_name,
            "kind": "discrete" if group_name in DISCRETE_GROUPS else "continuous",
            "n_dropped": len(group_cols),
            "accuracy_without_group": eval_result["accuracy"],
            "delta_from_baseline": delta,
        })
        logger.info(
            "  drop %-30s (%d cols): acc=%.4f  Δ=%+.4f",
            group_name, len(group_cols),
            eval_result["accuracy"], delta,
        )

    # Sort by accuracy drop magnitude (most important = biggest drop when removed)
    ablation_results.sort(key=lambda x: x["delta_from_baseline"])

    # PART C: write CSVs + report
    csv_path = output_dir / "ablation_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["group", "kind", "n_dropped",
                           "accuracy_without_group", "delta_from_baseline"],
        )
        writer.writeheader()
        for r in ablation_results:
            writer.writerow(r)
    logger.info("wrote %s", csv_path)

    # Per-class table (continuous vs discrete vs both)
    per_class_path = output_dir / "per_class_breakdown.csv"
    with per_class_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "class_idx", "class_name",
            "auc_continuous", "auc_discrete", "auc_both",
            "best_kind", "delta_cont_minus_disc",
        ])
        for c_idx, c_name in enumerate(class_names):
            auc_c = baselines["continuous_only"]["per_class_auc"].get(c_idx, np.nan)
            auc_d = baselines["discrete_only"]["per_class_auc"].get(c_idx, np.nan)
            auc_b = baselines["both"]["per_class_auc"].get(c_idx, np.nan)
            delta = auc_c - auc_d if not (np.isnan(auc_c) or np.isnan(auc_d)) else np.nan
            best = "continuous" if (not np.isnan(delta) and delta > 0.005) else (
                "discrete" if (not np.isnan(delta) and delta < -0.005) else "tied"
            )
            writer.writerow([
                c_idx, c_name,
                f"{auc_c:.4f}" if not np.isnan(auc_c) else "",
                f"{auc_d:.4f}" if not np.isnan(auc_d) else "",
                f"{auc_b:.4f}" if not np.isnan(auc_b) else "",
                best,
                f"{delta:+.4f}" if not np.isnan(delta) else "",
            ])
    logger.info("wrote %s", per_class_path)

    # Markdown report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = output_dir / "report.md"
    lines = [
        "# De-quantization Deep Dive",
        "",
        f"_Generated {now}_",
        "",
        "## Setup",
        f"- Event corpus: {len(df):,} events × {n_classes} classes",
        f"- Continuous cols: {len(cont_cols)}",
        f"- Discrete cols:   {len(disc_cols)}",
        f"- Total cols:      {len(both_cols)}",
        "",
        "## Part A: aggregate baselines",
        "",
        "| Feature set | N cols | CV accuracy |",
        "|---|---|---|",
        f"| Continuous-only | {baselines['continuous_only']['n_cols']} | {baselines['continuous_only']['accuracy']:.4f} |",
        f"| Discrete-only   | {baselines['discrete_only']['n_cols']} | {baselines['discrete_only']['accuracy']:.4f} |",
        f"| Both            | {baselines['both']['n_cols']} | {baselines['both']['accuracy']:.4f} |",
        "",
        f"Random baseline: 1/{n_classes} = {1 / n_classes:.4f}",
        "",
        "## Part A: per-class breakdown",
        "",
        "Per-class one-vs-rest AUCs for each feature set. **delta** > 0 = "
        "continuous wins for that class; delta < 0 = discrete wins.",
        "",
        "| Class | AUC cont. | AUC disc. | AUC both | Best | Δ (cont-disc) |",
        "|---|---|---|---|---|---|",
    ]
    for c_idx, c_name in enumerate(class_names):
        auc_c = baselines["continuous_only"]["per_class_auc"].get(c_idx, np.nan)
        auc_d = baselines["discrete_only"]["per_class_auc"].get(c_idx, np.nan)
        auc_b = baselines["both"]["per_class_auc"].get(c_idx, np.nan)
        delta = auc_c - auc_d if not (np.isnan(auc_c) or np.isnan(auc_d)) else np.nan
        best = "cont." if (not np.isnan(delta) and delta > 0.005) else (
            "disc." if (not np.isnan(delta) and delta < -0.005) else "tied"
        )
        c_str = f"{auc_c:.3f}" if not np.isnan(auc_c) else "—"
        d_str = f"{auc_d:.3f}" if not np.isnan(auc_d) else "—"
        b_str = f"{auc_b:.3f}" if not np.isnan(auc_b) else "—"
        delta_str = f"{delta:+.3f}" if not np.isnan(delta) else "—"
        lines.append(f"| `{c_name}` | {c_str} | {d_str} | {b_str} | {best} | {delta_str} |")

    lines.extend([
        "",
        "## Part B: drop-one-group ablation",
        "",
        "Sorted by impact: most-negative `Δ` = group is most important "
        "(its removal hurts accuracy the most).",
        "",
        "| Group | Kind | N cols | Acc w/o group | Δ from baseline |",
        "|---|---|---|---|---|",
    ])
    for r in ablation_results:
        lines.append(
            f"| `{r['group']}` | {r['kind']} | {r['n_dropped']} | "
            f"{r['accuracy_without_group']:.4f} | {r['delta_from_baseline']:+.4f} |"
        )

    lines.extend([
        "",
        "## Interpretation guide",
        "",
        "- **Per-class breakdown** answers: are some event classes better-",
        "  predicted by continuous features vs discrete? (Answer: see the "
        "'Best' column.)",
        "- **Ablation** answers: which feature groups matter most? The "
        "groups with the biggest negative Δ are load-bearing.",
        "- A group with Δ near 0 is redundant (other features cover it).",
        "- A group with positive Δ when removed is actively HURTING the "
        "model (e.g., spurious features that confuse XGBoost).",
        "",
        "Full ablation: `ablation_results.csv`.",
        "Per-class: `per_class_breakdown.csv`.",
    ])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dequant_deep_dive",
    )
    parser.add_argument(
        "--corpus", type=Path,
        default=Path("app/medini/data/event_corpus_round5_all.parquet"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/dequant_deep_dive/"),
    )
    parser.add_argument("--min-class-count", type=int, default=100)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_deep_dive(
        corpus_parquet=args.corpus,
        output_dir=args.output,
        min_class_count=args.min_class_count,
    )
    print(f"Deep-dive artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
