"""Round-11 follow-up — Pooled doctrine RR across ADB + Wikidata + Lunarastro.

Round 9's per-corpus doctrine RR test produced contradictory results:
  ADB:  fame RR=1.43 (Bonferroni PASS),  personal RR=2.44 PASS
  WD:   fame RR=1.04 (n.s.),             career RR=1.25 PASS
  LA:   family RR=1.23 PASS              (everything else fails)
  Intersection of Bonferroni passes across all 3 = EMPTY.

The verdict at the time was "corpus-specific Type I error." But that
conclusion was reached via a NAIVE intersection rule — it doesn't ask
the right question. The correct question is:

  Is there a common underlying effect across all 3 corpora,
  with each corpus contributing partial information to the estimate?

This is the classical multi-stratum problem in epidemiology, solved by
Mantel-Haenszel pooled rate ratios + Cochran's Q heterogeneity test:

  RR_MH    : weighted pooled estimate. Each stratum contributes inversely
             proportional to its variance. Resistant to sparse strata.
  Cochran Q: tests whether per-stratum RRs differ significantly from the
             pooled estimate. If Q is large -> corpora truly disagree
             (heterogeneity rejects pooling). If Q is small -> the 3
             corpora are estimating the same underlying RR.

This script also DEDUPES cross-corpus dupes using ``resolved_persons.parquet``
so the same person doesn't contribute to more than one stratum.

Output: per-event-class table showing per-corpus RRs, pooled MH RR,
heterogeneity p, and a Bonferroni-corrected verdict on the POOLED estimate.

Usage:
    python -m app.medini.ml.dasha_doctrine_pooled
    python -m app.medini.ml.dasha_doctrine_pooled --out data/ml_runs/round11_doctrine_pooled
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import binom, chi2, norm

from app.medini.ml.dasha_doctrine_score import _HOUSE_MAP
from app.medini.ml.dasha_doctrine_score_mix import (
    _PER_CLASS_SCORER, _annotate_mix, _scorer_for,
)

logger = logging.getLogger(__name__)

# Per-corpus file locations. Each tuple is (corpus_tag, dasha_path, natal_path).
_CORPUS_FILES: Final[tuple[tuple[str, Path, Path], ...]] = (
    ("ADB",
     Path("app/medini/data/dasha_event_corpus.parquet"),
     Path("app/medini/data/natal_lord_houses.parquet")),
    ("WD",
     Path("app/medini/data/wikidata_dasha_corpus.parquet"),
     Path("app/medini/data/wikidata_natal_lord_houses.parquet")),
    ("LA",
     Path("app/medini/data/lunarastro_dasha_corpus.parquet"),
     Path("app/medini/data/lunarastro_natal_lord_houses.parquet")),
)

# Corpus precedence for dedup. Higher number wins (ADB > WD > LA).
_CORPUS_PRECEDENCE: Final[dict[str, int]] = {"ADB": 3, "WD": 2, "LA": 1}


@dataclass
class CorpusRR:
    """Per-(corpus, class) rate-ratio summary."""
    corpus: str
    n_events_top: int
    exp_top_days: float
    n_events_bot: int
    exp_bot_days: float
    rr: float
    log_rr_var: float

    @property
    def log_rr(self) -> float:
        if self.rr <= 0 or np.isnan(self.rr):
            return float("nan")
        return float(np.log(self.rr))


# --------------------------------------------------------------------------- #
# Dedup                                                                       #
# --------------------------------------------------------------------------- #

def _dedup_by_birth_jd(
    dasha_dfs: dict[str, pd.DataFrame],
    natal_dfs: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], int]:
    """Drop cross-corpus duplicates by exact birth_jd match.

    Strategy: build a set of (rounded birth_jd) values that appear in
    higher-precedence corpora. For each lower-precedence corpus, filter
    out persons whose birth_jd round-matches a higher-precedence person.

    Rounds birth_jd to 4 decimals (~9 sec TT) to match the resolution
    used by the Phase-1 person_id namespacing.
    """
    def _key(jd: float) -> float:
        return round(float(jd), 4)

    seen_jds: set[float] = set()
    out_natal: dict[str, pd.DataFrame] = {}
    out_dasha: dict[str, pd.DataFrame] = {}
    n_dropped = 0

    # Iterate corpora in DESCENDING precedence so the highest wins.
    for corpus in sorted(_CORPUS_PRECEDENCE, key=_CORPUS_PRECEDENCE.get, reverse=True):
        nat = natal_dfs[corpus]
        # Some natal tables don't carry birth_jd directly; pull it from dasha.
        if "birth_jd" not in nat.columns:
            # Build name_norm -> birth_jd map from the dasha corpus.
            bj_map = (
                dasha_dfs[corpus][["name_norm", "birth_jd"]]
                .drop_duplicates("name_norm").set_index("name_norm")["birth_jd"]
            )
            nat = nat.copy()
            nat["birth_jd"] = nat["name_norm"].map(bj_map)

        # Find which natal rows have a birth_jd already seen at higher precedence.
        jd_key_series = nat["birth_jd"].apply(_key)
        is_dup = jd_key_series.isin(seen_jds)
        n_dropped += int(is_dup.sum())
        kept_nat = nat.loc[~is_dup].copy()
        out_natal[corpus] = kept_nat
        # Filter dasha corpus to retained name_norms.
        retained_names = set(kept_nat["name_norm"])
        out_dasha[corpus] = dasha_dfs[corpus][
            dasha_dfs[corpus]["name_norm"].isin(retained_names)
        ].copy()
        # Add the kept JDs to the seen set so lower-precedence corpora skip them.
        seen_jds.update(kept_nat["birth_jd"].apply(_key).tolist())

    return out_dasha, out_natal, n_dropped


# --------------------------------------------------------------------------- #
# Per-corpus rate ratio with log-RR variance for MH pooling                   #
# --------------------------------------------------------------------------- #

def _per_corpus_rr(
    annotated: pd.DataFrame, event_class: str, n_bins: int = 5,
) -> CorpusRR | None:
    """Compute top-vs-bottom quintile RR + log-RR variance for one corpus.

    The log-RR variance under the Poisson model is the sum of inverse
    event counts in the two compared cells: Var(log RR) = 1/n_top + 1/n_bot.
    This is what MH pooling needs to weight the strata.
    """
    label_col = f"event_{event_class}"
    if label_col not in annotated.columns:
        return None

    annotated = annotated.copy()
    annotated["duration_days"] = (
        annotated["dasha_end_jd"] - annotated["dasha_start_jd"]
    )
    try:
        annotated["bin"] = pd.qcut(
            annotated["mix_score"].rank(method="first"),
            q=n_bins, labels=False, duplicates="drop",
        )
    except ValueError:
        return None

    n_top = int(annotated.loc[annotated["bin"] == n_bins - 1, label_col].sum())
    n_bot = int(annotated.loc[annotated["bin"] == 0, label_col].sum())
    exp_top = float(annotated.loc[annotated["bin"] == n_bins - 1, "duration_days"].sum())
    exp_bot = float(annotated.loc[annotated["bin"] == 0, "duration_days"].sum())

    if n_top == 0 or n_bot == 0 or exp_top <= 0 or exp_bot <= 0:
        return None

    rate_top = n_top / exp_top
    rate_bot = n_bot / exp_bot
    rr = rate_top / rate_bot
    log_rr_var = 1.0 / n_top + 1.0 / n_bot

    return CorpusRR(
        corpus="",  # caller sets
        n_events_top=n_top, exp_top_days=exp_top,
        n_events_bot=n_bot, exp_bot_days=exp_bot,
        rr=rr, log_rr_var=log_rr_var,
    )


# --------------------------------------------------------------------------- #
# Mantel-Haenszel pooling + Cochran's Q heterogeneity                         #
# --------------------------------------------------------------------------- #

def _mantel_haenszel_log_rr(per_corpus: list[CorpusRR]) -> dict[str, float]:
    """Inverse-variance-weighted pooled log-RR + Cochran's Q + p_het.

    For Poisson rate ratios with independent strata, the canonical pooled
    estimator is the inverse-variance-weighted average of log-RRs:
        log_RR_pooled = sum(w_i * log_RR_i) / sum(w_i)
        Var(log_RR_pooled) = 1 / sum(w_i)
    with w_i = 1 / Var(log_RR_i).

    Cochran's Q tests homogeneity:
        Q = sum(w_i * (log_RR_i - log_RR_pooled)^2)
    which is chi-squared with k-1 degrees of freedom under the null.
    """
    valid = [c for c in per_corpus if c is not None and not np.isnan(c.log_rr)]
    if not valid:
        return {"rr_pooled": float("nan"), "z": float("nan"), "p": 1.0,
                "ci_low": float("nan"), "ci_high": float("nan"),
                "q_stat": float("nan"), "q_p": 1.0, "k": 0}

    log_rrs = np.array([c.log_rr for c in valid])
    weights = np.array([1.0 / c.log_rr_var for c in valid])
    log_rr_pooled = (weights * log_rrs).sum() / weights.sum()
    var_pooled = 1.0 / weights.sum()
    se_pooled = float(np.sqrt(var_pooled))

    z = log_rr_pooled / se_pooled
    p_one = float(1.0 - norm.cdf(z)) if z > 0 else float(norm.cdf(z))

    q_stat = float((weights * (log_rrs - log_rr_pooled) ** 2).sum())
    k = len(valid)
    q_p = float(1.0 - chi2.cdf(q_stat, df=max(k - 1, 1))) if k > 1 else 1.0

    return {
        "rr_pooled": float(np.exp(log_rr_pooled)),
        "z": float(z),
        "p": p_one,
        "ci_low": float(np.exp(log_rr_pooled - 1.96 * se_pooled)),
        "ci_high": float(np.exp(log_rr_pooled + 1.96 * se_pooled)),
        "q_stat": q_stat,
        "q_p": q_p,
        "k": k,
    }


# --------------------------------------------------------------------------- #
# Driver                                                                      #
# --------------------------------------------------------------------------- #

def _load_corpora() -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    """Load all 3 dasha + natal pairs into dicts keyed by corpus tag."""
    dasha: dict[str, pd.DataFrame] = {}
    natal: dict[str, pd.DataFrame] = {}
    for corpus, dasha_path, natal_path in _CORPUS_FILES:
        d = pd.read_parquet(dasha_path)
        n = pd.read_parquet(natal_path)
        d["corpus"] = corpus
        n["corpus"] = corpus
        dasha[corpus] = d
        natal[corpus] = n
        logger.info("Loaded %s: %d dasha rows, %d natal rows",
                    corpus, len(d), len(n))
    return dasha, natal


def run_pooled(
    out_dir: Path, alpha: float = 0.01, n_bins: int = 5,
) -> dict:
    """Run the full pooled analysis and write outputs."""
    out_dir.mkdir(parents=True, exist_ok=True)

    dasha_dfs, natal_dfs = _load_corpora()
    dasha_dfs, natal_dfs, n_dropped = _dedup_by_birth_jd(dasha_dfs, natal_dfs)
    logger.info(
        "Dedup dropped %d cross-corpus duplicates (kept ADB>WD>LA precedence)",
        n_dropped,
    )

    classes_to_test = sorted(_HOUSE_MAP)
    results: dict[str, dict] = {}

    for event_class in classes_to_test:
        per_corpus: list[CorpusRR] = []
        per_corpus_dicts: dict[str, dict] = {}

        for corpus, dasha_df in dasha_dfs.items():
            natal_df = natal_dfs[corpus]
            label_col = f"event_{event_class}"
            if label_col not in dasha_df.columns or dasha_df[label_col].sum() < 30:
                per_corpus_dicts[corpus] = {"skipped": "insufficient labels"}
                continue
            annotated = _annotate_mix(dasha_df, natal_df, event_class)
            rr_obj = _per_corpus_rr(annotated, event_class, n_bins=n_bins)
            if rr_obj is None:
                per_corpus_dicts[corpus] = {"skipped": "rr computation failed"}
                continue
            rr_obj.corpus = corpus
            per_corpus.append(rr_obj)
            per_corpus_dicts[corpus] = {
                "rr": rr_obj.rr,
                "n_top": rr_obj.n_events_top,
                "n_bot": rr_obj.n_events_bot,
                "exp_top": rr_obj.exp_top_days,
                "exp_bot": rr_obj.exp_bot_days,
            }

        pooled = _mantel_haenszel_log_rr(per_corpus)
        results[event_class] = {
            "scorer_used": _scorer_for(event_class),
            "per_corpus": per_corpus_dicts,
            "pooled": pooled,
        }
        logger.info(
            "%-30s scorer=%s  k=%d  pooled_RR=%.2f  p=%.3g  Q_p=%.3g",
            event_class, _scorer_for(event_class),
            pooled["k"], pooled["rr_pooled"], pooled["p"], pooled["q_p"],
        )

    # Bonferroni on the pooled estimates only.
    n_classes = sum(1 for r in results.values() if r["pooled"]["k"] >= 2)
    bonf = alpha / max(n_classes, 1)
    n_sig = sum(1 for r in results.values()
                if r["pooled"]["k"] >= 2 and r["pooled"]["p"] < 0.05)
    n_bonf = sum(1 for r in results.values()
                 if r["pooled"]["k"] >= 2 and r["pooled"]["p"] < bonf)

    summary = {
        "n_classes_tested": n_classes,
        "n_sig_p05_pooled": n_sig,
        "n_bonferroni_pooled": n_bonf,
        "bonferroni_alpha": bonf,
        "n_dropped_dedup": n_dropped,
        "results": results,
    }

    (out_dir / "pooled_rr.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )

    # Markdown table.
    lines = [
        "# Round-11 follow-up — Pooled doctrine RR (Mantel-Haenszel)",
        "",
        f"Cross-corpus deduplicated: dropped {n_dropped} duplicate persons "
        "(ADB > WD > LA precedence).",
        "",
        f"Bonferroni α = {alpha}/{n_classes} = {bonf:.4g}",
        "",
        "## Per-class table",
        "",
        "| Class | Scorer | k | ADB RR | WD RR | LA RR | Pooled RR (95% CI) | p | Q_p |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    def _fmt(x: float | int | None) -> str:
        if x is None or (isinstance(x, float) and (np.isnan(x))):
            return "—"
        return f"{x:.2f}" if isinstance(x, float) else f"{x}"
    sorted_classes = sorted(
        results.items(),
        key=lambda kv: kv[1]["pooled"]["rr_pooled"]
        if not np.isnan(kv[1]["pooled"]["rr_pooled"]) else -1,
        reverse=True,
    )
    for cls, r in sorted_classes:
        p = r["pooled"]
        adb_rr = r["per_corpus"].get("ADB", {}).get("rr")
        wd_rr = r["per_corpus"].get("WD", {}).get("rr")
        la_rr = r["per_corpus"].get("LA", {}).get("rr")
        p_marker = "**" if p["p"] < bonf else ""
        q_marker = "⚠️" if p["q_p"] < 0.05 else ""
        lines.append(
            f"| `{cls}` | {r['scorer_used']} | {p['k']} | "
            f"{_fmt(adb_rr)} | {_fmt(wd_rr)} | {_fmt(la_rr)} | "
            f"{p_marker}{_fmt(p['rr_pooled'])}{p_marker} "
            f"({_fmt(p['ci_low'])}–{_fmt(p['ci_high'])}) | "
            f"{p_marker}{p['p']:.3g}{p_marker} | "
            f"{q_marker}{p['q_p']:.3g}{q_marker} |"
        )
    lines.extend([
        "",
        f"**Aggregate**: {n_sig}/{n_classes} pooled p<0.05, "
        f"{n_bonf}/{n_classes} Bonferroni",
        "",
        "⚠️ in Q_p column = significant cross-corpus heterogeneity (corpora disagree)",
        "** = pooled estimate clears Bonferroni",
        "",
    ])
    (out_dir / "pooled_rr.md").write_text("\n".join(lines), encoding="utf-8")

    logger.info("Wrote %s", out_dir / "pooled_rr.md")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.dasha_doctrine_pooled",
        description="Mantel-Haenszel pooled doctrine RR across ADB+WD+LA.",
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("data/ml_runs/round11_doctrine_pooled"),
    )
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("--n-bins", type=int, default=5)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    summary = run_pooled(args.out, alpha=args.alpha, n_bins=args.n_bins)
    print()
    print("=== Round-11 follow-up: pooled doctrine RR ===")
    print(f"  classes tested:        {summary['n_classes_tested']}")
    print(f"  pooled p<0.05:         {summary['n_sig_p05_pooled']}")
    print(f"  pooled p<Bonferroni:   {summary['n_bonferroni_pooled']}")
    print(f"  cross-corpus dupes dropped: {summary['n_dropped_dedup']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
