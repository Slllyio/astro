"""Gauntlet G2 — clean re-run of the WD marriage chart-lift (+0.043) with a geography arm.

Pre-registered in tools/raman_saab/astrobank/GAUNTLET_PREREG.md. The original
(xgboost_date_disambiguation, Round 11) found chart features add +0.043 AUC over an
explicit cyclic-date baseline and called it "REAL SIGNAL". This re-run keeps the exact
dataset builder (identical cohort n=32,932, identical label, identical 28 chart columns)
and closes the remaining holes:

  1. GEOGRAPHY CONFOUND (the new decisive arm). Condition B controlled date but not
     place. Every chart in this corpus is time_precision='day' / birth_time_confidence=0
     (verified 2026-07-24): all charts were cast at a default clock time, so asc_sign and
     all 9 *_house columns are deterministic functions of (birth_date, birth_place) — no
     birth-time information exists anywhere in the corpus. Wikidata marriage-documentation
     rates vary by country, and chart columns can reconstruct geography. Arms:
        B  = birth_jd + cyclic date                    (original baseline, replication)
        G  = B + birth_lat + birth_lon                 (geography baseline — NEW)
        D  = B + 28 chart columns                      (original chart arm, replication)
        DG = G + 28 chart columns                      (decisive arm)
     Pre-registered decision: the prereg success criterion "chart-arm AUC − era/date-
     baseline AUC > 0 with person-grouped bootstrap CI excluding 0" is evaluated on
     DG − G. If the CI includes 0, the +0.043 is a geography confound and G2 falls.
     NOTE (interpretation lock, stated before computation): because the corpus contains
     zero real birth times, even a surviving DG − G lift is a nonlinear date x place
     encoding, NOT birth-time astrology. tz_offset is 100% missing and excluded.

  2. PERSON GROUPING. charts.parquet is verified one-row-per-person (75,149 unique
     person_ids in 75,149 rows), so StratifiedKFold on rows IS person-disjoint here;
     asserted at runtime rather than assumed.

  3. SEED SENSITIVITY + PROPER CI. 5 seeds x 5 folds; out-of-fold predictions averaged
     per person across seeds; 2,000-resample person bootstrap on the paired AUC lifts
     (rows == persons, so the row bootstrap IS the person-grouped bootstrap).

Usage:
    py -3.12 -m app.medini.ml.gauntlet_g2_marriage
    py -3.12 -m app.medini.ml.gauntlet_g2_marriage --seeds 5 --folds 5 --boot 2000
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

import xgboost as xgb

from app.medini.ml.xgboost_date_disambiguation import (
    _CHART_COLS,
    _CYCLIC_DATE_COLS,
    _build_wikidata_marriage_dataset,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
DEFAULT_OUT: Final = Path("data/ml_runs/gauntlet/g2_marriage_clean.json")

_GEO_COLS: Final[list[str]] = ["birth_lat", "birth_lon"]


def _arms(df: pd.DataFrame) -> dict[str, tuple[str, np.ndarray]]:
    """Assemble the four pre-registered feature matrices from the merged frame."""
    base = df[["birth_jd"] + _CYCLIC_DATE_COLS].to_numpy(dtype=float)
    geo = df[_GEO_COLS].to_numpy(dtype=float)
    chart = df[_CHART_COLS].to_numpy(dtype=float)
    return {
        "B": ("birth_jd + cyclic date (original baseline)", base),
        "G": ("B + lat/lon (geography baseline)", np.hstack([base, geo])),
        "D": ("B + 28 chart cols (original chart arm)", np.hstack([base, chart])),
        "DG": ("G + 28 chart cols (decisive arm)", np.hstack([base, geo, chart])),
    }


def _oof_predict(X: np.ndarray, y: np.ndarray, seed: int, folds: int) -> np.ndarray:
    """One seed's out-of-fold predicted probabilities (person-disjoint by construction)."""
    oof = np.full(len(y), np.nan)
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    for train_idx, test_idx in skf.split(X, y):
        model = xgb.XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.1,
            n_jobs=-1, random_state=seed, eval_metric="auc", verbosity=0,
        )
        model.fit(X[train_idx], y[train_idx])
        oof[test_idx] = model.predict_proba(X[test_idx])[:, 1]
    if np.isnan(oof).any():
        raise RuntimeError("out-of-fold coverage incomplete")  # every row must be scored
    return oof


