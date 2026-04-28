"""Markdown report writer for Stage 3 training runs.

Combines model metrics + top-N feature importances + extracted rules +
plot file paths into a single human-readable `report.md` per run, alongside
the model artifact and SHAP plots in `data/ml_runs/{target}_{ts}/`.

The report is the primary deliverable for an astrologer reading a run —
it tells them *which* features the model latched onto and *what threshold
ranges* matter, in plain English.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Sequence

from app.medini.ml.shap_rules import Rule


def write_report(
    output_path: Path,
    *,
    target_name: str,
    n_train: int,
    n_test: int,
    base_rate: float,
    cv_roc_auc_mean: float,
    cv_roc_auc_std: float,
    test_roc_auc: float,
    top_features: Sequence[tuple[str, float]],
    rules: Sequence[Rule],
    plot_paths: Sequence[Path],
    min_rule_impact: float,
) -> None:
    """Write a complete training-run report to `output_path` (Markdown).

    Sections, in order:
      1. Run metadata (target, date, sample sizes, base rate)
      2. Model performance (CV ROC-AUC ± std, holdout ROC-AUC)
      3. Top features by importance
      4. Discovered rules (passing the magnitude filter)
      5. Plot artifacts (relative paths)
      6. Notes on reproducibility
    """
    lines: list[str] = []
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append(f"# Astrological Rule Discovery — `{target_name}`")
    lines.append("")
    lines.append(f"_Generated {timestamp}_")
    lines.append("")

    # Section 1: metadata
    lines.append("## Run metadata")
    lines.append("")
    lines.append(f"- **Target**: `{target_name}` (binary classification)")
    lines.append(f"- **Training samples**: {n_train:,}")
    lines.append(f"- **Holdout test samples**: {n_test:,}")
    lines.append(f"- **Base positive rate**: {base_rate:.3%}")
    lines.append(f"- **Magnitude filter**: rules below {min_rule_impact:.0%} probability shift suppressed")
    lines.append("")

    # Section 2: model performance
    lines.append("## Model performance")
    lines.append("")
    lines.append(
        f"- **Cross-validation ROC-AUC** (5-fold stratified): "
        f"{cv_roc_auc_mean:.4f} ± {cv_roc_auc_std:.4f}"
    )
    lines.append(f"- **Holdout test ROC-AUC**: {test_roc_auc:.4f}")
    lines.append("")
    lines.append("ROC-AUC interpretation: 0.5 = no signal, 1.0 = perfect "
                 "discrimination. Astrological targets typically reach 0.6–0.75 "
                 "if real signal exists; below 0.55 indicates the model didn't "
                 "find discriminating features.")
    lines.append("")

    # Section 3: top features
    lines.append("## Top features (by mean |SHAP|)")
    lines.append("")
    lines.append("| Rank | Feature | Importance |")
    lines.append("|---|---|---|")
    for rank, (feature, importance) in enumerate(top_features, start=1):
        lines.append(f"| {rank} | `{feature}` | {importance:.4f} |")
    lines.append("")

    # Section 4: discovered rules
    lines.append("## Discovered rules")
    lines.append("")
    if not rules:
        lines.append(
            f"_No rules passed the {min_rule_impact:.0%} magnitude filter — "
            f"the model's signal is too diffuse to yield clean threshold rules. "
            f"This often means the target class is too small (~{n_train * base_rate:.0f} positives) "
            f"or the discriminating features genuinely interact in ways simple "
            f"thresholds can't capture. Try a related but larger target class, "
            f"lower the magnitude filter, or examine the SHAP summary plot directly._"
        )
    else:
        lines.append(
            f"{len(rules)} rule(s) found with |probability shift| ≥ "
            f"{min_rule_impact:.0%}. Sorted by impact magnitude descending."
        )
        lines.append("")
        lines.append("| Rank | Rule | Δ probability | n |")
        lines.append("|---|---|---|---|")
        for rank, rule in enumerate(rules, start=1):
            sign = "+" if rule.probability_delta >= 0 else ""
            lines.append(
                f"| {rank} | `{rule.feature}` IN [{rule.range_low:.2f}, "
                f"{rule.range_high:.2f}] → **{rule.direction}** | "
                f"{sign}{rule.probability_delta * 100:.1f}% | {rule.sample_count} |"
            )
    lines.append("")

    # Section 5: plots
    lines.append("## Plot artifacts")
    lines.append("")
    if plot_paths:
        for path in plot_paths:
            lines.append(f"- `{path.name}`")
    else:
        lines.append("_(no plots generated)_")
    lines.append("")

    # Section 6: reproducibility
    lines.append("## Reproducibility notes")
    lines.append("")
    lines.append(
        "- Training pipeline: `python -m app.medini.ml.train_classifier "
        f"--target {target_name} --features <parquet>`"
    )
    lines.append(
        "- Random seed pinned in the trainer to ensure deterministic "
        "outputs across reruns."
    )
    lines.append(
        "- Astrological features computed under sidereal Lahiri ayanamsa "
        "via the project's pyswisseph engine (see `app/core/ephemeris_engine.py`)."
    )
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
