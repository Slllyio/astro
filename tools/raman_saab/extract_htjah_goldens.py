"""HTJAH golden extractor — Raman's worked charts, gated on his OWN printed dasha balance.

The problem this solves
-----------------------
The golden corpus holds 146 records mined from *How to Judge a Horoscope* Vols I & II, but the
books present far more worked judgments than that: a 2026-08-23 audit counted **136 "Conclusion"
paragraphs sitting on chart numbers the corpus never extracted** (81 in Vol I, 55 in Vol II).
That backlog — not the judge — is the project's declared remaining accuracy lever
(NORTH STAR PLAYBOOK rule 7).

Why extraction is dangerous, and the gate that makes it safe
------------------------------------------------------------
HTJAH gives birth DATA (``Born 8-10-1935 at 11-30 a.m. (I.S.T.) at 13 N 75 E``) rather than the
printed longitudes Notable Horoscopes gives, so a record must be FRESH CAST — and the scans are
OCR-noisy in exactly the fields that casting depends on. Observed corruption in this very corpus:
``Born 24-3-7883`` (a four-digit year with a mangled leading digit), coordinates truncated by a
line break, ``3/4-12-1953`` (an ambiguous midnight-straddling date). A mis-parsed birth line
yields a WRONG chart, and a wrong chart scored against Raman's verdict silently corrupts the
fidelity measurement — the one number this project exists to keep honest.

So this tool never trusts its own parse. Vol II prints, for most charts, **"Balance of <Lord>
Dasa at birth: N years, M months and D days"** — a value fixed by the Moon's longitude at birth,
and therefore an independent function of the exact date, time and place. The extractor:

    1. parses the birth line,
    2. casts the chart,
    3. computes the Vimshottari balance from the cast Moon,
    4. compares it against Raman's PRINTED balance,
    5. and emits the record ONLY if the dasha lord matches and the remaining duration agrees
       within tolerance.

A chart that fails the gate is reported and SKIPPED, never guessed at. This is the project's
standing discipline — verify against Raman's own published output, never against engine
self-assertion (CLAUDE.md, "Verify against Raman, never against engine self-output").

What it emits
-------------
DRAFT records only (``verdict_review="DRAFT"``). A DRAFT is NOT scored by the accuracy ratchet —
only ``verdict_review == "CONFIRMED"`` verdicts are. So extraction can never inflate 261/294 by
itself; it grows the cast corpus (rule-liveness coverage, differential astronomy) and builds a
reviewable queue. Promoting a DRAFT to CONFIRMED remains a per-record doctrine review against
Raman's text, and the never-confirm-to-pad rule stands.

Usage:
    py -3.12 -m tools.raman_saab.extract_htjah_goldens                # dry-run report
    py -3.12 -m tools.raman_saab.extract_htjah_goldens --emit         # JSONL to stdout
    py -3.12 -m tools.raman_saab.extract_htjah_goldens --tolerance-days 45
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vim

_SOURCES = Path("data/knowledge_library/sources")
_BOOKS: dict[str, Path] = {
    "HTJAH-I": _SOURCES / "how_to_judge_a_horoscope_raman" / "chapter_001_full-text-unsplit.md",
    "HTJAH-II": _SOURCES / "how_to_judge_horoscope_raman2" / "chapter_001_full-text-unsplit.md",
}
_GOLDENS = Path("tests/fixtures/raman_goldens.jsonl")

#: Raman's Indian charts are overwhelmingly I.S.T. (+5:30) or L.M.T. (longitude/15).
#: A chart whose zone marker we cannot read is REJECTED rather than assumed — a 30-minute
#: zone error moves the Moon ~15' and can flip the dasha balance by months.
_IST = 5.5

_CHART_RE = re.compile(r"Chart\s*No\.?\s*(\d+)", re.IGNORECASE)
# Born <d>-<m>-<yyyy> at <h>[-.:]<mm> a.m./p.m. (ZONE) at <lat> N/S[, ] <lon> E/W
_BORN_RE = re.compile(
    r"Born\s*(?:on\s*)?(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{3,4})"      # date
    r"[^\n]{0,18}?at\s*(?:about\s*)?(\d{1,2})\s*(?:[-.:]\s*(\d{1,2}))?\s*"    # time
    r"([ap])\.?\s*m",                                                          # meridiem
    re.IGNORECASE)
_ZONE_RE = re.compile(r"\(\s*([ILG])\.?\s*[MS]?\.?\s*[TM]?\.?\s*\)", re.IGNORECASE)
#: Raman prints coordinates as ``DD <dir> MM`` — the hemisphere letter sits BETWEEN the degrees
#: and the minutes (``13 N 10, 76 E 10``; ``13° N. \n 77 E35.``; ``51 N 30, 0 W 05``), and the
#: pair is routinely split across a line break by the scan. Minutes are optional and, when the
#: next token is a 3-digit number, it is the NEXT coordinate's degrees rather than minutes —
#: hence the {1,2} bound plus the trailing boundary.
#: BOTH minute orders occur in the scans and each must be accepted:
#:   ``13° 30' N``  — minutes BEFORE the hemisphere letter
#:   ``20 N 56``    — hemisphere letter BETWEEN degrees and minutes (Raman's dominant form)
#:   ``77 E35``     — the same, run together with no space
#: They are matched as ordered alternatives rather than one pattern with two optional minute
#: groups: a single pattern's trailing group greedily swallows the NEXT coordinate's degrees
#: ("13° 30' N, 77" reads 77 as the latitude's minutes), which silently produced a plausible but
#: wrong longitude — the exact failure mode this whole tool exists to prevent.
#: Hemisphere is guarded by (?![A-Za-z]) rather than \b: "77 E35" has no word boundary between
#: "E" and "3", and requiring one loses the longitude entirely.
_DEG = r"(\d{1,3})\s*(?:°|\*|o|º)?\s*"
_HEMI = r"([NSEW])(?![A-Za-z])"
_COORD_MIN_FIRST = re.compile(_DEG + r"(\d{1,2})(?!\d)\s*[’']\s*[.,]?\s*" + _HEMI, re.IGNORECASE)
#: Minutes-after must not be the next coordinate's degrees, so it is refused when a degree mark
#: or another hemisphere letter follows it.
_COORD_MIN_LAST = re.compile(
    _DEG + r"[.,]?\s*" + _HEMI + r"[.,]?\s*(\d{1,2})(?!\d)(?!\s*(?:°|\*|º|[NSEW]))\s*[’']?",
    re.IGNORECASE)
_COORD_BARE = re.compile(_DEG + r"[.,]?\s*" + _HEMI, re.IGNORECASE)
_BAL_RE = re.compile(
    r"Balance of\s*([A-Z][a-z]+)(?:'s|’s)?\s*Dasa at birth\s*[:\-—]?\s*"
    r"(?:(\d+)\s*years?)?[,\s]*(?:(\d+)\s*months?)?[,\s]*(?:and)?\s*(?:(\d+)\s*days?)?",
    re.IGNORECASE)

_LORDS = {"Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"}


@dataclass
class Candidate:
    """One chart presentation found in a book, with whatever could be parsed from it."""
    book: str
    chart_no: int
    line: int
    birth: Optional[dict[str, Any]] = None
    printed_lord: Optional[str] = None
    printed_years: Optional[float] = None
    conclusion: Optional[str] = None
    # filled by the gate
    cast_lord: Optional[str] = None
    cast_years: Optional[float] = None
    status: str = "unparsed"
    reason: str = ""
    notes: list[str] = field(default_factory=list)


def _dms(deg: str, minute: Optional[str]) -> float:
    return int(deg) + (int(minute) / 60.0 if minute else 0.0)


def _scan_coords(text: str) -> list[tuple[str, str, Optional[str]]]:
    """Every ``(degrees, hemisphere, minutes|None)`` in `text`, left to right.

    The three printed forms are tried in decreasing specificity at each position, and whichever
    matches consumes its span so a later form cannot re-read part of it. Scanning positionally
    (rather than running three independent finditers) is what keeps ``13° 30' N, 77° 45' E``
    from being read as one coordinate with 77 as its minutes."""
    out: list[tuple[str, str, Optional[str]]] = []
    pos = 0
    while pos < len(text):
        best = None
        for rx, has_min_first in ((_COORD_MIN_FIRST, True), (_COORD_MIN_LAST, False),
                                  (_COORD_BARE, None)):
            m = rx.match(text, pos)
            if m:
                best = (m, has_min_first)
                break
        if best is None:
            pos += 1
            continue
        m, kind = best
        if kind is True:
            out.append((m.group(1), m.group(3).upper(), m.group(2)))
        elif kind is False:
            out.append((m.group(1), m.group(2).upper(), m.group(3)))
        else:
            out.append((m.group(1), m.group(2).upper(), None))
        pos = m.end()
    return out


def _parse_birth(block: str) -> tuple[Optional[dict[str, Any]], list[str]]:
    """Birth dict from a chart block, or (None, reasons). Refuses anything ambiguous."""
    notes: list[str] = []
    m = _BORN_RE.search(block)
    if not m:
        return None, ["no parseable Born line"]
    day, month, year, hh, mm, mer = m.groups()
    day, month, year, hh = int(day), int(month), int(year), int(hh)
    mm = int(mm) if mm else 0

    # OCR year guard: Raman's nativities are 1700-1999. A 3-digit or out-of-range year is
    # corrupt (observed: "24-3-7883"), and we do NOT try to repair it.
    if not (1700 <= year <= 1999):
        return None, [f"implausible year {year} (OCR)"]
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None, [f"implausible date {day}-{month}"]
    if not (1 <= hh <= 12):
        return None, [f"implausible hour {hh}"]

    hour24 = hh % 12 + (12 if mer.lower() == "p" else 0)

    zm = _ZONE_RE.search(block[:m.end() + 40])
    zone = zm.group(1).upper() if zm else None
    if zone is None:
        return None, ["no zone marker (I.S.T./L.M.T./G.M.T.)"]

    # The coordinate pair frequently straddles a line break, so scan a generous tail and take
    # the FIRST latitude token and the FIRST longitude token found.
    tail = block[m.end(): m.end() + 160]
    lat = lon = None
    for deg_s, hemi, minute in _scan_coords(tail):
        deg = int(deg_s)
        val = _dms(deg_s, minute)
        if hemi in ("N", "S") and lat is None:
            if deg > 90:
                continue                                   # OCR noise, not a latitude
            lat = -val if hemi == "S" else val
        elif hemi in ("E", "W") and lon is None:
            if deg > 180:
                continue
            lon = -val if hemi == "W" else val
    if lat is None:
        return None, ["no latitude"]
    if lon is None:
        return None, ["longitude truncated (line break)"]
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None, [f"coords out of range {lat},{lon}"]

    if zone == "I":
        tz = _IST
    elif zone == "L":
        tz = round(lon / 15.0, 4)
        notes.append("L.M.T. — zone derived from longitude")
    else:                                    # G.M.T.
        tz = 0.0
    return {"dt": f"{year:04d}-{month:02d}-{day:02d}T{hour24:02d}:{mm:02d}:00",
            "tz": tz, "lat": round(lat, 4), "lon": round(lon, 4)}, notes


def _parse_balance(block: str) -> tuple[Optional[str], Optional[float]]:
    """(lord, years) from Raman's printed 'Balance of X Dasa at birth'."""
    m = _BAL_RE.search(block)
    if not m:
        return None, None
    lord, y, mo, d = m.groups()
    lord = lord.capitalize()
    if lord not in _LORDS:
        return None, None
    if y is None and mo is None and d is None:
        return lord, None
    years = (int(y or 0)) + (int(mo or 0)) / 12.0 + (int(d or 0)) / 365.2425
    return lord, years


