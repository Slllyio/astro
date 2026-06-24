"""Pull dated life events from Wikidata via SPARQL.

3rd-corpus replication test for the Round-9 doctrine work. Independent
of both Astro-Databank (the original signal) and lunarastro (the
replication-fail corpus). Wikidata gives clean STRUCTURED data:

  * P569 (date of birth) — usually day-precision; occasionally hour
  * P19  (place of birth) — resolves to lat/lon
  * P26  (spouse)         — with "start time" / "end time" qualifiers
  * P166 (award received) — with "point in time" qualifier
  * P39  (position held)  — with "start time" qualifier
  * P570 (date of death)

We pull humans (Q5) with at least one dated event in [1700, 2030].
Day-precision births mean the ascendant has ±12h uncertainty (could be
wrong by 1-2 signs); this degrades house assignment but sign-based
predictions (the bulk of the doctrine signal) remain robust.

Output:
  app/medini/data/wikidata_dated_events.parquet  — one row per (person, event_class, date)

Two output schemas in one file:
  - 'person_id', 'person_name', 'birth_date', 'birth_lat', 'birth_lon'
  - 'event_class', 'event_date_iso' (per dated event)

A separate ETL (wikidata_dasha_corpus.py) joins these into MD-window form.

Strategy: WDQS has 60s timeout. We use SMALL batched queries (~500 records
each) split by birth-year decade to avoid timeouts.

Usage:
    python -m app.medini.etl.wikidata_dated_events
    python -m app.medini.etl.wikidata_dated_events --max-records 5000
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)


# Wikidata Query Service SPARQL endpoint.
_WDQS_URL = "https://query.wikidata.org/sparql"
_USER_AGENT = "astro-doctrine-replication/1.0 (https://github.com/example/astro)"

# Per-decade SPARQL queries, ONE PER EVENT TYPE.
#
# The original combined OPTIONAL query (death + award + position + spouse
# in one shot) caused 504 Gateway Timeout — too many cross-product
# bindings. Splitting into separate queries per event type keeps each
# under 60s.
#
# Each query returns: (person, name, birth_date, place_coords, event_date,
# event_label_if_any). The event class is filled in client-side based on
# which query produced the row.

_QUERY_DEATH = """
SELECT ?person ?personLabel ?birthDate ?deathDate ?coords WHERE {{
  ?person wdt:P31 wd:Q5;
          wdt:P569 ?birthDate;
          wdt:P570 ?deathDate;
          wdt:P19/wdt:P625 ?coords.
  FILTER(YEAR(?birthDate) >= {year_start} && YEAR(?birthDate) < {year_end})
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit}
"""

_QUERY_AWARD = """
SELECT ?person ?personLabel ?birthDate ?coords ?awardTime ?awardLabel WHERE {{
  ?person wdt:P31 wd:Q5;
          wdt:P569 ?birthDate;
          wdt:P19/wdt:P625 ?coords;
          p:P166 ?awardStmt.
  ?awardStmt ps:P166 ?award;
             pq:P585 ?awardTime.
  ?award rdfs:label ?awardLabel.
  FILTER(LANG(?awardLabel) = "en")
  FILTER(YEAR(?birthDate) >= {year_start} && YEAR(?birthDate) < {year_end})
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit}
"""

_QUERY_POSITION = """
SELECT ?person ?personLabel ?birthDate ?coords ?positionStart ?positionLabel WHERE {{
  ?person wdt:P31 wd:Q5;
          wdt:P569 ?birthDate;
          wdt:P19/wdt:P625 ?coords;
          p:P39 ?positionStmt.
  ?positionStmt ps:P39 ?position;
                pq:P580 ?positionStart.
  ?position rdfs:label ?positionLabel.
  FILTER(LANG(?positionLabel) = "en")
  FILTER(YEAR(?birthDate) >= {year_start} && YEAR(?birthDate) < {year_end})
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit}
"""

_QUERY_SPOUSE = """
SELECT ?person ?personLabel ?birthDate ?coords ?marriageStart ?marriageEnd WHERE {{
  ?person wdt:P31 wd:Q5;
          wdt:P569 ?birthDate;
          wdt:P19/wdt:P625 ?coords;
          p:P26 ?spouseStmt.
  ?spouseStmt ps:P26 ?spouse.
  OPTIONAL {{ ?spouseStmt pq:P580 ?marriageStart. }}
  OPTIONAL {{ ?spouseStmt pq:P582 ?marriageEnd. }}
  FILTER(BOUND(?marriageStart) || BOUND(?marriageEnd))
  FILTER(YEAR(?birthDate) >= {year_start} && YEAR(?birthDate) < {year_end})
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit}
"""

# Map Wikidata event categories to doctrine event classes.
# These match the classes used in dasha_doctrine_score._HOUSE_MAP.
_AWARD_FAME_KEYWORDS: tuple[str, ...] = (
    "nobel", "pulitzer", "oscar", "academy award", "grammy", "emmy",
    "prize", "medal", "knight", "order of", "fellow", "laureate",
)
_POSITION_FAME_KEYWORDS: tuple[str, ...] = (
    "president", "prime minister", "senator", "governor", "mayor",
    "minister", "ambassador", "ceo", "chairman", "director",
)


def _coord_to_latlon(coord_str: str) -> tuple[float, float] | None:
    """Parse a Wikidata Point coord literal: 'Point(<lon> <lat>)'."""
    m = re.match(r"Point\(([-\d.]+)\s+([-\d.]+)\)", coord_str)
    if not m:
        return None
    return float(m.group(2)), float(m.group(1))  # (lat, lon)


def _date_to_iso(date_str: str | None) -> str | None:
    """Wikidata dates are like '+1879-03-14T00:00:00Z'; strip + and time."""
    if not date_str:
        return None
    m = re.match(r"^\+?(\d{4}-\d{2}-\d{2})", date_str)
    return m.group(1) if m else None


def _award_to_event_class(award_label: str) -> str:
    label = (award_label or "").lower()
    for kw in _AWARD_FAME_KEYWORDS:
        if kw in label:
            return "fame"
    return "fame"  # All awards default to fame for this purpose


def _position_to_event_class(position_label: str) -> str:
    label = (position_label or "").lower()
    for kw in _POSITION_FAME_KEYWORDS:
        if kw in label:
            return "fame"
    return "career"


def _run_sparql(query: str) -> list[dict]:
    """Run a SPARQL query. Retries 2x on 5xx errors; gives up if WDQS
    keeps timing out (some queries are inherently too heavy).
    """
    last_err: Exception | None = None
    for attempt in range(2):
        try:
            resp = requests.get(
                _WDQS_URL,
                params={"query": query, "format": "json"},
                headers={
                    "Accept": "application/sparql-results+json",
                    "User-Agent": _USER_AGENT,
                },
                timeout=70,
            )
            if resp.status_code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["results"]["bindings"]
        except (requests.HTTPError, requests.Timeout, requests.ConnectionError) as e:
            last_err = e
            logger.warning("SPARQL attempt %d failed: %s", attempt + 1, e)
            time.sleep(5 * (attempt + 1))
    if last_err is not None:
        logger.warning("SPARQL gave up: %s", last_err)
    return []


def _parse_death(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        pid = r.get("person", {}).get("value", "").rsplit("/", 1)[-1]
        name = r.get("personLabel", {}).get("value", "")
        birth = _date_to_iso(r.get("birthDate", {}).get("value"))
        death = _date_to_iso(r.get("deathDate", {}).get("value"))
        coords = _coord_to_latlon(r.get("coords", {}).get("value", ""))
        if not (pid and birth and death and coords):
            continue
        out.append({
            "person_id": pid, "person_name": name, "birth_date": birth,
            "birth_lat": coords[0], "birth_lon": coords[1],
            "event_class": "death_cause_unspecified",
            "event_date_iso": death, "event_label": "",
        })
    return out


def _parse_award(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        pid = r.get("person", {}).get("value", "").rsplit("/", 1)[-1]
        name = r.get("personLabel", {}).get("value", "")
        birth = _date_to_iso(r.get("birthDate", {}).get("value"))
        coords = _coord_to_latlon(r.get("coords", {}).get("value", ""))
        award_time = _date_to_iso(r.get("awardTime", {}).get("value"))
        award_label = r.get("awardLabel", {}).get("value", "")
        if not (pid and birth and coords and award_time):
            continue
        out.append({
            "person_id": pid, "person_name": name, "birth_date": birth,
            "birth_lat": coords[0], "birth_lon": coords[1],
            "event_class": _award_to_event_class(award_label),
            "event_date_iso": award_time, "event_label": award_label,
        })
    return out


def _parse_position(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        pid = r.get("person", {}).get("value", "").rsplit("/", 1)[-1]
        name = r.get("personLabel", {}).get("value", "")
        birth = _date_to_iso(r.get("birthDate", {}).get("value"))
        coords = _coord_to_latlon(r.get("coords", {}).get("value", ""))
        pos_start = _date_to_iso(r.get("positionStart", {}).get("value"))
        pos_label = r.get("positionLabel", {}).get("value", "")
        if not (pid and birth and coords and pos_start):
            continue
        out.append({
            "person_id": pid, "person_name": name, "birth_date": birth,
            "birth_lat": coords[0], "birth_lon": coords[1],
            "event_class": _position_to_event_class(pos_label),
            "event_date_iso": pos_start, "event_label": pos_label,
        })
    return out


def _parse_spouse(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        pid = r.get("person", {}).get("value", "").rsplit("/", 1)[-1]
        name = r.get("personLabel", {}).get("value", "")
        birth = _date_to_iso(r.get("birthDate", {}).get("value"))
        coords = _coord_to_latlon(r.get("coords", {}).get("value", ""))
        m_start = _date_to_iso(r.get("marriageStart", {}).get("value"))
        m_end = _date_to_iso(r.get("marriageEnd", {}).get("value"))
        if not (pid and birth and coords):
            continue
        if m_start:
            out.append({
                "person_id": pid, "person_name": name, "birth_date": birth,
                "birth_lat": coords[0], "birth_lon": coords[1],
                "event_class": "marriage", "event_date_iso": m_start,
                "event_label": "",
            })
        if m_end:
            out.append({
                "person_id": pid, "person_name": name, "birth_date": birth,
                "birth_lat": coords[0], "birth_lon": coords[1],
                "event_class": "relationships", "event_date_iso": m_end,
                "event_label": "",
            })
    return out


def fetch_corpus(
    *,
    year_start: int = 1850,
    year_end: int = 2000,
    per_decade_limit: int = 800,
) -> pd.DataFrame:
    """Fetch dated-events corpus from Wikidata.

    Runs four separate SPARQL queries per decade (death, award, position,
    marriage) and concatenates the results. Each query is simpler than
    the combined version, avoiding the 504 timeout.
    """
    all_records: list[dict] = []
    decades = list(range(year_start, year_end, 10))
    for y in decades:
        for query_name, query_tmpl, parser in (
            ("death", _QUERY_DEATH, _parse_death),
            ("award", _QUERY_AWARD, _parse_award),
            ("position", _QUERY_POSITION, _parse_position),
            ("spouse", _QUERY_SPOUSE, _parse_spouse),
        ):
            q = query_tmpl.format(
                year_start=y, year_end=y + 10, limit=per_decade_limit,
            )
            rows = _run_sparql(q)
            records = parser(rows)
            logger.info(
                "decade %d %s: %d bindings -> %d events",
                y, query_name, len(rows), len(records),
            )
            all_records.extend(records)
            time.sleep(0.5)  # polite throttle
    df = pd.DataFrame(all_records)
    if len(df):
        logger.info(
            "total events: %d across %d unique people",
            len(df), df["person_id"].nunique(),
        )
    else:
        logger.info("total events: 0")
    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.wikidata_dated_events",
    )
    parser.add_argument("--year-start", type=int, default=1850)
    parser.add_argument("--year-end", type=int, default=2000)
    parser.add_argument("--per-decade-limit", type=int, default=800)
    parser.add_argument(
        "--output", type=Path,
        default=Path("app/medini/data/wikidata_dated_events.parquet"),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    df = fetch_corpus(
        year_start=args.year_start,
        year_end=args.year_end,
        per_decade_limit=args.per_decade_limit,
    )
    if df.empty:
        print("WARNING: empty corpus")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.output, index=False)
    print()
    print(f"=== Wikidata corpus written ===")
    print(f"  file: {args.output}")
    print(f"  rows: {len(df):,}")
    print(f"  unique people: {df['person_id'].nunique():,}")
    print(f"  events by class:")
    for cls, n in df["event_class"].value_counts().items():
        print(f"    {cls:<30} {n:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
