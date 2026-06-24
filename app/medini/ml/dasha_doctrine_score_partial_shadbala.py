"""Stage F-5 — Partial-Shadbala strength modifier (4 of 6 balas).

Builds on Stage F-3 (§6 strength modifier) by replacing the dignity-only
proxy with a **partial Shadbala** computed from the natal data we have
on disk:

  1. **Sthana-bala proxy** — dignity_state lookup (6-step ladder).
     The pure Sthana-bala from BPHS Ch.27 has 5 sub-components and
     requires planet longitude (we don't have it cached); the dignity
     proxy captures the strongest single piece (uchcha + own/exalt).
  2. **Dig-bala** — directional strength per BPHS 27.36. Uses the
     planet's natal house, which we have. Range 0-60 virupa.
  3. **Naisargika-bala** — fixed natural-strength lookup. BPHS 27.38.
     Range fixed per planet, e.g. Sun=60, Moon=51.4, ..., Saturn=8.6.
  4. **Drik-bala** — aspectual strength net of benefic minus malefic
     aspects from other planets. BPHS 27.38 simplified. Uses the
     ``sign_<planet>`` columns we have. Range typically ±15-30 virupa.

NOT included (require data we don't have cached):
  - Pure Sthana-bala (needs longitude for continuous uchcha + D9 sign
    for saptavargaja)
  - Kala/Paksha bala (needs Sun-Moon angle)
  - Cheshta bala (needs retrograde flag)

The partial Shadbala is summed in virupa and normalized to [0, ~1.2]
by dividing by 240 (roughly the 4-component ceiling). This is then
multiplied into ``doctrine_relevance(§5)`` to produce the strength-
modulated score, same shape as Stage F-3 / §6.

If the empirical signal improves over Stage F-3 (which used dignity-
proxy alone), that's evidence the additional Shadbala components
carry actual signal. If it doesn't, the dignity proxy was already
capturing most of the per-class predictability — a useful finding
even when negative.
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
from app.core.shadbala import dig_bala, drik_bala, naisargika_bala
from app.medini.ml.dasha_doctrine_score import (
    _HOUSE_MAP,
    _poisson_rr,
    doctrine_relevance,
)

logger = logging.getLogger(__name__)


# Same dignity ladder as §6, expressed in virupa scale (multiplied by 60
# so it sums cleanly with the other balas which are in virupa).
_DIGNITY_VIRUPA: dict[str, float] = {
    "exalted":      60.0,
    "moolatrikona": 45.0,
    "own":          45.0,
    "friend":       30.0,
    "neutral":      24.0,
    "enemy":        15.0,
    "debilitated":   6.0,
}
_PLANETS_FOR_SHADBALA = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)
# Nodes get no Dig/Drik bala per classical doctrine; we give them a
# baseline Sthana (neutral) so they're not zero in the multiplier.
_NODE_VIRUPA: float = 24.0

# Approximate sum-ceiling for our 4-component partial Shadbala
# (sthana_proxy_max=60 + dig_max=60 + naisargika_max=60 + drik_max~30)
# Used only as a normalization scale so the multiplier sits in ~[0, 1.2].
_PARTIAL_SHADBALA_SCALE: float = 240.0


def _chart_signs_dict(natal_row: dict) -> dict[str, dict]:
    """Build the {planet: {"sign": int}} dict that ``drik_bala`` expects."""
    return {
        planet: {"sign": int(natal_row.get(f"sign_{planet.lower()}", 0))}
        for planet in (*_PLANETS_FOR_SHADBALA, "Rahu", "Ketu")
        if natal_row.get(f"sign_{planet.lower()}")
    }


def partial_shadbala_virupa(
    planet: str, natal_row: dict,
) -> float:
    """Sum of 4 Shadbala components computable from the cached natal data.

    Returns total in virupa. Negative-drik contributions are allowed
    (a planet under heavy malefic-aspect should be weaker than naisargika
    alone would suggest).
    """
    if planet in ("Rahu", "Ketu"):
        return _NODE_VIRUPA

    sign = natal_row.get(f"sign_{planet.lower()}")
    if not isinstance(sign, (int, np.integer)) or not (1 <= int(sign) <= 12):
        return _NODE_VIRUPA  # neutral fallback

    # 1. Sthana proxy via dignity
    dig_state = dignity_state(planet, int(sign))
    sthana = _DIGNITY_VIRUPA.get(dig_state, _DIGNITY_VIRUPA["neutral"])

    # 2. Dig bala (returns 0 for nodes; only called for main planets here)
    house = natal_row.get(f"occ_{planet.lower()}", -1)
    dig = (
        dig_bala(planet, int(house))
        if isinstance(house, (int, np.integer)) and 1 <= int(house) <= 12
        else 0.0
    )

    # 3. Naisargika bala (fixed per planet)
    nais = naisargika_bala(planet)

    # 4. Drik bala — needs the chart dict of signs
    chart = _chart_signs_dict(natal_row)
    try:
        drik = drik_bala(planet, chart)
    except ValueError:
        drik = 0.0  # safety: ignore drik on malformed input

    return sthana + dig + nais + drik


def partial_shadbala_strength(planet: str, natal_row: dict) -> float:
    """Normalized partial-Shadbala multiplier in roughly [0, 1.2].

    This is the strength factor that multiplies ``doctrine_relevance(§5)``
    in Stage F-5. Clipped to [0.05, 1.5] so a degenerate row (drik very
    negative) doesn't kill the relevance product entirely.
    """
    virupa = partial_shadbala_virupa(planet, natal_row)
    raw = virupa / _PARTIAL_SHADBALA_SCALE
    # Floor so a very-low-shadbala lord doesn't completely zero out the
    # §5 relevance score for binning.
    return float(np.clip(raw, 0.05, 1.5))


# --------------------------------------------------------------------------- #
# Per-class annotation                                                         #
# --------------------------------------------------------------------------- #

def _build_relevance_and_shadbala_lookup(
    natal_df: pd.DataFrame, event_class: str,
) -> dict[str, dict[str, tuple[float, float]]]:
    """Per-(name, lord) → (§5_relevance, partial_shadbala_strength)."""
    lookup: dict[str, dict[str, tuple[float, float]]] = {}
    lords = (*_PLANETS_FOR_SHADBALA, "Rahu", "Ketu")
    for row in natal_df.itertuples(index=False):
        row_dict = row._asdict()
        name = row_dict.get("name_norm")
        if name is None:
            continue
        per_lord = {
            lord: (
                doctrine_relevance(lord, event_class, row_dict),
                partial_shadbala_strength(lord, row_dict),
            )
            for lord in lords
        }
        lookup[name] = per_lord
    return lookup


def _annotate_with_shadbala(
    dasha_df: pd.DataFrame,
    natal_df: pd.DataFrame,
    event_class: str,
) -> pd.DataFrame:
    """Adds ``md_relevance``, ``md_shadbala`` (multiplier), and
    ``md_relevance_shadbala`` (product) columns."""
    lookup = _build_relevance_and_shadbala_lookup(natal_df, event_class)
    names = dasha_df["name_norm"].to_numpy()
    lords = dasha_df["dasha_lord"].to_numpy()
    n = len(dasha_df)
    rel = np.zeros(n, dtype=float)
    sb = np.zeros(n, dtype=float)
    missing = 0
    for i in range(n):
        per = lookup.get(names[i])
        if per is None:
            missing += 1
            continue
        rs = per.get(lords[i])
        if rs is None:
            continue
        rel[i], sb[i] = rs
    if missing:
        logger.warning("%d rows had no matching natal_lord_houses row", missing)
    out = dasha_df.copy()
    out["md_relevance"] = rel
    out["md_shadbala"] = sb
    out["md_relevance_shadbala"] = rel * sb
    return out


# --------------------------------------------------------------------------- #
# Quintile-trend test                                                          #
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

    annotated = _annotate_with_shadbala(dasha_df, natal_df, event_class)
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
    shadbala = _quintile_rr("md_relevance_shadbala")
    return {
        "event_class": event_class,
        "bare_md": bare,
        "shadbala_modulated": shadbala,
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
    n_sig_bare = sum(1 for r in results.values() if r["bare_md"]["trend_p"] < 0.05)
    n_sig_sb = sum(1 for r in results.values() if r["shadbala_modulated"]["trend_p"] < 0.05)
    n_bonf_bare = sum(1 for r in results.values() if r["bare_md"]["trend_p"] < bonf)
    n_bonf_sb = sum(1 for r in results.values() if r["shadbala_modulated"]["trend_p"] < bonf)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "partial_shadbala.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Stage F-5 - Partial-Shadbala strength modifier (4 of 6 balas)",
        "",
        f"_Dasha corpus_: {dasha_path}",
        f"_Natal lord-houses_: {natal_path}",
        f"_Formula_: md_relevance_shadbala = doctrine_relevance(S5) * partial_shadbala_strength",
        f"_Components_: dignity (sthana proxy) + dig + naisargika + drik, virupa-summed",
        f"_Scale_: /240 (4-component max ceiling), clipped to [0.05, 1.5]",
        f"_Bonferroni alpha_: {alpha}/{n_classes} = {bonf:.4g}",
        "",
        "## Headline - bare S5 vs S5 x partial-shadbala",
        "",
        "| Class | bare RR | bare trend p | shadbala RR | shadbala trend p | diff |",
        "|---|---|---|---|---|---|",
    ]
    for cls, r in sorted(
        results.items(),
        key=lambda kv: kv[1]["shadbala_modulated"]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["shadbala_modulated"]["rr_top_vs_bot"]) else -1,
        reverse=True,
    ):
        bare = r["bare_md"]
        sb = r["shadbala_modulated"]
        bare_mark = "**" if bare["trend_p"] < bonf else ""
        sb_mark = "**" if sb["trend_p"] < bonf else ""
        delta = sb["rr_top_vs_bot"] - bare["rr_top_vs_bot"]
        lines.append(
            f"| `{cls}` | {bare['rr_top_vs_bot']:.2f} | "
            f"{bare_mark}{bare['trend_p']:.4g}{bare_mark} | "
            f"**{sb['rr_top_vs_bot']:.2f}** | "
            f"{sb_mark}{sb['trend_p']:.4g}{sb_mark} | "
            f"{delta:+.2f} |"
        )
    lines.extend([
        "",
        f"**Bare S5 trend-p<0.05**: {n_sig_bare}/{n_classes}; "
        f"Bonferroni: {n_bonf_bare}/{n_classes}",
        f"**S5 x partial-shadbala**: trend-p<0.05 = {n_sig_sb}/{n_classes}; "
        f"Bonferroni: {n_bonf_sb}/{n_classes}",
        "",
    ])
    (out_dir / "partial_shadbala.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    return {
        "n_classes_tested": n_classes,
        "n_sig_bare": n_sig_bare, "n_bonf_bare": n_bonf_bare,
        "n_sig_shadbala": n_sig_sb, "n_bonf_shadbala": n_bonf_sb,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_score_partial_shadbala",
        description="Stage F-5 - Partial-Shadbala (4-bala) strength modifier.",
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
        default=Path("data/ml_runs/fork_a_doctrine_partial_shadbala"),
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
    print("=== Stage F-5 - Partial-Shadbala (4-bala) strength ===")
    print(f"  classes tested: {summary['n_classes_tested']}")
    print(f"  bare S5: trend<0.05 = {summary['n_sig_bare']}, "
          f"Bonferroni = {summary['n_bonf_bare']}")
    print(f"  S5 x partial-SB: trend<0.05 = {summary['n_sig_shadbala']}, "
          f"Bonferroni = {summary['n_bonf_shadbala']}")
    print()
    print("Per-class RR comparison (sorted by S5xSB RR):")
    print(f"  {'class':<35} {'bare-RR':>8} {'sb-RR':>10} {'diff':>7}")
    sorted_r = sorted(
        summary["results"].items(),
        key=lambda kv: kv[1]["shadbala_modulated"]["rr_top_vs_bot"]
        if not np.isnan(kv[1]["shadbala_modulated"]["rr_top_vs_bot"]) else -1,
        reverse=True,
    )
    for cls, r in sorted_r:
        bare = r["bare_md"]["rr_top_vs_bot"]
        sb = r["shadbala_modulated"]["rr_top_vs_bot"]
        diff = sb - bare
        print(f"  {cls:<35} {bare:>8.2f} {sb:>10.2f} {diff:>+7.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
