"""AD-level timing test — BPHS Ch.46-47 mutual-relation doctrine.

Round-11 K=100 permutation closed the population-scale chart-structural
RR chapter (`personal` event class: z=0.55, p=0.31 — definitively null).
That tested ONE specific classical claim: "where lord L sits in chart C
predicts whether L's MD windows are eventful."

This module tests a DIFFERENT and previously-unexplored claim from
BPHS Ch.46-47: the antardasha (AD sub-period) effect is driven by the
MUTUAL RELATION between the MD lord and AD lord, not just by either
one's individual placement. Classical witness-and-reception logic.

## Why this should sidestep the lifecycle confound

Within a single MD (e.g. Jupiter's 16-year window), all 9 ADs occur at
similar life stages. Comparing "high-mutual-aspect ADs vs low-mutual-
aspect ADs *within Jupiter MD*" cannot be lifecycle confounding — the
ages are clustered. This is the same logic as test (b) within-lord
stratification, applied one level deeper: stratify by (MD lord, AD lord)
or just by MD lord and use AD-mutual features.

## The AD-mutual-relation score

BPHS Ch.46-47 + Sanjay Rath's reception-witness commentary identifies
five classical features for MD↔AD interaction:

  mutual_aspect_md_to_ad       (MD lord casts drishti on AD lord)
  mutual_aspect_ad_to_md       (AD lord casts drishti back on MD lord)
  dispositor_md_is_ad          (AD lord rules MD lord's sign — reception)
  dispositor_ad_is_md          (MD lord rules AD lord's sign — reception)
  mutual_house_distance        (whole-sign distance MD→AD: 1..12)

We combine these into a doctrine-faithful score with NO chart-structural
HR component (which K=100 already ruled out):

  score = 1.0 * (mutual_aspect_md_to_ad > 0)
        + 1.0 * (mutual_aspect_ad_to_md > 0)
        + 1.0 * dispositor_md_is_ad
        + 1.0 * dispositor_ad_is_md
        + 0.5 * (mutual_house_distance in {1, 5, 9})   # trikona
        - 0.5 * (mutual_house_distance in {6, 8, 12})  # dusthana

The score range is [-0.5, +4.5]. Higher = "more classically witnessed
and supported AD-period."

## The test

1. For each (person, MD, AD) row in dasha_tree, compute the AD-mutual score.
2. Join to events_with_dasha to flag which AD windows had events.
3. Join to dasha_windows for the exposure (duration_days).
4. Stratify by MD lord (9 strata).
5. Within each stratum, bin by score quintile.
6. Compute top-vs-bottom event-rate ratio per stratum.
7. Mantel-Haenszel pool across strata.
8. Cochran's Q heterogeneity test.
9. K=50 chart-shuffle permutation falsifier (cheaper than K=100 since
   AD-mutual features are coarser).

Usage:
    python -m app.medini.ml.dasha_doctrine_ad_timing
    python -m app.medini.ml.dasha_doctrine_ad_timing --event-class marriage
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import norm

from app.medini.ml.dasha_doctrine_pooled import (
    _mantel_haenszel_log_rr, _per_corpus_rr, CorpusRR,
)
from app.medini.ml.dasha_doctrine_personal_disambiguation import (
    _shuffle_natal_charts,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
_N_BINS: Final = 5
_TRIKONA_DISTANCES: Final = frozenset({1, 5, 9})
_DUSTHANA_DISTANCES: Final = frozenset({6, 8, 12})

_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
    "Saturn", "Rahu", "Ketu",
)


# --------------------------------------------------------------------------- #
# AD-mutual-relation score                                                    #
# --------------------------------------------------------------------------- #

def ad_mutual_score(row: pd.Series) -> float:
    """Per-(person, MD, AD) score using only Ch.46-47 mutual-relation features.

    Vectorisable: caller can apply this row-by-row or replicate the
    arithmetic on whole columns.
    """
    score = 0.0
    if row["mutual_aspect_md_to_ad"] > 0:
        score += 1.0
    if row["mutual_aspect_ad_to_md"] > 0:
        score += 1.0
    if row["dispositor_md_is_ad"]:
        score += 1.0
    if row["dispositor_ad_is_md"]:
        score += 1.0
    if row["mutual_house_distance"] in _TRIKONA_DISTANCES:
        score += 0.5
    elif row["mutual_house_distance"] in _DUSTHANA_DISTANCES:
        score -= 0.5
    return score


def ad_mutual_score_vec(df: pd.DataFrame) -> pd.Series:
    """Vectorised version of ad_mutual_score — required for 3.5M rows."""
    score = pd.Series(0.0, index=df.index, dtype="float64")
    score += (df["mutual_aspect_md_to_ad"] > 0).astype(float)
    score += (df["mutual_aspect_ad_to_md"] > 0).astype(float)
    score += df["dispositor_md_is_ad"].astype(float)
    score += df["dispositor_ad_is_md"].astype(float)
    score += 0.5 * df["mutual_house_distance"].isin(_TRIKONA_DISTANCES).astype(float)
    score -= 0.5 * df["mutual_house_distance"].isin(_DUSTHANA_DISTANCES).astype(float)
    return score


# --------------------------------------------------------------------------- #
# Build the AD-level test matrix                                              #
# --------------------------------------------------------------------------- #

def build_ad_test_matrix(
    event_class: str, data_dir: Path = DEFAULT_DATA_DIR,
) -> pd.DataFrame:
    """One row per (person, md_seq, ad_seq) with:
      - md_lord, ad_lord
      - ad_mutual_score (computed)
      - n_events     (count of event_class during this AD window)
      - had_event    (binary: n_events > 0)
      - duration_days (summed across PD windows in this AD)
      - corpus       (from name_norm pattern)

    Uses ``dasha_mdadpd_corpus.parquet`` (Round-9 ADB MD-AD-PD-level data)
    because ``events_with_dasha.parquet`` only has the harmonized 5-class
    cross-corpus taxonomy (no ``personal``, ``health``, ``career``, etc).

    Currently ADB-only — the WD/LA corpora don't have the granular
    event classes that BPHS doctrine cares about.
    """
    label_col = f"event_{event_class}"
    mdadpd = pd.read_parquet(data_dir / "dasha_mdadpd_corpus.parquet")
    if label_col not in mdadpd.columns:
        raise ValueError(
            f"event_{event_class!r} not in dasha_mdadpd_corpus columns. "
            f"Available event_* cols: {[c for c in mdadpd.columns if c.startswith('event_')]}"
        )

    # Aggregate PD rows up to AD level: sum events + sum durations.
    ad_level = mdadpd.groupby(
        ["name_norm", "birth_jd", "md_seq_idx", "ad_seq_idx", "md_lord", "ad_lord"],
        as_index=False,
    ).agg(
        n_events=(label_col, "sum"),
        duration_days=("window_duration_days", "sum"),
    )
    ad_level["had_event"] = (ad_level["n_events"] > 0).astype(int)
    ad_level["corpus"] = "ADB"

    # Bridge name_norm → person_id via the canonical mapping table.
    # Replaces the fragile inline "ADB:" + birth_jd.round(4) composition.
    id_map = pd.read_parquet(
        data_dir / "person_id_map.parquet",
        columns=["corpus_tag", "name_norm", "person_id"],
    )
    adb_map = id_map[id_map["corpus_tag"] == "ADB"][["name_norm", "person_id"]]
    ad_level = ad_level.merge(adb_map, on="name_norm", how="left")

    # Join with dasha_tree on (person_id, md_seq, ad_seq) for mutual-relation features.
    tree = pd.read_parquet(
        data_dir / "dasha_tree.parquet",
        columns=[
            "person_id", "md_seq", "ad_seq",
            "mutual_house_distance",
            "mutual_aspect_md_to_ad", "mutual_aspect_ad_to_md",
            "dispositor_md_is_ad", "dispositor_ad_is_md",
        ],
    )
    df = ad_level.rename(
        columns={"md_seq_idx": "md_seq", "ad_seq_idx": "ad_seq"},
    ).merge(tree, on=["person_id", "md_seq", "ad_seq"], how="inner")

    df["ad_mutual_score"] = ad_mutual_score_vec(df)
    return df


# --------------------------------------------------------------------------- #
# Stratified RR analysis                                                      #
# --------------------------------------------------------------------------- #

def _ad_rr_for_stratum(stratum: pd.DataFrame) -> CorpusRR | None:
    """Compute top-vs-bottom quintile event-rate RR for one (corpus, MD lord)
    stratum, using ad_mutual_score for binning and duration_days for exposure.
    """
    if len(stratum) < 100 or stratum["had_event"].sum() < 5:
        return None

    s = stratum.copy()
    try:
        s["bin"] = pd.qcut(
            s["ad_mutual_score"].rank(method="first"),
            q=_N_BINS, labels=False, duplicates="drop",
        )
    except ValueError:
        return None

    n_top = int(s.loc[s["bin"] == _N_BINS - 1, "had_event"].sum())
    n_bot = int(s.loc[s["bin"] == 0, "had_event"].sum())
    exp_top = float(s.loc[s["bin"] == _N_BINS - 1, "duration_days"].sum())
    exp_bot = float(s.loc[s["bin"] == 0, "duration_days"].sum())

    if n_top == 0 or n_bot == 0 or exp_top <= 0 or exp_bot <= 0:
        return None

    rr = (n_top / exp_top) / (n_bot / exp_bot)
    var = 1.0 / n_top + 1.0 / n_bot
    return CorpusRR(
        corpus="",
        n_events_top=n_top, exp_top_days=exp_top,
        n_events_bot=n_bot, exp_bot_days=exp_bot,
        rr=rr, log_rr_var=var,
    )


def pool_by_md_lord(df: pd.DataFrame, min_events: int = 10) -> dict:
    """Mantel-Haenszel pooling across (corpus, MD lord) strata."""
    strata: list[CorpusRR] = []
    per_stratum_dicts: list[dict] = []
    for corpus in df["corpus"].dropna().unique():
        for md_lord in _GRAHAS:
            sub = df[(df["corpus"] == corpus) & (df["md_lord"] == md_lord)]
            if sub["had_event"].sum() < min_events:
                continue
            rr = _ad_rr_for_stratum(sub)
            if rr is None:
                continue
            rr.corpus = f"{corpus}::{md_lord}"
            strata.append(rr)
            per_stratum_dicts.append({
                "stratum": rr.corpus,
                "rr": rr.rr,
                "n_top": rr.n_events_top, "n_bot": rr.n_events_bot,
            })
    pooled = _mantel_haenszel_log_rr(strata)
    return {"strata": per_stratum_dicts, "pooled": pooled, "k": len(strata)}


# --------------------------------------------------------------------------- #
# Permutation falsifier                                                       #
# --------------------------------------------------------------------------- #

def _shuffled_pooled_rr(
    event_class: str,
    seed: int,
    data_dir: Path = DEFAULT_DATA_DIR,
) -> float:
    """One permutation: shuffle natal charts, rebuild dasha_tree-equivalent
    features, re-run stratified pooling.

    Approach: shuffle the planet position columns in the per-corpus natal
    files (lord houses/signs), then re-derive mutual-relation features.
    Implementation reuses _shuffle_natal_charts on the same natal source
    files; the dasha_tree itself doesn't get re-derived since that's
    expensive. Instead we shuffle within the (corpus, md_seq, ad_seq)
    groups directly — equivalent for an asymptotic null.

    Simpler approach used here: shuffle the ad_mutual_score column within
    each (corpus, md_lord) stratum. This breaks the chart→score linkage
    while preserving the marginal distribution of scores per stratum,
    which is the exact null we want to test.
    """
    rng = np.random.default_rng(seed)
    df = build_ad_test_matrix(event_class, data_dir=data_dir)
    # Shuffle scores within each (corpus, md_lord) stratum.
    for (corpus, lord), idx in df.groupby(["corpus", "md_lord"]).groups.items():
        perm = rng.permutation(len(idx))
        df.loc[idx, "ad_mutual_score"] = df.loc[idx, "ad_mutual_score"].to_numpy()[perm]
    result = pool_by_md_lord(df)
    return result["pooled"]["rr_pooled"]


# --------------------------------------------------------------------------- #
# Driver                                                                      #
# --------------------------------------------------------------------------- #

def run(
    out_dir: Path,
    event_class: str = "personal",
    n_perms: int = 50,
    data_dir: Path = DEFAULT_DATA_DIR,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    df = build_ad_test_matrix(event_class, data_dir=data_dir)
    logger.info(
        "Built AD test matrix: %d rows, %d events of class %s",
        len(df), int(df["had_event"].sum()), event_class,
    )
    logger.info("Score distribution: min=%.2f mean=%.2f max=%.2f",
                df["ad_mutual_score"].min(),
                df["ad_mutual_score"].mean(),
                df["ad_mutual_score"].max())

    real = pool_by_md_lord(df)
    logger.info(
        "Real AD-mutual pooled RR = %.3f (95%% CI %.3f-%.3f), p=%.3g, Q_p=%.3g, k=%d",
        real["pooled"]["rr_pooled"], real["pooled"]["ci_low"],
        real["pooled"]["ci_high"], real["pooled"]["p"],
        real["pooled"]["q_p"], real["pooled"]["k"],
    )

    # Permutation null: shuffle scores within (corpus, MD lord).
    rng = np.random.default_rng(42)
    seeds = rng.integers(0, 2**31 - 1, size=n_perms)
    shuffled_rrs: list[float] = []
    for i, seed in enumerate(seeds, start=1):
        rr = _shuffled_pooled_rr(event_class, int(seed), data_dir=data_dir)
        shuffled_rrs.append(rr)
        if i % 5 == 0 or i == 1 or i == n_perms:
            logger.info("Permutation %d/%d  shuffled_RR=%.3f", i, n_perms, rr)

    arr = np.array(shuffled_rrs)
    log_real = np.log(real["pooled"]["rr_pooled"])
    log_shuf = np.log(arr[~np.isnan(arr) & (arr > 0)])
    null_mean_log = float(np.mean(log_shuf))
    null_std_log = (float(np.std(log_shuf, ddof=1))
                    if len(log_shuf) > 1 else float("nan"))
    z = ((log_real - null_mean_log) / null_std_log
         if null_std_log and null_std_log > 0 else float("nan"))
    p_one = float(1.0 - norm.cdf(z)) if not np.isnan(z) else float("nan")
    n_exceed = int(np.sum(arr >= real["pooled"]["rr_pooled"]))
    emp_p = (n_exceed + 1) / (n_perms + 1)

    summary = {
        "event_class": event_class,
        "score_formula": (
            "1.0 * (mutual_aspect_md_to_ad > 0) + "
            "1.0 * (mutual_aspect_ad_to_md > 0) + "
            "1.0 * dispositor_md_is_ad + "
            "1.0 * dispositor_ad_is_md + "
            "0.5 * (mutual_house_distance in {1,5,9}) - "
            "0.5 * (mutual_house_distance in {6,8,12})"
        ),
        "n_rows": len(df),
        "n_events": int(df["had_event"].sum()),
        "real": real,
        "permutation": {
            "n_perms": n_perms,
            "all_shuffled_rrs": [float(x) for x in arr],
            "null_mean": float(np.exp(null_mean_log)),
            "null_min": float(np.min(arr)),
            "null_max": float(np.max(arr)),
            "null_median": float(np.median(arr)),
            "z_score": float(z),
            "p_value_parametric": p_one,
            "empirical_p_value": emp_p,
            "n_shuffled_exceeding_real": n_exceed,
        },
    }
    (out_dir / f"ad_timing_{event_class}.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8",
    )

    p = summary["permutation"]
    lines = [
        f"# AD-level timing test — `{event_class}` (BPHS Ch.46-47)",
        "",
        f"**Score**: AD-mutual-relation only (no chart-structural HR).",
        "",
        "```",
        summary["score_formula"],
        "```",
        "",
        f"## Test corpus",
        "",
        f"- AD-window rows: {summary['n_rows']:,}",
        f"- Events of class `{event_class}`: {summary['n_events']:,}",
        f"- Stratification: per (corpus, MD lord); within-MD AD-quintile binning",
        "",
        f"## Per-stratum RRs (real)",
        "",
        "| Stratum (corpus::md_lord) | n_top | n_bot | RR |",
        "|---|---:|---:|---:|",
    ]
    for s in sorted(real["strata"], key=lambda x: -x["rr"] if not np.isnan(x["rr"]) else 0):
        lines.append(f"| {s['stratum']} | {s['n_top']} | {s['n_bot']} | {s['rr']:.2f} |")

    lines.extend([
        "",
        f"## Pooled (Mantel-Haenszel)",
        "",
        f"| Quantity | Value |",
        f"|---|---|",
        f"| n strata | {real['pooled']['k']} |",
        f"| Pooled RR | **{real['pooled']['rr_pooled']:.3f}** |",
        f"| 95% CI | {real['pooled']['ci_low']:.2f}–{real['pooled']['ci_high']:.2f} |",
        f"| p-value | **{real['pooled']['p']:.3g}** |",
        f"| Cochran Q_p | {real['pooled']['q_p']:.3g} |",
        "",
        f"## Permutation falsifier (K={n_perms})",
        "",
        f"| Quantity | Value |",
        f"|---|---|",
        f"| Real RR | {real['pooled']['rr_pooled']:.3f} |",
        f"| Null mean | {p['null_mean']:.3f} |",
        f"| Null median | {p['null_median']:.3f} |",
        f"| Null min | {p['null_min']:.3f} |",
        f"| Null max | {p['null_max']:.3f} |",
        f"| z-score | **{p['z_score']:.2f}** |",
        f"| Empirical p-value | **{p['empirical_p_value']:.3g}** |",
        f"| Shuffled ≥ real | {p['n_shuffled_exceeding_real']}/{p['n_perms']} |",
        "",
        f"## Verdict",
        "",
    ])
    z_val = p["z_score"]
    if not np.isnan(z_val) and z_val > 3 and p["empirical_p_value"] < 0.01:
        lines.append("> ✅ **AD-MUTUAL TIMING SIGNAL CONFIRMED** — Classical "
                     "Ch.46-47 mutual-relation features predict event timing "
                     "within MDs above chart-shuffled null.")
    elif not np.isnan(z_val) and z_val < 1:
        lines.append("> 🚫 **NULL** — Mutual-relation score doesn't beat the "
                     "permutation null. AD-level timing signal not recoverable "
                     "at population scale with these features.")
    else:
        lines.append(f"> 🤔 **PARTIAL/AMBIGUOUS** — z={z_val:.2f}. Some lift above "
                     "null but margin requires larger K to resolve.")
    lines.append("")
    (out_dir / f"ad_timing_{event_class}.md").write_text(
        "\n".join(lines), encoding="utf-8",
    )
    logger.info("Wrote %s", out_dir / f"ad_timing_{event_class}.md")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_ad_timing",
        description="AD-level mutual-relation timing test (BPHS Ch.46-47).",
    )
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/round11_ad_timing"))
    parser.add_argument("--event-class", type=str, default="personal")
    parser.add_argument("--n-perms", type=int, default=50)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    summary = run(args.out, event_class=args.event_class, n_perms=args.n_perms)
    print()
    print(f"=== AD-mutual timing test ({args.event_class}) ===")
    print(f"  n strata:       {summary['real']['pooled']['k']}")
    print(f"  real pooled RR: {summary['real']['pooled']['rr_pooled']:.3f}")
    print(f"  95% CI:         "
          f"{summary['real']['pooled']['ci_low']:.2f}-"
          f"{summary['real']['pooled']['ci_high']:.2f}")
    print(f"  p-value:        {summary['real']['pooled']['p']:.3g}")
    print(f"  Cochran Q_p:    {summary['real']['pooled']['q_p']:.3g}")
    p = summary["permutation"]
    print(f"  Null mean:      {p['null_mean']:.3f}")
    print(f"  Null max:       {p['null_max']:.3f}")
    print(f"  z-score:        {p['z_score']:.2f}")
    print(f"  empirical p:    {p['empirical_p_value']:.3g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
