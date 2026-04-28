"""Phase 5C: load a trained XGBoost model and predict for a new birth chart.

Composes the existing primitives:
  - app.medini.etl.feature_engineering.compute_chart_features  for per-chart features
  - app.core.ephemeris_engine.calculate_jd                     for birth-data → JD
  - the run_dir artifacts from app.medini.ml.train_classifier  for the model + schema

Stateless. Loads model + schema from disk on each call (cheap — XGBoost JSON
boosters are <1MB and SHAP is allocated on demand). For high-traffic
deployment, wrap in an LRU cache keyed by run_dir mtime.

Graceful no-model behavior: callers query a target like "politician"; if no
ml_runs subdirectory matches that prefix, NoModelForTarget is raised and
the route layer turns it into a 404 with available_targets in the body.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap
import xgboost as xgb

from app.core.ephemeris_engine import calculate_jd
from app.medini.etl.feature_engineering import compute_chart_features
from app.medini.ml.train_classifier import NON_FEATURE_COLUMNS, select_features

logger = logging.getLogger(__name__)

# Default location of trained-model output directories. Overridable via the
# `output_root` argument on the public functions, which keeps tests
# hermetically pinned to tmp_path.
DEFAULT_OUTPUT_ROOT = Path("data/ml_runs")

# Run-dir naming: "{safe_target}_{YYYYMMDDTHHMMSSZ}". Trainer sanitizes the
# target by replacing non-alphanumerics with underscores, so we apply the
# same transformation when matching.
_RUN_DIR_RE = re.compile(r"^(?P<target>[A-Za-z0-9_]+?)_(?P<ts>\d{8}T\d{6}Z)$")


class NoModelForTarget(Exception):
    """Raised when no trained run exists for the requested target."""


@dataclass(frozen=True)
class TargetRunInfo:
    """Metadata about an available trained run, surfaced for the 404 fallback."""
    target: str          # The sanitized target prefix (e.g. "politician")
    run_dir: Path        # Absolute path to data/ml_runs/{target}_{ts}/
    timestamp: str       # ISO 8601 (UTC) when the run was created


def _sanitize_target(target: str) -> str:
    """Match the trainer's safe_target rule: non-alphanumerics → underscore."""
    return "".join(c if c.isalnum() else "_" for c in target.strip())


def _parse_run_dir(d: Path) -> tuple[str, str] | None:
    """Return (target_prefix, timestamp) for a run directory, or None if it
    doesn't match the trainer's naming convention."""
    m = _RUN_DIR_RE.match(d.name)
    if not m:
        return None
    return m.group("target"), m.group("ts")


def list_available_targets(
    output_root: Path | None = None,
) -> list[TargetRunInfo]:
    """Enumerate every trained run found under output_root.

    One entry per run directory. The 404 fallback uses this so a caller
    asking for an unknown target sees what's actually available without
    needing filesystem access.
    """
    root = output_root if output_root is not None else DEFAULT_OUTPUT_ROOT
    if not root.exists() or not root.is_dir():
        return []
    runs: list[TargetRunInfo] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        parsed = _parse_run_dir(child)
        if parsed is None:
            continue
        target_prefix, ts = parsed
        runs.append(TargetRunInfo(
            target=target_prefix, run_dir=child, timestamp=ts,
        ))
    runs.sort(key=lambda r: r.timestamp, reverse=True)
    return runs


