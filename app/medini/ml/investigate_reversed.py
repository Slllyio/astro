"""Tier 1 §1: investigate the 7 BPHS rules REVERSED by the causal audit.

Hypothesis (from auto-mode chat): the 7 reversed rules cluster on
3rd / 6th house "upachaya" placements. Classical interpretation:
upachaya houses promote effort-based, often unrecorded growth.
events_all.csv records DRAMATIC events; perhaps the rule's true
positive effect plays out on event SUBTYPES that aren't well
captured (or only on specific eras).

Three stratification tests per reversed rule:

1. **Subtype split**: re-run DML on POSITIVE-subtype events only vs
   NEGATIVE-subtype only vs the full mixture. If the reversal flips
   on a specific subtype, the rule isn't wrong — it's miscalibrated
   against the modern taxonomy.

2. **Era split**: pre-1900 vs 1900-1950 vs post-1950 birth-year
   strata. Classical Vedic was developed pre-1900; era-stratified
   ATE tests whether the rule held in its original context but
   broke under modern conditions.

3. **Coverage check**: how does the antecedent group's overall
   event rate compare to the rest of the cohort? If they have
   FEWER events of ALL types (not just the consequent), the
   reversal is a coverage artefact ("quiet life" people).

Output: per-rule stratified ATE table + interpretation note.
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
import swisseph as swe
from econml.dml import LinearDML
from sklearn.ensemble import GradientBoostingClassifier

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


# The 7 reversed rules from data/ml_runs/bphs_causal_audit/
REVERSED_RULES: tuple[dict, ...] = (
    {
        "name": "sun_in_9th_father",
        "antecedent_col": "house_sun", "antecedent_val": 9,
        "consequent": "family",
        "expected_direction": "promotes",
    },
    {
        "name": "saturn_in_6th_service",
        "antecedent_col": "house_saturn", "antecedent_val": 6,
        "consequent": "work",
        "expected_direction": "promotes",
    },
    {
        "name": "mercury_in_6th_business",
        "antecedent_col": "house_mercury", "antecedent_val": 6,
        "consequent": "work",
        "expected_direction": "promotes",
    },
    {
        "name": "venus_in_5th_romance",
        "antecedent_col": "house_venus", "antecedent_val": 5,
        "consequent": "relationship",
        "expected_direction": "promotes",
    },
    {
        "name": "mercury_in_3rd_writing",
        "antecedent_col": "house_mercury", "antecedent_val": 3,
        "consequent": "published/ exhibited/ released",
        "expected_direction": "promotes",
    },
    {
        "name": "saturn_in_6th_chronic_disease",
        "antecedent_col": "house_saturn", "antecedent_val": 6,
        "consequent": "health",
        "expected_direction": "promotes",
    },
    {
        "name": "venus_in_3rd_arts",
        "antecedent_col": "house_venus", "antecedent_val": 3,
        "consequent": "published/ exhibited/ released",
        "expected_direction": "promotes",
    },
)


# ---------- Cohort + outcome helpers ----------

NON_FEATURE_NAMES: frozenset[str] = frozenset({
    "name", "rodden_rating", "categories_raw", "categories_lower",
    "categories_tokens", "source_url", "_n", "y",
    "event_date", "event_jd", "birth_jd", "event_root",
    "event_subtype", "is_event",
})


def _is_numeric_feature(col: str, df: pd.DataFrame) -> bool:
    if col in NON_FEATURE_NAMES:
        return False
    s = df[col]
    if not pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
        return False
    return s.nunique() > 1


def _build_cohort(
    natal_parquet: Path, events_csv: Path, raw_csv: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (natal_df_with_birth_year, events_df)."""
    natal = pd.read_parquet(natal_parquet)
    natal["_n"] = natal["name"].astype(str).str.strip().str.lower()
    natal = natal.drop_duplicates(subset="_n")

    events = pd.read_csv(events_csv)
    events["_n"] = events["name"].astype(str).str.strip().str.lower()
    events["root_lower"] = events["event_root"].astype(str).str.lower().str.strip()
    events["event_subtype_clean"] = (
        events["event_subtype"].astype(str).str.strip().str.lower()
    )
    events["event_year"] = pd.to_numeric(events["event_year"], errors="coerce")

    # Birth year per person from raw CSV
    raw = pd.read_csv(raw_csv, low_memory=False)
    raw["_n"] = raw["name"].astype(str).str.strip().str.lower()
    raw["birth_year"] = pd.to_datetime(
        raw["date_of_birth"], errors="coerce",
    ).dt.year
    raw = raw[["_n", "birth_year"]].drop_duplicates(subset="_n")

    natal = natal.merge(raw, on="_n", how="left")
    return natal, events


