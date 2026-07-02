"""Timed-birth death corpus from Astro-Databank via the Wayback Machine.

Builds the corpus the house-based maraka validation needs: **birth time**
(Rodden-rated), birth coordinates + timezone, and a **death date** — one row
per deceased Astro-Databank entry.

Pipeline (all archive.org access at the repo's polite 4 s rate):

1. Load the paginated CDX index of archived ADB entries
   ({entry_url: latest_timestamp}, built separately).
2. Derive person names from entry URLs ("Lastname,_Firstname").
3. Batch-query Wikidata for name → (dob, dod) of deceased people. Used only
   to PRIORITIZE the fetch queue (dead-matched entries first) and as a
   homonym-guarded fallback death date.
4. Fetch each entry's archived HTML (`id_` raw replay), parse birth data with
   the repo's ``parse_wayback_entry`` (name, dob, tob, coords, tz, Rodden),
   and parse the own-death event from the Events section — lines that start
   with "Death" but NOT "Death of" (family losses are a different taxonomy
   class, see build_event_class_taxonomy).
5. Death-date priority: page event date (authoritative); else the Wikidata
   dod, accepted ONLY if the page's dob equals the Wikidata dob (kills
   homonym mismatches).
6. Append rows incrementally to a CSV checkpoint; final parquet keeps rows
   with Rodden ∈ {AA, A, B}, a real birth time, coords, tz and a valid death
   date.

CLI:
    python -m app.medini.etl.adb_wayback_death_corpus \
        --cdx app/medini/data/raman_saab/wayback/cdx_index.json \
        --out app/medini/data/raman_saab/adb_timed_death_corpus.parquet \
        [--max-entries N] [--skip-wikidata] [--rate-limit 4.0]
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import unquote

import pandas as pd
import requests

from bs4 import BeautifulSoup

from app.medini.etl.scraper import parse_tz_offset
from app.medini.etl.wayback_scraper import (
    DEFAULT_USER_AGENT, WAYBACK_REPLAY_TEMPLATE, _wb_extract_infobox_fields,
    parse_wayback_entry,
)

logger = logging.getLogger(__name__)

_WD_ENDPOINT = "https://query.wikidata.org/sparql"
_MONTHS = {m: i + 1 for i, m in enumerate(
    ("january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"))}

# Own-death event line: "Death  18 April 1955 ..." or "Death, Cause unspecified
# 4 May 1970" or "Death by Heart Attack 22 March 1994". NOT "Death of Mate ...".
_DEATH_LINE_RE = re.compile(
    r"\bDeath\b(?!\s+of\b)[^0-9]{0,60}?(\d{1,2})\s+"
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{4})",
    re.IGNORECASE,
)


def name_from_entry_url(url: str) -> str:
    """'…/astro-databank/Kennedy,_John_F.' -> 'John F. Kennedy'."""
    slug = unquote(url.rstrip("/").rsplit("/", 1)[-1]).replace("_", " ")
    if "," in slug:
        last, _, first = slug.partition(",")
        return f"{first.strip()} {last.strip()}".strip()
    return slug.strip()


# ADB timezone notation: "h1e" = +1h standard, "h5w30" = -5.5h,
# "m10e0" = LMT at meridian 10°0'E = +(10+0/60)/15 h. The repo's
# parse_tz_offset covers h-notation but deliberately drops LMT ("unreliable
# for ML") — for chart-casting LMT is exact (mean solar time at the given
# meridian), so we decode it here.
_TZ_NOTATION_RE = re.compile(r"\b([hm])(\d+)([ew])(\d+)?\b", re.IGNORECASE)


def parse_adb_tz(text: str) -> float | None:
    """Decode an ADB timezone string to hours from UTC (east positive)."""
    if not text:
        return None
    got = parse_tz_offset(text)
    if got is not None:
        return got
    m = _TZ_NOTATION_RE.search(text)
    if not m:
        return None
    kind, big, ew, small = (m.group(1).lower(), int(m.group(2)),
                            m.group(3).lower(), int(m.group(4) or 0))
    if kind == "h":
        val = big + small / 60.0
    else:  # meridian degrees -> hours
        val = (big + small / 60.0) / 15.0
    return val if ew == "e" else -val


def parse_death_date(html: str) -> str | None:
    """ISO date of the subject's own death from the Events section, or None."""
    m = _DEATH_LINE_RE.search(html)
    if not m:
        return None
    day, mon, year = int(m.group(1)), _MONTHS[m.group(2).lower()], int(m.group(3))
    try:
        return f"{year:04d}-{mon:02d}-{day:02d}"
    except ValueError:
        return None


