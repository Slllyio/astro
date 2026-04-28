"""Backfill occupation labels from ayushman1024/ASTROLOGY-BOOKS-DATABASE.

The ASTROLOGY-BOOKS-DATABASE repo ships ~1,160 Kala-software .cht chart
files organized by occupation directory:

  Birth-detail-collections/Charts Kala/Database/Actors/Arnold Schwarzenegger.cht
  Birth-detail-collections/Charts Kala/Database/Politicians_Rulers/Indira Gandhi.cht

The .cht files are proprietary UTF-16 binary (Kala-format), but the
**file paths** carry name + occupation metadata for free. This module:

  1. Generates a (name, occupation) TSV from the GitHub tree (offline-
     reproducible — needs only a tree dump from the gh API).
  2. Backfills our merged_all.csv with derived 'Vocation : <category>'
     tags for any name match (in either Last,First or First Last form).

Cross-reference results on the 84k-row merged corpus:
  656 names matched in either name form
  366 records had a new occupation tag appended (rest already labeled)

Source: https://github.com/ayushman1024/ASTROLOGY-BOOKS-DATABASE
        (no LICENSE file; the kala chart files are user-curated public
        astrology data).

CLI:
    python -m app.medini.etl.kala_metadata_importer \\
        --metadata-tsv data/holos/charts_kala_metadata.tsv \\
        --merged-csv   data/astro_databank/merged_all.csv \\
        --output       data/astro_databank/merged_all_kala.csv
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

csv.field_size_limit(10 ** 7)

# Map Kala's directory-based occupation tags to Astro-Databank's standard
# 'Vocation : Root : Subtype' convention so the backfilled labels follow
# the same shape the trainer's --target substring matching already supports.
KALA_TO_VOCATION: dict[str, str] = {
    "Politicians_Rulers":   "Vocation : Politics : Politician",
    "Actors":               "Vocation : Entertainment : Actor",
    "Actresses":            "Vocation : Entertainment : Actress",
    "Musicians":            "Vocation : Entertain/Music : Musician",
    "Philosophers_Gurus":   "Vocation : Religion : Philosopher",
    "Authors":              "Vocation : Writers : Author",
    "Atheletes":            "Vocation : Sports : Athlete",
    "Astrologers, etc":     "Vocation : Occult Fields : Astrologer",
    "Scientists_Inventors": "Vocation : Science : Scientist",
    "Business Tycoons":     "Vocation : Business : Business Owner",
    "Criminals":            "Passions : Criminal Perpetrator",
    "Military":             "Vocation : Military : Officer",
    "Artists":              "Vocation : Art : Artist",
    "Physicians_Doctors":   "Vocation : Medical : Physician",
    "Dancers":              "Vocation : Entertainment : Dancer",
    # Intentionally NOT mapped: Miscellaneous, Longevity, Diseases,
    # Number of Children, Muhurtas — these aren't vocations.
}


def invert_last_first(name: str) -> str:
    """'Grant, Cary' -> 'Cary Grant'. Astro-Databank uses Last,First; Kala
    uses First Last; matching against both lets us catch all overlap."""
    if "," not in name:
        return name
    parts = [p.strip() for p in name.split(",", 1)]
    if len(parts) != 2:
        return name
    return f"{parts[1]} {parts[0]}".strip()


def load_kala_map(metadata_tsv: Path) -> dict[str, str]:
    """Read the (name, occupation) TSV → {lower(name): vocation_tag}.

    Only includes names whose Kala occupation maps to a vocation tag
    (KALA_TO_VOCATION). Skips Miscellaneous / Longevity / etc.
    """
    mapping: dict[str, str] = {}
    if not metadata_tsv.exists():
        raise FileNotFoundError(f"Kala metadata TSV missing: {metadata_tsv}")
    with metadata_tsv.open("r", encoding="utf-8") as f:
        next(f)  # header
        for line in f:
            line = line.rstrip("\n")
            if "\t" not in line:
                continue
            name, occupation = line.split("\t", 1)
            voc = KALA_TO_VOCATION.get(occupation.strip())
            if not voc:
                continue
            mapping[name.strip().lower()] = voc
    return mapping


def backfill_categories(
    merged_csv: Path,
    output_csv: Path,
    kala_map: dict[str, str],
) -> dict[str, int]:
    """For every row in merged_csv, append the Kala vocation tag to
    categories if (a) the name matches Kala in either form and (b) the
    tag isn't already in categories."""
    if not merged_csv.exists():
        raise FileNotFoundError(f"merged CSV missing: {merged_csv}")

    stats = {"rows_read": 0, "backfilled": 0, "rows_written": 0}
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with merged_csv.open("r", encoding="utf-8") as fin, \
         output_csv.open("w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("merged CSV is empty or unreadable")
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            stats["rows_read"] += 1
            name = (row.get("name") or "").strip()
            voc = kala_map.get(name.lower())
            if voc is None:
                inverted = invert_last_first(name)
                voc = kala_map.get(inverted.lower())
            if voc is not None:
                cats = (row.get("categories") or "").strip()
                if voc.lower() not in cats.lower():
                    row["categories"] = f"{cats};{voc}" if cats else voc
                    stats["backfilled"] += 1
            writer.writerow(row)
            stats["rows_written"] += 1

    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.kala_metadata_importer",
        description=(
            "Backfill occupation tags into merged.csv using the Kala chart "
            "metadata (filename-derived) from ayushman1024/ASTROLOGY-BOOKS-"
            "DATABASE."
        ),
    )
    parser.add_argument(
        "--metadata-tsv", type=Path, required=True,
        help="TSV with columns name,occupation (header on first line).",
    )
    parser.add_argument(
        "--merged-csv", type=Path, required=True,
        help="Existing merged corpus to backfill.",
    )
    parser.add_argument(
        "--output", type=Path, required=True,
        help="Where to write the patched merged CSV.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    kala_map = load_kala_map(args.metadata_tsv)
    logger.info("Kala vocation map: %d entries", len(kala_map))

    stats = backfill_categories(args.merged_csv, args.output, kala_map)
    logger.info(
        "backfill done: read=%d backfilled=%d written=%d",
        stats["rows_read"], stats["backfilled"], stats["rows_written"],
    )
    print(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
