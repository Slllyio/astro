"""Stage B (corrected) — MD-only hazard diagnostic with exposure adjustment.

The original Stage B used per-window Fisher exact, treating each
mahadasha as one trial. That test confounds true astrology-timing
signal with the fact that Venus (20y) and Jupiter (16y) MDs are simply
LONGER than the average MD — more exposure inherently means more
events even under the null hypothesis.

This corrected version computes events-per-day rates and tests rate
ratios with Poisson 95% CIs. If the marriage signal survives this
adjustment, the time-to-event framing genuinely supports the classical
attribution. If it doesn't, the Stage B headline was driven by
exposure-time confounding.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

logger = logging.getLogger(__name__)


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
}


def _poisson_rr(n_a: float, exp_a: float, n_b: float, exp_b: float):
    """Return (RR=rate_b/rate_a, log_RR, SE, z, 95% CI low, 95% CI high, p_1sided)."""
    if min(n_a, n_b, exp_a, exp_b) <= 0:
        return tuple([float("nan")] * 7)
    rate_a = n_a / exp_a
    rate_b = n_b / exp_b
    rr = rate_b / rate_a
    log_rr = np.log(rr)
    se = np.sqrt(1.0 / n_a + 1.0 / n_b)
    z = log_rr / se
    ci_low = float(np.exp(log_rr - 1.96 * se))
    ci_high = float(np.exp(log_rr + 1.96 * se))
    p_one = float(1.0 - norm.cdf(z)) if z > 0 else 1.0
    return float(rr), float(log_rr), float(se), float(z), ci_low, ci_high, p_one


def run(corpus_path: Path, out_dir: Path, alpha: float = 0.01) -> dict:
    df = pd.read_parquet(corpus_path)
    logger.info("loaded %s shape=%s", corpus_path, df.shape)
    df["duration_days"] = df["dasha_end_jd"] - df["dasha_start_jd"]

    results: dict[str, dict] = {}
    for cls, relevant_lords in _LORD_ATTRIBUTIONS.items():
        col = f"event_{cls}"
        if col not in df.columns:
            continue
        if df[col].sum() < 30:
            continue
        relevant_mask = df["dasha_lord"].isin(set(relevant_lords))
        a_events = float(df.loc[~relevant_mask, col].sum())
        b_events = float(df.loc[relevant_mask, col].sum())
        a_exposure = float(df.loc[~relevant_mask, "duration_days"].sum())
        b_exposure = float(df.loc[relevant_mask, "duration_days"].sum())
        rr, log_rr, se, z, ci_low, ci_high, p_one = _poisson_rr(
            a_events, a_exposure, b_events, b_exposure,
        )
        rate_irrelevant = a_events / a_exposure * 365.2425 if a_exposure > 0 else 0
        rate_relevant = b_events / b_exposure * 365.2425 if b_exposure > 0 else 0
        results[cls] = {
            "relevant_lords": list(relevant_lords),
            "n_events_relevant": int(b_events),
            "n_events_irrelevant": int(a_events),
            "exposure_days_relevant": b_exposure,
            "exposure_days_irrelevant": a_exposure,
            "rate_per_year_relevant": float(rate_relevant),
            "rate_per_year_irrelevant": float(rate_irrelevant),
            "rate_ratio": rr,
            "log_rr_se": se,
            "z": z,
            "rr_95_ci_low": ci_low,
            "rr_95_ci_high": ci_high,
            "p_one_sided": p_one,
        }

    bonferroni_alpha = alpha / max(len(results), 1)
    n_sig_unadjusted = sum(
        1 for r in results.values() if r.get("p_one_sided", 1.0) < 0.05
    )
    n_sig_bonferroni = sum(
        1 for r in results.values() if r.get("p_one_sided", 1.0) < bonferroni_alpha
    )
    # Joint binomial under H0: each test has P(p<0.05) = 0.05 in correct direction.
    from scipy.stats import binom
    n_classes = len(results)
    joint_p = float(1.0 - binom.cdf(n_sig_unadjusted - 1, n_classes, 0.05)) \
        if n_sig_unadjusted > 0 else 1.0

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stage_b_corrected.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Stage B (corrected) — MD-only hazard diagnostic with exposure adjustment",
        "",
        f"_Corpus_: {corpus_path}",
        f"_Method_: Poisson rate ratio with 95% log-normal CI.",
        f"_Bonferroni α_: {alpha}/{n_classes} = {bonferroni_alpha:.4g}",
        "",
        "## Per-class results (rate per year of exposure, exposure-adjusted)",
        "",
        "| Class | Lords | Rate(relevant) | Rate(other) | RR (95% CI) | p (1-sided) |",
        "|---|---|---|---|---|---|",
    ]
    sorted_results = sorted(
        results.items(),
        key=lambda kv: kv[1].get("rate_ratio", -1),
        reverse=True,
    )
    for cls, r in sorted_results:
        lords = ", ".join(r["relevant_lords"])
        marker = "**" if r["p_one_sided"] < bonferroni_alpha else ""
        lines.append(
            f"| `{cls}` | {lords} | {r['rate_per_year_relevant']:.5f} | "
            f"{r['rate_per_year_irrelevant']:.5f} | "
            f"**{r['rate_ratio']:.2f}** "
            f"({r['rr_95_ci_low']:.2f}-{r['rr_95_ci_high']:.2f}) | "
            f"{marker}{r['p_one_sided']:.4g}{marker} |"
        )
    lines.extend([
        "",
        f"**Classes with p<0.05 (unadjusted, 1-sided)**: {n_sig_unadjusted} / {n_classes}",
        f"**Classes with p<Bonferroni α**: {n_sig_bonferroni} / {n_classes}",
        f"**Joint binomial P(≥{n_sig_unadjusted} same-sign hits | H0)**: {joint_p:.4g}",
        "",
    ])
    (out_dir / "stage_b_corrected.md").write_text("\n".join(lines), encoding="utf-8")

    return {
        "n_classes_tested": n_classes,
        "n_significant_p05": n_sig_unadjusted,
        "n_significant_bonferroni": n_sig_bonferroni,
        "joint_binomial_p": joint_p,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus", type=Path,
        default=Path("app/medini/data/dasha_event_corpus.parquet"),
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("data/ml_runs/fork_a_diagnostic"),
    )
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    summary = run(args.corpus, args.out, alpha=args.alpha)
    print()
    print("=== Stage B (corrected, exposure-adjusted) ===")
    print(f"  classes tested: {summary['n_classes_tested']}")
    print(f"  p<0.05: {summary['n_significant_p05']}")
    print(f"  p<Bonferroni: {summary['n_significant_bonferroni']}")
    print(f"  joint binomial p: {summary['joint_binomial_p']:.4g}")
    print()
    sorted_r = sorted(
        summary["results"].items(),
        key=lambda kv: kv[1].get("rate_ratio", -1),
        reverse=True,
    )
    for cls, r in sorted_r:
        marker = "PASS" if r["p_one_sided"] < (args.alpha / summary["n_classes_tested"]) else "fail"
        print(f"  [{marker}] {cls:<35} RR={r['rate_ratio']:.3f} "
              f"CI=({r['rr_95_ci_low']:.2f}-{r['rr_95_ci_high']:.2f}) "
              f"p={r['p_one_sided']:.4g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
