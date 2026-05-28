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
LA_NATAL_FILE: Final = "lunarastro_natal.parquet"
LA_DASHA_FILE: Final = "lunarastro_dasha_corpus.parquet"
EVENT_TAXONOMY_FILE: Final = "event_class_taxonomy.parquet"

def _normalize_event_root(raw: str) -> str:
    """Convert ADB title-case event_root to snake_case granular_class key.

    Example: ``"Death of Mate"`` → ``"death_of_mate"``,
    ``"Death, Cause unspecified"`` → ``"death_cause_unspecified"``.
    Keeps the result aligned with ``event_class_taxonomy.granular_class``
    so the canonical taxonomy is the single source of truth for harmonized
    mapping.
    """
    import re
    s = (raw or "").lower().strip()
    s = re.sub(r"[,/]", "", s)        # drop commas + slashes
    s = re.sub(r"\s+", "_", s)        # collapse whitespace to underscore
    s = re.sub(r"_+", "_", s)         # collapse runs of underscores
    return s.strip("_")


def _load_canonical_event_class_map(taxonomy_path: Path) -> dict[str, str]:
    """Load granular_class → harmonized_class from the taxonomy parquet."""
    if not taxonomy_path.exists():
        return {}
    tax = pd.read_parquet(
        taxonomy_path, columns=["granular_class", "harmonized_class"],
    )
    return dict(zip(tax["granular_class"], tax["harmonized_class"]))


# ADB-specific raw event_root strings NOT covered by the canonical taxonomy
# (the taxonomy was built from dasha_mdadpd_corpus's pre-aggregated 56
# classes; ADB event_corpus_all has finer-grained Round-9-era strings).
# These overrides apply AFTER _normalize_event_root + taxonomy lookup.
_ADB_RAW_EVENT_ROOT_OVERRIDES: Final[dict[str, str]] = {
    "divorce_dates":              "marriage",
    "new_job":                    "career",
    "new_career":                 "career",
    "begin_major_project":        "career",
    "end_a_program_of_study":     "career",
    "published_exhibited_released": "fame",
    "prize":                      "fame",
    "gain_social_status":         "fame",
}

# Legacy inline mapping retained for backward compatibility — now derived
# from canonical taxonomy + ADB-specific overrides at module-load time.
# DEPRECATED: prefer reading event_class_taxonomy.parquet directly in new code.
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
    "birth_time_confidence",  # 0.0=unknown, 0.2=approx, 1.0=Rodden A/AA; NULL where source has no flag
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
    "event_date_precision",  # "day" | "approx_window_midpoint"
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
        # ADB is Rodden-rated AA/A/B/C/X/XX but the rating isn't carried
        # forward by the upstream ETL. All ADB persons here passed the
        # AA/A quality filter, so treat as full confidence.
        "birth_time_confidence": pd.Series([1.0] * len(df), dtype="Float64"),
        "source": "astro_databank",
    })
    return persons.drop_duplicates("person_id").reset_index(drop=True)


def load_adb_events(
    events_path: Path, taxonomy_path: Path | None = None,
) -> pd.DataFrame:
    """Read ADB event corpus, project down to relational schema only.

    Harmonizes ``event_root`` to the 6-class vocabulary via:
      1. _normalize_event_root → snake_case granular_class
      2. canonical event_class_taxonomy.parquet lookup
      3. _ADB_RAW_EVENT_ROOT_OVERRIDES for Round-9 strings not covered
      4. fallback to "other"
    """
    df = pd.read_parquet(events_path, columns=[
        "name", "birth_jd", "event_date", "event_root", "event_subtype",
    ])
    df = df[df["event_date"].notna()].copy()
    canonical_map = (
        _load_canonical_event_class_map(taxonomy_path)
        if taxonomy_path is not None else {}
    )
    def _map(raw: str) -> str:
        normalised = _normalize_event_root(raw)
        if normalised in canonical_map:
            return canonical_map[normalised]
        if normalised in _ADB_RAW_EVENT_ROOT_OVERRIDES:
            return _ADB_RAW_EVENT_ROOT_OVERRIDES[normalised]
        return "other"
    return pd.DataFrame({
        "person_id": df["birth_jd"].map(_adb_person_id),
        "event_class": df["event_root"].map(_map).astype("string"),
        "event_root": df["event_root"].astype("string"),
        "event_subtype": df["event_subtype"].astype("string"),
        "event_date": _to_iso_date_string(df["event_date"]),
        "event_date_precision": "day",  # ADB events Rodden-rated to the day
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
        # Wikidata stores only birth_date (day precision). No time-of-birth
        # is available, so confidence is 0.0 (unknown time).
        "birth_time_confidence": pd.Series([0.0] * len(df), dtype="Float64"),
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
        "event_date_precision": "day",  # Wikidata events are day-precision
        "event_label": df["event_label"].astype("string"),
        "source": "wikidata",
    })


