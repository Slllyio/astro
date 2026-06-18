"""Adapter: build canonical Silver `persons.parquet` + `events.parquet` from the
two corpora we collected this session (VedAstro + geocoded ASTROCRM).

The canonical Silver pipeline (`build_charts_table` → `build_dasha_windows` →
`build_event_dasha_join` → `resolve_persons_dedup` → `build_duckdb_catalog` →
`materialize_gold_views` → `validate_silver_layer`) all consume the Tier-0
`persons`/`events` tables — only `build_person_event_tables` was coupled to the
absent Round-9 source parquets. This adapter fills that one gap from our CSVs so
the rest of the validated pipeline runs unchanged.

Inputs (produced earlier this session):
  data/astro_databank/raw.csv          VedAstro persons  (name/dob/time/lat/lon/tz/rodden/categories)
  data/astro_databank/raw_astrocrm.csv geocoded ASTROCRM persons (same schema)
  data/astro_databank/events.csv       ASTROCRM dated events (name/event_root/event_subtype/event_date/...)

Outputs (canonical Tier-0 schema, see docs/data_dictionary.md):
  app/medini/data/persons.parquet      one row per chart (PK person_id)
  app/medini/data/events.parquet       one row per dated event (FK person_id)

Reuses the canonical schema + event-class harmonization from
`build_person_event_tables` so there's a single source of truth for both.

CLI:
    python -m app.medini.etl.build_silver_from_corpora
    python -m app.medini.etl.build_silver_from_corpora --data-dir app/medini/data
"""
from __future__ import annotations

import argparse
import logging
import re
import unicodedata
from pathlib import Path
from typing import Final

import pandas as pd

