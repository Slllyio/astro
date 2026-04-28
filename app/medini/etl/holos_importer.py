"""Convert ASTROCRM's holos_clean.csv (lat/lon) joined with its raw
astro_people.csv (categories) into the raw.csv schema our Stage 2 ETL
expects.

ASTROCRM ships two CSVs derived from Astro-Databank:

  holos_clean.csv     - 61,583 AA+A records.
                        Has: name, birth_year/month/day/hour/min/sec,
                        utc_offset, latitude, longitude, rodden_rating
                        Missing: categories (occupation field is empty)

  astro_people.csv    - 6,488 raw records (AA + A + B + C + X + DD).
                        Has: name, date_of_birth, time_of_birth,
                        place_of_birth, rodden_rating, **categories**
                        Missing: latitude, longitude (only place_of_birth text)

Inner-joining the two on `name` yields 4,929 fully-equipped records:
the geographic precision of holos_clean + the vocational labels of
astro_people. That's ~5x our current Wayback corpus (1k records) and
brings the same Wayback-style category vocabulary so existing model
targets (politics, entertainment, etc.) extend transparently.

Source: https://github.com/jfsagro-glitch/ASTROCRM (no LICENSE; public
GitHub repo). The underlying birth data is Astro-Databank's, with the
usual research-use posture as our other Astrodienst-derived sources.

CLI:
    python -m app.medini.etl.holos_importer \\
        --holos-clean   data/holos/holos_clean.csv \\
        --astro-people  data/holos/astro_people.csv \\
        --output        data/astro_databank/raw_holos.csv \\
        [--rodden-min A]
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Allow large CSV cells (biography field can be long).
csv.field_size_limit(10 ** 7)

# raw.csv columns Stage 2 expects.
OUTPUT_COLUMNS: tuple[str, ...] = (
    "name", "date_of_birth", "time_of_birth",
    "latitude", "longitude", "tz_offset",
    "rodden_rating", "categories", "source_url",
)

# Acceptable Rodden ratings in priority order. CLI --rodden-min picks the
# floor; everything at or above is kept.
_RODDEN_PRIORITY: tuple[str, ...] = ("AA", "A", "B", "C", "DD", "X", "XX")


def _filter_by_rodden(df: pd.DataFrame, min_rating: str) -> pd.DataFrame:
    """Keep only rows whose rodden_rating is at least `min_rating` in the
    standard priority order."""
    min_rating = (min_rating or "").upper().strip()
    if min_rating not in _RODDEN_PRIORITY:
        raise ValueError(
            f"unknown rating {min_rating!r}; expected one of {_RODDEN_PRIORITY}"
        )
    cutoff_idx = _RODDEN_PRIORITY.index(min_rating)
    accepted = set(_RODDEN_PRIORITY[: cutoff_idx + 1])
    rating_col = df["rodden_rating"].astype(str).str.upper().str.strip()
    return df[rating_col.isin(accepted)].copy()


def _format_date(year: int, month: int, day: int) -> str:
    """birth_year/month/day → ISO YYYY-MM-DD. Returns '' for invalid."""
    try:
        y, m, d = int(year), int(month), int(day)
        if not (1 <= m <= 12 and 1 <= d <= 31):
            return ""
        return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, TypeError):
        return ""


def _format_time(hour, minute, second) -> str:
    """birth_hour/min/sec → HH:MM:SS. Returns '' for invalid."""
    try:
        h, m, s = int(hour), int(minute), int(second)
        if not (0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60):
            return ""
        return f"{h:02d}:{m:02d}:{s:02d}"
    except (ValueError, TypeError):
        return ""


def import_holos(
    holos_clean_path: Path,
    astro_people_path: Path,
    output_path: Path,
    *,
    min_rodden: str = "A",
) -> dict[str, int]:
    """Read both ASTROCRM CSVs, inner-join on name, write a raw.csv.

    Returns stats dict: holos_rows, ap_rows, joined_rows, written.
    """
    if not holos_clean_path.exists():
        raise FileNotFoundError(f"holos_clean missing: {holos_clean_path}")
    if not astro_people_path.exists():
        raise FileNotFoundError(f"astro_people missing: {astro_people_path}")

    logger.info("loading %s", holos_clean_path)
    hc = pd.read_csv(holos_clean_path, low_memory=False)
    logger.info("loading %s", astro_people_path)
    ap = pd.read_csv(astro_people_path, low_memory=False)

    stats = {
        "holos_rows": len(hc),
        "ap_rows": len(ap),
        "joined_rows": 0,
        "written": 0,
        "skipped_no_categories": 0,
        "skipped_invalid_date": 0,
        "skipped_below_rodden_min": 0,
    }

    # Inner-join: name from holos_clean must appear in astro_people.
    # We take lat/lon/utc_offset/rodden from holos_clean, categories from
    # astro_people (since holos_clean's gender/occupation are blank).
    hc_named = hc.dropna(subset=["name"]).copy()
    ap_named = ap.dropna(subset=["name", "categories"])[["name", "categories"]].copy()
    ap_named = ap_named.drop_duplicates(subset="name", keep="first")

    merged = hc_named.merge(ap_named, on="name", how="inner")
    stats["joined_rows"] = len(merged)

    merged = _filter_by_rodden(merged, min_rodden)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(OUTPUT_COLUMNS))
        writer.writeheader()

        for _, row in merged.iterrows():
            date_str = _format_date(
                row["birth_year"], row["birth_month"], row["birth_day"],
            )
            if not date_str:
                stats["skipped_invalid_date"] += 1
                continue
            time_str = _format_time(
                row["birth_hour"], row["birth_min"], row["birth_sec"],
            )
            if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
                continue
            categories = (row.get("categories") or "").strip()
            if not categories:
                stats["skipped_no_categories"] += 1
                continue

            # Categories in astro_people use ' ; ' or '; ' or sometimes
            # '\n' separators. Normalise to the semicolon convention our
            # Stage 2 ETL expects.
            cats_normalised = ";".join(
                c.strip() for c in categories.replace("\n", ";").split(";")
                if c.strip()
            )

            writer.writerow({
                "name": str(row["name"]).strip(),
                "date_of_birth": date_str,
                "time_of_birth": time_str,
                "latitude": f"{float(row['latitude']):.6f}",
                "longitude": f"{float(row['longitude']):.6f}",
                "tz_offset": f"{float(row['utc_offset']):.4f}"
                              if pd.notna(row['utc_offset']) else "",
                "rodden_rating": str(row["rodden_rating"]).upper().strip(),
                "categories": cats_normalised,
                "source_url": (
                    "https://github.com/jfsagro-glitch/ASTROCRM"
                    f"#holos:{row.get('birth_year', '')}"
                    f":{str(row['name']).strip()[:40]}"
                ),
            })
            stats["written"] += 1

    return stats


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.holos_importer",
        description="Import ASTROCRM holos_clean + astro_people into raw.csv format.",
    )
    parser.add_argument(
        "--holos-clean", type=Path, required=True,
        help="Path to holos_clean.csv (provides lat/lon + clean dates).",
    )
    parser.add_argument(
        "--astro-people", type=Path, required=True,
        help="Path to astro_people.csv (provides vocational categories).",
    )
    parser.add_argument(
        "--output", type=Path, required=True,
        help="Where to write raw.csv. Parent dir is created.",
    )
    parser.add_argument(
        "--rodden-min", type=str, default="A",
        help="Lowest acceptable Rodden rating (AA/A/B/C/DD/X/XX). Default A.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = import_holos(
        holos_clean_path=args.holos_clean,
        astro_people_path=args.astro_people,
        output_path=args.output,
        min_rodden=args.rodden_min,
    )
    logger.info(
        "import complete: holos=%d ap=%d joined=%d written=%d "
        "skipped_no_categories=%d skipped_invalid_date=%d",
        stats["holos_rows"], stats["ap_rows"], stats["joined_rows"],
        stats["written"], stats["skipped_no_categories"],
        stats["skipped_invalid_date"],
    )
    print(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
