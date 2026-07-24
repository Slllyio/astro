"""Notable Horoscopes golden extractor — Track-B from Raman's OWN printed positions.

Each NH chart prints Raman's computed SIDEREAL longitudes for every graha + the Lagna
("The Sun 304° 6'; ... and Lagna 316° 39'."). Those are the maximally-faithful ground truth
(Raman's own worked nativity, no coord/tz/ayanamsa reconstruction — and immune to the birth-coord
OCR errors the existing goldens' _notes document, e.g. Lincoln's 'Long 89° E' for a Kentucky birth).
This tool parses them into DRAFT ``stated_positions`` (Track-B) golden records for every NH chart
NOT already in the corpus and that parses cleanly. It NEVER fabricates: a chart missing any of the
nine grahas or the Lagna is SKIPPED and reported.

Verdicts are conservative DRAFT (verdict_review="DRAFT" — NOT asserted by the ratchet). The chart
itself is the immediate value: it grows the cast corpus (rule-liveness coverage, differential
astronomy), while the DRAFT verdict is a reviewable starting point for later CONFIRMED promotion.

Usage:
    py -3.12 -m tools.raman_saab.extract_nh_goldens                 # dry-run report
    py -3.12 -m tools.raman_saab.extract_nh_goldens --emit          # print JSONL to stdout
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from app.raman_saab.chart.constants import SIGN_LORDS  # noqa: F401  (kept for parity/imports)
from tools.raman_saab.extract_goldens import GoldenRecord, classify_prose

_MD = Path("data/knowledge_library/sources/notable_horoscopes_raman/"
           "chapter_001_full-text-unsplit.md")
_GOLDENS = Path("tests/fixtures/raman_goldens.jsonl")

_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_CHART_HEADER = re.compile(r"^No\.?\s*([0-9IlOo]{1,3})\s*[.,\-—]", re.IGNORECASE)
_OCR_DIGITS = str.maketrans({"I": "1", "l": "1", "O": "0", "o": "0"})


def _ocr_int(raw: str) -> int | None:
    try:
        return int(raw.translate(_OCR_DIGITS))
    except ValueError:
        return None


def _deg(text: str, name: str) -> float | None:
    """First 'NAME  DDD° MM' occurrence -> a 0..360 longitude, or None. Tolerant of OCR noise
    (missing minutes, a trailing '*', 'V' for the minute tick)."""
    m = re.search(rf"{name}\s+(\d{{1,3}})\s*°\s*(\d{{1,2}})?", text)
    if not m:
        return None
    deg = int(m.group(1))
    minutes = int(m.group(2)) if m.group(2) else 0
    lon = deg + minutes / 60.0
    return lon % 360.0 if 0 <= deg < 360 and 0 <= minutes < 60 else None


@dataclass(frozen=True)
class _Section:
    number: int
    name: str
    start_line: int          # 1-indexed md line of the 'No. N' header
    body: str                # the section text
    pos_line: int            # 1-indexed md line where 'Planetary Positions' appears (citation)


def _split_sections(lines: list[str]) -> list[_Section]:
    heads: list[tuple[int, int, str]] = []      # (line_idx0, number, name)
    for i, line in enumerate(lines):
        m = _CHART_HEADER.match(line.strip())
        if not m:
            continue
        num = _ocr_int(m.group(1))
        if num is None:
            continue
        name = line.strip().split("—", 1)[-1].split("-", 1)[-1].strip(" .,-—")
        heads.append((i, num, name or f"chart {num}"))
    out: list[_Section] = []
    for j, (i0, num, name) in enumerate(heads):
        i1 = heads[j + 1][0] if j + 1 < len(heads) else len(lines)
        body = "\n".join(lines[i0:i1])
        pos_idx = next((k for k in range(i0, i1) if "Planetary Position" in lines[k]), i0)
        out.append(_Section(number=num, name=name, start_line=i0 + 1, body=body,
                            pos_line=pos_idx + 1))
    return out


def _positions_block(body: str) -> str:
    """The text from 'Planetary Positions' up to 'Balance of'/'Special Features' (positions end at
    the Dasa-balance line). Joined to one line so wrapped positions parse."""
    start = body.find("Planetary Position")
    if start < 0:
        return ""
    tail = body[start:]
    for stop in ("Balance of", "Special Features", "Special  Features", "Important Events"):
        idx = tail.find(stop)
        if idx > 0:
            tail = tail[:idx]
            break
    return " ".join(tail.split())


def _special_features(body: str) -> str:
    m = re.search(r"Special\s+Features\.?\s*[.\-—]*\s*(.+?)(?:Important Events|$)", body, re.DOTALL)
    if not m:
        return ""
    return " ".join(m.group(1).split())[:480]


def _stated_from_positions(pos: str) -> dict[str, dict[str, object]] | None:
    lag = _deg(pos, "Lagna") or _deg(pos, "Ascendant")
    if lag is None:
        return None
    lagna_sign = int(lag // 30) + 1
    stated: dict[str, dict[str, object]] = {}
    for g in _GRAHAS:
        lon = _deg(pos, "Moon" if g == "Moon" else g)
        if lon is None:
            return None
        sign = int(lon // 30) + 1
        stated[g] = {"lon": round(lon, 4), "bhava": ((sign - lagna_sign) % 12) + 1,
                     "position_source": "printed_degree"}
    stated["_lagna_sign"] = lagna_sign  # sentinel, popped by the caller
    return stated


def _existing_numbers() -> set[int]:
    nums: set[int] = set()
    for line in _GOLDENS.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        rec = json.loads(s)
        if rec.get("book") == "NH":
            m = re.search(r"chart_(\d+)", rec.get("id", ""))
            if m:
                nums.add(int(m.group(1)))
    return nums


def extract(md_path: Path = _MD) -> tuple[list[GoldenRecord], list[tuple[int, str, str]]]:
    """Return (records, skipped) where skipped is (number, name, reason)."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    existing = _existing_numbers()
    records: list[GoldenRecord] = []
    skipped: list[tuple[int, str, str]] = []
    seen: set[int] = set()
    for sec in _split_sections(lines):
        if sec.number in seen:
            continue
        seen.add(sec.number)
        if sec.number in existing:
            skipped.append((sec.number, sec.name, "already a golden"))
            continue
        pos = _positions_block(sec.body)
        stated = _stated_from_positions(pos) if pos else None
        if stated is None:
            skipped.append((sec.number, sec.name, "positions did not parse (all 9 grahas + Lagna)"))
            continue
        lagna_sign = int(stated.pop("_lagna_sign"))  # type: ignore[arg-type]
        prose = _special_features(sec.body)
        records.append(GoldenRecord(
            id=f"NH.chart_{sec.number}", book="NH", name=sec.name,
            case_type="worked_example", birth=None, lagna_sign=lagna_sign,
            stated_positions=stated,  # type: ignore[arg-type]
            expected_verdicts={"H1": {
                "signification": "self", "verdict": classify_prose(prose),
                "verdict_prose": prose[:400], "verdict_review": "DRAFT"}},
            expected_longevity=None, track_eligibility=("B", "3"),
            confidence=0.25, citations=(f"NH:{sec.pos_line}",)))
    return records, skipped


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Extract NH charts into DRAFT Track-B goldens.")
    ap.add_argument("--emit", action="store_true", help="print JSONL records to stdout")
    args = ap.parse_args(argv)

    records, skipped = extract()
    if args.emit:
        for rec in records:
            print(rec.to_jsonl())
        return 0
    print(f"[nh-extract] new parseable charts: {len(records)}")
    print(f"[nh-extract] skipped: {len(skipped)}")
    for num, name, reason in sorted(skipped):
        print(f"    No.{num:<3} {name[:34]:<34} {reason}")
    print("\n  new records (number | name | lagna | H1 draft verdict):")
    for rec in records:
        v = rec.expected_verdicts["H1"]["verdict"]
        print(f"    {rec.id:<14} {rec.name[:30]:<30} lagna={rec.lagna_sign:<2} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