from app.core.ephemeris_engine import calculate_jd
from app.medini.etl.build_person_event_tables import (
    EVENT_COLS,
    PERSON_COLS,
    _ADB_RAW_EVENT_ROOT_OVERRIDES,
    _load_canonical_event_class_map,
    _normalize_event_root,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
DEFAULT_RAW_DIR: Final = Path("data/astro_databank")
EVENT_TAXONOMY_FILE: Final = "event_class_taxonomy.parquet"

# (raw.csv filename, source label, person_id prefix)
_CORPORA: Final = (
    ("raw.csv", "vedastro", "VA"),
    ("raw_astrocrm.csv", "astrocrm", "AC"),
    ("raw_holos.csv", "holos", "HO"),
)

# Rodden rating → birth_time_confidence (mirrors the ADB convention: AA/A are
# the timed, trustworthy ratings).
_RODDEN_CONFIDENCE: Final = {"AA": 1.0, "A": 1.0, "B": 0.2}


def _name_norm(name: str) -> str:
    """Normalized join/key form: accent-stripped, lowercased, single-spaced.

    Used identically for persons and events so the event→person join is exact.
    """
    s = unicodedata.normalize("NFKD", str(name or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    return re.sub(r"\s+", " ", s)


def _decimal_hour(time_str: str) -> float:
    """'HH:MM:SS' → decimal hours; missing/garbage → 12.0 (noon)."""
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", str(time_str or "").strip())
    if not m:
        return 12.0
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    return h + mi / 60.0 + s / 3600.0


def _confidence(rodden: str) -> float:
    return _RODDEN_CONFIDENCE.get(str(rodden or "").strip().upper(), 0.0)


def build_persons(raw_dir: Path) -> pd.DataFrame:
    """Union the corpora into the canonical persons schema (PK person_id)."""
    frames: list[pd.DataFrame] = []
    for filename, source, prefix in _CORPORA:
        path = raw_dir / filename
        if not path.exists():
            logger.warning("skipping missing corpus %s", path)
            continue
        df = pd.read_csv(path, dtype=str).fillna("")
        rows: list[dict] = []
        skipped = 0
        for r in df.itertuples(index=False):
            d = r._asdict() if hasattr(r, "_asdict") else dict(zip(df.columns, r))
            date = (d.get("date_of_birth") or "").strip()
            lat, lon, tz = d.get("latitude"), d.get("longitude"), d.get("tz_offset")
            if not date or not lat or not lon or tz in (None, ""):
                skipped += 1
                continue
            try:
                y, m, day = (int(x) for x in date.split("-"))
                # Sanity gate: reject implausible years (e.g. holos ships the
                # mythological "Thema Mundi" at year 6050) so every person yields
                # a computable chart and the charts 1:1 contract holds.
                if not (1 <= y <= 2100):
                    skipped += 1
                    continue
                jd = calculate_jd(y, m, day, _decimal_hour(d.get("time_of_birth")), float(tz))
            except (ValueError, TypeError):
                skipped += 1
                continue
            rows.append({
                "person_id": f"{prefix}:{jd:.4f}",
                "name": _name_norm(d.get("name")),
                "birth_date": date,
                "birth_time": (d.get("time_of_birth") or "").strip() or pd.NA,
                "birth_lat": float(lat),
                "birth_lon": float(lon),
                "tz_offset": float(tz),
                "birth_jd": jd,
                "birth_time_confidence": _confidence(d.get("rodden_rating")),
                "source": source,
            })
        logger.info("%s: %d persons (%d skipped for missing fields)", source, len(rows), skipped)
        frames.append(pd.DataFrame(rows))

    persons = pd.concat(frames, ignore_index=True)
    persons["birth_time_confidence"] = persons["birth_time_confidence"].astype("Float64")
    # Dedup by chart identity; ASTROCRM kept ahead of VedAstro on collision so the
    # event names (ASTROCRM lineage) resolve to their own corpus.
    persons["_src_rank"] = (persons["source"] != "astrocrm").astype(int)
    persons = (
        persons.sort_values("_src_rank")
        .drop_duplicates("person_id")
        .drop(columns="_src_rank")
        .reset_index(drop=True)
    )
    return persons[list(PERSON_COLS)]


def build_events(
    raw_dir: Path, persons: pd.DataFrame, taxonomy_path: Path | None,
) -> pd.DataFrame:
    """Read events.csv, link to persons by normalized name, harmonize classes."""
    path = raw_dir / "events.csv"
    df = pd.read_csv(path, dtype=str).fillna("")
    df = df[df["event_date"].str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)].copy()

    # name → person_id. ASTROCRM (the corpus the events were extracted from)
    # takes precedence, then holos, then vedastro.
    name_to_id: dict[str, str] = {}
    for src_pref in ("astrocrm", "holos", "vedastro"):
        sub = persons[persons["source"] == src_pref]
        for name, pid in zip(sub["name"], sub["person_id"]):
            name_to_id.setdefault(name, pid)

    canonical_map = (
        _load_canonical_event_class_map(taxonomy_path) if taxonomy_path else {}
    )

    def _class(raw: str) -> str:
        norm = _normalize_event_root(raw)
        return canonical_map.get(norm) or _ADB_RAW_EVENT_ROOT_OVERRIDES.get(norm, "other")

    df["person_id"] = df["name"].map(_name_norm).map(name_to_id)
    orphans = int(df["person_id"].isna().sum())
    df = df[df["person_id"].notna()].copy()

    events = pd.DataFrame({
        "event_id": range(len(df)),
        "person_id": df["person_id"].to_numpy(),
        "event_class": df["event_root"].map(_class).to_numpy(),
        "event_root": df["event_root"].to_numpy(),
        "event_subtype": df["event_subtype"].replace("", pd.NA).to_numpy(),
        "event_date": df["event_date"].to_numpy(),
        "event_date_precision": "day",
        "event_label": pd.NA,
        "source": "astro_databank",
    })
    logger.info(
        "events: %d linked, %d orphans dropped, %d classes",
        len(events), orphans, events["event_class"].nunique(),
    )
    return events[list(EVENT_COLS)]


def build(data_dir: Path = DEFAULT_DATA_DIR, raw_dir: Path = DEFAULT_RAW_DIR) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)
    persons = build_persons(raw_dir)
    taxonomy_path = data_dir / EVENT_TAXONOMY_FILE
    events = build_events(raw_dir, persons, taxonomy_path if taxonomy_path.exists() else None)

    persons.to_parquet(data_dir / "persons.parquet", index=False)
    events.to_parquet(data_dir / "events.parquet", index=False)

    stats = {
        "persons": len(persons),
        "events": len(events),
        "persons_by_source": persons["source"].value_counts().to_dict(),
        "event_classes": events["event_class"].value_counts().to_dict(),
    }
    logger.info("wrote persons.parquet (%d) + events.parquet (%d)", len(persons), len(events))
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.build_silver_from_corpora",
        description="Build canonical persons + events parquets from the collected corpora.",
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    print(build(args.data_dir, args.raw_dir))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
