"""Build a dasha-event corpus for the Wikidata 3rd-corpus replication test.

Inputs:
  app/medini/data/wikidata_dated_events.parquet  - from wikidata_dated_events.py

Outputs (two parquets, same shape as the Astro-Databank and lunarastro ones):
  app/medini/data/wikidata_natal_lord_houses.parquet
  app/medini/data/wikidata_dasha_corpus.parquet

Per-person processing:

  1. Birth date is day-precision (Wikidata convention). We default the
     birth time to **12:00 UTC** at the recorded place — degrades the
     ascendant (which the doctrine scorer DOES use via rules_<lord> /
     occ_<lord>), but planet signs (the bulk of the doctrine signal)
     are robust to this.
  2. ``app.core.ephemeris_engine.calculate_all_charts`` is called per
     person to get planet longitudes, signs, and the ascendant. From
     these we derive the same natal_lord_houses schema.
  3. ``mahadasha_sequence`` produces the MD windows; events are
     attributed to whichever window their date falls in.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

from app.core.ephemeris_engine import calculate_all_charts
from app.medini.etl.build_dasha_event_corpus import mahadasha_sequence
from app.medini.etl.build_natal_lord_houses import (
    house_occupied_by,
    houses_aspected_by,
    houses_ruled_by,
)

logger = logging.getLogger(__name__)


_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu")


# Event-class list must match the doctrine scorer's _HOUSE_MAP keys.
_EVENT_CLASSES = (
    "marriage", "relationship", "relationships", "career", "work",
    "fame", "death", "death_cause_unspecified", "death_by_disease",
    "health", "education", "finance", "legal", "personal", "family",
)


def _person_to_chart_inputs(birth_date: str, lat: float, lon: float):
    """Parse 'YYYY-MM-DD' birth_date + lat/lon → calculate_all_charts kwargs.

    Defaults to 12:00 UTC + tz_offset=0 because Wikidata is day-precision.
    """
    y, m, d = (int(x) for x in birth_date.split("-"))
    return dict(
        year=y, month=m, day=d, hour=12, minute=0,
        tz_offset=0.0, latitude=lat, longitude=lon,
    )


def _chart_to_lord_houses(chart: dict, name: str) -> dict:
    """Convert calculate_all_charts dict → natal_lord_houses row."""
    asc = chart.get("ascendant", {})
    asc_sign = asc.get("sign")
    d1 = chart.get("d1", {})
    out: dict[str, object] = {"name_norm": name, "asc_sign": asc_sign}
    for planet in _PLANETS:
        p = d1.get(planet, {})
        sign = p.get("sign")
        lon = p.get("longitude")
        out[f"sign_{planet.lower()}"] = sign if sign else 0
        if not sign or not asc_sign:
            out[f"occ_{planet.lower()}"] = -1
            out[f"rules_{planet.lower()}"] = []
            out[f"aspects_{planet.lower()}"] = []
            continue
        out[f"occ_{planet.lower()}"] = house_occupied_by(sign, asc_sign)
        out[f"rules_{planet.lower()}"] = houses_ruled_by(planet, asc_sign)
        out[f"aspects_{planet.lower()}"] = houses_aspected_by(
            planet, sign, asc_sign,
        )
    out["birth_jd"] = chart.get("birth_jd")
    moon = d1.get("Moon", {})
    out["moon_longitude"] = moon.get("longitude", 0.0)
    return out


def _event_iso_to_jd(date_iso: str) -> float | None:
    """ISO date 'YYYY-MM-DD' → JD UT (noon)."""
    try:
        y, m, d = (int(x) for x in date_iso.split("-"))
        return float(swe.julday(y, m, d, 12.0, swe.GREG_CAL))
    except Exception:
        return None


def build_corpus(events_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (natal_lord_houses_df, dasha_event_corpus_df)."""
    events_df = pd.read_parquet(events_path)
    logger.info("loaded %d event rows", len(events_df))

    # Unique people: one chart per (person_id, birth_date, birth_lat,
    # birth_lon). Wikidata's person_id is unique but a person may have
    # multiple event rows; we want one natal row per person.
    person_keys = events_df.drop_duplicates(
        subset=["person_id", "birth_date", "birth_lat", "birth_lon"],
    ).reset_index(drop=True)
    logger.info("unique people: %d", len(person_keys))

    natal_rows: list[dict] = []
    name_norm_by_id: dict[str, str] = {}
    natal_lookup: dict[str, dict] = {}
    failed = 0
    for i, person in person_keys.iterrows():
        if i % 200 == 0 and i > 0:
            logger.info("natal compute: %d / %d (%d failures)",
                        i, len(person_keys), failed)
        name = (person["person_name"] or person["person_id"] or "").lower().strip()
        if not name:
            continue
        try:
            inp = _person_to_chart_inputs(
                person["birth_date"], person["birth_lat"], person["birth_lon"],
            )
            chart = calculate_all_charts(**inp)
        except Exception as e:
            failed += 1
            continue
        row = _chart_to_lord_houses(chart, name)
        natal_rows.append(row)
        name_norm_by_id[person["person_id"]] = name
        natal_lookup[name] = row

    logger.info("computed %d natal charts (%d failures)", len(natal_rows), failed)

    natal_df = pd.DataFrame(natal_rows).drop_duplicates(subset=["name_norm"])
    # Cast list columns to lists
    for planet in _PLANETS:
        for col in (f"rules_{planet.lower()}", f"aspects_{planet.lower()}"):
            natal_df[col] = natal_df[col].apply(
                lambda x: list(x) if isinstance(x, (list, tuple)) else []
            )

    # Build the dasha corpus: per (name, MD-window) row, labeled by which
    # events fall in the window.
    events_by_name: dict[str, list[tuple[str, float]]] = {}
    for _, e in events_df.iterrows():
        name = name_norm_by_id.get(e["person_id"])
        if not name:
            continue
        jd = _event_iso_to_jd(e["event_date_iso"])
        if jd is None:
            continue
        events_by_name.setdefault(name, []).append((e["event_class"], jd))

    out_rows: list[dict] = []
    for natal_row in natal_rows:
        name = natal_row["name_norm"]
        birth_jd = natal_row.get("birth_jd")
        moon_lon = natal_row.get("moon_longitude")
        if birth_jd is None or moon_lon is None:
            continue
        try:
            windows = mahadasha_sequence(
                float(moon_lon), float(birth_jd), observation_years=100.0,
            )
        except Exception:
            continue
        person_events = events_by_name.get(name, [])
        for win in windows:
            row = {
                "name_norm": name,
                "birth_jd": float(birth_jd),
                "moon_longitude": float(moon_lon),
                "seq_idx": win.seq_idx,
                "dasha_lord": win.lord,
                "dasha_start_jd": win.start_jd,
                "dasha_end_jd": win.end_jd,
                "dasha_duration_years": win.duration_years,
            }
            n_pos = 0
            for cls in _EVENT_CLASSES:
                row[f"event_{cls}"] = 0
            for cls, jd in person_events:
                if win.start_jd <= jd < win.end_jd:
                    col = f"event_{cls}"
                    if col in row:
                        row[col] = 1
                        n_pos += 1
            row["n_events_in_window"] = n_pos
            out_rows.append(row)
    dasha_df = pd.DataFrame(out_rows)

    # Drop columns not needed downstream
    drop = ["birth_jd", "moon_longitude"]
    natal_df_out = natal_df.drop(columns=[c for c in drop if c in natal_df.columns])
    return natal_df_out, dasha_df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.wikidata_dasha_corpus",
    )
    parser.add_argument(
        "--events", type=Path,
        default=Path("app/medini/data/wikidata_dated_events.parquet"),
    )
    parser.add_argument(
        "--out-natal", type=Path,
        default=Path("app/medini/data/wikidata_natal_lord_houses.parquet"),
    )
    parser.add_argument(
        "--out-dasha", type=Path,
        default=Path("app/medini/data/wikidata_dasha_corpus.parquet"),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    natal_df, dasha_df = build_corpus(args.events)
    args.out_natal.parent.mkdir(parents=True, exist_ok=True)
    natal_df.to_parquet(args.out_natal, index=False)
    dasha_df.to_parquet(args.out_dasha, index=False)
    print(f"natal: {args.out_natal} rows={len(natal_df):,}")
    print(f"dasha: {args.out_dasha} rows={len(dasha_df):,} "
          f"unique_people={dasha_df['name_norm'].nunique() if len(dasha_df) else 0:,}")
    for cls in _EVENT_CLASSES:
        col = f"event_{cls}"
        if col in dasha_df.columns:
            n = int(dasha_df[col].sum())
            if n:
                print(f"  {col}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
