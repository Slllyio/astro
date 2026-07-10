"""Audit our scored corpora's Raman verdicts against the CLEAN full text.

The vision/OCR extraction that built the held-out + fresh corpora was error-prone in two
ways the clean HTJAH full text (a browser-saved archive.org page, no chart *figures* but
clean *prose*) resolves: (1) an offset diagram/analysis flow that mis-attributed verdicts
to the wrong chart, and (2) garbled verdict words. This audit re-locates every scored
chart in the clean text **by its birth date** (unambiguous -- chart *numbers* restart per
volume, so the same "Chart No. 91" exists in both books) and compares the stored per-factor
verdict phrase's mapped grade to the clean source's, flagging every mismatch.

Input: the clean text at ``scratchpad/htjah_clean.txt`` (produced from the uploaded .mht;
not committed). The durable artifact is the audit report this emits.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.audit_verdicts
"""
from __future__ import annotations

import glob
import json
import os
import re
from pathlib import Path

from app.medini.doctrine.validation import worked_chart_validate as W

_ROOT = Path(__file__).resolve().parents[4]
# Clean full text extracted from the uploaded .mht (not committed -- a user artifact).
# Point HTJAH_CLEAN_TEXT at it to re-run the audit in a future session.
_CLEAN = Path(os.environ.get(
    "HTJAH_CLEAN_TEXT",
    "/tmp/claude-0/-home-user-astro/fb94cb00-7ff5-5ee6-843c-f8d2bc3ca323"
    "/scratchpad/htjah_clean.txt"))
_DATE = re.compile(r"(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{2,4})")
_ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
        "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12}
_ORDRX = "|".join(_ORD)


def _norm_date(s: str) -> str | None:
    m = _DATE.search(s or "")
    if not m:
        return None
    d, mo, y = m.group(1), m.group(2), m.group(3)
    if len(y) == 2:                      # HTJAH is all 18xx-19xx; expand crudely
        y = ("18" if int(y) > 30 else "19") + y
    return f"{int(d)}-{int(mo)}-{int(y)}"


def _clean_text() -> str:
    return re.sub(r"\s+", " ", re.sub(r"Page \d+ of \d+", " ", _CLEAN.read_text()))


def _vol_boundary(txt: str) -> int:
    """Char offset where Vol II begins (chart numbering restarts). HTJAH prints each
    volume's charts in ascending order, so the boundary is the last big descent in the
    birthline chart-number series."""
    bl = [(m.start(), int(m.group(1)))
          for m in re.finditer(r"Chart No\.?\s*(\d+)\s*[.—-]*\s*Born", txt)]
    drop = [bl[i][0] for i in range(1, len(bl)) if bl[i][1] < bl[i - 1][1] - 5]
    return drop[-1] if drop else len(txt)


def clean_charts() -> dict[tuple[str, int], dict]:
    """(vol, chart_no) -> {date, verdicts:{factor: phrase}} from the clean full text.

    Verdicts are attributed by the chart number Raman names IN the analysis prose ("In
    Chart No. N the Nth house ..."), NOT by proximity to a birth line -- the analysis is
    physically offset from the diagram/birthline (the same offset the OCR showed; the clean
    text removes the *garble*, not the *layout*). The House header carries the chart id; the
    following Lord/Karaka/Conclusion inherit it until the next House header."""
    txt = _clean_text()
    boundary = _vol_boundary(txt)

    # birthline chart_no -> date, per volume
    dates: dict[tuple[str, int], str] = {}
    for m in re.finditer(r"Chart No\.?\s*(\d+)\s*[.—-]*\s*Born([^.]{0,60})", txt):
        vol = "htjah_vol1" if m.start() < boundary else "htjah_vol2"
        d = _norm_date(m.group(2))
        if d:
            dates.setdefault((vol, int(m.group(1))), d)

    # factor headers in order; a House header sets the current (vol, chart) context
    heads = [("bhava", rf"The\s+(?:{_ORDRX})\s+House"),
             ("lord", rf"(?:The\s+)?(?:{_ORDRX})\s+Lord"),
             ("karaka", r"[A-Z][a-z]+-?[Kk]araka"),
             ("concl", r"Conclusion")]
    events = []
    for fac, rx in heads:
        for m in re.finditer(rx + r"\s*[.:—-]+([^§]{0,340})", txt, re.IGNORECASE):
            events.append((m.start(), fac, m.group(1).strip()[:320]))
    events.sort()

    charts: dict[tuple[str, int], dict] = {}
    cur: tuple[str, int] | None = None
    for pos, fac, phrase in events:
        if fac == "bhava":
            cm = re.match(r"[^.]*?Chart No\.?\s*(\d+)", phrase)
            if cm:
                vol = "htjah_vol1" if pos < boundary else "htjah_vol2"
                cur = (vol, int(cm.group(1)))
        if cur is None:
            continue
        charts.setdefault(cur, {"verdicts": {}})["verdicts"].setdefault(fac, phrase)
    for key, d in dates.items():
        charts.setdefault(key, {"verdicts": {}})["date"] = d
    return charts


