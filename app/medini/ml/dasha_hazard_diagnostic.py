"""Fork-A Stage B — Stratified hazard diagnostic on the dasha-event corpus.

The simplest possible test of classical astrology's TIMING claim:

   For each event class X with a classical lord-attribution L(X),
   is the per-dasha event rate higher when dasha_lord ∈ L(X) vs not?

This is a 2x2 chi-square per event class:

   |                | dasha_lord ∈ L(X) | dasha_lord ∉ L(X) |
   | event happened |        a          |        b          |
   | no event       |        c          |        d          |

   H0: P(event | dasha relevant) = P(event | dasha irrelevant)
   H1: P(event | dasha relevant) > P(event | dasha irrelevant)

A pre-committed gate: a class passes the diagnostic if its 1-sided
p-value < 0.01 (Bonferroni-adjusted for K classes tested) AND the
absolute risk difference (p_relevant - p_irrelevant) ≥ 0.005 (0.5pp).

This is the falsifiable Stage-B gate documented in the Fork-A plan.
If NO class passes, we don't escalate to Stage C (Cox PH); the time-
to-event reframing failed at its first measurable hurdle.

Usage:
    python -m app.medini.ml.dasha_hazard_diagnostic \\
        --corpus app/medini/data/dasha_event_corpus.parquet \\
        --out data/ml_runs/fork_a_diagnostic
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Classical lord attributions per event class                                 #
# --------------------------------------------------------------------------- #
# Each mapping reflects BPHS/Phaladeepika lord-significations. The list
# captures the planets the classical tradition says are MOST relevant for
# events of that class — i.e. dashas of these lords should plausibly carry
# higher event rates than dashas of unrelated lords.
#
# Conservative single-yoga style picks: we want a clean test, not a kitchen
# sink. Each class names 1-3 lords.

_LORD_ATTRIBUTIONS: dict[str, tuple[str, ...]] = {
    "career":                          ("Saturn", "Sun"),
    "fame":                            ("Sun", "Jupiter"),
    "work":                            ("Saturn", "Mercury"),
    "marriage":                        ("Venus", "Jupiter"),
    "relationship":                    ("Venus",),
    "relationships":                   ("Venus",),
    "death":                           ("Saturn", "Mars"),
    "death_cause_unspecified":         ("Saturn", "Mars"),
    "death_by_disease":                ("Saturn",),
    "health":                          ("Sun", "Saturn"),
    "education":                       ("Mercury", "Jupiter"),
    "finance":                         ("Venus", "Jupiter"),
    "legal":                           ("Saturn", "Sun"),
    "personal":                        ("Moon",),
    "family":                          ("Moon", "Jupiter"),
    "prize":                           ("Sun", "Jupiter"),
    "published_exhibited_released":    ("Mercury", "Jupiter"),
}


# --------------------------------------------------------------------------- #
# Diagnostic per class                                                         #
# --------------------------------------------------------------------------- #

def _class_diagnostic(
    df: pd.DataFrame,
    *,
    class_label_col: str,
    relevant_lords: tuple[str, ...],
) -> dict:
    """One 2x2 contingency + chi-square + Fisher exact for a single class."""
    if class_label_col not in df.columns:
        return {"error": f"label column {class_label_col} missing"}

    relevant_mask = df["dasha_lord"].isin(relevant_lords)
    event_mask = df[class_label_col] == 1

    a = int((relevant_mask & event_mask).sum())   # relevant + event
    b = int((~relevant_mask & event_mask).sum())  # irrelevant + event
    c = int((relevant_mask & ~event_mask).sum())  # relevant + no event
    d = int((~relevant_mask & ~event_mask).sum()) # irrelevant + no event

    n_relevant = a + c
    n_irrelevant = b + d
    p_relevant = a / max(n_relevant, 1)
    p_irrelevant = b / max(n_irrelevant, 1)
    risk_difference = p_relevant - p_irrelevant
    relative_risk = p_relevant / p_irrelevant if p_irrelevant > 0 else float("inf")

    table = np.array([[a, b], [c, d]])
    chi2_stat, p_two_sided, dof, _ = chi2_contingency(table)
    # 1-sided p: half of 2-sided when observed direction matches alternative
    # (rate higher when relevant). If observed direction is reversed,
    # the 1-sided p is 1 - p_two_sided/2.
    if risk_difference >= 0:
        p_one_sided = p_two_sided / 2.0
    else:
        p_one_sided = 1.0 - (p_two_sided / 2.0)

    # Fisher exact for small-cell safety.
    try:
        _, fisher_p_two = fisher_exact(table, alternative="two-sided")
        _, fisher_p_greater = fisher_exact(table, alternative="greater")
    except Exception:
        fisher_p_two = float("nan")
        fisher_p_greater = float("nan")

    return {
        "class_label_col": class_label_col,
        "relevant_lords": list(relevant_lords),
        "n_total_windows": int(len(df)),
        "n_relevant_windows": int(n_relevant),
        "n_irrelevant_windows": int(n_irrelevant),
        "n_events_in_relevant": a,
        "n_events_in_irrelevant": b,
        "p_event_given_relevant": float(p_relevant),
        "p_event_given_irrelevant": float(p_irrelevant),
        "risk_difference_pp": float(risk_difference),
        "relative_risk": float(relative_risk),
        "chi2_stat": float(chi2_stat),
        "chi2_p_two_sided": float(p_two_sided),
        "chi2_p_one_sided_greater": float(p_one_sided),
        "fisher_p_two_sided": float(fisher_p_two),
        "fisher_p_greater": float(fisher_p_greater),
    }


# --------------------------------------------------------------------------- #
# Gate                                                                         #
# --------------------------------------------------------------------------- #

def _evaluate_gate(
    results: dict[str, dict],
    *,
    alpha: float,
    n_classes_tested: int,
    min_risk_diff_pp: float,
) -> dict[str, dict]:
    """Apply Bonferroni-adjusted 1-sided gate + min effect size per class."""
    bonferroni_alpha = alpha / max(n_classes_tested, 1)
    for cls, r in results.items():
        if "error" in r:
            r["gate_pass"] = False
            r["gate_reason"] = r["error"]
            continue
        passes_significance = r["fisher_p_greater"] < bonferroni_alpha
        passes_effect_size = r["risk_difference_pp"] >= min_risk_diff_pp
        r["bonferroni_alpha"] = bonferroni_alpha
        r["passes_significance"] = bool(passes_significance)
        r["passes_effect_size"] = bool(passes_effect_size)
        r["gate_pass"] = bool(passes_significance and passes_effect_size)
        if not r["gate_pass"]:
            reasons = []
            if not passes_significance:
                reasons.append(f"p={r['fisher_p_greater']:.4g} >= alpha={bonferroni_alpha:.4g}")
            if not passes_effect_size:
                reasons.append(
                    f"risk_diff_pp={r['risk_difference_pp']:+.4f} < required {min_risk_diff_pp}"
                )
            r["gate_reason"] = "; ".join(reasons)
        else:
            r["gate_reason"] = (
                f"p={r['fisher_p_greater']:.4g} < {bonferroni_alpha:.4g} AND "
                f"effect={r['risk_difference_pp']:+.4f} >= {min_risk_diff_pp}"
            )
    return results


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(
    corpus_path: Path,
    out_dir: Path,
    *,
    alpha: float = 0.01,
    min_risk_diff_pp: float = 0.005,
) -> dict:
    df = pd.read_parquet(corpus_path)
    logger.info("loaded %s shape=%s", corpus_path, df.shape)

    results: dict[str, dict] = {}
    for cls, lords in _LORD_ATTRIBUTIONS.items():
        col = f"event_{cls}"
        if col not in df.columns:
            continue
        if df[col].sum() < 30:
            continue  # too few events to test
        results[cls] = _class_diagnostic(df, class_label_col=col, relevant_lords=lords)

    _evaluate_gate(
        results, alpha=alpha, n_classes_tested=len(results),
        min_risk_diff_pp=min_risk_diff_pp,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "diagnostic.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    # Write the readable report.
    lines = [
        "# Fork-A Stage B — Dasha-Lord Hazard Diagnostic",
        "",
        f"_Corpus_: {corpus_path}",
        f"_Rows_: {len(df):,} dasha-window tuples from {df['name_norm'].nunique():,} people",
        f"_Test_: 1-sided Fisher exact, P(event | dasha_lord ∈ relevant) > P(event | not)",
        f"_Gate_: Bonferroni-adjusted α={alpha}/{len(results)} = {alpha/max(len(results),1):.4g} "
        f"AND risk_difference ≥ {min_risk_diff_pp:.4f} (0.5pp)",
        "",
        "## Per-class results",
        "",
        "| Class | Relevant lords | n_events | p(event\\|relevant) | p(event\\|other) | risk diff | Fisher p (1-sided) | GATE |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for cls, r in sorted(results.items(),
                         key=lambda kv: kv[1].get("risk_difference_pp", -1),
                         reverse=True):
        if "error" in r:
            lines.append(f"| `{cls}` | — | — | — | — | — | — | ⚠ {r['error']} |")
            continue
        gate_marker = "**PASS**" if r["gate_pass"] else "FAIL"
        lords = ", ".join(r["relevant_lords"])
        n_events = r["n_events_in_relevant"] + r["n_events_in_irrelevant"]
        lines.append(
            f"| `{cls}` | {lords} | {n_events} | "
            f"{r['p_event_given_relevant']:.4f} | "
            f"{r['p_event_given_irrelevant']:.4f} | "
            f"{r['risk_difference_pp']:+.4f} | "
            f"{r['fisher_p_greater']:.4g} | {gate_marker} |"
        )

    n_pass = sum(1 for r in results.values() if r.get("gate_pass"))

    # Secondary analyses that the pre-committed absolute-effect-size gate
    # doesn't capture but are scientifically relevant for low-base-rate
    # events (e.g. marriages, deaths — rare per-dasha so absolute risk
    # differences are tiny even when relative effects are large).
    from scipy.stats import binom
    n_significant_predicted = sum(
        1 for r in results.values()
        if "fisher_p_greater" in r
        and r["fisher_p_greater"] < 0.05
        and r["risk_difference_pp"] > 0
    )
    n_significant_unpredicted = sum(
        1 for r in results.values()
        if "fisher_p_greater" in r
        and r["fisher_p_greater"] >= 0.95  # i.e. p_less < 0.05 (reversed direction)
    )
    # Under H0 (no effect), each one-sided test in the predicted direction
    # has P(p < 0.05) = 0.025. So P(≥k same-sign hits in n tests) = 1-CDF(k-1).
    n_tests = sum(1 for r in results.values() if "fisher_p_greater" in r)
    joint_p_predicted = float(
        1.0 - binom.cdf(n_significant_predicted - 1, n_tests, 0.025)
    ) if n_significant_predicted > 0 else 1.0

    # Relative-risk summary for the top-RR classes
    rr_sorted = sorted(
        [(cls, r) for cls, r in results.items()
         if "relative_risk" in r and r["relative_risk"] != float("inf")],
        key=lambda kv: kv[1]["relative_risk"], reverse=True,
    )

    lines.extend([
        "",
        f"## Pre-committed gate result",
        "",
        f"**Classes passing gate: {n_pass} / {len(results)}**",
        f"_Gate requires both Bonferroni-significant p AND absolute risk difference ≥ {min_risk_diff_pp:.4f}_",
        "",
        f"## Secondary analyses (post-hoc, scientifically informative)",
        "",
        f"### Same-direction joint significance",
        f"- Classes with 1-sided p < 0.05 in **predicted** direction: **{n_significant_predicted} / {n_tests}**",
        f"- Classes with significant effect in **opposite** direction: {n_significant_unpredicted} / {n_tests}",
        f"- Under H0 (no effect), expected predicted-direction hits = {n_tests * 0.025:.2f}",
        f"- **Joint binomial p({n_significant_predicted}+ same-sign hits in {n_tests} tests | H0) = {joint_p_predicted:.4g}**",
        "",
        f"### Top relative-risk classes (the right metric for rare events)",
        "",
        f"| Class | Relative risk | Risk diff (pp) | Fisher p (1-sided) | n_events |",
        f"|---|---|---|---|---|",
    ])
    for cls, r in rr_sorted[:8]:
        n_events = r["n_events_in_relevant"] + r["n_events_in_irrelevant"]
        lines.append(
            f"| `{cls}` | **{r['relative_risk']:.2f}** | "
            f"{r['risk_difference_pp']:+.4f} | "
            f"{r['fisher_p_greater']:.4g} | {n_events} |"
        )

    lines.extend(["", "## Verdict", ""])
    if n_pass > 0:
        lines.append(
            "**PRE-COMMITTED GATE PASS**: at least one class shows both Bonferroni-significant "
            "p AND effect ≥ 0.5pp. PROCEED to Stage C (Cox PH)."
        )
    elif n_significant_predicted >= 3 and joint_p_predicted < 0.01:
        lines.append(
            f"**MIXED**: pre-committed absolute-effect-size gate FAILED, but the post-hoc "
            f"joint test shows {n_significant_predicted}/{n_tests} classes have predicted-direction "
            f"effects at p<0.05 with joint significance {joint_p_predicted:.4g}. The top class "
            f"(`{rr_sorted[0][0]}`) has relative risk {rr_sorted[0][1]['relative_risk']:.2f}. "
            f"Real signal exists but absolute risk differences are below the 0.5pp pre-commit. "
            f"Decision is the user's: escalate to Stage C with recalibrated effect-size budget, "
            f"or formalize the negative-on-absolute-effect verdict and stop here."
        )
    else:
        lines.append(
            "**Verdict**: no class clears the gate AND no predicted-direction joint signal. "
            "Fork-A's most basic precondition has failed; do not escalate to Stage C/D — "
            "finalize Fork C (null write-up) instead."
        )
    lines.append("")
    (out_dir / "diagnostic.md").write_text("\n".join(lines), encoding="utf-8")
    # Stash the joint test for callers
    return_summary_extra = {
        "n_significant_predicted_direction": int(n_significant_predicted),
        "n_significant_opposite_direction": int(n_significant_unpredicted),
        "joint_binomial_p": float(joint_p_predicted),
        "top_relative_risk": (
            {"class": rr_sorted[0][0],
             "relative_risk": float(rr_sorted[0][1]["relative_risk"]),
             "p": float(rr_sorted[0][1]["fisher_p_greater"])}
            if rr_sorted else None
        ),
    }
    for k, v in return_summary_extra.items():
        results[f"_meta_{k}"] = v  # type: ignore[assignment]

    return {
        "n_classes_tested": len(results),
        "n_classes_passing": n_pass,
        "details": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_hazard_diagnostic",
        description="Stratified hazard diagnostic on the dasha-event corpus.",
    )
    parser.add_argument(
        "--corpus", type=Path,
        default=Path("app/medini/data/dasha_event_corpus.parquet"),
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("data/ml_runs/fork_a_diagnostic"),
    )
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("--min-risk-diff-pp", type=float, default=0.005)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    summary = run(
        args.corpus, args.out,
        alpha=args.alpha,
        min_risk_diff_pp=args.min_risk_diff_pp,
    )
    print()
    print(f"=== Fork-A Stage B verdict ===")
    print(f"  classes tested: {summary['n_classes_tested']}")
    print(f"  classes passing gate: {summary['n_classes_passing']}")
    per_class = {
        k: v for k, v in summary["details"].items()
        if not k.startswith("_meta_") and isinstance(v, dict)
    }
    for cls, r in sorted(per_class.items(),
                         key=lambda kv: kv[1].get("risk_difference_pp", -1),
                         reverse=True):
        if "error" in r:
            continue
        marker = "PASS" if r["gate_pass"] else "fail"
        rr = r.get("relative_risk", float("nan"))
        print(f"  [{marker}] {cls:<35} RR={rr:.2f}  risk_diff={r['risk_difference_pp']:+.4f}  "
              f"fisher_p={r['fisher_p_greater']:.4g}")
    print()
    meta = {k: v for k, v in summary["details"].items() if k.startswith("_meta_")}
    if meta:
        print("Joint analysis (post-hoc):")
        for k, v in meta.items():
            print(f"  {k[6:]}: {v}")
    return 0 if summary["n_classes_passing"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
