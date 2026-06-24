"""Extract life events from cached HTML biographies using local Gemma 4 via Ollama.

This script processes all ~33k HTML files in `wayback_cache/` sequentially,
extracting the biography text and calling the local `gemma4:31b` model via
Ollama's `/api/generate` endpoint. The LLM is strictly prompted with a few-shot
example to return a JSON array, which is written to `events_llm_extracted.csv`.

A SQLite state database ensures the script is fully resumable — interrupted runs
can be restarted safely without re-processing files.

CLI:
    # Dry-run test on 3 files first:
    python -m app.medini.etl.llm_event_extractor --limit 3

    # Full run (estimate: ~100s/file × 33k files ≈ 38 days on a single GPU;
    #   consider running overnight and resuming, or deploying on a faster GPU):
    python -m app.medini.etl.llm_event_extractor

    # After extraction, merge into events_all.csv:
    python -m app.medini.etl.llm_event_extractor --merge-only
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Prompt Engineering
# Few-shot + strict instruction to counter Gemma-4's "helpful reformatting"   #
# --------------------------------------------------------------------------- #
# The biography is truncated to MAX_BIO_CHARS to reduce inference latency.
MAX_BIO_CHARS = 1500

_PROMPT_TEMPLATE = """\
You are a structured data extraction system. Your output must be ONLY a valid JSON array.
Do NOT include any markdown, backticks, explanations, or extra text.

Extract Marriage, Divorce, and Death events from the biography below.
Return a JSON array using EXACTLY this format (empty array [] if none found):

[
  {{"event_root": "Relationship", "event_subtype": "Marriage", "event_year": 1975, "event_date": "1975-06-12"}},
  {{"event_root": "Relationship", "event_subtype": "Divorce", "event_year": 1982, "event_date": ""}},
  {{"event_root": "Death", "event_subtype": "Disease", "event_year": 2010, "event_date": "2010-03-05"}}
]

Rules:
- event_root must be "Relationship" or "Death"
- event_subtype for Relationship must be "Marriage" or "Divorce"
- event_subtype for Death must be "Disease", "Accident", "Suicide", or "Unspecified"
- event_year must be an integer (not a string)
- event_date is "YYYY-MM-DD" or "" if the exact date is unknown
- Include ALL marriages and divorces if there were multiple

Biography:
{bio}

JSON array output:"""

CSV_COLUMNS = (
    "name", "event_code", "event_root", "event_subtype",
    "event_date", "event_year", "source_url"
)

OLLAMA_URL = "http://localhost:11434/api/generate"


# --------------------------------------------------------------------------- #
# SQLite State Store                                                            #
# --------------------------------------------------------------------------- #
class LLMStateDB:
    """Simple SQLite store to track which files have been processed."""

    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS processed (
                file_path TEXT PRIMARY KEY,
                status    TEXT,
                events_found INTEGER
            )
        """)
        self.conn.commit()

    def is_processed(self, file_path: str) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM processed WHERE file_path=?", (file_path,)
        ).fetchone() is not None

    def mark(self, file_path: str, status: str, n: int):
        self.conn.execute(
            "INSERT OR REPLACE INTO processed VALUES (?,?,?)",
            (file_path, status, n)
        )
        self.conn.commit()


