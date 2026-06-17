"""Aggregate dated events from every source and report the funnel to the target.

The four importers (`vedastro_events_importer`, `wikidata_events_importer`,
`astrodatabank_xml_importer`, plus the existing LunarAstro events) each emit dated
events in slightly different shapes. This module normalises them to one schema,
enriches missing birth years from the matching persons table, concatenates and
de-duplicates, optionally attaches `person_id` via `match_events_to_charts`, and
reports the **funnel to the power target** — the single number the replication
turns on: how many *auspicious first events in the age band* the combined corpus
yields versus the ~9,000 `replication_preregistration.md` needs.

Normalised event schema: ``name_norm, birth_year, event_class, event_year, source``.

CLI::

    python -m app.medini.etl.aggregate_events \\
        --events wikidata=wd.parquet vedastro=ved_events.csv:ved_persons.csv \\
        --persons persons.parquet --output events_unified.parquet
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from app.medini.etl.match_events_to_charts import attach_person_ids, jd_to_year
from app.medini.etl.resolve_persons_dedup import normalize_name_key
from app.medini.ml.dasha_verse_timing import DOMAINS

logger = logging.getLogger(__name__)

_NORM_COLS = ("name_norm", "birth_year", "event_class", "event_year", "source")
# event_root → analysis event_class (the slim vocabulary the ML layer uses).
_ROOT_TO_CLASS = {
    "marriage": "marriage", "divorce": "divorce",
    "career": "career", "work": "career", "business": "career", "new_job": "career",
    "education": "education",
    "death": "death", "death_cause_unspecified": "death",
}
AUSPICIOUS = tuple(d for d, (aus, _) in DOMAINS.items() if aus)


def normalize_events(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Map any importer's event frame to the normalised schema. `event_class` is
    taken directly if present, else derived from `event_root`/`event_code`.
    `birth_year` is taken if present, else left NA for `enrich_birth_year`."""
    out = pd.DataFrame()
    if "name_norm" in df.columns:
        out["name_norm"] = df["name_norm"].fillna("").astype(str)
    elif "name" in df.columns:
        out["name_norm"] = df["name"].map(normalize_name_key)
    else:
        raise KeyError(f"[{source}] events need 'name_norm' or 'name'")

    if "event_class" in df.columns:
        out["event_class"] = df["event_class"].astype(str)
    else:
        root = df.get("event_root", df.get("event_code"))
        if root is None:
            raise KeyError(f"[{source}] events need 'event_class'/'event_root'")
        out["event_class"] = (root.astype(str).str.lower().str.replace(" ", "_")
                              .map(_ROOT_TO_CLASS).fillna("other"))

    out["event_year"] = pd.to_numeric(df.get("event_year"), errors="coerce").astype("Int64")
    if "birth_year" in df.columns:
        out["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
    elif "birth_jd" in df.columns:
        out["birth_year"] = df["birth_jd"].map(jd_to_year).astype("Int64")
    else:
        out["birth_year"] = pd.array([pd.NA] * len(df), dtype="Int64")
    out["source"] = source
    return out.dropna(subset=["event_year"]).reset_index(drop=True)


def enrich_birth_year(events: pd.DataFrame, persons: pd.DataFrame) -> pd.DataFrame:
    """Fill missing `birth_year` by joining same-source events to their persons on
    `name_norm` (unique names only — ambiguous names stay NA)."""
    nn = (persons["name"].map(normalize_name_key) if "name_norm" not in persons
          else persons["name_norm"])
    yr = (persons["birth_year"] if "birth_year" in persons
          else persons["birth_jd"].map(jd_to_year))
    lut = pd.DataFrame({"name_norm": nn, "birth_year": yr}).dropna()
    counts = lut.groupby("name_norm")["birth_year"].nunique()
    unique = lut[lut["name_norm"].isin(counts[counts == 1].index)]
    m = dict(zip(unique["name_norm"], unique["birth_year"].astype(int)))
    filled = events["birth_year"].copy()
    need = filled.isna()
    filled.loc[need] = events.loc[need, "name_norm"].map(m).astype("Int64")
    out = events.copy()
    out["birth_year"] = filled
    return out


def aggregate(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=_NORM_COLS)
    df = pd.concat(frames, ignore_index=True)
    # collapse the same event reported by multiple sources.
    return df.drop_duplicates(
        subset=["name_norm", "birth_year", "event_class", "event_year"]
    ).reset_index(drop=True)


def funnel(events: pd.DataFrame, *, target: int = 9000) -> dict:
    """Auspicious first-events in the age band — the power-target estimand."""
    e = events.dropna(subset=["birth_year"]).copy()
    e["age"] = e["event_year"].astype(int) - e["birth_year"].astype(int)
    in_band = pd.Series(False, index=e.index)
    for dom in AUSPICIOUS:
        lo, hi = DOMAINS[dom][1]
        in_band |= (e["event_class"] == dom) & e["age"].between(lo, hi)
    aus = e[in_band]
    # first event per (person, class) ≈ the estimand the replication counts.
    first = aus.drop_duplicates(subset=["name_norm", "birth_year", "event_class"])
    by_source = aus.groupby("source").size().to_dict()
    by_class = aus.groupby("event_class").size().to_dict()
    return {
        "total_events": len(events),
        "with_birth_year": int(events["birth_year"].notna().sum()),
        "auspicious_in_band": len(aus),
        "auspicious_first_events": len(first),
        "target": target,
        "fraction_of_target": round(len(first) / target, 3),
        "by_source": {k: int(v) for k, v in by_source.items()},
        "by_class": {k: int(v) for k, v in by_class.items()},
    }


def build(events_frames: list[pd.DataFrame], output: Path,
          persons: pd.DataFrame | None = None, *, target: int = 9000) -> dict:
    agg = aggregate(events_frames)
    report = {"funnel_raw": funnel(agg, target=target)}
    if persons is not None:
        matched, mstats = attach_person_ids(agg, persons)
        report["match"] = mstats
        report["funnel_matched"] = funnel(matched, target=target)
        agg = matched
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".csv":
        agg.to_csv(output, index=False)
    else:
        agg.to_parquet(output, index=False)
    return report


def _load_one(spec: str) -> pd.DataFrame:
    """`name=eventspath[:personspath]` → a normalised (and enriched) event frame."""
    src, _, paths = spec.partition("=")
    ev_path, _, persons_path = paths.partition(":")
    raw = (pd.read_parquet(ev_path) if ev_path.endswith(".parquet")
           else pd.read_csv(ev_path))
    norm = normalize_events(raw, src)
    if persons_path:
        pp = (pd.read_parquet(persons_path) if persons_path.endswith(".parquet")
              else pd.read_csv(persons_path))
        norm = enrich_birth_year(norm, pp)
    return norm


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m app.medini.etl.aggregate_events",
        description="Merge all dated-event sources and report the funnel to target.")
    p.add_argument("--events", nargs="+", required=True,
                   help="source specs 'name=events[:persons]' (persons enriches birth_year)")
    p.add_argument("--persons", type=Path, default=None,
                   help="persons table for person_id matching (optional)")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--target", type=int, default=9000)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    frames = [_load_one(s) for s in args.events]
    persons = pd.read_parquet(args.persons) if args.persons else None
    report = build(frames, args.output, persons, target=args.target)
    logger.info("funnel: %s", report.get("funnel_matched", report["funnel_raw"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