def _dml_ate(
    natal_subset: pd.DataFrame, antecedent_col: str, antecedent_val: int,
    positive_names: set[str], seed: int = 42,
) -> dict[str, float]:
    """Run a quick DML on a subset, return ATE + p-value."""
    natal_subset = natal_subset.copy()
    natal_subset["y"] = natal_subset["_n"].isin(positive_names).astype(int)
    if natal_subset["y"].sum() < 20:
        return {"ate": float("nan"), "p_value": float("nan"),
                "n": len(natal_subset), "n_positive": int(natal_subset["y"].sum()),
                "reason": "too few positives"}
    T = (natal_subset[antecedent_col].astype(int) == antecedent_val).astype(int).to_numpy()
    if T.sum() < 30 or (1 - T).sum() < 30:
        return {"ate": float("nan"), "p_value": float("nan"),
                "n": len(natal_subset), "n_positive": int(natal_subset["y"].sum()),
                "n_treated": int(T.sum()),
                "reason": "treatment too imbalanced"}
    natal_numerics = [
        c for c in natal_subset.columns
        if c != antecedent_col and _is_numeric_feature(c, natal_subset)
    ]
    W = natal_subset[natal_numerics].fillna(0.0).to_numpy()
    Y = natal_subset["y"].to_numpy()
    try:
        est = LinearDML(
            model_y=GradientBoostingClassifier(
                n_estimators=40, max_depth=3, random_state=seed,
            ),
            model_t=GradientBoostingClassifier(
                n_estimators=40, max_depth=3, random_state=seed,
            ),
            discrete_treatment=True, discrete_outcome=True, random_state=seed,
        )
        est.fit(Y=Y, T=T, W=W)
        ate = float(np.atleast_1d(est.ate()).flatten()[0])
        try:
            inf = est.ate_inference()
            p = float(np.atleast_1d(inf.pvalue()).flatten()[0])
        except Exception:
            p = float("nan")
        return {
            "ate": ate, "p_value": p,
            "n": len(natal_subset),
            "n_positive": int(natal_subset["y"].sum()),
            "n_treated": int(T.sum()),
        }
    except Exception as exc:
        return {"ate": float("nan"), "p_value": float("nan"),
                "n": len(natal_subset),
                "reason": f"DML: {exc}"}


# ---------- Stratification logic ----------

def _split_by_subtype(
    events: pd.DataFrame, consequent: str,
) -> dict[str, set[str]]:
    """For each event_subtype of the consequent class, collect the
    set of people who had ≥1 event of that subtype.

    Returns {subtype_label: {name_lower}}. The 'ALL' key collects every
    person with ANY event of the consequent class.
    """
    sub = events.loc[events["root_lower"] == consequent.lower()]
    out: dict[str, set[str]] = {"ALL": set(sub["_n"])}
    # Top subtypes only (≥ 30 occurrences)
    sub_counts = sub["event_subtype_clean"].value_counts()
    for st, n in sub_counts.head(8).items():
        if n < 30 or st == "nan":
            continue
        out[f"subtype:{st}"] = set(sub.loc[sub["event_subtype_clean"] == st, "_n"])
    return out


def _stratify_by_era(natal: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "ALL": natal,
        "era:pre_1900": natal.loc[natal["birth_year"] < 1900],
        "era:1900-1949": natal.loc[
            (natal["birth_year"] >= 1900) & (natal["birth_year"] < 1950)
        ],
        "era:1950+": natal.loc[natal["birth_year"] >= 1950],
    }


# ---------- Coverage check ----------

