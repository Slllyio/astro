"""Scrape a death-timing validation corpus from Wikidata.

Pulls humans (``wdt:P31 wd:Q5``) who have **day-precision** date of birth
(``P569``) and date of death (``P570``) plus a birthplace with coordinates
(``P19``/``P625``). Day precision is enforced via the statement node's
``wikibase:timePrecision = 11`` so we never ingest a year-only date silently.

Wikidata has essentially no birth *times*, so this corpus supports the
house-independent death-timing tests (Vimshottari dasha of the death karaka)
but NOT ascendant/house-based maraka rules — exactly the WD limitation
documented in docs/death_timing_findings.md §6. Birth time is unknown, so
charts are computed at a chosen hour (default 12:00 local) and the validation
runs a birth-time sensitivity sweep on top.

Queries are bucketed by birth-year window to stay under the WDQS ~60s limit,
then deduped by QID.

Usage:
    python -m app.medini.etl.wikidata_death_corpus \
        --out app/medini/data/raman_saab/death_corpus.parquet \
        --start-year 1850 --end-year 1955 --bucket 3 --limit-per-bucket 2500
"""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_ENDPOINT = "https://query.wikidata.org/sparql"
_UA = "astro-raman-validation/0.1 (research; population death-timing validation)"

_QUERY_TMPL = """
SELECT ?person ?personLabel ?dob ?dod ?lat ?lon WHERE {{
  ?person wdt:P31 wd:Q5 ;
          p:P569/psv:P569 ?dobn ;
          p:P570/psv:P570 ?dodn ;
          wdt:P19 ?bp .
  ?dobn wikibase:timeValue ?dob ; wikibase:timePrecision ?dobp .
  ?dodn wikibase:timeValue ?dod ; wikibase:timePrecision ?dodp .
  ?bp wdt:P625 ?coord .
  BIND(geof:latitude(?coord) AS ?lat)
  BIND(geof:longitude(?coord) AS ?lon)
  FILTER(?dobp = 11 && ?dodp = 11)
  FILTER(YEAR(?dob) >= {y0} && YEAR(?dob) < {y1})
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit}
"""


def _fetch_bucket(y0: int, y1: int, limit: int, retries: int = 3) -> list[dict]:
    query = _QUERY_TMPL.format(y0=y0, y1=y1, limit=limit)
    for attempt in range(retries):
        try:
            r = requests.get(
                _ENDPOINT,
                params={"query": query, "format": "json"},
                headers={"User-Agent": _UA},
                timeout=120,
            )
            if r.status_code == 429:
                wait = 5 * (attempt + 1)
                logger.warning("429 rate-limited on %d-%d; sleep %ds", y0, y1, wait)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()["results"]["bindings"]
        except Exception as exc:  # noqa: BLE001
            wait = 3 * (attempt + 1)
            logger.warning("bucket %d-%d attempt %d failed: %s; sleep %ds",
                           y0, y1, attempt + 1, exc, wait)
            time.sleep(wait)
    logger.error("bucket %d-%d gave up after %d retries", y0, y1, retries)
    return []


def scrape(
    start_year: int, end_year: int, bucket: int, limit_per_bucket: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    for y0 in range(start_year, end_year, bucket):
        y1 = min(y0 + bucket, end_year)
        binds = _fetch_bucket(y0, y1, limit_per_bucket)
        logger.info("bucket %d-%d: %d rows", y0, y1, len(binds))
        for b in binds:
            try:
                rows.append({
                    "person_id": "WD:" + b["person"]["value"].rsplit("/", 1)[-1],
                    "name": b.get("personLabel", {}).get("value", ""),
                    "dob": b["dob"]["value"][:10],
                    "dod": b["dod"]["value"][:10],
                    "lat": float(b["lat"]["value"]),
                    "lon": float(b["lon"]["value"]),
                })
            except (KeyError, ValueError, TypeError):
                continue
        time.sleep(1.0)  # be polite to WDQS
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Dedup: one row per person (first birthplace coord wins).
    df = df.drop_duplicates("person_id").reset_index(drop=True)
    # Sanity: death strictly after birth, plausible lifespan.
    df["dob_dt"] = pd.to_datetime(df["dob"], errors="coerce")
    df["dod_dt"] = pd.to_datetime(df["dod"], errors="coerce")
    df = df.dropna(subset=["dob_dt", "dod_dt"])
    age = (df["dod_dt"] - df["dob_dt"]).dt.days / 365.2425
    df = df[(age > 0) & (age <= 120)].reset_index(drop=True)
    df = df.drop(columns=["dob_dt", "dod_dt"])
    return df


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path,
                   default=Path("app/medini/data/raman_saab/death_corpus.parquet"))
    p.add_argument("--start-year", type=int, default=1850)
    p.add_argument("--end-year", type=int, default=1955)
    p.add_argument("--bucket", type=int, default=3)
    p.add_argument("--limit-per-bucket", type=int, default=2500)
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    df = scrape(args.start_year, args.end_year, args.bucket, args.limit_per_bucket)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    logger.info("wrote %d persons -> %s", len(df), args.out)
    print(f"corpus: {len(df)} persons -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