def _conclusion(block: str) -> Optional[str]:
    m = re.search(r"Conclusion\s*[:\.\-—]\s*(.{40,600}?)(?:\n\s*\n|Chart\s*No)", block, re.S | re.I)
    return " ".join(m.group(1).split()) if m else None


def collect(book: str, path: Path) -> list[Candidate]:
    """Every chart presentation in one book, with birth/balance/conclusion parsed."""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    starts: list[tuple[int, int]] = []
    for i, line in enumerate(lines):
        m = _CHART_RE.search(line)
        if m:
            starts.append((int(m.group(1)), i))
    out: list[Candidate] = []
    for idx, (no, i) in enumerate(starts):
        end = starts[idx + 1][1] if idx + 1 < len(starts) else len(lines)
        block = "\n".join(lines[i:min(end, i + 120)])
        if not re.search(r"\bBorn\b", block[:400], re.IGNORECASE):
            continue                                    # a cross-reference, not a presentation
        c = Candidate(book=book, chart_no=no, line=i + 1)
        c.birth, notes = _parse_birth(block)
        c.notes.extend(notes)
        c.printed_lord, c.printed_years = _parse_balance(block)
        c.conclusion = _conclusion(block)
        if c.birth is None:
            c.status, c.reason = "unparsed", "; ".join(notes)
        out.append(c)
    return out


