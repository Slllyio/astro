"""Soul-destiny reading CLI (REPORT-ONLY) — decipher a nativity as a scripted soul.

Reads a chart's soul through the Parashari mokṣa core (Raman-cited) + the Jaimini soul-script
(experiment-unlocked citations) + nakṣatra archetypes, and can cross-reference several family
members' souls (the soul-group interlock). Never touches the D1 verdict path.

Usage:
    # single chart from explicit birth data:
    py -3.12 -m tools.raman_saab.soul_reading --date 1990-07-15 --time 12:00 --tz 5.5 \\
        --lat 12.97 --lon 77.59
    # from a fixture carrying a {"birth": {...}} block:
    py -3.12 -m tools.raman_saab.soul_reading --fixture tests/fixtures/field_case_01.json
    # family soul-group from a members JSON ({"members": {role: {"birth": {...}}}}):
    py -3.12 -m tools.raman_saab.soul_reading --family data/private/family_charts.json
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges.family_soul_group import build_family_soul_group
from app.raman_saab.judges.soul_reading import build_soul_reading
from app.raman_saab.render_family_soul import to_text as group_text
from app.raman_saab.render_soul import to_text as soul_text


def _birth(d: dict, name: str = "chart") -> BirthData:
    """Build a BirthData from either a flat {year,month,day,hour,minute} block or a
    {date:'YYYY-MM-DD', time:'HH:MM'} block (family_charts.json shape)."""
    if "date" in d:
        y, mo, day = (int(x) for x in str(d["date"]).split("-"))
        hh, mm = (int(x) for x in str(d["time"]).split(":"))
    else:
        y, mo, day = int(d["year"]), int(d["month"]), int(d["day"])
        hh, mm = int(d["hour"]), int(d["minute"])
    return BirthData(name=d.get("name", name), year=y, month=mo, day=day, hour=hh, minute=mm,
                     tz_offset=float(d["tz_offset"]), latitude=float(d["latitude"]),
                     longitude=float(d["longitude"]))


def _from_flags(args: argparse.Namespace) -> BirthData:
    y, mo, d = (int(x) for x in args.date.split("-"))
    hh, _, mm = args.time.partition(":")
    return BirthData(name="chart", year=y, month=mo, day=d, hour=int(hh), minute=int(mm or 0),
                     tz_offset=float(args.tz), latitude=float(args.lat), longitude=float(args.lon))


def _cast(birth: BirthData, ayanamsa: str) -> RamanChart:
    return cast_chart(birth, ayanamsa=ayanamsa)


def _emit(obj: object, as_json: bool, render) -> None:
    if as_json:
        print(json.dumps(dataclasses.asdict(obj), indent=2, ensure_ascii=False))
    else:
        print(render(obj))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Soul-destiny reading (report-only).")
    ap.add_argument("--fixture", type=Path, help="JSON file with a {'birth': {...}} block")
    ap.add_argument("--family", type=Path, help="JSON with {'members': {role: {'birth': {...}}}}")
    ap.add_argument("--date", help="YYYY-MM-DD birth date")
    ap.add_argument("--time", help="HH:MM (24h) birth time")
    ap.add_argument("--tz", help="tz offset in hours, e.g. 5.5")
    ap.add_argument("--lat", help="latitude")
    ap.add_argument("--lon", help="longitude")
    ap.add_argument("--ayanamsa", default="raman", help="ayanamsa (default: raman)")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args(argv)
    as_json = args.format == "json"

    if args.family:
        doc = json.loads(args.family.read_text(encoding="utf-8"))
        members = doc.get("members", doc)
        pairs: list[tuple[str, RamanChart]] = []
        for role, member in members.items():
            chart = _cast(_birth(member["birth"], role), args.ayanamsa)
            pairs.append((role, chart))
            if not as_json:
                print(f"\n########## {role} ##########")
                print(soul_text(build_soul_reading(chart)))
        group = build_family_soul_group(pairs)
        _emit(group, as_json, group_text)
        return 0

    if args.fixture:
        birth = _birth(json.loads(args.fixture.read_text(encoding="utf-8"))["birth"])
    elif args.date and args.time and args.tz and args.lat and args.lon:
        birth = _from_flags(args)
    else:
        ap.error("provide --family, --fixture, or all of --date --time --tz --lat --lon")

    _emit(build_soul_reading(_cast(birth, args.ayanamsa)), as_json, soul_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
