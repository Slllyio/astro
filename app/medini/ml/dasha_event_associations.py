"""Descriptive dasha→event associations — "which lord running makes which event".

This is the plain, model-free answer to a question the doctrine-scorer
machinery (``dasha_doctrine_*``) never reports directly:

  Across every dated life event, which **Mahadasha lord** and
  **Antardasha lord** was actually running — and which lord (or MD/AD
  pair) is *over-represented* for each kind of event?

No classifier, no chart features, no scorer. Just a contingency table
between the active Vimshottari lord at ``event_jd`` and the event class,
turned into an honest **lift** statistic.

Why lift and not raw counts
---------------------------
Vimshottari Mahadashas have unequal lengths::

    Ketu 7   Venus 20   Sun 6    Moon 10   Mars 7
    Rahu 18  Jupiter 16 Saturn 19  Mercury 17     (= 120 years)

So *everyone* spends 20/120 ≈ 16.7 % of life under Venus and only
6/120 = 5 % under Sun, **before any astrology**. A naive "most common
MD lord at marriage" is therefore biased toward the long dashas
(Venus, Saturn, Mercury, Rahu). The honest metric is::

    lift = observed_share / baseline_exposure_share

lift = 1.0  → the lord shows up exactly as often as raw exposure predicts
lift > 1.0  → events of this class cluster under this lord
lift < 1.0  → events of this class avoid this lord

Each cell also gets a two-sided binomial p-value (observed count vs the
baseline-expected count), so you can tell a real tilt from small-n noise.

Baseline exposure
-----------------
Two ways to get the denominator, picked by ``--baseline``:

  ``windows``  (default when ``dasha_windows.parquet`` is present)
      Measured person-time: sum ``duration_days`` per lord across every
      dasha window in the corpus, normalised to a share. This captures
      the real, lifespan-truncated exposure of *these* people.

  ``nominal``  (theory-only fallback)
      The Vimshottari constants themselves: ``lord_years / 120``. Clean
      and corpus-independent. Across a population with uniformly
      distributed birth nakshatras the marginal AD share also collapses
      to the same proportions, so one table serves both MD and AD.

Caveat carried forward from the Round-11 synthesis: a raw association is
*not* a deconfounded causal effect. Life events cluster by age, and dasha
lords correlate with age-at-onset through the cycle. This module reports
the descriptive tilt only — see ``dasha_doctrine_pooled`` /
``round11_triple_test_synthesis`` for the permutation-controlled verdict.

Usage::

    python -m app.medini.ml.dasha_event_associations
    python -m app.medini.ml.dasha_event_associations \\
        --data-dir app/medini/data \\
        --out data/ml_runs/dasha_event_associations \\
        --baseline windows --min-support 8
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd
from scipy.stats import binomtest

from app.core.ephemeris_engine import DASHA_LORDS

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
DEFAULT_OUT_DIR: Final = Path("data/ml_runs/dasha_event_associations")
EVENTS_FILE: Final = "events_with_dasha.parquet"
WINDOWS_FILE: Final = "dasha_windows.parquet"

# Total Vimshottari cycle length in years (sum of DASHA_LORDS).
_CYCLE_YEARS: Final = float(sum(years for _, years in DASHA_LORDS))


# --------------------------------------------------------------------------
# Baselines
# --------------------------------------------------------------------------

def nominal_exposure() -> dict[str, float]:
    """Vimshottari proportional exposure: ``lord_years / 120``.

    Sums to 1.0. Serves as both the MD and the marginal-AD baseline (the
    within-MD AD proportions are the same constants, so across a full
    cycle the marginal AD share equals the MD share).
    """
    return {lord: years / _CYCLE_YEARS for lord, years in DASHA_LORDS}


def measured_exposure(windows: pd.DataFrame, lord_col: str) -> dict[str, float]:
    """Person-time exposure per lord, measured from the dasha windows.

    ``windows`` must carry ``duration_days`` and ``lord_col`` (``md_lord``
    or ``ad_lord``). Returns a share dict summing to 1.0 over the lords
    that actually appear. Falls back to nominal weighting only for lords
    with zero measured exposure (shouldn't happen on a full corpus).
    """
    if lord_col not in windows.columns or "duration_days" not in windows.columns:
        raise KeyError(
            f"windows frame needs '{lord_col}' and 'duration_days'; "
            f"got {list(windows.columns)}"
        )
    totals = (
        windows.groupby(lord_col)["duration_days"].sum().astype(float)
    )
    grand = float(totals.sum())
    if grand <= 0:
        raise ValueError("measured exposure has non-positive total duration")
    return {str(lord): days / grand for lord, days in totals.items()}


# --------------------------------------------------------------------------
# Single-lord associations (MD or AD)
# --------------------------------------------------------------------------

def compute_lord_associations(
    events: pd.DataFrame,
    lord_col: str,
    exposure: dict[str, float],
    *,
    class_col: str = "event_class",
    min_support: int = 5,
) -> pd.DataFrame:
    """One row per (event_class, lord): observed share, baseline, lift, p.

    Only rows where ``lord_col`` is non-null are counted. Cells below
    ``min_support`` observed events are dropped (too noisy to report).
    ``lift`` is ``observed_share / baseline_share``; ``p_value`` is a
    two-sided binomial test of the observed count against the baseline
    probability over the per-class event total.
    """
    df = events[[class_col, lord_col]].dropna()
    rows: list[dict[str, object]] = []

    for event_class, grp in df.groupby(class_col):
        n_class = len(grp)
        counts = grp[lord_col].value_counts()
        for lord, n in counts.items():
            if n < min_support:
                continue
            base = exposure.get(str(lord))
            if not base or base <= 0:
                continue
            observed_share = n / n_class
            lift = observed_share / base
            p = binomtest(int(n), int(n_class), base, alternative="two-sided").pvalue
            rows.append({
                "scope": lord_col.replace("_lord_at_event", "").replace("_lord", ""),
                "event_class": event_class,
                "lord": str(lord),
                "n": int(n),
                "n_class": int(n_class),
                "observed_share": round(observed_share, 4),
                "baseline_share": round(base, 4),
                "expected_n": round(base * n_class, 2),
                "lift": round(lift, 3),
                "p_value": p,
            })

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(
        ["event_class", "lift"], ascending=[True, False]
    ).reset_index(drop=True)


# --------------------------------------------------------------------------
# MD×AD pair associations — "which lord-pair running makes which event"
# --------------------------------------------------------------------------

def compute_pair_associations(
    events: pd.DataFrame,
    exposure_md: dict[str, float],
    exposure_ad: dict[str, float],
    *,
    md_col: str = "md_lord_at_event",
    ad_col: str = "ad_lord_at_event",
    class_col: str = "event_class",
    min_support: int = 5,
) -> pd.DataFrame:
    """One row per (event_class, MD lord, AD lord) with lift over the
    independence baseline ``P(MD) * P(AD)``.

    The independence baseline asks: relative to how often this MD/AD
    *combination* is running at all, does this event class prefer it?
    """
    df = events[[class_col, md_col, ad_col]].dropna()
    rows: list[dict[str, object]] = []

    for event_class, grp in df.groupby(class_col):
        n_class = len(grp)
        combos = grp.groupby([md_col, ad_col]).size()
        for (md, ad), n in combos.items():
            if n < min_support:
                continue
            base_md = exposure_md.get(str(md))
            base_ad = exposure_ad.get(str(ad))
            if not base_md or not base_ad:
                continue
            base = base_md * base_ad
            observed_share = n / n_class
            lift = observed_share / base
            p = binomtest(int(n), int(n_class), base, alternative="two-sided").pvalue
            rows.append({
                "scope": "md_ad_pair",
                "event_class": event_class,
                "lord": f"{md}/{ad}",
                "md_lord": str(md),
                "ad_lord": str(ad),
                "n": int(n),
                "n_class": int(n_class),
                "observed_share": round(observed_share, 4),
                "baseline_share": round(base, 5),
                "expected_n": round(base * n_class, 2),
                "lift": round(lift, 3),
                "p_value": p,
            })

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(
        ["event_class", "lift"], ascending=[True, False]
    ).reset_index(drop=True)


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def _fmt_p(p: float) -> str:
    if p < 1e-4:
        return f"{p:.1e}"
    return f"{p:.4f}"


def _lord_block(title: str, sub: pd.DataFrame, alpha: float) -> list[str]:
    lines = [f"### {title}", ""]
    lines.append("| lord | n | obs % | base % | lift | p |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for _, r in sub.iterrows():
        star = " ✶" if r["p_value"] < alpha else ""
        lines.append(
            f"| {r['lord']} | {r['n']} | {r['observed_share']*100:.1f} | "
            f"{r['baseline_share']*100:.1f} | **{r['lift']:.2f}**{star} | "
            f"{_fmt_p(r['p_value'])} |"
        )
    lines.append("")
    return lines


def build_report(
    md_assoc: pd.DataFrame,
    ad_assoc: pd.DataFrame,
    pair_assoc: pd.DataFrame,
    *,
    baseline_mode: str,
    alpha: float = 0.05,
    top_pairs: int = 8,
) -> str:
    """Render a human-readable markdown digest of the associations."""
    lines: list[str] = [
        "# Dasha → event associations (descriptive)",
        "",
        f"Baseline exposure: **{baseline_mode}**. "
        f"lift = observed_share ÷ baseline_share. ✶ = binomial p < {alpha}.",
        "",
        "> Descriptive tilt only — NOT a deconfounded causal effect. "
        "Events cluster by age and dasha lords correlate with age through "
        "the cycle. See `round11_triple_test_synthesis` for the "
        "permutation-controlled verdict.",
        "",
    ]

    # Headline: strongest significant over-representations across all scopes.
    frames = [f for f in (md_assoc, ad_assoc) if not f.empty]
    if frames:
        allm = pd.concat(frames, ignore_index=True)
        head = allm[(allm["p_value"] < alpha) & (allm["lift"] > 1.0)]
        head = head.sort_values("lift", ascending=False).head(12)
        if not head.empty:
            lines += ["## Headline over-representations", "",
                      "| scope | event_class | lord | n | lift | p |",
                      "|---|---|---|---:|---:|---:|"]
            for _, r in head.iterrows():
                lines.append(
                    f"| {r['scope']} | {r['event_class']} | {r['lord']} | "
                    f"{r['n']} | **{r['lift']:.2f}** | {_fmt_p(r['p_value'])} |"
                )
            lines.append("")

    # Per-class detail.
    classes = sorted(
        set(md_assoc.get("event_class", pd.Series(dtype=str)))
        | set(ad_assoc.get("event_class", pd.Series(dtype=str)))
    )
    for ec in classes:
        lines += [f"## {ec}", ""]
        if not md_assoc.empty:
            sub = md_assoc[md_assoc["event_class"] == ec]
            if not sub.empty:
                lines += _lord_block("Mahadasha lord", sub, alpha)
        if not ad_assoc.empty:
            sub = ad_assoc[ad_assoc["event_class"] == ec]
            if not sub.empty:
                lines += _lord_block("Antardasha lord", sub, alpha)
        if not pair_assoc.empty:
            sub = pair_assoc[pair_assoc["event_class"] == ec].head(top_pairs)
            if not sub.empty:
                lines += [f"### Top MD/AD pairs (lift, min support)", "",
                          "| MD/AD | n | obs % | base % | lift | p |",
                          "|---|---:|---:|---:|---:|---:|"]
                for _, r in sub.iterrows():
                    star = " ✶" if r["p_value"] < alpha else ""
                    lines.append(
                        f"| {r['lord']} | {r['n']} | {r['observed_share']*100:.1f} | "
                        f"{r['baseline_share']*100:.2f} | **{r['lift']:.2f}**{star} | "
                        f"{_fmt_p(r['p_value'])} |"
                    )
                lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def run(
    data_dir: Path,
    out_dir: Path,
    *,
    baseline: str = "windows",
    min_support: int = 5,
    alpha: float = 0.05,
) -> dict[str, int]:
    """Load the join, compute MD/AD/pair associations, write CSV + markdown."""
    events_path = data_dir / EVENTS_FILE
    if not events_path.exists():
        raise FileNotFoundError(
            f"{events_path} missing — run "
            f"`python -m app.medini.etl.build_event_dasha_join` first."
        )
    events = pd.read_parquet(events_path)
    events = events[events["md_lord_at_event"].notna()].copy()
    logger.info("loaded %d dasha-matched events from %s", len(events), events_path)

    # Resolve baselines.
    windows_path = data_dir / WINDOWS_FILE
    if baseline == "windows" and windows_path.exists():
        windows = pd.read_parquet(windows_path)
        exp_md = measured_exposure(windows, "md_lord")
        exp_ad = measured_exposure(windows, "ad_lord")
        baseline_mode = "windows (measured person-time)"
    else:
        if baseline == "windows":
            logger.warning("%s absent — falling back to nominal baseline", windows_path)
        exp_md = nominal_exposure()
        exp_ad = nominal_exposure()
        baseline_mode = "nominal (Vimshottari proportions)"

    md_assoc = compute_lord_associations(
        events, "md_lord_at_event", exp_md, min_support=min_support
    )
    ad_assoc = compute_lord_associations(
        events, "ad_lord_at_event", exp_ad, min_support=min_support
    )
    pair_assoc = compute_pair_associations(
        events, exp_md, exp_ad, min_support=min_support
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    long = pd.concat(
        [f for f in (md_assoc, ad_assoc, pair_assoc) if not f.empty],
        ignore_index=True,
    ) if any(not f.empty for f in (md_assoc, ad_assoc, pair_assoc)) else pd.DataFrame()
    csv_path = out_dir / "dasha_event_associations.csv"
    long.to_csv(csv_path, index=False)

    md_path = out_dir / "dasha_event_associations.md"
    md_path.write_text(
        build_report(md_assoc, ad_assoc, pair_assoc,
                     baseline_mode=baseline_mode, alpha=alpha),
        encoding="utf-8",
    )

    logger.info("wrote %s and %s", csv_path, md_path)
    return {
        "events": len(events),
        "md_cells": len(md_assoc),
        "ad_cells": len(ad_assoc),
        "pair_cells": len(pair_assoc),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--baseline", choices=["windows", "nominal"], default="windows")
    parser.add_argument("--min-support", type=int, default=5)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s",
    )
    stats = run(
        args.data_dir, args.out,
        baseline=args.baseline, min_support=args.min_support, alpha=args.alpha,
    )
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
