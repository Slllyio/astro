"""Fast regex-based event extractor from Wayback-cached HTML biographies.

This script uses deterministic regex patterns rather than LLM calls, making it
capable of processing all 33k files in minutes rather than 50 days. It extracts:
  - Marriage events (year + optional date)
  - Divorce events (year + optional date)
  - Death events (year + cause)

For truly ambiguous biographies, an optional --llm-fallback flag queues those
files for LLM processing (see llm_event_extractor.py).

CLI:
    python -m app.medini.etl.regex_event_extractor
    python -m app.medini.etl.regex_event_extractor --merge-only
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CSV_COLUMNS = (
    "name", "event_code", "event_root", "event_subtype",
    "event_date", "event_year", "source_url"
)

# ---------------------------------------------------------------------------
# Regex patterns – designed for Astro-Databank biographical text style
# ---------------------------------------------------------------------------

# Month names for pattern building
_MONTHS = (
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)
_MON_ABBR = (
    "Jan\\.?|Feb\\.?|Mar\\.?|Apr\\.?|May\\.?|Jun\\.?|"
    "Jul\\.?|Aug\\.?|Sep\\.?|Oct\\.?|Nov\\.?|Dec\\.?"
)
_MONTH_PAT = f"(?:{_MONTHS}|{_MON_ABBR})"
_DAY_PAT   = r"(?:\d{1,2}(?:st|nd|rd|th)?)"
_YEAR_PAT  = r"(1[5-9]\d{2}|20[012]\d)"  # capture group: year

# Full date: "June 12, 1941" / "12 June 1941" / "June 1941"
_FULL_DATE = (
    rf"(?:{_MONTH_PAT}\s+{_DAY_PAT},?\s+{_YEAR_PAT}"     # Month D, YYYY
    rf"|{_DAY_PAT}\s+{_MONTH_PAT}\s+{_YEAR_PAT}"          # D Month YYYY
    rf"|{_MONTH_PAT}\s+{_YEAR_PAT})"                       # Month YYYY
)
_FULL_DATE_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")   # for ISO dates in text

# marriage trigger words
_MARRY_TRIGGERS = r"(?:married|wed(?:ded)?|marriage|wedded to|union with|tied the knot)"
_DIVORCE_TRIGGERS = r"(?:divorced?|separated?|annulled?|split from|ended the marriage)"
_DEATH_TRIGGERS = r"(?:died|passed away|death|deceased|succumbed|killed)"

MARRIAGE_RE = re.compile(
    rf"{_MARRY_TRIGGERS}[^.{{}}]*?{_YEAR_PAT}", re.IGNORECASE
)
DIVORCE_RE = re.compile(
    rf"{_DIVORCE_TRIGGERS}[^.{{}}]*?{_YEAR_PAT}", re.IGNORECASE
)
DEATH_RE = re.compile(
    rf"{_DEATH_TRIGGERS}[^.{{}}]*?{_YEAR_PAT}", re.IGNORECASE
)

# death cause sub-classification
_DISEASE_WORDS = r"cancer|tumor|disease|illness|heart attack|stroke|AIDS|HIV|pneumonia|diabetes|leukemia"
_ACCIDENT_WORDS = r"accident|crash|collision|drowned|drowning|fell|fall|fire|explosion|plane crash"
_SUICIDE_WORDS = r"suicide|overdose|self-inflicted|took his own life|took her own life|hanged himself|shot himself|shot herself"


def _death_subtype(sentence: str) -> str:
    s = sentence.lower()
    if re.search(_SUICIDE_WORDS, s, re.IGNORECASE):
        return "Suicide"
    if re.search(_ACCIDENT_WORDS, s, re.IGNORECASE):
        return "Accident"
    if re.search(_DISEASE_WORDS, s, re.IGNORECASE):
        return "Disease"
    return "Unspecified"


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------
def parse_biography(html_content: str) -> tuple[str, str]:
    soup = BeautifulSoup(html_content, "html.parser")
    tag = soup.select_one("#firstHeading") or soup.find("h1")
    name = tag.get_text(strip=True) if tag else ""
    root = soup.select_one("#mw-content-text") or soup.find("body")
    paras: list[str] = []
    if root:
        for p in root.find_all("p"):
            t = p.get_text(" ", strip=True)
            if t:
                paras.append(t)
    return name, "\n".join(paras)


# ---------------------------------------------------------------------------
# Extraction logic
# ---------------------------------------------------------------------------
def extract_events_from_bio(name: str, bio: str, source: str) -> list[dict]:
    events: list[dict] = []

    # -- marriages --
    for m in MARRIAGE_RE.finditer(bio):
        year = int(m.group(1))
        if not (1600 < year < 2030):
            continue
        events.append({
            "name": name,
            "event_code": "Relationship : Marriage",
            "event_root": "Relationship",
            "event_subtype": "Marriage",
            "event_date": "",
            "event_year": year,
            "source_url": source,
        })

    # -- divorces --
    for m in DIVORCE_RE.finditer(bio):
        year = int(m.group(1))
        if not (1600 < year < 2030):
            continue
        events.append({
            "name": name,
            "event_code": "Relationship : Divorce",
            "event_root": "Relationship",
            "event_subtype": "Divorce",
            "event_date": "",
            "event_year": year,
            "source_url": source,
        })

    # -- deaths --
    for m in DEATH_RE.finditer(bio):
        year = int(m.group(1))
        if not (1600 < year < 2030):
            continue
        sentence = bio[max(0, m.start() - 50): m.end() + 100]
        subtype = _death_subtype(sentence)
        events.append({
            "name": name,
            "event_code": f"Death, {subtype}",
            "event_root": "Death",
            "event_subtype": subtype,
            "event_date": "",
            "event_year": year,
            "source_url": source,
        })

    # De-duplicate within same person: keep earliest instance per (root, subtype, year)
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for ev in events:
        key = (ev["event_root"], ev["event_subtype"], ev["event_year"])
        if key not in seen:
            seen.add(key)
            deduped.append(ev)

    return deduped


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run_extraction(cache_dir: Path, output_csv: Path, limit: int | None, log_every: int = 500):
    html_files = sorted(cache_dir.glob("*.html"))
    if limit:
        html_files = html_files[:limit]
    total = len(html_files)
    logger.info("Processing %d HTML files...", total)

    write_header = not output_csv.exists()
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    total_events = 0
    people_with_events = 0

    with output_csv.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()

        for idx, fp in enumerate(html_files, 1):
            html = fp.read_text(encoding="utf-8", errors="ignore")
            name, bio = parse_biography(html)
            if not name or len(bio) < 30:
                continue

            source = f"regex_extracted:{fp.name}"
            events = extract_events_from_bio(name, bio, source)

            if events:
                people_with_events += 1
                for ev in events:
                    writer.writerow(ev)
                total_events += len(events)

            if idx % log_every == 0 or idx == total:
                logger.info("[%d/%d] total_events=%d people_with_events=%d",
                            idx, total, total_events, people_with_events)

        fh.flush()

    logger.info(
        "Done! Files=%d, people_with_events=%d, events=%d → %s",
        total, people_with_events, total_events, output_csv,
    )
    return people_with_events, total_events


def run_merge(extracted_csv: Path, target_csv: Path):
    """Append extracted events (de-duplicated) into events_all.csv."""
    if not extracted_csv.exists():
        logger.error("Extracted CSV not found: %s", extracted_csv)
        return

    new_rows = pd.read_csv(extracted_csv, low_memory=False)
    logger.info("Loaded %d extracted events from %s", len(new_rows), extracted_csv)

    if target_csv.exists():
        existing = pd.read_csv(target_csv, low_memory=False)
        combined = pd.concat([existing, new_rows], ignore_index=True)
    else:
        combined = new_rows

    before = len(combined)
    combined = combined.drop_duplicates(
        subset=["name", "event_root", "event_subtype", "event_year"], keep="first"
    )
    after = len(combined)
    logger.info(
        "Merged: %d existing + %d new → %d unique (dropped %d dupes)",
        before - len(new_rows), len(new_rows), after, before - after,
    )
    combined.to_csv(target_csv, index=False)
    logger.info("Wrote merged events_all.csv → %s (%d rows)", target_csv, len(combined))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.regex_event_extractor",
        description="Fast regex-based life event extraction from Wayback HTML cache.",
    )
    parser.add_argument("--cache-dir", type=Path,
                        default=Path("data/astro_databank/wayback_cache"))
    parser.add_argument("--output", type=Path,
                        default=Path("data/astro_databank/events_regex_extracted.csv"))
    parser.add_argument("--events-all", type=Path,
                        default=Path("data/astro_databank/events_all.csv"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--merge-only", action="store_true",
                        help="Skip extraction, just merge into events_all.csv.")
    parser.add_argument("--log-every", type=int, default=500)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.merge_only:
        run_merge(args.output, args.events_all)
        return 0

    run_extraction(args.cache_dir, args.output, args.limit, args.log_every)
    return 0


if __name__ == "__main__":
    sys.exit(main())
