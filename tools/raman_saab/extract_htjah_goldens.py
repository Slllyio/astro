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
only ``verdict_review == "CONFIRMED"`` verdicts are. So extraction can never inflate the accuracy
figure by itself (the live value lives in tests/fixtures/golden_accuracy_baseline.json — do not
restate it here, it moves); it grows the cast corpus (rule-liveness coverage, differential
astronomy) and builds a reviewable queue. Promoting a DRAFT to CONFIRMED remains a per-record doctrine review against
Raman's text, and the never-confirm-to-pad rule stands.

Usage:
    py -3.12 -m tools.raman_saab.extract_htjah_goldens                # dry-run report
    py -3.12 -m tools.raman_saab.extract_htjah_goldens --emit         # JSONL to stdout
    py -3.12 -m tools.raman_saab.extract_htjah_goldens --pdf VolI.pdf --pdf VolII.pdf
    py -3.12 -m tools.raman_saab.extract_htjah_goldens --tolerance-deg 2.5
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
    # 3HC added 2026-08-30 (corpus-growth survey): "Three Hundred Important Combinations"
    # presents ~57 worked charts in exactly the same shape this tool already parses — a
    # "Chart No. N.—Born on D-M-YYYY at H-MM a.m./p.m. ... Lat ... Long ..." line, chart
    # grids that OCR into unusable fragments, and a printed "Balance of <lord> Dasa at
    # birth" which IS this tool's gate. The `_raman` scan is used deliberately: the
    # `_complete` scan of the same book carries materially worse OCR on exactly the birth
    # lines ("3l- Z- 19t0" for a date, and a chart-2 time that disagrees with this scan).
    # Feasibility validated before adding: Chart 1 (Raman's own nativity, 8-8-1912) casts
    # to a Mars balance of 6y1m5d against his printed 6-1-6 — one day.
    "3HC": _SOURCES / "three_hundred_combinations_raman" / "chapter_001_full-text-unsplit.md",
}
_GOLDENS = Path("tests/fixtures/raman_goldens.jsonl")

#: Raman's Indian charts are overwhelmingly I.S.T. (+5:30) or L.M.T. (longitude/15).
#: A chart whose zone marker we cannot read is REJECTED rather than assumed — a 30-minute
#: zone error moves the Moon ~15' and can flip the dasha balance by months.
_IST = 5.5

_CHART_RE = re.compile(r"Chart\s*No\.?\s*(\d+)", re.IGNORECASE)
#: Same Born line, but with the MERIDIEM OCR-DESTROYED ("7-35 fi.m.", "2-30 j).m.",
#: "11-50 n.m."). Added 2026-08-30 for the 3HC scan, where this damage accounts for most
#: unparsed presentations. Ambiguity is SAFE here and nowhere else: the printed dasha
#: balance is a hard arbiter, so the parser may hand BOTH readings (a.m. and p.m.) to the
#: gate and keep a chart only when EXACTLY ONE of them reproduces Raman's own printed
#: balance. A 12-hour error moves the Moon ~6.6 deg — far outside the 2.5 deg tolerance —
#: so the wrong branch cannot survive. If both branches somehow passed, the chart is
#: dropped as genuinely ambiguous rather than guessed.
# Born <d>-<m>-<yyyy> at <h>[-.:]<mm> a.m./p.m. (ZONE) at <lat> N/S[, ] <lon> E/W
_BORN_RE = re.compile(
    r"Born\s*(?:on\s*)?(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{3,4})"      # date
    r"[^\n]{0,18}?at\s*(?:about\s*)?(\d{1,2})\s*(?:[-.:]\s*(\d{1,2}))?\s*"    # time
    r"([ap])\.?\s*m",                                                          # meridiem
    re.IGNORECASE)
#: TRADITIONAL TIME: "Born on 28-7-1896 at Gh. 10 after Sunrise" — ghatis (and vighatis)
#: elapsed since sunrise, 1 ghati = 24 minutes, 1 vighati = 24 seconds. Raman prints this form
#: throughout 3HC (and occasionally in HTJAH), and it accounts for the single largest block of
#: otherwise-parseable presentations the tool used to drop. Resolving it needs the day's actual
#: sunrise, which the engine already computes (chart/kala_context._sunrise_sunset); the result
#: is then handed to the SAME dasha-balance gate as any clock time, so a mis-parsed ghati count
#: cannot enter the corpus.
_BORN_GHATI_RE = re.compile(
    r"Born\s*(?:on\s*)?(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{3,4})"        # date
    r"[^\n]{0,24}?(?:at\s*)?(?:Gh|gha)[.a]?\s*(\d{1,2})"                          # ghatis
    r"(?:\s*[-.]\s*(\d{1,2}))?"                                                     # vighatis
    r"[^\n]{0,12}?after\s*Sunris",                                                   # anchor
    re.IGNORECASE)
_BORN_LOOSE_RE = re.compile(
    r"Born\s*(?:on\s*)?(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{3,4})"      # date
    r"[^\n]{0,20}?at\s*(?:about\s*)?(\d{1,2})\s*[-.:]\s*(\d{1,2})"             # time (mm required)
    r"(?![-.:\d])",                                                             # not a longer run
    re.IGNORECASE)
