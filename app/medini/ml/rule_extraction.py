"""RuleFit-style rule extraction from trained XGBoost models.

Walks every leaf in every tree of a saved XGBoost model, materializes
the leaf's root-to-leaf path as a logical IF-THEN rule, computes that
rule's activation column on the training data, then fits a sparse
Lasso logistic regression to select the rules that carry the most
class-specific signal.

The output is per-event-class CSV + Markdown reports listing the
most discriminative rules, sorted by ``|coefficient| × support``. These
read like classical Vedic rules but were discovered empirically:

  IF cross_lon_saturn < 5.2 AND active_md_lord == "Venus":
      P(marriage) shifts by +0.18   (support: 43 / 14166 rows)

CLI
===
    python -m app.medini.ml.rule_extraction \\
        --model data/ml_runs/multiclass_event_root_20260518T221902Z/model.json \\
        --features app/medini/data/event_corpus_round5_all.parquet \\
        --target-column event_root \\
        --output data/ml_runs/rules_round6_phase1/

Output: one rules.csv + report.md per top class.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from app.medini.ml.train_classifier import NON_FEATURE_COLUMNS, select_features

logger = logging.getLogger(__name__)


# ---------- Iteration 2: filter seasonal features ----------
#
# Day-of-year features at transit time encode "what month is this" and
# act as a confounder when event classes have seasonal incidence (deaths
# peak in winter, prizes in announcement season, etc.). Rules whose
# ONLY discriminator is one of these are sociology, not astrology.
#
# Strategy: rules retain seasonality features only when COMBINED with
# at least one non-seasonal feature (cross-feature, dasha, drishti,
# divisional chart, yoga, etc.). Pure-seasonal predicates are filtered.

_SEASONAL_FEATURE_SUFFIXES: tuple[str, ...] = (
    "_sun",  # any t_*_sun feature (declination, velocity, etc.)
)
_SEASONAL_FEATURE_NAMES: frozenset[str] = frozenset({
    "t_dec_sun", "t_vel_sun", "t_lon_sun", "t_lat_sun",
    "t_nak_sun", "t_house_sun", "t_house_pos_sun",
    "t_nak_pos_sun", "t_combust_sun", "t_rx_sun",
    "t_lagna_lon", "t_lagna_degree_in_sign", "t_lagna_sign",
    "t_tithi_angle", "t_yoga_angle", "t_moon_phase_normalized",
    "t_panchanga_tithi", "t_panchanga_paksha",
    "t_panchanga_karana", "t_panchanga_yoga", "t_panchanga_vara",
})


def _is_seasonal_feature(feature: str) -> bool:
    """True if a feature is essentially calendar-day-of-event.

    Strict: only flags the explicit list. Doesn't catch every possible
    seasonal proxy but covers the obvious culprits.
    """
    return feature in _SEASONAL_FEATURE_NAMES


def _is_pure_seasonal_rule(rule: "Rule") -> bool:
    """True if EVERY predicate in the rule is a seasonal feature.

    A rule with `t_dec_sun < 23.05 AND t_house_sun >= 9` is pure
    seasonal (both predicates encode date-of-year only). A rule with
    `t_dec_sun < 23.05 AND cross_lon_saturn < 5` is NOT pure seasonal
    (the second predicate is genuine cross-feature signal).
    """
    if not rule.predicates:
        return False
    return all(_is_seasonal_feature(p.feature) for p in rule.predicates)


# ---------- Iteration 2: human-readable translation ----------

def humanize_predicate(predicate: "RulePredicate") -> str:
    """Translate a raw predicate into Vedic-style English.

    Examples:
      `cross_lon_saturn < 5.2` → "Saturn within 5.2° of natal Saturn"
      `active_md_lord == "Venus"` → "Venus Mahadasha running"
      `house_pos_sun < 6` → "Sun in 1st-6th house (continuous)"
      `yoga_gajakesari >= 1` → "Gajakesari yoga active"
    """
    f = predicate.feature
    op = predicate.op
    t = predicate.threshold

    if f.startswith("cross_lon_"):
        planet = f.replace("cross_lon_", "").title()
        if op == "<":
            return f"Transit {planet} within {t:.1f}° of natal {planet}"
        return f"Transit {planet} > {t:.1f}° from natal {planet}"
    if f.startswith("aspect_orb_"):
        parts = f.replace("aspect_orb_", "").split("_")
        if len(parts) == 2:
            p1, p2 = parts[0].title(), parts[1].title()
            verb = "within" if op == "<" else "beyond"
            return f"{p1}→{p2} aspect orb {verb} {t:.1f}°"
    if f.startswith("drishti_"):
        parts = f.replace("drishti_", "").split("_")
        if len(parts) == 2:
            p1, p2 = parts[0].title(), parts[1].title()
            verb = "casts" if op == ">=" else "does not cast"
            return f"{p1} {verb} drishti on {p2}"
    if f.startswith("active_md_lord"):
        return f"Mahadasha lord {op} {t}"  # categorical encodings appear as numeric
    if f.startswith("active_ad_lord"):
        return f"Antardasha lord {op} {t}"
    if f.startswith("active_pd_lord"):
        return f"Pratyantar lord {op} {t}"
    if f.startswith("yoga_"):
        yoga = f.replace("yoga_", "").replace("_", "-").title()
        return f"{yoga} yoga {'active' if op == '>=' else 'inactive'}"
    if f.startswith("house_pos_"):
        planet = f.replace("house_pos_", "").title()
        return f"{planet} continuous house position {op} {t:.2f}"
    if f.startswith("house_from_moon_"):
        planet = f.replace("house_from_moon_", "").title()
        return f"{planet} {op} {t:.0f}-th house from Moon (Chandra Lagna)"
    if f.startswith("house_from_sun_"):
        planet = f.replace("house_from_sun_", "").title()
        return f"{planet} {op} {t:.0f}-th house from Sun (Surya Lagna)"
    if f.startswith("d9_") and f.endswith("_sign"):
        planet = f.replace("d9_", "").replace("_sign", "").title()
        return f"D9 (Navamsa) {planet} sign {op} {t:.0f}"
    if f.startswith("d12_") and f.endswith("_sign"):
        planet = f.replace("d12_", "").replace("_sign", "").title()
        return f"D12 (Dwadasamsa) {planet} sign {op} {t:.0f}"
    if f.startswith("sade_sati_") or f in ("kantaka_shani", "ashtama_shani"):
        return f"{f.replace('_', ' ').title()} {'active' if op == '>=' else 'inactive'}"
    if f.startswith("md_elapsed_years"):
        return f"Mahadasha {op} {t:.1f} years in"
    if f.startswith("ad_elapsed_years"):
        return f"Antardasha {op} {t:.1f} years in"
    if f.startswith("transit_bav_"):
        planet = f.replace("transit_bav_", "").title()
        return f"Transit {planet} bav-bindu strength {op} {t:.1f}"
    if f.startswith("t_"):
        return f"Transit {f[2:]} {op} {t:.2f}"
    # Fallback
    return f"{f} {op} {t:.4g}"


def _classify_rule_provenance(rule: "Rule") -> str:
    """Tag rule as natal-only / transit-only / composite.

    composite rules (mixing natal + transit) carry the highest-signal
    Vedic-astrology patterns.
    """
    has_natal = any(not p.feature.startswith("t_") for p in rule.predicates)
    has_transit = any(p.feature.startswith("t_") for p in rule.predicates)
    if has_natal and has_transit:
        return "composite"
    if has_transit:
        return "transit-only"
    return "natal-only"


# ---------- Tree path → rule ----------

@dataclass(frozen=True)
class RulePredicate:
    """One condition in a path: e.g. ``feature < 5.2``."""

    feature: str
    op: str           # "<", ">="
    threshold: float

    def as_string(self) -> str:
        return f"{self.feature} {self.op} {self.threshold:.4g}"


@dataclass(frozen=True)
class Rule:
    """A path from root to leaf in an XGBoost tree, as a conjunction of
    predicates plus the leaf's contribution to the model's logit output.
    """

    predicates: tuple[RulePredicate, ...]
    tree_index: int
    leaf_value: float

    def as_string(self) -> str:
        if not self.predicates:
            return "TRUE  (constant)"
        return " AND ".join(p.as_string() for p in self.predicates)

    def matches(self, row: pd.Series) -> bool:
        """Evaluate the conjunction against one row. NaN values trigger
        the 'missing' branch in XGBoost — we approximate by treating
        NaN as failing the condition (conservative)."""
        for p in self.predicates:
            value = row.get(p.feature)
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return False
            try:
                v = float(value)
            except (ValueError, TypeError):
                return False
            if p.op == "<" and not (v < p.threshold):
                return False
            if p.op == ">=" and not (v >= p.threshold):
                return False
        return True


def extract_rules_from_booster(
    booster: xgb.Booster,
    max_depth_per_path: int = 8,
) -> list[Rule]:
    """Materialize the root-to-leaf path of every leaf in the booster.

    Uses booster.trees_to_dataframe() which returns one row per node
    with columns: Tree, Node, ID, Feature, Split, Yes, No, Missing,
    Gain, Cover, Category. Leaves have Feature == "Leaf" and Split == NaN.

    Returns a list of Rule objects, one per (leaf, tree) pair.
    """
    df = booster.trees_to_dataframe()
    rules: list[Rule] = []

    # For each tree, walk DFS from root to each leaf
    for tree_idx, tree_df in df.groupby("Tree"):
        # Build children + parent lookup
        node_by_id: dict[str, dict] = {
            row["ID"]: row.to_dict() for _, row in tree_df.iterrows()
        }
        # Find leaves
        leaves = [
            row for _, row in tree_df.iterrows()
            if row["Feature"] == "Leaf"
        ]
        # Build parent map: child_id -> (parent_id, branch)
        parent: dict[str, tuple[str, str]] = {}
        for nid, node in node_by_id.items():
            if node["Feature"] == "Leaf":
                continue
            yes_id = node.get("Yes")
            no_id = node.get("No")
            if yes_id and yes_id in node_by_id:
                parent[yes_id] = (nid, "yes")
            if no_id and no_id in node_by_id:
                parent[no_id] = (nid, "no")

        for leaf in leaves:
            leaf_id = leaf["ID"]
            leaf_value = float(leaf["Gain"])  # Gain holds leaf weight for leaves
            # Walk up to root collecting predicates
            preds: list[RulePredicate] = []
            current = leaf_id
            steps = 0
            while current in parent and steps < max_depth_per_path:
                pid, branch = parent[current]
                pnode = node_by_id[pid]
                feature = str(pnode["Feature"])
                threshold = float(pnode["Split"])
                # XGBoost convention: Yes branch = feature < threshold;
                # No branch = feature >= threshold.
                op = "<" if branch == "yes" else ">="
                preds.append(RulePredicate(feature, op, threshold))
                current = pid
                steps += 1
            preds.reverse()
            rules.append(Rule(
                predicates=tuple(preds),
                tree_index=int(tree_idx),
                leaf_value=leaf_value,
            ))

    logger.info("extracted %d rules from %d trees", len(rules), df["Tree"].nunique())
    return rules


# ---------- Rule activation matrix ----------

def compute_activation_matrix(
    rules: list[Rule], X: pd.DataFrame, max_rules: int = 2000,
) -> tuple[np.ndarray, list[Rule]]:
    """For each (rule, row) pair, compute 1/0 activation. Memory budget
    drives ``max_rules`` cap: 14k rows × 2k rules × 1 byte ≈ 28MB.

    Selects rules by ``|leaf_value|`` (largest contributors first) to
    cap the matrix at ``max_rules`` columns.
    """
    rules_sorted = sorted(rules, key=lambda r: -abs(r.leaf_value))[:max_rules]
    n_rows = len(X)
    n_cols = len(rules_sorted)
    logger.info("activation matrix shape: (%d, %d)", n_rows, n_cols)
    activation = np.zeros((n_rows, n_cols), dtype=np.uint8)
    for col, rule in enumerate(rules_sorted):
        if not rule.predicates:
            activation[:, col] = 1
            continue
        # Vectorised evaluation: build a mask per predicate, AND them.
        mask = np.ones(n_rows, dtype=bool)
        for p in rule.predicates:
            if p.feature not in X.columns:
                mask &= False
                break
            col_vals = pd.to_numeric(X[p.feature], errors="coerce").to_numpy()
            if p.op == "<":
                step_mask = col_vals < p.threshold
            else:
                step_mask = col_vals >= p.threshold
            # NaN comparisons return False — that's the conservative
            # "missing fails predicate" convention.
            mask &= np.where(np.isnan(col_vals), False, step_mask)
        activation[:, col] = mask.astype(np.uint8)
    return activation, rules_sorted


# ---------- Lasso rule selection ----------

def fit_sparse_rule_selector(
    activation: np.ndarray,
    y: pd.Series,
    *,
    target_nonzero: int = 30,
    Cs: tuple[float, ...] = (0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1),
) -> tuple[np.ndarray, float, float]:
    """Fit L1-regularised logistic regression on rule activations.

    Iteration-2 strategy: choose the C that gives a non-zero count closest
    to ``target_nonzero`` (so we get a focused rule set, not 400 rules).
    Returns (coefficients, holdout_auc, chosen_C).
    """
    from sklearn.model_selection import train_test_split
    X_tr, X_val, y_tr, y_val = train_test_split(
        activation, y.to_numpy(), test_size=0.2, random_state=42, stratify=y,
    )

    best_coef: np.ndarray | None = None
    best_auc = 0.0
    best_c: float = 0.0
    best_distance_from_target = 10**9
    for c_val in Cs:
        try:
            clf = LogisticRegression(
                penalty="l1", solver="saga", C=c_val,
                max_iter=2000, random_state=42,
            )
            clf.fit(X_tr, y_tr)
        except Exception as exc:
            logger.warning("LogisticRegression(C=%g) failed: %s", c_val, exc)
            continue
        proba = clf.predict_proba(X_val)[:, 1]
        try:
            auc = float(roc_auc_score(y_val, proba))
        except ValueError:
            continue
        n_nonzero = int(np.sum(clf.coef_[0] != 0))
        distance = abs(n_nonzero - target_nonzero)
        logger.info(
            "  C=%g  nonzero=%d  auc=%.4f  dist_from_target=%d",
            c_val, n_nonzero, auc, distance,
        )
        # Prefer Cs that hit the target count, breaking ties by AUC
        if (distance < best_distance_from_target) or (
            distance == best_distance_from_target and auc > best_auc
        ):
            best_distance_from_target = distance
            best_auc = auc
            best_coef = clf.coef_[0]
            best_c = c_val
    if best_coef is None:
        return np.zeros(activation.shape[1]), 0.0, 0.0
    return best_coef, best_auc, best_c


# ---------- Output writers ----------

def _write_rules_csv(
    path: Path,
    rules: list[Rule],
    coefs: np.ndarray,
    activation: np.ndarray,
    target_name: str,
    y_class: pd.Series,
    drop_seasonal: bool = True,
) -> int:
    """Write a CSV of non-zero rules sorted by |coefficient| × support.

    Iteration-2 columns: + ``rule_english`` (humanized), + ``provenance``
    (natal/transit/composite), + ``pct_class_explained`` (of positives
    in this class, % satisfying the rule), + ``seasonal_only`` flag.
    Rules where ``seasonal_only`` is True are filtered when
    ``drop_seasonal`` is True.
    """
    n_positives = int(y_class.sum())
    rows = []
    # Build index map once (rules.index() is O(N) per call → O(N²) total)
    rule_to_idx = {id(r): i for i, r in enumerate(rules)}
    for rule, coef in zip(rules, coefs, strict=True):
        if coef == 0:
            continue
        seasonal = _is_pure_seasonal_rule(rule)
        if drop_seasonal and seasonal:
            continue
        col_idx = rule_to_idx[id(rule)]
        mask = activation[:, col_idx].astype(bool)
        support = int(mask.sum())
        pos_satisfied = int((mask & y_class.astype(bool).to_numpy()).sum())
        pct_class = (pos_satisfied / max(n_positives, 1)) * 100
        rows.append({
            "rule_english": " AND ".join(
                humanize_predicate(p) for p in rule.predicates
            ),
            "rule_raw": rule.as_string(),
            "coefficient": float(coef),
            "support": support,
            "support_pct": f"{(support / len(y_class)) * 100:.1f}",
            "pct_class_explained": f"{pct_class:.1f}",
            "impact": abs(float(coef)) * support,
            "provenance": _classify_rule_provenance(rule),
            "seasonal_only": int(seasonal),
            "tree_index": rule.tree_index,
        })
    rows.sort(key=lambda r: -r["impact"])
    with path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "rule_english", "rule_raw", "coefficient", "support",
            "support_pct", "pct_class_explained", "impact",
            "provenance", "seasonal_only", "tree_index",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    logger.info("wrote %d %s rules to %s", len(rows), target_name, path)
    return len(rows)


def _write_report(
    path: Path,
    target_name: str,
    n_total_rules: int,
    n_kept: int,
    auc: float,
    chosen_C: float,
    top_rules_csv: Path,
    top_n_in_report: int = 12,
) -> None:
    """Markdown report with the top-N rules rendered as human English.

    Iteration-2 additions:
      - chosen L1 C value (transparency on regularisation strength)
      - inline top-N table with humanised rules
      - provenance breakdown (natal/transit/composite counts)
    """
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Phase 1 — RuleFit rules for `{target_name}`",
        "",
        f"_Generated {now}_",
        "",
        f"- **Rules extracted from XGBoost**: {n_total_rules:,}",
        f"- **Rules kept (non-zero coefficient, non-seasonal)**: {n_kept:,}",
        f"- **L1 regularisation C**: {chosen_C:g}",
        f"- **Holdout AUC** (logistic on rule activations): {auc:.4f}",
        "",
        f"Full rule list with coefficients in `{top_rules_csv.name}`.",
        "",
        "## How to read a rule",
        "",
        "Each rule is a conjunction of decision-tree splits taken from",
        "the Round-5 XGBoost ensemble. **Positive coefficient** = activating",
        "the rule **raises P(target)**; negative coefficient = lowers it.",
        "`impact = |coefficient| × support` ranks rules by how much they",
        "move predictions across the entire training corpus.",
        "",
        "**Provenance**:",
        "- `natal-only` — depends only on the birth chart",
        "- `transit-only` — depends only on the sky at event time",
        "- `composite` — birth + transit + dasha combined (most Vedic-like)",
        "",
        "## Filters applied",
        "",
        "- **Seasonal filter**: rules whose ONLY predicates reference",
        "  transit-Sun day-of-year features (`t_dec_sun`, `t_vel_sun`,",
        "  `t_lon_sun`, `t_house_sun`, etc.) are removed. These rules",
        "  encode 'event occurred in winter/summer' rather than Vedic",
        "  astrological structure. Rules where Sun-features appear",
        "  **alongside** non-seasonal predicates are kept.",
        "- **Sparse L1**: regularisation tuned so the rule set",
        "  is ~25-40 rules per class (focused, not exhaustive).",
        "",
        f"Top {top_n_in_report} rules below — see CSV for the full list.",
    ]
    # Inject top-N from the CSV file we just wrote (re-read to get the
    # sorted order — keeps the rendering single-sourced).
    with top_rules_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
    lines.append("")
    lines.append("| Rank | Coeff | Support | %Class | Provenance | Rule |")
    lines.append("|---|---|---|---|---|---|")
    for rank, r in enumerate(all_rows[:top_n_in_report], start=1):
        coef = float(r["coefficient"])
        coef_str = f"{coef:+.3f}"
        sup = r["support"]
        pct = r["pct_class_explained"]
        prov = r["provenance"]
        eng = r["rule_english"]
        lines.append(
            f"| {rank} | {coef_str} | {sup} | {pct}% | {prov} | {eng} |"
        )

    # Provenance breakdown
    provenance_counts: dict[str, int] = {
        "natal-only": 0, "transit-only": 0, "composite": 0,
    }
    for r in all_rows:
        provenance_counts[r["provenance"]] = (
            provenance_counts.get(r["provenance"], 0) + 1
        )
    lines.extend([
        "",
        "## Provenance breakdown (all kept rules)",
        "",
        f"- natal-only: {provenance_counts['natal-only']}",
        f"- transit-only: {provenance_counts['transit-only']}",
        f"- composite: {provenance_counts['composite']}",
    ])

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- Main ----------

def run_extraction(
    *,
    model_path: Path,
    features_parquet: Path,
    target_column: str,
    output_dir: Path,
    top_classes: int = 5,
    max_rules_pool: int = 2000,
    max_rules_kept: int = 30,
) -> None:
    """End-to-end Phase 1.

    For each top-N class (by population), filter rules learned by the
    multi-class XGBoost down to those that discriminate `class vs rest`
    via Lasso. Output per-class CSVs.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("loading model from %s", model_path)
    model = xgb.XGBClassifier()
    model.load_model(str(model_path))
    booster = model.get_booster()

    logger.info("loading features from %s", features_parquet)
    df = pd.read_parquet(features_parquet)
    if target_column not in df.columns:
        raise ValueError(f"target column {target_column!r} missing")
    df["_label"] = df[target_column].astype(str).str.strip().str.lower()

    class_counts = df["_label"].value_counts()
    logger.info("class counts: %s", class_counts.head(10).to_dict())

    X = select_features(df)
    classes_to_train = list(class_counts.head(top_classes).index)

    logger.info("extracting rules from booster ...")
    rules_pool = extract_rules_from_booster(booster)
    logger.info("computing activation matrix ...")
    activation, rules_kept = compute_activation_matrix(
        rules_pool, X, max_rules=max_rules_pool,
    )

    for class_name in classes_to_train:
        logger.info("=== fitting rule selector for class %r ===", class_name)
        y_class = (df["_label"] == class_name).astype(int)
        n_pos = int(y_class.sum())
        if n_pos < 50:
            logger.warning("skip %r — only %d positives", class_name, n_pos)
            continue
        coefs, auc, chosen_c = fit_sparse_rule_selector(
            activation, y_class, target_nonzero=max_rules_kept,
        )

        safe_name = "".join(c if c.isalnum() else "_" for c in class_name)
        csv_path = output_dir / f"rules_{safe_name}.csv"
        report_path = output_dir / f"report_{safe_name}.md"
        n_kept = _write_rules_csv(
            csv_path, rules_kept, coefs, activation, class_name,
            y_class=y_class, drop_seasonal=True,
        )
        _write_report(
            report_path,
            target_name=class_name,
            n_total_rules=len(rules_pool),
            n_kept=n_kept,
            auc=auc,
            chosen_C=chosen_c,
            top_rules_csv=csv_path,
        )

    # Summary index
    summary_path = output_dir / "INDEX.md"
    summary_path.write_text(
        "# Phase 1 — RuleFit rule extraction\n\n"
        f"Generated {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        "Per-class rule files in this directory.\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.rule_extraction",
        description="Phase 1 of Round 6: extract human-readable rules "
                    "from a trained XGBoost multi-class model.",
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--target-column", type=str, default="event_root")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-classes", type=int, default=5)
    parser.add_argument("--max-rules-pool", type=int, default=2000)
    parser.add_argument("--max-rules-kept", type=int, default=30)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_extraction(
        model_path=args.model,
        features_parquet=args.features,
        target_column=args.target_column,
        output_dir=args.output,
        top_classes=args.top_classes,
        max_rules_pool=args.max_rules_pool,
        max_rules_kept=args.max_rules_kept,
    )
    print(f"Phase 1 rules written to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
