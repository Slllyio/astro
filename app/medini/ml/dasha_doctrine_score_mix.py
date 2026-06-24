"""Stage F-6 — Doctrine-informed per-class mix-and-match scorer.

Final production scorer for the Round-9 doctrine work. Each event class
gets the doctrine refinement that classical authors apply to THAT class
of prediction, NOT the empirically-best scorer (which would be
data-fishing).

## Per-class scoring assignment

| Class           | Scorer  | Doctrinal reason                                |
|---|---|---|
| `fame`          | §6      | BPHS 27.62: results "delivered fully" when     |
|                 |         | strength > apekshita. Exaltation is the        |
|                 |         | canonical fame-marker.                          |
| `personal`      | §6      | Self/health/individuality. Phaladeepika Ch.4   |
|                 |         | ties personal events to 1H-lord strength.       |
| `relationships` | §8.3    | Raman/Rao explicitly use triple-witness for     |
|                 |         | yoga manifestation. Partnerships are yoga-      |
|                 |         | shaped (Venus + 7H + lagna together).           |
| `marriage`      | §5      | Marriage timing is classically dasha+transit-   |
|                 |         | driven, not lord-strength-driven. §5 baseline. |
| `family`        | §5      | Default. Family signals are scattered (Moon,   |
|                 |         | Jupiter, 4H, 2H, 9H, 11H). No single mechanism. |
| `career`        | §5      | Default. Saturn/Sun/Mercury all karakas; broad. |
| `work`          | §5      | Default.                                        |
| `health`        | §5      | Default. Affliction reading more than strength. |
| `education`     | §5      | Default.                                        |
| `finance`       | §5      | Default.                                        |
| `legal`         | §5      | Default.                                        |
| `death_*`       | §5      | Default. Affliction-based.                      |

This locked mapping is the actual production output of the Round-9
doctrine work — it's what an astrologer-mimetic ML system would use
to score "is this event class likely to fire in this dasha window?".

## Why not just pick empirically-best per class?

That would be data-mining. The §6 / §8.3 / §5 assignment matches what
classical authors do — they use *strength* for honour/self-events, the
*triple-witness rule* for yoga manifestations (relationships, dharma),
and *bare lord attribution* for timing (marriage, death). The empirical
results align with these doctrinal mechanisms, which is the point:
*the doctrine works because it has internal structure that survives
out-of-sample testing.*

## What this delivers

- Per-event-class predicted score column in the dasha event corpus.
- Standard Poisson rate-ratio test on the same quintile-binning.
- Aggregate Bonferroni count.
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
from app.medini.ml.dasha_doctrine_score_trikona import (
    _bhavesha_planet,
    _primary_house_for,
)

logger = logging.getLogger(__name__)


# Per-class scorer assignment — see module docstring for rationale.
# Values: "s5" (bare §5), "s6" (§5 × dignity_strength),
#         "s8_3" (triple-witness: min over bhavesha/karaka/md).
_PER_CLASS_SCORER: dict[str, str] = {
    "fame":          "s6",
    "personal":      "s6",
    "relationships": "s8_3",
    # All others default to s5 (bare doctrine §5).
}


def _scorer_for(event_class: str) -> str:
    """Return the locked scorer assignment for ``event_class``."""
    return _PER_CLASS_SCORER.get(event_class, "s5")


# --------------------------------------------------------------------------- #
# Per-person, per-event-class score (the actual production output)             #
# --------------------------------------------------------------------------- #

def _s5_score(lord: str, event_class: str, natal_row: dict) -> float:
    return doctrine_relevance(lord, event_class, natal_row)


def _s6_score(lord: str, event_class: str, natal_row: dict) -> float:
    rel = doctrine_relevance(lord, event_class, natal_row)
    sign = natal_row.get(f"sign_{lord.lower()}")
    return rel * dignity_strength(lord, sign)


def _triwit_score(lord: str, event_class: str, natal_row: dict) -> float:
    """Trikona-sakshi: min(bhavesha_witness, karaka_witness, md_witness)."""
    primary_h = _primary_house_for(event_class)
    karaka_set = _KARAKA_MAP.get(event_class, {})
    # bhavesha witness
    bh_planet = _bhavesha_planet(primary_h, natal_row) if primary_h else None
    bh_witness = _s6_score(bh_planet, event_class, natal_row) if bh_planet else 0.0
    # karaka witness — max across the karaka set
    kr_witness = max(
        (_s6_score(p, event_class, natal_row) for p in karaka_set),
        default=0.0,
    )
    # md_lord witness — the actual MD lord's strength-modulated relevance
    md_witness = _s6_score(lord, event_class, natal_row)
    # Clip negatives, take min
    return float(min(max(bh_witness, 0.0),
                     max(kr_witness, 0.0),
                     max(md_witness, 0.0)))


def mix_score(lord: str, event_class: str, natal_row: dict) -> float:
    """Compute the per-class doctrine-informed score for one
    (lord, event_class, natal_row) triple.

    Dispatches on ``_PER_CLASS_SCORER`` — the locked classical mapping.
    """
    scorer = _scorer_for(event_class)
    if scorer == "s5":
        return _s5_score(lord, event_class, natal_row)
    if scorer == "s6":
        return _s6_score(lord, event_class, natal_row)
    if scorer == "s8_3":
        return _triwit_score(lord, event_class, natal_row)
    raise ValueError(f"unknown scorer {scorer!r}")


# --------------------------------------------------------------------------- #
# Annotation + analysis                                                        #
# --------------------------------------------------------------------------- #

def _build_lookup(natal_df: pd.DataFrame, event_class: str) -> dict:
    """Per-(name, lord) → mix-score; for s8_3 the per-lord variation is
    only md_witness — bh and kr are fixed per (name, class)."""
    lookup: dict[str, dict[str, float]] = {}
    lords = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
             "Saturn", "Rahu", "Ketu")
    for row in natal_df.itertuples(index=False):
        rd = row._asdict()
        name = rd.get("name_norm")
        if name is None:
            continue
        lookup[name] = {
            lord: mix_score(lord, event_class, rd) for lord in lords
        }
    return lookup


def _annotate_mix(
    dasha_df: pd.DataFrame, natal_df: pd.DataFrame, event_class: str,
) -> pd.DataFrame:
    lookup = _build_lookup(natal_df, event_class)
    names = dasha_df["name_norm"].to_numpy()
    lords = dasha_df["dasha_lord"].to_numpy()
    n = len(dasha_df)
    score = np.zeros(n, dtype=float)
    missing = 0
    for i in range(n):
        per = lookup.get(names[i])
        if per is None:
            missing += 1
            continue
        score[i] = per.get(lords[i], 0.0)
    if missing:
        logger.warning("%d rows had no matching natal_lord_houses row", missing)
    out = dasha_df.copy()
    out["mix_score"] = score
    out["scorer_used"] = _scorer_for(event_class)
    return out


def analyze_class(
    dasha_df: pd.DataFrame, natal_df: pd.DataFrame,
    event_class: str, n_bins: int = 5,
) -> dict:
    label_col = f"event_{event_class}"
    if label_col not in dasha_df.columns:
        return {"error": f"missing {label_col}"}
    if dasha_df[label_col].sum() < 30:
        return {"error": f"too few events ({int(dasha_df[label_col].sum())})"}

    annotated = _annotate_mix(dasha_df, natal_df, event_class)
    annotated["duration_days"] = (
        annotated["dasha_end_jd"] - annotated["dasha_start_jd"]
    )
    try:
        annotated["bin"] = pd.qcut(
            annotated["mix_score"].rank(method="first"),
            q=n_bins, labels=False, duplicates="drop",
        )
    except ValueError:
        return {"error": "qcut failed"}

    ladder = []
    for b in range(n_bins):
        mask = annotated["bin"] == b
        n_e = int(annotated.loc[mask, label_col].sum())
        days = float(annotated.loc[mask, "duration_days"].sum())
        ladder.append({
            "bin": b, "n_events": n_e, "total_days": days,
            "rate_per_year": (n_e / days * 365.2425) if days > 0 else 0.0,
        })
    rr, z, lo, hi, p_top = _poisson_rr(
        n_a=ladder[0]["n_events"], exp_a=ladder[0]["total_days"],
        n_b=ladder[-1]["n_events"], exp_b=ladder[-1]["total_days"],
    )
    n_events_arr = np.array([r["n_events"] for r in ladder], dtype=float)
    exp_arr = np.array([r["total_days"] for r in ladder], dtype=float)
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
        "scorer_used": _scorer_for(event_class),
        "ladder": ladder,
        "rr_top_vs_bot": rr,
        "rr_ci_low": lo, "rr_ci_high": hi, "rr_p": p_top,
        "trend_z": float(z_trend), "trend_p": p_trend,
    }


def run(
    dasha_path: Path, natal_path: Path, out_dir: Path,
    *, alpha: float = 0.01, n_bins: int = 5,
) -> dict:
    dasha_df = pd.read_parquet(dasha_path)
    natal_df = pd.read_parquet(natal_path)
    logger.info("dasha=%s shape=%s | natal=%s shape=%s",
                dasha_path, dasha_df.shape, natal_path, natal_df.shape)

    results: dict[str, dict] = {}
    for cls in _HOUSE_MAP:
        logger.info("analyzing %s (scorer=%s) ...", cls, _scorer_for(cls))
        r = analyze_class(dasha_df, natal_df, cls, n_bins=n_bins)
        if "error" not in r:
            results[cls] = r
        else:
            logger.info("  skipped: %s", r["error"])

    n_classes = len(results)
    bonf = alpha / max(n_classes, 1)
    n_sig = sum(1 for r in results.values() if r["trend_p"] < 0.05)
    n_bonf = sum(1 for r in results.values() if r["trend_p"] < bonf)
    joint_p = float(1.0 - binom.cdf(n_sig - 1, n_classes, 0.05)) if n_sig else 1.0

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "mix_score.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Stage F-6 - Doctrine-informed mix-and-match scoring",
        "",
        f"_Dasha corpus_: {dasha_path}",
        f"_Natal lord-houses_: {natal_path}",
        "_Per-class scorer assignment_:",
    ]
    for cls in sorted(_HOUSE_MAP):
        lines.append(f"  - `{cls}`: {_scorer_for(cls)}")
    lines.extend([
        "",
        f"_Bonferroni alpha_: {alpha}/{n_classes} = {bonf:.4g}",
        "",
        "## Per-class RR(top/bot) and trend p",
        "",
        "| Class | Scorer | RR(top/bot) [95% CI] | trend p |",
        "|---|---|---|---|",
    ])
    for cls, r in sorted(
        results.items(),
        key=lambda kv: kv[1]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["rr_top_vs_bot"]) else -1,
        reverse=True,
    ):
        trend_marker = "**" if r["trend_p"] < bonf else ""
        rr_marker = "**" if r["rr_p"] < bonf else ""
        lines.append(
            f"| `{cls}` | {r['scorer_used']} | "
            f"{rr_marker}{r['rr_top_vs_bot']:.2f}{rr_marker} "
            f"({r['rr_ci_low']:.2f}-{r['rr_ci_high']:.2f}) | "
            f"{trend_marker}{r['trend_p']:.4g}{trend_marker} |"
        )
    lines.extend([
        "",
        f"**Aggregate**: {n_sig}/{n_classes} trend p<0.05, "
        f"{n_bonf}/{n_classes} Bonferroni; joint binomial p={joint_p:.4g}",
        "",
    ])
    (out_dir / "mix_score.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    return {
        "n_classes_tested": n_classes,
        "n_sig_p05": n_sig, "n_sig_bonf": n_bonf,
        "joint_binomial_p": joint_p,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_score_mix",
        description="Stage F-6 - Doctrine-informed per-class mix scorer.",
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
        default=Path("data/ml_runs/fork_a_doctrine_mix"),
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
    print("=== Stage F-6 - Doctrine-informed mix-and-match scoring ===")
    print(f"  classes tested: {summary['n_classes_tested']}")
    print(f"  trend p<0.05: {summary['n_sig_p05']}")
    print(f"  trend p<Bonferroni: {summary['n_sig_bonf']}")
    print(f"  joint binomial: {summary['joint_binomial_p']:.4g}")
    sorted_r = sorted(
        summary["results"].items(),
        key=lambda kv: kv[1]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["rr_top_vs_bot"]) else -1,
        reverse=True,
    )
    print()
    print("Per-class result (sorted by RR):")
    for cls, r in sorted_r:
        bonf_pass = ("PASS" if r["trend_p"] <
                     (args.alpha / summary["n_classes_tested"]) else "fail")
        print(
            f"  [{bonf_pass}] {cls:<35} scorer={r['scorer_used']:<6} "
            f"RR={r['rr_top_vs_bot']:.2f} "
            f"({r['rr_ci_low']:.2f}-{r['rr_ci_high']:.2f}) "
            f"trend_p={r['trend_p']:.4g}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