# --------------------------------------------------------------------------- #
# Lunarastro lineage                                                          #
# --------------------------------------------------------------------------- #

def _la_person_id(name_norm: str) -> str:
    """Stable id from the lunarastro normalised name.

    Matches the synthetic id convention already used in person_id_map.parquet
    so any downstream join keeps working after LA persons are promoted.
    """
    return f"LA:{name_norm}"


def load_la_persons(natal_path: Path) -> pd.DataFrame:
    """Read lunarastro natal data, dedupe by name_norm, project to canonical schema.

    Some persons appear in lunarastro_natal.parquet with multiple birth_time
    variants (uncertainty). We keep the row with the highest
    ``birth_time_confidence`` per name_norm (ties broken by first occurrence).
    """
    df = pd.read_parquet(natal_path, columns=[
        "name_norm", "date_of_birth", "birth_time",
        "latitude", "longitude", "tz_offset_used", "birth_time_confidence",
    ])
    # Keep highest-confidence row per person.
    df = (df.sort_values(["name_norm", "birth_time_confidence"],
                         ascending=[True, False])
            .drop_duplicates("name_norm", keep="first")
            .reset_index(drop=True))

    # Compute birth_jd from (date, time, tz_offset). Same convention as the
    # core ephemeris engine: local time minus tz → UTC, then swe.julday.
    import swisseph as swe
    def _to_jd(row: dict) -> float | None:
        date_str = row.get("date_of_birth")
        time_str = row.get("birth_time")
        tz = row.get("tz_offset_used")
        if date_str is None or pd.isna(date_str) or tz is None or pd.isna(tz):
            return None
        try:
            y, m, d = str(date_str).split("-")
            if time_str is None or pd.isna(time_str):
                hour = 12.0
            else:
                h, mi, *_ = str(time_str).split(":")
                hour = int(h) + int(mi) / 60.0
            return swe.julday(int(y), int(m), int(d), hour - float(tz), swe.GREG_CAL)
        except (ValueError, AttributeError):
            return None
    birth_jds = df.to_dict("records")
    df["birth_jd"] = [_to_jd(r) for r in birth_jds]

    return pd.DataFrame({
        "person_id": df["name_norm"].map(_la_person_id),
        "name": df["name_norm"].astype("string"),
        "birth_date": _to_iso_date_string(df["date_of_birth"]),
        "birth_time": df["birth_time"].astype("string"),
        "birth_lat": df["latitude"].astype("float64"),
        "birth_lon": df["longitude"].astype("float64"),
        "tz_offset": df["tz_offset_used"].astype("float64"),
        "birth_jd": df["birth_jd"].astype("float64"),
        # LA carries an explicit ∈ {0.0, 0.2, 1.0} confidence flag from
        # its source. Preserve directly so downstream weighting can use it.
        "birth_time_confidence": df["birth_time_confidence"].astype("Float64"),
        "source": "lunarastro",
    }).reset_index(drop=True)


