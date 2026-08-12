"""Run the screening stage of the tournament over an acquired corpus.

**Screening, not confirmatory.** This stage looks only at the training portion.
The 25% holdout is assigned and then left strictly alone — no model sees it, no
statistic is computed on it. Screening exists to decide which tests are worth
re-registering for a confirmatory run; a result here is a candidate, never a
finding.

**Nothing here is scorable while the registry is unlocked.** Every row in
``tools/empirical/prereg.csv`` is a draft, so this run is explicitly exploratory
and says so in its own output. Locking a row is a scientific commitment and is
the author's to make, not this script's.

The protocol is the real one regardless: sham read before the real result, every
chart bank scored as its delta over the chartless twin on the identical split,
and Benjamini-Hochberg across the whole family at q=0.10.

Usage:
    python -m app.empirical.tournament.run_screening \
        --banks data/empirical/feature_banks.parquet \
        --out data/empirical/screening_report.json
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
from app.empirical.tournament.scoring import GatedScorer, TestOutcome, summarize, survivors
from app.empirical.tournament.synthetic import bootstrap_delta_p, fit_auc

logger = logging.getLogger(__name__)

__all__ = ["run_screening"]

_SALT: Final[str] = "gauquelin-screening-v1"
_N_SHAM: Final[int] = 10
_MIN_POSITIVES: Final[int] = 200

#: Chart banks that compete. ``chartless`` is the twin, not a competitor.
_CHART_BANKS: Final[tuple[str, ...]] = tuple(b for b in BANKS if b != "chartless")


def _cohort(
    frame: pd.DataFrame,
    *,
    tier: str,
    min_per_stratum: int = 30,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """The admissible rows: requested birth-time tier, no quality flags, and no
    era stratum too thin to support stratified analysis.

    Rows CURA publishes with impossible dates or years are excluded here rather
    than silently carried — they were flagged at import precisely so this filter
    could be explicit.

    Thin birth decades are dropped rather than pooled. A decade holding two
    people contributes noise with a confident-looking point estimate: it is the
    small-sample positive bias that made Round 11's within-lord RR=1.58 look
    like signal when the shuffled null sat at exactly the same value. The
    era_stratification arm demands this be resolved before scoring; dropping is
    the conservative resolution, and the count is reported rather than absorbed.

    Returns:
      ``(cohort, drop_counts)`` so the caller can disclose what was removed.
    """
    keep = frame["data_quality"].eq("ok")
    if tier == "A":
        keep &= frame["time_tier"].eq("A")
    cohort = frame[keep].reset_index(drop=True)

    decades = (cohort["cl_birth_year"].astype(int) // 10) * 10
    counts = decades.value_counts()
    thin = set(counts[counts < min_per_stratum].index)
    dropped_thin = int(decades.isin(thin).sum())
    cohort = cohort[~decades.isin(thin)].reset_index(drop=True)

    return cohort, {
        "excluded_quality_or_tier": int(len(frame) - int(keep.sum())),
        "excluded_thin_era": dropped_thin,
        "thin_decades": sorted(int(d) for d in thin),
    }


def run_screening(
    banks_path: str | Path,
    *,
    tier: str = "A",
    seed: int = 7,
) -> tuple[list[TestOutcome], dict[str, object]]:
    """Screen every (chart bank x profession) pair against the chartless twin."""
    frame = pd.read_parquet(banks_path)
    cohort, drops = _cohort(frame, tier=tier)
    logger.info("cohort: %d of %d rows (tier=%s, quality=ok)", len(cohort), len(frame), tier)
    logger.info("  excluded %d for tier/quality, %d in thin decades %s",
                drops["excluded_quality_or_tier"], drops["excluded_thin_era"], drops["thin_decades"])

    # Freeze the holdout and drop it. Screening never sees these people.
    person_ids = cohort["person_id"].tolist()
    holdout = assign_holdout(person_ids, salt=_SALT)
    screening = cohort[~cohort["person_id"].isin(holdout)].reset_index(drop=True)
    logger.info("holdout frozen: %d persons withheld, %d remain for screening",
                len(holdout), len(screening))

    # Inside screening, split again for fit/evaluate.
    inner_ids = screening["person_id"].tolist()
    inner_eval = assign_holdout(inner_ids, salt=_SALT + "-inner")
    train_mask = np.array([pid not in inner_eval for pid in inner_ids])
    train_ids = [p for p, keep in zip(inner_ids, train_mask) if keep]
    eval_ids = [p for p, keep in zip(inner_ids, train_mask) if not keep]
    check_person_leak(train_ids, eval_ids)

    chartless_cols = bank_columns(screening, "chartless")
    professions = [
        p for p, n in screening["label"].value_counts().items() if n >= _MIN_POSITIVES
    ]
    logger.info("targets: %d professions with >= %d rows", len(professions), _MIN_POSITIVES)

    outcomes: list[TestOutcome] = []
    for profession in sorted(professions):
        target = (screening["label"] == profession).astype(int)
        work = screening.copy()
        work["_y"] = target
        n_pos_eval = int(target[~train_mask].sum())
        n_neg_eval = int((~train_mask).sum() - n_pos_eval)
        if n_pos_eval < 20 or n_neg_eval < 20:
            logger.info("  %s: too few evaluation positives, skipped", profession)
            continue

        chartless_auc, y_eval, chartless_scores = fit_auc(
            work, chartless_cols, "_y", train_mask, seed=seed
        )

        for bank in _CHART_BANKS:
            chart_cols = chartless_cols + bank_columns(screening, bank)
            registration = Registration(
                test_id=f"SCR-{bank}-{profession}",
                feature_bank=bank,
                target=f"profession:{profession}",
                statistic="auc",
                baseline_model="chartless_screening",
                control_arms=(
                    "sham_target", "chartless_baseline",
                    "era_stratification", "person_leak_preflight",
                ),
                min_n=_MIN_POSITIVES,
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
                logger.warning("  %s/%s: %s", bank, profession, sham_outcome.detail)
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
                "  %-14s %-16s chart=%.4f chartless=%.4f delta=%+.4f p=%.3f sham=%.4f",
                bank, profession, chart_auc, chartless_auc, outcome.delta, p_value, sham_auc,
            )

    report = summarize(outcomes)
    report["stage"] = "screening"
    report["exploratory"] = True
    report["exploratory_reason"] = (
        "tools/empirical/prereg.csv contains only DRAFT rows. No result here is a "
        "finding; survivors are candidates to re-register for a confirmatory run."
    )
    report["cohort_rows"] = len(cohort)
    report["cohort_exclusions"] = drops
    report["screening_rows"] = len(screening)
    report["holdout_persons_untouched"] = len(holdout)
    report["tier"] = tier
    return outcomes, report


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run the tournament screening stage.")
    parser.add_argument("--banks", required=True, help="feature-bank parquet")
    parser.add_argument("--out", required=True, help="output JSON report")
    parser.add_argument("--tier", default="A", choices=["A", "AB"], help="birth-time tier floor")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    outcomes, report = run_screening(args.banks, tier=args.tier)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    kept = survivors(outcomes)
    logger.info("")
    logger.info("=== SCREENING VERDICT (exploratory — prereg unlocked) ===")
    logger.info("%s", report["verdict"])
    if kept:
        for outcome in kept:
            logger.info("  candidate: %s delta=%+.4f p=%.4f",
                        outcome.test_id, outcome.delta, outcome.p_value)
    else:
        logger.info("  No chart bank beat its chartless twin after FDR correction.")
    logger.info("wrote %s", out)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