def _corpus_date(rec: dict) -> str | None:
    return _norm_date(rec.get("birth_line") or "")


def audit(scored_only: bool = True) -> dict:
    """Compare each scored corpus chart's stored verdicts to the clean full text."""
    patterns = W.load_verdict_map()
    charts = clean_charts()
    by_date: dict[str, dict] = {}                    # date -> verdicts (offset-corrected)
    for key, c in charts.items():
        if c.get("date") and c.get("verdicts"):
            by_date.setdefault(c["date"], c["verdicts"])
    corpora = sorted(glob.glob(str(_ROOT / "docs/raman_doctrine/validation/corpora/heldout_ch*.json"))) \
        + [str(_ROOT / "docs/raman_doctrine/validation/corpora/unseen_scoreable.json")]
    rows, matched, unmatched, mismatches = [], 0, [], []
    for f in corpora:
        d = json.loads(Path(f).read_text())
        for rec in d.get("charts", []):
            date = _corpus_date(rec)
            if not date or date not in by_date:
                if any(W.map_verdict(v.get("phrase", ""), patterns) for v in rec.get("verdicts", [])):
                    unmatched.append({"corpus": Path(f).name, "chart": rec.get("chart_no"), "date": date})
                continue
            matched += 1
            cf = by_date[date]
            for v in rec.get("verdicts", []):
                stored_g = W.map_verdict(v.get("phrase", ""), patterns)
                if stored_g is None:
                    continue
                clean_phrase = cf.get(v["factor"], "")
                clean_g = W.map_verdict(clean_phrase, patterns)
                agree = (stored_g == clean_g)
                rows.append({"corpus": Path(f).name, "chart": rec.get("chart_no"),
                             "date": date, "factor": v["factor"], "stored": stored_g,
                             "clean": clean_g, "agree": agree})
                if clean_g is not None and not agree:
                    mismatches.append({"corpus": Path(f).name, "chart": rec.get("chart_no"),
                                       "date": date, "factor": v["factor"],
                                       "stored_grade": stored_g, "clean_grade": clean_g,
                                       "stored_phrase": v["phrase"][:70],
                                       "clean_phrase": clean_phrase[:70]})
    checkable = [r for r in rows if r["clean"] is not None]
    agree = sum(1 for r in checkable if r["agree"])
    return {"charts_in_clean_text": len(charts),
            "scored_charts_matched_by_date": matched,
            "verdict_rows_checked": len(checkable),
            "verdict_rows_agree": agree,
            "agree_pct": round(100 * agree / len(checkable), 1) if checkable else 0.0,
            "mismatches": mismatches,
            "corpus_charts_unmatched_in_clean_text": unmatched}


def main() -> None:
    if not _CLEAN.exists():
        print(f"clean text not found at {_CLEAN}; set HTJAH_CLEAN_TEXT to the extracted "
              f".mht text to run the audit.")
        return
    a = audit()
    print(f"clean-text charts:             {a['charts_in_clean_text']}")
    print(f"scored charts matched by date: {a['scored_charts_matched_by_date']}")
    print(f"verdict rows cross-checkable:  {a['verdict_rows_checked']}")
    print(f"  agree with clean source:     {a['verdict_rows_agree']} ({a['agree_pct']}%)")
    print(f"  MISMATCHES:                  {len(a['mismatches'])}")
    for m in a["mismatches"]:
        print(f"    {m['corpus'][:16]} ch{m['chart']} {m['factor']}: stored={m['stored_grade']} "
              f"clean={m['clean_grade']} | clean='{m['clean_phrase']}'")
    print(f"  corpus charts not found in clean text (by date): "
          f"{len(a['corpus_charts_unmatched_in_clean_text'])}")


if __name__ == "__main__":
    main()