def load_la_events(
    dasha_path: Path, taxonomy_path: Path | None = None,
) -> pd.DataFrame:
    """Pivot the LA dasha corpus's wide per-window event flags into long form.

    LA's source data records events as binary flags per (person, dasha
    window). We treat each fired flag as one event whose canonical date
    is the **midpoint of the dasha window**. This conservatively assigns
    an event_jd that always falls inside the window it came from, so the
    downstream `events_with_dasha` join always succeeds.

    If ``taxonomy_path`` is provided, ``event_class`` is mapped to the
    harmonized 6-class vocabulary via event_class_taxonomy.parquet.
    Otherwise the raw LA class names are kept.
    """
    df = pd.read_parquet(dasha_path)
    event_cols = [c for c in df.columns if c.startswith("event_")
                  and c not in ("event_root", "event_subtype")]
    if not event_cols:
        return pd.DataFrame()

    if taxonomy_path is not None and taxonomy_path.exists():
        tax = pd.read_parquet(taxonomy_path)
        granular_to_harmonized = dict(
            zip(tax["granular_class"], tax["harmonized_class"])
        )
    else:
        granular_to_harmonized = {}

    # Pivot wide-to-long: one row per fired flag.
    df["_midpoint_jd"] = (df["dasha_start_jd"] + df["dasha_end_jd"]) / 2.0
    keep = ["name_norm", "_midpoint_jd"]
    long_df = df[keep + event_cols].melt(
        id_vars=keep, value_vars=event_cols,
        var_name="event_root_full", value_name="fired",
    )
    long_df = long_df[long_df["fired"] > 0].reset_index(drop=True)
    long_df["event_root"] = long_df["event_root_full"].str.removeprefix("event_")
    long_df["event_class"] = (
        long_df["event_root"]
        .map(granular_to_harmonized)
        .fillna("other")
    )

    import swisseph as swe
    def _jd_to_iso(jd: float) -> str | None:
        if jd is None or pd.isna(jd):
            return None
        try:
            y, m, d, _ = swe.revjul(float(jd), swe.GREG_CAL)
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        except (ValueError, OverflowError):
            return None
    long_df["event_date"] = long_df["_midpoint_jd"].map(_jd_to_iso)

    return pd.DataFrame({
        "person_id": "LA:" + long_df["name_norm"].astype(str),
        "event_class": long_df["event_class"].astype("string"),
        "event_root": long_df["event_root"].astype("string"),
        "event_subtype": pd.Series([pd.NA] * len(long_df), dtype="string"),
        "event_date": long_df["event_date"].astype("string"),
        # LA events have approximate dates (midpoint of the dasha window
        # in which the flag fired). Downstream code can filter or weight
        # accordingly: ``WHERE event_date_precision = 'day'`` for the
        # subset of Rodden-rated / day-precision events.
        "event_date_precision": "approx_window_midpoint",
        "event_label": pd.Series([pd.NA] * len(long_df), dtype="string"),
        "source": "lunarastro",
    })


# --------------------------------------------------------------------------- #
# Build                                                                       #
# --------------------------------------------------------------------------- #

def build_tables(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the unified persons + events tables across all 3 corpora.

    Notes:
    - LA persons come with full birth metadata (date/time/lat/lon/tz) from
      ``lunarastro_natal.parquet`` and are first-class Silver residents.
    - LA does NOT contribute to ``events.parquet`` yet — the Round-9 LA
      dasha corpus stores events as per-window binary flags rather than
      per-event records, so it needs a separate promotion path (TODO).
    """
    adb_persons = load_adb_persons(data_dir / ADB_BIRTH_FILE)
    wd_persons = load_wd_persons(data_dir / WD_EVENTS_FILE)
    la_persons = (
        load_la_persons(data_dir / LA_NATAL_FILE)
        if (data_dir / LA_NATAL_FILE).exists()
        else pd.DataFrame(columns=PERSON_COLS)
    )
    adb_events = load_adb_events(
        data_dir / ADB_EVENTS_FILE,
        taxonomy_path=data_dir / EVENT_TAXONOMY_FILE,
    )
    wd_events = load_wd_events(data_dir / WD_EVENTS_FILE)
    la_events = (
        load_la_events(data_dir / LA_DASHA_FILE,
                       taxonomy_path=data_dir / EVENT_TAXONOMY_FILE)
        if (data_dir / LA_DASHA_FILE).exists()
        else pd.DataFrame()
    )

    persons = pd.concat(
        [adb_persons, wd_persons, la_persons], ignore_index=True,
    )
    persons = persons[list(PERSON_COLS)]

    events = pd.concat([adb_events, wd_events, la_events], ignore_index=True)
    events = events[events["person_id"].isin(set(persons["person_id"]))].copy()
    events.insert(0, "event_id", range(len(events)))
    events = events[list(EVENT_COLS)]

    logger.info(
        "Built %d persons (ADB=%d, WD=%d, LA=%d), %d events (ADB=%d, WD=%d, LA=%d)",
        len(persons), len(adb_persons), len(wd_persons), len(la_persons),
        len(events), len(adb_events), len(wd_events), len(la_events),
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
