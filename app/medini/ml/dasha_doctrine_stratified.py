"""Test (b): Stratified-by-active-dasha-lord pooled RR.

Companion to ``dasha_doctrine_structural.py``. Same underlying question
(does the chart matter?) approached from a different angle.

Round-11's permutation test diagnosis was that the personal RR=2.31 is
driven by between-LORD differences: rows where dasha_lord==Moon get a
chart-independent +1.0 from the karaka contribution, dominating quintile
binning. This means the doctrine RR test is effectively asking "are
Moon-MD rows more eventful?" — which the chart contributes nothing to.

The clean way to remove between-lord confounding without modifying the
scorer is to **stratify by active dasha lord**:

  For each (corpus, dasha_lord) cell:
    bin rows by mix_score quintile (within that lord)
    compute top-vs-bottom RR

  Then Mantel-Haenszel pool across all (corpus, lord) strata.

This isolates the chart-DEPENDENT signal because:
  - Within a single lord, the karaka contribution is constant (it depends
    only on lord identity).
  - The remaining score variation comes entirely from HR / dignity / fmod
    — all chart-dependent.
  - So the within-lord quintile gradient is the chart-attributable effect.

If the stratified pooled RR retreats to ~1.0, that confirms (alongside
test (a)) that NO chart-dependent signal exists.

If the stratified pooled RR remains elevated, we have within-lord
gradient = real chart signal, and the between-lord component was the
lifecycle confound.

Usage:
    python -m app.medini.ml.dasha_doctrine_stratified --event-class personal
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

from app.medini.ml.dasha_doctrine_pooled import (
    _dedup_by_birth_jd, _load_corpora,
    _mantel_haenszel_log_rr, _per_corpus_rr, CorpusRR,
)
from app.medini.ml.dasha_doctrine_score_mix import _annotate_mix, _scorer_for

logger = logging.getLogger(__name__)

_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
    "Saturn", "Rahu", "Ketu",
)
_N_BINS: Final = 5
_MIN_STRATUM_EVENTS: Final = 10  # minimum events to include a (corpus, lord) cell


def _per_stratum_rrs(
    annotated_by_corpus: dict[str, pd.DataFrame],
    event_class: str,
) -> list[CorpusRR]:
    """Compute one RR per (corpus, dasha_lord) stratum, within-lord quintile."""
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
            rr.corpus = f"{corpus}::{lord}"  # stratum id
            out.append(rr)
    return out


def run(out_dir: Path, event_class: str = "personal") -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    dasha_dfs, natal_dfs = _load_corpora()
    dasha_dfs, natal_dfs, n_dropped = _dedup_by_birth_jd(dasha_dfs, natal_dfs)
    logger.info("Dedup dropped %d cross-corpus duplicates", n_dropped)

    label_col = f"event_{event_class}"
    annotated_by_corpus: dict[str, pd.DataFrame] = {}
    for corpus, dasha_df in dasha_dfs.items():
        if label_col not in dasha_df.columns or dasha_df[label_col].sum() < 30:
            continue
        ann = _annotate_mix(dasha_df, natal_dfs[corpus], event_class)
        annotated_by_corpus[corpus] = ann

    strata = _per_stratum_rrs(annotated_by_corpus, event_class)
    logger.info(
        "Built %d (corpus, lord) strata for event_class=%s",
        len(strata), event_class,
    )
    for s in strata:
        logger.debug(
            "  %s  RR=%.2f  n_top=%d  n_bot=%d",
            s.corpus, s.rr, s.n_events_top, s.n_events_bot,
        )

    pooled = _mantel_haenszel_log_rr(strata)
    logger.info(
        "Stratified pooled %s RR = %.3f (95%% CI %.3f-%.3f) p=%.3g Q_p=%.3g",
        event_class,
        pooled["rr_pooled"], pooled["ci_low"], pooled["ci_high"],
        pooled["p"], pooled["q_p"],
    )

    # Per-corpus aggregated stratified RR (one per corpus, pooled over lords).
    per_corpus_pooled: dict[str, dict] = {}
    for corpus in annotated_by_corpus:
        corpus_strata = [s for s in strata if s.corpus.startswith(f"{corpus}::")]
        if not corpus_strata:
            continue
        per_corpus_pooled[corpus] = _mantel_haenszel_log_rr(corpus_strata)

    summary = {
        "event_class": event_class,
        "scorer": _scorer_for(event_class),
        "n_strata": len(strata),
        "stratified_pooled": pooled,
        "per_corpus_lord_strata": [
            {
                "stratum": s.corpus,
                "rr": s.rr,
                "n_events_top": s.n_events_top,
                "n_events_bot": s.n_events_bot,
                "log_rr_var": s.log_rr_var,
            } for s in strata
        ],
        "per_corpus_pooled_over_lords": per_corpus_pooled,
    }

    (out_dir / "stratified_test.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        f"# Test (b): Stratified-by-dasha-lord pooled RR — `{event_class}`",
        "",
        f"Scorer: {summary['scorer']} (original — karaka contribution INCLUDED)",
        "Stratification: every (corpus, dasha_lord) cell binned independently "
        "by mix_score quintile, then Mantel-Haenszel pooled.",
        "",
        "## Per-stratum RRs",
        "",
        "| Stratum (corpus::lord) | n_top events | n_bot events | RR |",
        "|---|---|---|---|",
    ]
    for s in sorted(strata, key=lambda x: -x.rr if not np.isnan(x.rr) else 0):
        lines.append(
            f"| {s.corpus} | {s.n_events_top} | {s.n_events_bot} | {s.rr:.2f} |"
        )

    lines.extend([
        "",
        "## Per-corpus stratified pool",
        "",
        "| Corpus | Pooled RR | 95% CI | p | Cochran Q_p |",
        "|---|---|---|---|---|",
    ])
    for c, p in per_corpus_pooled.items():
        marker = "**" if p["p"] < 0.01 else ""
        het = "⚠️" if p["q_p"] < 0.05 else ""
        lines.append(
            f"| {c} | {marker}{p['rr_pooled']:.3f}{marker} | "
            f"{p['ci_low']:.2f}-{p['ci_high']:.2f} | "
            f"{marker}{p['p']:.3g}{marker} | {het}{p['q_p']:.3g}{het} |"
        )

    lines.extend([
        "",
        "## Overall stratified pool",
        "",
        f"| Quantity | Value |",
        f"|---|---|",
        f"| n strata | {pooled['k']} |",
        f"| Pooled RR | **{pooled['rr_pooled']:.3f}** |",
        f"| 95% CI | {pooled['ci_low']:.2f}-{pooled['ci_high']:.2f} |",
        f"| p-value | **{pooled['p']:.3g}** |",
        f"| Cochran Q_p | {pooled['q_p']:.3g} |",
        "",
        "## Verdict",
        "",
    ])

    rr = pooled["rr_pooled"]
    if rr > 1.5 and pooled["p"] < 0.001 and pooled["q_p"] > 0.05:
        lines.append("> ✅ **WITHIN-LORD CHART SIGNAL CONFIRMED** — Even after "
                     "removing between-lord lifecycle confounding by "
                     "stratification, the chart-attributable RR remains "
                     "elevated. This is a clean test of the chart-structural "
                     "hypothesis.")
    elif abs(rr - 1.0) < 0.1:
        lines.append("> 🚫 **NULL** — Within-lord stratification collapses the "
                     "pooled RR to ~1.0. The original RR=2.31 was entirely "
                     "between-lord (lifecycle) signal; the within-lord (chart-"
                     "attributable) signal is zero.")
    else:
        lines.append(f"> 🤔 **MIXED** — Stratified pooled RR = {rr:.3f}. "
                     "Some chart-attributable signal remains but the effect "
                     "size is much smaller than the original between-lord RR. "
                     "Most of the RR=2.31 was lifecycle; a small structural "
                     "component may exist.")
    lines.append("")
    (out_dir / "stratified_test.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote %s", out_dir / "stratified_test.md")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_stratified",
        description="Stratified-by-dasha-lord doctrine RR.",
    )
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/round11_stratified_test"))
    parser.add_argument("--event-class", type=str, default="personal")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    summary = run(args.out, event_class=args.event_class)
    print()
    print(f"=== Test (b): Stratified-by-lord pooled RR ({args.event_class}) ===")
    print(f"  n strata:            {summary['n_strata']}")
    print(f"  stratified pooled:   {summary['stratified_pooled']['rr_pooled']:.3f}")
    print(f"  95% CI:              "
          f"{summary['stratified_pooled']['ci_low']:.2f}-"
          f"{summary['stratified_pooled']['ci_high']:.2f}")
    print(f"  p-value:             {summary['stratified_pooled']['p']:.3g}")
    print(f"  Cochran Q_p:         {summary['stratified_pooled']['q_p']:.3g}")
    print(f"  per-corpus pools:")
    for c, p in summary["per_corpus_pooled_over_lords"].items():
        print(f"    {c}: RR={p['rr_pooled']:.3f}, p={p['p']:.3g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
