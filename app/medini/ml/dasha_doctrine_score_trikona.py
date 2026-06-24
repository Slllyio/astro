"""Stage F-4 — §8.3 trikona-sakshi (triple-witness) composite scoring.

Doctrine source (``docs/dasha_house_lord_doctrine.md`` §8.3):

    triwit_E = min(
        bhavesha_strength_for_E,
        karaka_strength_for_E,
        md_relevance_for_E,
    )

This is B.V. Raman's *triple-witness* rule: an event fires only when
ALL THREE classical witnesses agree. The MINIMUM across witnesses
captures the "weakest link" constraint:

  * bhavesha — the lord of the primary house for E (e.g. 10H lord for
    fame, 7H lord for marriage). Personal, chart-level: doesn't change
    across MD windows.
  * karaka — the natural significator (Sun/Jupiter for fame, Venus for
    marriage). Also chart-level — depends on each karaka's
    strength-modulated relevance in this chart.
  * md_lord — the current MD lord's strength-modulated relevance for E.
    Varies per window.

When any one witness is weak, the minimum collapses to that low value
even if the other two are strong. This is the strictest formulation
in the doctrine — predicted to be the highest-RR signal IF the
doctrine is empirically correct.

Implementation: per (person, event_class), pre-compute bhavesha + karaka
witness once; per (window), look up md_lord witness; take the min;
quantile-bin and Poisson-trend test as before.

Refines §6 (strength modifier) which already showed personal +
fame Bonferroni-pass. If §8.3 adds value on top, that's a strong
empirical confirmation of the triple-witness doctrine.
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
from app.medini.ml.dasha_doctrine_score_strength import dignity_strength

logger = logging.getLogger(__name__)


def _primary_house_for(event_class: str) -> int | None:
    """The house with the highest weight in the §3.2 map for E.

    Used as the "bhavesha-house" for the triple-witness rule. Returns
    None if the event_class has no entry (caller should handle).
    """
    hmap = _HOUSE_MAP.get(event_class)
    if not hmap:
        return None
    return max(hmap.items(), key=lambda kv: kv[1])[0]


def _bhavesha_planet(primary_house: int, natal_row: dict) -> str | None:
    """Find which planet rules ``primary_house`` in this chart.

    Falls back to None if no planet's `rules_<lord>` list contains the
    house — exotic edge case (chart with missing rulership data).
    """
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                   "Saturn", "Rahu", "Ketu"):
        ruled = natal_row.get(f"rules_{planet.lower()}", [])
        if ruled is not None and primary_house in ruled:
            return planet
    return None


def _strength_modulated_relevance(
    lord: str, event_class: str, natal_row: dict,
) -> float:
    """§5 relevance × §6 dignity-strength (the Stage F-3 winner)."""
    rel = doctrine_relevance(lord, event_class, natal_row)
    sign = natal_row.get(f"sign_{lord.lower()}")
    return rel * dignity_strength(lord, sign)


def _per_person_witnesses(
    natal_df: pd.DataFrame, event_class: str,
) -> dict[str, dict]:
    """Pre-compute bhavesha + karaka witnesses per person for one E.

    Returns ``{name_norm: {"bhavesha": <strength>, "karaka": <strength>,
    "per_lord": {<lord>: <strength>}}}``. The ``per_lord`` lookup is
    reused to compute the md_lord witness per window.
    """
    primary_h = _primary_house_for(event_class)
    karaka_set = _KARAKA_MAP.get(event_class, {})
    all_lords = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                 "Saturn", "Rahu", "Ketu")
    out: dict[str, dict] = {}
    for row in natal_df.itertuples(index=False):
        row_dict = row._asdict()
        name = row_dict.get("name_norm")
        if name is None:
            continue
        per_lord = {
            lord: _strength_modulated_relevance(lord, event_class, row_dict)
            for lord in all_lords
        }
        # Bhavesha = strength-modulated relevance of the primary-house lord.
        # If the house has no ruler in this chart, fall back to 0 (no witness).
        bh_planet = (
            _bhavesha_planet(primary_h, row_dict) if primary_h else None
        )
        bh_strength = per_lord.get(bh_planet, 0.0) if bh_planet else 0.0
        # Karaka = max over karaka-set of strength-modulated relevance.
        # Note: the karaka planet IS itself in the karaka_set, so its
        # _strength_modulated_relevance already includes the §5 KR term.
        kr_strength = max(
            (per_lord.get(planet, 0.0) for planet in karaka_set),
            default=0.0,
        )
        out[name] = {
            "bhavesha": bh_strength,
            "karaka": kr_strength,
            "per_lord": per_lord,
        }
    return out


def _annotate_trikona(
    dasha_df: pd.DataFrame,
    natal_df: pd.DataFrame,
    event_class: str,
) -> pd.DataFrame:
    """Add ``triwit_strength`` column (and intermediate witness columns).

    triwit = min(bhavesha_witness, karaka_witness, md_lord_witness).
    All three witnesses use the §5×§6 strength-modulated relevance.
    """
    witnesses = _per_person_witnesses(natal_df, event_class)
    names = dasha_df["name_norm"].to_numpy()
    md_lords = dasha_df["dasha_lord"].to_numpy()
    n = len(dasha_df)
    bh = np.zeros(n, dtype=float)
    kr = np.zeros(n, dtype=float)
    md = np.zeros(n, dtype=float)
    missing = 0
    for i in range(n):
        w = witnesses.get(names[i])
        if w is None:
            missing += 1
            continue
        bh[i] = w["bhavesha"]
        kr[i] = w["karaka"]
        md[i] = w["per_lord"].get(md_lords[i], 0.0)
    if missing:
        logger.warning("%d rows had no matching natal_lord_houses row", missing)
    out = dasha_df.copy()
    out["bhavesha_witness"] = bh
    out["karaka_witness"] = kr
    out["md_witness"] = md
    # Clip negatives — a single negative witness shouldn't drag triwit
    # below zero (degenerates rate-ratio binning).
    bh_c = np.clip(bh, 0.0, None)
    kr_c = np.clip(kr, 0.0, None)
    md_c = np.clip(md, 0.0, None)
    out["triwit_strength"] = np.minimum.reduce([bh_c, kr_c, md_c])
    return out


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
        return {"error": f"too few events ({int(dasha_df[label_col].sum())})"}

    annotated = _annotate_trikona(dasha_df, natal_df, event_class)
    annotated["duration_days"] = (
        annotated["dasha_end_jd"] - annotated["dasha_start_jd"]
    )

    try:
        annotated["bin"] = pd.qcut(
            annotated["triwit_strength"].rank(method="first"),
            q=n_bins, labels=False, duplicates="drop",
        )
    except ValueError:
        return {"error": "qcut failed (insufficient relevance variation)"}

    rate_ladder = []
    for bin_idx in range(n_bins):
        mask = annotated["bin"] == bin_idx
        n_w = int(mask.sum())
        n_e = int(annotated.loc[mask, label_col].sum())
        days = float(annotated.loc[mask, "duration_days"].sum())
        rate_y = (n_e / days * 365.2425) if days > 0 else 0.0
        rate_ladder.append({
            "bin": bin_idx, "n_windows": n_w, "n_events": n_e,
            "total_days": days, "rate_per_year": rate_y,
        })

    rr, z, lo, hi, p_top = _poisson_rr(
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
        "primary_house": _primary_house_for(event_class),
        "karakas": list(_KARAKA_MAP.get(event_class, {}).keys()),
        "rate_ladder": rate_ladder,
        "trend_z": float(z_trend),
        "trend_p_one_sided": p_trend,
        "rr_top_vs_bot": rr,
        "rr_top_vs_bot_ci_low": lo,
        "rr_top_vs_bot_ci_high": hi,
        "rr_top_vs_bot_p_one_sided": p_top,
        "zero_triwit_fraction": float(
            (annotated["triwit_strength"] == 0).mean()
        ),
    }


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
        logger.info("analyzing %s ...", cls)
        r = analyze_class(dasha_df, natal_df, cls, n_bins=n_bins)
        if "error" not in r:
            results[cls] = r
        else:
            logger.info("  skipped: %s", r["error"])

    n_classes = len(results)
    bonf = alpha / max(n_classes, 1)
    n_sig = sum(1 for r in results.values() if r["trend_p_one_sided"] < 0.05)
    n_sig_bonf = sum(1 for r in results.values() if r["trend_p_one_sided"] < bonf)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "trikona_sakshi.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Stage F-4 - Trikona-sakshi (triple-witness) composite (BPHS doctrine S8.3)",
        "",
        f"_Dasha corpus_: {dasha_path}",
        f"_Natal lord-houses_: {natal_path}",
        f"_Formula_: triwit = min(bhavesha_witness, karaka_witness, md_witness)",
        f"  each witness = doctrine_relevance(S5) * dignity_strength(S6).",
        f"_Bonferroni alpha_: {alpha}/{n_classes} = {bonf:.4g}",
        "",
        "## Headline - top-quintile vs bottom-quintile rate ratio (triwit)",
        "",
        "| Class | Primary H | Karakas | RR(top/bot) [95% CI] | trend p | %zero |",
        "|---|---|---|---|---|---|",
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
            f"| `{cls}` | {r['primary_house']} | "
            f"{', '.join(r['karakas'])} | "
            f"{rr_marker}{r['rr_top_vs_bot']:.2f}{rr_marker} "
            f"({r['rr_top_vs_bot_ci_low']:.2f}-{r['rr_top_vs_bot_ci_high']:.2f}) | "
            f"{trend_marker}{r['trend_p_one_sided']:.4g}{trend_marker} | "
            f"{r['zero_triwit_fraction']:.1%} |"
        )
    lines.extend([
        "",
        f"**trend p<0.05**: {n_sig}/{n_classes}; "
        f"**trend p<Bonferroni**: {n_sig_bonf}/{n_classes}",
        "",
    ])

    (out_dir / "trikona_sakshi.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return {
        "n_classes_tested": n_classes,
        "n_sig_p05": n_sig, "n_sig_bonf": n_sig_bonf,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_score_trikona",
        description="Stage F-4 - Trikona-sakshi triple-witness composite (S8.3).",
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
        default=Path("data/ml_runs/fork_a_doctrine_trikona"),
    )
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("--n-bins", type=int, default=5)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    summary = run(args.dasha_corpus, args.natal_lord_houses, args.out,
                  alpha=args.alpha, n_bins=args.n_bins)
    print()
    print("=== Stage F-4 - Trikona-sakshi (S8.3) ===")
    print(f"  classes tested: {summary['n_classes_tested']}")
    print(f"  trend p<0.05: {summary['n_sig_p05']}")
    print(f"  trend p<Bonferroni: {summary['n_sig_bonf']}")
    sorted_r = sorted(
        summary["results"].items(),
        key=lambda kv: kv[1]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["rr_top_vs_bot"]) else -1,
        reverse=True,
    )
    print()
    print("Top classes by RR (top/bot quintile):")
    for cls, r in sorted_r:
        bonf_pass = ("PASS" if r["trend_p_one_sided"] <
                     (args.alpha / summary["n_classes_tested"]) else "fail")
        print(
            f"  [{bonf_pass}] {cls:<35} "
            f"RR={r['rr_top_vs_bot']:.2f} "
            f"({r['rr_top_vs_bot_ci_low']:.2f}-{r['rr_top_vs_bot_ci_high']:.2f}) "
            f"trend_p={r['trend_p_one_sided']:.4g} "
            f"zero={r['zero_triwit_fraction']:.0%}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
