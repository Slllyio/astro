"""Pull dated life events from Wikidata (CC0) — the scalable event multiplier.

The corpus is starved of dated events (4,590). Wikidata holds dated life events
for millions of people as structured, CC0 claims: marriage start dates
(``P26``/``spouse`` with the ``P580``/``start time`` qualifier), death dates
(``P570``), and career positions (``P39``/``position held`` with ``P580``). The
pipeline already expects a ``wikidata_dated_events.parquet`` and maps WD properties
to event classes — but nothing produced it. This is that producer.

Strategy: Wikidata rarely records birth *time*, so these events are not directly
chartable on their own. Instead we require each person to have a birth *date*
(``P569``) and emit ``(name, name_norm, birth_date, event_class, year)`` rows; the
downstream join attaches them to birth-*time* charts from Astro-Databank / VedAstro
by normalized name + birth date (`resolve_persons_dedup.normalize_name_key`),
multiplying the events available for already-charted public figures.

Network access is isolated in ``_sparql`` so the parser/builder are unit-tested
against canned WDQS JSON. Large pulls page with LIMIT/OFFSET; the public endpoint
has a ~60 s/query budget, so very large sweeps may need the WD dump or QLever —
the per-class queries here are written to stay within budget per page.

CLI::

    python -m app.medini.etl.wikidata_events_importer \\
        --classes marriage death career --page-size 5000 --max-pages 40 \\
        --output app/medini/data/wikidata_dated_events.parquet
"""
from __future__ import annotations

import argparse
import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Final

import pandas as pd

from app.medini.etl.resolve_persons_dedup import normalize_name_key

logger = logging.getLogger(__name__)

_ENDPOINT: Final = "https://query.wikidata.org/sparql"
_UA: Final = "medini-astro-research/1.0 (dasha timing study; contact: researcher)"
MIN_YEAR: Final = 1700
MAX_YEAR: Final = 2030

# event_class → SPARQL body. Each query selects ?person ?personLabel ?birth ?date,
# requires a birth DATE (P569) so the row is matchable, and is paginated by the
# caller with ORDER BY / LIMIT / OFFSET appended.
_QUERIES: Final[dict[str, str]] = {
    "marriage": """
        SELECT ?person ?personLabel ?birth ?date WHERE {
          ?person wdt:P31 wd:Q5 ; wdt:P569 ?birth ; p:P26 ?st .
          ?st pq:P580 ?date .
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }""",
    "death": """
        SELECT ?person ?personLabel ?birth ?date WHERE {
          ?person wdt:P31 wd:Q5 ; wdt:P569 ?birth ; wdt:P570 ?date .
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }""",
    "career": """
        SELECT ?person ?personLabel ?birth ?date WHERE {
          ?person wdt:P31 wd:Q5 ; wdt:P569 ?birth ; p:P39 ?st .
          ?st pq:P580 ?date .
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }""",
}


def _sparql(query: str, *, retries: int = 3, pause: float = 2.0) -> dict:
    """POST a SPARQL query to WDQS, return parsed JSON. Isolated for mocking."""
    data = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    req = urllib.request.Request(
        _ENDPOINT, data=data,
        headers={"User-Agent": _UA, "Accept": "application/sparql-results+json"})
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:                       # noqa: BLE001 (network is flaky)
            last = exc
            logger.warning("WDQS attempt %d failed: %s", attempt + 1, exc)
            time.sleep(pause * (attempt + 1))
    raise RuntimeError(f"WDQS query failed after {retries} tries: {last}")


def _iso_year(value: str | None) -> int | None:
    """Year from a Wikidata time literal like '1879-03-14T00:00:00Z' (or '-0044-...')."""
    if not value:
        return None
    s = str(value)
    neg = s.startswith("-")
    body = s[1:] if neg else s
    head = body.split("-", 1)[0]
    if not head.isdigit():
        return None
    y = -int(head) if neg else int(head)
    return y if MIN_YEAR <= y <= MAX_YEAR else None


