"""Certified Cohort — the matched-discordant-pair analysis engine (Phase 2), run on real data.

This is the primary-analysis layer specified in docs/raman_saab/CERTIFIED_COHORT_DESIGN.md §5,
built to run against the *certified* slice of the local corpus: quality-tier A only — AA Rodden
rating AND minute time precision, i.e. birth-certificate-sourced charts. It is outcome-agnostic:
parameterised by (case cohort, control cohort, house, signification, direction), so any future
domain — including the fresh-cohort domains once that data exists — flows through unchanged.

Design (locked in the design doc):
  * CASE vs CONTROL are two labelled cohorts (e.g. divorced vs long-married).
  * Match each case to one control on the CONFOUNDS, never the chart: birth-decade band x
    latitude band x longitude band. Within a matched pair both subjects share era + geography,
    so they still differ in birth time -> ascendant/house cusps/dasha -> the engine's affliction
    score for the mapped house. That residual is the variable under test.
  * Statistic: within-pair concordance = fraction of pairs where the CASE is more afflicted than
    its matched CONTROL in the pre-registered direction (ties split 0.5) == the paired AUC; plus a
    one-sided Wilcoxon signed-rank on the within-pair score difference. Pair-clustered bootstrap CI.
  * SHAM GATE: an off-target house (unrelated to the outcome) must test null BEFORE the real house
    is read — the pipeline-validity check inherited from the astrobank program.

Affliction score per (person, house, signification) from verdicts.parquet, ordinal in [0, 2]:
higher = more favourable, lower = more afflicted (identical mapping to the rest of the program).

Governance: this reuses the astrobank corpus (celebrity, hence still selection-limited — the
matched design controls era+geography+population but NOT celebrity selection itself; that hatch
closes only with the fresh cohort). No engine parameter is tuned from these results. REPORT-ONLY.

Usage:
    py -3.12 -m tools.raman_saab.astrobank.certified_matched_pairs \
        --case H7_DIVORCED --control H7_LONGMARRIAGE \
        --house 7 --signification marital_happiness --direction afflicted \
        --sham-house 10 --sham-signification profession
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

logger = logging.getLogger(__name__)

_STORE: Final = Path("data/astro_databank/derived/raman")
_OUT: Final = _STORE / "certified_matched_pairs_results.json"

# Ordinal affliction score — identical to the mapping used across the program.
_SCORE: Final[dict[tuple[str, str], float]] = {
    ("afflicted", "strong"): 0.0, ("afflicted", "moderate"): 0.17, ("afflicted", "mild"): 0.33,
    ("mixed", "strong"): 1.0, ("mixed", "moderate"): 1.0, ("mixed", "mild"): 1.0,
    ("favourable", "mild"): 1.67, ("favourable", "moderate"): 1.83, ("favourable", "strong"): 2.0,
}

# Matching bands (confound strata, NOT the chart).
_LAT_BINS: Final = [-90, 0, 25, 40, 55, 90]
_LON_BINS: Final = [-180, -60, 0, 60, 120, 180]


def _score_frame(verdicts: pd.DataFrame, house: int, signification: str) -> pd.Series:
    """person_id -> ordinal affliction score for one (house, signification)."""
    sub = verdicts[(verdicts["house"] == house) & (verdicts["signification"] == signification)]
    s = {r.person_id: _SCORE.get((r.verdict, r.degree), np.nan) for r in sub.itertuples()}
    return pd.Series(s, name="score").dropna()


def _build_cohort(
    master: pd.DataFrame, labels: pd.DataFrame, scores: pd.Series,
    case_map: str, control_map: str | None = None, exclude: frozenset[str] = frozenset(),
) -> pd.DataFrame:
    """Certified (tier-A) case+control people with score + matching covariates.

    control_map=None => POOLED control: every certified scored person who is not a case and
    not in ``exclude`` (used for outcomes with no labelled opposite, e.g. prison / suicide).
    """
    by_map = {m: set(g.person_id) for m, g in labels.groupby("map_id")}
    cases = by_map.get(case_map, set())
    score_ids = set(scores.index) & set(master.index)
    if control_map is None:
        controls = score_ids - cases - set(exclude)
    else:
        controls = by_map.get(control_map, set()) - cases          # contradiction -> not a control
    sub = master.loc[sorted((cases | controls) & score_ids)].copy()
    sub = sub[sub["quality_tier"] == "A"]                          # certified: AA + minute
    year = sub["birth_date"].astype(str).str[:4]
    sub = sub[year.str.fullmatch(r"\d{4}")]
    sub["is_case"] = sub.index.isin(cases)
    sub["score"] = sub.index.map(scores).astype(float)
    sub["decade"] = sub["birth_date"].astype(str).str[:4].astype(int) // 10 * 10
    sub["lat_band"] = np.digitize(sub["latitude"].to_numpy(), _LAT_BINS)
    sub["lon_band"] = np.digitize(sub["longitude"].to_numpy(), _LON_BINS)
    out = sub.reset_index()[
        ["person_id", "is_case", "score", "decade", "lat_band", "lon_band"]]
    return out.dropna(subset=["score"])


def _match_pairs(cohort: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Greedy 1:1 matching of cases to controls within (decade, lat_band, lon_band) strata."""
    rng = np.random.default_rng(seed)
    cases = cohort[cohort.is_case].sample(frac=1.0, random_state=seed)
    pool: dict[tuple, list[dict]] = {}
    for r in cohort[~cohort.is_case].itertuples():
        pool.setdefault((r.decade, r.lat_band, r.lon_band), []).append(
            {"person_id": r.person_id, "score": r.score})
    for key in pool:
        rng.shuffle(pool[key])
    pairs = []
    for c in cases.itertuples():
        key = (c.decade, c.lat_band, c.lon_band)
        bucket = pool.get(key)
        if not bucket:
            continue
        ctrl = bucket.pop()
        pairs.append({"case_score": c.score, "control_score": ctrl["score"],
                      "case_id": c.person_id, "control_id": ctrl["person_id"]})
    return pd.DataFrame(pairs)


