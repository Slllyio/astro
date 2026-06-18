"""Enrich the death-event corpus with day-precision death dates from Wikidata.

We already have ~30.9k deaths, but ~92% are *year-precision* (mid-year-anchored
from holos "NNNN deaths" tags), which blurs the MD/AD-at-death dāśā timing. Wikidata
carries **day-precision** death dates (P570) for a large share of the same notable
people. This builder matches our charted persons who lack a death event to Wikidata
by exact English label + birth year (±1), and emits fresh day-precision death events.

Matching discipline (high precision over recall):
  * exact rdfs:label match (Title-cased, ASCII) — uses Wikidata's indexed label
    lookup, so batches of 200 names resolve in well under a second;
  * person must be a human (wd:Q5) with both P569 (birth) and P570 (death);
  * accept only when the normalized label equals ours AND birth years agree within 1;
  * require a multi-token name (drop mononyms, which collide across entities);
  * one death per person_id (we only consider persons with no existing death event).

Network: POSTs to the public WDQS SPARQL endpoint with a descriptive User-Agent,
modest batch size, polite inter-batch sleep, and exponential-backoff retries. Results
are cached to ``wikidata_deaths.csv`` so the run is reproducible/auditable.

Usage:
    python -m app.medini.etl.enrich_deaths_wikidata           # full run, append to events
    python -m app.medini.etl.enrich_deaths_wikidata --limit-names 2000 --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Final, Iterable

import pandas as pd
import swisseph as swe

from app.medini.etl.build_person_event_tables import EVENT_COLS

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
DEFAULT_CORPUS_DIR: Final = Path("data/astro_databank")
WDQS_ENDPOINT: Final = "https://query.wikidata.org/sparql"
USER_AGENT: Final = "astro-research/1.0 (vedic death-timing study; akshayr11@gmail.com)"
CACHE_FILE: Final = "wikidata_deaths.csv"

# Only query people plausibly dead — caps query volume and avoids matching a living
# person to a same-named, same-birth-year decedent (vanishingly rare, but excluded).
DEFAULT_MAX_BIRTH_YEAR: Final = 1995


def _norm(s: str) -> str:
    """Lowercase, strip accents, collapse whitespace — our canonical name key."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.split()).strip().lower()


def _title(name: str) -> str:
    """Title-case a normalized name for exact-label matching ('john lennon' →
    'John Lennon'). Wikidata person labels are overwhelmingly Title Case."""
    return " ".join(w.capitalize() for w in name.split())


def _birth_year(jd: float) -> int:
    return int(swe.revjul(float(jd), swe.GREG_CAL)[0])


def _candidate_index(
    persons: pd.DataFrame, charts: pd.DataFrame, max_birth_year: int,
) -> dict[str, list[int]]:
    """norm_name → sorted unique birth years, for charted persons with no death
    event and a multi-token name born on/before ``max_birth_year``."""
    charted = set(charts["person_id"])
    idx: dict[str, set[int]] = {}
    for name, pid, jd in zip(persons["name"], persons["person_id"], persons["birth_jd"]):
        if pid not in charted or name is None or pd.isna(name) or pd.isna(jd):
            continue
        key = _norm(name)
        if len(key.split()) < 2:        # drop mononyms (entity collisions)
            continue
        by = _birth_year(jd)
        if by > max_birth_year:
            continue
        idx.setdefault(key, set()).add(by)
    return {k: sorted(v) for k, v in idx.items()}