# ---------- Wikidata name-batch matching (prioritization + fallback) ----------

def _wd_query(names: list[str], retries: int = 4) -> list[dict]:
    values = " ".join(json.dumps(n) + "@en" for n in names)
    q = f"""
    SELECT ?name ?dob ?dod WHERE {{
      VALUES ?name {{ {values} }}
      ?p rdfs:label ?name ; wdt:P31 wd:Q5 ;
         p:P569/psv:P569 ?dobn ; p:P570/psv:P570 ?dodn .
      ?dobn wikibase:timeValue ?dob ; wikibase:timePrecision 11 .
      ?dodn wikibase:timeValue ?dod ; wikibase:timePrecision 11 .
    }}
    """
    for attempt in range(retries):
        try:
            r = requests.get(_WD_ENDPOINT,
                             params={"query": q, "format": "json"},
                             headers={"User-Agent": DEFAULT_USER_AGENT},
                             timeout=90)
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()["results"]["bindings"]
        except Exception as exc:  # noqa: BLE001
            logger.warning("WD batch failed (%s); retry %d", exc, attempt + 1)
            time.sleep(5 * (attempt + 1))
    return []


def wikidata_death_map(names: list[str], batch: int = 120) -> dict[str, tuple[str, str]]:
    """name -> (dob, dod) for names Wikidata knows as deceased humans.

    Names that match multiple people keep the FIRST binding; downstream use is
    guarded by a dob-consistency check, so collisions degrade to "no fallback",
    never to a wrong death date.
    """
    out: dict[str, tuple[str, str]] = {}
    for i in range(0, len(names), batch):
        chunk = names[i:i + batch]
        for b in _wd_query(chunk):
            n = b["name"]["value"]
            if n not in out:
                out[n] = (b["dob"]["value"][:10], b["dod"]["value"][:10])
        logger.info("WD matched %d/%d names (…batch %d)",
                    len(out), i + len(chunk), i // batch)
        time.sleep(1.0)
    return out


# ---------- Fetch + parse loop ----------

_CSV_COLS = ("name", "dob", "tob", "tz_offset", "lat", "lon", "rodden",
             "dod", "dod_source", "source_url")


def _fetch(url: str, timestamp: str, session: requests.Session,
           retries: int = 3) -> str | None:
    replay = WAYBACK_REPLAY_TEMPLATE.format(timestamp=timestamp, original=url)
    for attempt in range(retries):
        try:
            r = session.get(replay, timeout=60, allow_redirects=True)
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 503):
                time.sleep(15 * (attempt + 1))
                continue
            return None
        except Exception:  # noqa: BLE001
            time.sleep(5 * (attempt + 1))
    return None


