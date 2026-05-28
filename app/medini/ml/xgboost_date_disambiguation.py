"""Round 11 Phase 8 — Cyclic-date vs chart-features disambiguation.

Controls for sub-year birth-date precision to determine whether the +0.045 AUC
lift from chart features (observed in Phase 8) is a genuine astrological signal
or a cyclic-date confound (Saturn-sign encodes ±2.5yr band, Jupiter-sign ±1yr,
etc.).

Five conditions on Wikidata marriage (n=32,932, person-disjoint 5-fold
StratifiedKFold, seed=42, XGBoost n_est=100 depth=4 lr=0.1):

  A: birth_jd ONLY                                  (Phase 8 control replicated)
  B: birth_jd + birth_month + birth_day_of_year      (explicit cyclic date —
       + birth_day_of_month                           new control)
  C: birth_jd + chart features (28 cols)             (Phase 8 best replicated)
  D: birth_jd + cyclic date + chart features         (THE DECISIVE TEST)
  E: cyclic date ONLY (no birth_jd)                  (sanity check)

Interpretation key
------------------
  D ≈ B (< +0.005 AUC lift from chart features on top of cyclic date)
    → CONFOUND: cyclic date accounts for the lift; no astrological signal.
  D > B by ≥ +0.020 AUC
    → REAL SIGNAL (or era-bias; next stage needed).
  B alone ≥ 0.67
    → Sub-year precision alone explains most of the original lift.

Usage:
    python -m app.medini.ml.xgboost_date_disambiguation
    python -m app.medini.ml.xgboost_date_disambiguation --out-dir data/ml_runs/round11_disambiguation
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import swisseph as swe
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

import xgboost as xgb

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
DEFAULT_OUT_DIR: Final = Path("data/ml_runs/round11_disambiguation")

# 28 flat chart features — identical to xgboost_chart_baseline._FEATURE_COLS
_CHART_COLS: Final[list[str]] = (
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

# Explicit sub-year cyclic date features
_CYCLIC_DATE_COLS: Final[list[str]] = [
    "birth_month",          # 1-12
    "birth_day_of_year",    # 1-366
    "birth_day_of_month",   # 1-31
]


def _derive_cyclic_date_features(birth_jd: pd.Series) -> pd.DataFrame:
    """Derive sub-year date precision features from Julian Day numbers.

    Uses swe.revjul() to convert each JD to (year, month, day) and then
    computes day_of_year via the standard library.  Returns a DataFrame
    with columns: birth_month, birth_day_of_year, birth_day_of_month.

    Args:
        birth_jd: Series of Julian Day float values (must not contain NaN).
    """
    months: list[int] = []
    days_of_year: list[int] = []
    days_of_month: list[int] = []

    for jd_val in birth_jd:
        year, month, day_frac, _ = swe.revjul(float(jd_val), swe.GREG_CAL)
        day = int(day_frac)
        try:
            dt = datetime.date(int(year), int(month), day)
        except ValueError:
            # Malformed JD — fall back to Jan 1 sentinel
            dt = datetime.date(max(1, int(year)), 1, 1)
        months.append(dt.month)
        days_of_year.append(dt.timetuple().tm_yday)
        days_of_month.append(dt.day)

    return pd.DataFrame(
        {
            "birth_month": months,
            "birth_day_of_year": days_of_year,
            "birth_day_of_month": days_of_month,
        },
        index=birth_jd.index,
    )


def _build_wikidata_marriage_dataset(data_dir: Path) -> pd.DataFrame:
    """Return a merged DataFrame ready for all 5 conditions.

    Cohort: all persons whose source is 'wikidata' (n=32,932).
    Label:  1 if the person has any marriage event, 0 otherwise.
    Columns returned:
        person_id, birth_jd, birth_month, birth_day_of_year,
        birth_day_of_month, <28 chart cols>, label
    """
    persons = pd.read_parquet(data_dir / "persons.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    events = pd.read_parquet(data_dir / "events.parquet")

    # Wikidata cohort
    wiki_mask = persons["source"].str.contains("wikidata", case=False, na=False)
    wikidata_ids: set[str] = set(persons.loc[wiki_mask, "person_id"])

    # Label map
    persons_with_marriage: set[str] = set(
        events.loc[
            events["person_id"].isin(wikidata_ids) & (events["event_class"] == "marriage"),
            "person_id",
        ]
    )

    # Base: charts for wikidata persons
    df = charts[charts["person_id"].isin(wikidata_ids)].copy()
    df["label"] = df["person_id"].map(
        lambda pid: 1 if pid in persons_with_marriage else 0
    )

    # Append cyclic date features derived from birth_jd_used (no NaNs)
    cyclic = _derive_cyclic_date_features(df["birth_jd_used"])
    df = pd.concat([df.reset_index(drop=True), cyclic.reset_index(drop=True)], axis=1)

    # Rename for clarity
    df = df.rename(columns={"birth_jd_used": "birth_jd"})

    logger.info(
        "Wikidata marriage dataset: %d persons, %d positive (%.3f rate)",
        len(df), int(df["label"].sum()), df["label"].mean(),
    )
    return df


def _run_cv(
    X: np.ndarray,
    y: np.ndarray,
    skf: StratifiedKFold,
    seed: int,
) -> list[float]:
    """Run stratified k-fold CV and return per-fold AUCs."""
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
        logger.info("  fold %d/%d  AUC=%.4f", fold_idx, skf.n_splits, auc)
    return fold_aucs


def run_disambiguation(
    data_dir: Path = DEFAULT_DATA_DIR,
    n_folds: int = 5,
    seed: int = 42,
) -> dict[str, dict]:
    """Run all 5 disambiguation conditions on identical CV splits.

    Returns a dict keyed by condition label (A-E) with keys:
        feature_set, fold_aucs, mean_auc, std_auc,
        n_total, n_positive, positive_rate.
    """
    df = _build_wikidata_marriage_dataset(data_dir)

    y = df["label"].to_numpy()
    n_total = len(y)
    n_positive = int(y.sum())
    positive_rate = float(y.mean())

    # Build feature matrices for each condition
    birth_jd = df[["birth_jd"]].to_numpy()
    cyclic = df[_CYCLIC_DATE_COLS].to_numpy()
    chart = df[_CHART_COLS].to_numpy()

    conditions: dict[str, tuple[str, np.ndarray]] = {
        "A": ("birth_jd only", birth_jd),
        "B": ("birth_jd + cyclic date", np.hstack([birth_jd, cyclic])),
        "C": ("birth_jd + chart features", np.hstack([birth_jd, chart])),
        "D": ("birth_jd + cyclic date + chart features", np.hstack([birth_jd, cyclic, chart])),
        "E": ("cyclic date only", cyclic),
    }

    # Shared splits — all conditions evaluated on IDENTICAL folds
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)

    results: dict[str, dict] = {}
    for cond_key, (feature_set_name, X) in conditions.items():
        logger.info("Condition %s: %s  [%d features]", cond_key, feature_set_name, X.shape[1])
        fold_aucs = _run_cv(X, y, skf, seed)
        results[cond_key] = {
            "feature_set": feature_set_name,
            "n_features": X.shape[1],
            "fold_aucs": fold_aucs,
            "mean_auc": float(np.mean(fold_aucs)),
            "std_auc": float(np.std(fold_aucs)),
            "n_total": n_total,
            "n_positive": n_positive,
            "positive_rate": positive_rate,
        }
        logger.info(
            "  -> mean AUC=%.4f ± %.4f",
            results[cond_key]["mean_auc"],
            results[cond_key]["std_auc"],
        )

    return results


def _derive_verdict(results: dict[str, dict]) -> str:
    """Derive a verdict string from the 5-condition results.

    Decision rule:
      - If D.mean_auc - B.mean_auc < 0.005: CONFOUND
      - If D.mean_auc - B.mean_auc >= 0.020: REAL SIGNAL
      - Otherwise: AMBIGUOUS
    """
    lift_d_over_b = results["D"]["mean_auc"] - results["B"]["mean_auc"]
    b_auc = results["B"]["mean_auc"]

    if lift_d_over_b < 0.005:
        verdict = "CONFOUND"
        explanation = (
            f"Chart features add only {lift_d_over_b:+.4f} AUC on top of explicit cyclic "
            f"date (condition D {results['D']['mean_auc']:.4f} vs B {b_auc:.4f}). "
            "The +0.045 lift from Round 11 Phase 8 is fully explained by sub-year "
            "birth-date precision encoded in planet signs. Consistent with all 5 "
            "prior null findings. No actionable astrological signal detected."
        )
    elif lift_d_over_b >= 0.020:
        verdict = "REAL SIGNAL"
        explanation = (
            f"Chart features add {lift_d_over_b:+.4f} AUC over explicit cyclic date "
            f"(condition D {results['D']['mean_auc']:.4f} vs B {b_auc:.4f}). "
            "This exceeds the +0.020 threshold; chart features carry information "
            "BEYOND raw date precision. Further analysis (era-bias decomposition, "
            "SHAP inspection) is warranted before claiming genuine astrological signal."
        )
    else:
        verdict = "AMBIGUOUS"
        explanation = (
            f"Chart features add {lift_d_over_b:+.4f} AUC over explicit cyclic date "
            f"(condition D {results['D']['mean_auc']:.4f} vs B {b_auc:.4f}). "
            "This is between the confound threshold (0.005) and the signal threshold "
            "(0.020). Larger dataset or feature ablation per planet required."
        )

    return verdict, explanation, lift_d_over_b, b_auc


def write_artifacts(
    results: dict[str, dict],
    out_dir: Path,
) -> tuple[Path, Path]:
    """Write disambiguation_v1.json and disambiguation_v1.md to out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)

    verdict, explanation, lift_d_over_b, b_auc = _derive_verdict(results)

    # --- JSON artifact ---
    payload = {
        "experiment": "Round 11 Phase 8 cyclic-date disambiguation",
        "verdict": verdict,
        "lift_D_over_B": round(lift_d_over_b, 6),
        "conditions": results,
    }
    json_path = out_dir / "disambiguation_v1.json"
    with open(json_path, "w") as fh:
        json.dump(payload, fh, indent=2)
    logger.info("Wrote %s", json_path)

    # --- Markdown artifact ---
    a = results["A"]
    b = results["B"]
    c = results["C"]
    d = results["D"]
    e = results["E"]

    md_lines = [
        "# Round 11 Disambiguation — Cyclic Date vs Chart Features",
        "",
        f"**Verdict: {verdict}**",
        "",
        explanation,
        "",
        "## AUC Table",
        "",
        "| Cond | Feature set | n_feat | Mean AUC | ± Std |",
        "|------|-------------|--------|----------|-------|",
        f"| A | {a['feature_set']} | {a['n_features']} | {a['mean_auc']:.4f} | {a['std_auc']:.4f} |",
        f"| B | {b['feature_set']} | {b['n_features']} | {b['mean_auc']:.4f} | {b['std_auc']:.4f} |",
        f"| C | {c['feature_set']} | {c['n_features']} | {c['mean_auc']:.4f} | {c['std_auc']:.4f} |",
        f"| D | {d['feature_set']} | {d['n_features']} | {d['mean_auc']:.4f} | {d['std_auc']:.4f} |",
        f"| E | {e['feature_set']} | {e['n_features']} | {e['mean_auc']:.4f} | {e['std_auc']:.4f} |",
        "",
        "## Key Deltas",
        "",
        f"- Lift of chart features over birth_jd alone (C - A): "
        f"{c['mean_auc'] - a['mean_auc']:+.4f} AUC",
        f"- Lift of cyclic date over birth_jd alone (B - A): "
        f"{b['mean_auc'] - a['mean_auc']:+.4f} AUC",
        f"- Lift of chart features over cyclic date (D - B): "
        f"{lift_d_over_b:+.4f} AUC  **<-- decisive test**",
        "",
        "## Dataset",
        "",
        f"- Corpus: Wikidata",
        f"- n_total: {a['n_total']}",
        f"- n_positive (marriage): {a['n_positive']}",
        f"- positive_rate: {a['positive_rate']:.3f}",
        f"- CV: 5-fold StratifiedKFold seed=42, person-disjoint",
        f"- Model: XGBoost n_est=100 depth=4 lr=0.1 seed=42",
        "",
        "## Interpretation",
        "",
        "Condition A replicates the Phase 8 birth_jd baseline. Condition C "
        "replicates the Phase 8 best result. Condition B adds explicit sub-year "
        "date precision (month, day-of-year, day-of-month), which XGBoost's "
        "axis-aligned splits can exploit directly without relying on planet-sign "
        "proxies. If D ≈ B, the cyclic date features fully account for the lift, "
        "meaning chart features contribute no information beyond what the raw "
        "birth date already provides.",
    ]

    md_path = out_dir / "disambiguation_v1.md"
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md_lines) + "\n")
    logger.info("Wrote %s", md_path)

    return json_path, md_path


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--n-folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s | %(message)s",
    )

    results = run_disambiguation(
        data_dir=args.data_dir,
        n_folds=args.n_folds,
        seed=args.seed,
    )

    verdict, explanation, lift_d_over_b, b_auc = _derive_verdict(results)

    print("\n=== Round 11 Disambiguation ===")
    print(f"{'Cond':<4} {'Feature set':<45} {'n_feat':>6} {'Mean AUC':>9} {'±Std':>7}")
    print("-" * 76)
    for key in ("A", "B", "C", "D", "E"):
        r = results[key]
        print(
            f"{key:<4} {r['feature_set']:<45} {r['n_features']:>6} "
            f"{r['mean_auc']:>9.4f} {r['std_auc']:>7.4f}"
        )
    print()
    print(f"Lift D over B (decisive): {lift_d_over_b:+.4f}")
    print(f"VERDICT: {verdict}")
    print()
    print(explanation)

    json_path, md_path = write_artifacts(results, args.out_dir)
    print(f"\nArtifacts written to:\n  {json_path}\n  {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