#: Zone marker. Parentheses are optional and the separator is a dot OR a hyphen, because all of
#: "(I.S.T.)", "(L.M.T)", "L.T." (bare) and "(L-T.)" occur. The leading letter is what matters:
#: I -> Indian Standard Time, L -> Local (mean) Time, G -> Greenwich.
#: The leading letter is OCR-fragile: "I.S.T." prints as "(/. S. T.)" in the 3HC scan, and a
#: bare "/" or "|" or "1" or "l" all stand in for I. Getting this wrong is NOT harmless — an
#: unrecognised zone silently falls back to LMT, a ~20-minute error on an Indian chart — so the
#: substitutes are accepted and normalised to I. The gate still arbitrates the result.
_ZONE_RE = re.compile(
    r"\(?\s*(?:\b([ILG])|([/|1l]))[.\-]\s?(?:[MS][.\-]\s?)?T\.?\s*\)?", re.IGNORECASE)
#: Longitude printed as TIME rather than arc: "Long. 5h. 10m. 20s. E" == 5h10m20s x 15 deg.
#: The minutes token is written ``m.`` but OCR renders it ``in.``/``rn.``/``n.`` often enough
#: to strand whole presentations (3HC chart 1: "Long. 5 h. 10 in. 20 s. E"). Accepting those
#: spellings costs nothing: the token sits between two digit runs inside an anchored
#: ``Long. ... E/W`` frame, and a wrong reading cannot survive the dasha-balance gate.
_LON_TIME_RE = re.compile(
    r"Long\.?\s*(\d{1,2})\s*h\.?\s*(?:(\d{1,2})\s*(?:m|in|rn|n)\.?)?"
    r"\s*(?:(\d{1,2})\s*s\.?)?\s*([EW])",
    re.IGNORECASE)
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
#: The degree mark is OCR-rendered as a double-quote often enough to strand a whole
#: presentation (3HC: 'Lat. 13" N.'). It is accepted here as a degree mark even though the
#: double-prime conventionally means SECONDS: the group is optional and non-capturing, so
#: this only lets the scanner step over the character on its way to the hemisphere letter,
#: and a misread coordinate cannot survive the dasha-balance gate.
_DEG = r"(\d{1,3})\s*(?:°|\*|o|º|\"|”|“)?\s*"
#: The hemisphere letter is OCR-fragile: N prints as ".V", "V" or "IV" in the 3HC scan
#: ("Lat. 9° .V ;", "hat. 17°/V."). Those are normalised to N by _hemi(); S/E/W show no
#: comparable substitutes in the corpus, so none are invented for them.
_HEMI = r"(?:\.?\s*)([NSEW]|IV|V)(?![A-Za-z])"
_COORD_MIN_FIRST = re.compile(_DEG + r"(\d{1,2})(?!\d)\s*[’']\s*[.,]?\s*" + _HEMI, re.IGNORECASE)
#: Minutes-after must not be the next coordinate's degrees, so it is refused when a degree mark
#: or another hemisphere letter follows it.
_COORD_MIN_LAST = re.compile(
    _DEG + r"[.,]?\s*" + _HEMI + r"[.,]?\s*(\d{1,2})(?!\d)(?!\s*(?:°|\*|º|[NSEW]))\s*[’']?",
    re.IGNORECASE)
_COORD_BARE = re.compile(_DEG + r"[.,]?\s*" + _HEMI, re.IGNORECASE)
#: Two printings phrase the balance differently and BOTH are accepted:
#:   scanned Bangalore ed. — "Balance of Ketu Dasa at birth : 6 years, 4 months and 4 days."
#:   Motilal 12th ed.      — "Balance of Ketu Dasha at birth: Years 5-0-24."  (Y-M-D, compact)
#: The compact form is the more trustworthy of the two: it cannot be truncated mid-phrase the
#: way "6 years, 4 months and..." is when a line breaks.
#: The dasha word and the year/month/day words are both OCR-fragile in the 3HC scan
#: ("Balance of Moon's Da->a at Birth, yens", "Balance of Mars Dasa at birth, \\ ear-. 5-10-7").
#: `_DASA` accepts the mangled spellings; the numeric groups are unchanged, so a garbled
#: NUMBER still fails to match rather than being guessed at.
_DASA = r"Da[s\->]{1,3}h?a"
_BAL_PROSE_RE = re.compile(
    r"Balance of\s*([A-Z][a-z]+)(?:'s|’s)?\s*" + _DASA + r"\s*at\s*birth\s*[:\-—,]?\s*"
    r"(?:(\d+)\s*y[ea]{1,3}rs?)?[,\s]*(?:(\d+)\s*months?)?[,\s]*(?:and)?\s*(?:(\d+)\s*days?)?",
    re.IGNORECASE)
_BAL_COMPACT_RE = re.compile(
    r"Balance of\s*([A-Z][a-z]+)(?:'s|’s)?\s*" + _DASA + r"\s*at\s*birth\s*[:\-—,]?\s*"
    r"(?:y[ea]{1,3}rs?[.,\s]*)?(\d{1,3})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})",
    re.IGNORECASE)

