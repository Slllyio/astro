"""CLI entry point for `app.reading`.

Usage:
    python -m app.reading.cli --dob 1990-07-15 --time 12:00 --tz +05:30 \
                              --lat 12.97 --lon 77.59 \
                              [--out reading.json] [--no-enrich] [--verbose]

Exit codes (spec Section 5):
    0 = success
    1 = bad input (Pydantic ValidationError on ChartInput)
    2 = ephemeris / chart computation failure
    3 = schema validation failure on the engine output
    4 = RAG index missing (Tier-3 fallback; current behaviour is exit 0
        with a warning unless --strict is set, reserved for Task 6.x)

Stdout: a single JSON document matching `app.reading.schema.ReadingOutput`.
        When `--out PATH` is given, the JSON is written there instead and
        stdout stays empty.
Stderr: human-readable diagnostics; `--verbose` enables DEBUG-level logs.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from pydantic import ValidationError

from app.reading.proforma import compute
from app.reading.schema import ChartInput, ReadingOutput

logger = logging.getLogger(__name__)


def _build_arg_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser. Extracted for testability."""
    parser = argparse.ArgumentParser(
        prog="app.reading.cli",
        description="Compute a kundli reading from birth data and emit JSON.",
    )
    parser.add_argument("--dob", required=True, help="Date of birth (YYYY-MM-DD).")
    parser.add_argument("--time", required=True, help="Time of birth (HH:MM, 24h).")
    parser.add_argument(
        "--tz", required=True, help="Timezone as signed offset (e.g. +05:30)."
    )
    parser.add_argument(
        "--lat", type=float, required=True, help="Latitude in decimal degrees."
    )
    parser.add_argument(
        "--lon", type=float, required=True, help="Longitude in decimal degrees."
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Write JSON output to this path instead of stdout.",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip Tier-3 enrichment (RAG citations, consensus, robustness).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging on stderr.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the desired process exit code."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # --- Input validation (exit 1 on ValidationError) -----------------------
    try:
        chart_input = ChartInput(
            dob=args.dob,
            time=args.time,
            tz=args.tz,
            lat=args.lat,
            lon=args.lon,
        )
    except ValidationError as exc:
        sys.stderr.write(f"Invalid chart input: {exc}\n")
        return 1

    # --- Compute (exit 2 on engine failure) ---------------------------------
    try:
        output = compute(chart_input, enrich=not args.no_enrich)
    except Exception:
        logger.exception("Compute failed")
        return 2

    # --- Schema sanity-check (exit 3 if engine returns malformed output) ---
    try:
        ReadingOutput.model_validate(output)
    except ValidationError as exc:
        sys.stderr.write(f"Engine output failed schema validation: {exc}\n")
        return 3

    # --- Emit ---------------------------------------------------------------
    payload = json.dumps(output, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload)
    else:
        sys.stdout.write(payload)
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