def gate(c: Candidate, tolerance_days: float) -> Candidate:
    """Cast the chart and require Raman's OWN printed dasha balance to reproduce."""
    if c.birth is None:
        return c
    if c.printed_lord is None:
        c.status, c.reason = "ungated", "no printed dasha balance to verify against"
        return c
    date, _, clock = c.birth["dt"].partition("T")
    y, mo, d = (int(x) for x in date.split("-"))
    hh, mm = (int(x) for x in clock.split(":")[:2])
    try:
        chart = cast_chart(BirthData(name=f"{c.book} chart {c.chart_no}", year=y, month=mo, day=d,
                                     hour=hh, minute=mm, tz_offset=float(c.birth["tz"]),
                                     latitude=float(c.birth["lat"]),
                                     longitude=float(c.birth["lon"])), ayanamsa="raman")
    except Exception as exc:                                  # noqa: BLE001 — report, never crash
        c.status, c.reason = "cast-failed", f"{type(exc).__name__}: {exc}"
        return c
    moon = chart.planets.get("Moon")
    if moon is None:
        c.status, c.reason = "cast-failed", "no Moon in cast chart"
        return c
    md = vim.calculate_vimshottari_mahadasha(moon.lon, chart.jd_ut)
    c.cast_lord = str(md["mahadasha_lord"])
    c.cast_years = float(md["years_remaining"])
    if c.cast_lord != c.printed_lord:
        c.status = "gate-failed"
        c.reason = f"dasha lord {c.cast_lord} != Raman's {c.printed_lord}"
        return c
    if c.printed_years is None:
        c.status, c.reason = "gate-partial", "lord matches; Raman printed no duration"
        return c
    delta_days = abs(c.cast_years - c.printed_years) * 365.2425
    if delta_days > tolerance_days:
        c.status = "gate-failed"
        c.reason = (f"balance off by {delta_days:.0f}d "
                    f"(cast {c.cast_years:.2f}y vs printed {c.printed_years:.2f}y)")
        return c
    c.status = "verified"
    c.reason = f"lord {c.cast_lord}, balance within {delta_days:.0f}d"
    return c


