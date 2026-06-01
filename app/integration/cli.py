"""Integration CLI — single entrypoint exercising both adapters.

Usage:
  py -3.12 -m app.integration --mode enhance --in reading.json --out enhanced.json
  py -3.12 -m app.integration --mode compare --in reading.json --target-jd 2462000.5
  py -3.12 -m app.integration --mode generate-and-enhance \
      --dob=1990-07-15 --time=12:00 --tz=+05:30 \
      --lat=12.97 --lon=77.59 --out=enhanced.json

Modes:
  enhance               — load a Track-A reading JSON, attach DKP translations,
                          write IntegratedReadingOutput JSON.
  compare               — load a Track-A reading JSON, reconstruct its
                          chara_dasha, diff against Track B's chara_dasha for
                          the same chart, print/write the report.
  generate-and-enhance  — run Track A's full pipeline first (DOB+place inputs),
                          then enhance in the same shot. Convenience mode.

All output files are UTF-8 JSON with ``ensure_ascii=False`` so Sanskrit
shloka text stays readable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.integration.chara_compare import CharaComparisonReport, compare_chara_dasha
from app.integration.dkp_enhancer import IntegratedReadingOutput, enhance, registry_size
from app.reading.sequences.chara_dasha import CharaDashaResult


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.integration",
        description="Bridge Track-A reading engine + Track-B astrologer's-lens "
                    "framework. Read-only over both; produces a new envelope.",
    )
    parser.add_argument(
        "--mode",
        choices=["enhance", "compare", "generate-and-enhance"],
        required=True,
        help="Which adapter to run.",
    )
    parser.add_argument(
        "--in", dest="in_path",
        type=Path,
        help="Input Track-A reading JSON file (for enhance/compare).",
    )
    parser.add_argument(
        "--out", dest="out_path",
        type=Path,
        help="Output file. If omitted, JSON is printed to stdout.",
    )
    parser.add_argument(
        "--target-jd",
        type=float,
        help="Optional target Julian Day for compare mode's current-MD check.",
    )
    # Inputs for generate-and-enhance mode (mirrors app.reading.cli flags).
    parser.add_argument("--dob", help="Date of birth YYYY-MM-DD (generate-and-enhance).")
    parser.add_argument("--time", help="Time of birth HH:MM (generate-and-enhance).")
    parser.add_argument("--tz", help="Timezone offset, e.g. +05:30 (generate-and-enhance).")
    parser.add_argument("--lat", type=float, help="Latitude (generate-and-enhance).")
    parser.add_argument("--lon", type=float, help="Longitude (generate-and-enhance).")
    parser.add_argument(
        "--no-enrich", action="store_true",
        help="In generate-and-enhance mode, skip Track-A Tier-3 enrichments "
             "(faster — useful when only DKP enhancement is wanted).",
    )
    return parser


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def _load_reading(in_path: Path) -> dict[str, Any]:
    if not in_path.exists():
        raise SystemExit(f"Input file not found: {in_path}")
    with in_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise SystemExit(f"Input is not a JSON object: {in_path}")
    return data


def _emit(payload: dict[str, Any], out_path: Path | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if out_path is None:
        sys.stdout.write(text + "\n")
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")


def _run_enhance(args: argparse.Namespace) -> int:
    if args.in_path is None:
        raise SystemExit("--in is required for --mode enhance")
    reading = _load_reading(args.in_path)
    result: IntegratedReadingOutput = enhance(reading)
    _emit(result.model_dump(mode="json"), args.out_path)
    print(
        f"DKP enhancer: registry={registry_size()} records, "
        f"attached={result.dkp_translations_summary.total_records_attached}, "
        f"unique={len(result.dkp_translations_summary.records)}",
        file=sys.stderr,
    )
    return 0


def _reconstruct_chara_result(reading: dict[str, Any]) -> CharaDashaResult:
    chara_block = (reading.get("sequences") or {}).get("chara_dasha")
    if chara_block is None:
        raise SystemExit(
            "Input reading has no sequences.chara_dasha block. "
            "Re-run app.reading.cli with --enrich or regenerate at schema_version >= 1.1.0."
        )
    return CharaDashaResult.model_validate(chara_block)


def _run_compare(args: argparse.Namespace) -> int:
    if args.in_path is None:
        raise SystemExit("--in is required for --mode compare")
    reading = _load_reading(args.in_path)
    a_result = _reconstruct_chara_result(reading)

    chart_block = reading.get("chart") or {}
    primitives = reading.get("primitives") or {}
    foundations = reading.get("foundations") or {}

    lagna_sign = (
        chart_block.get("ascendant_sign")
        or primitives.get("ascendant_sign")
        or foundations.get("ascendant_sign")
    )
    birth_jd = (
        chart_block.get("birth_jd")
        or primitives.get("birth_jd")
        or foundations.get("birth_jd")
    )
    if lagna_sign is None or birth_jd is None:
        raise SystemExit(
            "Could not extract ascendant_sign / birth_jd from input reading. "
            "Update the loader extraction keys to match your schema."
        )

    report: CharaComparisonReport = compare_chara_dasha(
        a_result,
        lagna_sign=int(lagna_sign),
        birth_jd=float(birth_jd),
        target_jd=args.target_jd,
    )
    _emit(report.model_dump(mode="json"), args.out_path)
    print(f"Chara comparator verdict: {report.verdict_summary}", file=sys.stderr)
    return 0 if report.full_timeline_agrees else 0  # exit 0 either way; verdict is data


def _run_generate_and_enhance(args: argparse.Namespace) -> int:
    required = ("dob", "time", "tz", "lat", "lon")
    missing = [name for name in required if getattr(args, name) in (None, "")]
    if missing:
        raise SystemExit(
            f"--mode generate-and-enhance requires: {', '.join('--' + m for m in required)}; "
            f"missing: {', '.join('--' + m for m in missing)}"
        )

    # Lazy import — Track A's compute pulls in swisseph and is heavy. We keep
    # the import inside this function so other modes start fast.
    from app.reading.proforma import compute as track_a_compute

    reading_obj = track_a_compute(
        dob=args.dob,
        time=args.time,
        tz=args.tz,
        lat=args.lat,
        lon=args.lon,
        enrich=not args.no_enrich,
    )
    result: IntegratedReadingOutput = enhance(reading_obj)
    _emit(result.model_dump(mode="json"), args.out_path)
    print(
        f"Generated + enhanced: attached="
        f"{result.dkp_translations_summary.total_records_attached} records",
        file=sys.stderr,
    )
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.mode == "enhance":
        return _run_enhance(args)
    if args.mode == "compare":
        return _run_compare(args)
    if args.mode == "generate-and-enhance":
        return _run_generate_and_enhance(args)
    parser.error(f"Unknown mode: {args.mode}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
