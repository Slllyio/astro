"""Stage E — Dasha lord-house-relationship scoring + Poisson hazard test.

The user observed correctly: "MD, AD, PD lords are ruling which houses,
present where, and aspecting where — these matter."

Bare lord identity (Saturn vs Venus) was too coarse and only fame
survived Bonferroni at RR=1.39. Classical doctrine says a dasha lord
activates a house's matters via THREE channels — lordship, occupancy,
aspect — and event rates should peak when the lord has ANY of those
relationships to the karaka-house of the event class.

Per-(person, dasha_lord) we compute a 0-3 relevance score:
  + 1 if lord rules any karaka-house of the event class
  + 1 if lord occupies any karaka-house of the event class
  + 1 if lord aspects any karaka-house of the event class

Then we run the same exposure-adjusted Poisson rate-ratio test as
Stage B-corrected, but now stratified by relevance score 0..3.

If the score genuinely captures classical doctrine, we should see
monotonic increase in event rate across score levels. The Poisson
trend test gives a single p-value per class.

The per-class house mappings here are PROVISIONAL — based on standard
BPHS karaka attributions. They will be refined when the BN Rao deep
research completes (at `docs/dasha_house_lord_doctrine.md`).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom, norm

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Per-event-class karaka houses (provisional — BPHS chapters 11-21)           #
# --------------------------------------------------------------------------- #

_EVENT_CLASS_HOUSES: dict[str, frozenset[int]] = {
    # Career / profession — 10H is karma, 6H is service/employment, 2H is income
    "career":                          frozenset({10, 6, 2}),
    "work":                            frozenset({10, 6, 2}),
    # Fame — 10H public status, 1H self-projection, 11H gains/recognition
    "fame":                            frozenset({10, 1, 11}),
    # Marriage — 7H partnership, 2H family extension, 4H domestic life
    "marriage":                        frozenset({7, 2, 4}),
    "relationship":                    frozenset({7, 5}),
    "relationships":                   frozenset({7, 5}),
    # Death — 8H longevity, 2H/7H marakas, 12H loss
    "death":                           frozenset({8, 2, 7, 12}),
    "death_cause_unspecified":         frozenset({8, 2, 7, 12}),
    "death_by_disease":                frozenset({6, 8, 12}),
    # Health — 6H disease, 1H body, 8H chronic
    "health":                          frozenset({6, 1, 8}),
    # Education — 5H intellect, 9H higher learning, 4H basic schooling
    "education":                       frozenset({5, 9, 4, 2}),
    # Finance — 2H wealth, 11H gains, 5H speculation
    "finance":                         frozenset({2, 11, 5}),
    # Legal — 6H litigation, 8H loss
    "legal":                           frozenset({6, 8}),
    # Personal/inner-life — 1H self, 5H mind
    "personal":                        frozenset({1, 5}),
    # Family — 4H mother/home, 2H kutumb
    "family":                          frozenset({4, 2, 11}),
}


_PLANETS_CANONICAL: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


# --------------------------------------------------------------------------- #
# Score computation                                                            #
# --------------------------------------------------------------------------- #

def _lord_relevance_score(
    lord: str,
    event_houses: frozenset[int],
    natal_row: dict,
) -> int:
    """0-3 score: +1 each for lord rules/occupies/aspects ANY event_house.

    A simple additive scoring; equal weight per channel pending the BN Rao
    research recommendation on relative weighting.
    """
    lord_l = lord.lower()
    score = 0
    ruled = natal_row.get(f"rules_{lord_l}", [])
    if ruled is not None and any(h in event_houses for h in ruled):
        score += 1
    occ = natal_row.get(f"occ_{lord_l}", -1)
    if occ in event_houses:
        score += 1
    aspected = natal_row.get(f"aspects_{lord_l}", [])
    if aspected is not None and any(h in event_houses for h in aspected):
        score += 1
    return score


def _annotate_corpus_with_scores(
    dasha_df: pd.DataFrame,
    natal_df: pd.DataFrame,
    event_class: str,
) -> pd.DataFrame:
    """Return dasha_df with a new 'md_lord_score' column for the event class."""
    event_houses = _EVENT_CLASS_HOUSES[event_class]
    natal_by_name = natal_df.set_index("name_norm")
    # Index for fast lookup
    natal_lookup = natal_by_name.to_dict("index")

    scores = np.zeros(len(dasha_df), dtype=int)
    names = dasha_df["name_norm"].to_numpy()
    lords = dasha_df["dasha_lord"].to_numpy()
    missing = 0
    for i in range(len(dasha_df)):
        row = natal_lookup.get(names[i])
        if row is None:
            missing += 1
            continue
        scores[i] = _lord_relevance_score(lords[i], event_houses, row)
    if missing:
        logger.warning("%d dasha rows had no matching natal_lord_houses row", missing)
    out = dasha_df.copy()
    out["md_lord_score"] = scores
    return out


# --------------------------------------------------------------------------- #
# Poisson rate-ratio + trend test                                              #
# --------------------------------------------------------------------------- #

def _poisson_rr(n_a: float, exp_a: float, n_b: float, exp_b: float):
    """RR=rate_b/rate_a, 95% log-normal CI, 1-sided p (positive)."""
    if min(n_a, n_b, exp_a, exp_b) <= 0:
        return tuple([float("nan")] * 5)
    rate_a = n_a / exp_a
    rate_b = n_b / exp_b
    rr = rate_b / rate_a
    log_rr = np.log(rr)
    se = np.sqrt(1.0 / n_a + 1.0 / n_b)
    z = log_rr / se
    ci_low = float(np.exp(log_rr - 1.96 * se))
    ci_high = float(np.exp(log_rr + 1.96 * se))
    p_one = float(1.0 - norm.cdf(z)) if z > 0 else 1.0
    return float(rr), float(z), ci_low, ci_high, p_one


def _exposure_trend_test(
    n_events: np.ndarray, exposure: np.ndarray, scores: np.ndarray,
) -> tuple[float, float]:
    """Poisson-regression z-test for monotonic trend in rate vs score.

    Returns (z, one-sided p for positive trend).
    """
    if n_events.sum() == 0 or exposure.sum() == 0:
        return float("nan"), 1.0
    rate_null = n_events.sum() / exposure.sum()
    expected = exposure * rate_null
    s_bar = (scores * expected).sum() / expected.sum()
    num = ((scores - s_bar) * n_events).sum()
    var = (((scores - s_bar) ** 2) * expected).sum()
    if var <= 0:
        return float("nan"), 1.0
    z = num / np.sqrt(var)
    return float(z), float(1.0 - norm.cdf(z))


def analyze_class(
    dasha_df: pd.DataFrame,
    natal_df: pd.DataFrame,
    event_class: str,
) -> dict:
    """Score every dasha row + run the Poisson rate-ladder test for one class."""
    label_col = f"event_{event_class}"
    if label_col not in dasha_df.columns:
        return {"error": f"missing {label_col}"}
    if dasha_df[label_col].sum() < 30:
        return {"error": f"too few events ({dasha_df[label_col].sum()})"}

    annotated = _annotate_corpus_with_scores(dasha_df, natal_df, event_class)
    duration_days = annotated["dasha_end_jd"] - annotated["dasha_start_jd"]

    rate_ladder: list[dict] = []
    for k in range(4):
        mask = (annotated["md_lord_score"] == k).to_numpy()
        n_w = int(mask.sum())
        n_e = int(annotated.loc[mask, label_col].sum())
        days = float(duration_days[mask].sum())
        rate_y = (n_e / days * 365.2425) if days > 0 else 0.0
        rate_ladder.append({
            "score": k,
            "n_windows": n_w,
            "n_events": n_e,
            "total_days": days,
            "rate_per_year": rate_y,
        })

    n_events_arr = np.array([r["n_events"] for r in rate_ladder], dtype=float)
    exp_arr = np.array([r["total_days"] for r in rate_ladder], dtype=float)
    scores_arr = np.array([0, 1, 2, 3], dtype=float)
    z_trend, p_trend = _exposure_trend_test(n_events_arr, exp_arr, scores_arr)

    # Conjunction: rate(3) / rate(0)
    rr, z_conj, ci_low, ci_high, p_conj = _poisson_rr(
        n_a=n_events_arr[0], exp_a=exp_arr[0],
        n_b=n_events_arr[3], exp_b=exp_arr[3],
    )
    # Any-channel: rate(≥1) / rate(0)
    n_any = float(n_events_arr[1:].sum())
    e_any = float(exp_arr[1:].sum())
    rr_any, z_any, ci_low_any, ci_high_any, p_any = _poisson_rr(
        n_a=n_events_arr[0], exp_a=exp_arr[0],
        n_b=n_any, exp_b=e_any,
    )

    return {
        "event_class": event_class,
        "event_houses": sorted(_EVENT_CLASS_HOUSES[event_class]),
        "rate_ladder": rate_ladder,
        "trend_z": z_trend,
        "trend_p_one_sided": p_trend,
        "rr_3_vs_0": rr,
        "rr_3_vs_0_ci_low": ci_low,
        "rr_3_vs_0_ci_high": ci_high,
        "rr_3_vs_0_p": p_conj,
        "rr_anyscore_vs_0": rr_any,
        "rr_anyscore_vs_0_ci_low": ci_low_any,
        "rr_anyscore_vs_0_ci_high": ci_high_any,
        "rr_anyscore_vs_0_p": p_any,
    }


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(
    dasha_path: Path,
    natal_path: Path,
    out_dir: Path,
    *,
    alpha: float = 0.01,
) -> dict:
    dasha_df = pd.read_parquet(dasha_path)
    natal_df = pd.read_parquet(natal_path)
    logger.info("dasha=%s shape=%s | natal=%s shape=%s",
                dasha_path, dasha_df.shape, natal_path, natal_df.shape)

    results: dict[str, dict] = {}
    for cls in _EVENT_CLASS_HOUSES:
        r = analyze_class(dasha_df, natal_df, cls)
        if "error" not in r:
            results[cls] = r

    n_classes = len(results)
    bonf = alpha / max(n_classes, 1)
    n_sig_p05 = sum(1 for r in results.values() if r["trend_p_one_sided"] < 0.05)
    n_sig_bonf = sum(1 for r in results.values() if r["trend_p_one_sided"] < bonf)
    joint_p = float(1.0 - binom.cdf(n_sig_p05 - 1, n_classes, 0.05)) if n_sig_p05 else 1.0

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stage_e_lord_house_score.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Stage E — Lord-House Relationship Score (Poisson rate ratios)",
        "",
        f"_Dasha corpus_: {dasha_path}",
        f"_Natal lord-houses_: {natal_path}",
        f"_Score per (person, MD lord)_: +1 each for rules / occupies / aspects ANY karaka-house of the event class. Range 0-3.",
        f"_Test_: exposure-adjusted Poisson trend (z) + rate ratio for score=3 vs 0 and score≥1 vs 0.",
        f"_Bonferroni α_: {alpha}/{n_classes} = {bonf:.4g}",
        "",
        "## Headline — rate ratio when classical lord-house chain activates the event-house",
        "",
        "| Class | Karaka houses | RR(score≥1 vs 0) [95% CI] | RR(3 vs 0) [95% CI] | Trend p |",
        "|---|---|---|---|---|",
    ]
    for cls, r in sorted(results.items(),
                         key=lambda kv: kv[1]["rr_anyscore_vs_0"]
                         if not np.isnan(kv[1]["rr_anyscore_vs_0"]) else -1,
                         reverse=True):
        houses = ", ".join(str(h) for h in r["event_houses"])
        marker = "**" if r["trend_p_one_sided"] < bonf else ""
        lines.append(
            f"| `{cls}` | {houses} | "
            f"**{r['rr_anyscore_vs_0']:.2f}** "
            f"({r['rr_anyscore_vs_0_ci_low']:.2f}-{r['rr_anyscore_vs_0_ci_high']:.2f}) | "
            f"{r['rr_3_vs_0']:.2f} "
            f"({r['rr_3_vs_0_ci_low']:.2f}-{r['rr_3_vs_0_ci_high']:.2f}) | "
            f"{marker}{r['trend_p_one_sided']:.4g}{marker} |"
        )

    lines.extend([
        "",
        f"**Joint significance**: {n_sig_p05}/{n_classes} classes with trend p<0.05, "
        f"{n_sig_bonf}/{n_classes} pass Bonferroni; joint binomial p={joint_p:.4g}",
        "",
        "## Rate ladder per class (events / Vedic year)",
        "",
    ])
    for cls, r in sorted(results.items()):
        lines.append(f"### `{cls}` (karaka houses {r['event_houses']})")
        lines.append("")
        lines.append("| score | n_windows | n_events | total_days | rate/year |")
        lines.append("|---|---|---|---|---|")
        for level in r["rate_ladder"]:
            lines.append(
                f"| {level['score']} | {level['n_windows']:,} | "
                f"{level['n_events']} | {level['total_days']:,.0f} | "
                f"**{level['rate_per_year']:.5f}** |"
            )
        lines.append(
            f"\nTrend z={r['trend_z']:.3f} p={r['trend_p_one_sided']:.4g}  "
            f"any-vs-0 RR={r['rr_anyscore_vs_0']:.2f}  3-vs-0 RR={r['rr_3_vs_0']:.2f}\n"
        )

    (out_dir / "stage_e_lord_house_score.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    return {
        "n_classes_tested": n_classes,
        "n_significant_p05": n_sig_p05,
        "n_significant_bonferroni": n_sig_bonf,
        "joint_binomial_p": joint_p,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_lord_house_score",
        description="Stage E — Poisson rate-ratio test with lord-house relevance score.",
    )
    parser.add_argument(
        "--dasha-corpus", type=Path,
        default=Path("app/medini/data/dasha_event_corpus.parquet"),
    )
    parser.add_argument(
        "--natal-lord-houses", type=Path,
        default=Path("app/medini/data/natal_lord_houses.parquet"),
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("data/ml_runs/fork_a_stage_e"),
    )
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    summary = run(
        args.dasha_corpus, args.natal_lord_houses, args.out, alpha=args.alpha,
    )
    print()
    print(f"=== Stage E — Lord-house relevance scoring ===")
    print(f"  classes tested: {summary['n_classes_tested']}")
    print(f"  trend p<0.05: {summary['n_significant_p05']}")
    print(f"  trend p<Bonferroni: {summary['n_significant_bonferroni']}")
    print(f"  joint binomial: {summary['joint_binomial_p']:.4g}")
    sorted_r = sorted(
        summary["results"].items(),
        key=lambda kv: kv[1].get("rr_anyscore_vs_0", -1),
        reverse=True,
    )
    print()
    print("Top classes by RR(score>=1 vs 0):")
    for cls, r in sorted_r:
        bonf_pass = "PASS" if r["trend_p_one_sided"] < (args.alpha / summary["n_classes_tested"]) else "fail"
        print(
            f"  [{bonf_pass}] {cls:<35} "
            f"RR(any/0)={r['rr_anyscore_vs_0']:.3f} "
            f"({r['rr_anyscore_vs_0_ci_low']:.2f}-{r['rr_anyscore_vs_0_ci_high']:.2f})  "
            f"trend_p={r['trend_p_one_sided']:.4g}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
