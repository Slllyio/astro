"""Tier 1 §4: per-event-subtype outcome analysis.

For event classes whose `event_subtype` carries Positive / Negative
(or analogous valence) labels — marriage (Positive=lasting,
Negative=divorce-ending), health (Negative=disease), work (Prize /
New Job / etc.) — we train per-class XGBoost models that predict
the subtype, not the occurrence.

Rationale: a chart with Saturn-Venus drishti causes marriage
*delay*, but conditional on a marriage event occurring, does it
predict Positive vs Negative outcome? The Phase-6 finding tells us
WHO gets married. This analysis tells us WHICH KIND of marriage
occurs.

For each consequent event class with a Positive/Negative-ish
subtype split:
1. Restrict cohort to people with at least one event of that class.
2. Label them by their FIRST event's subtype (positive=1, negative=0).
3. Train XGBoost binary classifier on natal features.
4. Report 5-fold CV ROC-AUC + top SHAP features.
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

from app.medini.ml.train_classifier import NON_FEATURE_COLUMNS, select_features

logger = logging.getLogger(__name__)


# Subtype valence mappings: which subtypes count as POSITIVE (1) vs
# NEGATIVE (0). Derived from observed event_subtype distributions.
SUBTYPE_VALENCE: dict[str, dict[str, int]] = {
    "marriage": {
        "positive": 1, "negative": 0,
    },
    "health": {
        "negative": 0, "medical procedure": 0, "medical diagnosis": 0,
        "accident (non-fatal)": 0, "acute illness": 0,
        "healing": 1, "recovery": 1,
    },
    "work": {
        "prize": 1, "published/ exhibited/ released": 1,
        "gain social status": 1, "new career": 1, "new job": 1,
        "fired/ laid off / quit": 0, "demotion": 0, "fall from status": 0,
    },
    "relationship": {
        "marriage": 1, "begin significant relationship": 1,
        "meet a significant person": 1,
        "end significant relationship": 0, "divorce dates": 0,
        "break-up": 0,
    },
}


def _build_subtype_cohort(
    natal: pd.DataFrame, events: pd.DataFrame, ev_class: str,
) -> pd.DataFrame:
    """Return (natal_cohort, y) where y is the subtype valence label
    for the person's FIRST event of this class.

    Drops rows whose subtype isn't in the valence map.
    """
    valence_map = SUBTYPE_VALENCE.get(ev_class.lower(), {})
    if not valence_map:
        raise ValueError(f"no subtype valence mapping for {ev_class!r}")
    sub = events.loc[events["root_lower"] == ev_class.lower()].copy()
    sub = sub.dropna(subset=["event_subtype"])
    sub["subtype_clean"] = (
        sub["event_subtype"].astype(str).str.strip().str.lower()
    )
    sub = sub[sub["subtype_clean"].isin(valence_map.keys())]
    sub["valence"] = sub["subtype_clean"].map(valence_map).astype(int)
    sub_first = sub.sort_values("event_date").drop_duplicates(
        subset="_n", keep="first",
    )
    natal_idx = natal.set_index("_n")
    joined = sub_first.set_index("_n").join(natal_idx, how="inner", rsuffix="_natal")
    return joined.reset_index()


def _eval_subtype_classifier(
    df: pd.DataFrame, seed: int = 42,
) -> dict[str, float]:
    """Train + 5-fold CV ROC-AUC for predicting `valence` from natal features."""
    y = df["valence"].astype(int)
    if y.nunique() < 2:
        return {"auc": float("nan"), "n_rows": len(df),
                "n_positive": int(y.sum()),
                "reason": "single-class target"}
    if y.sum() < 10 or (len(y) - y.sum()) < 10:
        return {"auc": float("nan"), "n_rows": len(df),
                "n_positive": int(y.sum()),
                "reason": "too few of one class"}

    # Drop non-feature cols + subtype-leaking cols
    drop_cols = (set(NON_FEATURE_COLUMNS)
                 | {"valence", "subtype_clean", "_n",
                    "event_date", "event_jd", "birth_jd",
                    "event_root", "event_subtype", "event_subtype_clean",
                    "root_lower", "is_event", "event_year",
                    "event_code", "source_url"})
    drop_cols &= set(df.columns)
    X = select_features(df.drop(columns=list(drop_cols), errors="ignore"))

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    aucs: list[float] = []
    for train_idx, val_idx in cv.split(X, y):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        if y_tr.sum() < 5 or y_val.sum() < 1:
            continue
        scale_pos = float((y_tr == 0).sum()) / max(int(y_tr.sum()), 1)
        clf = xgb.XGBClassifier(
            n_estimators=150, max_depth=4, learning_rate=0.1,
            scale_pos_weight=scale_pos, enable_categorical=True,
            tree_method="hist", random_state=seed, n_jobs=-1,
            eval_metric="logloss",
        )
        clf.fit(X_tr, y_tr)
        proba = clf.predict_proba(X_val)[:, 1]
        try:
            aucs.append(roc_auc_score(y_val, proba))
        except ValueError:
            continue
    return {
        "auc": float(np.mean(aucs)) if aucs else float("nan"),
        "auc_std": float(np.std(aucs)) if aucs else float("nan"),
        "n_rows": len(df),
        "n_positive": int(y.sum()),
        "n_negative": int(len(y) - y.sum()),
    }


def run_subtype_analysis(
    *,
    natal_parquet: Path,
    events_csv: Path,
    output_dir: Path,
    seed: int = 42,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("loading natal + events ...")
    natal = pd.read_parquet(natal_parquet)
    natal["_n"] = natal["name"].astype(str).str.strip().str.lower()
    natal = natal.drop_duplicates(subset="_n").reset_index(drop=True)
    events = pd.read_csv(events_csv)
    events["_n"] = events["name"].astype(str).str.strip().str.lower()
    events["root_lower"] = events["event_root"].astype(str).str.lower().str.strip()
    events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")

    results = []
    for ev_class in SUBTYPE_VALENCE.keys():
        logger.info("=== %s ===", ev_class)
        try:
            df = _build_subtype_cohort(natal, events, ev_class)
        except Exception as exc:
            logger.error("failed to build cohort for %s: %s", ev_class, exc)
            continue
        if len(df) < 50:
            logger.warning(
                "  skip %s: only %d rows after valence-filtered join",
                ev_class, len(df),
            )
            continue
        logger.info("  cohort: %d rows  (positive=%d, negative=%d)",
                    len(df), int(df["valence"].sum()),
                    int(len(df) - df["valence"].sum()))
        res = _eval_subtype_classifier(df, seed=seed)
        res["event_class"] = ev_class
        results.append(res)
        logger.info(
            "  AUC=%.4f ± %.4f",
            res["auc"] if not np.isnan(res["auc"]) else float("nan"),
            res.get("auc_std", float("nan")),
        )

    csv_path = output_dir / "subtype_outcome_classifier.csv"
    if not results:
        logger.warning("no results"); return
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(results[0].keys()), extrasaction="ignore",
        )
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    logger.info("wrote %s", csv_path)

    # Report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Tier-1 §4 — Per-event-subtype outcome analysis",
        "",
        f"_Generated {now}_",
        "",
        "For each event class with a Positive/Negative-valence",
        "`event_subtype` column, we train an XGBoost classifier to",
        "predict the subtype valence from the person's natal chart.",
        "",
        "This is the **outcome-prediction layer** that sits on top of",
        "Phase 6's occurrence-prediction. Phase 6 tells us WHO marries.",
        "This tells us WHICH KIND of marriage occurs given that one does.",
        "",
        "## 5-fold CV ROC-AUC per event class",
        "",
        "| Event class | N rows | Positive | Negative | CV AUC | Std |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['event_class']} | {r['n_rows']} | {r.get('n_positive', '?')} | "
            f"{r.get('n_negative', '?')} | "
            f"{r.get('auc', float('nan')):.4f} | "
            f"{r.get('auc_std', float('nan')):.4f} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- AUC ≈ 0.50 → chart cannot predict subtype given the event",
        "  occurs; subtype is determined by non-chart factors.",
        "- AUC > 0.60 → chart carries subtype-prediction signal "
        "(astrological subtype theory is at least partially right).",
        "- AUC > 0.70 → strong subtype signal — chart determines the",
        "  outcome flavor, not just the occurrence.",
    ])
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report.md")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.subtype_analysis",
    )
    parser.add_argument(
        "--natal", type=Path,
        default=Path("app/medini/data/ml_astro_round5.parquet"),
    )
    parser.add_argument(
        "--events", type=Path,
        default=Path("data/astro_databank/events_all.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/tier1_subtype_analysis/"),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_subtype_analysis(
        natal_parquet=args.natal,
        events_csv=args.events,
        output_dir=args.output,
    )
    print(f"Subtype analysis artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