_LORDS = {"Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"}
#: Vimshottari mahadasha spans, used to convert a balance disagreement into the Moon-longitude
#: disagreement that actually caused it.
_SPAN: Final[dict[str, int]] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
#: Default gate width, in DEGREES of Moon longitude. Chosen from measurement, not taste: across
#: 227 charts carrying a printed balance, the offset between Raman's implied Moon and a modern
#: cast has median -0.010 deg, mean +0.161, stdev 1.248 — no systematic bias, so there is nothing
#: to calibrate, only per-chart noise from era table interpolation and rounded birth times.
#: 2.5 deg is ~2 sigma of that noise and admits 209 of the 227.
_TOL_DEG: Final[float] = 2.5
#: A nakshatra is 360/27 degrees; a mahadasha maps one-to-one onto it, which is what makes the
#: balance invertible back to a Moon longitude.
_NAK_DEG: Final[float] = 360.0 / 27.0


@dataclass
class Candidate:
    """One chart presentation found in a book, with whatever could be parsed from it."""
    book: str
    chart_no: int
    line: int
    origin: str = "corpus"
    birth: Optional[dict[str, Any]] = None
    printed_lord: Optional[str] = None
    printed_years: Optional[float] = None
    conclusion: Optional[str] = None
    # filled by the gate
    cast_lord: Optional[str] = None
    cast_years: Optional[float] = None
    moon_offset_deg: Optional[float] = None
    house: Optional[int] = None
    status: str = "unparsed"
    reason: str = ""
    notes: list[str] = field(default_factory=list)
    #: "a"/"p" when this candidate is one of two meridiem branches submitted to the gate
    #: (see the MERIDIEM-DESTROYED FALLBACK in collect_text); None for a printed meridiem.
    meridiem_branch: Optional[str] = None


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
            out.append((m.group(1), _hemi(m.group(3)), m.group(2)))
        elif kind is False:
            out.append((m.group(1), _hemi(m.group(2)), m.group(3)))
        else:
            out.append((m.group(1), _hemi(m.group(2)), None))
        pos = m.end()
    return out


def _flatten_head(block: str, n_lines: int = 10) -> str:
    """The block's first `n_lines` with newlines collapsed to spaces, then the remainder.

    Every birth-line pattern here is deliberately newline-bounded (`[^\n]{0,18}?`) so a
    match cannot wander across unrelated prose. That is right for HTJAH, whose presentations
    sit on one or two lines — but the 3HC scan breaks the SAME datum across lines much more
    aggressively ("Chart No. 6 .—Born on" with the date on the next line; the latitude
    routinely a line below the time), which stranded 25 of 63 candidates on "no parseable
    Born line" and 11 more on "no latitude". Flattening only the HEADER region keeps the
    newline bound doing its job everywhere else: the presentation's own datum lines are
    joined, the discussion prose below is not.
    """
    lines = block.splitlines()
    head = " ".join(lines[:n_lines])
    tail = "\n".join(lines[n_lines:])
    return head + ("\n" + tail if tail else "")


def _resolve_ghati(year: int, month: int, day: int, lat: float, lon: float,
                   tz: float, ghatis: tuple[int, int]) -> Optional[tuple[int, int]]:
    """Local clock (hour, minute) for `ghatis` elapsed since that day's sunrise.

    1 ghati = 24 minutes, 1 vighati = 24 seconds (60 ghatis to the day). Sunrise comes from
    the engine's own swisseph call rather than an almanac approximation, so the extraction
    and the judge agree about the sky. Returns None where sunrise is not computable (polar
    latitudes), rather than guessing."""
    from app.raman_saab.chart.kala_context import _sunrise_sunset
    from app.raman_saab.chart.model import BirthData
    probe = BirthData(name="ghati-probe", year=year, month=month, day=day, hour=12, minute=0,
                      tz_offset=tz, latitude=lat, longitude=lon)
    try:
        sunrise_jd, _sunset = _sunrise_sunset(probe, "raman")
    except Exception:
        return None
    # sunrise_jd is UT; convert to local clock, then add the elapsed ghatis.
    frac_ut = (sunrise_jd + 0.5) % 1.0                 # JD day starts at noon
    local_hours = frac_ut * 24.0 + tz
    total = local_hours + ghatis[0] * 0.4 + ghatis[1] * (0.4 / 60.0)
    total %= 24.0
    return int(total), int(round((total % 1.0) * 60)) % 60


def _hemi(tok: str) -> str:
    """Hemisphere letter, with the scan's OCR substitutes for N folded back."""
    tok = tok.upper()
    return "N" if tok in ("V", "IV") else tok


