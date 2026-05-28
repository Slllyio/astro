"""Build a star-schema (persons + events) from the two scraped corpora.

The repo currently stores person/event data in two long-format parquets per
corpus, with denormalized chart features mixed in. This ETL extracts the
pure relational core:

  - ``persons.parquet`` : one row per person  (PK = person_id)
  - ``events.parquet``  : one row per dated event  (FK person_id -> persons)

person_id namespacing keeps the two corpora cleanly separable without a
fuzzy-name dedup step (which is out of scope for v1):

  - ``ADB:<birth_jd:.4f>`` for Astro-Databank lineage
    (birth_jd is preserved to 4 decimals -- ~9 seconds of TT, well below
    the time-of-birth precision in the source data)
  - ``WD:<Q-number>``      for Wikidata persons

Events carry the raw ``event_root`` / ``event_subtype`` from ADB AND a
harmonized ``event_class`` mapped to the same 5-value vocabulary used by
the Wikidata pull (marriage, career, fame, death, relationships) plus
unmapped overflow as ``other``. Both raw and harmonized are kept so
downstream code can pick the granularity it wants.

Usage:
    python -m app.medini.etl.build_person_event_tables
    python -m app.medini.etl.build_person_event_tables --out-dir app/medini/data
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)


def _to_iso_date_string(s: pd.Series) -> pd.Series:
    """Return a string Series of YYYY-MM-DD dates.

    Why not ``pd.to_datetime(s).dt.date``: pandas Timestamps are
    nanosecond-precision and overflow for any date before 1677 or after
    2262. ADB contains historical figures (e.g. born 1665), so we keep
    dates as strings end-to-end.
    """
    out = s.astype("string").str.slice(0, 10)
    # ``.astype("string")`` on a column with NaN produces the literal string
    # 'nan'; coerce back to NA so downstream filters like ``.notna()`` work.
    return out.where(out != "nan", pd.NA)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
ADB_BIRTH_FILE: Final = "dasha_corpus_birth_data.parquet"
ADB_EVENTS_FILE: Final = "event_corpus_all.parquet"
WD_EVENTS_FILE: Final = "wikidata_dated_events.parquet"

# Map ADB event_root strings (free-form, ~50 distinct values) onto the
# harmonized 5-value taxonomy used by Wikidata. Unmapped roots fall through
# to 'other' and the raw root is preserved in event_root for granular work.
ADB_EVENT_ROOT_TO_CLASS: Final[dict[str, str]] = {
    "Marriage": "marriage",
    "Divorce dates": "marriage",
    "Relationship": "relationships",
    "Family": "relationships",
    "Death of Mate": "relationships",
    "Death of Father": "relationships",
    "Death of Mother": "relationships",
    "Death of Sibling": "relationships",
    "Death of Child": "relationships",
    "Death, Cause unspecified": "death_cause_unspecified",
    "Death by Disease": "death_cause_unspecified",
    "Death": "death_cause_unspecified",
    "Death by Accident": "death_cause_unspecified",
    "Death by Suicide": "death_cause_unspecified",
    "Death by Homicide": "death_cause_unspecified",
    "Work": "career",
    "New Job": "career",
    "New Career": "career",
    "career": "career",
    "Begin Major Project": "career",
    "End a program of study": "career",
    "Published/ Exhibited/ Released": "fame",
    "Prize": "fame",
    "fame": "fame",
    "Gain social status": "fame",
}

# Person column order (canonical).
PERSON_COLS: Final = (
    "person_id",
    "name",
    "birth_date",
    "birth_time",
    "birth_lat",
    "birth_lon",
    "tz_offset",
    "birth_jd",
    "source",
)

# Event column order (canonical).
EVENT_COLS: Final = (
    "event_id",
    "person_id",
    "event_class",
    "event_root",
    "event_subtype",
    "event_date",
    "event_label",
    "source",
)


# --------------------------------------------------------------------------- #
# ADB lineage (Astro-Databank Rodden-rated births)                            #
# --------------------------------------------------------------------------- #

def _adb_person_id(birth_jd: float) -> str:
    """Stable per-chart id from Julian Day (4 decimals ~= 9 sec TT)."""
    return f"ADB:{birth_jd:.4f}"


def load_adb_persons(birth_path: Path) -> pd.DataFrame:
    """Read ADB birth data, return one row per chart in canonical schema."""
    df = pd.read_parquet(birth_path)
    persons = pd.DataFrame({
        "person_id": df["birth_jd"].map(_adb_person_id),
        "name": df["name_norm"].astype("string"),
        "birth_date": _to_iso_date_string(df["date_of_birth"]),
        "birth_time": df["time_of_birth"].astype("string"),
        "birth_lat": df["latitude"].astype("float64"),
        "birth_lon": df["longitude"].astype("float64"),
        "tz_offset": df["tz_offset"].astype("float64"),
        "birth_jd": df["birth_jd"].astype("float64"),
        "source": "astro_databank",
    })
    return persons.drop_duplicates("person_id").reset_index(drop=True)


def load_adb_events(events_path: Path) -> pd.DataFrame:
    """Read ADB event corpus, project down to relational schema only."""
    df = pd.read_parquet(events_path, columns=[
        "name", "birth_jd", "event_date", "event_root", "event_subtype",
    ])
    df = df[df["event_date"].notna()].copy()
    return pd.DataFrame({
        "person_id": df["birth_jd"].map(_adb_person_id),
        "event_class": df["event_root"].map(ADB_EVENT_ROOT_TO_CLASS).fillna("other"),
        "event_root": df["event_root"].astype("string"),
        "event_subtype": df["event_subtype"].astype("string"),
        "event_date": _to_iso_date_string(df["event_date"]),
        "event_label": df["name"].astype("string"),  # ADB has no separate label, use person name
        "source": "astro_databank",
    })


# --------------------------------------------------------------------------- #
# Wikidata lineage                                                            #
# --------------------------------------------------------------------------- #

def _wd_person_id(qid: str) -> str:
    """Stable id from Wikidata Q-number."""
    return f"WD:{qid}"


def load_wd_persons(events_path: Path) -> pd.DataFrame:
    """Wikidata stores birth fields denormalized on every event row.

    Collapse to one row per person and project to canonical schema.
    """
    df = pd.read_parquet(events_path, columns=[
        "person_id", "person_name", "birth_date", "birth_lat", "birth_lon",
    ])
    # Reset index after dedup: drop_duplicates keeps original (gapped) index,
    # which would outer-align with the fresh-index pd.Series([NA]*len(df))
    # below and resurrect dropped rows as NaN.
    df = df.drop_duplicates("person_id").reset_index(drop=True)
    return pd.DataFrame({
        "person_id": df["person_id"].map(_wd_person_id),
        "name": df["person_name"].astype("string"),
        "birth_date": _to_iso_date_string(df["birth_date"]),
        "birth_time": pd.Series([pd.NA] * len(df), dtype="string"),
        "birth_lat": df["birth_lat"].astype("float64"),
        "birth_lon": df["birth_lon"].astype("float64"),
        "tz_offset": pd.Series([pd.NA] * len(df), dtype="Float64"),
        "birth_jd": pd.Series([pd.NA] * len(df), dtype="Float64"),
        "source": "wikidata",
    }).reset_index(drop=True)


def load_wd_events(events_path: Path) -> pd.DataFrame:
    """Project Wikidata events to canonical schema (already long-format)."""
    df = pd.read_parquet(events_path, columns=[
        "person_id", "event_class", "event_date_iso", "event_label",
    ])
    return pd.DataFrame({
        "person_id": df["person_id"].map(_wd_person_id),
        "event_class": df["event_class"].astype("string"),
        "event_root": df["event_class"].astype("string"),  # WD has no raw root, mirror class
        "event_subtype": pd.Series([pd.NA] * len(df), dtype="string"),
        "event_date": _to_iso_date_string(df["event_date_iso"]),
        "event_label": df["event_label"].astype("string"),
        "source": "wikidata",
    })


# --------------------------------------------------------------------------- #
# Build                                                                       #
# --------------------------------------------------------------------------- #

def build_tables(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the unified persons + events tables from both corpora."""
    adb_persons = load_adb_persons(data_dir / ADB_BIRTH_FILE)
    wd_persons = load_wd_persons(data_dir / WD_EVENTS_FILE)
    adb_events = load_adb_events(data_dir / ADB_EVENTS_FILE)
    wd_events = load_wd_events(data_dir / WD_EVENTS_FILE)

    persons = pd.concat([adb_persons, wd_persons], ignore_index=True)
    persons = persons[list(PERSON_COLS)]

    events = pd.concat([adb_events, wd_events], ignore_index=True)
    events = events[events["person_id"].isin(set(persons["person_id"]))].copy()
    events.insert(0, "event_id", range(len(events)))
    events = events[list(EVENT_COLS)]

    logger.info(
        "Built %d persons (ADB=%d, WD=%d), %d events (ADB=%d, WD=%d)",
        len(persons), len(adb_persons), len(wd_persons),
        len(events), len(adb_events), len(wd_events),
    )
    return persons, events


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help="Directory holding source + output parquets.")
    parser.add_argument("--out-dir", type=Path, default=None,
                        help="Output dir (defaults to --data-dir).")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s | %(message)s")

    out_dir = args.out_dir or args.data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    persons, events = build_tables(args.data_dir)
    persons.to_parquet(out_dir / "persons.parquet", index=False)
    events.to_parquet(out_dir / "events.parquet", index=False)
    logger.info("Wrote %s and %s", out_dir / "persons.parquet", out_dir / "events.parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
