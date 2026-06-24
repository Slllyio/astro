"""Round 8.5 Repair 1: build proper screening cohorts.

The pre-existing event_corpus_round5_all.parquet has THREE structural
problems documented in CRITICAL_REVIEW_R8.md:
  1. event-positive only (no negative class; only is_event=1 rows)
  2. selection bias (only 5,084 notable people from astro-databank)
  3. era-confounded (60-year birth-decade gap between event classes)

This script rebuilds, per event class, a binary screening cohort:
  - POSITIVES: people with at least one event of class X (with date)
  - NEGATIVES: era-matched random people sampled from the 85k unused
    natal universe who DO NOT appear in events_all.csv
  - One row per unique person (no row-level duplication)
  - Pure-natal features (535 cols from ml_astro_15k.parquet) — no
    transit features, since negatives have no event time

Output: app/medini/data/screening_<class>.parquet per event class.

Usage:
    python -m app.medini.etl.build_screening_cohort --class Marriage --neg-ratio 2
    python -m app.medini.etl.build_screening_cohort --all
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NATAL_PARQUET = Path("app/medini/data/ml_astro_15k.parquet")
EVENTS_CSV = Path("data/astro_databank/events_all.csv")
BIRTH_DATA_CSV = Path("data/astro_databank/merged_all.csv")
OUTPUT_DIR = Path("app/medini/data/")
SEED = 42

# Per-class matching strategy: some classes (e.g. Marriage) live as a
# subtype under a different event_root (Relationship). Counts here are
# UNIQUE PEOPLE with dated events in events_all.csv as of 2026-05-20.
CLASS_DEFS: dict[str, dict] = {
    "Work":                           {"match_by": "root",    "value": "Work",                           "n_people": 466},
    "Death, Cause unspecified":       {"match_by": "root",    "value": "Death, Cause unspecified",       "n_people": 1645},
    "Relationship":                   {"match_by": "root",    "value": "Relationship",                   "n_people": 540},
    "Published/ Exhibited/ Released": {"match_by": "subtype", "value": "Published/ Exhibited/ Released", "n_people": 115},
    "Prize":                          {"match_by": "subtype", "value": "Prize",                          "n_people": 145},
    "Family":                         {"match_by": "root",    "value": "Family",                         "n_people": 208},
    "fame":                           {"match_by": "root",    "value": "fame",                           "n_people": 1953},
    "career":                         {"match_by": "root",    "value": "career",                         "n_people": 1901},
    "Death by Disease":               {"match_by": "root",    "value": "Death by Disease",               "n_people": 493},
    "Marriage":                       {"match_by": "subtype", "value": "Marriage",                       "n_people": 523},
}
TOP_10_EVENT_CLASSES = list(CLASS_DEFS.keys())


def _norm_name(s):
    return str(s).strip()


def _load_birth_dates() -> pd.DataFrame:
    df = pd.read_csv(BIRTH_DATA_CSV, low_memory=False)
    df["name_norm"] = df["name"].astype(str).str.strip()
    df["birth_dt"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
    df["birth_year"] = df["birth_dt"].dt.year
    df["birth_decade"] = (df["birth_year"] // 10 * 10).astype("Int64")
    # de-dupe by name (keep first)
    df = df.drop_duplicates(subset=["name_norm"], keep="first")
    return df[["name_norm", "birth_dt", "birth_year", "birth_decade"]]


def _load_natal_universe(birth_df: pd.DataFrame) -> pd.DataFrame:
    natal = pd.read_parquet(NATAL_PARQUET)
    natal["name_norm"] = natal["name"].astype(str).str.strip()
    # Join birth date
    natal = natal.merge(birth_df, on="name_norm", how="left")
    # Drop charts with no birth date (can't era-stratify)
    natal = natal.dropna(subset=["birth_decade"])
    natal["birth_decade"] = natal["birth_decade"].astype(int)
    # De-dupe by name (some natal charts appear multiple times)
    natal = natal.drop_duplicates(subset=["name_norm"], keep="first").reset_index(drop=True)
    return natal


def _load_events() -> pd.DataFrame:
    ev = pd.read_csv(EVENTS_CSV, low_memory=False)
    ev["name_norm"] = ev["name"].astype(str).str.strip()
    ev["event_root_norm"] = ev["event_root"].astype(str).str.strip()
    ev["event_dt"] = pd.to_datetime(ev["event_date"], errors="coerce")
    return ev


def build_cohort_for_class(
    target_class: str,
    *,
    neg_ratio: float = 2.0,
    require_event_date: bool = True,
) -> pd.DataFrame:
    """Build the screening cohort for one event class.

    Returns a per-person parquet:
      - all natal feature cols
      - `name`, `birth_dt`, `birth_year`, `birth_decade`
      - `is_event_X`: 1 if person had ≥1 event of class X (with date if
        require_event_date), 0 if person never had any event in
        events_all.csv (i.e. drawn from the 77k unused negative pool).

    Era-stratified negative sampling: for each birth-decade bucket of
    positives, sample neg_ratio × n_positives from natal-universe
    negatives in that same decade.
    """
    birth_df = _load_birth_dates()
    natal = _load_natal_universe(birth_df)
    events = _load_events()

    logger.info("Natal universe with birth date: %d people", len(natal))
    logger.info("events_all: %d rows, %d unique people",
                len(events), events["name_norm"].nunique())

    # POSITIVES: people who had ≥1 event of target_class
    # Class matching strategy: by event_root OR by event_subtype (see CLASS_DEFS).
    cls_def = CLASS_DEFS.get(target_class, {"match_by": "root", "value": target_class})
    if cls_def["match_by"] == "subtype":
        events["event_subtype_norm"] = events["event_subtype"].astype(str).str.strip()
        pos_event_mask = events["event_subtype_norm"] == cls_def["value"]
        logger.info("Matching '%s' as event_subtype", cls_def["value"])
    else:
        pos_event_mask = events["event_root_norm"] == cls_def["value"]
        logger.info("Matching '%s' as event_root", cls_def["value"])
    if require_event_date:
        pos_event_mask &= events["event_dt"].notna()
    positive_names = set(events.loc[pos_event_mask, "name_norm"])
    logger.info("'%s': %d people with ≥1 event of this class",
                target_class, len(positive_names))

    # All people with ANY event in events_all (these can't be negatives)
    any_event_names = set(events["name_norm"])
    logger.info("Total people with any event: %d", len(any_event_names))

    # Negative pool: natal-universe people with NO event in events_all
    negative_pool_mask = ~natal["name_norm"].isin(any_event_names)
    neg_pool = natal[negative_pool_mask].copy()
    logger.info("Negative pool (natal-only, no events): %d people", len(neg_pool))

    # Positives present in natal universe
    pos_mask = natal["name_norm"].isin(positive_names)
    positives = natal[pos_mask].copy()
    positives["is_event_X"] = 1
    logger.info("Positives in natal universe: %d", len(positives))

    if len(positives) == 0:
        raise ValueError(f"No positives found in natal universe for class '{target_class}'")

    # Era-stratified negative sampling
    rng = np.random.default_rng(SEED)
    neg_samples = []
    for decade, group in positives.groupby("birth_decade"):
        n_neg_wanted = int(len(group) * neg_ratio)
        neg_in_decade = neg_pool[neg_pool["birth_decade"] == decade]
        if len(neg_in_decade) == 0:
            logger.warning("Decade %d has %d positives but 0 negative pool — skipping decade",
                           decade, len(group))
            continue
        n_neg = min(n_neg_wanted, len(neg_in_decade))
        sampled = neg_in_decade.sample(n=n_neg, random_state=rng.integers(1e9))
        neg_samples.append(sampled)

    negatives = pd.concat(neg_samples, ignore_index=True) if neg_samples else pd.DataFrame()
    negatives["is_event_X"] = 0
    logger.info("Negatives sampled (era-matched): %d", len(negatives))

    # Combine
    cohort = pd.concat([positives, negatives], ignore_index=True)
    cohort["target_class"] = target_class
    cohort["neg_ratio"] = neg_ratio

    # Sanity: era distribution should now be similar between pos and neg
    logger.info("\nEra distribution sanity check:")
    for decade in sorted(cohort["birth_decade"].unique()):
        p = ((cohort["birth_decade"] == decade) & (cohort["is_event_X"] == 1)).sum()
        n = ((cohort["birth_decade"] == decade) & (cohort["is_event_X"] == 0)).sum()
        if p > 0 or n > 0:
            logger.info("  %d: %d pos, %d neg  (ratio %.2f)",
                        decade, p, n, n / max(p, 1))

    return cohort.reset_index(drop=True)


def build_all(neg_ratio: float = 2.0):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for cls in TOP_10_EVENT_CLASSES:
        logger.info("\n========== Building cohort for: %s ==========", cls)
        cohort = build_cohort_for_class(cls, neg_ratio=neg_ratio)
        safe = "".join(c if c.isalnum() else "_" for c in cls).strip("_").lower()
        out_path = OUTPUT_DIR / f"screening_{safe}.parquet"
        cohort.to_parquet(out_path, index=False)
        logger.info("Wrote %s (%d rows × %d cols, %d positives)",
                    out_path, len(cohort), cohort.shape[1],
                    int(cohort["is_event_X"].sum()))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.medini.etl.build_screening_cohort")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--class", dest="target_class", type=str, help="Single event class to build")
    g.add_argument("--all", action="store_true", help="Build cohorts for all top-10 classes")
    parser.add_argument("--neg-ratio", type=float, default=2.0,
                        help="Negatives per positive (era-matched). Default 2.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    if args.all:
        build_all(neg_ratio=args.neg_ratio)
    else:
        cohort = build_cohort_for_class(args.target_class, neg_ratio=args.neg_ratio)
        safe = "".join(c if c.isalnum() else "_" for c in args.target_class).strip("_").lower()
        out = OUTPUT_DIR / f"screening_{safe}.parquet"
        cohort.to_parquet(out, index=False)
        print(f"Wrote {out} ({len(cohort)} rows × {cohort.shape[1]} cols)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
