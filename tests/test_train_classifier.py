"""Integration tests for app.medini.ml.train_classifier.

A real XGBoost training run on a tiny synthetic parquet (~50 rows). Tests
that the pipeline:
  - filters / encodes correctly
  - trains a model that beats random (ROC-AUC > 0.5)
  - emits all expected artifacts (model.json, plots, CSVs, report.md)
  - is deterministic given a fixed seed
  - rejects pathological inputs cleanly (single-class target, missing parquet)

Skipped on systems without xgboost+shap installed (handled via importorskip).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Skip the whole module if any heavy ML dep is missing — keeps the rest of
# the suite usable on minimal installs.
pytest.importorskip("xgboost")
pytest.importorskip("shap")
pytest.importorskip("matplotlib")

from app.medini.ml.train_classifier import (  # noqa: E402
    cross_validate_roc_auc,
    derive_binary_target,
    fit_final_model,
    run_training,
    select_features,
)


def _build_synthetic_parquet(tmp_path: Path, n_rows: int = 100, seed: int = 7) -> Path:
    """Create a small parquet with the expected schema and a learnable
    target. Two clusters of feature values so XGBoost can find a signal.
    """
    rng = np.random.default_rng(seed)

    # Half the rows are "politicians" with a distinctive feature distribution.
    n_pos = n_rows // 4   # ~25% positive class
    is_pol = np.zeros(n_rows, dtype=int)
    is_pol[:n_pos] = 1
    rng.shuffle(is_pol)

    rows = []
    for i in range(n_rows):
        # If positive class, push lon_sun into a distinctive range; otherwise
        # spread uniformly. This is the signal XGBoost should latch onto.
        lon_sun = rng.uniform(40, 80) if is_pol[i] else rng.uniform(0, 360)
        cats_lower = "vocation : politics : politician" if is_pol[i] else "vocation : other"
        # Minimal feature schema — only what train_classifier strictly needs.
        # The actual production parquet has 193 features; here we use 4 numeric
        # + 1 categorical to exercise both code paths.
        rows.append({
            "name": f"row_{i}",
            "rodden_rating": "AA",
            "categories_raw": "Vocation : Politics : Politician" if is_pol[i] else "Vocation : Other",
            "categories_lower": cats_lower,
            "categories_tokens": ["vocation", "politics", "politician"] if is_pol[i] else ["vocation", "other"],
            "source_url": f"https://example/row_{i}",
            "lon_sun": lon_sun,
            "lon_moon": float(rng.uniform(0, 360)),
            "lon_saturn": float(rng.uniform(0, 360)),
            "vel_jupiter": float(rng.uniform(-0.2, 0.3)),
            "tattva_sun": rng.choice(["Earth/Fire", "Water/Air", "Fire/Water", "Air/Water"]),
        })

    df = pd.DataFrame(rows)
    parquet_path = tmp_path / "synthetic.parquet"
    df.to_parquet(parquet_path, index=False)
    return parquet_path


# ---------- derive_binary_target ----------

def test_derive_binary_target_substring_match() -> None:
    df = pd.DataFrame({"categories_lower": [
        "vocation : politics : politician",
        "vocation : politics : diplomat",
        "vocation : sports : athlete",
        "",
    ]})
    target = derive_binary_target(df, "politician")
    assert target.tolist() == [1, 0, 0, 0]


def test_derive_binary_target_broader_token_widens_match() -> None:
    df = pd.DataFrame({"categories_lower": [
        "vocation : politics : politician",
        "vocation : politics : diplomat",
        "vocation : sports : athlete",
    ]})
    # "politics" matches both politician and diplomat
    target = derive_binary_target(df, "politics")
    assert target.tolist() == [1, 1, 0]


def test_derive_binary_target_handles_missing_column_values() -> None:
    df = pd.DataFrame({"categories_lower": [None, "vocation : politics", ""]})
    target = derive_binary_target(df, "politics")
    assert target.tolist() == [0, 1, 0]


def test_derive_binary_target_rejects_empty_substring() -> None:
    df = pd.DataFrame({"categories_lower": ["vocation"]})
    with pytest.raises(ValueError):
        derive_binary_target(df, "")


# ---------- select_features ----------

def test_select_features_drops_label_columns() -> None:
    df = pd.DataFrame({
        "name": ["a", "b"],
        "rodden_rating": ["AA", "AA"],
        "categories_raw": ["x", "y"],
        "categories_lower": ["x", "y"],
        "categories_tokens": [["x"], ["y"]],
        "source_url": ["u", "v"],
        "lon_sun": [10.0, 20.0],
    })
    features = select_features(df)
    for col in ("name", "rodden_rating", "categories_raw",
                "categories_lower", "categories_tokens", "source_url"):
        assert col not in features.columns
    assert "lon_sun" in features.columns


def test_select_features_categoricalizes_object_columns() -> None:
    df = pd.DataFrame({
        "lon_sun": [10.0, 20.0, 30.0],
        "tattva_sun": ["Earth/Fire", "Water/Air", "Earth/Fire"],
    })
    features = select_features(df)
    assert features["tattva_sun"].dtype.name == "category"
    assert features["lon_sun"].dtype.kind in "fi"


# ---------- cross_validate_roc_auc ----------

def test_cross_validate_rejects_single_class_target(tmp_path: Path) -> None:
    parquet = _build_synthetic_parquet(tmp_path, n_rows=20)
    df = pd.read_parquet(parquet)
    X = select_features(df)
    y = pd.Series([1] * len(X))  # all positive — invalid
    with pytest.raises(ValueError):
        cross_validate_roc_auc(X, y, seed=42)


def test_cross_validate_rejects_too_few_positives(tmp_path: Path) -> None:
    parquet = _build_synthetic_parquet(tmp_path, n_rows=20)
    df = pd.read_parquet(parquet)
    X = select_features(df)
    # Manually construct a target with only 2 positives — too few for 5-fold CV.
    y = pd.Series([1, 1] + [0] * (len(X) - 2))
    with pytest.raises(ValueError, match="at least"):
        cross_validate_roc_auc(X, y, seed=42)


# ---------- End-to-end run_training ----------

def test_run_training_emits_all_artifacts(tmp_path: Path) -> None:
    parquet = _build_synthetic_parquet(tmp_path, n_rows=100, seed=7)
    output_root = tmp_path / "ml_runs"

    run_dir = run_training(
        features_parquet=parquet,
        target_substring="politician",
        output_root=output_root,
        seed=42,
        top_n_features=4,
        min_rule_impact=0.0,    # accept any rule for this small synthetic dataset
    )

    # All expected artifacts exist
    assert (run_dir / "model.json").exists()
    assert (run_dir / "shap_summary.png").exists()
    assert (run_dir / "feature_importance.csv").exists()
    assert (run_dir / "rules.csv").exists()
    assert (run_dir / "report.md").exists()
    # At least one dependence plot
    dependence_pngs = list(run_dir.glob("shap_dependence_*.png"))
    assert len(dependence_pngs) >= 1


def test_run_training_model_beats_random(tmp_path: Path) -> None:
    """The synthetic dataset has a clear signal (lon_sun ∈ [40, 80] for
    positives); XGBoost should easily exceed ROC-AUC 0.5."""
    parquet = _build_synthetic_parquet(tmp_path, n_rows=200, seed=11)
    output_root = tmp_path / "ml_runs"

    run_dir = run_training(
        features_parquet=parquet,
        target_substring="politician",
        output_root=output_root,
        seed=42,
        top_n_features=4,
    )

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    # The report includes "Holdout test ROC-AUC: 0.XXXX". Must beat 0.5.
    import re
    m = re.search(r"Holdout test ROC-AUC.*?(\d+\.\d+)", report)
    assert m is not None, "no ROC-AUC line in report"
    test_auc = float(m.group(1))
    assert test_auc > 0.5, f"model didn't beat random: ROC-AUC = {test_auc}"


def test_run_training_is_deterministic(tmp_path: Path) -> None:
    """Same seed → same model. Compare the saved model.json byte-for-byte."""
    parquet = _build_synthetic_parquet(tmp_path, n_rows=100, seed=7)

    out1 = tmp_path / "run_a"
    out2 = tmp_path / "run_b"

    run_a = run_training(features_parquet=parquet, target_substring="politician",
                         output_root=out1, seed=42, top_n_features=3, min_rule_impact=0.0)
    run_b = run_training(features_parquet=parquet, target_substring="politician",
                         output_root=out2, seed=42, top_n_features=3, min_rule_impact=0.0)

    bytes_a = (run_a / "model.json").read_bytes()
    bytes_b = (run_b / "model.json").read_bytes()
    assert bytes_a == bytes_b, "model not deterministic across runs with same seed"


def test_run_training_rejects_too_few_positives(tmp_path: Path) -> None:
    """Substring matching nothing → 0 positives → clear error."""
    parquet = _build_synthetic_parquet(tmp_path, n_rows=50)
    with pytest.raises(ValueError, match="positive class samples"):
        run_training(
            features_parquet=parquet,
            target_substring="zzz_nonexistent",  # matches nothing
            output_root=tmp_path / "ml_runs",
            seed=42,
        )


def test_run_training_rejects_missing_parquet(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        run_training(
            features_parquet=tmp_path / "nonexistent.parquet",
            target_substring="politician",
            output_root=tmp_path / "ml_runs",
            seed=42,
        )
