"""Saptamsa (D-7) children reading CLI — decipher the child-varga for one chart.

REPORT-ONLY: prints the provenance-tagged D-7 children reading. The verdict shown is
Raman's real method (Rasi 5th + Navamsa + Beeja/Kshetra); the D-7 block corroborates.

Usage:
    # from a fixture with a {"birth": {...}} block (e.g. the confirmed field case):
    py -3.12 -m tools.raman_saab.saptamsa_reading --fixture tests/fixtures/field_case_01.json

    # or from explicit birth data:
    py -3.12 -m tools.raman_saab.saptamsa_reading \\
        --date 1986-09-05 --time 20:23 --tz 5.5 --lat 28.64 --lon 77.35 [--ayanamsa raman]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges.saptamsa_reading import build_saptamsa_children_reading
from app.raman_saab.render_saptamsa import to_text


def _birth_from_fixture(path: Path) -> BirthData:
    b = json.loads(path.read_text(encoding="utf-8"))["birth"]
    # fixtures carry either flat y/m/d or a "dt" ISO string; support the flat field_case shape.
    return BirthData(
        name=b.get("name", "chart"), year=int(b["year"]), month=int(b["month"]),
        day=int(b["day"]), hour=int(b["hour"]), minute=int(b["minute"]),
        tz_offset=float(b["tz_offset"]), latitude=float(b["latitude"]),
        longitude=float(b["longitude"]))


def _birth_from_flags(args: argparse.Namespace) -> BirthData:
    y, mo, d = (int(x) for x in args.date.split("-"))
    hh, _, mm = args.time.partition(":")
    return BirthData(name="chart", year=y, month=mo, day=d, hour=int(hh), minute=int(mm or 0),
                     tz_offset=float(args.tz), latitude=float(args.lat), longitude=float(args.lon))


def main(argv: list[str] | None = None) -> int:
    # utf-8 stdout so diacritics/box-drawing never trip a cp1252 console.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Saptamsa (D-7) children reading (report-only).")
    ap.add_argument("--fixture", type=Path, help="JSON file with a {'birth': {...}} block")
    ap.add_argument("--date", help="YYYY-MM-DD birth date")
    ap.add_argument("--time", help="HH:MM (24h) birth time")
    ap.add_argument("--tz", help="tz offset in hours, e.g. 5.5")
    ap.add_argument("--lat", help="latitude")
    ap.add_argument("--lon", help="longitude")
    ap.add_argument("--ayanamsa", default="raman", help="ayanamsa (default: raman)")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args(argv)

    if args.fixture:
        birth = _birth_from_fixture(args.fixture)
    elif args.date and args.time and args.tz and args.lat and args.lon:
        birth = _birth_from_flags(args)
    else:
        ap.error("provide --fixture, or all of --date --time --tz --lat --lon")

    chart = cast_chart(birth, ayanamsa=args.ayanamsa)
    reading = build_saptamsa_children_reading(chart)
    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(reading), indent=2, ensure_ascii=False))
    else:
        print(to_text(reading))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
