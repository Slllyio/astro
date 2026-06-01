"""Disambiguate cyclical-age vs structural-chart effect for the `personal` RR=2.31 finding.

The Round-11 pooled doctrine RR analysis found ONE robustly cross-corpus effect:
  `personal` events (s6 scorer, BPHS Phaladeepika Ch.4 / 1st-house-lord strength):
    Pooled RR = 2.31 (95% CI 1.73-3.08), p = 7.4e-9, Q_p = 0.13 (homogeneous)

But there is a confound to rule out before claiming this is a structural
astronomical effect:

  Vimshottari dashas are TIME-CYCLES tied to human aging. If the s6
  scorer's top-quintile MD windows happen to align with age windows where
  "personal" events naturally cluster (early-adulthood identity shifts,
  late-life health), the RR could be a brilliant statistical illusion
  driven by lifecycle confounding -- the chart-structure piece doing
  nothing, the dasha-lord-identity piece smuggling age in.

The clean falsifier is a permutation test:

  KEEP each person's real (events, ages, dasha windows, dasha lords).
  SHUFFLE the natal chart features across persons within each corpus
       (so person A is now scored against person B's chart).
  RECOMPUTE the s6 mix-score, rebin, recompute RR.

If the real RR=2.31 sits in the upper tail of the shuffled distribution
(say z > 3 or p < 0.01), the effect is structural -- it depends on the
REAL chart, not just the dasha sequence + age distribution.

If the shuffled-RR distribution is centered near 2.31, the "effect" is
just age/dasha-lord-identity confounding masquerading as doctrine.

Output:
  data/ml_runs/round11_personal_disambiguation/permutation_test.json
  data/ml_runs/round11_personal_disambiguation/permutation_test.md

Usage:
    python -m app.medini.ml.dasha_doctrine_personal_disambiguation
    python -m app.medini.ml.dasha_doctrine_personal_disambiguation --n-perms 20
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import norm

from app.medini.ml.dasha_doctrine_pooled import (
    _CORPUS_FILES, _dedup_by_birth_jd, _load_corpora,
    _mantel_haenszel_log_rr, _per_corpus_rr, CorpusRR,
)
from app.medini.ml.dasha_doctrine_score_mix import _annotate_mix

logger = logging.getLogger(__name__)

# The event class we are defending.
_TARGET_CLASS: Final = "personal"
_N_BINS: Final = 5


def _shuffle_natal_charts(natal_df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Permute the chart-feature columns across name_norm.

    Keeps name_norm in place (the lookup key) but shuffles every OTHER
    column so each name_norm gets a random person's chart features. This
    preserves the marginal distribution of every feature; it only breaks
    the alignment between names and charts.
    """
    rng = np.random.default_rng(seed)
    shuffled = natal_df.copy()
    feature_cols = [c for c in natal_df.columns
                    if c not in ("name_norm", "name", "corpus")]
    perm = rng.permutation(len(natal_df))
    shuffled[feature_cols] = natal_df[feature_cols].iloc[perm].to_numpy()
    return shuffled


def _real_rr_per_corpus(
    dasha_dfs: dict[str, pd.DataFrame],
    natal_dfs: dict[str, pd.DataFrame],
    event_class: str,
) -> dict[str, CorpusRR | None]:
    """Recompute the real (non-shuffled) per-corpus RR baseline."""
    out: dict[str, CorpusRR | None] = {}
    for corpus, dasha_df in dasha_dfs.items():
        label_col = f"event_{event_class}"
        if label_col not in dasha_df.columns or dasha_df[label_col].sum() < 30:
            out[corpus] = None
            continue
        ann = _annotate_mix(dasha_df, natal_dfs[corpus], event_class)
        rr = _per_corpus_rr(ann, event_class, n_bins=_N_BINS)
        if rr is not None:
            rr.corpus = corpus
        out[corpus] = rr
    return out


def _shuffled_rep(
    dasha_dfs: dict[str, pd.DataFrame],
    natal_dfs: dict[str, pd.DataFrame],
    event_class: str,
    seed: int,
) -> dict[str, float]:
    """One shuffled permutation: returns per-corpus + pooled RR."""
    per_corpus_rrs: list[CorpusRR] = []
    per_corpus_dict: dict[str, float] = {}

    for corpus, dasha_df in dasha_dfs.items():
        label_col = f"event_{event_class}"
        if label_col not in dasha_df.columns or dasha_df[label_col].sum() < 30:
            per_corpus_dict[corpus] = float("nan")
            continue
        shuffled = _shuffle_natal_charts(natal_dfs[corpus], seed=seed)
        ann = _annotate_mix(dasha_df, shuffled, event_class)
        rr = _per_corpus_rr(ann, event_class, n_bins=_N_BINS)
        if rr is None:
            per_corpus_dict[corpus] = float("nan")
            continue
        rr.corpus = corpus
        per_corpus_rrs.append(rr)
        per_corpus_dict[corpus] = rr.rr

    pooled = _mantel_haenszel_log_rr(per_corpus_rrs)
    per_corpus_dict["pooled"] = pooled["rr_pooled"]
    per_corpus_dict["pooled_p"] = pooled["p"]
    return per_corpus_dict


