"""Stage F-3 — §6 strength modifier applied to MD-only Stage F baseline.

Doctrine source (``docs/dasha_house_lord_doctrine.md`` §6 + BPHS Ch.27.62):

  *"A planet with Shadbala greater than its required strength
  (apekshita-bala) gives results fully; less than apekshita-bala, the
  results are perverted, delayed, or denied."*

Full Shadbala (6-fold strength) requires computing sthana / dig / kala /
chesta / naisargika / drik balas — about 60 lines of math per planet per
person × 84k people. We're not running that here; instead, we use a
**dignity-based positional-strength proxy** that captures the strongest
single Shadbala component (Sthana bala) without the full 6-fold compute.

The proxy follows BPHS Ch.27 Sthana-bala intent:

    +1.00 — exalted
    +0.75 — own sign / moolatrikona
    +0.50 — friend's sign
    +0.40 — neutral
    +0.25 — enemy's sign
    +0.10 — debilitated

This is then multiplied into ``doctrine_relevance`` from §5 to produce
``strength_modulated_relevance(L, E, C) = relevance(L, E, C) *
dignity_strength(L, C)``. If the doctrine claim (BPHS 27.62) holds, the
modulated score should produce LARGER top-vs-bottom RRs than the bare §5
score because debilitated lords get penalized and exalted lords get
amplified.

Refines MD-only baseline (Stage F) rather than the §5.8 multi-layer
because Stage F-2 showed §5.8 didn't help on this corpus — adding
strength modulation on top of a working baseline is the cleaner ablation.
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

from app.core.dignity import dignity_state
from app.medini.ml.dasha_doctrine_score import (
    _HOUSE_MAP,
    _KARAKA_MAP,
    _poisson_rr,
    doctrine_relevance,
)

logger = logging.getLogger(__name__)


# Per-dignity strength multiplier (§6 proxy). Lock as constants so tests
# can pin the doctrine choice; tunable in future calibration work.
_DIGNITY_STRENGTH: dict[str, float] = {
    "exalted":      1.00,
    "moolatrikona": 0.75,
    "own":          0.75,
    "friend":       0.50,
    "neutral":      0.40,
    "enemy":        0.25,
    "debilitated":  0.10,
}
_PLANETS_FOR_DIGNITY = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
# Nodes (Rahu / Ketu) have no classical exaltation in BPHS Ch.7; some
# authors give them Taurus / Scorpio respectively. We treat them as
# 'neutral' across all signs by default — a fixed multiplier that doesn't
# differentiate node strength by sign. Future work can refine.
_NODE_DEFAULT_STRENGTH: float = 0.40


def dignity_strength(planet: str, sign: int | None) -> float:
    """Return the §6 dignity-based strength multiplier for a planet+sign.

    Returns ``_NODE_DEFAULT_STRENGTH`` for Rahu/Ketu (no classical
    exaltation) and ``neutral`` (0.40) for unknown/missing data so the
    pipeline never multiplies relevance by 0 unintentionally.
    """
    if planet in ("Rahu", "Ketu"):
        return _NODE_DEFAULT_STRENGTH
    if planet not in _PLANETS_FOR_DIGNITY:
        return _DIGNITY_STRENGTH["neutral"]
    if sign is None or not (1 <= int(sign) <= 12):
        return _DIGNITY_STRENGTH["neutral"]
    state = dignity_state(planet, int(sign))
    return _DIGNITY_STRENGTH.get(state, _DIGNITY_STRENGTH["neutral"])


# --------------------------------------------------------------------------- #
# Per-class annotation with strength-modulated relevance                       #
# --------------------------------------------------------------------------- #

def _build_relevance_and_strength_lookup(
    natal_df: pd.DataFrame, event_class: str,
) -> dict[str, dict[str, tuple[float, float]]]:
    """Per-(name, lord): pre-compute (relevance, strength) once.

    Returns ``{name_norm: {lord: (relevance, strength)}}`` so the row-loop
    over the 86k dasha corpus reduces to two dict lookups + a multiply.
    """
    lookup: dict[str, dict[str, tuple[float, float]]] = {}
    lords = _PLANETS_FOR_DIGNITY + ("Rahu", "Ketu")
    for row in natal_df.itertuples(index=False):
        row_dict = row._asdict()
        name = row_dict.get("name_norm")
        if name is None:
            continue
        per_lord: dict[str, tuple[float, float]] = {}
        for lord in lords:
            rel = doctrine_relevance(lord, event_class, row_dict)
            sign = row_dict.get(f"sign_{lord.lower()}")
            strength = dignity_strength(lord, sign)
            per_lord[lord] = (rel, strength)
        lookup[name] = per_lord
    return lookup


def _annotate_with_strength(
    dasha_df: pd.DataFrame,
    natal_df: pd.DataFrame,
    event_class: str,
) -> pd.DataFrame:
    """Add ``md_relevance`` (§5), ``md_strength`` (§6), and
    ``md_relevance_strong = md_relevance * md_strength`` columns."""
    lookup = _build_relevance_and_strength_lookup(natal_df, event_class)
    names = dasha_df["name_norm"].to_numpy()
    lords = dasha_df["dasha_lord"].to_numpy()
    n = len(dasha_df)
    rel = np.zeros(n, dtype=float)
    stre = np.zeros(n, dtype=float)
    missing = 0
    for i in range(n):
        per = lookup.get(names[i])
        if per is None:
            missing += 1
            continue
        rs = per.get(lords[i])
        if rs is None:
            continue
        rel[i], stre[i] = rs
    if missing:
        logger.warning("%d rows had no matching natal_lord_houses row", missing)
    out = dasha_df.copy()
    out["md_relevance"] = rel
    out["md_strength"] = stre
    # Modulated score — strength acts as a multiplier on the §5 relevance.
    # We DON'T clip rel here so negative relevance × strength still goes
    # negative (preserves the bare-§5 quantile direction). Clip to non-neg
    # would change the binning baseline.
    out["md_relevance_strong"] = rel * stre
    return out


# --------------------------------------------------------------------------- #
# Quintile-trend test (compares §5 vs §5+§6 on same dataframe)                 #
# --------------------------------------------------------------------------- #

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

    annotated = _annotate_with_strength(dasha_df, natal_df, event_class)
    annotated["duration_days"] = (
        annotated["dasha_end_jd"] - annotated["dasha_start_jd"]
    )

    def _quintile_rr(score_col: str) -> dict:
        a = annotated.copy()
        try:
            a["bin"] = pd.qcut(
                a[score_col].rank(method="first"),
                q=n_bins, labels=False, duplicates="drop",
            )
        except ValueError:
            return {"error": "qcut failed"}
        ladder = []
        for b in range(n_bins):
            mask = a["bin"] == b
            n_e = int(a.loc[mask, label_col].sum())
            days = float(a.loc[mask, "duration_days"].sum())
            ladder.append({
                "bin": b, "n_events": n_e, "total_days": days,
                "rate_per_year": (n_e / days * 365.2425) if days > 0 else 0.0,
            })
        rr, z, lo, hi, p = _poisson_rr(
            n_a=ladder[0]["n_events"], exp_a=ladder[0]["total_days"],
            n_b=ladder[-1]["n_events"], exp_b=ladder[-1]["total_days"],
        )
        # Trend test
        ne = np.array([r["n_events"] for r in ladder], dtype=float)
        ex = np.array([r["total_days"] for r in ladder], dtype=float)
        idx = np.arange(n_bins, dtype=float)
        rate_null = ne.sum() / max(ex.sum(), 1e-9)
        expected = ex * rate_null
        s_bar = (idx * expected).sum() / max(expected.sum(), 1e-9)
        num = ((idx - s_bar) * ne).sum()
        var = (((idx - s_bar) ** 2) * expected).sum()
        z_trend = num / np.sqrt(var) if var > 0 else float("nan")
        p_trend = float(1.0 - norm.cdf(z_trend)) if not np.isnan(z_trend) else 1.0
        return {
            "ladder": ladder,
            "rr_top_vs_bot": rr,
            "rr_ci_low": lo, "rr_ci_high": hi, "rr_p": p,
            "trend_z": float(z_trend), "trend_p": p_trend,
        }

    bare = _quintile_rr("md_relevance")
    strong = _quintile_rr("md_relevance_strong")
    return {
        "event_class": event_class,
        "bare_md": bare,
        "strength_modulated": strong,
    }


# --------------------------------------------------------------------------- #
# Driver — runs MD-only §5 and §5+§6 side by side                              #
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
        logger.info("analyzing %s ...", cls)
        r = analyze_class(dasha_df, natal_df, cls, n_bins=n_bins)
        if "error" not in r:
            results[cls] = r
        else:
            logger.info("  skipped: %s", r["error"])

    n_classes = len(results)
    bonf = alpha / max(n_classes, 1)

    n_sig_bare = sum(1 for r in results.values() if r["bare_md"]["trend_p"] < 0.05)
    n_sig_strong = sum(1 for r in results.values() if r["strength_modulated"]["trend_p"] < 0.05)
    n_bonf_bare = sum(1 for r in results.values() if r["bare_md"]["trend_p"] < bonf)
    n_bonf_strong = sum(1 for r in results.values() if r["strength_modulated"]["trend_p"] < bonf)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "strength_modulated.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Stage F-3 — §6 strength modifier vs bare §5 (MD-only)",
        "",
        f"_Dasha corpus_: {dasha_path}",
        f"_Natal lord-houses_: {natal_path}",
        f"_Formula_: md_relevance_strong = doctrine_relevance(§5) × dignity_strength(§6)",
        f"_Strength scheme_: exalted=1.0, own/moolatrikona=0.75, friend=0.50,",
        f"  neutral=0.40, enemy=0.25, debilitated=0.10. Nodes default 0.40.",
        f"_Bonferroni α_: {alpha}/{n_classes} = {bonf:.4g}",
        "",
        "## Headline — bare §5 vs §5×§6 (RR(top/bot), trend p)",
        "",
        "| Class | bare RR | bare trend p | strong RR | strong trend p | Δ RR |",
        "|---|---|---|---|---|---|",
    ]
    for cls, r in sorted(
        results.items(),
        key=lambda kv: kv[1]["strength_modulated"]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["strength_modulated"]["rr_top_vs_bot"]) else -1,
        reverse=True,
    ):
        bare = r["bare_md"]
        strong = r["strength_modulated"]
        bare_mark = "**" if bare["trend_p"] < bonf else ""
        strong_mark = "**" if strong["trend_p"] < bonf else ""
        delta = strong["rr_top_vs_bot"] - bare["rr_top_vs_bot"]
        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "="
        lines.append(
            f"| `{cls}` | {bare['rr_top_vs_bot']:.2f} | "
            f"{bare_mark}{bare['trend_p']:.4g}{bare_mark} | "
            f"**{strong['rr_top_vs_bot']:.2f}** | "
            f"{strong_mark}{strong['trend_p']:.4g}{strong_mark} | "
            f"{arrow}{delta:+.2f} |"
        )

    lines.extend([
        "",
        f"**Bare §5 trend-p<0.05**: {n_sig_bare}/{n_classes}; "
        f"trend-p<Bonferroni: {n_bonf_bare}/{n_classes}",
        f"**§5×§6 trend-p<0.05**: {n_sig_strong}/{n_classes}; "
        f"trend-p<Bonferroni: {n_bonf_strong}/{n_classes}",
        "",
    ])
    (out_dir / "strength_modulated.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    return {
        "n_classes_tested": n_classes,
        "n_sig_bare": n_sig_bare, "n_bonf_bare": n_bonf_bare,
        "n_sig_strong": n_sig_strong, "n_bonf_strong": n_bonf_strong,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_score_strength",
        description="Stage F-3 — §6 strength modifier vs bare §5 (MD-only).",
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
        default=Path("data/ml_runs/fork_a_doctrine_strength"),
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
    print("=== Stage F-3 — §6 strength × §5 relevance ===")
    print(f"  classes tested: {summary['n_classes_tested']}")
    print(f"  bare §5: trend<0.05 = {summary['n_sig_bare']}, "
          f"Bonferroni = {summary['n_bonf_bare']}")
    print(f"  §5×§6:   trend<0.05 = {summary['n_sig_strong']}, "
          f"Bonferroni = {summary['n_bonf_strong']}")
    print()
    print("Per-class RR comparison (sorted by S5*S6 RR):")
    print(f"  {'class':<35} {'bare-RR':>8} {'strong-RR':>10} {'diff':>7}")
    sorted_r = sorted(
        summary["results"].items(),
        key=lambda kv: kv[1]["strength_modulated"]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["strength_modulated"]["rr_top_vs_bot"]) else -1,
        reverse=True,
    )
    for cls, r in sorted_r:
        bare = r["bare_md"]["rr_top_vs_bot"]
        strong = r["strength_modulated"]["rr_top_vs_bot"]
        delta = strong - bare
        print(f"  {cls:<35} {bare:>8.2f} {strong:>10.2f} {delta:>+7.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