def run_summary(run_dir: Path, top_n_features: int = 5) -> dict[str, Any]:
    """Build a JSON-friendly summary of a single trained run.

    Reads alongside model.json:
      - feature_columns.json: training-time column count
      - feature_importance.csv: top-N features by mean |SHAP|
      - report.md (optional): scrape ROC-AUC + base rate from the headers

    Designed to be cheap (no model load) — used by /medini/runs to render
    a comparison table without paying XGBoost startup cost per run.
    """
    parsed = _parse_run_dir(run_dir)
    target, ts = (parsed[0], parsed[1]) if parsed else ("?", "?")

    summary: dict[str, Any] = {
        "run": run_dir.name,
        "target": target,
        "trained_at_utc": _format_run_timestamp(ts),
        "feature_count": None,
        "top_features": [],
        "metrics": {},
        "has_inference_schema": False,
    }

    columns_path = run_dir / "feature_columns.json"
    if columns_path.exists():
        try:
            cols = json.loads(columns_path.read_text(encoding="utf-8"))
            summary["feature_count"] = len(cols)
            summary["has_inference_schema"] = True
        except (ValueError, json.JSONDecodeError):
            pass

    fi_path = run_dir / "feature_importance.csv"
    if fi_path.exists():
        rows: list[dict[str, str]] = []
        with fi_path.open("r", encoding="utf-8", newline="") as f:
            import csv as _csv
            for row in _csv.DictReader(f):
                rows.append(row)
                if len(rows) >= top_n_features:
                    break
        summary["top_features"] = [
            {
                "rank": int(r["rank"]) if r.get("rank") else None,
                "feature": r.get("feature", ""),
                "mean_abs_shap": float(r["mean_abs_shap"])
                if r.get("mean_abs_shap") else None,
            }
            for r in rows
        ]

    # Best-effort scrape of the auto-generated report.md for AUC + base rate.
    # The trainer writes lines like "Cross-validation ROC-AUC ...: 0.5829 ± 0.0195"
    # and "Base positive rate: 23.946%".
    report_path = run_dir / "report.md"
    if report_path.exists():
        text = report_path.read_text(encoding="utf-8")
        cv_match = re.search(
            r"Cross-validation\s+ROC-AUC[^:]*:\s*([\d.]+)\s*[±+]?\s*([\d.]+)?",
            text,
        )
        if cv_match:
            summary["metrics"]["cv_roc_auc_mean"] = float(cv_match.group(1))
            if cv_match.group(2):
                summary["metrics"]["cv_roc_auc_std"] = float(cv_match.group(2))
        test_match = re.search(
            r"Holdout\s+test\s+ROC-AUC[^:]*:\s*([\d.]+)", text,
        )
        if test_match:
            summary["metrics"]["test_roc_auc"] = float(test_match.group(1))
        base_match = re.search(
            r"Base\s+positive\s+rate[^:]*:\s*([\d.]+)\s*%", text,
        )
        if base_match:
            summary["metrics"]["base_rate"] = float(base_match.group(1)) / 100.0

    return summary


def find_run_for_target(
    target: str,
    output_root: Path | None = None,
) -> Path:
    """Return the most recent run directory whose target prefix matches.

    Matching rule: the trainer-sanitized form of `target` must equal the
    run dir's target prefix exactly (case-insensitive). E.g. user-supplied
    "Politician" → "Politician" → matches a "Politician_*" directory but
    not "athlete_*". This mirrors how the trainer was originally invoked.

    Raises NoModelForTarget if no match exists, with a useful message that
    the route layer can surface verbatim.
    """
    safe = _sanitize_target(target).lower()
    if not safe:
        raise NoModelForTarget("target cannot be empty")
    runs = list_available_targets(output_root)
    matches = [r for r in runs if r.target.lower() == safe]
    if not matches:
        available = ", ".join(sorted({r.target for r in runs})) or "(none)"
        raise NoModelForTarget(
            f"no trained model for target {target!r}. Available: {available}"
        )
    # list_available_targets() is already sorted newest-first.
    return matches[0].run_dir


def _load_schema(run_dir: Path) -> tuple[list[str], dict[str, list[str]]]:
    """Read feature_columns.json + category_levels.json from a run dir.

    Both files are written by train_classifier._write_inference_schema. For
    older runs that predate this artifact, the function returns (empty list,
    empty dict) — the predictor falls back to whatever the new feature row
    naturally produces, which only works if the dtypes line up. To avoid
    surprise inference errors, the route layer treats a missing schema as
    a 410 Gone (legacy run, retrain to enable inference).
    """
    columns_path = run_dir / "feature_columns.json"
    levels_path = run_dir / "category_levels.json"
    if not columns_path.exists() or not levels_path.exists():
        return [], {}
    columns = json.loads(columns_path.read_text(encoding="utf-8"))
    levels = json.loads(levels_path.read_text(encoding="utf-8"))
    return list(columns), {k: list(v) for k, v in levels.items()}


def _load_model(run_dir: Path) -> xgb.XGBClassifier:
    """Reconstruct the booster from model.json. enable_categorical must
    match the trainer; load_model preserves it from the JSON anyway, but
    we set it explicitly for safety."""
    model_path = run_dir / "model.json"
    if not model_path.exists():
        raise NoModelForTarget(f"model.json missing in {run_dir}")
    clf = xgb.XGBClassifier(enable_categorical=True)
    clf.load_model(str(model_path))
    return clf