def _sparql(query: str, timeout: int = 60, retries: int = 4) -> list[dict[str, Any]]:
    """POST a SPARQL query; return result bindings. Exponential backoff on failure."""
    data = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    delay = 2.0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                WDQS_ENDPOINT, data=data,
                headers={"User-Agent": USER_AGENT,
                         "Accept": "application/sparql-results+json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)["results"]["bindings"]
        except Exception as exc:  # noqa: BLE001 — network sweep + retry
            if attempt == retries - 1:
                logger.warning("WDQS batch failed after %d tries: %s", retries, exc)
                return []
            time.sleep(delay)
            delay *= 2
    return []


def _batch_query(titles: list[str]) -> list[dict[str, Any]]:
    """Exact-label lookup for a batch of Title-cased names → (label, dob, dod)."""
    values = " ".join('"%s"@en' % t.replace('"', "") for t in titles)
    q = (
        "SELECT ?label ?dob ?dod WHERE { VALUES ?label { %s } "
        "?p rdfs:label ?label ; wdt:P31 wd:Q5 ; wdt:P569 ?dob ; wdt:P570 ?dod . }"
        % values
    )
    return _sparql(q)


def fetch_wikidata_deaths(
    names: list[str], batch: int = 200, sleep: float = 0.4,
) -> pd.DataFrame:
    """Resolve a list of normalized names to Wikidata death records.

    Returns a DataFrame [norm_name, birth_year, death_date] (one row per raw
    binding; matching/dedup happens downstream)."""
    out: list[dict[str, Any]] = []
    titles = [_title(n) for n in names]
    n_batches = (len(titles) + batch - 1) // batch
    for bi in range(0, len(titles), batch):
        chunk = titles[bi:bi + batch]
        for r in _batch_query(chunk):
            try:
                dob = r["dob"]["value"]
                dod = r["dod"]["value"]
            except KeyError:
                continue
            out.append({
                "norm_name": _norm(r["label"]["value"]),
                "birth_year": int(dob[:4]) if dob[:4].lstrip("-").isdigit() else None,
                "death_date": dod[:10],
            })
        if (bi // batch) % 25 == 0:
            logger.info("  WDQS batch %d/%d (%d raw records)",
                        bi // batch + 1, n_batches, len(out))
        time.sleep(sleep)
    df = pd.DataFrame(out)
    if not df.empty:
        df = df.dropna(subset=["birth_year"]).drop_duplicates()
    return df


def match_deaths(
    persons: pd.DataFrame, charts: pd.DataFrame, wd: pd.DataFrame,
    max_birth_year: int,
) -> pd.DataFrame:
    """Join Wikidata death records to our charted, death-less persons on
    (norm_name, birth_year ±1). Returns one death per person_id."""
    idx = _candidate_index(persons, charts, max_birth_year)
    # person_id lookup by (norm_name, birth_year)
    charted = set(charts["person_id"])
    by_key: dict[tuple[str, int], str] = {}
    for name, pid, jd in zip(persons["name"], persons["person_id"], persons["birth_jd"]):
        if pid not in charted or name is None or pd.isna(name) or pd.isna(jd):
            continue
        by_key[(_norm(name), _birth_year(jd))] = pid

    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for nm, wy, dod in zip(wd["norm_name"], wd["birth_year"], wd["death_date"]):
        if nm not in idx:
            continue
        for by in idx[nm]:
            if abs(by - int(wy)) <= 1:
                pid = by_key.get((nm, by))
                if pid and pid not in seen:
                    seen.add(pid)
                    rows.append({"person_id": pid, "event_date": str(dod)})
                break
    return pd.DataFrame(rows)


def _to_event_rows(matched: pd.DataFrame, start_event_id: int) -> pd.DataFrame:
    """Shape matched deaths into the canonical EVENT_COLS schema."""
    rows = []
    for i, (pid, date) in enumerate(zip(matched["person_id"], matched["event_date"])):
        rows.append({
            "event_id": start_event_id + i,
            "person_id": pid,
            "event_class": "death_cause_unspecified",
            "event_root": "Death, Cause unspecified",
            "event_subtype": None,
            "event_date": date,
            "event_date_precision": "day",
            "event_label": None,
            "source": "wikidata",
        })
    return pd.DataFrame(rows, columns=list(EVENT_COLS))


def enrich(
    data_dir: Path = DEFAULT_DATA_DIR,
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
    max_birth_year: int = DEFAULT_MAX_BIRTH_YEAR,
    limit_names: int | None = None,
    use_cache: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """End-to-end: pick death-less charted persons, resolve via Wikidata, append
    fresh day-precision death events to events.parquet. Returns run stats."""
    persons = pd.read_parquet(data_dir / "persons.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    events = pd.read_parquet(data_dir / "events.parquet")

    have_death = set(events.loc[events["event_class"] == "death_cause_unspecified",
                                "person_id"])
    persons_nd = persons[~persons["person_id"].isin(have_death)].copy()

    idx = _candidate_index(persons_nd, charts, max_birth_year)
    names = sorted(idx)
    if limit_names is not None:
        names = names[:limit_names]
    logger.info("Candidate death-less charted names (≤%d, multi-token): %d",
                max_birth_year, len(names))

    cache_path = corpus_dir / CACHE_FILE
    if use_cache and cache_path.exists():
        wd = pd.read_csv(cache_path)
        logger.info("Loaded %d cached Wikidata death records from %s", len(wd), cache_path)
    else:
        logger.info("Querying Wikidata for %d names…", len(names))
        wd = fetch_wikidata_deaths(names)
        corpus_dir.mkdir(parents=True, exist_ok=True)
        wd.to_csv(cache_path, index=False)
        logger.info("Cached %d Wikidata death records → %s", len(wd), cache_path)

    matched = match_deaths(persons_nd, charts, wd, max_birth_year)
    logger.info("Matched %d fresh day-precision deaths (name + birth-year ±1)", len(matched))

    stats = {
        "candidate_names": len(names),
        "wikidata_records": int(len(wd)),
        "matched_deaths": int(len(matched)),
        "events_before": int(len(events)),
    }

    if dry_run or matched.empty:
        stats["events_after"] = int(len(events))
        stats["written"] = False
        return stats

    new_events = _to_event_rows(matched, start_event_id=int(events["event_id"].max()) + 1)
    combined = pd.concat([events, new_events], ignore_index=True)
    combined.to_parquet(data_dir / "events.parquet", index=False)
    stats["events_after"] = int(len(combined))
    stats["written"] = True
    logger.info("events.parquet: %d → %d (+%d Wikidata deaths)",
                stats["events_before"], stats["events_after"], len(new_events))
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--max-birth-year", type=int, default=DEFAULT_MAX_BIRTH_YEAR)
    parser.add_argument("--limit-names", type=int, default=None)
    parser.add_argument("--no-cache", action="store_true",
                        help="ignore any cached wikidata_deaths.csv and re-query")
    parser.add_argument("--dry-run", action="store_true",
                        help="report match counts without writing events.parquet")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s | %(message)s")
    stats = enrich(
        data_dir=args.data_dir, corpus_dir=args.corpus_dir,
        max_birth_year=args.max_birth_year, limit_names=args.limit_names,
        use_cache=not args.no_cache, dry_run=args.dry_run,
    )
    logger.info("Done: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
