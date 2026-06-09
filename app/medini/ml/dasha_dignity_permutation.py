"""Permutation control for the dignity × life-stage interaction.

Finding 3 of the LunarAstro run was a +0.21 *prime-stage pair gradient*:
when BOTH the MD and AD lord are well-disposed in the native's chart,
prime-life events skew beneficial. The honest question (the one that
collapsed Round-11's RR=2.31) is whether that reflects a genuine match
between THIS person's chart and THIS person's events, or an artifact of
lord-identity/age structure that any chart would reproduce.

Test: keep every event's (md_lord, ad_lord, age/life_stage, valence)
fixed — those come from the real dasha timeline — but **score the running
lords' dignity from a SHUFFLED chart** (a random other person's natal
chart). Recompute the gradient. Repeat K times to build a null.

  * If the real gradient sits deep in the upper tail of the null
    (z large, empirical p small), the chart→event match carries signal.
  * If the null routinely reaches the real value, the gradient is
    lifecycle/identity structure, not chart-structure — the Round-11
    outcome.

Only the chart assignment is permuted; lord identities, event timing and
valence are untouched, so this isolates the chart-structural contribution.

Usage::

    python -m app.medini.ml.dasha_dignity_permutation \\
        --data-dir app/medini/data/lunarastro_run \\
        --out data/ml_runs/lunarastro_dignity --k 200 --seed 0
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from app.medini.ml.dasha_lifestage_dignity import (
    _QUALITY_ORDER, event_valence, life_stage, md_lord_quality,
)

logger = logging.getLogger(__name__)

_LORDS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_STRONG, _WEAK = 0.33, -0.33


def precompute_quality(charts: pd.DataFrame) -> tuple[list[str], np.ndarray]:
    """Q[i, j] = composite quality_score of lord j in person i's chart.

    Computed once (n_charts × 9), so each permutation is a cheap re-index
    instead of millions of dignity recomputations.
    """
    persons = charts["person_id"].tolist()
    q = np.zeros((len(persons), len(_LORDS)), dtype=float)
    asc = charts["asc_sign"].to_numpy()
    sign_cols = {lord: charts[f"{lord.lower()}_sign"].to_numpy() for lord in _LORDS}
    for i in range(len(persons)):
        a = int(asc[i]) if pd.notna(asc[i]) else None
        for j, lord in enumerate(_LORDS):
            s = sign_cols[lord][i]
            q[i, j] = md_lord_quality(
                lord, int(s) if pd.notna(s) else None, a)["quality_score"]
    return persons, q


def _gradient(pair_score: np.ndarray, benefit: np.ndarray, prime: np.ndarray) -> float:
    """Strong − weak benefit share within the prime life stage.

    Returns NaN if either tail is empty (so a permutation with no strong
    or no weak prime events is dropped rather than biasing the null)."""
    strong = prime & (pair_score >= _STRONG)
    weak = prime & (pair_score <= _WEAK)
    if not strong.any() or not weak.any():
        return float("nan")
    return float(benefit[strong].mean() - benefit[weak].mean())


def run_permutation(
    events: pd.DataFrame, charts: pd.DataFrame, *, k: int = 200, seed: int = 0,
) -> dict[str, object]:
    """Compute the real prime pair gradient and a K-sample chart-shuffle null."""
    persons, q = precompute_quality(charts)
    pid_index = {p: i for i, p in enumerate(persons)}
    lord_index = {l: j for j, l in enumerate(_LORDS)}

    # Keep only events whose person has a chart, with a usable valence.
    df = events.copy()
    df["valence"] = [
        event_valence(c, s)
        for c, s in zip(df["event_class"],
                        df.get("event_subtype", pd.Series([None] * len(df))))
    ]
    df["life_stage"] = df["age_at_event_years"].map(life_stage)
    keep = (
        df["person_id"].isin(pid_index)
        & df["md_lord_at_event"].isin(lord_index)
        & df["ad_lord_at_event"].isin(lord_index)
        & (df["valence"] != 0)
        & df["life_stage"].notna()
    )
    df = df[keep]

    pe = df["person_id"].map(pid_index).to_numpy()
    md = df["md_lord_at_event"].map(lord_index).to_numpy()
    ad = df["ad_lord_at_event"].map(lord_index).to_numpy()
    benefit = (df["valence"].to_numpy() > 0).astype(float)
    prime = (df["life_stage"].to_numpy() == "prime")

    def gradient_for(donor: np.ndarray) -> float:
        dp = donor[pe]                       # chart index used to score each event
        pair = (q[dp, md] + q[dp, ad]) / 2.0
        return _gradient(pair, benefit, prime)

    identity = np.arange(len(persons))
    real = gradient_for(identity)

    rng = np.random.default_rng(seed)
    null = np.empty(k, dtype=float)
    for i in range(k):
        null[i] = gradient_for(rng.permutation(len(persons)))
    null = null[~np.isnan(null)]

    if len(null) == 0 or np.isnan(real):
        # Degenerate (e.g. weights that never populate a strong/weak tail).
        return {
            "n_events": int(len(df)), "n_prime_events": int(prime.sum()),
            "real_gradient": None if np.isnan(real) else round(real, 4),
            "null_mean": None, "null_std": None, "null_min": None,
            "null_max": None, "k_effective": 0, "z_score": None,
            "empirical_p": None, "exceed_real": 0,
        }

    mean, std = float(null.mean()), float(null.std(ddof=1))
    z = (real - mean) / std if std > 0 else float("nan")
    emp_p = float((null >= real).sum() + 1) / (len(null) + 1)  # +1 smoothing
    return {
        "n_events": int(len(df)),
        "n_prime_events": int(prime.sum()),
        "real_gradient": round(real, 4),
        "null_mean": round(mean, 4),
        "null_std": round(std, 4),
        "null_min": round(float(null.min()), 4),
        "null_max": round(float(null.max()), 4),
        "k_effective": int(len(null)),
        "z_score": round(z, 3),
        "empirical_p": round(emp_p, 4),
        "exceed_real": int((null >= real).sum()),
    }


def _verdict(r: dict[str, object]) -> str:
    z = r["z_score"]
    p = r["empirical_p"]
    if isinstance(z, float) and z >= 2.0 and p <= 0.05:
        return ("✅ SIGNAL — the real prime pair gradient sits in the upper "
                "tail of the chart-shuffle null. Chart→event match carries "
                "structural signal at this sample size.")
    if isinstance(z, float) and z >= 1.0:
        return ("🤔 HINT — directionally above the null but not resolved. "
                "Needs larger K or sample to separate from chart-permutation "
                "variance (the Round-11 situation).")
    return ("🚫 NULL — the chart-shuffle null routinely reaches the real "
            "gradient. The +0.21 is lifecycle/identity structure, not "
            "chart-structure. (Consistent with round11_triple_test_synthesis.)")


def build_report(r: dict[str, object], *, k: int, seed: int) -> str:
    return "\n".join([
        "# Permutation control — prime-stage MD+AD pair dignity gradient",
        "",
        f"Chart-shuffle null, K={k}, seed={seed}. Statistic: strong−weak "
        "benefit share among prime-life events, where pair quality = mean of "
        "the MD and AD lords' composite dignity scores.",
        "",
        "| quantity | value |",
        "|---|---|",
        f"| events (charted, valenced) | {r['n_events']} |",
        f"| prime-stage events | {r['n_prime_events']} |",
        f"| **real gradient** | **{r['real_gradient']:+.4f}** |",
        f"| null mean | {r['null_mean']:+.4f} |",
        f"| null std | {r['null_std']:.4f} |",
        f"| null min / max | {r['null_min']:+.4f} / {r['null_max']:+.4f} |",
        f"| K effective | {r['k_effective']} |",
        f"| shuffled ≥ real | {r['exceed_real']} / {r['k_effective']} |",
        f"| **z-score** | **{r['z_score']}** |",
        f"| **empirical p** | **{r['empirical_p']}** |",
        "",
        "## Verdict",
        "",
        f"> {_verdict(r)}",
        "",
    ])


def run(data_dir: Path, out_dir: Path, *, k: int = 200, seed: int = 0) -> dict[str, object]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    events = events[events["md_lord_at_event"].notna()].copy()
    charts = pd.read_parquet(data_dir / "charts.parquet")
    logger.info("events=%d charts=%d", len(events), len(charts))

    r = run_permutation(events, charts, k=k, seed=seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "permutation_test.md").write_text(
        build_report(r, k=k, seed=seed), encoding="utf-8")
    (out_dir / "permutation_test.json").write_text(
        json.dumps(r, indent=2), encoding="utf-8")
    logger.info("permutation result: %s", r)
    return r


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path,
                        default=Path("app/medini/data/lunarastro_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/lunarastro_dignity"))
    parser.add_argument("--k", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(run(args.data_dir, args.out, k=args.k, seed=args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
