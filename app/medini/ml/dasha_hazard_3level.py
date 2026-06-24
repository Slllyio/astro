"""Fork-A Stage B+ — 3-level (MD x AD x PD) hazard diagnostic.

Generalizes ``dasha_hazard_diagnostic.py`` from "dasha lord ∈ relevant"
to the full Vimshottari chain. The key statistical question:

   For each event class X with classical lord-attribution L(X),
   does the per-day event rate monotonically increase as the lord
   chain (MD, AD, PD) accumulates more lords from L(X)?

That is — if marriage is associated with Venus + Jupiter, do we see:

   rate(0 of 3 lords ∈ {V,J}) < rate(1 of 3) < rate(2 of 3) < rate(3 of 3) ?

Monotonic strict ordering = strong evidence the lord chain matters.
Single-level lift = the deeper levels add nothing beyond MD.

Three complementary tests are run per class:

  1. **Rate ladder**: events-per-day at each n_relevant ∈ {0, 1, 2, 3}.
  2. **Cochran-Armitage trend**: tests the monotonic-trend hypothesis
     directly with one p-value per class.
  3. **Conjunction RR**: rate(3-of-3 chain) / rate(0-of-3 chain). The
     headline relative-risk for the "deep dasha activation" hypothesis.

This is the natural next step after Stage B showed RR=1.5+ effects at
the MD-only level with joint p=1.8e-08 over 14 classes.

Usage:
    python -m app.medini.ml.dasha_hazard_3level \\
        --corpus app/medini/data/dasha_mdadpd_corpus.parquet \\
        --out data/ml_runs/fork_a_3level
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

logger = logging.getLogger(__name__)


# Same classical attributions as the 1-level diagnostic — keeps the
# scientific question identical, only the depth of conditioning changes.
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
# Exposure-adjusted Poisson rate-ratio tests                                  #
# --------------------------------------------------------------------------- #
#
# The right unit-of-analysis for hazard is event-per-time, not event-per-
# window: PD windows differ in duration by 100x+ (Sun-Sun-Sun PD is ~6
# days; Venus-Saturn-Saturn PD is ~190 days). A per-window proportion
# test would systematically penalise the dense-chain buckets where
# windows are shorter. The Poisson rate-ratio with log-exposure offset
# is the standard epi/survival test for this.

def _poisson_rate_ratio_log_normal_z(
    n_events_a: float, exposure_a: float,
    n_events_b: float, exposure_b: float,
) -> tuple[float, float, float, float]:
    """Return (log_RR, z, 95% CI low, 95% CI high) for RR = rate_b / rate_a.

    Uses the log-normal large-sample approximation: log(RR) ~ N(0, 1/n_a + 1/n_b).
    Standard practice for Poisson rate-ratio inference at large counts.
    """
    if n_events_a == 0 or n_events_b == 0 or exposure_a == 0 or exposure_b == 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    rate_a = n_events_a / exposure_a
    rate_b = n_events_b / exposure_b
    log_rr = np.log(rate_b / rate_a)
    se_log_rr = np.sqrt(1.0 / n_events_a + 1.0 / n_events_b)
    z = log_rr / se_log_rr
    ci_low = float(np.exp(log_rr - 1.96 * se_log_rr))
    ci_high = float(np.exp(log_rr + 1.96 * se_log_rr))
    return float(log_rr), float(z), ci_low, ci_high


def _exposure_weighted_trend_p(
    n_events_by_score: np.ndarray, total_days_by_score: np.ndarray,
) -> tuple[float, float]:
    """Poisson regression z-test for monotonic trend in event rate vs score.

    Model: log(rate_k) = beta_0 + beta_1 * k, with offset log(exposure_k).
    Tests H1: beta_1 > 0 (rate increases with score). Computed in closed
    form using the score-test approximation since this is exactly the
    setting Poisson regression solves analytically for grouped data.
    """
    scores = np.arange(len(n_events_by_score), dtype=float)
    exposure = np.asarray(total_days_by_score, dtype=float)
    events = np.asarray(n_events_by_score, dtype=float)
    if events.sum() == 0 or exposure.sum() == 0:
        return float("nan"), 1.0
    # Null rate (across all scores)
    rate_null = events.sum() / exposure.sum()
    expected = exposure * rate_null
    s_bar = (scores * expected).sum() / expected.sum()
    num = ((scores - s_bar) * events).sum()
    var = (((scores - s_bar) ** 2) * expected).sum()
    if var <= 0:
        return float("nan"), 1.0
    z = num / np.sqrt(var)
    from scipy.stats import norm
    return float(z), float(1.0 - norm.cdf(z))


# --------------------------------------------------------------------------- #
# Per-class analysis                                                          #
# --------------------------------------------------------------------------- #

def _n_relevant_per_row(df: pd.DataFrame, relevant: set[str]) -> np.ndarray:
    """Count how many of (md_lord, ad_lord, pd_lord) are in ``relevant`` per row."""
    md = df["md_lord"].isin(relevant).to_numpy(dtype=int)
    ad = df["ad_lord"].isin(relevant).to_numpy(dtype=int)
    pd_ = df["pd_lord"].isin(relevant).to_numpy(dtype=int)
    return md + ad + pd_


def analyze_class(
    df: pd.DataFrame,
    class_col: str,
    relevant_lords: tuple[str, ...],
) -> dict:
    """Compute the rate ladder + trend test + 3-of-3 conjunction RR per class."""
    if class_col not in df.columns:
        return {"error": f"label column {class_col} missing"}

    rel_set = set(relevant_lords)
    n_rel = _n_relevant_per_row(df, rel_set)
    events = df[class_col].to_numpy(dtype=int)
    dur_days = df["window_duration_days"].to_numpy(dtype=float)

    rate_ladder: list[dict] = []
    n_events_by_score = np.zeros(4, dtype=float)
    n_windows_by_score = np.zeros(4, dtype=float)
    total_days_by_score = np.zeros(4, dtype=float)

    for k in range(4):
        mask = n_rel == k
        n_w = int(mask.sum())
        n_e = int(events[mask].sum())
        days = float(dur_days[mask].sum())
        rate_per_year = (n_e / days * 365.2425) if days > 0 else 0.0
        rate_per_window = (n_e / n_w) if n_w > 0 else 0.0
        rate_ladder.append({
            "n_relevant": k,
            "n_windows": n_w,
            "n_events": n_e,
            "total_days": days,
            "rate_per_year": rate_per_year,
            "rate_per_window": rate_per_window,
        })
        n_events_by_score[k] = n_e
        n_windows_by_score[k] = n_w
        total_days_by_score[k] = days

    # Exposure-adjusted Poisson trend test: log(rate) ~ score, offset=log(exposure).
    # This is the right test for "does the per-day event rate increase
    # monotonically with the depth of the relevant lord chain?"
    z, trend_p = _exposure_weighted_trend_p(n_events_by_score, total_days_by_score)

    # Conjunction Poisson rate ratio: rate(3-of-3) / rate(0-of-3) + 95% CI.
    log_rr, conj_z, ci_low, ci_high = _poisson_rate_ratio_log_normal_z(
        n_events_a=n_events_by_score[0], exposure_a=total_days_by_score[0],
        n_events_b=n_events_by_score[3], exposure_b=total_days_by_score[3],
    )
    conjunction_rr = float(np.exp(log_rr)) if not np.isnan(log_rr) else float("nan")
    from scipy.stats import norm
    conj_p_one_sided = float(1.0 - norm.cdf(conj_z)) if not np.isnan(conj_z) else float("nan")

    # 2x2 collapsed: (any-relevant vs none) for comparison with the
    # 1-level test in dasha_hazard_diagnostic.
    any_relevant = (n_rel > 0)
    a = int(events[any_relevant].sum())
    c = int(events[~any_relevant].sum())
    b = int(any_relevant.sum() - a)  # non-events in any-relevant
    d = int((~any_relevant).sum() - c)
    if a + b > 0 and c + d > 0:
        table = np.array([[a, c], [b, d]])
        chi2, chi_p, _, _ = chi2_contingency(table)
        # One-sided: divide if rate higher with any-relevant
        p_rel = a / (a + b)
        p_irrel = c / (c + d)
        chi_p_one = chi_p / 2.0 if p_rel >= p_irrel else 1.0 - chi_p / 2.0
    else:
        chi_p_one = float("nan")

    return {
        "class_col": class_col,
        "relevant_lords": list(relevant_lords),
        "n_rows_total": int(len(df)),
        "n_events_total": int(events.sum()),
        "rate_ladder": rate_ladder,
        "trend_z": float(z),
        "trend_p_one_sided": float(trend_p),
        "conjunction_rr_3of3_over_0of3": float(conjunction_rr),
        "conjunction_rr_ci_low": float(ci_low),
        "conjunction_rr_ci_high": float(ci_high),
        "conjunction_p_one_sided": float(conj_p_one_sided),
        "any_relevant_chi2_p_one_sided": float(chi_p_one),
    }


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(
    corpus_path: Path,
    out_dir: Path,
    *,
    alpha: float = 0.01,
) -> dict:
    df = pd.read_parquet(corpus_path)
    logger.info("loaded %s shape=%s", corpus_path, df.shape)

    results: dict[str, dict] = {}
    for cls, lords in _LORD_ATTRIBUTIONS.items():
        col = f"event_{cls}"
        if col not in df.columns:
            continue
        if df[col].sum() < 30:
            continue
        results[cls] = analyze_class(df, col, lords)

    # Joint test on Cochran-Armitage one-sided p across classes
    from scipy.stats import binom
    n_classes = len(results)
    n_significant = sum(
        1 for r in results.values()
        if r.get("trend_p_one_sided", 1.0) < 0.05
    )
    joint_p = float(1.0 - binom.cdf(n_significant - 1, n_classes, 0.05)) if n_significant > 0 else 1.0
    bonferroni_alpha = alpha / max(n_classes, 1)
    n_significant_bonf = sum(
        1 for r in results.values()
        if r.get("trend_p_one_sided", 1.0) < bonferroni_alpha
    )

    # Headline conjunction RR
    rr_sorted = sorted(
        ((cls, r["conjunction_rr_3of3_over_0of3"], r["trend_p_one_sided"])
         for cls, r in results.items()
         if not np.isnan(r.get("conjunction_rr_3of3_over_0of3", float("nan")))),
        key=lambda x: x[1], reverse=True,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "diagnostic_3level.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Fork-A 3-Level Dasha Hazard Diagnostic (MD x AD x PD)",
        "",
        f"_Corpus_: {corpus_path}",
        f"_Rows_: {len(df):,} PD-grained windows from {df['name_norm'].nunique():,} people",
        f"_Test_: For each class, does event rate (events per day) increase monotonically",
        f"     with the number of {{MD lord, AD lord, PD lord}} in the relevant set?",
        f"_Method_: Exposure-adjusted Poisson rate-ratio + log-normal 95% CI.",
        f"_Trend test_: Poisson-regression z-test (α={alpha}, Bonferroni α/{n_classes}={bonferroni_alpha:.4g}).",
        "",
        "## Headline — conjunction Poisson rate ratio (3-of-3 chain vs 0-of-3)",
        "",
        "| Class | Lords | Conjunction RR (95% CI) | Conj. p (1-sided) | Trend p (1-sided) |",
        "|---|---|---|---|---|",
    ]
    for cls, rr, ca_p in rr_sorted:
        lords = ", ".join(_LORD_ATTRIBUTIONS[cls])
        r = results[cls]
        ci_low = r.get("conjunction_rr_ci_low", float("nan"))
        ci_high = r.get("conjunction_rr_ci_high", float("nan"))
        conj_p = r.get("conjunction_p_one_sided", float("nan"))
        ca_marker = "**" if ca_p < bonferroni_alpha else ""
        conj_marker = "**" if conj_p < bonferroni_alpha else ""
        lines.append(
            f"| `{cls}` | {lords} | **{rr:.2f}** ({ci_low:.2f}–{ci_high:.2f}) | "
            f"{conj_marker}{conj_p:.4g}{conj_marker} | "
            f"{ca_marker}{ca_p:.4g}{ca_marker} |"
        )

    lines.extend([
        "",
        "## Joint significance",
        "",
        f"- Classes with Cochran-Armitage trend p < 0.05: **{n_significant} / {n_classes}**",
        f"- Classes with Cochran-Armitage trend p < Bonferroni-α ({bonferroni_alpha:.4g}): **{n_significant_bonf} / {n_classes}**",
        f"- Joint binomial P({n_significant}+ trend hits in {n_classes} tests | H0) = **{joint_p:.4g}**",
        "",
        "## Rate ladder per class (events per Vedic year of exposure)",
        "",
    ])

    for cls, r in sorted(results.items()):
        lines.append(f"### `{cls}` (lords: {', '.join(r['relevant_lords'])})")
        lines.append("")
        lines.append("| n_relevant | n_windows | n_events | total_days | rate_per_year |")
        lines.append("|---|---|---|---|---|")
        for level in r["rate_ladder"]:
            lines.append(
                f"| {level['n_relevant']} | {level['n_windows']:,} | "
                f"{level['n_events']} | {level['total_days']:,.0f} | "
                f"**{level['rate_per_year']:.5f}** |"
            )
        lines.append(
            f"\nPoisson trend z={r['trend_z']:.3f}  "
            f"trend p (1-sided)={r['trend_p_one_sided']:.4g}  "
            f"conjunction RR (3/0)={r['conjunction_rr_3of3_over_0of3']:.2f} "
            f"(95% CI {r.get('conjunction_rr_ci_low', float('nan')):.2f}-"
            f"{r.get('conjunction_rr_ci_high', float('nan')):.2f})\n"
        )

    (out_dir / "diagnostic_3level.md").write_text("\n".join(lines), encoding="utf-8")

    return {
        "n_classes_tested": n_classes,
        "n_significant_trend_p05": n_significant,
        "n_significant_trend_bonferroni": n_significant_bonf,
        "joint_binomial_p": joint_p,
        "top_conjunction_rrs": [(c, float(rr), float(ca_p)) for c, rr, ca_p in rr_sorted[:5]],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_hazard_3level",
        description="3-level Vimshottari (MD x AD x PD) hazard diagnostic.",
    )
    parser.add_argument(
        "--corpus", type=Path,
        default=Path("app/medini/data/dasha_mdadpd_corpus.parquet"),
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("data/ml_runs/fork_a_3level"),
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
    print(f"=== Fork-A 3-Level Diagnostic ===")
    print(f"  classes tested: {summary['n_classes_tested']}")
    print(f"  Cochran-Armitage trend p<0.05: {summary['n_significant_trend_p05']}")
    print(f"  Cochran-Armitage trend p<Bonferroni: {summary['n_significant_trend_bonferroni']}")
    print(f"  joint binomial p: {summary['joint_binomial_p']:.4g}")
    print(f"\n  Top conjunction RRs (3-of-3 / 0-of-3):")
    for cls, rr, p in summary["top_conjunction_rrs"]:
        print(f"    {cls:<35} RR={rr:.2f}  trend_p={p:.4g}")
    return 0 if summary["n_significant_trend_bonferroni"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