def _parse_birth(block: str, *, meridiem: Optional[str] = None,
                 ) -> tuple[Optional[dict[str, Any]], list[str]]:
    """Birth dict from a chart block, or (None, reasons). Refuses anything ambiguous.

    `meridiem` ("a"/"p") forces the reading when the printed one is OCR-destroyed; the
    caller then submits BOTH branches to the dasha gate and keeps the one Raman's printed
    balance confirms (see _BORN_LOOSE_RE)."""
    notes: list[str] = []
    ghatis: Optional[tuple[int, int]] = None      # (ghati, vighati) when time is traditional
    m = _BORN_RE.search(block)
    g = None if m else _BORN_GHATI_RE.search(block)
    if g is not None:
        # Traditional reckoning: the clock time is UNKNOWN until the day's sunrise is
        # computed, which needs the coordinates parsed further down — so record the offset
        # and resolve it at the end.
        day, month, year, gh, vig = g.groups()
        ghatis = (int(gh), int(vig or 0))
        hh, mm, mer = 12, 0, "p"                  # placeholders, overwritten after sunrise
        m = g
        notes.append(f"time given as {ghatis[0]}gh {ghatis[1]}vig after sunrise; "
                     "resolved against the computed sunrise and gate-arbitrated")
    elif m:
        day, month, year, hh, mm, mer = m.groups()
    elif meridiem is not None:
        m = _BORN_LOOSE_RE.search(block)
        if not m:
            return None, ["no parseable Born line"]
        day, month, year, hh, mm = m.groups()
        mer = meridiem
        notes.append(f"meridiem OCR-destroyed; read as {meridiem}.m. and gate-arbitrated")
    else:
        return None, ["no parseable Born line"]
    day, month, year, hh = int(day), int(month), int(year), int(hh)
    mm = int(mm) if mm else 0

    # OCR year guard: Raman's nativities are 1700-1999. A 3-digit or out-of-range year is
    # corrupt (observed: "24-3-7883"), and we do NOT try to repair it.
    if not (1700 <= year <= 1999):
        return None, [f"implausible year {year} (OCR)"]
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None, [f"implausible date {day}-{month}"]
    if ghatis is None and not (1 <= hh <= 12):
        return None, [f"implausible hour {hh}"]
    if ghatis is not None and not (0 <= ghatis[0] <= 60 and 0 <= ghatis[1] <= 60):
        return None, [f"implausible ghati {ghatis}"]

    hour24 = hh % 12 + (12 if mer.lower() == "p" else 0)

    zm = _ZONE_RE.search(block[:m.end() + 40])
    # group(2) is the OCR-substituted leading letter ("/", "|", "1", "l"); all stand for I.
    zone = ((zm.group(1) or "I").upper() if zm else None)

    # The coordinate pair frequently straddles a line break, so scan a generous tail and take
    # the FIRST latitude token and the FIRST longitude token found.
    tail = block[m.end(): m.end() + 160]
    lat = lon = None
    # Longitude stated as TIME ("Long. 5h. 10m. 20s. E") is read first: its digits would
    # otherwise be picked up as a spurious arc longitude by the generic scanner.
    lt = _LON_TIME_RE.search(tail)
    if lt:
        h, mi, se = int(lt.group(1)), int(lt.group(2) or 0), int(lt.group(3) or 0)
        lon = (h + mi / 60.0 + se / 3600.0) * 15.0
        if lt.group(4).upper() == "W":
            lon = -lon
        tail = tail[:lt.start()] + " " + tail[lt.end():]
        notes.append("longitude printed as time (h/m/s), converted at 15°/h")
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
    elif zone == "G":
        tz = 0.0
    else:
        # Zone omitted by the printing (it happens: "Born on 12-3-1863 at 2-3 a.m. (Lat. 22°
        # 20' N., Long. 4h. 53m. E.)"). We do NOT assume — we HYPOTHESISE Local Mean Time, the
        # convention for Raman's older nativities, and flag it. The dasha gate then adjudicates:
        # a wrong zone moves the Moon and the printed balance will not reproduce, so the record
        # is rejected. Hypothesise-then-verify is only safe because the gate is independent.
        tz = round(lon / 15.0, 4)
        notes.append("ZONE ABSENT — hypothesised L.M.T., accepted only if the dasha gate passes")
    if ghatis is not None:
        resolved = _resolve_ghati(year, month, day, lat, lon, tz, ghatis)
        if resolved is None:
            return None, notes + ["sunrise not computable for this date/place"]
        hour24, mm = resolved
    return {"dt": f"{year:04d}-{month:02d}-{day:02d}T{hour24:02d}:{mm:02d}:00",
            "tz": tz, "lat": round(lat, 4), "lon": round(lon, 4)}, notes


def _parse_balance(block: str) -> tuple[Optional[str], Optional[float]]:
    """(lord, years) from Raman's printed 'Balance of X Das(h)a at birth'.

    The compact Y-M-D form is tried FIRST: where both could match, it is the unambiguous one."""
    m = _BAL_COMPACT_RE.search(block)
    if m:
        lord, y, mo, d = m.groups()
        lord = lord.capitalize()
        if lord in _LORDS and int(mo) < 12 and int(d) <= 31:
            return lord, int(y) + int(mo) / 12.0 + int(d) / 365.2425
    m = _BAL_PROSE_RE.search(block)
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


