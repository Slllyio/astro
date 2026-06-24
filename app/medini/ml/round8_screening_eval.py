"""Round 8.5 Repair 3+4 — Era-stratified eval harness on screening cohorts.

For each screening_<class>.parquet:
  1. Train XGBoost on natal features.
  2. Group-split holdout by name (no person leak).
  3. Report:
     - Overall holdout AUC
     - Per-decade AUC (which eras still carry signal once era is
       controlled by the negative-sampling stratification)
     - Lift over base rate
     - 5-fold CV AUC for variance estimate.

Checkpointed: one (class, variant) per call.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedKFold

from app.medini.ml.feature_groups import resolve_drop_columns

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/ml_runs/round8_screening_eval")
STATE_FILE = OUTPUT_DIR / "state.json"
SEED = 42
N_EST = 100
MAX_DEPTH = 4

CLASS_TO_PARQUET = {
    "Work":                           "screening_work.parquet",
    "Death, Cause unspecified":       "screening_death__cause_unspecified.parquet",
    "Relationship":                   "screening_relationship.parquet",
    "Published/ Exhibited/ Released": "screening_published__exhibited__released.parquet",
    "Prize":                          "screening_prize.parquet",
    "Family":                         "screening_family.parquet",
    "fame":                           "screening_fame.parquet",
    "career":                         "screening_career.parquet",
    "Death by Disease":               "screening_death_by_disease.parquet",
    "Marriage":                       "screening_marriage.parquet",
}

NON_FEATURE = (
    "name", "name_norm", "rodden_rating", "categories_raw", "categories_lower",
    "categories_tokens", "source_url", "is_event", "event_root", "event_subtype",
    "event_date", "event_jd", "birth_jd",
    "is_event_X", "target_class", "neg_ratio",
    "birth_dt", "birth_year", "birth_decade",
)


def _empty_state():
    todo = []
    for cls in CLASS_TO_PARQUET:
        for variant in ("full", "lean"):
            todo.append((cls, variant))
    return {
        "schema_version": 1,
        "todo": todo,
        "results": {},
        "completed": False,
    }


def load_state():
    if STATE_FILE.exists():
        s = json.loads(STATE_FILE.read_text())
        s["todo"] = [tuple(x) for x in s["todo"]]
        return s
    return _empty_state()


def save_state(state):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def _coerce_features(df, lean: bool):
    feature_df = df.drop(columns=list(NON_FEATURE), errors="ignore").copy()
    for col in feature_df.columns:
        s = feature_df[col]
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
            continue
        if isinstance(s.dtype, pd.CategoricalDtype):
            continue
        feature_df[col] = s.astype("category")
    if lean:
        drop_cols = resolve_drop_columns(feature_df.columns.tolist())
        feature_df = feature_df.drop(columns=list(drop_cols))
    return feature_df


def evaluate_cohort(cohort_path: Path, lean: bool) -> dict:
    t0 = time.time()
    df = pd.read_parquet(cohort_path)
    y = df["is_event_X"].astype(int)
    X = _coerce_features(df, lean=lean)
    decades = df["birth_decade"].astype(int)
    names = df["name_norm"]

    # GROUP SPLIT BY NAME — same protocol as Round 8 Phase 0
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SEED)
    train_idx, test_idx = next(gss.split(X, y, groups=names))

    # No leak check
    assert len(set(names.iloc[train_idx]) & set(names.iloc[test_idx])) == 0, "NAME LEAK"

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    dec_test = decades.iloc[test_idx]

    # 5-fold CV on train for variance
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_aucs = []
    for tr, va in cv.split(X_train, y_train):
        scale_pos = float((y_train.iloc[tr] == 0).sum()) / max(int((y_train.iloc[tr] == 1).sum()), 1)
        m = xgb.XGBClassifier(
            n_estimators=N_EST, max_depth=MAX_DEPTH, learning_rate=0.1,
            scale_pos_weight=scale_pos, enable_categorical=True,
            tree_method="hist", random_state=SEED, eval_metric="logloss", n_jobs=-1,
        ).fit(X_train.iloc[tr], y_train.iloc[tr])
        proba = m.predict_proba(X_train.iloc[va])[:, 1]
        cv_aucs.append(float(roc_auc_score(y_train.iloc[va], proba)))

    # Final fit + holdout
    scale_pos = float((y_train == 0).sum()) / max(int((y_train == 1).sum()), 1)
    final = xgb.XGBClassifier(
        n_estimators=N_EST, max_depth=MAX_DEPTH, learning_rate=0.1,
        scale_pos_weight=scale_pos, enable_categorical=True,
        tree_method="hist", random_state=SEED, eval_metric="logloss", n_jobs=-1,
    ).fit(X_train, y_train)
    test_proba = final.predict_proba(X_test)[:, 1]
    holdout_auc = float(roc_auc_score(y_test, test_proba))

    # Per-era AUC on the holdout (only eras with both classes in test)
    per_era = {}
    for dec in sorted(dec_test.unique()):
        mask = (dec_test == dec).to_numpy()
        if mask.sum() < 10:
            continue
        y_era = y_test[mask]
        if y_era.nunique() < 2:
            continue
        p_era = test_proba[mask]
        per_era[int(dec)] = {
            "n": int(mask.sum()),
            "n_pos": int(y_era.sum()),
            "auc": float(roc_auc_score(y_era, p_era)),
        }

    return {
        "n_cols": int(X.shape[1]),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "n_pos_train": int(y_train.sum()),
        "n_pos_test": int(y_test.sum()),
        "base_rate_test": float(y_test.mean()),
        "cv_auc_mean": float(np.mean(cv_aucs)),
        "cv_auc_std": float(np.std(cv_aucs)),
        "holdout_auc": holdout_auc,
        "lift_over_random": holdout_auc - 0.5,
        "per_era_auc": per_era,
        "elapsed_seconds": round(time.time() - t0, 2),
    }


def step_one():
    state = load_state()
    if state["completed"]:
        print("ALL DONE")
        return False
    if not state["todo"]:
        write_report(state)
        state["completed"] = True
        save_state(state)
        print("ALL DONE — wrote report")
        return False

    cls, variant = state["todo"][0]
    parquet_path = Path("app/medini/data") / CLASS_TO_PARQUET[cls]
    if not parquet_path.exists():
        print(f"SKIP {cls}: {parquet_path} not found")
        state["todo"] = state["todo"][1:]
        save_state(state)
        return True

    print(f"EVAL  {cls} ({variant}) ...")
    res = evaluate_cohort(parquet_path, lean=(variant == "lean"))
    res["class"] = cls
    res["variant"] = variant
    state["results"][f"{cls}__{variant}"] = res
    state["todo"] = state["todo"][1:]
    save_state(state)
    print(f"DONE  {cls} ({variant}): holdout_auc={res['holdout_auc']:.4f}  "
          f"cv={res['cv_auc_mean']:.4f}±{res['cv_auc_std']:.4f}  "
          f"base_rate={res['base_rate_test']:.3f}  ({res['elapsed_seconds']:.1f}s)")
    return True


def write_report(state):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = state["results"]
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Round 8.5 — Screening-cohort eval (Repair 1-4 validation)",
        "",
        f"_Generated {now}_",
        "",
        "## Setup",
        "- Per-event-class screening cohorts: positives + era-stratified",
        "  negatives sampled from the 77k unused natal universe.",
        "- One row per unique person (no row-level duplication).",
        "- Pure-natal features only (~535 cols); no transit features.",
        "- Holdout = 20% GroupShuffleSplit by name (no leak).",
        "- CV = 5-fold stratified on train portion.",
        "- XGBoost n_est=100, depth=4, scale_pos_weight balanced.",
        "",
        "## Headline: FULL feature tensor per class",
        "",
        "| Class | n_pos_train | n_pos_test | base_rate | CV AUC | Holdout AUC | Lift over random |",
        "|---|---|---|---|---|---|---|",
    ]

    full_results = []
    for cls in CLASS_TO_PARQUET:
        r = results.get(f"{cls}__full")
        if not r:
            continue
        full_results.append(r)
        lines.append(
            f"| `{cls}` | {r['n_pos_train']} | {r['n_pos_test']} | "
            f"{r['base_rate_test']:.3f} | {r['cv_auc_mean']:.4f}±{r['cv_auc_std']:.4f} | "
            f"**{r['holdout_auc']:.4f}** | {r['lift_over_random']:+.4f} |"
        )

    if full_results:
        mean_auc = float(np.mean([r['holdout_auc'] for r in full_results]))
        mean_lift = mean_auc - 0.5
        lines.extend([
            "",
            f"**Mean holdout AUC across 10 classes: {mean_auc:.4f}  "
            f"(lift over random: {mean_lift:+.4f})**",
            "",
            "Compare to old Phase-1.3 numbers (event-positive-only, no era control):",
            "  - Death AUC 0.94 (now: see above)",
            "  - fame AUC 0.86",
            "  - career AUC 0.86",
            "If the new screening AUCs are 0.55-0.65, the prior 0.86-0.94",
            "numbers were almost entirely era-confounding, as suspected in",
            "the critical review.",
        ])

    lines.extend([
        "",
        "## Per-era holdout AUC (full tensor)",
        "",
        "Should the model still discriminate within a SINGLE birth decade?",
        "If yes → real per-era signal. If AUC collapses to ~0.5 inside a",
        "decade, the across-decade lift was era-decoding, not astrology.",
        "",
    ])
    for r in full_results:
        if not r.get("per_era_auc"):
            continue
        lines.append(f"### `{r['class']}` per-era AUC")
        lines.append("")
        lines.append("| Decade | n | n_pos | AUC |")
        lines.append("|---|---|---|---|")
        for dec, era in sorted(r["per_era_auc"].items()):
            lines.append(f"| {dec} | {era['n']} | {era['n_pos']} | {era['auc']:.4f} |")
        # Mean per-era AUC for this class
        era_aucs = [era['auc'] for era in r["per_era_auc"].values()]
        if era_aucs:
            lines.append(f"\n**Mean per-era AUC for `{r['class']}`: {np.mean(era_aucs):.4f}** "
                         f"(if << overall {r['holdout_auc']:.4f}, the overall AUC was era-driven)")
            lines.append("")

    # LEAN vs FULL comparison
    lines.extend([
        "",
        "## LEAN vs FULL on the screening cohort",
        "",
        "Does the 15-group lean drop list (which failed on the old cohort)",
        "give a lift on the new (era-controlled) cohort? Or does it remain dead?",
        "",
        "| Class | FULL holdout AUC | LEAN holdout AUC | Δ |",
        "|---|---|---|---|",
    ])
    deltas = []
    for cls in CLASS_TO_PARQUET:
        full = results.get(f"{cls}__full", {})
        lean = results.get(f"{cls}__lean", {})
        f_auc = full.get("holdout_auc")
        l_auc = lean.get("holdout_auc")
        if f_auc is None or l_auc is None:
            continue
        d = l_auc - f_auc
        deltas.append(d)
        lines.append(f"| `{cls}` | {f_auc:.4f} | {l_auc:.4f} | {d:+.4f} |")

    if deltas:
        n_win = sum(1 for d in deltas if d > 0)
        lines.extend([
            "",
            f"**LEAN wins: {n_win}/{len(deltas)}  /  Mean Δ: {np.mean(deltas):+.4f}**",
        ])

    (OUTPUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with (OUTPUT_DIR / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class", "variant", "n_cols", "n_train", "n_test",
                    "n_pos_train", "n_pos_test", "base_rate_test",
                    "cv_auc_mean", "cv_auc_std", "holdout_auc", "elapsed_seconds"])
        for r in results.values():
            w.writerow([r["class"], r["variant"], r["n_cols"], r["n_train"],
                        r["n_test"], r["n_pos_train"], r["n_pos_test"],
                        r["base_rate_test"], r["cv_auc_mean"], r["cv_auc_std"],
                        r["holdout_auc"], r["elapsed_seconds"]])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-steps", type=int, default=1)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    for _ in range(args.max_steps):
        if not step_one():
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