def _fast_auc(y: np.ndarray, s: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney), fast enough for the 2,000-resample bootstrap."""
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=float)
    ranks[order] = np.arange(1, len(s) + 1)
    # midranks for ties
    sorted_s = s[order]
    i = 0
    while i < len(sorted_s):
        j = i
        while j + 1 < len(sorted_s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def _bootstrap_lift(
    y: np.ndarray, s_a: np.ndarray, s_b: np.ndarray, n_boot: int, seed: int,
) -> tuple[float, float, float]:
    """Person-bootstrap 95% CI on AUC(s_a) − AUC(s_b); rows are persons (asserted upstream)."""
    rng = np.random.default_rng(seed)
    n = len(y)
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        yb = y[idx]
        if yb.sum() == 0 or yb.sum() == len(yb):  # degenerate resample
            diffs[b] = np.nan
            continue
        diffs[b] = _fast_auc(yb, s_a[idx]) - _fast_auc(yb, s_b[idx])
    diffs = diffs[~np.isnan(diffs)]
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(np.mean(diffs)), float(lo), float(hi)


def run_gauntlet_g2(
    data_dir: Path = DEFAULT_DATA_DIR,
    out_path: Path = DEFAULT_OUT,
    n_seeds: int = 5,
    n_folds: int = 5,
    n_boot: int = 2000,
) -> dict:
    """Execute the four-arm clean re-run and write the verdict JSON."""
    df = _build_wikidata_marriage_dataset(data_dir)

    # Person-disjointness guarantee (audit CRITICAL #1 — verified, not assumed)
    if not df["person_id"].is_unique:
        raise RuntimeError("charts corpus is not one-row-per-person; GroupKFold required")

    # Geography join from the Silver persons table (person_id keys — never names)
    persons = pd.read_parquet(
        data_dir / "persons.parquet", columns=["person_id"] + _GEO_COLS,
    )
    df = df.merge(persons, on="person_id", how="left", validate="one_to_one")
    if df[_GEO_COLS].isna().any().any():
        raise RuntimeError("missing birth_lat/birth_lon after person_id join")

    y = df["label"].to_numpy(dtype=int)
    arms = _arms(df)
    logger.info("n=%d  positive_rate=%.3f  arms=%s", len(y), y.mean(), list(arms))

    # ── per-arm OOF predictions, averaged over seeds ─────────────────────────
    seed_aucs: dict[str, list[float]] = {k: [] for k in arms}
    mean_oof: dict[str, np.ndarray] = {}
    for key, (desc, X) in arms.items():
        acc = np.zeros(len(y))
        for seed in range(n_seeds):
            oof = _oof_predict(X, y, seed=seed, folds=n_folds)
            seed_aucs[key].append(round(roc_auc_score(y, oof), 6))
            acc += oof
        mean_oof[key] = acc / n_seeds
        logger.info("arm %-2s (%s): seed AUCs %s", key, desc, seed_aucs[key])

    # ── paired person-bootstrap CIs on the two pre-registered lifts ──────────
    lifts = {}
    for name, (a, b) in {
        "D_minus_B_replication": ("D", "B"),
        "DG_minus_G_decisive": ("DG", "G"),
        "G_minus_B_geography_share": ("G", "B"),
    }.items():
        point = roc_auc_score(y, mean_oof[a]) - roc_auc_score(y, mean_oof[b])
        bmean, lo, hi = _bootstrap_lift(y, mean_oof[a], mean_oof[b], n_boot, seed=0)
        lifts[name] = {
            "point": round(float(point), 6),
            "boot_mean": round(bmean, 6),
            "ci95": [round(lo, 6), round(hi, 6)],
            "excludes_zero": bool(lo > 0 or hi < 0),
        }
        logger.info("%s: %+.4f  CI(%+.4f, %+.4f)", name, point, lo, hi)

    decisive = lifts["DG_minus_G_decisive"]
    if decisive["point"] > 0 and decisive["excludes_zero"]:
        verdict = (
            "SURVIVES GEOGRAPHY: chart columns add signal beyond date+place. "
            "Interpretation lock applies — with zero real birth times in the corpus this "
            "is a nonlinear date x place encoding, not birth-time astrology."
        )
    else:
        verdict = (
            "FALLS: the chart-feature lift does not survive the geography baseline. "
            "The Round-11 +0.043 'REAL SIGNAL' is attributable to birth-place "
            "information leaking through default-time chart columns."
        )

    result = {
        "experiment": "Gauntlet G2 — WD marriage chart-lift, geography-controlled clean re-run",
        "prereg": "tools/raman_saab/astrobank/GAUNTLET_PREREG.md (G2)",
        "n_persons": int(len(y)),
        "positive_rate": round(float(y.mean()), 6),
        "time_precision_all_day": True,
        "tz_offset_excluded_all_missing": True,
        "protocol": {
            "seeds": n_seeds, "folds": n_folds, "bootstrap": n_boot,
            "split": "StratifiedKFold on rows == persons (uniqueness asserted)",
            "model": "XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1)",
        },
        "arms": {k: {"desc": d, "n_features": int(X.shape[1]),
                     "seed_aucs": seed_aucs[k],
                     "mean_auc": round(float(np.mean(seed_aucs[k])), 6)}
                 for k, (d, X) in arms.items()},
        "lifts": lifts,
        "prior_result": {"lift_D_over_B": 0.042889, "verdict": "REAL SIGNAL",
                         "source": "data/ml_runs/round11_disambiguation/disambiguation_v1.json"},
        "verdict": verdict,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info("wrote %s", out_path)
    return result


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    result = run_gauntlet_g2(n_seeds=args.seeds, n_folds=args.folds, n_boot=args.boot)
    print(json.dumps({k: result[k] for k in ("arms", "lifts", "verdict")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