def _iso_date(value: str | None) -> str:
    """Date portion 'YYYY-MM-DD' when day-precision is present, else ''."""
    if not value:
        return ""
    s = str(value).lstrip("-")
    date = s.split("T", 1)[0]
    parts = date.split("-")
    if len(parts) == 3 and all(p.isdigit() for p in parts) and parts[1] != "00" \
            and parts[2] != "00":
        return date
    return ""


def parse_bindings(result_json: dict, event_class: str) -> list[dict]:
    """WDQS JSON → event rows. Skips rows missing a usable event year, a birth
    year, or whose 'name' is an unlabelled Q-id."""
    rows: list[dict] = []
    for b in result_json.get("results", {}).get("bindings", []):
        name = (b.get("personLabel", {}) or {}).get("value", "").strip()
        qid = (b.get("person", {}) or {}).get("value", "").rsplit("/", 1)[-1]
        if not name or name == qid:                    # unlabelled entity
            continue
        year = _iso_year((b.get("date", {}) or {}).get("value"))
        birth_year = _iso_year((b.get("birth", {}) or {}).get("value"))
        if year is None or birth_year is None:
            continue
        rows.append({
            "person_qid": qid,
            "name": name,
            "name_norm": normalize_name_key(name),
            "birth_date": _iso_date((b.get("birth", {}) or {}).get("value")),
            "birth_year": birth_year,
            "event_class": event_class,
            "event_root": event_class,
            "event_year": year,
            "event_date": _iso_date((b.get("date", {}) or {}).get("value")),
            "source_url": f"https://www.wikidata.org/wiki/{qid}",
        })
    return rows


def pull_class(event_class: str, *, page_size: int, max_pages: int,
               sparql: Callable[[str], dict] = _sparql,
               pause: float = 1.0) -> list[dict]:
    """Paginate one event class via ORDER BY ?person + LIMIT/OFFSET."""
    if event_class not in _QUERIES:
        raise ValueError(f"unknown event class: {event_class}")
    base = _QUERIES[event_class]
    out: list[dict] = []
    for page in range(max_pages):
        q = f"{base}\nORDER BY ?person\nLIMIT {page_size} OFFSET {page * page_size}"
        rows = parse_bindings(sparql(q), event_class)
        out.extend(rows)
        logger.info("%s page %d: +%d rows (total %d)", event_class, page,
                    len(rows), len(out))
        if len(rows) < page_size:                      # last page
            break
        time.sleep(pause)
    return out


def build(classes: list[str], output: Path, *, page_size: int = 5000,
          max_pages: int = 40, sparql: Callable[[str], dict] = _sparql) -> dict:
    rows: list[dict] = []
    for cls in classes:
        rows.extend(pull_class(cls, page_size=page_size, max_pages=max_pages,
                               sparql=sparql))
    df = pd.DataFrame(rows).drop_duplicates(
        subset=["person_qid", "event_class", "event_year"])
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".csv":
        df.to_csv(output, index=False)
    else:
        df.to_parquet(output, index=False)
    stats = {"total_events": len(df), "unique_people": df["name_norm"].nunique()
             if not df.empty else 0,
             **{c: int((df["event_class"] == c).sum()) for c in classes}}
    return stats


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m app.medini.etl.wikidata_events_importer",
        description="Pull dated life events (marriage/death/career) from Wikidata.")
    p.add_argument("--classes", nargs="+", default=["marriage", "death", "career"],
                   choices=list(_QUERIES))
    p.add_argument("--page-size", type=int, default=5000)
    p.add_argument("--max-pages", type=int, default=40)
    p.add_argument("--output", type=Path,
                   default=Path("app/medini/data/wikidata_dated_events.parquet"))
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    stats = build(args.classes, args.output, page_size=args.page_size,
                  max_pages=args.max_pages)
    logger.info("wrote %s: %s", args.output, stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
