"""Phase-3C wedge eval — multi-seed bootstrap + replication clause + dual schema.

Replaces the single-seed ``phase0_wedge_eval.py``. Implements the
falsifiable gate from ``implementation_plan_round9.md`` Phase 3C:

* **Step 1 — noise floor.** 20 seeds of (baseline) vs (baseline + 1 column
  of N(0, 1) noise). σ_Δ_holdout_AUC is the noise floor per substrate.
* **Step 2 — wedge eval.** 10 seeds of (baseline) vs (baseline + the
  16 yoga columns shipped by ``add_yoga_features.py``).
* **Step 3 — per-yoga marginal.** For each of the 16 yogas, run a
  leave-one-out (baseline + 15 other yogas) vs (baseline + 16 yogas) and
  bootstrap 95% CI on its marginal AUC contribution.
* **Step 4 — replication clause.** If the gate passes by < 1.5× the
  threshold margin, rerun all of the above with ``test_size=0.25``
  (instead of 0.20) and require both runs to satisfy criteria A/B/C.

Gate criteria (ALL must hold):
* (A) Mean holdout AUC Δ across 10 seeds ≥ 3 × σ_noise, OR ≥ 3 yogas
  have bootstrap 95% CI lower-bound > 0.
* (B) σ_model ≤ Δ_mean (model is stable across seeds).
* (C) ≥ 5 yogas rank in top-50 by XGBoost gain importance.
* (D) Replication confirmation if gate passes by < 1.5× margin.

The eval is schema-agnostic: it accepts either ``is_event_X`` (screening
cohort) or ``is_event`` (event corpus), groups by ``name_norm`` if
present else ``name``, and runs per-decade only if ``birth_decade`` is
present.

Usage:
    python -m app.medini.ml.wedge_eval_v2 \\
        --baseline app/medini/data/screening_career.parquet \\
        --wedge    app/medini/data/screening_career_yogas.parquet \\
        --substrate-name screening_career \\
        --out data/ml_runs/phase3c_wedge

Outputs to ``--out``:
* ``summary.json`` — machine-readable
* ``report.md`` — human-readable decision document
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #

# 16 yoga slugs from add_yoga_features._YOGA_SPECS (kept in lockstep).
_YOGA_SLUGS: tuple[str, ...] = (
    "vipareeta_harsha", "vipareeta_sarala", "vipareeta_vimala",
    "sunapha", "anapha", "durudhura", "kemadruma",
    "ruchaka", "bhadra", "hamsa", "malavya", "sasa",
    "gajakesari", "budha_aditya", "raja_yoga", "dhana_yoga",
)

_NON_FEATURE = (
    "name", "name_norm", "rodden_rating", "categories_raw", "categories_lower",
    "categories_tokens", "source_url", "is_event", "event_root", "event_subtype",
    "event_date", "event_jd", "birth_jd",
    "is_event_X", "target_class", "neg_ratio",
    "birth_dt", "birth_year", "birth_decade",
    "active_md_lord", "active_ad_lord", "active_pd_lord",
    # Lunarastro-specific passthrough columns. CRITICAL: `tags` is the
    # source of `is_event_X` (the cohort builder regex-matches it) →
    # leaving it in the feature set is direct label leakage. `description`
    # often contains the label words verbatim. `category` is a 2-class
    # label-correlated tag. `lunarastro_id` is a unique identifier that
    # could memorise the target. lat/lon/tz/gender encode demographics
    # that correlate with the lunarastro selection bias rather than the
    # astrology being tested.
    "lunarastro_id", "tags", "description", "category",
    "date_of_birth", "birth_time", "birth_time_confidence",
    "latitude", "longitude", "tz_offset_used", "tz_name_used",
    "gender",
)

# XGBoost hyperparameters held constant across baseline and wedge so the Δ
# isolates the marginal feature contribution.
_N_ESTIMATORS = 100
_MAX_DEPTH = 4
_LEARNING_RATE = 0.1

# Phase-3C protocol parameters.
_PRIMARY_TEST_SIZE = 0.20
_REPLICATION_TEST_SIZE = 0.25
_NOISE_SEEDS = 20
_WEDGE_SEEDS = 10
_BOOTSTRAP_RESAMPLES = 1000
_BOOTSTRAP_CI = 0.95
_GATE_NOISE_SIGMA_MULT = 3.0
_GATE_REPLICATION_MARGIN = 1.5
_GATE_PER_YOGA_CI_PASSES = 3
_GATE_TOP_K_GAIN = 50
_GATE_MIN_YOGAS_IN_TOP_K = 5


# --------------------------------------------------------------------------- #
# Eval primitives                                                             #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class _SplitSpec:
    """A single GroupShuffleSplit configuration."""
    seed: int
    test_size: float


def _resolve_columns(df: pd.DataFrame) -> tuple[str, str]:
    """Return (target_col, group_col) for the dual-schema substrates."""
    if "is_event_X" in df.columns:
        target_col = "is_event_X"
    elif "is_event" in df.columns:
        target_col = "is_event"
    else:
        raise KeyError("parquet has neither 'is_event_X' nor 'is_event'")
    if "name_norm" in df.columns:
        group_col = "name_norm"
    elif "name" in df.columns:
        group_col = "name"
    else:
        raise KeyError("parquet has neither 'name_norm' nor 'name'")
    return target_col, group_col


def _coerce_features(df: pd.DataFrame, extra_drop: Sequence[str] = ()) -> pd.DataFrame:
    """Drop non-feature columns and cast object cols to category for XGBoost."""
    drop = list(_NON_FEATURE) + list(extra_drop)
    feat = df.drop(columns=drop, errors="ignore").copy()
    for col in feat.columns:
        s = feat[col]
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
            continue
        if isinstance(s.dtype, pd.CategoricalDtype):
            continue
        feat[col] = s.astype("category")
    return feat


def _fit_and_score(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    seed: int,
) -> tuple[float, xgb.XGBClassifier]:
    """Fit XGBoost on (X_train, y_train), return (AUC on test, fitted model)."""
    scale_pos = float((y_train == 0).sum()) / max(int((y_train == 1).sum()), 1)
    model = xgb.XGBClassifier(
        n_estimators=_N_ESTIMATORS,
        max_depth=_MAX_DEPTH,
        learning_rate=_LEARNING_RATE,
        scale_pos_weight=scale_pos,
        enable_categorical=True,
        tree_method="hist",
        random_state=seed,
        eval_metric="logloss",
        n_jobs=-1,
        verbosity=0,
    ).fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    return float(roc_auc_score(y_test, proba)), model


def _holdout_auc(
    df: pd.DataFrame,
    extra_drop: Sequence[str],
    split: _SplitSpec,
) -> tuple[float, xgb.XGBClassifier, np.ndarray, pd.Series]:
    """Score one (df, drop, seed, test_size) combination."""
    target_col, group_col = _resolve_columns(df)
    y = df[target_col].astype(int)
    X = _coerce_features(df, extra_drop=extra_drop)
    groups = df[group_col]

    gss = GroupShuffleSplit(n_splits=1, test_size=split.test_size, random_state=split.seed)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))
    # Group integrity check — no person in both halves.
    train_names = set(groups.iloc[train_idx])
    test_names = set(groups.iloc[test_idx])
    if train_names & test_names:
        raise RuntimeError("group leak between train and test")

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    auc, model = _fit_and_score(X_train, y_train, X_test, y_test, split.seed)
    return auc, model, test_idx, y_test


# --------------------------------------------------------------------------- #
# Step 1 — noise floor                                                        #
# --------------------------------------------------------------------------- #

def measure_noise_floor(
    baseline_path: Path,
    n_seeds: int,
    test_size: float,
) -> dict[str, Any]:
    """20-seed measurement of σ_Δ when only one N(0,1) column is added.

    Returns mean Δ and σ_Δ — the σ_Δ is the noise floor the Phase-3C
    gate compares against.
    """
    df = pd.read_parquet(baseline_path)
    deltas: list[float] = []
    base_aucs: list[float] = []
    noise_aucs: list[float] = []
    for seed in range(n_seeds):
        split = _SplitSpec(seed=seed, test_size=test_size)
        base_auc, _, _, _ = _holdout_auc(df, extra_drop=(), split=split)

        rng = np.random.default_rng(seed)
        df_noise = df.copy()
        df_noise["_noise_col"] = rng.normal(0.0, 1.0, len(df))
        noise_auc, _, _, _ = _holdout_auc(df_noise, extra_drop=(), split=split)

        base_aucs.append(base_auc)
        noise_aucs.append(noise_auc)
        deltas.append(noise_auc - base_auc)

    return {
        "n_seeds": n_seeds,
        "test_size": test_size,
        "base_auc_mean": float(np.mean(base_aucs)),
        "noise_auc_mean": float(np.mean(noise_aucs)),
        "delta_mean": float(np.mean(deltas)),
        "delta_std": float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0,
        "deltas": [float(d) for d in deltas],
    }


# --------------------------------------------------------------------------- #
# Step 2 — wedge eval (16 yogas)                                              #
# --------------------------------------------------------------------------- #

def _yoga_columns_in(df: pd.DataFrame) -> tuple[str, ...]:
    """Return the subset of yoga columns actually present in the parquet."""
    cols: list[str] = []
    for slug in _YOGA_SLUGS:
        for suffix in ("_natal_strength", "_dasha_gated_strength"):
            c = f"{slug}{suffix}"
            if c in df.columns:
                cols.append(c)
    return tuple(cols)


def measure_wedge_delta(
    baseline_path: Path,
    wedge_path: Path,
    n_seeds: int,
    test_size: float,
) -> dict[str, Any]:
    """10-seed measurement of (baseline) vs (baseline + 16 yoga cols)."""
    base_df = pd.read_parquet(baseline_path)
    wedge_df = pd.read_parquet(wedge_path)
    yoga_cols = _yoga_columns_in(wedge_df)

    base_aucs: list[float] = []
    wedge_aucs: list[float] = []
    deltas: list[float] = []
    gains_per_yoga: dict[str, list[float]] = {c: [] for c in yoga_cols}
    gain_ranks_per_yoga: dict[str, list[int]] = {c: [] for c in yoga_cols}

    for seed in range(n_seeds):
        split = _SplitSpec(seed=seed, test_size=test_size)
        base_auc, _, _, _ = _holdout_auc(base_df, extra_drop=(), split=split)
        wedge_auc, wedge_model, _, _ = _holdout_auc(wedge_df, extra_drop=(), split=split)

        base_aucs.append(base_auc)
        wedge_aucs.append(wedge_auc)
        deltas.append(wedge_auc - base_auc)

        booster = wedge_model.get_booster()
        gain_dict = booster.get_score(importance_type="gain")
        # XGBoost prefixes features with f<idx> when feature_names absent;
        # with enable_categorical=True + DataFrame input, names are preserved.
        sorted_gains = sorted(gain_dict.items(), key=lambda kv: kv[1], reverse=True)
        feat_to_rank = {name: rank + 1 for rank, (name, _) in enumerate(sorted_gains)}
        for c in yoga_cols:
            gains_per_yoga[c].append(float(gain_dict.get(c, 0.0)))
            gain_ranks_per_yoga[c].append(int(feat_to_rank.get(c, 10**6)))

    return {
        "n_seeds": n_seeds,
        "test_size": test_size,
        "yoga_columns": list(yoga_cols),
        "base_auc_mean": float(np.mean(base_aucs)),
        "wedge_auc_mean": float(np.mean(wedge_aucs)),
        "wedge_auc_std": float(np.std(wedge_aucs, ddof=1)) if len(wedge_aucs) > 1 else 0.0,
        "delta_mean": float(np.mean(deltas)),
        "delta_std": float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0,
        "deltas": [float(d) for d in deltas],
        "mean_gain_per_yoga": {c: float(np.mean(v)) for c, v in gains_per_yoga.items()},
        "median_rank_per_yoga": {c: int(np.median(v)) for c, v in gain_ranks_per_yoga.items()},
    }


# --------------------------------------------------------------------------- #
# Step 3 — per-yoga marginal + bootstrap CI                                   #
# --------------------------------------------------------------------------- #

def _bootstrap_auc_ci(
    y_true: np.ndarray,
    proba_a: np.ndarray,
    proba_b: np.ndarray,
    n_resamples: int,
    ci: float,
    rng: np.random.Generator,
) -> tuple[float, float]:
    """Bootstrap CI on (AUC_b - AUC_a) over test-set resamples."""
    n = len(y_true)
    deltas = np.empty(n_resamples, dtype=np.float64)
    valid = 0
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        y_resampled = y_true[idx]
        if len(np.unique(y_resampled)) < 2:
            continue
        a = roc_auc_score(y_resampled, proba_a[idx])
        b = roc_auc_score(y_resampled, proba_b[idx])
        deltas[valid] = b - a
        valid += 1
    if valid == 0:
        return 0.0, 0.0
    deltas = deltas[:valid]
    alpha = (1.0 - ci) / 2.0
    lo = float(np.quantile(deltas, alpha))
    hi = float(np.quantile(deltas, 1.0 - alpha))
    return lo, hi


def measure_per_yoga_loo_ci(
    wedge_path: Path,
    n_resamples: int,
    ci: float,
    seed: int,
    test_size: float,
) -> dict[str, dict[str, float]]:
    """For each yoga column, bootstrap 95% CI on the marginal AUC delta.

    Marginal = AUC(full wedge) - AUC(wedge minus this one column).
    A yoga "passes per-yoga" if its CI lower-bound > 0.
    """
    df = pd.read_parquet(wedge_path)
    target_col, group_col = _resolve_columns(df)
    y = df[target_col].astype(int)
    X_full = _coerce_features(df, extra_drop=())
    groups = df[group_col]
    yoga_cols = _yoga_columns_in(df)

    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(gss.split(X_full, y, groups=groups))
    if set(groups.iloc[train_idx]) & set(groups.iloc[test_idx]):
        raise RuntimeError("group leak in per-yoga LOO eval")

    X_train_full, X_test_full = X_full.iloc[train_idx], X_full.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    y_test_np = y_test.to_numpy()

    _, full_model = _fit_and_score(X_train_full, y_train, X_test_full, y_test, seed)
    proba_full = full_model.predict_proba(X_test_full)[:, 1]

    results: dict[str, dict[str, float]] = {}
    rng = np.random.default_rng(seed)
    for yoga_col in yoga_cols:
        X_train_loo = X_train_full.drop(columns=[yoga_col])
        X_test_loo = X_test_full.drop(columns=[yoga_col])
        _, loo_model = _fit_and_score(X_train_loo, y_train, X_test_loo, y_test, seed)
        proba_loo = loo_model.predict_proba(X_test_loo)[:, 1]

        point_full = float(roc_auc_score(y_test_np, proba_full))
        point_loo = float(roc_auc_score(y_test_np, proba_loo))
        marginal = point_full - point_loo

        ci_lo, ci_hi = _bootstrap_auc_ci(
            y_test_np, proba_loo, proba_full, n_resamples, ci, rng,
        )
        results[yoga_col] = {
            "marginal_auc": marginal,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "ci_passes": int(ci_lo > 0),
        }
    return results


# --------------------------------------------------------------------------- #
# Gate logic                                                                  #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class _GateResult:
    criterion_a: bool
    criterion_b: bool
    criterion_c: bool
    n_yoga_ci_passes: int
    n_yoga_top_k: int
    delta_mean: float
    delta_std: float
    sigma_model: float
    noise_sigma: float
    pass_strong: bool
    pass_weak: bool
    overall_pass: bool
    needs_replication: bool


def _classify_gate(
    noise: dict[str, Any],
    wedge: dict[str, Any],
    per_yoga: dict[str, dict[str, float]],
) -> _GateResult:
    """Apply Phase-3C criteria A/B/C to a noise+wedge+per-yoga bundle."""
    delta_mean = wedge["delta_mean"]
    sigma_model = wedge["wedge_auc_std"]
    noise_sigma = noise["delta_std"]

    n_ci = sum(1 for v in per_yoga.values() if v["ci_passes"])
    crit_a_cumulative = delta_mean >= _GATE_NOISE_SIGMA_MULT * noise_sigma
    crit_a_per_yoga = n_ci >= _GATE_PER_YOGA_CI_PASSES
    crit_a = crit_a_cumulative or crit_a_per_yoga

    crit_b = sigma_model <= max(delta_mean, 1e-9)

    top_k_yogas = sum(
        1 for r in wedge["median_rank_per_yoga"].values()
        if r <= _GATE_TOP_K_GAIN
    )
    crit_c = top_k_yogas >= _GATE_MIN_YOGAS_IN_TOP_K

    overall = crit_a and crit_b and crit_c

    # Replication clause: gate passes by < 1.5× the threshold margin.
    if overall:
        margin_factor_a = (
            delta_mean / max(_GATE_NOISE_SIGMA_MULT * noise_sigma, 1e-9)
            if crit_a_cumulative else float("inf")
        )
        margin_factor_per_yoga = (
            n_ci / _GATE_PER_YOGA_CI_PASSES
            if crit_a_per_yoga else float("inf")
        )
        # Pass-margin = whichever route to A was tighter.
        margin = min(margin_factor_a, margin_factor_per_yoga)
        needs_repl = margin < _GATE_REPLICATION_MARGIN
        pass_strong = margin >= 2.0
        pass_weak = overall and not pass_strong
    else:
        needs_repl = False
        pass_strong = False
        pass_weak = False

    return _GateResult(
        criterion_a=crit_a,
        criterion_b=crit_b,
        criterion_c=crit_c,
        n_yoga_ci_passes=n_ci,
        n_yoga_top_k=top_k_yogas,
        delta_mean=delta_mean,
        delta_std=wedge["delta_std"],
        sigma_model=sigma_model,
        noise_sigma=noise_sigma,
        pass_strong=pass_strong,
        pass_weak=pass_weak,
        overall_pass=overall,
        needs_replication=needs_repl,
    )


# --------------------------------------------------------------------------- #
# Top-level runner                                                            #
# --------------------------------------------------------------------------- #

def run_phase3c(
    baseline_path: Path,
    wedge_path: Path,
    out_dir: Path,
    substrate_name: str,
    noise_seeds: int = _NOISE_SEEDS,
    wedge_seeds: int = _WEDGE_SEEDS,
    bootstrap_resamples: int = _BOOTSTRAP_RESAMPLES,
) -> dict[str, Any]:
    """Execute the full Phase-3C protocol on one substrate.

    Returns the bundle written to summary.json.
    """
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    t0 = time.time()

    logger.info("substrate=%s | step 1 — noise floor (primary, %d seeds)",
                substrate_name, noise_seeds)
    noise_primary = measure_noise_floor(baseline_path, noise_seeds, _PRIMARY_TEST_SIZE)

    logger.info("substrate=%s | step 2 — wedge (primary, %d seeds)",
                substrate_name, wedge_seeds)
    wedge_primary = measure_wedge_delta(
        baseline_path, wedge_path, wedge_seeds, _PRIMARY_TEST_SIZE,
    )

    logger.info("substrate=%s | step 3 — per-yoga LOO bootstrap (primary)", substrate_name)
    per_yoga_primary = measure_per_yoga_loo_ci(
        wedge_path, bootstrap_resamples, _BOOTSTRAP_CI,
        seed=0, test_size=_PRIMARY_TEST_SIZE,
    )

    gate_primary = _classify_gate(noise_primary, wedge_primary, per_yoga_primary)
    replication: dict[str, Any] | None = None
    gate_replication: _GateResult | None = None

    if gate_primary.needs_replication:
        logger.info("substrate=%s | step 4 — replication clause (test_size=%.2f)",
                    substrate_name, _REPLICATION_TEST_SIZE)
        noise_rep = measure_noise_floor(baseline_path, noise_seeds, _REPLICATION_TEST_SIZE)
        wedge_rep = measure_wedge_delta(
            baseline_path, wedge_path, wedge_seeds, _REPLICATION_TEST_SIZE,
        )
        per_yoga_rep = measure_per_yoga_loo_ci(
            wedge_path, bootstrap_resamples, _BOOTSTRAP_CI,
            seed=0, test_size=_REPLICATION_TEST_SIZE,
        )
        gate_replication = _classify_gate(noise_rep, wedge_rep, per_yoga_rep)
        replication = {
            "noise": noise_rep,
            "wedge": wedge_rep,
            "per_yoga": per_yoga_rep,
            "gate": asdict(gate_replication),
        }

    overall_pass = gate_primary.overall_pass
    if gate_primary.needs_replication:
        overall_pass = (
            gate_primary.overall_pass
            and gate_replication is not None
            and gate_replication.overall_pass
        )

    bundle: dict[str, Any] = {
        "ran_at": started_at,
        "substrate": substrate_name,
        "baseline_path": str(baseline_path),
        "wedge_path": str(wedge_path),
        "elapsed_seconds": round(time.time() - t0, 1),
        "primary": {
            "noise": noise_primary,
            "wedge": wedge_primary,
            "per_yoga": per_yoga_primary,
            "gate": asdict(gate_primary),
        },
        "replication": replication,
        "overall_pass": overall_pass,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"summary_{substrate_name}.json").write_text(
        json.dumps(bundle, indent=2, default=str), encoding="utf-8"
    )
    _write_report(bundle, out_dir / f"report_{substrate_name}.md")
    return bundle


# --------------------------------------------------------------------------- #
# Report writer                                                               #
# --------------------------------------------------------------------------- #

def _write_report(bundle: dict[str, Any], path: Path) -> None:
    primary = bundle["primary"]
    gate = primary["gate"]
    noise = primary["noise"]
    wedge = primary["wedge"]
    per_yoga = primary["per_yoga"]

    lines = [
        f"# Phase-3C Wedge Eval — {bundle['substrate']}",
        f"",
        f"_ran at_: {bundle['ran_at']}",
        f"_elapsed_: {bundle['elapsed_seconds']}s",
        f"",
        f"## Headline",
        f"",
        f"- **Δ_mean** (wedge − baseline, {wedge['n_seeds']} seeds): "
        f"**{wedge['delta_mean']:+.4f}**",
        f"- **σ_noise** (noise floor, {noise['n_seeds']} seeds): "
        f"{noise['delta_std']:.4f}",
        f"- **σ_model** (wedge std across seeds): {wedge['wedge_auc_std']:.4f}",
        f"- **Yogas with bootstrap CI > 0**: {gate['n_yoga_ci_passes']}/16",
        f"- **Yogas in top-{_GATE_TOP_K_GAIN} by mean gain**: {gate['n_yoga_top_k']}/16",
        f"",
        f"## Gate criteria",
        f"",
        f"| Criterion | Required | Actual | Pass |",
        f"|---|---|---|---|",
        f"| A — cumulative or per-yoga | Δ_mean ≥ 3σ_noise "
        f"({_GATE_NOISE_SIGMA_MULT * noise['delta_std']:.4f}) OR "
        f"{_GATE_PER_YOGA_CI_PASSES}+ yogas CI>0 | "
        f"Δ_mean={wedge['delta_mean']:+.4f}; n_CI={gate['n_yoga_ci_passes']} | "
        f"{'✅' if gate['criterion_a'] else '❌'} |",
        f"| B — model stability | σ_model ≤ Δ_mean | "
        f"σ_model={wedge['wedge_auc_std']:.4f}; Δ_mean={wedge['delta_mean']:+.4f} | "
        f"{'✅' if gate['criterion_b'] else '❌'} |",
        f"| C — gain importance | ≥{_GATE_MIN_YOGAS_IN_TOP_K} yogas in top-"
        f"{_GATE_TOP_K_GAIN} | {gate['n_yoga_top_k']} | "
        f"{'✅' if gate['criterion_c'] else '❌'} |",
        f"",
        f"**Overall primary gate**: "
        f"{'PASS' if gate['overall_pass'] else 'FAIL'}",
    ]
    if gate["overall_pass"]:
        lines.append(
            f"- pass_strong: {gate['pass_strong']} · "
            f"pass_weak: {gate['pass_weak']} · "
            f"needs_replication: {gate['needs_replication']}"
        )

    lines.extend([
        f"",
        f"## Per-yoga marginal AUC (LOO, 1000-resample bootstrap)",
        f"",
        f"| Yoga column | marginal Δ | CI lo | CI hi | CI>0 | median rank |",
        f"|---|---|---|---|---|---|",
    ])
    for col, stats in per_yoga.items():
        median_rank = wedge["median_rank_per_yoga"].get(col, "—")
        lines.append(
            f"| `{col}` | {stats['marginal_auc']:+.4f} | "
            f"{stats['ci_lo']:+.4f} | {stats['ci_hi']:+.4f} | "
            f"{'✓' if stats['ci_passes'] else '·'} | {median_rank} |"
        )

    lines.extend([
        f"",
        f"## Noise floor (per-seed Δ)",
        f"",
        f"- mean Δ: {noise['delta_mean']:+.4f}",
        f"- σ Δ:    {noise['delta_std']:.4f}",
        f"",
        f"## Wedge Δ (per-seed)",
        f"",
        f"- mean Δ: {wedge['delta_mean']:+.4f}",
        f"- σ Δ:    {wedge['delta_std']:.4f}",
        f"- mean wedge AUC: {wedge['wedge_auc_mean']:.4f}",
        f"- mean base  AUC: {wedge['base_auc_mean']:.4f}",
    ])

    if bundle["replication"]:
        rep = bundle["replication"]
        rep_gate = rep["gate"]
        lines.extend([
            f"",
            f"## Replication clause (test_size=0.25)",
            f"",
            f"Replication fired because the primary pass margin was < "
            f"{_GATE_REPLICATION_MARGIN}× threshold.",
            f"",
            f"- replication Δ_mean: {rep['wedge']['delta_mean']:+.4f}",
            f"- replication σ_noise: {rep['noise']['delta_std']:.4f}",
            f"- replication σ_model: {rep['wedge']['wedge_auc_std']:.4f}",
            f"- replication n_CI passes: {rep_gate['n_yoga_ci_passes']}/16",
            f"- replication n_top-{_GATE_TOP_K_GAIN}: {rep_gate['n_yoga_top_k']}/16",
            f"- replication overall: "
            f"{'PASS' if rep_gate['overall_pass'] else 'FAIL'}",
        ])

    lines.extend([
        f"",
        f"## Final decision",
        f"",
        f"**Phase 3C overall**: "
        f"{'PASS' if bundle['overall_pass'] else 'FAIL'}",
        f"",
        _decision_text(gate, bundle.get("replication") is not None,
                       bundle["overall_pass"]),
        f"",
    ])

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _decision_text(gate: dict, has_replication: bool, overall: bool) -> str:
    """Return the decision-point paragraph per the Phase-3C plan table."""
    if overall and gate["pass_strong"]:
        return (
            "**PASS strong** — proceed to Phase 4 (full ~80-yoga catalog). "
            "Δ_mean ≥ 2× noise floor; per-yoga signal robust."
        )
    if overall and gate["pass_weak"] and not has_replication:
        return (
            "**PASS weak (margin > 1.5×)** — proceed to Phase 4 with the "
            "caveat that per-yoga effect sizes are modest; expect Phase 6 "
            "AUC at the lower end of the acceptance window."
        )
    if overall and has_replication:
        return (
            "**PASS weak + replication confirmed** — proceed to Phase 4 "
            "with the caveat above."
        )
    if not overall and has_replication:
        return (
            "**FAIL — replication failed**. Treat as FAIL with partial "
            "signal: re-plan Phase 4 to focus on the per-yoga CI>0 yogas, "
            "expand the corpus, and do not advance to Phase 5/6."
        )
    if gate["n_yoga_ci_passes"] > 0:
        return (
            f"**FAIL with partial signal** — {gate['n_yoga_ci_passes']} "
            f"yoga(s) have CI > 0, but the gate as a whole did not pass. "
            f"Document the passing yogas and replan Phase 4 around them; "
            f"do NOT proceed to Phase 6 on faith."
        )
    return (
        "**FAIL with no signal** — STOP. Pivot options per the plan: "
        "(a) corpus expansion (Astro-Databank scrape), "
        "(b) non-structural EGNN attempt on the honest substrate, "
        "(c) close the project as a defensible null result."
    )


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase-3C wedge eval (multi-seed bootstrap + replication)."
    )
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--wedge", required=True, type=Path)
    parser.add_argument("--substrate-name", required=True, type=str,
                        help="e.g. screening_career or event_corpus_career")
    parser.add_argument("--out", default=Path("data/ml_runs/phase3c_wedge"),
                        type=Path)
    parser.add_argument("--noise-seeds", type=int, default=_NOISE_SEEDS)
    parser.add_argument("--wedge-seeds", type=int, default=_WEDGE_SEEDS)
    parser.add_argument("--bootstrap-resamples", type=int,
                        default=_BOOTSTRAP_RESAMPLES)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if not args.baseline.exists():
        print(f"ERROR baseline not found: {args.baseline}", file=sys.stderr)
        return 2
    if not args.wedge.exists():
        print(f"ERROR wedge parquet not found: {args.wedge}", file=sys.stderr)
        return 2

    bundle = run_phase3c(
        baseline_path=args.baseline,
        wedge_path=args.wedge,
        out_dir=args.out,
        substrate_name=args.substrate_name,
        noise_seeds=args.noise_seeds,
        wedge_seeds=args.wedge_seeds,
        bootstrap_resamples=args.bootstrap_resamples,
    )

    print()
    g = bundle["primary"]["gate"]
    print(f"=== Phase-3C result: substrate={bundle['substrate']} ===")
    print(f"  delta_mean={g['delta_mean']:+.4f}  sigma_model={g['sigma_model']:.4f}  "
          f"sigma_noise={g['noise_sigma']:.4f}")
    print(f"  criteria: A={g['criterion_a']} B={g['criterion_b']} C={g['criterion_c']}")
    print(f"  CI>0 yogas: {g['n_yoga_ci_passes']}/16  "
          f"top-{_GATE_TOP_K_GAIN}: {g['n_yoga_top_k']}/16")
    if bundle["replication"]:
        rg = bundle["replication"]["gate"]
        print(f"  replication: A={rg['criterion_a']} B={rg['criterion_b']} "
              f"C={rg['criterion_c']} overall={rg['overall_pass']}")
    print(f"  OVERALL: {'PASS' if bundle['overall_pass'] else 'FAIL'}")
    return 0 if bundle["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
