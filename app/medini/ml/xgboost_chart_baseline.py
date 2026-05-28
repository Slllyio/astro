"""Phase 8 - XGBoost baseline on FLAT chart features for apples-to-apples R-GCN comparison.

The R-GCN MVP (rgcn_baseline.py) tests whether a relational heterograph
representation extracts signal that flat tabular ML destroys. This module
is its baseline counterpart: same task (binary "did this person have an
event of class X?"), same person-disjoint split, same dataset (events.parquet
filtered to persons with any event), but features are the **flat** chart:

  * 9 graha signs (1-12)        ->  9 cols
  * 9 graha houses (1-12)       ->  9 cols
  * 9 graha nakshatras (0-26)   ->  9 cols
  * 1 ascendant sign            ->  1 col
  Total: 28 columns. CRITICALLY excludes birth_jd / birth_year.

The Round-9 finding showed that ``person_only`` baselines (birth_year +
birth_jd) already explained 0.85-0.94 AUC. We are testing the chart
features ALONE, without date confounding, so the AUC here represents the
TRUE structural signal.

If XGBoost AUC ~~ R-GCN AUC -> representation hypothesis falsified.
If XGBoost AUC <  R-GCN AUC by >= 0.01 -> graph structure helped.

Usage:
    python -m app.medini.ml.xgboost_chart_baseline --event-class marriage
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

import xgboost as xgb

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")

# 28 flat features per chart (NO birth_year / birth_jd to prevent date leakage).
_FEATURE_COLS: Final[list[str]] = (
    ["asc_sign"]
    + [f"{g}_sign" for g in (
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
    )]
    + [f"{g}_house" for g in (
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
    )]
    + [f"{g}_nakshatra" for g in (
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
    )]
)


def _build_labels(events: pd.DataFrame, persons_with_any_event: set[str], event_class: str) -> dict[str, int]:
    """Same labeling logic as the R-GCN dataset: binary did-have-event."""
    persons_with_target = set(
        events.loc[events["event_class"] == event_class, "person_id"]
    )
    return {p: int(p in persons_with_target) for p in persons_with_any_event}


def run_xgboost_baseline(
    event_class: str,
    data_dir: Path = DEFAULT_DATA_DIR,
    n_folds: int = 5,
    seed: int = 42,
) -> dict[str, float | list[float]]:
    """Cross-validated XGBoost AUC on flat chart features."""
    charts = pd.read_parquet(data_dir / "charts.parquet")
    events = pd.read_parquet(data_dir / "events.parquet")

    persons_with_any = set(events["person_id"].unique())
    label_map = _build_labels(events, persons_with_any, event_class)

    df = charts[charts["person_id"].isin(persons_with_any)].copy()
    df["label"] = df["person_id"].map(label_map)
    df = df.dropna(subset=["label"])

    X = df[_FEATURE_COLS].to_numpy()
    y = df["label"].to_numpy()
    logger.info(
        "XGBoost baseline: %d persons (%d positive, %.3f rate), %d features",
        len(y), int(y.sum()), y.mean(), X.shape[1],
    )

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    fold_aucs: list[float] = []
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y), start=1):
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            n_jobs=-1,
            random_state=seed,
            eval_metric="auc",
            verbosity=0,
        )
        model.fit(X[train_idx], y[train_idx])
        proba = model.predict_proba(X[test_idx])[:, 1]
        auc = roc_auc_score(y[test_idx], proba)
        fold_aucs.append(float(auc))
        logger.info("Fold %d/%d  AUC=%.4f", fold_idx, n_folds, auc)

    return {
        "fold_aucs": fold_aucs,
        "mean_auc": float(np.mean(fold_aucs)),
        "std_auc": float(np.std(fold_aucs)),
        "n_total": len(y),
        "n_positive": int(y.sum()),
        "positive_rate": float(y.mean()),
    }


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-class", type=str, default="marriage")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--n-folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-json", type=Path, default=None,
                        help="If set, write the result dict as JSON.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    result = run_xgboost_baseline(
        event_class=args.event_class,
        data_dir=args.data_dir,
        n_folds=args.n_folds,
        seed=args.seed,
    )
    print("\n=== XGBoost flat-chart baseline ===")
    print(f"  event_class: {args.event_class}")
    print(f"  n_total:     {result['n_total']}")
    print(f"  positive_rate: {result['positive_rate']:.3f}")
    print(f"  fold AUCs:   {[f'{a:.4f}' for a in result['fold_aucs']]}")
    print(f"  mean AUC:    {result['mean_auc']:.4f} +- {result['std_auc']:.4f}")

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_json, "w") as f:
            json.dump({"event_class": args.event_class, **result}, f, indent=2)
        logger.info("Wrote %s", args.out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
