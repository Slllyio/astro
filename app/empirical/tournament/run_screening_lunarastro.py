"""Screen the LunarAstro corpus: chart bank vs. chartless twin, per category tag.

A close parallel of :mod:`run_screening` (the Gauquelin/profession screen),
reusing every piece of tournament machinery unchanged — the sham gate,
chartless-twin scoring, era stratification, person-leak preflight,
Benjamini-Hochberg correction — and differing only in how targets are found
and matched. Gauquelin's corpus carries one profession label per person, so
membership is a plain string equality; this corpus carries an open set of
category TAGS per person (semicolon-joined into ``label`` by
:mod:`lunarastro_corpus`), so each candidate target needs a split-and-contains
membership test instead. Kept as a separate module rather than generalizing
:mod:`run_screening` in place: that module produced the published
TIME_BASIS_CONFOUND result, and a shared code path risks a subtle behavioural
change to something already shipped. ``_cohort`` is imported unchanged — its
tier/quality/era-thinning logic never inspects what ``label`` means, so it is
genuinely shared, not duplicated.

**Screening, not confirmatory** — same posture as Gauquelin's run: the holdout
is frozen and dropped, nothing here is scorable while the registry is
unlocked, and a result is a candidate for a confirmatory run, never a finding.

Usage:
    python -m app.empirical.tournament.run_screening_lunarastro \
        --banks data/empirical/lunarastro_feature_banks.parquet \
        --out data/empirical/lunarastro_screening_report.json
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from app.empirical.tournament.build_feature_banks import BANKS, bank_columns
from app.empirical.tournament.controls import (
    check_chartless_baseline_arm,
    check_era_coverage,
    check_min_n,
    check_person_leak_arm,
    check_tier,
    era_strata,
    sham_labels,
    sham_tolerance_for,
)
from app.empirical.tournament.holdout import assign_holdout, check_person_leak
from app.empirical.tournament.prereg import Registration, Status
from app.empirical.tournament.run_screening import _cohort
from app.empirical.tournament.scoring import GatedScorer, TestOutcome, summarize
from app.empirical.tournament.synthetic import bootstrap_delta_p, fit_auc

logger = logging.getLogger(__name__)

__all__ = ["run_screening_lunarastro", "candidate_categories", "has_category"]

_SALT: Final[str] = "lunarastro-screening-v1"
_N_SHAM: Final[int] = 10
_MIN_POSITIVES: Final[int] = 200

_CHART_BANKS: Final[tuple[str, ...]] = tuple(b for b in BANKS if b != "chartless")


def _split_labels(label: str) -> list[str]:
    return [c for c in label.split(";") if c]


def candidate_categories(labels: pd.Series, *, min_n: int) -> list[str]:
    """Every distinct category tag appearing on at least ``min_n`` rows.

    Splits each row's semicolon-joined label and tallies individual tags —
    NOT the joined strings themselves, which are near-unique combinations and
    would clear no threshold at all. For a single-valued label (no
    semicolons, as Gauquelin's would be if routed through here) this reduces
    exactly to counting the label itself.
    """
    counts: dict[str, int] = {}
    for label in labels:
        for cat in _split_labels(label):
            counts[cat] = counts.get(cat, 0) + 1
    return [cat for cat, n in counts.items() if n >= min_n]


def has_category(labels: pd.Series, category: str) -> pd.Series:
    """Vectorized 0/1 membership: does this row's tag set contain ``category``?"""
    return labels.apply(lambda label: 1 if category in _split_labels(label) else 0)


def run_screening_lunarastro(
    banks_path: str | Path,
    *,
    tier: str = "A",
    seed: int = 7,
    min_n: int = _MIN_POSITIVES,
) -> tuple[list[TestOutcome], dict[str, object]]:
    """Screen every (chart bank x category tag) pair against the chartless twin."""
    frame = pd.read_parquet(banks_path)
    cohort, drops = _cohort(frame, tier=tier)
    logger.info("cohort: %d of %d rows (tier=%s, quality=ok)", len(cohort), len(frame), tier)
    logger.info("  excluded %d for tier/quality, %d in thin decades %s",
                drops["excluded_quality_or_tier"], drops["excluded_thin_era"], drops["thin_decades"])

    person_ids = cohort["person_id"].tolist()
    holdout = assign_holdout(person_ids, salt=_SALT)
    screening = cohort[~cohort["person_id"].isin(holdout)].reset_index(drop=True)
    logger.info("holdout frozen: %d persons withheld, %d remain for screening",
                len(holdout), len(screening))

    inner_ids = screening["person_id"].tolist()
    inner_eval = assign_holdout(inner_ids, salt=_SALT + "-inner")
    train_mask = np.array([pid not in inner_eval for pid in inner_ids])
    train_ids = [p for p, keep in zip(inner_ids, train_mask) if keep]
    eval_ids = [p for p, keep in zip(inner_ids, train_mask) if not keep]
    check_person_leak(train_ids, eval_ids)

    chartless_cols = bank_columns(screening, "chartless")
    categories = candidate_categories(screening["label"], min_n=min_n)
    logger.info("targets: %d categories with >= %d rows", len(categories), min_n)

    outcomes: list[TestOutcome] = []
    for category in sorted(categories):
        target = has_category(screening["label"], category)
        work = screening.copy()
        work["_y"] = target
        n_pos_eval = int(target[~train_mask].sum())
        n_neg_eval = int((~train_mask).sum() - n_pos_eval)
        if n_pos_eval < 20 or n_neg_eval < 20:
            logger.info("  %s: too few evaluation positives, skipped", category)
            continue

        chartless_auc, y_eval, chartless_scores = fit_auc(
            work, chartless_cols, "_y", train_mask, seed=seed
        )

        for bank in _CHART_BANKS:
            chart_cols = chartless_cols + bank_columns(screening, bank)
            registration = Registration(
                test_id=f"SCR-LA-{bank}-{category}",
                feature_bank=bank,
                target=f"category:{category}",
                statistic="auc",
                baseline_model="chartless_screening",
                control_arms=(
                    "sham_target", "chartless_baseline",
                    "era_stratification", "person_leak_preflight",
                ),
                min_n=min_n,
                tier_requirement="A" if tier == "A" else "AB",
                stage="screening",
                direction="greater",
                # Exploratory: the committed registry is still all drafts. Marked
                # LOCKED only so the machinery will assemble an outcome; the
                # report states plainly that nothing here is a finding.
                status=Status.LOCKED,
                notes="EXPLORATORY — prereg not locked",
            )

            tolerance = sham_tolerance_for(n_pos_eval, n_neg_eval, n_permutations=_N_SHAM)
            sham_aucs = [
                fit_auc(
                    work, chart_cols, "_y", train_mask, seed=seed,
                    target_override=sham_labels(work["_y"], seed=seed + 101 + k),
                )[0]
                for k in range(_N_SHAM)
            ]
            sham_auc = float(np.mean(sham_aucs))

            scorer = GatedScorer(registration, sham_tolerance=tolerance)
            scorer.record_controls([
                check_min_n(int((~train_mask).sum()), registration.min_n),
                check_tier(work["time_tier"], registration.tier_requirement),
                check_era_coverage(era_strata(work["cl_birth_year"].astype(int))),
                check_person_leak_arm(train_ids, eval_ids),
            ])
            sham_outcome = scorer.record_sham(sham_auc)
            if not sham_outcome.passed:
                logger.warning("  %s/%s: %s", bank, category, sham_outcome.detail)
                continue

            chart_auc, _, chart_scores = fit_auc(work, chart_cols, "_y", train_mask, seed=seed)
            p_value = bootstrap_delta_p(y_eval, chart_scores, chartless_scores, seed=seed + 7)
            scorer.record_controls([check_chartless_baseline_arm(chart_auc, chartless_auc)])
            scorer.record_real(
                chart_auc, chartless_auc, p_value=p_value, n=int((~train_mask).sum())
            )
            outcome = scorer.outcome()
            outcomes.append(outcome)
            logger.info(
                "  %-14s %-20s chart=%.4f chartless=%.4f delta=%+.4f p=%.3f sham=%.4f",
                bank, category, chart_auc, chartless_auc, outcome.delta, p_value, sham_auc,
            )

    report = summarize(outcomes)
    report["corpus"] = "lunarastro"
    report["all_outcomes"] = [
        {
            "test_id": o.test_id,
            "feature_bank": o.feature_bank,
            "target": o.target,
            "chart_statistic": round(o.chart_statistic, 4),
            "chartless_statistic": round(o.chartless_statistic, 4),
            "delta": round(o.delta, 4),
            "p_value": round(o.p_value, 4),
            "sham_statistic": round(o.sham_statistic, 4),
            "n": o.n,
            "admitted": o.admitted,
            "unmet_arms": list(o.unmet_arms),
        }
        for o in outcomes
    ]
    report["n_holdout"] = len(holdout)
    report["n_categories_tested"] = len(categories)
    return outcomes, report


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Screen the LunarAstro corpus by category tag.")
    parser.add_argument("--banks", required=True, help="feature-bank parquet path")
    parser.add_argument("--out", required=True, help="output report JSON path")
    parser.add_argument("--min-n", type=int, default=_MIN_POSITIVES)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _outcomes, report = run_screening_lunarastro(args.banks, min_n=args.min_n)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    logger.info("")
    logger.info("=== %d registered, %d admitted, %d survivors (q=%.2f) ===",
                report["n_registered"], report["n_admitted"], report["n_survivors"], report["fdr_q"])
    logger.info("wrote %s", out)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