# --------------------------------------------------------------------------- #
# HTML Parser                                                                   #
# --------------------------------------------------------------------------- #
def parse_biography(html_content: str) -> tuple[str, str]:
    """Return (name, biography_text) from a Wayback-cached AstroDatabank page."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Name: prefer the MediaWiki #firstHeading, fall back to <h1>
    tag = soup.select_one("#firstHeading") or soup.find("h1")
    name = tag.get_text(strip=True) if tag else ""

    # Biography text: all <p> blocks; #mw-content-text preferred to skip nav
    root = soup.select_one("#mw-content-text") or soup.find("body")
    paras: list[str] = []
    if root:
        for p in root.find_all("p"):
            t = p.get_text(" ", strip=True)
            if t:
                paras.append(t)

    return name, "\n".join(paras)[:MAX_BIO_CHARS]


# --------------------------------------------------------------------------- #
# LLM Caller                                                                    #
# --------------------------------------------------------------------------- #
def call_llm(model: str, bio_text: str, timeout_s: int = 600) -> list[dict]:
    """POST to Ollama and return parsed JSON list of events. Returns [] on failure."""
    prompt = _PROMPT_TEMPLATE.format(bio=bio_text)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "top_p": 1.0},
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout_s)
        r.raise_for_status()
        raw = r.json().get("response", "").strip()
    except requests.exceptions.Timeout:
        logger.warning("Ollama timeout after %ds", timeout_s)
        return []
    except Exception as exc:
        logger.error("Ollama request failed: %s: %s", type(exc).__name__, exc)
        return []

    # Strip markdown fences if the model still wraps despite instructions.
    for fence in ("```json", "```"):
        if raw.startswith(fence):
            raw = raw[len(fence):]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    # Gemma sometimes outputs a lone dict instead of a list — wrap it.
    if raw.startswith("{"):
        raw = f"[{raw}]"

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            logger.warning("LLM returned non-list JSON, skipping.")
            return []
        return parsed
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed: %s | raw[:300]: %s", exc, raw[:300])
        return []


# --------------------------------------------------------------------------- #
# Validation                                                                    #
# --------------------------------------------------------------------------- #
VALID_ROOTS = {"Relationship", "Death"}
VALID_REL_SUBTYPES = {"Marriage", "Divorce"}
VALID_DEATH_SUBTYPES = {"Disease", "Accident", "Suicide", "Unspecified"}


def validate_event(ev: dict) -> bool:
    if not isinstance(ev, dict):
        return False
    root = ev.get("event_root", "")
    subtype = ev.get("event_subtype", "")
    year = ev.get("event_year")
    if root not in VALID_ROOTS:
        return False
    if root == "Relationship" and subtype not in VALID_REL_SUBTYPES:
        return False
    if root == "Death" and subtype not in VALID_DEATH_SUBTYPES:
        return False
    if not isinstance(year, (int, float)) or not (1700 < int(year) < 2030):
        return False
    return True


# --------------------------------------------------------------------------- #
# Main pipeline                                                                 #
# --------------------------------------------------------------------------- #
def run_extraction(
    cache_dir: Path,
    output_csv: Path,
    state_db: LLMStateDB,
    model: str,
    limit: int | None,
    log_every: int = 10,
):
    html_files = sorted(cache_dir.glob("*.html"))
    if limit:
        html_files = html_files[:limit]
    total = len(html_files)
    logger.info("Found %d HTML files to process.", total)

    write_header = not output_csv.exists()
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with output_csv.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()

        processed = 0
        skipped = 0
        events_total = 0

        for idx, fp in enumerate(html_files, 1):
            fp_str = str(fp)

            if state_db.is_processed(fp_str):
                skipped += 1
                continue

            html = fp.read_text(encoding="utf-8", errors="ignore")
            name, bio = parse_biography(html)

            if not name or len(bio) < 50:
                state_db.mark(fp_str, "no_content", 0)
                processed += 1
                continue

            t0 = time.time()
            events = call_llm(model, bio)
            elapsed = time.time() - t0

            valid = [e for e in events if validate_event(e)]
            events_total += len(valid)

            for ev in valid:
                writer.writerow({
                    "name": name,
                    "event_code": f"{ev['event_root']} : {ev['event_subtype']}",
                    "event_root": ev["event_root"],
                    "event_subtype": ev["event_subtype"],
                    "event_date": ev.get("event_date", ""),
                    "event_year": int(ev["event_year"]),
                    "source_url": f"llm_extracted:{fp.name}",
                })
            fh.flush()

            state_db.mark(fp_str, "success", len(valid))
            processed += 1

            if idx % log_every == 0 or idx == total:
                logger.info(
                    "[%d/%d] %-40s → %d events (%.1fs) | total_events=%d",
                    idx, total, name[:40], len(valid), elapsed, events_total,
                )

    logger.info(
        "Extraction done. Processed=%d, skipped(already done)=%d, events=%d",
        processed, skipped, events_total,
    )
    return processed, events_total


def run_merge(extracted_csv: Path, target_csv: Path):
    """Append extracted events into the existing events_all.csv."""
    if not extracted_csv.exists():
        logger.error("Extracted CSV not found: %s", extracted_csv)
        return

    import pandas as pd
    existing = pd.read_csv(target_csv, low_memory=False) if target_csv.exists() else pd.DataFrame()
    new_rows = pd.read_csv(extracted_csv, low_memory=False)

    # De-duplicate by (name, event_root, event_year) to avoid double-counting.
    combined = pd.concat([existing, new_rows], ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["name", "event_root", "event_year"], keep="first")
    after = len(combined)
    logger.info("Merged %d new rows → %d unique events (dropped %d dupes)", len(new_rows), after, before - after)

    combined.to_csv(target_csv, index=False)
    logger.info("Wrote merged events to %s", target_csv)


# --------------------------------------------------------------------------- #
# CLI                                                                           #
# --------------------------------------------------------------------------- #
def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.llm_event_extractor",
        description="Extract life events from Wayback-cached HTML using local Gemma 4."
    )
    parser.add_argument("--cache-dir", type=Path,
                        default=Path("data/astro_databank/wayback_cache"))
    parser.add_argument("--output", type=Path,
                        default=Path("data/astro_databank/events_llm_extracted.csv"))
    parser.add_argument("--state-db", type=Path,
                        default=Path("data/astro_databank/llm_state.sqlite"))
    parser.add_argument("--events-all", type=Path,
                        default=Path("data/astro_databank/events_all.csv"),
                        help="Target events_all.csv to merge into.")
    parser.add_argument("--model", type=str, default="gemma4:31b")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap number of files (for testing).")
    parser.add_argument("--merge-only", action="store_true",
                        help="Skip extraction, just merge output into events_all.csv.")
    parser.add_argument("--log-every", type=int, default=10,
                        help="Log progress every N files.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.merge_only:
        run_merge(args.output, args.events_all)
        return 0

    state_db = LLMStateDB(args.state_db)
    run_extraction(args.cache_dir, args.output, state_db, args.model, args.limit, args.log_every)

    return 0


if __name__ == "__main__":
    sys.exit(main())