def _coerce_row_to_schema(
    row: dict[str, Any],
    feature_columns: list[str],
    category_levels: dict[str, list[str]],
) -> pd.DataFrame:
    """Build a 1-row DataFrame whose columns + dtypes exactly match training.

    Three transforms:
      1. Drop label/metadata columns that the trainer also drops.
      2. Reorder columns to feature_columns; missing → NaN, extra → discarded.
      3. For each categorical column, cast to pd.Categorical with the *exact*
         level list from training. Values not seen during training become
         NaN (XGBoost handles this as a missing categorical).
    """
    # Strip label/metadata columns up front (mirrors select_features behaviour).
    feature_dict = {k: v for k, v in row.items() if k not in NON_FEATURE_COLUMNS}

    df = pd.DataFrame([feature_dict])

    # Reorder + add any missing columns as NaN.
    for col in feature_columns:
        if col not in df.columns:
            df[col] = np.nan
    df = df[feature_columns]

    # Apply category dtypes with the trained level lists.
    for col, levels in category_levels.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col].astype("string"), categories=levels)

    # Anything else non-numeric falls through to select_features's catch-all.
    return select_features(df)


def _top_shap_contributors(
    model: xgb.XGBClassifier,
    X: pd.DataFrame,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """Per-feature SHAP contribution for THIS one chart. Returns the top-N
    by |shap_value| with the feature value alongside, so the response reads
    like a story ("Mars in Capricorn contributed +0.18 to the prediction")."""
    explainer = shap.TreeExplainer(model)
    # X has shape (1, n_features); shap_values has the same shape (binary).
    shap_values = explainer.shap_values(X)
    # XGBoost binary returns a single array, multiclass returns a list.
    sv = shap_values if not isinstance(shap_values, list) else shap_values[1]
    sv = np.asarray(sv).reshape(-1)  # flatten to 1D over features

    contributors: list[dict[str, Any]] = []
    for col, shap_val in zip(X.columns, sv):
        raw = X.iloc[0][col]
        # Coerce numpy / pandas scalars to plain Python so JSON serializes.
        if isinstance(raw, pd.Timestamp):
            value: Any = raw.isoformat()
        elif isinstance(raw, (np.integer, np.floating)):
            value = float(raw) if not pd.isna(raw) else None
        elif isinstance(raw, float) and np.isnan(raw):
            value = None
        else:
            value = None if pd.isna(raw) else str(raw) if not isinstance(raw, (int, float, bool, str)) else raw
        contributors.append({
            "feature": col,
            "value": value,
            "shap_value": float(shap_val),
        })

    contributors.sort(key=lambda c: abs(c["shap_value"]), reverse=True)
    return contributors[:top_n]


def predict_for_chart(
    target: str,
    *,
    year: int, month: int, day: int,
    hour: int, minute: int,
    latitude: float, longitude: float,
    tz_offset: float,
    output_root: Path | None = None,
    top_n_contributors: int = 5,
) -> dict[str, Any]:
    """End-to-end inference: birth data → features → probability + SHAP.

    Returns a JSON-friendly dict; the route layer wraps it as-is. Raises
    NoModelForTarget if no trained run matches the target — the route turns
    that into a 404 with available_targets.
    """
    run_dir = find_run_for_target(target, output_root=output_root)

    feature_columns, category_levels = _load_schema(run_dir)
    if not feature_columns:
        raise NoModelForTarget(
            f"run {run_dir.name} predates the inference-schema artifact "
            f"(feature_columns.json missing). Retrain to enable prediction."
        )

    # birth data → julian day → feature row.
    decimal_hour = hour + minute / 60.0
    jd = calculate_jd(year, month, day, decimal_hour, tz_offset)
    feature_row = compute_chart_features(jd, latitude, longitude)

    X = _coerce_row_to_schema(feature_row, feature_columns, category_levels)

    model = _load_model(run_dir)
    proba = float(model.predict_proba(X)[0, 1])

    contributors = _top_shap_contributors(model, X, top_n=top_n_contributors)

    parsed = _parse_run_dir(run_dir)
    run_target, run_ts = (parsed[0], parsed[1]) if parsed else ("?", "?")

    return {
        "target": target,
        "probability": proba,
        "top_contributors": contributors,
        "model": {
            "run_dir": run_dir.name,
            "run_target": run_target,
            "trained_at_utc": _format_run_timestamp(run_ts),
            "feature_count": len(feature_columns),
        },
        "input_jd": jd,
    }


def _format_run_timestamp(ts: str) -> str:
    """Convert "20260101T120000Z" to "2026-01-01T12:00:00Z" for the response."""
    if len(ts) != 16 or ts[8] != "T" or not ts.endswith("Z"):
        return ts
    try:
        d = dt.datetime.strptime(ts, "%Y%m%dT%H%M%SZ")
        return d.replace(tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return ts
