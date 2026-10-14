"""Admission gate — only keep benchmark charts whose cast reproduces Raman's printed positions.

The book prints both the birth data AND the resulting planetary longitudes, which makes each
chart self-checking. That matters because the printed birth data is not always right: Abraham
Lincoln's entry reads "(Lat. 35 N., Long. 89 E.)" — an EASTERN longitude for a man born in
Kentucky (37.6 N, 85.7 W). Casting from bad coordinates yields a chart Raman never read, and
scoring salience against his prose for that chart would be measuring noise.

So: parse the birth details, cast with the engine, compare to the printed longitudes, and admit
only charts that agree. `cast_chart` defaults to ayanamsa="raman" — the one Raman himself used,
which is what makes the comparison meaningful.

Usage:
    py -3.12 tools/raman_saab/admit_attention_charts.py \
        --bench tests/fixtures/notable_attention.json --tolerance 5
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path
from typing import Final, Optional

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData

_SIGN_NAMES: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")

MONTHS: Final[dict[str, int]] = {
    m: i + 1 for i, m in enumerate(
        ["january", "february", "march", "april", "may", "june", "july",
         "august", "september", "october", "november", "december"])}

_PLANET_RE = re.compile(
    r"\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu)\b[^0-9]{0,12}"
    r"(\d{1,3})\s*[°ºO]\s*(\d{1,2})?", re.I)
_DATE_RE = re.compile(
    r"(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:/\s*\d{1,2}\s*(?:st|nd|rd|th)?)?\s+"
    r"(january|february|march|april|may|june|july|august|september|october|november|december)"
    r"[^0-9]{0,6}(\d{3,4})", re.I)
_TIME_RE = re.compile(r"(\d{1,2})\s*[-–.:]\s*(\d{1,2})\s*([ap])\s*\.?\s*m", re.I)
_HOUR_RE = re.compile(r"at\s+(?:about\s+)?(\d{1,2})\s*([ap])\s*\.?\s*m", re.I)


def _norm(a: float) -> float:
    return a % 360.0


def _sep(a: float, b: float) -> float:
    """Circular separation — the 359/2 degree wrap is the classic silent bug."""
    d = abs(_norm(a) - _norm(b)) % 360.0
    return min(d, 360.0 - d)


def parse_printed(text: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for m in _PLANET_RE.finditer(text):
        name = m.group(1).capitalize()
        if name in out:
            continue
        out[name] = float(m.group(2)) + (float(m.group(3)) / 60.0 if m.group(3) else 0.0)
    return out


def parse_birth(rec: dict) -> Optional[BirthData]:
    """BirthData from the printed details, or None if unparseable / outside the engine's era."""
    txt = rec.get("birth_details", "")
    if re.search(r"B\.?\s?C", txt, re.I):
        return None                                   # pre-CE: outside the cast path we trust
    dm = _DATE_RE.search(txt)
    if not dm:
        return None
    day, month, year = int(dm.group(1)), MONTHS[dm.group(2).lower()], int(dm.group(3))
    if not (1 <= day <= 31 and 1000 <= year <= 2100):
        return None

    hour, minute = 12, 0
    if (tm := _TIME_RE.search(txt)):
        hour, minute = int(tm.group(1)), int(tm.group(2))
        if tm.group(3).lower() == "p" and hour != 12:
            hour += 12
        if tm.group(3).lower() == "a" and hour == 12:
            hour = 0
    elif (hm := _HOUR_RE.search(txt)):
        hour = int(hm.group(1))
        if hm.group(2).lower() == "p" and hour != 12:
            hour += 12
    elif re.search(r"midnight", txt, re.I):
        hour = 0
    elif re.search(r"midday|noon", txt, re.I):
        hour = 12

    lat, lon = rec.get("latitude"), rec.get("longitude")
    if lat is None or lon is None:
        return None

    # L.M.T. is the book's default; I.S.T. is stated explicitly when used.
    tz = 5.5 if re.search(r"I\.?\s?S\.?\s?T", txt, re.I) else round(lon / 15.0, 4)
    return BirthData(rec.get("name", "?"), year, month, day, hour, minute, tz, lat, lon)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bench", default="tests/fixtures/notable_attention.json")
    ap.add_argument("--tolerance", type=float, default=5.0,
                    help="max median |computed - printed| in degrees to admit a chart")
    ap.add_argument("--write", action="store_true", help="write admitted flags back")
    args = ap.parse_args()

    path = Path(args.bench)
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []

    for rec in data["charts"]:
        printed = parse_printed(rec.get("positions_raw", ""))
        birth = parse_birth(rec)
        if birth is None or len(printed) < 4:
            rec["admitted"] = False
            rec["admit_reason"] = "unparseable birth data" if birth is None else "few positions"
            rows.append((rec["name"], None, rec["admit_reason"]))
            continue
        try:
            chart = cast_chart(birth)
        except Exception as exc:                                       # noqa: BLE001
            rec["admitted"] = False
            rec["admit_reason"] = f"cast failed: {exc}"
            rows.append((rec["name"], None, rec["admit_reason"]))
            continue

        diffs = [_sep(chart.planets[n].lon, v)
                 for n, v in printed.items() if n in chart.planets]
        med = statistics.median(diffs) if diffs else None
        ok = med is not None and med <= args.tolerance

        # The LAGNA is the only printed value that tests the coordinates: planetary longitudes
        # depend on time alone, so a chart cast at the wrong place still matches them. Houses
        # are the salience target, and houses hang off the ascendant — so a stated Lagna that
        # disagrees disqualifies the chart no matter how well the planets line up.
        stated = (rec.get("stated_lagna") or "").strip()
        got = _SIGN_NAMES[chart.asc_sign - 1] if 1 <= chart.asc_sign <= 12 else "?"
        rec["computed_lagna"] = got
        if stated:
            if stated != got:
                ok = False
                rec["admit_reason"] = f"Lagna mismatch: book {stated}, cast {got}"
            else:
                rec["lagna_confirmed"] = True

        rec["admitted"] = bool(ok)
        rec["admit_median_deg"] = round(med, 2) if med is not None else None
        if ok:
            rec["admit_reason"] = "ok" + (f" (Lagna {got} confirmed)" if stated else
                                          " (no stated Lagna — time verified, place unverified)")
        elif "admit_reason" not in rec or rec["admit_reason"] == "ok":
            rec["admit_reason"] = f"median {med:.1f}deg vs printed"
        rows.append((rec["name"], med, rec["admit_reason"]))

    rows.sort(key=lambda r: (r[1] is None, r[1] if r[1] is not None else 0))
    print(f"{'chart':30s} {'median deg':>11s}  reason")
    for name, med, reason in rows:
        print(f"{name[:30]:30s} {('—' if med is None else f'{med:8.2f}'):>11s}  {reason}")

    admitted = [r for r in data["charts"] if r.get("admitted")]
    print(f"\nadmitted {len(admitted)} of {len(data['charts'])} "
          f"(tolerance {args.tolerance}deg)")
    for split in ("tune", "holdout"):
        n = sum(1 for r in admitted if r.get("split") == split)
        print(f"  {split:8s} {n}")

    if args.write:
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote admission flags to {path}")


if __name__ == "__main__":
    main()
