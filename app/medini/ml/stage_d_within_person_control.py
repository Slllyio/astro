"""Confound check for stage_d_within_person.py.

The DeepHit within-person test showed C_within = 0.58-0.61 across 5 classes
on 5 seeds. Before claiming Vedic signal, we must rule out the obvious
confound: documented life events cluster in adult years, so a model that
learns "predict higher hazard for adult-life windows" gets high within-person
concordance without any astrological information.

This script uses **age-at-window-start as the only risk score** (no model,
no chart features). If age alone produces C_within ≈ 0.6, the DeepHit
"signal" is age learning. If age produces C_within ≈ 0.5, the chart
structure is doing real work.

Usage:
    py -3.12 -m app.medini.ml.stage_d_within_person_control \\
        --seeds 1 2 3 4 5 \\
        --out data/ml_runs/fork_a_stage_d_subsample/within_person_control.md
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from app.medini.ml.stage_d_baseline import split_train_test
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
from app.medini.ml.stage_d_within_person import (
    _permutation_p,
    _within_person_concordance,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ControlResult:
    event_class: str
    seed: int
    risk_source: str       # "age" | "duration" | "sequence_idx"
    n_test_positives: int
    n_pairs: int
    n_persons_with_pairs: int
    concordance: float
    p_value_perm: float


def _evaluate_control(
    test: pd.DataFrame, *, seed: int, classes: list[str], risk_col: str,
    risk_label: str, n_perm: int,
) -> list[ControlResult]:
    """For each class, compute within-person concordance using `risk_col` as risk.

    Higher value of `risk_col` = higher predicted hazard. For age, higher age
    means more likely event. For window_duration_days, longer windows means
    more time to accumulate events.
    """
    person_ids = test["name_norm"].to_numpy()
    risks = test[risk_col].to_numpy().astype(np.float64)
    results: list[ControlResult] = []
    for cls in classes:
        event_col = f"event_{cls}"
        if event_col not in test.columns:
            continue
        events = test[event_col].to_numpy().astype(np.int8)
        n_pos = int(events.sum())
        nc, nd, nt, n_persons = _within_person_concordance(person_ids, events, risks)
        n_pairs = nc + nd + nt
        if n_pairs == 0:
            continue
        c = (nc + 0.5 * nt) / n_pairs
        p = _permutation_p(person_ids, events, risks,
                           observed_c=c, n_perm=n_perm, seed=seed)
        logger.info(
            "  risk=%-13s cls=%-25s n_pos=%3d c_within=%.4f n_pairs=%5d p_perm=%.4f",
            risk_label, cls, n_pos, c, n_pairs, p,
        )
        results.append(ControlResult(
            event_class=cls, seed=seed, risk_source=risk_label,
            n_test_positives=n_pos, n_pairs=n_pairs,
            n_persons_with_pairs=n_persons,
            concordance=c, p_value_perm=p,
        ))
    return results


def _render_report(
    deephit_results_path: Path,
    age_results: list[ControlResult],
    duration_results: list[ControlResult],
    combined_results: list[ControlResult] | None = None,
) -> str:
    """Side-by-side report: DeepHit vs age-only vs duration-only."""
    # Load DeepHit results for comparison.
    deephit = json.loads(deephit_results_path.read_text()) if deephit_results_path.exists() else []
    # Aggregate per-class mean concordance.
    def by_class(records: list, c_key: str) -> dict[str, float]:
        out: dict[str, list[float]] = {}
        for r in records:
            cls = r["event_class"]
            c = r[c_key]
            if c == c:  # not NaN
                out.setdefault(cls, []).append(c)
        return {k: sum(v) / len(v) for k, v in out.items()}

    deephit_means = by_class(deephit, "concordance")
    age_means = by_class([asdict(r) for r in age_results], "concordance")
    duration_means = by_class([asdict(r) for r in duration_results], "concordance")
    combined_means = (by_class([asdict(r) for r in combined_results], "concordance")
                      if combined_results else {})

    lines = [
        "# Within-person concordance — confound control",
        "",
        "Comparing the trained DeepHit model's within-person concordance against",
        "trivial baselines that use NO chart features:",
        "",
        "- **age**: window_start_jd - birth_jd (age in days at window start)",
        "- **duration**: window_duration_days (longer windows have more event opportunity)",
        "- **age+dur**: rank-sum of age and duration within each person (combined baseline)",
        "",
        "If age, duration, or their combination achieves similar C_within to DeepHit,",
        "the 'within-person signal' is a structural/exposure artifact, not Vedic.",
        "",
        "## Per-class mean C_within (over 5 seeds)",
        "",
        "| Class | DeepHit | Age | Duration | Age+Dur | DH - max(baseline) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    all_classes = sorted(set(deephit_means) | set(age_means) | set(duration_means))
    for cls in all_classes:
        dh = deephit_means.get(cls, float("nan"))
        ag = age_means.get(cls, float("nan"))
        du = duration_means.get(cls, float("nan"))
        co = combined_means.get(cls, float("nan"))
        best_baseline = max(
            (x for x in (ag, du, co) if x == x),  # filter NaN
            default=float("nan"),
        )
        delta = dh - best_baseline if (dh == dh and best_baseline == best_baseline) else float("nan")
        lines.append(
            f"| {cls} | {dh:.4f} | {ag:.4f} | {du:.4f} | {co:.4f} | {delta:+.4f} |"
        )
    lines.extend([
        "",
        "## Verdict heuristic",
        "",
        "- If `DH - max(baseline)` is large positive (> +0.03), DeepHit adds chart",
        "  structure on top of age+duration — Vedic signal is real (modest).",
        "- If `DH - max(baseline)` is near zero or negative, the model adds nothing",
        "  beyond trivial duration/age exposure — chart structure has no signal,",
        "  and the original within-person concordance was a duration confound.",
        "- Age-only is often REVERSED for life events (fame, career, personal come",
        "  at younger windows-of-life; only death tracks age positively).",
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.medini.ml.stage_d_within_person_control")
    p.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    p.add_argument("--classes", nargs="+", default=None,
                   help="Default: same top-5 as the DeepHit run.")
    p.add_argument("--n-perm", type=int, default=1000)
    p.add_argument("--features", type=Path,
                   default=Path("app/medini/data/dasha_stage_d_features_subsample.parquet"))
    p.add_argument("--deephit-json", type=Path,
                   default=Path("data/ml_runs/fork_a_stage_d_subsample/within_person_dml.json"))
    p.add_argument("--out", type=Path,
                   default=Path("data/ml_runs/fork_a_stage_d_subsample/within_person_control.md"))
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s :: %(message)s")
    df = pd.read_parquet(args.features)

    if args.classes is None:
        # Same auto-pick as the DeepHit run (top-5 by seed=1 test positives).
        _, test0 = split_train_test(df, seed=args.seeds[0])
        positives = {
            c: int(test0[f"event_{c}"].sum())
            for c in QUALIFYING_EVENT_CLASSES if f"event_{c}" in test0.columns
        }
        top = sorted(positives.items(), key=lambda kv: -kv[1])[:5]
        args.classes = [c for c, _ in top]
        logger.info("Using top-5 classes: %s", [c for c, _ in top])

    age_results: list[ControlResult] = []
    duration_results: list[ControlResult] = []
    combined_results: list[ControlResult] = []
    for s in args.seeds:
        logger.info("=== seed=%d ===", s)
        _, test_df = split_train_test(df, seed=s)
        test_df = test_df.copy()  # avoid SettingWithCopy
        test_df["age_at_window_days"] = test_df["window_start_jd"] - test_df["birth_jd"]
        # Combined risk = rank-sum of (age, duration) WITHIN each person, then
        # combined back. This gives an "age+duration" baseline that uses both
        # features without committing to a specific functional form. If this
        # matches DeepHit, then DH adds nothing chart-specific beyond
        # age+duration mechanics.
        test_df["age_rank"] = test_df.groupby("name_norm")["age_at_window_days"].rank()
        test_df["dur_rank"] = test_df.groupby("name_norm")["window_duration_days"].rank()
        test_df["age_plus_dur_rank"] = test_df["age_rank"] + test_df["dur_rank"]
        age_results.extend(_evaluate_control(
            test_df, seed=s, classes=args.classes,
            risk_col="age_at_window_days", risk_label="age",
            n_perm=args.n_perm,
        ))
        duration_results.extend(_evaluate_control(
            test_df, seed=s, classes=args.classes,
            risk_col="window_duration_days", risk_label="duration",
            n_perm=args.n_perm,
        ))
        combined_results.extend(_evaluate_control(
            test_df, seed=s, classes=args.classes,
            risk_col="age_plus_dur_rank", risk_label="age+dur",
            n_perm=args.n_perm,
        ))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        _render_report(args.deephit_json, age_results, duration_results,
                       combined_results=combined_results),
        encoding="utf-8",
    )
    jpath = args.out.with_suffix(".json")
    jpath.write_text(json.dumps({
        "age": [asdict(r) for r in age_results],
        "duration": [asdict(r) for r in duration_results],
        "combined": [asdict(r) for r in combined_results],
    }, indent=2))
    logger.info("Wrote %s + %s", args.out, jpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