#: Section headings that follow a Conclusion inside its capture window. Swallowing one drove a
#: SIGNIFICATION off the next section's title (HTJAH-I.x75 took "Education and Learning" while
#: its conclusion judged the mother — reviewer-caught 2026-08-23).
_SECTION_HEADING = re.compile(
    r"\n\s*(?:Education and Learning|The (?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|"
    r"Eighth|Ninth|Tenth|Eleventh|Twelfth) (?:House|Lord)|Conclusion|Remarks|Special Features|"
    r"Important Events|Balance of)\b")
#: Footnote openers. A sentence spliced across one INVERTED Raman's meaning (NH.chart_5: the
#: footnote "* A learned Indian scholar..." interrupted "the Lagna lord Moon ... is [rendered
#: highly fortified]", and the stitched prose read as afflicted — reviewer-caught 2026-08-23).
_FOOTNOTE = re.compile(r"\n\s*\*\s*[A-Z]")


def _conclusion(block: str) -> Optional[str]:
    """Raman's summing-up paragraph for the chart, normalised to one line.

    The two printings punctuate the label differently ("Conclusion :" in the scans,
    "Conclusion.—" in the Motilal setting) and neither reliably ends the paragraph with a blank
    line, so the capture runs to the first structural marker that DOES appear, and otherwise
    stops at a sane length rather than failing.

    Three splice classes are guarded, each observed corrupting a reviewed row (the full record
    is DOCTRINE_BACKLOG "FULL ADJUDICATION"): a FOOTNOTE interleaving the sentence (NH.chart_5 —
    polarity inverted), the NEXT SECTION'S HEADING swallowed into the text (HTJAH-I.x75 — the
    signification was then read off the heading), and a SECOND PASSAGE concatenated across a
    gap, dropping Raman's own hedge between them (NH.chart_41). The fix is one discipline: cut
    at the FIRST structural boundary of any kind, never bridge across one."""
    m = re.search(r"Conclusion\s*[:.\-—]+\s*(.+)", block, re.S | re.I)
    if not m:
        return None
    tail = m.group(1)
    stops = [tail.find(mark) for mark in ("\n\n", "Chart No")]
    stops += [p.start() for p in re.finditer(r"\nPage \d+ of \d+|\n\s*[IVXL]+\.\s+[A-Z]", tail)]
    stops += [p.start() for p in _SECTION_HEADING.finditer(tail)]
    stops += [p.start() for p in _FOOTNOTE.finditer(tail)]
    cut = min([s for s in stops if s > 40] or [600])
    text = " ".join(tail[:min(cut, 600)].split())
    return text or None


#: Chapter headings carry the house each worked judgment belongs to. The scans mangle the
#: ordinals ("Twelth", "Eleveath", "Eieventh", "Elevanth" all occur), so every observed variant
#: is listed rather than relying on a clean spelling.
_HOUSE_WORD: Final[dict[str, int]] = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    "eleventh": 11, "eleveath": 11, "eievenzh": 11, "eieventh": 11, "elevanth": 11,
    "twelfth": 12, "twelth": 12,
}
_CHAPTER_RE = re.compile(
    r"Concerning the ([A-Za-z]+) House|^\s*(?:X{0,3}(?:IX|IV|V?I{0,3})\.\s*)?The ([A-Za-z]+) House\s*$",
    re.IGNORECASE | re.MULTILINE)


#: A table-of-contents row names every chapter in the book and would otherwise leave the running
#: house state pointing at the LAST one listed — which is why the first charts of Vol I were
#: initially attributed to the 12th house. TOC rows are recognisable by their leader dots or by
#: ending in a bare page number.
_TOC_ROW = re.compile(r"\.{3,}|\.\s*\d{1,3}\s*$|\s\d{1,3}\s*$")


def house_of_chapter(text: str) -> Optional[int]:
    """The house of the LAST real chapter heading in `text`, or None.

    Used to attribute a chart to the house whose chapter it appears under — Raman organises the
    volumes by house, so a chart's judgment belongs to the chapter it sits in. Table-of-contents
    rows are skipped: they list every chapter and would pin the running state to the last one."""
    found = None
    for line in text.splitlines():
        if _TOC_ROW.search(line):
            continue
        m = _CHAPTER_RE.search(line)
        if not m:
            continue
        word = (m.group(1) or m.group(2) or "").lower()
        if word in _HOUSE_WORD:
            found = _HOUSE_WORD[word]
    return found


