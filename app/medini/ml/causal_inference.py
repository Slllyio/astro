"""Round 6 Phase 6: causal inference on chart features.

Distinguishes CAUSAL natal features from confounded correlates. For
each binary event outcome (e.g., "had_marriage_event"), estimates the
Average Treatment Effect (ATE) of each top-SHAP feature using
**Double Machine Learning (DML)** — Chernozhukov et al's robust
ATE estimator that handles high-dimensional confounders.

For each candidate feature F:
1. Binarise F at its median → "treatment" T ∈ {0, 1}.
2. Use the rest of the natal features as W (covariates).
3. Use DML to estimate E[Y | T=1, W] - E[Y | T=0, W].
4. Compare ATE magnitude to:
   - SHAP importance of F from Round 5 (mere correlation)
   - p-value of T's coefficient in a logistic regression
     conditioned on W.

Features with high SHAP but low ATE = confounded proxies (their
predictive power comes from co-varying with the true cause). Features
with high ATE = genuine causes whose intervention would shift outcomes.

This is the first quantitative causal-vs-confounded analysis applied
to Vedic astrology.

CLI
===
    python -m app.medini.ml.causal_inference \\
        --natal app/medini/data/ml_astro_round5.parquet \\
        --events data/astro_databank/events_all.csv \\
        --shap data/ml_runs/multiclass_event_root_20260518T221902Z/feature_importance.csv \\
        --target marriage \\
        --output data/ml_runs/causal_round6_phase6/
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
from econml.dml import LinearDML, NonParamDML
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestRegressor

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


# ---------- Cohort + target ----------

def build_target_outcome(
    natal_parquet: Path, events_csv: Path,
    target_event_substring: str,
) -> pd.DataFrame:
    """Build (natal_features, y) frame where y = 1 if person ever had
    an event whose event_root contains target_event_substring."""
    natal = pd.read_parquet(natal_parquet)
    natal["_n"] = natal["name"].astype(str).str.strip().str.lower()
    natal = natal.drop_duplicates(subset="_n")

    events = pd.read_csv(events_csv)
    events["_n"] = events["name"].astype(str).str.strip().str.lower()
    events["root_lower"] = events["event_root"].astype(str).str.lower().str.strip()
    target_lc = target_event_substring.strip().lower()
    positives = set(
        events.loc[events["root_lower"].str.contains(target_lc, na=False), "_n"]
    )
    cohort = set(events["_n"]) & set(natal["_n"])
    natal = natal[natal["_n"].isin(cohort)].copy()
    natal["y"] = natal["_n"].isin(positives).astype(int)
    logger.info(
        "cohort=%d  positives=%d (%.2f%%)",
        len(natal), natal["y"].sum(), 100 * natal["y"].mean(),
    )
    return natal


# ---------- Feature selection ----------

NON_FEATURE_PREFIXES: tuple[str, ...] = (
    "t_", "active_", "md_elapsed_years", "ad_elapsed_years",
    "pd_elapsed_years", "cross_lon_", "transit_bav_",
    "sade_sati_active", "kantaka_shani", "ashtama_shani",
)
NON_FEATURE_NAMES: frozenset[str] = frozenset({
    "name", "rodden_rating", "categories_raw", "categories_lower",
    "categories_tokens", "source_url", "_n", "y",
    "event_date", "event_jd", "birth_jd", "event_root",
    "event_subtype", "is_event",
})


def _is_natal_numeric(col: str, df: pd.DataFrame) -> bool:
    if col in NON_FEATURE_NAMES:
        return False
    if any(col.startswith(p) for p in NON_FEATURE_PREFIXES):
        return False
    s = df[col]
    if not pd.api.types.is_numeric_dtype(s):
        return False
    if pd.api.types.is_bool_dtype(s):
        return False
    if s.nunique() < 2:
        return False
    return True


def load_top_shap_features(
    shap_csv: Path, k: int = 20,
) -> list[str]:
    """Read the SHAP importance CSV from Phase 5 multi-class run.

    Format: rank,feature,mean_abs_shap
    """
    df = pd.read_csv(shap_csv)
    feature_col = "feature" if "feature" in df.columns else df.columns[1]
    return df[feature_col].head(k).tolist()


# ---------- ATE estimation per feature ----------

def estimate_ate_continuous(
    df: pd.DataFrame, feature: str, y_col: str = "y",
    seed: int = 42,
) -> dict[str, float]:
    """Continuous-treatment DML for a numeric natal feature.

    Round-7 upgrade per review §1.3: binarizing continuous treatments at
    the median destroys variance and any non-linear orb effect. This
    estimator treats the feature value AS-IS as a continuous treatment.

    For LinearDML with continuous T, the returned ATE is the
    **marginal effect per unit change in the feature** (in feature
    units). For an angular feature like `cross_lon_saturn` measured in
    degrees, an ATE of -0.0008 means each additional degree of Saturn-
    return separation drops marriage P by 0.08 percentage points.

    Returns a dict with the same keys as `estimate_ate_for_feature` so
    downstream code stays drop-in compatible.
    """
    if feature not in df.columns:
        return {"ate": float("nan"), "p_value": float("nan")}
    if not _is_natal_numeric(feature, df):
        return {
            "ate": float("nan"), "p_value": float("nan"),
            "reason": "feature not numeric",
        }
    natal_numerics = [
        c for c in df.columns
        if c != feature and _is_natal_numeric(c, df)
    ]
    if not natal_numerics:
        return {"ate": float("nan"), "p_value": float("nan")}

    T = pd.to_numeric(df[feature], errors="coerce").fillna(
        df[feature].median()
    ).to_numpy().astype(float)
    if T.std() < 1e-6:
        return {"ate": float("nan"), "p_value": float("nan"),
                "reason": "treatment has zero variance"}
    Y = df[y_col].astype(int).to_numpy()
    W = df[natal_numerics].fillna(0.0).to_numpy()

    try:
        est = LinearDML(
            model_y=GradientBoostingClassifier(
                n_estimators=50, max_depth=3, random_state=seed,
            ),
            model_t=GradientBoostingRegressor(
                n_estimators=50, max_depth=3, random_state=seed,
            ),
            discrete_treatment=False,    # continuous!
            discrete_outcome=True,
            random_state=seed,
        )
        est.fit(Y=Y, T=T, W=W)
        ate = float(np.atleast_1d(est.ate()).flatten()[0])
        try:
            inf = est.ate_inference()
            lo_arr, hi_arr = inf.conf_int_mean()
            ate_lower = float(np.atleast_1d(lo_arr).flatten()[0])
            ate_upper = float(np.atleast_1d(hi_arr).flatten()[0])
            ate_se = float(np.atleast_1d(inf.stderr_mean).flatten()[0])
            p_value = float(np.atleast_1d(inf.pvalue()).flatten()[0])
        except Exception:
            ate_lower = ate_upper = ate_se = p_value = float("nan")
        return {
            "ate": ate, "ate_se": ate_se,
            "ate_lower_95": ate_lower, "ate_upper_95": ate_upper,
            "p_value": p_value,
            "treatment_mean": float(T.mean()),
            "treatment_std": float(T.std()),
            "treatment_kind": "continuous",
        }
    except Exception as exc:
        logger.warning("continuous DML failed for %s: %s", feature, exc)
        return {"ate": float("nan"), "p_value": float("nan"),
                "error": str(exc), "treatment_kind": "continuous"}


def estimate_ate_for_feature(
    df: pd.DataFrame, feature: str, y_col: str = "y",
    seed: int = 42,
) -> dict[str, float]:
    """Double ML ATE: binarise `feature` at median → treatment T,
    use other natal numerics as W, estimate E[Y|T=1,W] - E[Y|T=0,W].

    Returns dict with ate, ate_se, ate_lower_95, ate_upper_95, p_value.
    """
    if feature not in df.columns:
        return {"ate": float("nan"), "p_value": float("nan")}
    # The feature itself must be numeric; reject categoricals/strings
    if not _is_natal_numeric(feature, df):
        return {
            "ate": float("nan"), "p_value": float("nan"),
            "reason": "feature not numeric",
        }
    natal_numerics = [
        c for c in df.columns
        if c != feature and _is_natal_numeric(c, df)
    ]
    if not natal_numerics:
        return {"ate": float("nan"), "p_value": float("nan")}

    # Binarise treatment
    feat_vals = df[feature].astype(float).fillna(df[feature].median())
    median = float(np.nanmedian(feat_vals))
    T = (feat_vals > median).astype(int).to_numpy()
    if T.sum() < 30 or (1 - T).sum() < 30:
        return {"ate": float("nan"), "p_value": float("nan"),
                "reason": "treatment too imbalanced"}

    Y = df[y_col].astype(int).to_numpy()
    W = df[natal_numerics].fillna(0.0).to_numpy()

    try:
        est = LinearDML(
            model_y=GradientBoostingClassifier(
                n_estimators=50, max_depth=3, random_state=seed,
            ),
            model_t=GradientBoostingClassifier(
                n_estimators=50, max_depth=3, random_state=seed,
            ),
            discrete_treatment=True,
            discrete_outcome=True,
            random_state=seed,
        )
        est.fit(Y=Y, T=T, W=W)
        # For LinearDML with no X, ate() returns a 1-d numpy array
        ate_arr = np.atleast_1d(est.ate())
        ate = float(ate_arr.flatten()[0])
        try:
            inf = est.ate_inference()
            lo_arr, hi_arr = inf.conf_int_mean()
            ate_lower = float(np.atleast_1d(lo_arr).flatten()[0])
            ate_upper = float(np.atleast_1d(hi_arr).flatten()[0])
            ate_se = float(np.atleast_1d(inf.stderr_mean).flatten()[0])
            p_value = float(np.atleast_1d(inf.pvalue()).flatten()[0])
        except Exception as exc:
            logger.debug("inference failed for %s: %s", feature, exc)
            ate_lower = ate_upper = ate_se = p_value = float("nan")
        return {
            "ate": ate, "ate_se": ate_se,
            "ate_lower_95": ate_lower, "ate_upper_95": ate_upper,
            "p_value": p_value, "median_threshold": median,
            "n_treated": int(T.sum()), "n_untreated": int((1 - T).sum()),
        }
    except Exception as exc:
        logger.warning("DML failed for %s: %s", feature, exc)
        return {"ate": float("nan"), "p_value": float("nan"), "error": str(exc)}


def plot_continuous_drishti(
    df: pd.DataFrame, feature: str, y_col: str = "y",
    output_dir: Path = Path("."), seed: int = 42
) -> None:
    """Generates a Continuous Causal Dose-Response curve for a feature.
    Uses NonParamDML to capture non-linear treatment effects (like aspects).
    """
    import matplotlib.pyplot as plt
    logger.info("Generating Continuous Dose-Response plot for %s...", feature)
    
    if feature not in df.columns or not _is_natal_numeric(feature, df):
        logger.warning("Feature %s is not valid for plotting.", feature)
        return

    natal_numerics = [c for c in df.columns if c != feature and _is_natal_numeric(c, df)]
    T = pd.to_numeric(df[feature], errors="coerce").fillna(df[feature].median()).to_numpy().astype(float)
    Y = df[y_col].astype(int).to_numpy()
    W = df[natal_numerics].fillna(0.0).to_numpy()

    # Use PolynomialFeatures on T with LinearDML to capture non-linear dose-response
    from sklearn.preprocessing import PolynomialFeatures
    try:
        T_poly = PolynomialFeatures(degree=3, include_bias=False).fit_transform(T.reshape(-1, 1))
        
        # LinearDML with continuous T allows multiple T columns for polynomial effects
        # model_t needs to handle multi-output (3 polynomial features), so we use RandomForestRegressor
        est = LinearDML(
            model_y=GradientBoostingRegressor(n_estimators=50, max_depth=3, random_state=seed),
            model_t=RandomForestRegressor(n_estimators=50, max_depth=5, random_state=seed),
            discrete_treatment=False,
            random_state=seed,
        )
        est.fit(Y=Y, T=T_poly, W=W)
        
        # Test treatments across the range
        T_test = np.linspace(np.percentile(T, 1), np.percentile(T, 99), 100)
        T_test_poly = PolynomialFeatures(degree=3, include_bias=False).fit_transform(T_test.reshape(-1, 1))
        
        # Calculate dose-response effect E[Y(T)] - E[Y(0)]
        # We can use est.effect which computes the effect of T1 vs T0
        T0 = np.zeros_like(T_test_poly)
        te_pred = est.effect(X=None, T0=T0, T1=T_test_poly)
        
        plt.figure(figsize=(10, 6))
        plt.plot(T_test, te_pred, color='blue', linewidth=2, label='Causal Effect vs T=0')
        plt.title(f"Continuous Causal Dose-Response: {feature} on {y_col}")
        plt.xlabel(f"{feature} (Degrees)")
        plt.ylabel(f"Effect on P({y_col})")
        plt.axhline(0, color='red', linestyle='--', alpha=0.5)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        out_path = output_dir / f"causal_dose_response_{feature}.png"
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Saved dose-response plot to %s", out_path)
    except Exception as exc:
        logger.error("Failed to generate plot: %s", exc)



# ---------- Main ----------

def run_phase6(
    *,
    natal_parquet: Path,
    events_csv: Path,
    shap_csv: Path,
    target_substring: str,
    output_dir: Path,
    top_k_features: int = 15,
    seed: int = 42,
    treatment_kind: str = "binary",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("loading SHAP top-%d features ...", top_k_features)
    top_features_raw = load_top_shap_features(shap_csv, k=top_k_features * 3)

    logger.info("building cohort + outcome ...")
    df = build_target_outcome(natal_parquet, events_csv, target_substring)

    # Filter SHAP features to those that exist in the natal frame
    top_features = [f for f in top_features_raw if f in df.columns][:top_k_features]
    if len(top_features) < top_k_features:
        # Fallback: rank natal numerics by univariate F-statistic
        from sklearn.feature_selection import f_classif
        natal_numerics = [c for c in df.columns if _is_natal_numeric(c, df)]
        X = df[natal_numerics].fillna(0.0).to_numpy()
        y = df["y"].to_numpy()
        try:
            scores, _ = f_classif(X, y)
        except Exception:
            scores = np.zeros(len(natal_numerics))
        ranked = sorted(
            zip(natal_numerics, scores, strict=True),
            key=lambda x: -(x[1] if not np.isnan(x[1]) else 0.0),
        )
        existing = set(top_features)
        for feat, _ in ranked:
            if feat not in existing:
                top_features.append(feat)
                existing.add(feat)
            if len(top_features) >= top_k_features:
                break
        logger.info(
            "filled top-features list via F-stat fallback to %d features",
            len(top_features),
        )
    logger.info("top features for causal analysis: %s", top_features[:5])

    logger.info("estimating ATEs ...")
    results = []
    shap_imp = pd.read_csv(shap_csv).set_index(
        "feature" if "feature" in pd.read_csv(shap_csv).columns else 1
    )
    if "mean_abs_shap" in shap_imp.columns:
        shap_lookup = shap_imp["mean_abs_shap"].to_dict()
    else:
        shap_lookup = {}

    estimator = (
        estimate_ate_continuous if treatment_kind in ("continuous", "continuous_plot")
        else estimate_ate_for_feature
    )
    logger.info("treatment_kind=%s (estimator=%s)",
                treatment_kind, estimator.__name__)
    
    # If continuous_plot is requested, plot the top feature or specific feature
    if treatment_kind == "continuous_plot":
        # Check if dist_venus_saturn is present and plot it
        plot_feat = "dist_venus_saturn" if "dist_venus_saturn" in df.columns else top_features[0]
        plot_continuous_drishti(df, plot_feat, "y", output_dir, seed)

    for feat in top_features:
        if feat not in df.columns:
            logger.warning("feature %s not in df — skip", feat)
            continue
        res = estimator(df, feat, seed=seed)
        res["feature"] = feat
        res["shap_importance"] = shap_lookup.get(feat, float("nan"))
        results.append(res)
        logger.info(
            "  %-30s  ATE=%+.4g  p=%.4f  shap=%.4f",
            feat, res.get("ate", float("nan")), res.get("p_value", float("nan")),
            res.get("shap_importance", float("nan")),
        )

    # Sort by absolute ATE
    results.sort(key=lambda r: -abs(r.get("ate", 0.0)) if not np.isnan(r.get("ate", float("nan"))) else 0)

    # Write CSV
    csv_path = output_dir / f"causal_{target_substring}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "feature", "shap_importance", "ate", "ate_se",
            "ate_lower_95", "ate_upper_95", "p_value",
            "median_threshold", "n_treated", "n_untreated",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = output_dir / f"report_{target_substring}.md"
    lines = [
        f"# Phase 6 — Causal Inference for `{target_substring}`",
        "",
        f"_Generated {now}_",
        "",
        f"- Cohort: {len(df):,} people  ({df['y'].sum():,} positives)",
        f"- Top-{top_k_features} SHAP features analysed",
        "",
        "## Causal vs Confounded",
        "",
        "**ATE > 0**: increasing this feature (above its median) raises P(event).",
        "**|ATE| large + p < 0.05**: strong causal evidence beyond confounding.",
        "**SHAP high + ATE near 0**: feature is a confounded correlate — its",
        "predictive power comes from co-varying with the actual cause.",
        "",
        "| Feature | SHAP | ATE | 95% CI | p-value | Verdict |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        feat = r["feature"]
        shap = r.get("shap_importance", float("nan"))
        ate = r.get("ate", float("nan"))
        lo = r.get("ate_lower_95", float("nan"))
        hi = r.get("ate_upper_95", float("nan"))
        p = r.get("p_value", float("nan"))
        if np.isnan(ate):
            verdict = "n/a"
        elif p < 0.05 and abs(ate) > 0.01:
            verdict = "**CAUSAL**"
        elif abs(ate) < 0.005 and not np.isnan(shap) and shap > 0.05:
            verdict = "confounded?"
        else:
            verdict = "weak"
        ci = f"[{lo:+.4f}, {hi:+.4f}]" if not np.isnan(lo) else "n/a"
        lines.append(
            f"| `{feat}` | {shap:.4f} | {ate:+.4f} | {ci} | {p:.4f} | {verdict} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "Each row tests: if we COULD intervene on this feature in a chart",
        "(holding all others fixed), would the event probability change?",
        "DML separates this from mere correlation by absorbing the rest of",
        "the natal features as covariates W.",
        "",
        "Features marked **CAUSAL** are the ones whose change would actually",
        "shift outcomes — these are 'real' astrological drivers. Features",
        "marked `confounded?` carry SHAP signal but no causal effect — they",
        "are markers, not levers.",
        "",
        f"Full CSV in `{csv_path.name}`.",
    ])

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report to %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.causal_inference",
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
        "--shap", type=Path,
        default=Path(
            "data/ml_runs/multiclass_event_root_20260518T221902Z/"
            "feature_importance.csv"
        ),
    )
    parser.add_argument(
        "--target", type=str, default="marriage",
        help="event_root substring to use as binary outcome",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/causal_round6_phase6/"),
    )
    parser.add_argument("--top-k", type=int, default=15)
    parser.add_argument(
        "--treatment-kind", choices=("binary", "continuous", "continuous_plot"), default="binary",
        help="binary = legacy median-split; continuous = LinearDML; continuous_plot = NonParamDML plotting.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_phase6(
        natal_parquet=args.natal,
        events_csv=args.events,
        shap_csv=args.shap,
        target_substring=args.target,
        output_dir=args.output,
        top_k_features=args.top_k,
        treatment_kind=args.treatment_kind,
    )
    print(f"Phase 6 artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
