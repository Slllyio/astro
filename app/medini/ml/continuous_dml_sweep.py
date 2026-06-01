"""Tier 1 §3: continuous-treatment DML sweep across event classes × top features.

The user-flagged limitation of Round 7's continuous DML: we only ran
it on the marriage cohort. This script sweeps it across:
  - 8 top event classes (death, work, relationship, career, prize,
    fame, family, published)
  - Top-30 natal features per class (by F-statistic on the binary
    "had event X" outcome)

Output: master CSV with (event_class, feature, ATE_continuous,
p_value, ATE_binary, p_binary, treatment_kind) so we can see which
findings only emerge under continuous DML.

Conservative scoping: ~30s per (feature, class) DML fit × 8 classes
× 30 features ≈ 2 hours. Background-run friendly.
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
from sklearn.feature_selection import f_classif

from app.medini.ml.causal_inference import (
    _is_natal_numeric,
    build_target_outcome,
    estimate_ate_continuous,
    estimate_ate_for_feature,
)

logger = logging.getLogger(__name__)


DEFAULT_EVENT_CLASSES: tuple[str, ...] = (
    "death", "work", "relationship", "career", "prize",
    "fame", "family", "publish",
)


def _rank_features_by_f_stat(
    df: pd.DataFrame, top_k: int = 30,
) -> list[str]:
    """Return top-K natal features by univariate ANOVA F-statistic
    against y. Drops constants and non-numerics."""
    numerics = [c for c in df.columns if _is_natal_numeric(c, df)]
    X = df[numerics].fillna(0.0).to_numpy()
    y = df["y"].to_numpy()
    try:
        scores, _ = f_classif(X, y)
    except Exception:
        scores = np.zeros(len(numerics))
    ranked = sorted(
        zip(numerics, scores, strict=True),
        key=lambda x: -(x[1] if not np.isnan(x[1]) else 0.0),
    )
    return [feat for feat, _ in ranked[:top_k]]


def run_sweep(
    *,
    natal_parquet: Path,
    events_csv: Path,
    output_dir: Path,
    event_classes: tuple[str, ...] = DEFAULT_EVENT_CLASSES,
    top_k_features: int = 20,
    seed: int = 42,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    for ev_class in event_classes:
        logger.info("=" * 60)
        logger.info("event class: %s", ev_class)
        df = build_target_outcome(natal_parquet, events_csv, ev_class)
        if df["y"].sum() < 50:
            logger.warning("  skip: only %d positives", df["y"].sum())
            continue
        top_features = _rank_features_by_f_stat(df, top_k=top_k_features)
        logger.info(
            "  top features (by F-stat): %s ...",
            top_features[:3],
        )
        for feat in top_features:
            # Continuous DML (Round 7 §1.3)
            cont = estimate_ate_continuous(df, feat, seed=seed)
            # Binary DML (legacy)
            binary = estimate_ate_for_feature(df, feat, seed=seed)
            row = {
                "event_class": ev_class,
                "feature": feat,
                "n_cohort": len(df),
                "n_positive": int(df["y"].sum()),
                "ate_continuous": cont.get("ate", float("nan")),
                "p_continuous": cont.get("p_value", float("nan")),
                "ate_binary": binary.get("ate", float("nan")),
                "p_binary": binary.get("p_value", float("nan")),
                "treatment_mean": cont.get("treatment_mean", float("nan")),
                "treatment_std": cont.get("treatment_std", float("nan")),
            }
            all_rows.append(row)
            logger.info(
                "  %-30s cont=%+.4g (p=%.3f)  bin=%+.4g (p=%.3f)",
                feat,
                row["ate_continuous"], row["p_continuous"],
                row["ate_binary"], row["p_binary"],
            )

    # Write CSV
    csv_path = output_dir / "continuous_dml_sweep.csv"
    if not all_rows:
        logger.warning("no results to write")
        return
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        for r in all_rows:
            writer.writerow(r)
    logger.info("wrote %s (%d rows)", csv_path, len(all_rows))

    # Synthesis: find features that flip significance between modes
    flips_to_significant = [
        r for r in all_rows
        if not np.isnan(r["p_continuous"]) and not np.isnan(r["p_binary"])
        and r["p_continuous"] < 0.05 and r["p_binary"] >= 0.05
    ]
    flips_to_insignificant = [
        r for r in all_rows
        if not np.isnan(r["p_continuous"]) and not np.isnan(r["p_binary"])
        and r["p_continuous"] >= 0.05 and r["p_binary"] < 0.05
    ]
    both_significant = [
        r for r in all_rows
        if not np.isnan(r["p_continuous"]) and not np.isnan(r["p_binary"])
        and r["p_continuous"] < 0.05 and r["p_binary"] < 0.05
    ]

    # Markdown report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Tier-1 §3 — Continuous-treatment DML sweep",
        "",
        f"_Generated {now}_",
        "",
        f"- Event classes: {', '.join(event_classes)}",
        f"- Top features per class (by F-stat): {top_k_features}",
        f"- Total (class, feature) cells: {len(all_rows)}",
        "",
        "## Continuous vs binary DML head-to-head",
        "",
        f"- Both modes significant (p<0.05): {len(both_significant)}",
        f"- Continuous-only significant: {len(flips_to_significant)} ← new findings",
        f"- Binary-only significant: {len(flips_to_insignificant)} ← lost in continuous",
        "",
        "## Findings ONLY visible under continuous DML",
        "",
        "These features are statistically significant causally under "
        "continuous-treatment DML but missed by the binary median-split:",
        "",
        "| Event class | Feature | Continuous ATE | p | Binary ATE | p |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(flips_to_significant, key=lambda x: x["p_continuous"]):
        lines.append(
            f"| {r['event_class']} | `{r['feature']}` | "
            f"{r['ate_continuous']:+.4g} | {r['p_continuous']:.4f} | "
            f"{r['ate_binary']:+.4g} | {r['p_binary']:.4f} |"
        )

    lines.extend([
        "",
        "## Both-significant (continuous validates binary)",
        "",
        "| Event class | Feature | Continuous ATE | p | Binary ATE | p |",
        "|---|---|---|---|---|---|",
    ])
    for r in sorted(both_significant, key=lambda x: x["p_continuous"])[:30]:
        lines.append(
            f"| {r['event_class']} | `{r['feature']}` | "
            f"{r['ate_continuous']:+.4g} | {r['p_continuous']:.4f} | "
            f"{r['ate_binary']:+.4g} | {r['p_binary']:.4f} |"
        )

    lines.extend([
        "",
        "Full sweep results: `continuous_dml_sweep.csv`",
    ])
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report.md")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.continuous_dml_sweep",
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
        default=Path("data/ml_runs/tier1_continuous_dml_sweep/"),
    )
    parser.add_argument(
        "--classes", type=str, nargs="+",
        default=list(DEFAULT_EVENT_CLASSES),
    )
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_sweep(
        natal_parquet=args.natal,
        events_csv=args.events,
        output_dir=args.output,
        event_classes=tuple(args.classes),
        top_k_features=args.top_k,
    )
    print(f"Sweep artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