def existing_chart_numbers() -> set[tuple[str, int]]:
    """(book, chart_no) already present in the golden corpus."""
    have: set[tuple[str, int]] = set()
    if not _GOLDENS.is_file():
        return have
    for raw in _GOLDENS.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        rec = json.loads(s)
        m = re.search(r"Chart\s*(?:No\.?)?\s*(\d+)", str(rec.get("name", "")), re.IGNORECASE)
        if m:
            have.add((str(rec.get("book", "")), int(m.group(1))))
    return have


def to_record(c: Candidate) -> dict[str, Any]:
    """A DRAFT golden record. The verdict is deliberately left unset — this tool extracts
    CHARTS, and the verdict is a doctrine judgment a reviewer makes by reading Raman."""
    return {
        "id": f"{c.book}.x{c.chart_no}",
        "book": c.book,
        "name": f"Chart {c.chart_no} (extraction pending review)",
        "case_type": "worked_example",
        "birth": c.birth,
        "lagna_sign": None,
        "stated_positions": {},
        "expected_verdicts": {},
        "expected_longevity": None,
        # Track B only. Track A asserts the engine reproduces Raman's PRINTED placements, and
        # these records have none — the HTJAH chart grids OCR into unusable fragments, which is
        # precisely why the dasha balance is the gate instead.
        "track_eligibility": ["B"],
        "confidence": 0.5,
        "citations": [f"{c.book}:{c.line}"],
        "_extraction": {
            "tool": "extract_htjah_goldens",
            "gate": "raman_printed_dasha_balance",
            "printed_balance": {"lord": c.printed_lord, "years": c.printed_years},
            "cast_balance": {"lord": c.cast_lord, "years": c.cast_years},
            "notes": c.notes,
            "conclusion_prose": c.conclusion,
        },
    }


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")          # type: ignore[attr-defined]
    except Exception:                                      # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit", action="store_true", help="print JSONL for verified NEW charts")
    ap.add_argument("--tolerance-days", type=float, default=30.0,
                    help="max disagreement with Raman's printed dasha balance (default 30)")
    ap.add_argument("--book", choices=sorted(_BOOKS), help="limit to one book")
    a = ap.parse_args(argv)

    have = existing_chart_numbers()
    books = {a.book: _BOOKS[a.book]} if a.book else _BOOKS
    all_c: list[Candidate] = []
    for tag, path in books.items():
        if not path.is_file():
            print(f"[skip] {tag}: corpus file absent", file=sys.stderr)
            continue
        for c in collect(tag, path):
            all_c.append(gate(c, a.tolerance_days))

    new = [c for c in all_c if (c.book, c.chart_no) not in have]
    verified_new = [c for c in new if c.status == "verified"]

    from collections import Counter
    print(f"[htjah] chart presentations found : {len(all_c)}")
    print(f"[htjah] already in golden corpus  : {len(all_c) - len(new)}")
    print(f"[htjah] NOT yet extracted         : {len(new)}")
    print(f"[htjah] status of the unextracted : "
          f"{dict(Counter(c.status for c in new))}")
    print(f"[htjah] VERIFIED against Raman's printed dasha balance : {len(verified_new)}")
    withconc = sum(1 for c in verified_new if c.conclusion)
    print(f"[htjah]   ...of which carry a Conclusion paragraph      : {withconc}")

    if not a.emit:
        for c in sorted(new, key=lambda x: (x.book, x.chart_no))[:200]:
            flag = {"verified": "OK ", "gate-failed": "GATE", "unparsed": "PARSE",
                    "ungated": "NOGATE", "gate-partial": "PART", "cast-failed": "CAST"}.get(c.status, "?")
            print(f"  {flag:6s} {c.book}.{c.chart_no:<4d} L{c.line:<6d} {c.reason[:78]}")
        return 0

    for c in sorted(verified_new, key=lambda x: (x.book, x.chart_no)):
        print(json.dumps(to_record(c), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
