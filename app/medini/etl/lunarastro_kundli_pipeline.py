"""Build charts + events_with_dasha from a LunarAstro kundlis.jsonl dump.

The LunarAstro research export ships one JSON object per line. Two
``category`` values matter:

  * ``personality`` — birth chart only (no life events).
  * ``event``       — birth chart PLUS a ``description`` that is a
                      comma-separated list of dated Astro-Databank-style
                      life events, e.g.::

       "Marriage 1903 (Mileva Maric), Prize 1922 (Nobel Prize),
        New Job 1902, Institutionalized 13 April 1955 (...)"

Only the ``event`` rows carry dated events, and they are self-contained
(their own birth fields), so this pipeline reads them directly. Two data
quirks are handled explicitly:

  * ``time_zone`` is a constant garbage value (``-05:30:00 hrs`` for every
    row), so the UTC offset is derived from longitude as Local Mean Time
    (``lon / 15``). Birth place/time in this source is noisy; Vimshottari
    dashas key off the Moon's nakshatra and are robust to hours of time
    error and to place, so dasha/dignity-by-sign survive it. Functional
    (house-lordship) nature is the noisiest derived feature — treat it as
    such.
  * some birth years are mis-scraped (e.g. a 2016 birth with 1960s
    events); events with implausible age (≤0 or >105) are dropped.

Outputs (schema matched to the analyzers in app/medini/ml):

  charts.parquet              person_id, asc_sign, birth_jd_used,
                              moon_lon, <graha>_sign, <graha>_house
  events_with_dasha.parquet   event_id, person_id, event_class,
                              event_subtype (polarity), event_date,
                              event_jd, birth_jd, age_at_event_years,
                              md_lord_at_event, ad_lord_at_event,
                              md_seq, ad_seq, source
  dasha_windows.parquet       person_id, md_lord, ad_lord, md_seq,
                              ad_seq, start_jd, end_jd, duration_days

Usage::

    python -m app.medini.etl.lunarastro_kundli_pipeline \\
        --input kundlis.jsonl --out-dir app/medini/data/lunarastro_run
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Final, Iterator

import pandas as pd
import swisseph as swe

from app.core.ephemeris_engine import (
    PLANETS, calculate_ascendant, calculate_d1_position, calculate_jd,
    calculate_ketu_d1, whole_sign_house,
)
from app.medini.etl.build_dasha_windows import _windows_for_person

logger = logging.getLogger(__name__)

GRAHAS: Final[tuple[str, ...]] = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
)

_MONTHS: Final[dict[str, int]] = {
    m.lower(): i for i, m in enumerate(
        ["January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"], start=1)
}
_YEAR_RE = re.compile(r"\b(1[5-9]\d\d|20[0-2]\d)\b")
_FULL_RE = re.compile(
    r"\b(\d{1,2})\s+([A-Za-z]+)\s+(1[5-9]\d\d|20[0-2]\d)\b")
_MONTHYEAR_RE = re.compile(r"\b([A-Za-z]+)\s+(1[5-9]\d\d|20[0-2]\d)\b")
_DOB_RE = re.compile(r"^\s*(\d{1,2}):(\d{1,2}):(\d{4})\s*$")
_COORD_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*°?\s*([NSEW])?", re.IGNORECASE)


# --------------------------------------------------------------------------
# Birth-field parsing
# --------------------------------------------------------------------------

def parse_birth_date(s: str) -> tuple[int, int, int] | None:
    """``"14:03:1879"`` (DD:MM:YYYY) → (1879, 3, 14). None if implausible."""
    m = _DOB_RE.match(s or "")
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31 and 1500 < y < 2030):
        return None
    return y, mo, d


def parse_time(s: str) -> float:
    """``"HH:MM:SS"`` → decimal hours; noon on parse failure."""
    try:
        parts = [int(x) for x in str(s).split(":")[:3]]
        while len(parts) < 3:
            parts.append(0)
        h, mi, se = parts
        if not (0 <= h < 24 and 0 <= mi < 60):
            return 12.0
        return h + mi / 60.0 + se / 3600.0
    except (ValueError, TypeError):
        return 12.0


def parse_coord(s: str) -> float | None:
    """``"9.9876° E"`` / ``"48.4011° N"`` / ``"-118.25"`` → signed degrees."""
    m = _COORD_RE.match(str(s))
    if not m:
        return None
    val = float(m.group(1))
    hemi = (m.group(2) or "").upper()
    if hemi in ("S", "W"):
        val = -abs(val)
    return val


def lmt_offset(longitude: float) -> float:
    """Local Mean Time UTC offset (hours) from longitude — the only usable
    offset here, since the source ``time_zone`` field is constant garbage."""
    return longitude / 15.0


# --------------------------------------------------------------------------
# Event extraction from the free-text description
# --------------------------------------------------------------------------

def split_top_level(desc: str) -> list[str]:
    """Split on commas that are NOT inside parentheses."""
    out, depth, cur = [], 0, ""
    for ch in desc:
        if ch == "(":
            depth += 1; cur += ch
        elif ch == ")":
            depth = max(0, depth - 1); cur += ch
        elif ch == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def _date_in_chunk(chunk: str) -> tuple[str, int, int] | None:
    """Return (ISO date, year, match_start). Full date > month+year (day=15)
    > year-only (Jul 1). None if no in-range year present. ``match_start`` is
    where the date token begins, so the caller can take the label as the text
    before it (excluding any leading month name)."""
    m = _FULL_RE.search(chunk)
    if m and m.group(2).lower() in _MONTHS:
        d, mo, y = int(m.group(1)), _MONTHS[m.group(2).lower()], int(m.group(3))
        if 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}", y, m.start()
    m = _MONTHYEAR_RE.search(chunk)
    if m and m.group(1).lower() in _MONTHS:
        mo, y = _MONTHS[m.group(1).lower()], int(m.group(2))
        return f"{y:04d}-{mo:02d}-15", y, m.start()
    m = _YEAR_RE.search(chunk)
    if m:
        y = int(m.group(1))
        return f"{y:04d}-07-01", y, m.start()
    return None


def extract_events(description: str) -> list[dict[str, object]]:
    """Parse a description into [{label, event_date, event_year}]. Only
    chunks carrying an in-range year are kept (undated traits dropped)."""
    out: list[dict[str, object]] = []
    for chunk in split_top_level(description or ""):
        chunk = chunk.strip()
        if not chunk:
            continue
        dated = _date_in_chunk(chunk)
        if dated is None:
            continue
        iso, year, start = dated
        # Label = text before the date token (drops any leading month name).
        label = re.sub(r"\s*\(.*$", "", chunk[:start]).strip(" -:–—")
        if not label:
            continue
        out.append({"label": label, "event_date": iso, "event_year": year})
    return out


# --------------------------------------------------------------------------
# Label → (harmonized event_class, polarity)
# --------------------------------------------------------------------------

# (substring-matched, case-insensitive) → (event_class, polarity_subtype)
_LABEL_RULES: Final[tuple[tuple[str, str, str], ...]] = (
    ("divorce", "divorce", "Adverse"),
    ("end significant relationship", "relationship", "Adverse"),
    ("end a significant", "relationship", "Adverse"),
    ("begin significant relationship", "relationship", "Beneficial"),
    ("marriage", "marriage", "Beneficial"),
    ("death of", "death", "Adverse"),
    ("widow", "death", "Adverse"),
    ("death", "death", "Adverse"),
    ("prize", "career", "Beneficial"),
    ("great achievement", "career", "Beneficial"),
    ("published", "career", "Beneficial"),
    ("new job", "career", "Beneficial"),
    ("new career", "career", "Beneficial"),
    ("start business", "career", "Beneficial"),
    ("begin major project", "career", "Beneficial"),
    ("end major project", "career", "Beneficial"),
    ("gain social status", "career", "Beneficial"),
    ("lose social status", "career", "Adverse"),
    ("retired", "career", "Neutral"),
    ("fired", "career", "Adverse"),
    ("joined group", "career", "Neutral"),
    ("begin a program of study", "education", "Beneficial"),
    ("end a program of study", "education", "Beneficial"),
    ("graduat", "education", "Beneficial"),
    ("medical diagnosis", "health", "Adverse"),
    ("accident", "health", "Adverse"),
    ("institutionalized", "health", "Adverse"),
    ("hospital", "health", "Adverse"),
    ("change in family", "family", "Neutral"),
    ("kids", "family", "Beneficial"),
    ("change residence", "personal", "Neutral"),
    ("change of lifestyle", "personal", "Neutral"),
    ("meet a significant person", "relationship", "Beneficial"),
)


def classify_label(label: str) -> tuple[str, str]:
    """(event_class, polarity_subtype). Unmatched → ('other', 'Neutral')."""
    low = label.lower()
    for needle, cls, pol in _LABEL_RULES:
        if needle in low:
            return cls, pol
    return "other", "Neutral"


# --------------------------------------------------------------------------
# Chart + dasha
# --------------------------------------------------------------------------

def compute_chart(person_id: str, y: int, mo: int, d: int, hour: float,
                  lat: float, lon: float) -> dict[str, object] | None:
    """Sidereal D1 chart row + birth_jd + moon_lon. None on ephemeris error."""
    try:
        jd = calculate_jd(y, mo, d, hour, lmt_offset(lon))
        asc = calculate_ascendant(jd, lat, lon)
        asc_sign = asc["sign"]
        pos = {name: calculate_d1_position(jd, pid) for name, pid in PLANETS.items()}
        pos["Ketu"] = calculate_ketu_d1(pos["Rahu"])
        row: dict[str, object] = {
            "person_id": person_id, "birth_jd_used": jd, "asc_sign": asc_sign,
            "moon_lon": pos["Moon"]["longitude"],
        }
        for g in GRAHAS:
            p = pos[g.title()]
            row[f"{g}_sign"] = p["sign"]
            row[f"{g}_house"] = whole_sign_house(asc_sign, p["sign"])
        return row
    except Exception as exc:  # swisseph edge cases on extreme dates/lats
        logger.debug("chart failed for %s: %s", person_id, exc)
        return None


def _read_event_rows(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("category") == "event":
                yield r


def build(input_path: Path, out_dir: Path) -> dict[str, int]:
    """Parse → chart → dasha → event-join. Writes the three parquets."""
    charts: list[dict[str, object]] = []
    windows: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    stats = {"event_rows": 0, "charts_built": 0, "events_parsed": 0,
             "events_joined": 0, "events_dropped_age": 0, "events_unmatched_window": 0}

    for r in _read_event_rows(input_path):
        stats["event_rows"] += 1
        bd = parse_birth_date(r.get("date_of_birth", ""))
        lat = parse_coord(r.get("latitude"))
        lon = parse_coord(r.get("longitude"))
        if bd is None or lat is None or lon is None:
            continue
        y, mo, d = bd
        person_id = f"LA:{r.get('id')}"
        chart = compute_chart(person_id, y, mo, d, parse_time(r.get("time")), lat, lon)
        if chart is None:
            continue

        parsed = extract_events(r.get("description", ""))
        if not parsed:
            continue

        win = _windows_for_person(person_id, chart["birth_jd_used"], chart["moon_lon"])
        charts.append(chart)
        windows.extend(win)
        stats["charts_built"] += 1
        birth_jd = chart["birth_jd_used"]

        for i, ev in enumerate(parsed):
            stats["events_parsed"] += 1
            ey, em, ed = (int(x) for x in str(ev["event_date"]).split("-"))
            event_jd = swe.julday(ey, em, ed, 12.0, swe.GREG_CAL)
            age = (event_jd - birth_jd) / 365.2425
            if not (0.0 < age <= 105.0):
                stats["events_dropped_age"] += 1
                continue
            md = ad = None
            md_seq = ad_seq = None
            for w in win:
                if w["start_jd"] <= event_jd <= w["end_jd"]:
                    md, ad = w["md_lord"], w["ad_lord"]
                    md_seq, ad_seq = w["md_seq"], w["ad_seq"]
                    break
            if md is None:
                stats["events_unmatched_window"] += 1
                continue
            cls, pol = classify_label(str(ev["label"]))
            events.append({
                "event_id": f"{person_id}:{i}", "person_id": person_id,
                "event_class": cls, "event_subtype": pol,
                "event_label": ev["label"], "event_date": ev["event_date"],
                "event_jd": event_jd, "birth_jd": birth_jd,
                "age_at_event_years": age,
                "md_lord_at_event": md, "ad_lord_at_event": ad,
                "md_seq": md_seq, "ad_seq": ad_seq, "source": "lunarastro",
            })
            stats["events_joined"] += 1

    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(charts).to_parquet(out_dir / "charts.parquet", index=False)
    pd.DataFrame(windows).to_parquet(out_dir / "dasha_windows.parquet", index=False)
    pd.DataFrame(events).to_parquet(out_dir / "events_with_dasha.parquet", index=False)
    logger.info("stats: %s", stats)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path,
                        default=Path("app/medini/data/lunarastro_run"))
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(build(args.input, args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