def build(cdx_path: Path, out_path: Path, *, rate_limit: float = 4.0,
          max_entries: int | None = None, skip_wikidata: bool = False) -> int:
    idx: dict[str, str] = json.loads(cdx_path.read_text())
    urls = sorted(idx)
    logger.info("CDX index: %d entries", len(urls))

    names = {u: name_from_entry_url(u) for u in urls}
    wd: dict[str, tuple[str, str]] = {}
    if not skip_wikidata:
        wd = wikidata_death_map(sorted(set(names.values())))
        logger.info("Wikidata: %d names matched as deceased", len(wd))

    # Priority queue: WD-matched-dead first, then the rest.
    queue = sorted(urls, key=lambda u: (names[u] not in wd, u))
    if max_entries:
        queue = queue[:max_entries]

    ckpt = out_path.with_suffix(".checkpoint.csv")
    done: set[str] = set()
    if ckpt.exists():
        with ckpt.open() as f:
            done = {row["source_url"] for row in csv.DictReader(f)}
        logger.info("resuming: %d already fetched", len(done))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not ckpt.exists()

    session = requests.Session()
    session.headers["User-Agent"] = DEFAULT_USER_AGENT
    n_dead = 0
    with ckpt.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_CSV_COLS)
        if write_header:
            w.writeheader()
        for i, url in enumerate(queue):
            if url in done:
                continue
            html = _fetch(url, idx[url], session)
            time.sleep(rate_limit)
            row = {c: "" for c in _CSV_COLS}
            row["source_url"] = url
            if html:
                rec = parse_wayback_entry(html, url)
                if rec:
                    tz = rec.tz_offset
                    if tz is None:
                        # Fallback: decode ADB h/m-notation (incl. LMT).
                        fields = _wb_extract_infobox_fields(
                            BeautifulSoup(html, "html.parser"))
                        tz = parse_adb_tz(fields.get("timezone", ""))
                    row.update(name=rec.name, dob=rec.date_of_birth,
                               tob=rec.time_of_birth,
                               tz_offset="" if tz is None else tz,
                               lat="" if rec.latitude is None else rec.latitude,
                               lon="" if rec.longitude is None else rec.longitude,
                               rodden=rec.rodden_rating)
                page_dod = parse_death_date(html)
                if page_dod:
                    row["dod"], row["dod_source"] = page_dod, "adb_page"
                else:
                    hit = wd.get(names[url])
                    # Homonym guard: only trust the WD dod if dob agrees.
                    if hit and row["dob"] and hit[0] == row["dob"]:
                        row["dod"], row["dod_source"] = hit[1], "wikidata"
            if row["dod"]:
                n_dead += 1
            w.writerow(row)
            f.flush()
            if (i + 1) % 100 == 0:
                logger.info("fetched %d/%d (deceased so far: %d)",
                            i + 1, len(queue), n_dead)

    return finalize(ckpt, out_path)


def finalize(ckpt: Path, out_path: Path) -> int:
    """Checkpoint CSV -> filtered parquet. Returns row count."""
    df = pd.read_csv(ckpt, dtype=str).fillna("")
    n_raw = len(df)
    df = df[(df["dod"] != "") & (df["dob"] != "") & (df["tob"] != "")
            & (df["lat"] != "") & (df["lon"] != "") & (df["tz_offset"] != "")
            & df["rodden"].isin(["AA", "A", "B"])].copy()
    for c in ("lat", "lon", "tz_offset"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["lat", "lon", "tz_offset"])
    dob = pd.to_datetime(df["dob"], errors="coerce")
    dod = pd.to_datetime(df["dod"], errors="coerce")
    age = (dod - dob).dt.days / 365.2425
    df = df[(age > 1) & (age <= 120)].reset_index(drop=True)
    df.to_parquet(out_path, index=False)
    logger.info("finalized: %d raw -> %d timed+deceased (AA/A/B) -> %s",
                n_raw, len(df), out_path)
    print(f"corpus: {len(df)} timed deceased persons -> {out_path}")
    return len(df)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cdx", type=Path,
                   default=Path("app/medini/data/raman_saab/wayback/cdx_index.json"))
    p.add_argument("--out", type=Path,
                   default=Path("app/medini/data/raman_saab/adb_timed_death_corpus.parquet"))
    p.add_argument("--rate-limit", type=float, default=4.0)
    p.add_argument("--max-entries", type=int, default=None)
    p.add_argument("--skip-wikidata", action="store_true")
    p.add_argument("--finalize-only", action="store_true",
                   help="just rebuild the parquet from the checkpoint CSV")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.finalize_only:
        finalize(args.out.with_suffix(".checkpoint.csv"), args.out)
        return 0
    build(args.cdx, args.out, rate_limit=args.rate_limit,
          max_entries=args.max_entries, skip_wikidata=args.skip_wikidata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
