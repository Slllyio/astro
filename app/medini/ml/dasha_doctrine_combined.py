"""Test (c) — Combined: karaka-stripped scorer + within-lord stratification.

The cleanest test of chart-structural doctrine. Takes the lifecycle-
confound-cleanup from BOTH:

  Test (a): doctrine_relevance_structural (HR + func_mod, no KR baseline)
  Test (b): per-(corpus, dasha_lord) stratification

Composed: bin each (corpus, lord) cell by the karaka-stripped score
quintile, compute top-vs-bottom RR, Mantel-Haenszel pool across cells.

Why this is the cleanest control:
  - KR's chart-independent +1.0 baseline is removed from the score
  - Between-lord lifecycle variance is removed by stratification
  - The remaining quintile gradient reflects HR + func_mod × dignity
    variation WITHIN a single lord's rows — pure chart structure

If THIS retreats to ~1.0, the chart contributes nothing.
If it stays at ~1.5, we have triangulated genuine chart-structural
signal at modest effect size.

Usage:
    python -m app.medini.ml.dasha_doctrine_combined --event-class personal
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from scipy.stats import norm

from app.medini.ml.dasha_doctrine_pooled import (
    _dedup_by_birth_jd, _load_corpora,
    _mantel_haenszel_log_rr, _per_corpus_rr, CorpusRR,
)
from app.medini.ml.dasha_doctrine_personal_disambiguation import (
    _shuffle_natal_charts,
)
from app.medini.ml.dasha_doctrine_structural import _annotate_structural

logger = logging.getLogger(__name__)

_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
    "Saturn", "Rahu", "Ketu",
)
_N_BINS: Final = 5
_MIN_STRATUM_EVENTS: Final = 10


def _per_stratum_rrs(
    annotated_by_corpus: dict[str, pd.DataFrame],
    event_class: str,
) -> list[CorpusRR]:
    """Per-(corpus, lord) stratum RR using karaka-stripped mix_score."""
    out: list[CorpusRR] = []
    label_col = f"event_{event_class}"
    for corpus, ann in annotated_by_corpus.items():
        for lord in _GRAHAS:
            sub = ann[ann["dasha_lord"] == lord]
            if len(sub) < 100:
                continue
            if label_col not in sub.columns or sub[label_col].sum() < _MIN_STRATUM_EVENTS:
                continue
            rr = _per_corpus_rr(sub, event_class, n_bins=_N_BINS)
            if rr is None:
                continue
            rr.corpus = f"{corpus}::{lord}"
            out.append(rr)
    return out


def _shuffled_rep(
    dasha_dfs: dict[str, pd.DataFrame],
    natal_dfs: dict[str, pd.DataFrame],
    event_class: str,
    seed: int,
) -> float:
    """One permutation: shuffle charts then rerun combined (karaka-stripped + stratified)."""
    annotated: dict[str, pd.DataFrame] = {}
    for corpus, dasha_df in dasha_dfs.items():
        label_col = f"event_{event_class}"
        if label_col not in dasha_df.columns or dasha_df[label_col].sum() < 30:
            continue
        shuffled_natal = _shuffle_natal_charts(natal_dfs[corpus], seed=seed)
        annotated[corpus] = _annotate_structural(
            dasha_df, shuffled_natal, event_class,
        )
    strata = _per_stratum_rrs(annotated, event_class)
    pooled = _mantel_haenszel_log_rr(strata)
    return pooled["rr_pooled"]


def run(
    out_dir: Path,
    event_class: str = "personal",
    n_perms: int = 20,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    dasha_dfs, natal_dfs = _load_corpora()
    dasha_dfs, natal_dfs, _ = _dedup_by_birth_jd(dasha_dfs, natal_dfs)

    annotated: dict[str, pd.DataFrame] = {}
    for corpus, dasha_df in dasha_dfs.items():
        label_col = f"event_{event_class}"
        if label_col not in dasha_df.columns or dasha_df[label_col].sum() < 30:
            continue
        annotated[corpus] = _annotate_structural(
            dasha_df, natal_dfs[corpus], event_class,
        )

    strata = _per_stratum_rrs(annotated, event_class)
    pooled = _mantel_haenszel_log_rr(strata)
    logger.info(
        "Combined (karaka-stripped + stratified) pooled %s RR = %.3f "
        "(95%% CI %.3f-%.3f), p=%.3g, Q_p=%.3g, k=%d",
        event_class,
        pooled["rr_pooled"], pooled["ci_low"], pooled["ci_high"],
        pooled["p"], pooled["q_p"], pooled["k"],
    )

    # Permutation test: shuffle charts then rerun karaka-stripped + stratified.
    # This is the cleanest possible chart-dependence falsifier.
    rng = np.random.default_rng(42)
    seeds = rng.integers(0, 2**31 - 1, size=n_perms)
    shuffled_rrs: list[float] = []
    for i, seed in enumerate(seeds, start=1):
        rr = _shuffled_rep(dasha_dfs, natal_dfs, event_class, int(seed))
        shuffled_rrs.append(rr)
        logger.info("Permutation %d/%d  shuffled_combined_RR=%.3f", i, n_perms, rr)

    arr = np.array(shuffled_rrs)
    log_real = np.log(pooled["rr_pooled"])
    log_shuf = np.log(arr[~np.isnan(arr) & (arr > 0)])
    null_mean_log = float(np.mean(log_shuf))
    null_std_log = (float(np.std(log_shuf, ddof=1))
                    if len(log_shuf) > 1 else float("nan"))
    z = ((log_real - null_mean_log) / null_std_log
         if null_std_log and null_std_log > 0 else float("nan"))
    p_one = float(1.0 - norm.cdf(z)) if not np.isnan(z) else float("nan")
    n_exceed = int(np.sum(arr >= pooled["rr_pooled"]))
    emp_p = (n_exceed + 1) / (n_perms + 1)

    summary = {
        "event_class": event_class,
        "n_strata": len(strata),
        "combined_pooled": pooled,
        "per_stratum": [
            {"stratum": s.corpus, "rr": s.rr,
             "n_top": s.n_events_top, "n_bot": s.n_events_bot}
            for s in strata
        ],
        "permutation": {
            "n_perms": n_perms,
            "all_shuffled_rrs": [float(x) for x in arr],
            "null_mean": float(np.exp(null_mean_log)),
            "null_min": float(np.min(arr)),
            "null_max": float(np.max(arr)),
            "null_median": float(np.median(arr)),
            "z_score": float(z),
            "p_value_parametric": p_one,
            "empirical_p_value": emp_p,
            "n_shuffled_exceeding_real": n_exceed,
        },
    }
    (out_dir / "combined_test.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8",
    )

    lines = [
        f"# Test (c): Combined karaka-stripped + stratified RR — `{event_class}`",
        "",
        f"Scorer: structural (HR + func_mod, NO karaka baseline)",
        "Stratification: per-(corpus, dasha_lord) cell, within-lord quintile binning",
        "",
        "## Per-stratum RRs (karaka-stripped, within-lord)",
        "",
        "| Stratum | n_top | n_bot | RR |",
        "|---|---|---|---|",
    ]
    for s in sorted(strata, key=lambda x: -x.rr if not np.isnan(x.rr) else 0):
        lines.append(f"| {s.corpus} | {s.n_events_top} | {s.n_events_bot} | {s.rr:.2f} |")

    perm = summary["permutation"]
    lines.extend([
        "",
        "## Overall combined pool",
        "",
        f"| Quantity | Value |",
        f"|---|---|",
        f"| n strata | {pooled['k']} |",
        f"| Pooled RR | **{pooled['rr_pooled']:.3f}** |",
        f"| 95% CI | {pooled['ci_low']:.2f}-{pooled['ci_high']:.2f} |",
        f"| p-value | **{pooled['p']:.3g}** |",
        f"| Cochran Q_p | {pooled['q_p']:.3g} |",
        "",
        "## Permutation falsifier (shuffle charts within strata)",
        "",
        f"| Quantity | Value |",
        f"|---|---|",
        f"| K permutations | {perm['n_perms']} |",
        f"| Null mean | {perm['null_mean']:.3f} |",
        f"| Null median | {perm['null_median']:.3f} |",
        f"| Null min | {perm['null_min']:.3f} |",
        f"| Null max | {perm['null_max']:.3f} |",
        f"| Real RR | {pooled['rr_pooled']:.3f} |",
        f"| z-score | **{perm['z_score']:.2f}** |",
        f"| Empirical p-value | **{perm['empirical_p_value']:.3g}** |",
        f"| Shuffled ≥ real | {perm['n_shuffled_exceeding_real']}/{perm['n_perms']} |",
        "",
        "## Verdict",
        "",
    ])
    z_val = perm["z_score"]
    if not np.isnan(z_val) and z_val > 3:
        lines.append("> ✅ **CHART-STRUCTURAL EFFECT CONFIRMED** — The "
                     "karaka-stripped within-lord stratified RR survives "
                     "chart shuffling with high z. After removing BOTH the "
                     "karaka baseline AND between-lord lifecycle confounding, "
                     "the chart still predicts events. This is the cleanest "
                     "evidence yet for genuine doctrine-structural signal.")
    elif not np.isnan(z_val) and z_val < 1:
        lines.append("> 🚫 **NO CHART STRUCTURAL SIGNAL** — Even with both "
                     "controls applied, the shuffled null tracks the real RR. "
                     "The entire RR ~1.5 is residual lifecycle leakage that "
                     "neither karaka-stripping nor stratification can remove.")
    else:
        lines.append(f"> 🤔 **PARTIAL** — z={z_val:.2f}. Some chart signal "
                     "above noise but margin is small. Larger K needed.")
    lines.append("")
    (out_dir / "combined_test.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote %s", out_dir / "combined_test.md")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_combined",
        description="Karaka-stripped + within-lord-stratified pooled RR.",
    )
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/round11_combined_test"))
    parser.add_argument("--event-class", type=str, default="personal")
    parser.add_argument("--n-perms", type=int, default=20)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    summary = run(args.out, event_class=args.event_class, n_perms=args.n_perms)
    print()
    print(f"=== Test (c): Combined ({args.event_class}) ===")
    print(f"  n strata:         {summary['n_strata']}")
    print(f"  pooled RR:        {summary['combined_pooled']['rr_pooled']:.3f}")
    print(f"  95% CI:           "
          f"{summary['combined_pooled']['ci_low']:.2f}-"
          f"{summary['combined_pooled']['ci_high']:.2f}")
    print(f"  p-value:          {summary['combined_pooled']['p']:.3g}")
    print(f"  Cochran Q_p:      {summary['combined_pooled']['q_p']:.3g}")
    p = summary["permutation"]
    print(f"  Shuffled null mean: {p['null_mean']:.3f}")
    print(f"  Shuffled null max:  {p['null_max']:.3f}")
    print(f"  z-score real vs null: {p['z_score']:.2f}")
    print(f"  empirical p:          {p['empirical_p_value']:.3g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