def collect_text(book: str, text: str, *, origin: str = "corpus") -> list[Candidate]:
    """Every chart presentation in a book's text, with birth/balance/conclusion parsed.

    Works on any source that yields the book's prose — the vendored (OCR'd) markdown or a
    digitally-typeset PDF — because both print the same sentences. `origin` is recorded on each
    candidate so a record's provenance says which printing it came from."""
    lines = text.splitlines()
    # A chart's discussion runs to the next PRESENTATION, not to the next mention of a chart
    # number. Raman cross-references charts constantly inside his prose ("...as in Chart No. 44"),
    # and 754 of Vol I's mentions are only 364 presentations: bounding blocks at every mention
    # truncated 270 of them before their Conclusion paragraph, which is where the verdict lives.
    # A presentation is a chart number with "Born" close behind it.
    starts: list[tuple[int, int]] = []
    for i, line in enumerate(lines):
        m = _CHART_RE.search(line)
        if m and re.search(r"\bBorn\b", "\n".join(lines[i:i + 3]), re.IGNORECASE):
            starts.append((int(m.group(1)), i))
    out: list[Candidate] = []
    prev = 0
    for idx, (no, i) in enumerate(starts):
        end = starts[idx + 1][1] if idx + 1 < len(starts) else len(lines)
        block = "\n".join(lines[i:min(end, i + 200)])
        if not re.search(r"\bBorn\b", block[:400], re.IGNORECASE):
            continue                                    # defensive; starts are presentations
        c = Candidate(book=book, chart_no=no, line=i + 1, origin=origin)
        # The house comes from the chapter this chart sits under. Scan from the previous chart
        # forward so the running chapter state is carried without re-reading the whole book.
        c.house = house_of_chapter("\n".join(lines[prev:i + 1])) or (
            out[-1].house if out else None)
        prev = i
        c.birth, notes = _parse_birth(_flatten_head(block))
        c.notes.extend(notes)
        c.printed_lord, c.printed_years = _parse_balance(block)
        c.conclusion = _conclusion(block)
        if c.birth is None:
            # MERIDIEM-DESTROYED FALLBACK (2026-08-30): emit BOTH readings as sibling
            # candidates and let the dasha gate arbitrate — a 12-hour error moves the Moon
            # ~6.6 deg, far outside tolerance, so at most one can verify. `verify()` marks
            # the losers rejected in the normal way, and `_drop_ambiguous_siblings` below
            # discards a chart where BOTH somehow passed rather than guessing.
            alt = [(_parse_birth(_flatten_head(block), meridiem=mer), mer)
                   for mer in ("a", "p")]
            alt = [((b, n), mer) for (b, n), mer in alt if b is not None]
            if alt:
                for (b, n), mer in alt:
                    sib = Candidate(book=book, chart_no=no, line=i + 1, origin=origin)
                    sib.house, sib.birth = c.house, b
                    sib.notes = list(c.notes) + list(n)
                    sib.printed_lord, sib.printed_years = c.printed_lord, c.printed_years
                    sib.conclusion = c.conclusion
                    sib.meridiem_branch = mer
                    out.append(sib)
                continue
            c.status, c.reason = "unparsed", "; ".join(notes)
        out.append(c)
    return out


def collect(book: str, path: Path) -> list[Candidate]:
    """Chart presentations from a vendored corpus markdown file."""
    return collect_text(book, path.read_text(encoding="utf-8", errors="ignore"))


def collect_pdf(path: Path) -> list[Candidate]:
    """Chart presentations from a digitally-typeset PDF of both volumes.

    The Motilal printing carries a real text layer rather than OCR, so the birth lines survive
    intact ("Lat. 12° 20' N., Long. 76° 38' E." instead of the scan's truncated "at 13° N. \\n77
    E35."). It is used as an EXTRACTION source only: citations continue to resolve against the
    hash-locked vendored corpus, because this is a different edition and its line numbers would
    not match the anchors already written throughout the engine.

    Volume One runs houses I-VI and Volume Two VII-XII, so the chart-number series restarts;
    candidates are tagged by which volume their page falls in."""
    import fitz                                          # PyMuPDF; optional, tool-time only

    doc = fitz.open(path)
    pages = [p.get_text() for p in doc]
    head = "\n".join(pages[:6])
    # A file may hold both volumes (the Motilal omnibus) or just one. Detect which, rather than
    # assuming: a single-volume file mislabelled as an omnibus would attribute every Vol II
    # chart to Vol I and corrupt the house attribution downstream.
    vol2_page = next((i for i, t in enumerate(pages)
                      if i > 20 and re.search(r"^\s*Volume Two\s*$", t, re.M)), None)
    if vol2_page is None:
        only = "HTJAH-II" if re.search(r"Volume\s+Two", head, re.I) else "HTJAH-I"
        spans = [(only, 0, len(pages))]
    else:
        spans = [("HTJAH-I", 0, vol2_page), ("HTJAH-II", vol2_page, len(pages))]
    out: list[Candidate] = []
    for tag, lo, hi in spans:
        text = "\n".join(pages[lo:hi])
        out.extend(collect_text(tag, text, origin=f"pdf:{path.name}"))
    return out


def moon_offset_deg(cast_years: float, printed_years: float, lord: str) -> float:
    """How far apart Raman's Moon and the cast Moon are, in degrees of longitude.

    A mahadasha balance is just the unelapsed fraction of the Moon's nakshatra, so the balance
    disagreement inverts directly to the longitude disagreement that produced it. Comparing in
    DEGREES rather than in days is what makes the gate scale-free: the same 1 deg of Moon error
    shows up as ~4 months inside a 6-year Sun dasha and ~1.5 years inside a 20-year Venus one, so
    a flat day tolerance silently applies a threshold three times stricter to Sun-dasha charts
    than to Venus-dasha ones."""
    span = _SPAN[lord]
    return abs((cast_years - printed_years) / span) * _NAK_DEG


