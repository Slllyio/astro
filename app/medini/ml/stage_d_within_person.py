"""Stage D follow-up: within-person concordance test.

Background: 4 prior ML attempts on this corpus returned NULL VERDICTS, all
between-person comparisons (does person A's life predict events better than
person B's). Stage D Dynamic-DeepHit at 5 seeds confirmed: mean Delta = -0.16,
DeepHit worse than Cox by 4σ in the wrong direction.

What none of the 4 attempts tested: within a SINGLE person, do dasha windows
the Cox model rates as high-hazard actually contain more events than the
windows it rates low-hazard?

This factors out every person-level confound (birth year, ascendant, document-
ation density, selection bias). Within a person, chart features are constant;
only dasha-time features vary. If real structural Vedic signal exists, this is
where it would still appear.

We compute pairwise concordance restricted to within-person (event_window,
non_event_window) pairs using fitted Cox baseline. We also report a per-class
permutation p-value (shuffle event labels within each person; recompute).

Usage:
    py -3.12 -m app.medini.ml.stage_d_within_person --seed 1 \\
        --classes fame career business finance marriage \\
        --out data/ml_runs/fork_a_stage_d_subsample/within_person_seed1.md
"""
from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from app.medini.ml.stage_d_baseline import (
    PENALIZER,
    _feature_columns,
    _ordinal_encode_lords,
    split_train_test,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WithinPersonResult:
    event_class: str
    seed: int
    n_concordant: int
    n_discordant: int
    n_ties: int
    n_pairs: int
    n_persons_with_pairs: int
    concordance: float        # 0.5 = chance
    p_value_perm: float       # one-sided: P(concordance >= observed | shuffled labels)
    population_c_index: float # the population-level Cox c-index (for comparison)


def _fit_cox_and_predict(
    train: pd.DataFrame, test: pd.DataFrame, *, event_class: str,
) -> tuple[pd.Series, float]:
    """Re-fit cause-specific Cox PH on train, return (test_hazard, c_index).

    Mirrors stage_d_baseline.fit_cause_specific_cox but exposes the per-test-row
    partial hazard (lifelines doesn't expose it from CoxFitResult).
    """
    from lifelines import CoxPHFitter
    from lifelines.utils import concordance_index

    train_e = _ordinal_encode_lords(train)
    test_e = _ordinal_encode_lords(test)
    event_col = f"event_{event_class}"
    features = _feature_columns(train_e)
    # Variance filter (same logic as fit_cause_specific_cox).
    feat_var = train_e[features].var()
    features = [c for c in features if feat_var[c] > 0]

    cph_input = train_e[features + ["window_duration_days", event_col]].copy()
    cph_input.rename(columns={"window_duration_days": "T", event_col: "E"}, inplace=True)
    cph = CoxPHFitter(penalizer=PENALIZER, l1_ratio=1.0)
    cph.fit(cph_input, duration_col="T", event_col="E", show_progress=False)

    hazard = cph.predict_partial_hazard(test_e[features])
    # Reset to the original test row order so we can join on test indices.
    hazard.index = test.index
    c = float(concordance_index(test["window_duration_days"], -hazard, test_e[event_col]))
    return hazard, c


def within_person_concordance(
    test: pd.DataFrame,
    hazard: pd.Series,
    *,
    event_class: str,
    group_col: str = "name_norm",
) -> tuple[int, int, int, int]:
    """Count concordant / discordant / tied pairs WITHIN each person.

    A pair is two windows from the SAME person, one with event=1 and one with
    event=0. Concordant = event window has higher hazard than non-event window.

    Returns: (n_concordant, n_discordant, n_ties, n_persons_contributing).
    """
    event_col = f"event_{event_class}"
    nc = nd = nt = 0
    persons = 0
    # Pre-extract numpy arrays for speed (groupby with python loop is slow).
    for _, group in test.groupby(group_col, sort=False):
        events = group[event_col].values
        hzs = hazard.loc[group.index].values
        ev_mask = events == 1
        ne_mask = events == 0
        if not ev_mask.any() or not ne_mask.any():
            continue
        persons += 1
        ev_h = hzs[ev_mask]
        ne_h = hzs[ne_mask]
        # All ev x ne pairs at once via broadcasting.
        diff = ev_h[:, None] - ne_h[None, :]
        nc += int((diff > 0).sum())
        nd += int((diff < 0).sum())
        nt += int((diff == 0).sum())
    return nc, nd, nt, persons


def _permutation_p(
    test: pd.DataFrame, hazard: pd.Series, *, event_class: str,
    observed_c: float, n_perm: int = 1000, seed: int = 42,
) -> float:
    """Shuffle event labels WITHIN each person; recompute concordance n_perm times.

    P-value = fraction of permutations producing concordance >= observed.
    Within-person shuffle preserves per-person event counts (so persons with
    1/0 events stay that way) — only the dasha-window assignment of events is
    permuted, which is exactly the null we want to test.
    """
    event_col = f"event_{event_class}"
    rng = np.random.default_rng(seed)
    perm_test = test.copy()
    n_geq = 0
    for _ in range(n_perm):
        # Shuffle event labels within each person.
        for _, idx in perm_test.groupby("name_norm", sort=False).indices.items():
            if len(idx) < 2:
                continue
            shuffled = perm_test[event_col].values[idx].copy()
            rng.shuffle(shuffled)
            perm_test.iloc[idx, perm_test.columns.get_loc(event_col)] = shuffled
        nc, nd, nt, _ = within_person_concordance(
            perm_test, hazard, event_class=event_class,
        )
        total = nc + nd + nt
        if total == 0:
            continue
        c_perm = (nc + 0.5 * nt) / total
        if c_perm >= observed_c:
            n_geq += 1
    return (n_geq + 1) / (n_perm + 1)  # Laplace-smoothed


def evaluate_one_class(
    train: pd.DataFrame, test: pd.DataFrame, *, event_class: str, seed: int,
    n_perm: int,
) -> WithinPersonResult:
    t0 = time.time()
    hazard, c_pop = _fit_cox_and_predict(train, test, event_class=event_class)
    nc, nd, nt, n_persons = within_person_concordance(
        test, hazard, event_class=event_class,
    )
    n_pairs = nc + nd + nt
    concordance = (nc + 0.5 * nt) / n_pairs if n_pairs else float("nan")
    if n_pairs > 0 and n_perm > 0:
        p_perm = _permutation_p(
            test, hazard, event_class=event_class,
            observed_c=concordance, n_perm=n_perm,
        )
    else:
        p_perm = float("nan")
    logger.info(
        "class=%s seed=%d c_within=%.4f n_pairs=%d n_persons=%d p_perm=%.4f c_pop=%.4f (%.1fs)",
        event_class, seed, concordance, n_pairs, n_persons, p_perm, c_pop,
        time.time() - t0,
    )
    return WithinPersonResult(
        event_class=event_class, seed=seed,
        n_concordant=nc, n_discordant=nd, n_ties=nt, n_pairs=n_pairs,
        n_persons_with_pairs=n_persons,
        concordance=concordance, p_value_perm=p_perm,
        population_c_index=c_pop,
    )


def _render_report(results: list[WithinPersonResult], *, seed: int) -> str:
    lines = [
        "# Stage D follow-up · Within-person concordance test",
        "",
        f"**Seed**: {seed}",
        f"**Substrate**: subsample_2000p (1.2M rows / 2000 persons)",
        "",
        "## Background",
        "",
        "Within a single person, chart features are constant (asc, planets, lords).",
        "Only dasha-time features vary. This test asks: does a fitted Cox model rank",
        "a person's actual event-windows higher than their non-event-windows?",
        "",
        "If yes (concordance significantly > 0.5), there is at least within-person",
        "dasha-time signal even though between-person prediction has failed.",
        "",
        "If no (concordance ~ 0.5 with p > 0.05), the data has no recoverable",
        "structural signal — between OR within person — and the prediction question",
        "is definitively closed.",
        "",
        "## Results",
        "",
        "| Class | n_pairs | n_persons | C_within | p_perm | C_pop | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in results:
        if r.n_pairs == 0:
            verdict = "no usable pairs"
        elif r.p_value_perm < 0.01 and r.concordance > 0.55:
            verdict = "**SIGNAL**"
        elif r.p_value_perm < 0.05:
            verdict = "weak"
        else:
            verdict = "null"
        lines.append(
            f"| {r.event_class} | {r.n_pairs} | {r.n_persons_with_pairs} | "
            f"{r.concordance:.4f} | {r.p_value_perm:.4f} | "
            f"{r.population_c_index:.4f} | {verdict} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- **C_within**: pairwise concordance over (event, non-event) windows within",
        "  the SAME person. 0.5 = chance.",
        "- **p_perm**: one-sided permutation test, shuffling event labels within",
        "  each person (preserves per-person event counts). 1000 permutations.",
        "- **C_pop**: lifelines population concordance (between-person).",
        "",
        "If C_within tracks C_pop tightly, within-person variance contributes nothing",
        "beyond what between-person already captures.",
        "If C_within > C_pop and p_perm < 0.05, dasha-time signal exists at the",
        "individual scale but is washed out by between-person confounding.",
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.medini.ml.stage_d_within_person")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--classes", nargs="+", default=None,
                   help="Event classes to test. Default: top 5 by test-positive count.")
    p.add_argument("--n-perm", type=int, default=1000)
    p.add_argument("--features", type=Path,
                   default=Path("app/medini/data/dasha_stage_d_features_subsample.parquet"))
    p.add_argument("--out", type=Path,
                   default=Path("data/ml_runs/fork_a_stage_d_subsample/within_person_seed1.md"))
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s :: %(message)s")
    logger.info("Loading %s", args.features)
    df = pd.read_parquet(args.features)
    train, test = split_train_test(df, seed=args.seed)
    logger.info("Split: train=%d rows / %d persons, test=%d rows / %d persons",
                len(train), train["name_norm"].nunique(),
                len(test), test["name_norm"].nunique())

    if args.classes is None:
        # Top 5 classes by test-positive count.
        positives = {
            c: int(test[f"event_{c}"].sum())
            for c in [col[len("event_"):] for col in test.columns
                      if col.startswith("event_") and not col.startswith("event_jd_")]
            if f"event_{c}" in test.columns
        }
        top = sorted(positives.items(), key=lambda kv: -kv[1])[:5]
        args.classes = [c for c, _ in top]
        logger.info("Auto-picked top-5 classes by test positives: %s",
                    [(c, n) for c, n in top])

    results: list[WithinPersonResult] = []
    for cls in args.classes:
        try:
            r = evaluate_one_class(
                train, test, event_class=cls, seed=args.seed, n_perm=args.n_perm,
            )
            results.append(r)
        except Exception as e:
            logger.error("class=%s failed: %s", cls, e)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(_render_report(results, seed=args.seed), encoding="utf-8")
    # Also dump raw JSON next to the report for downstream aggregation.
    jpath = args.out.with_suffix(".json")
    jpath.write_text(json.dumps([asdict(r) for r in results], indent=2))
    logger.info("Wrote %s + %s", args.out, jpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
