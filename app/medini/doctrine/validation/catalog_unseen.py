"""Tier-1 catalog of HTJAH worked charts UNSEEN by the engine.

Enumerates every "Chart No. N ... Born <line>" in both HTJAH volumes (machine-readable text;
only the sign *diagrams* need vision), de-duplicates by birth-date against EVERY existing
corpus, and tags each fresh chart's readings by type (strength / longevity / death_timing /
yoga) from its surrounding prose. The output (`unseen_catalog.json`) is the durable index of
genuinely-unseen nativities; sign grids + exact per-factor verdicts are added in Tier 2 (vision).

Requires the source PDFs at ``scratchpad/htjah_vol{1,2}.pdf`` (not committed). Text-only, no vision.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.catalog_unseen [--write]
"""
from __future__ import annotations

import glob
import json
import re
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_CORPORA = _ROOT / "docs/raman_doctrine/validation/corpora"
_OUT = _CORPORA / "unseen_catalog.json"

_STR = re.compile(r"(fairly (strong|powerful|good)|considerably (afflicted|blemished)|feebly|"
                  r"moderately (afflicted|blemished|good)|unafflicted|unsullied|well disposed|"
                  r"very (strong|powerful)|is (afflicted|weak)|not afflicted)", re.I)
_YOGA = re.compile(r"\b[A-Z][a-z]+ ?[Yy]oga\b")
_LONG = re.compile(r"\b(Balarishta|Alpayu|Madhyayu|Purnayu)\b", re.I)
_DEATH = re.compile(r"\b(died|death|expired|guillotined)\b[^.]{0,80}\b(Dasa|Bhukti)\b", re.I)
_DATE = re.compile(r"(\d{1,2}-\d{1,2}-\d{4})")


_ORD = re.compile(r"(\d+)(?:st|nd|rd|th)")


def _iter_corpora():
    for f in (glob.glob(str(_CORPORA / "*.json"))
              + glob.glob(str(_ROOT / "docs/raman_doctrine/audit/corpora/*.json"))):
        # unseen_catalog is this file's own output; unseen_scoreable is a derived subset
        # of it (Tier-2 grids) -- neither is an independent "seen" corpus for de-dup.
        if Path(f).name in ("unseen_catalog.json", "unseen_scoreable.json"):
            continue
        try:
            d = json.loads(Path(f).read_text())
        except (ValueError, OSError):
            continue
        recs = d.get("charts", d if isinstance(d, list) else d.get("rows", [])) or []
        yield Path(f).name, d, recs


def _vol_of(name: str, d: dict) -> str:
    """Volume a corpus belongs to: houses 1-6 -> Vol I, 7-12 -> Vol II.

    HTJAH restarts its "Chart No." numbering at the top of Vol II (the 7th-house
    chapter is Chart No. 1), so chart numbers are only unique *within* a volume --
    the de-dup key must be (vol, chart_no). House comes from the calibration corpus's
    ``house`` field, else from the held-out filename's ordinal (``ch06_3rd`` -> 3).
    """
    house = d.get("house") if isinstance(d, dict) else None
    if not house:
        m = _ORD.search(name)
        house = int(m.group(1)) if m else None
    return "htjah_vol1" if house and int(house) <= 6 else "htjah_vol2"


def seen_keys() -> set[str]:
    """Birth-date keys of every already-extracted chart (a de-dup set).

    Fragile alone: seen corpora that store no ``birth_line`` (the tuned/anchor
    calibration corpora, ch07_4th) contribute nothing here, and OCR-garbled years
    (``18*0``) never match -- so ``seen_chart_keys`` is the primary de-dup and this
    is a secondary net.
    """
    keys: set[str] = set()
    for _name, _d, recs in _iter_corpora():
        for r in recs:
            m = _DATE.search((r.get("birth_line") or ""))
            if m:
                keys.add(m.group(1).replace(" ", ""))
    return keys


def seen_chart_keys() -> set[tuple[str, int]]:
    """(vol, chart_no) of every already-extracted chart -- the robust de-dup set.

    Covers the corpora ``seen_keys`` misses: the tuned/anchor calibration corpora
    and ch07_4th carry a chart number but no birth line, so without this a seen
    chart (e.g. the anchor Charts 12-14, tuned h2/h7/h9/h11) leaks into the "fresh"
    catalog. Volume is derived per :func:`_vol_of`.
    """
    keys: set[tuple[str, int]] = set()
    for name, d, recs in _iter_corpora():
        vol = _vol_of(name, d)
        for r in recs:
            n = r.get("chart_no", r.get("chart"))
            try:                                   # NH cases key on a name string, not an
                keys.add((vol, int(n)))            # HTJAH chart number -- can't collide, skip
            except (TypeError, ValueError):
                continue
    return keys


def _pdf_text(path: Path) -> str:
    import fitz
    doc = fitz.open(str(path))
    t = "".join(doc[i].get_text() for i in range(doc.page_count))
    return re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", t))


def build(write: bool = False) -> dict:
    seen = seen_keys()
    seen_charts = seen_chart_keys()
    fresh: list[dict] = []
    n_seen_by_chart = n_seen_by_date = 0
    for vol in ("htjah_vol1", "htjah_vol2"):
        full = _pdf_text(_ROOT / f"scratchpad/{vol}.pdf")
        for m in re.finditer(r"Chart No\.?\s*(\d+)\.?\s*[-—]*\s*Born([^.]{0,80})", full):
            chart_no = int(m.group(1))
            bl = ("Born" + m.group(2)).strip()[:80]
            dk = _DATE.search(bl)
            key = dk.group(1).replace(" ", "") if dk else None
            # Primary de-dup: (vol, chart_no) -- robust to missing/garbled birth lines.
            if (vol, chart_no) in seen_charts:
                n_seen_by_chart += 1
                continue
            # Secondary net: birth-date match (catches cross-chapter chart-number reuse).
            if key and key in seen:
                n_seen_by_date += 1
                continue
            blk = full[m.start(): m.start() + 1500]
            types = [name for name, rx in (("strength", _STR), ("longevity", _LONG),
                                           ("death_timing", _DEATH), ("yoga", _YOGA)) if rx.search(blk)]
            fresh.append({"vol": vol, "chart_no": chart_no, "birth_line": bl,
                          "key": key, "reading_types": types})
    counts = dict(Counter(t for r in fresh for t in r["reading_types"]))
    corpus = {
        "source": "HTJAH Vol I & II -- worked charts UNSEEN by the engine, de-duped against "
                  "every existing corpus by (vol, chart_no) first (robust: HTJAH restarts chart "
                  "numbering per volume, and the tuned/anchor corpora carry a chart number but no "
                  "birth line) and by birth-date as a secondary net. Tier-1 TEXT index: metadata + "
                  "heuristic reading-type tags. Sign grids + exact verdicts added in Tier 2 (vision).",
        "n_fresh": len(fresh), "reading_type_counts": counts,
        "excluded_as_seen": {"by_chart_no": n_seen_by_chart, "by_birth_date": n_seen_by_date},
        "charts": fresh,
    }
    if write:
        _OUT.write_text(json.dumps(corpus, indent=1))
    return corpus


def main() -> None:
    import sys
    c = build(write="--write" in sys.argv)
    print(f"fresh (unseen) charts: {c['n_fresh']}")
    print(f"excluded as seen:      {c['excluded_as_seen']}")
    print(f"reading-type counts:   {c['reading_type_counts']}")
    print(f"strength candidates (Tier-2 priority): "
          f"{sum(1 for r in c['charts'] if 'strength' in r['reading_types'])}")


if __name__ == "__main__":
    main()