def gate(c: Candidate, tolerance_deg: float = _TOL_DEG) -> Candidate:
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
    off = moon_offset_deg(c.cast_years, c.printed_years, c.cast_lord)
    c.moon_offset_deg = round(off, 3)
    if off > tolerance_deg:
        c.status = "gate-failed"
        c.reason = (f"Moon off by {off:.2f} deg "
                    f"(cast {c.cast_years:.2f}y vs printed {c.printed_years:.2f}y)")
        return c
    c.status = "verified"
    c.reason = f"lord {c.cast_lord}, Moon within {off:.2f} deg"
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


def existing_birth_keys() -> set[str]:
    """Birth moments already in the golden corpus, to the minute.

    Deduplication is by NATIVITY, not by chart number: the two printings number their charts
    differently (the Motilal edition restarts the series at Volume Two), so the same nativity
    carries different numbers in different sources. The birth moment is the edition-independent
    identity."""
    have: set[str] = set()
    if not _GOLDENS.is_file():
        return have
    for raw in _GOLDENS.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        b = json.loads(s).get("birth")
        if b and b.get("dt"):
            have.add(str(b["dt"])[:16])
    return have


#: H8's primary signification is `longevity`, which the judge deliberately does NOT decide from
#: raw positions — LONGEVITY_GUARD defers the numeric span to the ayurdaya pre-pass and returns
#: insufficient-evidence. A scored H8 longevity verdict would therefore measure the guard rather
#: than the doctrine, so H8 charts are extracted WITHOUT a verdict.
_NO_VERDICT_HOUSES: Final[frozenset[int]] = frozenset({8})


#: A Raman chapter can judge more than one matter. HTJAH-I's fourth-house chapter runs the
#: mother AND the native's education (Vidya), and blanket-mapping H4 -> "mother" mislabelled every
#: learning row — caught by an engine-blind reviewer on 2026-08-23. Where a house is ambiguous
#: this way, the prose picks the matter; the first entry is the fallback.
_SIG_HINTS: Final[dict[int, tuple[tuple[str, str], ...]]] = {
    4: (("education", r"learning|educat|vidya|scholar|study|studies"),
        ("mother", r"mother|matru")),
}


def _signification_for(house: int, prose: str) -> Optional[str]:
    """Which matter of `house` this prose is about."""
    from app.raman_saab.doctrine.significations import significations_of
    keys = significations_of(house)
    if not keys:
        return None
    valid = {s.key for s in keys}
    for key, pattern in _SIG_HINTS.get(house, ()):
        if key in valid and re.search(pattern, prose, re.IGNORECASE):
            return key
    return keys[0].key


#: Raman states the FACTORS first and the outcome last ("The fourth house is moderately strong,
#: but the lord and the Karaka are considerably afflicted. Hence the native lost his mother very
#: early."). Reading the ordinal off the whole paragraph lets the factor clause dominate, which
#: was the single biggest error mode the 2026-08-23 review found. These mark the outcome clause.
_OUTCOME_LEAD = re.compile(
    r"(?:\bhence\b|\bthus\b|\btherefore\b|\bso\b|\bas a result\b|\baccordingly\b|"
    r"\bthe native\b|\bthe subject\b|\bhe was\b|\bshe was\b|\bhe had\b|\bshe had\b|"
    r"\bthis (?:gave|enabled|resulted|accounts)\b)", re.IGNORECASE)


def outcome_clause(prose: str) -> str:
    """The part of a Conclusion that states what HAPPENED, not which factors were weighed.

    Returns the prose from the first outcome marker onward, or the whole thing when no marker is
    present. Raman's conclusions routinely concede a factor before delivering the result, and the
    result is the verdict."""
    m = _OUTCOME_LEAD.search(prose)
    return prose[m.start():] if m else prose


def draft_verdict(c: Candidate) -> dict[str, Any]:
    """`expected_verdicts` for a candidate — DRAFT, or empty when nothing can be said.

    The ordinal comes from `extract_goldens.classify_prose`, the project's existing and tested
    prose classifier, applied to the OUTCOME clause rather than the whole paragraph (see
    `outcome_clause`). It is conservative by construction — an explicit concession outranks a bare
    affliction word, and anything it cannot read becomes insufficient-evidence. Everything it
    produces is marked DRAFT.

    DRAFT no longer means "unscored forever": under the 2026-08-23 confirmation-rule amendment a
    reviewer may confirm any of these regardless of whether the engine agrees. That makes the
    LABEL QUALITY matter far more than it did when drafts were inert, which is why the
    signification is now chosen from the prose and the ordinal read from the outcome."""
    from tools.raman_saab.extract_goldens import classify_prose

    if not c.conclusion or not c.house or c.house in _NO_VERDICT_HOUSES:
        return {}
    sig = _signification_for(c.house, c.conclusion)
    if sig is None:
        return {}
    return {
        f"H{c.house}": {
            "signification": sig,
            "verdict": classify_prose(outcome_clause(c.conclusion)),
            "verdict_prose": c.conclusion[:600],
            "verdict_review": "DRAFT",
        }
    }


