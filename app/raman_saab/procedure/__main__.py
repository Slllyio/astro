"""CLI for the procedure reader: prints a chart read house by house in Raman's order.

Usage:
    python -m app.raman_saab.procedure --date 1990-07-15 --time 12:00 --lat 12.97 --lon 77.59 --tz 5.5
    python -m app.raman_saab.procedure --date 1912-08-08 --time 19:35 --lat 13 --lon 77.5833 --tz 5.5 --format json
    python -m app.raman_saab.procedure ... --house 4 --no-timing

Arguments follow ``python -m app.raman_saab`` (``--date YYYY-MM-DD``, ``--time HH:MM``,
``--tz``, ``--lat``, ``--lon``, ``--ayanamsa raman|lahiri``); ``--name`` is optional here.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.procedure.reader import read_procedure
from app.raman_saab.procedure.render import to_text

logger = logging.getLogger(__name__)


def _parse(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="app.raman_saab.procedure",
                                 description="Raman's house-reading procedure")
    ap.add_argument("--name", default="")
    ap.add_argument("--date", required=True)                  # YYYY-MM-DD
    ap.add_argument("--time", required=True)                  # HH:MM
    ap.add_argument("--tz", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--ayanamsa", default="raman", choices=["raman", "lahiri"])
    ap.add_argument("--format", default="text", choices=["text", "json"])
    ap.add_argument("--house", type=int, choices=range(1, 13), help="print one house only")
    ap.add_argument("--no-timing", action="store_true", help="skip the timing rules")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    a = _parse(argv)
    y, mo, d = (int(x) for x in a.date.split("-"))
    hh, mm = (int(x) for x in a.time.split(":"))
    birth = BirthData(a.name or "native", y, mo, d, hh, mm, a.tz, a.lat, a.lon)
    chart = cast_chart(birth, ayanamsa=a.ayanamsa)
    reading = read_procedure(chart, name=a.name, with_timing=not a.no_timing)
    if a.house is not None:
        import dataclasses
        reading = dataclasses.replace(
            reading, matters=tuple(m for m in reading.matters if m.house == a.house))
    if a.format == "json":
        print(json.dumps(reading.to_dict(), indent=2))
    else:
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except Exception:
            pass
        print(to_text(reading))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
