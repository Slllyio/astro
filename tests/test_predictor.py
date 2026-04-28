"""Integration tests for app.medini.ml.predictor (Phase 5C).

Builds a real trained run on a tiny synthetic parquet, then exercises the
predictor against that run end-to-end. Pinned to the Bangalore baseline
birth data so the JD computation is deterministic.

Skipped on installs without xgboost / shap / matplotlib (mirrors the
test_train_classifier guard).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("xgboost")
pytest.importorskip("shap")
pytest.importorskip("matplotlib")

from app.medini.ml.predictor import (  # noqa: E402
    NoModelForTarget,
    _coerce_row_to_schema,
    _format_run_timestamp,
    _parse_run_dir,
    _sanitize_target,
    find_run_for_target,
    list_available_targets,
    predict_for_chart,
)
from app.medini.ml.train_classifier import run_training  # noqa: E402

# Bangalore 1990-07-15 12:00 IST — the canonical anchor used everywhere else.
BANGALORE = {
    "year": 1990, "month": 7, "day": 15,
    "hour": 12, "minute": 0,
    "latitude": 12.9716, "longitude": 77.5946,
    "tz_offset": 5.5,
}


# ---------- helpers ----------

def _build_synthetic_parquet(tmp_path: Path, n_rows: int = 100, seed: int = 7) -> Path:
    """Same shape as test_train_classifier — exercises both the numeric
    path and the categorical path so the saved schema is meaningful."""
    rng = np.random.default_rng(seed)
    n_pos = n_rows // 4
    is_pol = np.zeros(n_rows, dtype=int)
    is_pol[:n_pos] = 1
    rng.shuffle(is_pol)

    rows = []
    for i in range(n_rows):
        lon_sun = rng.uniform(40, 80) if is_pol[i] else rng.uniform(0, 360)
        cats_lower = "vocation : politics : politician" if is_pol[i] else "vocation : other"
        rows.append({
            "name": f"row_{i}",
            "rodden_rating": "AA",
            "categories_raw": "Vocation : Politics" if is_pol[i] else "Vocation : Other",
            "categories_lower": cats_lower,
            "categories_tokens": ["vocation", "politics"] if is_pol[i] else ["vocation"],
            "source_url": f"https://example/row_{i}",
            "lon_sun": lon_sun,
            "lon_moon": float(rng.uniform(0, 360)),
            "lon_saturn": float(rng.uniform(0, 360)),
            "vel_jupiter": float(rng.uniform(-0.2, 0.3)),
            "tattva_sun": rng.choice(["Earth/Fire", "Water/Air", "Fire/Water", "Air/Water"]),
        })
    df = pd.DataFrame(rows)
    pq = tmp_path / "synthetic.parquet"
    df.to_parquet(pq, index=False)
    return pq


@pytest.fixture(scope="module")
def trained_run(tmp_path_factory) -> tuple[Path, Path]:
    """Train once for the whole module — XGBoost+SHAP fit is the slow bit.

    Returns (output_root, run_dir). output_root is a fresh tmp dir that
    contains exactly one ml_runs subdirectory: the freshly-trained run.
    """
    train_dir = tmp_path_factory.mktemp("predictor_train")
    parquet = _build_synthetic_parquet(train_dir, n_rows=120)
    output_root = tmp_path_factory.mktemp("predictor_runs")
    run_dir = run_training(
        features_parquet=parquet,
        target_substring="politician",
        output_root=output_root,
        seed=42,
        top_n_features=5,
        min_rule_impact=0.0,
    )
    return output_root, run_dir


# ---------- _sanitize_target / _parse_run_dir ----------

def test_sanitize_target_replaces_non_alphanumerics() -> None:
    assert _sanitize_target("Football (American)") == "Football__American_"
    assert _sanitize_target("astronaut") == "astronaut"


def test_parse_run_dir_accepts_trainer_naming() -> None:
    parsed = _parse_run_dir(Path("politician_20260101T120000Z"))
    assert parsed == ("politician", "20260101T120000Z")


def test_parse_run_dir_rejects_arbitrary_dirs() -> None:
    assert _parse_run_dir(Path("not_a_run_dir")) is None
    assert _parse_run_dir(Path("politician_no_timestamp")) is None


def test_format_run_timestamp_pretty_prints() -> None:
    assert _format_run_timestamp("20260101T120000Z") == "2026-01-01T12:00:00Z"


def test_format_run_timestamp_passes_through_garbage() -> None:
    """A non-conforming string must round-trip unchanged rather than crash."""
    assert _format_run_timestamp("not-a-timestamp") == "not-a-timestamp"


# ---------- list_available_targets ----------

def test_list_available_targets_when_root_missing(tmp_path: Path) -> None:
    """Pointing at a non-existent root returns [], not an exception."""
    assert list_available_targets(tmp_path / "does-not-exist") == []


def test_list_available_targets_returns_runs(trained_run) -> None:
    output_root, _ = trained_run
    runs = list_available_targets(output_root)
    assert len(runs) == 1
    assert runs[0].target == "politician"


# ---------- find_run_for_target ----------

def test_find_run_for_target_matches_case_insensitive(trained_run) -> None:
    output_root, run_dir = trained_run
    assert find_run_for_target("Politician", output_root=output_root) == run_dir
    assert find_run_for_target("POLITICIAN", output_root=output_root) == run_dir


def test_find_run_for_target_raises_on_unknown(trained_run) -> None:
    output_root, _ = trained_run
    with pytest.raises(NoModelForTarget) as exc:
        find_run_for_target("astronaut", output_root=output_root)
    # The exception message must surface what's actually available so the
    # caller can correct their request.
    assert "politician" in str(exc.value)


def test_find_run_for_target_rejects_empty_target(trained_run) -> None:
    output_root, _ = trained_run
    with pytest.raises(NoModelForTarget):
        find_run_for_target("   ", output_root=output_root)


# ---------- _coerce_row_to_schema ----------

def test_coerce_row_to_schema_aligns_columns_and_categories() -> None:
    """A new row with extra/missing/wrong-order columns must come back
    matching feature_columns exactly, with categoricals aligned."""
    row = {
        "lon_sun": 60.0,
        "tattva_sun": "Fire/Water",   # known level
        "lon_moon": 120.0,
        "extra_column": 99.0,         # should be dropped
        # "lon_saturn" missing — should appear as NaN
    }
    feature_columns = ["lon_sun", "lon_moon", "lon_saturn", "tattva_sun"]
    category_levels = {
        "tattva_sun": ["Earth/Fire", "Water/Air", "Fire/Water", "Air/Water"],
    }
    X = _coerce_row_to_schema(row, feature_columns, category_levels)
    assert list(X.columns) == feature_columns
    assert pd.isna(X.iloc[0]["lon_saturn"])
    # tattva_sun must now be a categorical with the trained levels.
    assert isinstance(X["tattva_sun"].dtype, pd.CategoricalDtype)
    assert X["tattva_sun"].iloc[0] == "Fire/Water"


def test_coerce_row_to_schema_unknown_category_becomes_nan() -> None:
    """A categorical value the model never saw becomes NaN — XGBoost
    treats it as missing rather than crashing on category-code lookup."""
    row = {"tattva_sun": "Quintessence/Aether"}
    X = _coerce_row_to_schema(
        row,
        feature_columns=["tattva_sun"],
        category_levels={"tattva_sun": ["Earth/Fire", "Water/Air"]},
    )
    assert pd.isna(X.iloc[0]["tattva_sun"])


# ---------- predict_for_chart (full pipeline) ----------

def test_predict_for_chart_returns_probability_and_contributors(trained_run) -> None:
    output_root, _ = trained_run
    result = predict_for_chart(
        "politician",
        output_root=output_root,
        **BANGALORE,
    )
    assert 0.0 <= result["probability"] <= 1.0
    assert "top_contributors" in result
    assert len(result["top_contributors"]) <= 5
    assert "model" in result
    assert result["model"]["run_target"] == "politician"
    assert result["target"] == "politician"
    assert result["input_jd"] > 2447000  # ballpark for 1990


def test_predict_for_chart_top_contributors_have_feature_value(trained_run) -> None:
    """Each top-contributor entry must surface (feature, value, shap_value)
    — the value field is what makes the response readable as a sentence."""
    output_root, _ = trained_run
    result = predict_for_chart(
        "politician",
        output_root=output_root,
        **BANGALORE,
    )
    for c in result["top_contributors"]:
        assert "feature" in c
        assert "value" in c
        assert "shap_value" in c
        assert isinstance(c["shap_value"], float)


def test_predict_for_chart_unknown_target_raises(trained_run) -> None:
    output_root, _ = trained_run
    with pytest.raises(NoModelForTarget):
        predict_for_chart(
            "astronaut",
            output_root=output_root,
            **BANGALORE,
        )


def test_predict_for_chart_legacy_run_without_schema_raises(tmp_path: Path) -> None:
    """An ml_runs/ entry with model.json but no feature_columns.json is a
    legacy run — predict raises NoModelForTarget rather than silently
    inferring with mismatched columns."""
    legacy = tmp_path / "legacy_20260101T120000Z"
    legacy.mkdir()
    (legacy / "model.json").write_text("{}", encoding="utf-8")
    with pytest.raises(NoModelForTarget):
        predict_for_chart(
            "legacy",
            output_root=tmp_path,
            **BANGALORE,
        )


# ---------- /medini/predict route ----------

@pytest.mark.asyncio
async def test_predict_endpoint_lists_available_targets_when_empty(client) -> None:
    """GET /medini/predict on a fresh checkout where no models have been
    trained returns count=0 instead of crashing."""
    response = await client.get("/medini/predict")
    assert response.status_code == 200
    body = response.json()
    assert "available_targets" in body
    assert "count" in body
    # In CI / a fresh checkout there's no data/ml_runs/ so count is 0.
    assert isinstance(body["count"], int)


@pytest.mark.asyncio
async def test_predict_endpoint_404_when_target_unknown(client) -> None:
    """POST against an untrained target → 404 with available_targets so
    the caller can correct their request."""
    response = await client.post(
        "/medini/predict/definitely-not-a-real-target",
        json={
            "year": 1990, "month": 7, "day": 15,
            "hour": 12, "minute": 0,
            "latitude": 12.9716, "longitude": 77.5946,
            "tz_offset": 5.5,
        },
    )
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    detail = body["detail"]
    assert "available_targets" in detail
    assert "hint" in detail