def merge_by_nativity(cands: list[Candidate]) -> dict[str, list[Candidate]]:
    """Group VERIFIED candidates by birth moment.

    Raman re-presents the same nativity in several chapters — up to ten times — and each
    presentation carries the Conclusion for THAT chapter's house. Deduplicating them away throws
    the extra houses out; grouping keeps every judgment he made about the chart."""
    out: dict[str, list[Candidate]] = {}
    for c in cands:
        if c.status == "verified" and c.birth:
            out.setdefault(str(c.birth["dt"])[:16], []).append(c)
    return out


def merged_verdicts(group: list[Candidate]) -> dict[str, Any]:
    """Every house verdict available for one nativity, across all its presentations.

    Where two presentations disagree about the same house the FIRST is kept and the collision
    recorded — a disagreement is a reviewer's problem to adjudicate, not something to average."""
    out: dict[str, Any] = {}
    for c in sorted(group, key=lambda x: (x.book, x.line)):
        for tag, v in draft_verdict(c).items():
            if tag not in out:
                out[tag] = v
            elif out[tag]["verdict"] != v["verdict"]:
                out[tag].setdefault("_collision", []).append(v["verdict"])
    return out


def to_record(c: Candidate) -> dict[str, Any]:
    """A DRAFT golden record.

    Any verdict here is a keyword reading of Raman's own Conclusion paragraph, marked DRAFT and
    therefore unscored; the paragraph itself is stored verbatim so a reviewer can promote it
    without reopening the book."""
    verdicts = draft_verdict(c)
    return {
        "id": f"{c.book}.x{c.chart_no}",
        "book": c.book,
        "name": f"Chart {c.chart_no} (extracted, DRAFT)",
        "case_type": "worked_example",
        "birth": c.birth,
        "lagna_sign": None,
        "stated_positions": {},
        "expected_verdicts": verdicts,
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
            "origin": c.origin,
            "printed_balance": {"lord": c.printed_lord, "years": c.printed_years},
            "cast_balance": {"lord": c.cast_lord, "years": c.cast_years},
            "moon_offset_deg": c.moon_offset_deg,
            "house_from_chapter": c.house,
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
    ap.add_argument("--tolerance-deg", type=float, default=_TOL_DEG,
                    help=f"max Moon-longitude disagreement with Raman's printed dasha balance, "
                         f"in degrees (default {_TOL_DEG}; ~2 sigma of the measured noise)")
    ap.add_argument("--book", choices=sorted(_BOOKS), help="limit to one book")
    ap.add_argument("--pdf", type=Path, action="append", default=[],
                    help="a digitally-typeset PDF (repeatable, e.g. one per volume). Used in "
                         "preference to the vendored OCR markdown; citations still resolve "
                         "against the hash-locked corpus, which this never touches.")
    ap.add_argument("--with-corpus", action="store_true",
                    help="also scan the vendored OCR markdown for nativities the PDFs miss")
    a = ap.parse_args(argv)

    all_c: list[Candidate] = []
    for pdf in a.pdf:
        if not pdf.is_file():
            print(f"[error] no such PDF: {pdf}", file=sys.stderr)
            return 2
        all_c.extend(gate(c, a.tolerance_deg) for c in collect_pdf(pdf))
    if a.with_corpus or not a.pdf:
        for tag, path in _BOOKS.items():
            if not path.is_file():
                print(f"[skip] {tag}: corpus file absent", file=sys.stderr)
                continue
            all_c.extend(gate(c, a.tolerance_deg) for c in collect(tag, path))
    if a.book:
        all_c = [c for c in all_c if c.book == a.book]

    # Deduplicate by NATIVITY, not chart number: the editions number charts differently, so the
    # same birth moment appears under different numbers in different sources.
    have = existing_birth_keys()
    fresh: dict[str, Candidate] = {}
    for c in all_c:
        if c.status != "verified" or not c.birth:
            continue
        key = str(c.birth["dt"])[:16]
        if key in have or key in fresh:
            continue
        fresh[key] = c
    verified_new = list(fresh.values())

    from collections import Counter
    print(f"[htjah] chart presentations found : {len(all_c)}")
    print(f"[htjah] status of every candidate : {dict(Counter(c.status for c in all_c))}")
    print(f"[htjah] VERIFIED (lord + Moon within {a.tolerance_deg} deg) : "
          f"{sum(1 for c in all_c if c.status == 'verified')}")
    print(f"[htjah]   ...NEW nativities after dedupe               : {len(verified_new)}")
    print(f"[htjah]   ...carrying a Conclusion paragraph           : "
          f"{sum(1 for c in verified_new if c.conclusion)}")
    print(f"[htjah]   ...that yield a DRAFT verdict                : "
          f"{sum(1 for c in verified_new if draft_verdict(c))}")

    if not a.emit:
        for c in sorted(verified_new, key=lambda x: (x.book, x.chart_no))[:250]:
            h = f"H{c.house}" if c.house else "H?"
            print(f"  OK  {c.book}.{c.chart_no:<4d} {h:4s} {c.reason[:64]}")
        return 0

    for c in sorted(verified_new, key=lambda x: (x.book, x.chart_no)):
        print(json.dumps(to_record(c), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