def _paired_stats(
    pairs: pd.DataFrame, direction: str, n_boot: int = 2000, seed: int = 0,
) -> dict:
    """Within-pair concordance (paired AUC), signed-rank p, pair-clustered bootstrap CI."""
    # 'afflicted' direction: CASE expected MORE afflicted => lower score => case < control.
    delta = pairs["control_score"].to_numpy() - pairs["case_score"].to_numpy()
    if direction != "afflicted":
        delta = -delta
    concord = np.where(delta > 0, 1.0, np.where(delta < 0, 0.0, 0.5))
    point = float(concord.mean())

    nonzero = delta[delta != 0]
    if len(nonzero) >= 10:
        stat, p = wilcoxon(nonzero, alternative="greater")
        p = float(p)
    else:
        stat, p = float("nan"), float("nan")

    rng = np.random.default_rng(seed)
    boots = np.array([concord[rng.integers(0, len(concord), len(concord))].mean()
                      for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n_pairs": int(len(pairs)), "paired_auc": round(point, 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "signed_rank_p": round(p, 4) if p == p else None,
            "case_mean_score": round(float(pairs.case_score.mean()), 4),
            "control_mean_score": round(float(pairs.control_score.mean()), 4)}


def analyze_domain(
    master: pd.DataFrame, labels: pd.DataFrame, verdicts: pd.DataFrame,
    case_map: str, control_map: str | None, house: int, signification: str, direction: str,
    sham_house: int, sham_signification: str,
    exclude: frozenset[str] = frozenset(), n_boot: int = 2000,
) -> dict:
    """Sham-gated matched-pair analysis for one domain against pre-loaded frames."""
    # ── SHAM FIRST (anti-peeking): off-target house must be null ──────────────
    sham_scores = _score_frame(verdicts, sham_house, sham_signification)
    sham_pairs = _match_pairs(_build_cohort(master, labels, sham_scores,
                                            case_map, control_map, exclude))
    sham = _paired_stats(sham_pairs, direction, n_boot=n_boot)
    sham_ok = sham["ci95"][0] <= 0.5 <= sham["ci95"][1]

    # ── REAL target ───────────────────────────────────────────────────────────
    scores = _score_frame(verdicts, house, signification)
    cohort = _build_cohort(master, labels, scores, case_map, control_map, exclude)
    real = _paired_stats(_match_pairs(cohort), direction, n_boot=n_boot)
    n_case, n_ctrl = int(cohort.is_case.sum()), int((~cohort.is_case).sum())

    insufficient = real["n_pairs"] < 30
    passes = (not insufficient and sham_ok and real["ci95"][0] > 0.5
              and (real["signed_rank_p"] or 1.0) < 0.05)
    if insufficient:
        verdict = f"INSUFFICIENT N: only {real['n_pairs']} matched pairs — not interpretable."
    elif passes:
        verdict = (f"SIGNAL: paired AUC {real['paired_auc']} CI{real['ci95']} — mapped-house "
                   "affliction distinguishes the outcome within era+geography-matched certified pairs.")
    else:
        verdict = (f"NULL: paired AUC {real['paired_auc']} CI{real['ci95']} "
                   f"(sham {sham['paired_auc']}, {'gate open' if sham_ok else 'GATE FAILED'}) — "
                   "no distinction within era+geography-matched certified pairs.")

    return {
        "case": case_map, "control": control_map or "__POOLED__",
        "target": {"house": house, "signification": signification, "direction": direction},
        "n_certified_case": n_case, "n_certified_control": n_ctrl,
        "sham_gate": {"house": sham_house, "signification": sham_signification,
                      **sham, "null_gate_open": sham_ok},
        "primary": real, "insufficient_n": insufficient, "verdict": verdict,
    }


def run(
    case_map: str, control_map: str, house: int, signification: str, direction: str,
    sham_house: int, sham_signification: str, n_boot: int = 2000,
) -> dict:
    """Acquire the certified matched-pair dataset and run sham-gated primary analysis."""
    master = pd.read_parquet(_STORE / "person_master.parquet").set_index("person_id")
    labels = pd.read_parquet(_STORE / "labels.parquet")
    verdicts = pd.read_parquet(_STORE / "verdicts.parquet")
    res = analyze_domain(master, labels, verdicts, case_map, control_map, house,
                         signification, direction, sham_house, sham_signification, n_boot=n_boot)
    result = {
        "experiment": "Certified Cohort — matched-discordant-pair (Phase-2 engine on tier-A data)",
        "design_doc": "docs/raman_saab/CERTIFIED_COHORT_DESIGN.md",
        "certification": "quality_tier A only (AA Rodden + minute precision = birth-certificate)",
        "matching": "decade x lat_band x lon_band (confounds only; chart free to vary)",
        "limitation": "celebrity corpus — matched design controls era+geography+population but NOT "
                      "celebrity selection; sex unavailable as a matching key.",
        **res,
    }
    _OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info("wrote %s", _OUT)
    return result


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case", default="H7_DIVORCED")
    ap.add_argument("--control", default="H7_LONGMARRIAGE")
    ap.add_argument("--house", type=int, default=7)
    ap.add_argument("--signification", default="marital_happiness")
    ap.add_argument("--direction", default="afflicted")
    ap.add_argument("--sham-house", type=int, default=10)
    ap.add_argument("--sham-signification", default="profession")
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    res = run(a.case, a.control, a.house, a.signification, a.direction,
              a.sham_house, a.sham_signification, n_boot=a.boot)
    print(json.dumps({k: res[k] for k in
                      ("n_certified_case", "n_certified_control", "sham_gate", "primary",
                       "verdict")}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