def _coverage_check(
    natal: pd.DataFrame, events: pd.DataFrame,
    antecedent_col: str, antecedent_val: int,
) -> dict[str, float]:
    """For people whose antecedent matches vs everyone else, compute
    AVERAGE number of recorded events per person across all types.

    Returns mean and ratio. If antecedent group's mean is materially
    lower (< 90% of comparison), the reversed-rule result may be a
    'quiet life' coverage artefact.
    """
    counts_per_person = events.groupby("_n").size()
    natal = natal.copy()
    natal["event_count"] = natal["_n"].map(counts_per_person).fillna(0)
    treated = natal.loc[natal[antecedent_col].astype(int) == antecedent_val]
    untreated = natal.loc[natal[antecedent_col].astype(int) != antecedent_val]
    mean_t = float(treated["event_count"].mean()) if len(treated) else 0.0
    mean_u = float(untreated["event_count"].mean()) if len(untreated) else 0.0
    return {
        "n_treated": len(treated),
        "n_untreated": len(untreated),
        "mean_events_treated": mean_t,
        "mean_events_untreated": mean_u,
        "ratio_treated_over_untreated": mean_t / mean_u if mean_u > 0 else float("nan"),
    }


# ---------- Main investigation ----------

def run_investigation(
    *,
    natal_parquet: Path, events_csv: Path, raw_csv: Path,
    output_dir: Path, seed: int = 42,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("loading cohort ...")
    natal, events = _build_cohort(natal_parquet, events_csv, raw_csv)
    cohort_names = set(events["_n"]) & set(natal["_n"])
    natal_cohort = natal.loc[natal["_n"].isin(cohort_names)].copy()
    logger.info("cohort: %d people", len(natal_cohort))

    all_results = []
    for rule in REVERSED_RULES:
        logger.info("=" * 60)
        logger.info("Rule: %s (consequent=%s)", rule["name"], rule["consequent"])

        # Coverage check
        coverage = _coverage_check(
            natal_cohort, events,
            rule["antecedent_col"], rule["antecedent_val"],
        )
        logger.info(
            "  coverage: treated_mean_events=%.2f  untreated=%.2f  ratio=%.3f",
            coverage["mean_events_treated"],
            coverage["mean_events_untreated"],
            coverage["ratio_treated_over_untreated"],
        )

        # Subtype split
        subtype_groups = _split_by_subtype(events, rule["consequent"])
        for label, positives in subtype_groups.items():
            res = _dml_ate(
                natal_cohort,
                rule["antecedent_col"], rule["antecedent_val"],
                positives, seed=seed,
            )
            res.update({
                "rule": rule["name"],
                "stratification": label,
                "stratification_kind": "subtype" if label != "ALL" else "ALL",
                "n_in_stratum": res.get("n"),
                "coverage_ratio": coverage["ratio_treated_over_untreated"],
            })
            logger.info(
                "  [%s] ate=%+.4f  p=%.4f  n_pos=%s",
                label, res.get("ate", float("nan")),
                res.get("p_value", float("nan")),
                res.get("n_positive", "?"),
            )
            all_results.append(res)

        # Era split — ALL-subtype consequent in each era
        positives_all = subtype_groups.get("ALL", set())
        for era_label, era_df in _stratify_by_era(natal_cohort).items():
            if era_label == "ALL":
                continue
            if len(era_df) < 100:
                continue
            res = _dml_ate(
                era_df,
                rule["antecedent_col"], rule["antecedent_val"],
                positives_all, seed=seed,
            )
            res.update({
                "rule": rule["name"],
                "stratification": era_label,
                "stratification_kind": "era",
                "n_in_stratum": res.get("n"),
                "coverage_ratio": coverage["ratio_treated_over_untreated"],
            })
            logger.info(
                "  [%s] ate=%+.4f  p=%.4f  n_strat=%d",
                era_label, res.get("ate", float("nan")),
                res.get("p_value", float("nan")),
                len(era_df),
            )
            all_results.append(res)

    # Write CSV
    csv_path = output_dir / "reversed_investigation.csv"
    fields = [
        "rule", "stratification", "stratification_kind", "n_in_stratum",
        "n_positive", "n_treated", "ate", "p_value",
        "coverage_ratio", "reason",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)
    logger.info("wrote %s", csv_path)

    # Synthesis: for each rule, identify whether ANY stratum shows
    # the expected (positive) ATE direction.
    synthesis = []
    for rule in REVERSED_RULES:
        rule_results = [r for r in all_results if r["rule"] == rule["name"]]
        positive_strata = [
            r for r in rule_results
            if not np.isnan(r.get("ate") or 0)
            and r.get("ate", 0) > 0
            and r.get("p_value", 1) < 0.10
        ]
        synthesis.append({
            "rule": rule["name"],
            "consequent": rule["consequent"],
            "any_stratum_positive_at_p10": len(positive_strata),
            "positive_strata": "; ".join(r["stratification"] for r in positive_strata),
            "coverage_ratio": rule_results[0].get("coverage_ratio")
            if rule_results else float("nan"),
            "interpretation": _interpret(
                rule_results,
                coverage_ratio=rule_results[0].get("coverage_ratio", 1.0)
                if rule_results else 1.0,
            ),
        })

    syn_path = output_dir / "synthesis.csv"
    syn_fields = list(synthesis[0].keys())
    with syn_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=syn_fields)
        writer.writeheader()
        for s in synthesis:
            writer.writerow(s)

    # Markdown report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = output_dir / "report.md"
    lines = [
        "# Tier-1 §1 — Reversed-rule investigation",
        "",
        f"_Generated {now}_",
        "",
        "Stratified DML on the 7 BPHS rules the Round-7 audit marked",
        "REVERSED. For each rule we re-ran the causal estimator on:",
        "- the full cohort (baseline = audit result)",
        "- each subtype of the consequent event class separately",
        "- pre-1900 / 1900-1949 / 1950+ birth-era splits",
        "- coverage check: do treated-group people have fewer overall events?",
        "",
        "## Per-rule synthesis",
        "",
        "| Rule | Consequent | Coverage ratio | Positive strata at p<0.10 | Interpretation |",
        "|---|---|---|---|---|",
    ]
    for s in synthesis:
        ratio = s["coverage_ratio"]
        ratio_str = f"{ratio:.2f}" if ratio is not None and not np.isnan(ratio) else "n/a"
        lines.append(
            f"| `{s['rule']}` | {s['consequent']} | {ratio_str} | "
            f"{s['any_stratum_positive_at_p10']} ({s['positive_strata']}) | "
            f"{s['interpretation']} |"
        )

    lines.extend([
        "",
        "## How to read coverage_ratio",
        "",
        "- = mean_recorded_events(treated) / mean_recorded_events(untreated)",
        "- < 0.90 → treated group has FEWER recorded events overall — the",
        "  reversal may be a *quiet-life* coverage artefact, not a real",
        "  contradiction of the rule.",
        "- > 1.10 → treated group has MORE events overall (rule is",
        "  associated with general visibility); a reversal here means",
        "  the rule's specific consequent is genuinely lower despite",
        "  higher overall coverage. That's a real contradiction.",
        "- ≈ 1.00 → coverage neutral; reversal is consequent-specific.",
        "",
        "Full per-stratum table: `reversed_investigation.csv`",
    ])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote %s", report)


def _interpret(rule_results: list[dict], coverage_ratio: float) -> str:
    """Free-text verdict per rule."""
    if np.isnan(coverage_ratio):
        coverage_ratio = 1.0
    if coverage_ratio < 0.85:
        return "coverage artefact (treated group has 15%+ fewer recorded events)"
    # Look for positive strata
    positives = [
        r for r in rule_results
        if not np.isnan(r.get("ate") or 0)
        and r.get("ate", 0) > 0
        and r.get("p_value", 1) < 0.10
    ]
    if positives:
        labels = ", ".join(p["stratification"] for p in positives)
        return f"reversal flips positive in: {labels}"
    # All strata still negative
    return "reversal consistent across strata — genuine contradiction"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.investigate_reversed",
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
        "--raw", type=Path,
        default=Path("data/astro_databank/merged_with_events.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/tier1_reversed_investigation/"),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_investigation(
        natal_parquet=args.natal,
        events_csv=args.events,
        raw_csv=args.raw,
        output_dir=args.output,
    )
    print(f"Investigation artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
