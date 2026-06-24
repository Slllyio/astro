"""Stage F — Doctrine-faithful dasha relevance scoring (BPHS Ch.46 + Raman + Rao).

Implements the formula from ``docs/dasha_house_lord_doctrine.md`` §5:

    chrel(L, h)       = 1.00 * is_lord + 0.75 * occupies + 0.50 * aspects_full
    HR(L, E, C)       = Σ (h, w) in house_map(E):  w * chrel(L, h, C)
    KR(L, E)          = max (planet, w) in karaka(E): w * 1[L == planet]
    func_mod(L, C)    = +0.5 yogakaraka / +0.25 trikona / 0 kendra / -0.25 dusthana
    relevance(L, E)   = HR + KR + func_mod

Replaces the prior provisional binary scoring (which equal-weighted all 3 channels
and broadened the house set without weights). The provisional version diluted the
bare-lord fame signal from RR=1.39 → 1.24; the doctrine-faithful version should
restore/improve the signal because:

1. House weights (1.0 / 0.5 / 0.25) put more weight on the karaka-house (10H for
   fame, 7H for marriage) rather than equal weight on all relevant houses.
2. Channel weights (1.0 / 0.75 / 0.5) put more weight on lordship, the strongest
   channel per BPHS Ch.46, rather than treating all three channels equally.
3. Karaka resonance adds the planet-level signal (Sun/Jupiter for fame; Venus for
   marriage etc.) ON TOP of the house signal — captures the natural significator.

Tests on the 86k-row MD-only dasha corpus (Stage A output) plus the per-person
natal-lord-houses parquet (Stage E.1 output).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import binom, norm

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Doctrine constants                                                           #
# --------------------------------------------------------------------------- #

# Channel weights per §5.1 — lordship strongest, occupancy strong-secondary,
# aspect tertiary. Tunable hyperparameters; default = doctrine-recommended.
W_LORDSHIP: float = 1.00
W_OCCUPANCY: float = 0.75
W_ASPECT_FULL: float = 0.50

# Per-event-class house weights per §3.2. Primary house = 1.0, secondary = 0.5,
# tertiary = 0.25. (We omit the gendered branches — e.g. marriage karaka =
# Venus for men / Jupiter for women — by including both as karakas.)
_HOUSE_MAP: dict[str, dict[int, float]] = {
    "marriage":     {7: 1.0, 2: 0.5, 11: 0.5, 4: 0.25, 5: 0.25},
    "relationship": {7: 1.0, 5: 0.5},
    "relationships": {7: 1.0, 5: 0.5},
    "career":       {10: 1.0, 6: 0.5, 2: 0.5, 11: 0.25, 5: 0.25},
    "work":         {10: 1.0, 6: 0.5, 2: 0.5},
    "fame":         {10: 1.0, 1: 0.5, 5: 0.5, 11: 0.25},
    "death":        {8: 1.0, 2: 0.5, 7: 0.5, 3: 0.25},
    "death_cause_unspecified": {8: 1.0, 2: 0.5, 7: 0.5, 3: 0.25},
    "death_by_disease": {6: 1.0, 8: 0.5, 12: 0.5, 1: 0.25, 11: 0.25},
    "health":       {6: 1.0, 8: 0.5, 12: 0.5, 1: 0.25, 11: 0.25},
    "education":    {4: 1.0, 5: 1.0, 9: 1.0, 2: 0.5, 3: 0.25},
    "finance":      {2: 1.0, 11: 1.0, 5: 0.5, 9: 0.5, 10: 0.25},
    "legal":        {6: 1.0, 12: 0.5, 8: 0.5},
    "personal":     {1: 1.0, 5: 0.5},
    "family":       {4: 1.0, 2: 0.5, 9: 0.5, 11: 0.25},
}

# Karaka mappings per §3.2 / §4. Each maps event_class -> {planet: weight}.
# Weights default to 1.0 (full karaka). Use max-aggregation in KR so a planet
# that's karaka for multiple aspects of one event class doesn't double-count.
_KARAKA_MAP: dict[str, dict[str, float]] = {
    "marriage":     {"Venus": 1.0, "Jupiter": 1.0},
    "relationship": {"Venus": 1.0},
    "relationships": {"Venus": 1.0},
    "career":       {"Sun": 1.0, "Saturn": 1.0, "Mercury": 1.0},
    "work":         {"Saturn": 1.0, "Mercury": 1.0},
    "fame":         {"Sun": 1.0, "Jupiter": 1.0},
    "death":        {"Saturn": 1.0},
    "death_cause_unspecified": {"Saturn": 1.0},
    "death_by_disease": {"Sun": 1.0, "Saturn": 1.0, "Mars": 1.0},
    "health":       {"Sun": 1.0, "Saturn": 1.0, "Mars": 1.0},
    "education":    {"Jupiter": 1.0, "Mercury": 1.0},
    "finance":      {"Jupiter": 1.0, "Venus": 1.0, "Mercury": 1.0},
    "legal":        {"Mars": 1.0, "Saturn": 1.0},
    "personal":     {"Moon": 1.0},
    "family":       {"Moon": 1.0, "Sun": 1.0, "Jupiter": 1.0},
}

# Functional benefic / malefic modifier per §5.5.
KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})
TRIKONA_HOUSES: frozenset[int] = frozenset({1, 5, 9})
DUSTHANA_HOUSES: frozenset[int] = frozenset({6, 8, 12})


# --------------------------------------------------------------------------- #
# Scoring helpers                                                              #
# --------------------------------------------------------------------------- #

def _channel_relation_score(
    lord_lower: str,
    house: int,
    natal_row: dict,
) -> float:
    """§5.1 channel-relation score for planet L w.r.t. house h.

    aspect_strength_normalised = 1.0 if the planet aspects the house (binary
    full-strength using our project's _DRISHTI_HOUSES table — all aspects in
    that table are full per BPHS 26.2 + Phaladeepika 4.3 per §2.2 of the
    doctrine). Partial generic aspects are future work.
    """
    s = 0.0
    ruled = natal_row.get(f"rules_{lord_lower}", [])
    if ruled is not None and house in ruled:
        s += W_LORDSHIP
    occ = natal_row.get(f"occ_{lord_lower}", -1)
    if occ == house:
        s += W_OCCUPANCY
    aspected = natal_row.get(f"aspects_{lord_lower}", [])
    if aspected is not None and house in aspected:
        s += W_ASPECT_FULL
    return s


def _house_resonance(
    lord: str,
    house_map: dict[int, float],
    natal_row: dict,
) -> float:
    """§5.2: HR = Σ (h, w) in house_map: w * chrel(L, h, C)."""
    lord_l = lord.lower()
    return sum(
        w * _channel_relation_score(lord_l, h, natal_row)
        for h, w in house_map.items()
    )


def _karaka_resonance(lord: str, karaka_map: dict[str, float]) -> float:
    """§5.3: KR = max (planet, w) in karaka_map: w * 1[L == planet]."""
    return max((w for p, w in karaka_map.items() if p == lord), default=0.0)


def _functional_modifier(lord: str, natal_row: dict) -> float:
    """§5.5 — yogakaraka / trikona / kendra / dusthana lordship bonus/penalty."""
    ruled = natal_row.get(f"rules_{lord.lower()}", [])
    if ruled is None:
        return 0.0
    ruled_set = set(int(h) for h in ruled)
    has_kendra = bool(ruled_set & KENDRA_HOUSES - {1})  # 1H counts as both
    has_trikona = bool(ruled_set & TRIKONA_HOUSES)
    has_pure_kendra = bool(ruled_set & (KENDRA_HOUSES - {1}))
    has_dusthana = bool(ruled_set & DUSTHANA_HOUSES)
    # Yogakaraka: rules both kendra (excluding 1) AND trikona (excluding 1)
    pure_trikona = ruled_set & (TRIKONA_HOUSES - {1})
    is_yogakaraka = bool(has_pure_kendra and pure_trikona)
    if is_yogakaraka:
        return 0.5
    if pure_trikona and not has_dusthana:
        return 0.25
    if has_dusthana:
        # Compound dusthana lord: penalty stacks
        if len(ruled_set & DUSTHANA_HOUSES) >= 2:
            return -0.5
        return -0.25
    return 0.0  # pure kendra non-1 (functional neutral)


def doctrine_relevance(
    lord: str,
    event_class: str,
    natal_row: dict,
) -> float:
    """§5.7 (without strength_modifier and veto): HR + KR + func_mod."""
    hmap = _HOUSE_MAP.get(event_class, {})
    kmap = _KARAKA_MAP.get(event_class, {})
    hr = _house_resonance(lord, hmap, natal_row)
    kr = _karaka_resonance(lord, kmap)
    fm = _functional_modifier(lord, natal_row)
    return hr + kr + fm


# --------------------------------------------------------------------------- #
# Per-class annotation                                                         #
# --------------------------------------------------------------------------- #

def _annotate_with_relevance(
    dasha_df: pd.DataFrame,
    natal_df: pd.DataFrame,
    event_class: str,
) -> pd.DataFrame:
    """Add `md_relevance` (continuous) and `md_relevance_quartile` columns."""
    natal_lookup = natal_df.set_index("name_norm").to_dict("index")
    names = dasha_df["name_norm"].to_numpy()
    lords = dasha_df["dasha_lord"].to_numpy()
    relevance = np.zeros(len(dasha_df), dtype=float)
    missing = 0
    for i in range(len(dasha_df)):
        row = natal_lookup.get(names[i])
        if row is None:
            missing += 1
            continue
        relevance[i] = doctrine_relevance(lords[i], event_class, row)
    if missing:
        logger.warning("%d dasha rows had no matching natal_lord_houses row", missing)
    out = dasha_df.copy()
    out["md_relevance"] = relevance
    return out


# --------------------------------------------------------------------------- #
# Poisson rate-ratio tests on doctrine-relevance quintiles                    #
# --------------------------------------------------------------------------- #

def _poisson_rr(n_a: float, exp_a: float, n_b: float, exp_b: float):
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


def analyze_class(
    dasha_df: pd.DataFrame,
    natal_df: pd.DataFrame,
    event_class: str,
    n_bins: int = 5,
) -> dict:
    label_col = f"event_{event_class}"
    if label_col not in dasha_df.columns:
        return {"error": f"missing {label_col}"}
    if dasha_df[label_col].sum() < 30:
        return {"error": f"too few events ({dasha_df[label_col].sum()})"}

    annotated = _annotate_with_relevance(dasha_df, natal_df, event_class)
    annotated["duration_days"] = annotated["dasha_end_jd"] - annotated["dasha_start_jd"]

    # Quantile-bin the continuous relevance score into n_bins buckets.
    # Use rank-based quantiles to handle ties cleanly.
    try:
        annotated["bin"] = pd.qcut(
            annotated["md_relevance"].rank(method="first"),
            q=n_bins, labels=False, duplicates="drop",
        )
    except ValueError:
        return {"error": "qcut failed (insufficient relevance variation)"}

    rate_ladder = []
    for bin_idx in range(n_bins):
        mask = (annotated["bin"] == bin_idx)
        n_w = int(mask.sum())
        n_e = int(annotated.loc[mask, label_col].sum())
        days = float(annotated.loc[mask, "duration_days"].sum())
        rate_y = (n_e / days * 365.2425) if days > 0 else 0.0
        min_rel = float(annotated.loc[mask, "md_relevance"].min()) if n_w else 0.0
        max_rel = float(annotated.loc[mask, "md_relevance"].max()) if n_w else 0.0
        rate_ladder.append({
            "bin": bin_idx,
            "min_relevance": min_rel,
            "max_relevance": max_rel,
            "n_windows": n_w,
            "n_events": n_e,
            "total_days": days,
            "rate_per_year": rate_y,
        })

    # Top vs bottom quintile RR
    rr_top_vs_bot, z_top, ci_low, ci_high, p_top = _poisson_rr(
        n_a=rate_ladder[0]["n_events"], exp_a=rate_ladder[0]["total_days"],
        n_b=rate_ladder[-1]["n_events"], exp_b=rate_ladder[-1]["total_days"],
    )

    # Exposure-adjusted Poisson trend test over the quantile bins
    n_events_arr = np.array([r["n_events"] for r in rate_ladder], dtype=float)
    exp_arr = np.array([r["total_days"] for r in rate_ladder], dtype=float)
    bin_idx_arr = np.arange(n_bins, dtype=float)
    rate_null = n_events_arr.sum() / max(exp_arr.sum(), 1e-9)
    expected = exp_arr * rate_null
    s_bar = (bin_idx_arr * expected).sum() / max(expected.sum(), 1e-9)
    num = ((bin_idx_arr - s_bar) * n_events_arr).sum()
    var = (((bin_idx_arr - s_bar) ** 2) * expected).sum()
    z_trend = num / np.sqrt(var) if var > 0 else float("nan")
    p_trend = float(1.0 - norm.cdf(z_trend)) if not np.isnan(z_trend) else 1.0

    return {
        "event_class": event_class,
        "house_map": _HOUSE_MAP.get(event_class),
        "karaka_map": _KARAKA_MAP.get(event_class),
        "rate_ladder": rate_ladder,
        "trend_z": float(z_trend),
        "trend_p_one_sided": p_trend,
        "rr_top_vs_bot": rr_top_vs_bot,
        "rr_top_vs_bot_ci_low": ci_low,
        "rr_top_vs_bot_ci_high": ci_high,
        "rr_top_vs_bot_p_one_sided": p_top,
        "median_relevance": float(annotated["md_relevance"].median()),
        "mean_relevance": float(annotated["md_relevance"].mean()),
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
    n_bins: int = 5,
) -> dict:
    dasha_df = pd.read_parquet(dasha_path)
    natal_df = pd.read_parquet(natal_path)
    logger.info("dasha=%s shape=%s | natal=%s shape=%s",
                dasha_path, dasha_df.shape, natal_path, natal_df.shape)

    results: dict[str, dict] = {}
    for cls in _HOUSE_MAP:
        r = analyze_class(dasha_df, natal_df, cls, n_bins=n_bins)
        if "error" not in r:
            results[cls] = r

    n_classes = len(results)
    bonf = alpha / max(n_classes, 1)
    n_sig = sum(1 for r in results.values() if r["trend_p_one_sided"] < 0.05)
    n_sig_bonf = sum(1 for r in results.values() if r["trend_p_one_sided"] < bonf)
    joint_p = float(1.0 - binom.cdf(n_sig - 1, n_classes, 0.05)) if n_sig else 1.0

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "doctrine_score.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Stage F — Doctrine-Faithful Dasha Relevance (BPHS Ch.46 + Raman)",
        "",
        f"_Dasha corpus_: {dasha_path}",
        f"_Natal lord-houses_: {natal_path}",
        f"_Formula_: relevance(L, E) = HR(L, E) + KR(L, E) + func_mod(L) per §5 of",
        f"  `docs/dasha_house_lord_doctrine.md`.",
        f"  HR = Σ w_h × (1.0 × is_lord + 0.75 × occupies + 0.50 × aspects_full)",
        f"  House weights: 1.0 primary, 0.5 secondary, 0.25 tertiary (§3.2).",
        f"  KR = max (planet, w) in karaka_set : w × 1[L == karaka]",
        f"_Test_: continuous relevance score binned into {n_bins} quantiles;",
        f"  exposure-adjusted Poisson trend + top-vs-bottom rate ratio.",
        f"_Bonferroni α_: {alpha}/{n_classes} = {bonf:.4g}",
        "",
        "## Headline — top-quintile vs bottom-quintile rate ratio",
        "",
        "| Class | Houses | Karakas | RR(top/bot) [95% CI] | trend p | top-bot p |",
        "|---|---|---|---|---|---|",
    ]
    for cls, r in sorted(
        results.items(),
        key=lambda kv: kv[1]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["rr_top_vs_bot"]) else -1,
        reverse=True,
    ):
        hmap = ", ".join(f"{h}:{w:.2g}" for h, w in r["house_map"].items())
        kmap = ", ".join(r["karaka_map"].keys())
        trend_marker = "**" if r["trend_p_one_sided"] < bonf else ""
        rr_marker = "**" if r["rr_top_vs_bot_p_one_sided"] < bonf else ""
        lines.append(
            f"| `{cls}` | {hmap} | {kmap} | "
            f"{rr_marker}{r['rr_top_vs_bot']:.2f}{rr_marker} "
            f"({r['rr_top_vs_bot_ci_low']:.2f}-{r['rr_top_vs_bot_ci_high']:.2f}) | "
            f"{trend_marker}{r['trend_p_one_sided']:.4g}{trend_marker} | "
            f"{r['rr_top_vs_bot_p_one_sided']:.4g} |"
        )

    lines.extend([
        "",
        f"**Joint significance**: {n_sig}/{n_classes} classes with trend p<0.05, "
        f"{n_sig_bonf}/{n_classes} pass Bonferroni; joint binomial p={joint_p:.4g}",
        "",
        "## Rate ladder per class (continuous relevance, quantile-binned)",
        "",
    ])
    for cls, r in sorted(results.items()):
        lines.append(f"### `{cls}` — houses {r['house_map']}, karakas {list(r['karaka_map'])}")
        lines.append(f"\nMedian relevance: {r['median_relevance']:.3f}; mean: {r['mean_relevance']:.3f}\n")
        lines.append("| bin | relevance range | n_windows | n_events | total_days | rate/year |")
        lines.append("|---|---|---|---|---|---|")
        for b in r["rate_ladder"]:
            lines.append(
                f"| {b['bin']} | [{b['min_relevance']:.2f}, {b['max_relevance']:.2f}] | "
                f"{b['n_windows']:,} | {b['n_events']} | {b['total_days']:,.0f} | "
                f"**{b['rate_per_year']:.5f}** |"
            )
        lines.append(
            f"\nTrend z={r['trend_z']:.3f} p={r['trend_p_one_sided']:.4g}  "
            f"RR(top/bot)={r['rr_top_vs_bot']:.2f} "
            f"({r['rr_top_vs_bot_ci_low']:.2f}-{r['rr_top_vs_bot_ci_high']:.2f})\n"
        )

    (out_dir / "doctrine_score.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    return {
        "n_classes_tested": n_classes,
        "n_significant_p05": n_sig,
        "n_significant_bonferroni": n_sig_bonf,
        "joint_binomial_p": joint_p,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_score",
        description="Stage F — Doctrine-faithful (BPHS Ch.46) dasha relevance scoring.",
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
        default=Path("data/ml_runs/fork_a_doctrine"),
    )
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("--n-bins", type=int, default=5)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    summary = run(
        args.dasha_corpus, args.natal_lord_houses, args.out,
        alpha=args.alpha, n_bins=args.n_bins,
    )
    print()
    print(f"=== Stage F — Doctrine-faithful relevance scoring ===")
    print(f"  classes tested: {summary['n_classes_tested']}")
    print(f"  trend p<0.05: {summary['n_significant_p05']}")
    print(f"  trend p<Bonferroni: {summary['n_significant_bonferroni']}")
    print(f"  joint binomial: {summary['joint_binomial_p']:.4g}")
    sorted_r = sorted(
        summary["results"].items(),
        key=lambda kv: kv[1]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["rr_top_vs_bot"]) else -1,
        reverse=True,
    )
    print()
    print("Top classes by top-vs-bot quintile RR:")
    for cls, r in sorted_r:
        bonf_pass = "PASS" if r["trend_p_one_sided"] < (args.alpha / summary["n_classes_tested"]) else "fail"
        print(
            f"  [{bonf_pass}] {cls:<35} "
            f"RR(top/bot)={r['rr_top_vs_bot']:.2f} "
            f"({r['rr_top_vs_bot_ci_low']:.2f}-{r['rr_top_vs_bot_ci_high']:.2f})  "
            f"trend_p={r['trend_p_one_sided']:.4g}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
