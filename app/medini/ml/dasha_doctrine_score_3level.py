"""Stage F-2 — Doctrine §5.8 multi-layer relevance (MD × AD × PD).

Extends ``dasha_doctrine_score.py`` from MD-only to the full
MD/AD/PD chain. Per ``docs/dasha_house_lord_doctrine.md`` §5.8::

    relevance_full(MD, AD, PD, E, C) =
        relevance(MD, E, C) ^ 0.5
      * relevance(AD, E, C) ^ 0.3
      * relevance(PD, E, C) ^ 0.2

The exponents (0.5 / 0.3 / 0.2) sum to 1 and roughly match the
temporal-importance weighting in BPHS 47.10. The product encodes the
classical *both-witnesses-agree* rule (Phaladeepika 15.5-15.10): when any
single layer has zero relevance the product collapses, simulating the
classical "trigger must be present at every layer" requirement.

**Negative-relevance handling.** Single-layer relevance can be slightly
negative when the functional-modifier penalty (-0.25 for dusthana lord,
-0.5 for compound dusthana) is not offset by HR/KR. The doctrine treats
a negative-relevance lord as "actively obstructive" — for multiplicative
composition we clip to ``[0, +inf)`` so an obstructive lord drives the
product to 0 (the natural both-witnesses-agree breakdown) rather than
producing imaginary numbers from negative-base fractional exponents.

We reuse ``_HOUSE_MAP``, ``_KARAKA_MAP``, ``doctrine_relevance`` from
``dasha_doctrine_score`` so the §5 building blocks stay the single source
of truth.

Usage:
    python -m app.medini.ml.dasha_doctrine_score_3level
    python -m app.medini.ml.dasha_doctrine_score_3level \\
        --dasha-corpus app/medini/data/dasha_mdadpd_corpus.parquet \\
        --natal-lord-houses app/medini/data/natal_lord_houses.parquet \\
        --out data/ml_runs/fork_a_doctrine_3level
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

from app.medini.ml.dasha_doctrine_score import (
    _HOUSE_MAP,
    _KARAKA_MAP,
    _poisson_rr,
    doctrine_relevance,
)

logger = logging.getLogger(__name__)


# Layer-weight exponents per §5.8. Sum to 1.0 (BPHS 47.10 temporal weights).
W_MD: float = 0.5
W_AD: float = 0.3
W_PD: float = 0.2


# --------------------------------------------------------------------------- #
# Multi-layer relevance                                                        #
# --------------------------------------------------------------------------- #

def _build_lord_relevance_lookup(
    natal_df: pd.DataFrame, event_class: str,
) -> dict[str, dict[str, float]]:
    """Pre-compute per-(name, lord) doctrine relevance for one event class.

    Faster than calling ``doctrine_relevance`` 6.2M times: we compute once
    per (person, lord, event-class) and look up by name. With ~10k people
    and 9 lords, this is ~90k computations per class instead of millions.
    """
    lookup: dict[str, dict[str, float]] = {}
    lords = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    for natal_row in natal_df.itertuples(index=False):
        row_dict = natal_row._asdict()
        name = row_dict.get("name_norm")
        if name is None:
            continue
        per_lord = {
            lord: doctrine_relevance(lord, event_class, row_dict)
            for lord in lords
        }
        lookup[name] = per_lord
    return lookup


def multi_layer_relevance(
    md_rel: np.ndarray,
    ad_rel: np.ndarray,
    pd_rel: np.ndarray,
) -> np.ndarray:
    """§5.8 PRODUCT combiner: clip negatives to 0, then R_md^0.5 × R_ad^0.3 × R_pd^0.2.

    Negative-relevance lords collapse the product to 0 (both-witnesses-
    agree rule). Zero-relevance lords also collapse to 0.

    Empirical finding: this strict-AND interpretation produces 25-75% of
    rows with composite=0 (single uninvolved layer kills the product),
    which degenerates the bottom-quintile rate. Use ``additive_relevance``
    instead for classes where MD alone is enough to trigger (like fame).
    """
    md_clip = np.clip(md_rel, 0.0, None)
    ad_clip = np.clip(ad_rel, 0.0, None)
    pd_clip = np.clip(pd_rel, 0.0, None)
    return (np.power(md_clip, W_MD)
            * np.power(ad_clip, W_AD)
            * np.power(pd_clip, W_PD))


def additive_relevance(
    md_rel: np.ndarray,
    ad_rel: np.ndarray,
    pd_rel: np.ndarray,
) -> np.ndarray:
    """Additive variant: 0.5·R_md + 0.3·R_ad + 0.2·R_pd (clipped non-neg).

    Doctrinally this matches Phaladeepika 15's softer reading: "AD lord
    MODIFIES the MD result, doesn't trigger from scratch." A strong MD
    alone can drive the composite high; a strong AD+PD without MD support
    contributes modestly rather than nothing. This avoids the degenerate-
    bottom-bin artifact of the strict product combiner without losing
    MD-dominance (same coefficients).

    Negative relevance values (compound dusthana penalty) still clip to 0
    — an obstructive lord contributes nothing rather than canceling the
    MD layer.
    """
    md_clip = np.clip(md_rel, 0.0, None)
    ad_clip = np.clip(ad_rel, 0.0, None)
    pd_clip = np.clip(pd_rel, 0.0, None)
    return W_MD * md_clip + W_AD * ad_clip + W_PD * pd_clip


def _annotate_with_multi_relevance(
    mdadpd_df: pd.DataFrame,
    natal_df: pd.DataFrame,
    event_class: str,
) -> pd.DataFrame:
    """Add layer + composite columns for one event class.

    Adds:
      * ``md_relevance``, ``ad_relevance``, ``pd_relevance`` — per-layer
      * ``relevance_full`` — §5.8 product combiner
      * ``relevance_additive`` — softer additive combiner (recommended)
    """
    lookup = _build_lord_relevance_lookup(natal_df, event_class)

    def per_lord_vec(name_arr: np.ndarray, lord_arr: np.ndarray) -> np.ndarray:
        out = np.zeros(len(name_arr), dtype=float)
        for i in range(len(name_arr)):
            per = lookup.get(name_arr[i])
            if per is None:
                continue
            out[i] = per.get(lord_arr[i], 0.0)
        return out

    names = mdadpd_df["name_norm"].to_numpy()
    md_rel = per_lord_vec(names, mdadpd_df["md_lord"].to_numpy())
    ad_rel = per_lord_vec(names, mdadpd_df["ad_lord"].to_numpy())
    pd_rel = per_lord_vec(names, mdadpd_df["pd_lord"].to_numpy())

    out = mdadpd_df.copy()
    out["md_relevance"] = md_rel
    out["ad_relevance"] = ad_rel
    out["pd_relevance"] = pd_rel
    out["relevance_full"] = multi_layer_relevance(md_rel, ad_rel, pd_rel)
    out["relevance_additive"] = additive_relevance(md_rel, ad_rel, pd_rel)
    return out


# --------------------------------------------------------------------------- #
# Quintile-trend test (same shape as MD-only Stage F)                          #
# --------------------------------------------------------------------------- #

def analyze_class(
    mdadpd_df: pd.DataFrame,
    natal_df: pd.DataFrame,
    event_class: str,
    n_bins: int = 5,
    relevance_col: str = "relevance_full",
) -> dict:
    label_col = f"event_{event_class}"
    if label_col not in mdadpd_df.columns:
        return {"error": f"missing {label_col}"}
    if mdadpd_df[label_col].sum() < 30:
        return {"error": f"too few events ({int(mdadpd_df[label_col].sum())})"}

    annotated = _annotate_with_multi_relevance(mdadpd_df, natal_df, event_class)
    annotated["duration_days"] = (
        annotated["window_end_jd"] - annotated["window_start_jd"]
    )

    # Quantile-bin using rank-based tiebreaking. The 3-level relevance has
    # MANY zero-product rows (any layer with zero relevance → 0) so we
    # need rank-then-cut, not value-then-cut.
    try:
        annotated["bin"] = pd.qcut(
            annotated[relevance_col].rank(method="first"),
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
        min_rel = float(annotated.loc[mask, relevance_col].min()) if n_w else 0.0
        max_rel = float(annotated.loc[mask, relevance_col].max()) if n_w else 0.0
        rate_ladder.append({
            "bin": bin_idx,
            "min_relevance": min_rel,
            "max_relevance": max_rel,
            "n_windows": n_w,
            "n_events": n_e,
            "total_days": days,
            "rate_per_year": rate_y,
        })

    rr_top_vs_bot, z_top, ci_low, ci_high, p_top = _poisson_rr(
        n_a=rate_ladder[0]["n_events"], exp_a=rate_ladder[0]["total_days"],
        n_b=rate_ladder[-1]["n_events"], exp_b=rate_ladder[-1]["total_days"],
    )

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
        "median_relevance": float(annotated[relevance_col].median()),
        "mean_relevance": float(annotated[relevance_col].mean()),
        "zero_product_fraction": float(
            (annotated[relevance_col] == 0).mean()
        ),
    }


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(
    mdadpd_path: Path,
    natal_path: Path,
    out_dir: Path,
    *,
    alpha: float = 0.01,
    n_bins: int = 5,
    combiner: str = "additive",
) -> dict:
    mdadpd_df = pd.read_parquet(mdadpd_path)
    natal_df = pd.read_parquet(natal_path)
    logger.info("mdadpd=%s shape=%s | natal=%s shape=%s combiner=%s",
                mdadpd_path, mdadpd_df.shape, natal_path, natal_df.shape, combiner)

    rel_col = "relevance_full" if combiner == "product" else "relevance_additive"
    results: dict[str, dict] = {}
    for cls in _HOUSE_MAP:
        logger.info("analyzing %s ...", cls)
        r = analyze_class(mdadpd_df, natal_df, cls, n_bins=n_bins, relevance_col=rel_col)
        if "error" not in r:
            results[cls] = r
        else:
            logger.info("  skipped: %s", r["error"])

    n_classes = len(results)
    bonf = alpha / max(n_classes, 1)
    n_sig = sum(1 for r in results.values() if r["trend_p_one_sided"] < 0.05)
    n_sig_bonf = sum(1 for r in results.values() if r["trend_p_one_sided"] < bonf)
    joint_p = float(1.0 - binom.cdf(n_sig - 1, n_classes, 0.05)) if n_sig else 1.0

    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "product" if combiner == "product" else "additive"
    (out_dir / f"doctrine_score_3level_{suffix}.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    if combiner == "product":
        formula = f"R_md^{W_MD} * R_ad^{W_AD} * R_pd^{W_PD} (strict §5.8 AND)"
    else:
        formula = f"{W_MD}*R_md + {W_AD}*R_ad + {W_PD}*R_pd (additive MD-dominant)"

    lines = [
        f"# Stage F-2 — Doctrine §5.8 multi-layer relevance ({combiner})",
        "",
        f"_3-level dasha corpus_: {mdadpd_path}",
        f"_Natal lord-houses_: {natal_path}",
        f"_Combiner_: {combiner}",
        f"_Formula_: relevance = {formula}",
        f"  where each layer R uses the §5 doctrine: HR + KR + func_mod.",
        f"  Negatives clipped to 0.",
        f"_Test_: continuous composite binned into {n_bins} quantiles;",
        f"  exposure-adjusted Poisson trend + top-vs-bottom rate ratio.",
        f"_Bonferroni α_: {alpha}/{n_classes} = {bonf:.4g}",
        "",
        "## Headline — top-quintile vs bottom-quintile rate ratio (3-level)",
        "",
        "| Class | RR(top/bot) [95% CI] | trend p | top-bot p | %zero |",
        "|---|---|---|---|---|",
    ]
    for cls, r in sorted(
        results.items(),
        key=lambda kv: kv[1]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["rr_top_vs_bot"]) else -1,
        reverse=True,
    ):
        trend_marker = "**" if r["trend_p_one_sided"] < bonf else ""
        rr_marker = "**" if r["rr_top_vs_bot_p_one_sided"] < bonf else ""
        lines.append(
            f"| `{cls}` | "
            f"{rr_marker}{r['rr_top_vs_bot']:.2f}{rr_marker} "
            f"({r['rr_top_vs_bot_ci_low']:.2f}-{r['rr_top_vs_bot_ci_high']:.2f}) | "
            f"{trend_marker}{r['trend_p_one_sided']:.4g}{trend_marker} | "
            f"{r['rr_top_vs_bot_p_one_sided']:.4g} | "
            f"{r['zero_product_fraction']:.1%} |"
        )

    lines.extend([
        "",
        f"**Joint significance**: {n_sig}/{n_classes} classes with trend p<0.05, "
        f"{n_sig_bonf}/{n_classes} pass Bonferroni; joint binomial p={joint_p:.4g}",
        "",
    ])
    (out_dir / f"doctrine_score_3level_{suffix}.md").write_text(
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
        prog="python -m app.medini.ml.dasha_doctrine_score_3level",
        description=("Stage F-2 — Doctrine §5.8 multi-layer relevance scoring "
                     "(MD/AD/PD chain)."),
    )
    parser.add_argument(
        "--dasha-corpus", type=Path,
        default=Path("app/medini/data/dasha_mdadpd_corpus.parquet"),
    )
    parser.add_argument(
        "--natal-lord-houses", type=Path,
        default=Path("app/medini/data/natal_lord_houses.parquet"),
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("data/ml_runs/fork_a_doctrine_3level"),
    )
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("--n-bins", type=int, default=5)
    parser.add_argument(
        "--combiner",
        choices=["product", "additive"], default="additive",
        help="Layer-composition rule: 'product' is strict §5.8 AND, "
             "'additive' is softer MD-dominant sum (recommended).",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    summary = run(
        args.dasha_corpus, args.natal_lord_houses, args.out,
        alpha=args.alpha, n_bins=args.n_bins, combiner=args.combiner,
    )
    print()
    print(f"=== Stage F-2 — §5.8 multi-layer (MD × AD × PD) ===")
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
        bonf_pass = ("PASS" if r["trend_p_one_sided"] <
                     (args.alpha / summary["n_classes_tested"]) else "fail")
        print(
            f"  [{bonf_pass}] {cls:<35} "
            f"RR(top/bot)={r['rr_top_vs_bot']:.2f} "
            f"({r['rr_top_vs_bot_ci_low']:.2f}-{r['rr_top_vs_bot_ci_high']:.2f})  "
            f"trend_p={r['trend_p_one_sided']:.4g}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