def run_disambiguation(
    out_dir: Path, n_perms: int = 20, event_class: str = _TARGET_CLASS,
) -> dict:
    """Run the permutation test and write outputs."""
    out_dir.mkdir(parents=True, exist_ok=True)

    dasha_dfs, natal_dfs = _load_corpora()
    dasha_dfs, natal_dfs, n_dropped = _dedup_by_birth_jd(dasha_dfs, natal_dfs)
    logger.info("Dedup dropped %d cross-corpus duplicates", n_dropped)

    # Baseline: the REAL RR per corpus + pooled.
    real_per_corpus = _real_rr_per_corpus(dasha_dfs, natal_dfs, event_class)
    real_pooled = _mantel_haenszel_log_rr(
        [r for r in real_per_corpus.values() if r is not None]
    )
    logger.info(
        "REAL pooled %s RR = %.3f (95%% CI %.3f-%.3f), p=%.3g",
        event_class,
        real_pooled["rr_pooled"], real_pooled["ci_low"], real_pooled["ci_high"],
        real_pooled["p"],
    )

    # Run K permutations.
    rng = np.random.default_rng(42)
    seeds = rng.integers(0, 2**31 - 1, size=n_perms)
    shuffled_pooled_rrs: list[float] = []
    shuffled_per_corpus: dict[str, list[float]] = {
        c: [] for c in dasha_dfs
    }

    t0 = time.time()
    for i, seed in enumerate(seeds, start=1):
        rep = _shuffled_rep(dasha_dfs, natal_dfs, event_class, int(seed))
        shuffled_pooled_rrs.append(rep["pooled"])
        for c in dasha_dfs:
            shuffled_per_corpus[c].append(rep.get(c, float("nan")))
        elapsed = time.time() - t0
        eta = elapsed / i * (n_perms - i)
        logger.info(
            "Permutation %d/%d  shuffled_pooled_RR=%.3f  elapsed=%.1fs  eta=%.0fs",
            i, n_perms, rep["pooled"], elapsed, eta,
        )

    # Statistics on the null distribution.
    shuffled_arr = np.array(shuffled_pooled_rrs)
    shuffled_logs = np.log(shuffled_arr[~np.isnan(shuffled_arr) & (shuffled_arr > 0)])
    real_log = np.log(real_pooled["rr_pooled"])

    null_mean = float(np.mean(shuffled_logs))
    null_std = float(np.std(shuffled_logs, ddof=1)) if len(shuffled_logs) > 1 else float("nan")
    z = (real_log - null_mean) / null_std if null_std > 0 else float("nan")
    p_one_sided = float(1.0 - norm.cdf(z)) if not np.isnan(z) else float("nan")
    n_exceeding = int(np.sum(shuffled_arr >= real_pooled["rr_pooled"]))
    empirical_p = (n_exceeding + 1) / (n_perms + 1)

    summary = {
        "event_class": event_class,
        "n_permutations": n_perms,
        "real_rr_pooled": real_pooled["rr_pooled"],
        "real_p_pooled": real_pooled["p"],
        "real_ci_low": real_pooled["ci_low"],
        "real_ci_high": real_pooled["ci_high"],
        "real_q_p": real_pooled["q_p"],
        "real_per_corpus_rr": {
            c: (r.rr if r is not None else None)
            for c, r in real_per_corpus.items()
        },
        "shuffled_pooled_rr_distribution": {
            "mean": float(np.exp(null_mean)),
            "std_log": null_std,
            "min": float(np.nanmin(shuffled_arr)),
            "max": float(np.nanmax(shuffled_arr)),
            "p25": float(np.nanpercentile(shuffled_arr, 25)),
            "p50": float(np.nanpercentile(shuffled_arr, 50)),
            "p75": float(np.nanpercentile(shuffled_arr, 75)),
            "all_values": [float(x) for x in shuffled_arr],
        },
        "z_score_real_vs_null": float(z),
        "p_value_real_vs_null": p_one_sided,
        "empirical_p_value": empirical_p,
        "n_shuffled_exceeding_real": n_exceeding,
        "shuffled_per_corpus_rr_distribution": {
            c: {"mean": float(np.nanmean(v)), "std": float(np.nanstd(v))}
            for c, v in shuffled_per_corpus.items() if any(not np.isnan(x) for x in v)
        },
    }

    (out_dir / "permutation_test.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )

    # Markdown writeup.
    lines = [
        f"# Permutation test: structural vs cyclical for `{event_class}` doctrine RR",
        "",
        "## Setup",
        "",
        f"- Real pooled RR (from Round-11 pooled analysis): **{real_pooled['rr_pooled']:.3f}** "
        f"(95% CI {real_pooled['ci_low']:.2f}-{real_pooled['ci_high']:.2f}), "
        f"p={real_pooled['p']:.3g}",
        f"- Real per-corpus RRs: " + ", ".join(
            f"{c}={r.rr:.2f}" if r is not None else f"{c}=NA"
            for c, r in real_per_corpus.items()
        ),
        f"- Permutations: {n_perms}",
        f"- Procedure: shuffle every natal chart's feature columns across persons "
        "within corpus; keep events, dasha windows, ages intact; recompute s6 score; "
        "recompute Mantel-Haenszel pooled RR.",
        "",
        "## Null distribution (shuffled charts)",
        "",
        f"| Statistic | Value |",
        f"|---|---|",
        f"| mean (geometric) | {summary['shuffled_pooled_rr_distribution']['mean']:.3f} |",
        f"| log-RR std | {null_std:.3f} |",
        f"| min | {summary['shuffled_pooled_rr_distribution']['min']:.3f} |",
        f"| 25th percentile | {summary['shuffled_pooled_rr_distribution']['p25']:.3f} |",
        f"| median | {summary['shuffled_pooled_rr_distribution']['p50']:.3f} |",
        f"| 75th percentile | {summary['shuffled_pooled_rr_distribution']['p75']:.3f} |",
        f"| max | {summary['shuffled_pooled_rr_distribution']['max']:.3f} |",
        "",
        "## Verdict",
        "",
        f"- z-score of real RR vs null:  **{z:.2f}**",
        f"- parametric p-value:          **{p_one_sided:.3g}**",
        f"- empirical p-value:           **{empirical_p:.3g}** "
        f"({n_exceeding}/{n_perms} shuffled reps exceeded real)",
        "",
    ]

    if not np.isnan(z) and z > 3:
        lines.append("> ✅ **STRUCTURAL EFFECT CONFIRMED**: the real RR sits "
                     f"~{z:.1f}σ above the shuffled-chart null. The s6 scorer's "
                     "personal-RR finding requires the real chart — it is NOT "
                     "explained by age-window or dasha-lord-identity cycling.")
    elif not np.isnan(z) and z < 1:
        lines.append("> ⚠️ **LIFECYCLE ARTIFACT**: the shuffled null distribution "
                     "includes RR values close to the real RR. The s6 personal "
                     "finding can be reproduced even with scrambled charts, "
                     "indicating the signal comes from age/dasha-lord-identity "
                     "cycling, not chart structure.")
    else:
        lines.append("> 🤔 **AMBIGUOUS**: real RR exceeds the null mean but not "
                     f"by enough margin to confidently rule out lifecycle "
                     f"confounding (z={z:.2f}). Larger n_perms recommended.")
    lines.append("")
    (out_dir / "permutation_test.md").write_text("\n".join(lines), encoding="utf-8")

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_personal_disambiguation",
        description="Permutation test for the personal-class doctrine RR.",
    )
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/round11_personal_disambiguation"))
    parser.add_argument("--n-perms", type=int, default=20)
    parser.add_argument("--event-class", type=str, default=_TARGET_CLASS)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    summary = run_disambiguation(
        args.out, n_perms=args.n_perms, event_class=args.event_class,
    )
    print()
    print("=== Permutation disambiguation result ===")
    print(f"  event class:           {summary['event_class']}")
    print(f"  real pooled RR:        {summary['real_rr_pooled']:.3f}  p={summary['real_p_pooled']:.3g}")
    print(f"  shuffled null mean:    {summary['shuffled_pooled_rr_distribution']['mean']:.3f}")
    print(f"  shuffled null max:     {summary['shuffled_pooled_rr_distribution']['max']:.3f}")
    print(f"  z-score real vs null:  {summary['z_score_real_vs_null']:.2f}")
    print(f"  empirical p-value:     {summary['empirical_p_value']:.3g}")
    if summary["z_score_real_vs_null"] > 3:
        print("  VERDICT: STRUCTURAL EFFECT CONFIRMED")
    elif summary["z_score_real_vs_null"] < 1:
        print("  VERDICT: LIFECYCLE ARTIFACT (chart structure not load-bearing)")
    else:
        print("  VERDICT: AMBIGUOUS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
