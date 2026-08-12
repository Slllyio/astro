"""Wikidata importer — the event-timing corpus.

The Gauquelin archive and this source are complements, and neither is sufficient
alone:

* **Gauquelin** has minute-precise registry birth times but *zero dated events*.
  It can test what a chart says about a person; it cannot test *when* anything
  happened.
* **Wikidata** has dated life events at enormous scale — death dates alone run to
  millions — but almost never a birth *time*.

So this corpus opens the tournament's second target (event timing) and is barred
from the first (anything needing houses or an ascendant). That is recorded per
row as ``time_tier="C"``, a tier below self-reported: not an unverified time, but
*no time at all*. A tier-C chart has trustworthy slow-planet longitudes, a Sun
good to ~1°, and a Moon that could be anywhere in a 13° arc.

**What can honestly be tested here**: transits of the slow planets to natal
slow-planet positions at a dated event. **What cannot**: houses, ascendant,
anything Moon-precise, and any claim that needs a birth time.

Query volume is real — one birth year returns ~14,000 people — so results are
cached per year and the service is queried once per year with a delay. WDQS is a
public research endpoint; this uses a descriptive User-Agent and does not
parallelise.

Usage:
    python -m app.empirical.acquire.wikidata_import --from-year 1880 --to-year 1920 \
        --persons data/empirical/wikidata_persons.csv \
        --events data/empirical/wikidata_events.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Final, Iterator

logger = logging.getLogger(__name__)

__all__ = [
    "WikidataPerson",
    "LifeEvent",
    "parse_point",
    "parse_rows",
    "fetch_year",
    "import_range",
]

_ENDPOINT: Final[str] = "https://query.wikidata.org/sparql"
_CACHE_DIR: Final[Path] = Path("data/empirical/raw/wikidata")
_USER_AGENT: Final[str] = "astro-empirical/1.0 (research corpus build; github.com/Slllyio/astro)"

#: Seconds between queries. WDQS is volunteer-run infrastructure.
_DELAY_SECONDS: Final[float] = 1.5

#: Wikidata time precision: 11 = day, 10 = month, 9 = year. Only day precision is
#: admitted — a year-precision death cannot evidence a transit exact for days.
_DAY_PRECISION: Final[int] = 11

#: No birth time at all. Distinct from "S" (self-reported time): S has a claimed
#: time that might be wrong; C has none, so house-dependent features are not
#: merely unreliable, they are undefined.
_TIER_NO_TIME: Final[str] = "C"

_QUERY: Final[str] = """
SELECT ?person ?birth ?death ?coord WHERE {
  ?person wdt:P31 wd:Q5 ;
          p:P569/psv:P569 ?bn ;
          p:P570/psv:P570 ?dn ;
          wdt:P19 ?place .
  ?bn wikibase:timeValue ?birth ; wikibase:timePrecision ?bp .
  ?dn wikibase:timeValue ?death ; wikibase:timePrecision ?dp .
  ?place wdt:P625 ?coord .
  FILTER(?bp >= %(prec)d && ?dp >= %(prec)d)
  FILTER(YEAR(?birth) = %(year)d)
}
LIMIT %(limit)d
"""

_POINT_RE: Final[re.Pattern[str]] = re.compile(
    r"Point\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\)"
)


@dataclass(frozen=True, slots=True)
class WikidataPerson:
    """One person with a birth date and place, but no birth time.

    Attributes:
      person_id: Deterministic id derived from the Wikidata QID.
      qid: The Wikidata entity, for traceability back to the source.
      birth_year, birth_month, birth_day: Day-precision civil date.
      latitude, longitude: Birth place, decimal degrees.
      time_tier: Always ``C`` — no birth time exists in this source.
      data_quality: ``ok`` or a reason the row is suspect.
    """

    person_id: str
    qid: str
    birth_year: int
    birth_month: int
    birth_day: int
    latitude: float
    longitude: float
    time_tier: str
    data_quality: str


@dataclass(frozen=True, slots=True)
class LifeEvent:
    """One dated event. Currently death; the schema admits more.

    Attributes:
      person_id: Links to :class:`WikidataPerson`.
      event_class: Taxonomy label.
      event_year, event_month, event_day: Day-precision date.
      date_precision: Always ``day`` here — coarser rows are filtered at query
        time, because a year-precision date cannot evidence a transit.
      age_years: Age at the event, for the immortal-time and age controls.
      source: Provenance.
    """

    person_id: str
    event_class: str
    event_year: int
    event_month: int
    event_day: int
    date_precision: str
    age_years: float
    source: str


def parse_point(raw: str) -> tuple[float, float]:
    """``"Point(7.9956 58.1467)"`` -> ``(latitude, longitude)``.

    Note the order swap: WKT is ``Point(longitude latitude)`` while every other
    coordinate in this repo is (lat, lon). Getting this backwards silently
    relocates every birth, so it is parsed explicitly rather than unpacked.
    """
    match = _POINT_RE.search(raw)
    if not match:
        raise ValueError(f"unparseable coordinate {raw!r}")
    longitude, latitude = float(match[1]), float(match[2])
    if not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude <= 180.0:
        raise ValueError(f"coordinate out of range: {raw!r}")
    return latitude, longitude


def _person_id(qid: str) -> str:
    return "wd_" + hashlib.sha1(qid.encode("utf-8")).hexdigest()[:16]


def _split_date(iso: str) -> tuple[int, int, int]:
    """Wikidata ISO timestamps, tolerant of the leading ``+`` and BCE minus."""
    body = iso.lstrip("+")
    date_part = body.split("T")[0]
    year_str, month_str, day_str = date_part.split("-")[-3:]
    sign = -1 if body.startswith("-") else 1
    return sign * int(year_str), int(month_str), int(day_str)


def _age_years(birth: tuple[int, int, int], death: tuple[int, int, int]) -> float:
    by, bm, bd = birth
    dy, dm, dd = death
    return round((dy - by) + (dm - bm) / 12.0 + (dd - bd) / 365.25, 3)


def parse_rows(payload: dict[str, Any]) -> tuple[list[WikidataPerson], list[LifeEvent]]:
    """Turn one SPARQL response into persons and their dated events.

    Rows that fail to parse, or that describe an impossible life (death before
    birth, implausible lifespan), are flagged rather than dropped — same policy
    as the Gauquelin importer, for the same reason: a silent discard hides a
    source defect.
    """
    persons: list[WikidataPerson] = []
    events: list[LifeEvent] = []
    seen: set[str] = set()

    for row in payload.get("results", {}).get("bindings", []):
        try:
            qid = row["person"]["value"].rsplit("/", 1)[-1]
            if qid in seen:
                continue
            latitude, longitude = parse_point(row["coord"]["value"])
            birth = _split_date(row["birth"]["value"])
            death = _split_date(row["death"]["value"])
        except (KeyError, ValueError) as exc:
            logger.debug("skipping unparseable row: %s", exc)
            continue

        seen.add(qid)
        age = _age_years(birth, death)
        if age < 0:
            quality = f"death_before_birth:{age}"
        elif age > 122.0:  # documented human maximum
            quality = f"implausible_lifespan:{age}"
        else:
            quality = "ok"

        person_id = _person_id(qid)
        persons.append(
            WikidataPerson(
                person_id=person_id,
                qid=qid,
                birth_year=birth[0],
                birth_month=birth[1],
                birth_day=birth[2],
                latitude=round(latitude, 4),
                longitude=round(longitude, 4),
                time_tier=_TIER_NO_TIME,
                data_quality=quality,
            )
        )
        events.append(
            LifeEvent(
                person_id=person_id,
                event_class="death",
                event_year=death[0],
                event_month=death[1],
                event_day=death[2],
                date_precision="day",
                age_years=age,
                source="wikidata:P570",
            )
        )
    return persons, events


def fetch_year(
    year: int,
    *,
    limit: int = 30000,
    refresh: bool = False,
    cache_dir: Path = _CACHE_DIR,
) -> dict[str, Any]:
    """One birth year's rows, fetched once and cached.

    Year slicing keeps each query inside the service's 60-second budget; a single
    query spanning decades times out.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"birthyear_{year}.json"
    if cached.is_file() and not refresh:
        return json.loads(cached.read_text(encoding="utf-8"))

    query = _QUERY % {"prec": _DAY_PRECISION, "year": year, "limit": limit}
    body = urllib.parse.urlencode({"query": query}).encode("utf-8")
    request = urllib.request.Request(
        _ENDPOINT,
        data=body,
        headers={"Accept": "application/sparql-results+json", "User-Agent": _USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310 - fixed host
        payload = json.loads(response.read().decode("utf-8"))
    cached.write_text(json.dumps(payload), encoding="utf-8")
    time.sleep(_DELAY_SECONDS)
    return payload


def import_range(
    from_year: int,
    to_year: int,
    *,
    refresh: bool = False,
    cache_dir: Path = _CACHE_DIR,
) -> Iterator[tuple[int, list[WikidataPerson], list[LifeEvent]]]:
    """Yield one birth year at a time, so a long run can be written incrementally."""
    if from_year > to_year:
        raise ValueError(f"from_year {from_year} is after to_year {to_year}")
    for year in range(from_year, to_year + 1):
        try:
            payload = fetch_year(year, refresh=refresh, cache_dir=cache_dir)
        except Exception as exc:  # noqa: BLE001 - one bad year must not lose the run
            logger.warning("year %d failed (%s) — skipped, rerun to fill the gap", year, exc)
            continue
        persons, events = parse_rows(payload)
        yield year, persons, events


def _write(path: Path, rows: list[Any], row_type: type) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [f.name for f in fields(row_type)]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Import dated life events from Wikidata.")
    parser.add_argument("--from-year", type=int, required=True)
    parser.add_argument("--to-year", type=int, required=True)
    parser.add_argument("--persons", required=True, help="output persons CSV")
    parser.add_argument("--events", required=True, help="output events CSV")
    parser.add_argument("--refresh", action="store_true", help="re-fetch cached years")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    all_persons: list[WikidataPerson] = []
    all_events: list[LifeEvent] = []
    for year, persons, events in import_range(
        args.from_year, args.to_year, refresh=args.refresh
    ):
        all_persons.extend(persons)
        all_events.extend(events)
        logger.info("  %d: %5d persons (running total %d)", year, len(persons), len(all_persons))

    # Deduplicate across years — a person appears once, but a cache refresh or an
    # overlapping rerun could otherwise double-count them.
    seen: set[str] = set()
    deduped: list[WikidataPerson] = []
    for person in all_persons:
        if person.person_id in seen:
            continue
        seen.add(person.person_id)
        deduped.append(person)

    _write(Path(args.persons), deduped, WikidataPerson)
    _write(Path(args.events), all_events, LifeEvent)

    flagged = sum(1 for p in deduped if p.data_quality != "ok")
    logger.info("")
    logger.info("persons written : %d (%d duplicates dropped)", len(deduped), len(all_persons) - len(deduped))
    logger.info("events written  : %d (all day-precision)", len(all_events))
    logger.info("quality-flagged : %d", flagged)
    logger.info("time tier       : C (no birth time) — house-dependent tests are barred")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
