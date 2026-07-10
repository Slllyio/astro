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


def seen_keys() -> set[str]:
    """Birth-date keys of every already-extracted chart (the de-dup set)."""
    keys: set[str] = set()
    for f in (glob.glob(str(_CORPORA / "*.json"))
              + glob.glob(str(_ROOT / "docs/raman_doctrine/audit/corpora/*.json"))):
        if Path(f).name in ("unseen_catalog.json",):
            continue
        try:
            d = json.loads(Path(f).read_text())
        except (ValueError, OSError):
            continue
        recs = d.get("charts", d if isinstance(d, list) else d.get("rows", [])) or []
        for r in recs:
            m = _DATE.search((r.get("birth_line") or ""))
            if m:
                keys.add(m.group(1).replace(" ", ""))
    return keys


def _pdf_text(path: Path) -> str:
    import fitz
    doc = fitz.open(str(path))
    t = "".join(doc[i].get_text() for i in range(doc.page_count))
    return re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", t))


def build(write: bool = False) -> dict:
    seen = seen_keys()
    fresh: list[dict] = []
    for vol in ("htjah_vol1", "htjah_vol2"):
        full = _pdf_text(_ROOT / f"scratchpad/{vol}.pdf")
        for m in re.finditer(r"Chart No\.?\s*(\d+)\.?\s*[-—]*\s*Born([^.]{0,80})", full):
            bl = ("Born" + m.group(2)).strip()[:80]
            dk = _DATE.search(bl)
            key = dk.group(1).replace(" ", "") if dk else None
            if key and key in seen:
                continue
            blk = full[m.start(): m.start() + 1500]
            types = [name for name, rx in (("strength", _STR), ("longevity", _LONG),
                                           ("death_timing", _DEATH), ("yoga", _YOGA)) if rx.search(blk)]
            fresh.append({"vol": vol, "chart_no": int(m.group(1)), "birth_line": bl,
                          "key": key, "reading_types": types})
    counts = dict(Counter(t for r in fresh for t in r["reading_types"]))
    corpus = {
        "source": "HTJAH Vol I & II -- worked charts UNSEEN by the engine (de-duped by "
                  "birth-date against every existing corpus). Tier-1 TEXT index: metadata + "
                  "heuristic reading-type tags. Sign grids + exact verdicts added in Tier 2 (vision).",
        "n_fresh": len(fresh), "reading_type_counts": counts, "charts": fresh,
    }
    if write:
        _OUT.write_text(json.dumps(corpus, indent=1))
    return corpus


def main() -> None:
    import sys
    c = build(write="--write" in sys.argv)
    print(f"fresh (unseen) charts: {c['n_fresh']}")
    print(f"reading-type counts:   {c['reading_type_counts']}")
    print(f"strength candidates (Tier-2 priority): "
          f"{sum(1 for r in c['charts'] if 'strength' in r['reading_types'])}")


if __name__ == "__main__":
    main()
