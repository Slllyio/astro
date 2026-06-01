"""Safely archive unreferenced legacy parquets to a ``legacy/`` subfolder.

Round-11 introduced a clean canonical Silver layer (persons.parquet,
charts.parquet, dasha_*, etc.). Many Round 5/6/9-era parquets are now
superseded but kept on disk for safety. This script moves the
**unreferenced** ones to ``app/medini/data/legacy/``, leaving the
canonical layer + actively-referenced files in place.

The archive process is conservative:
  1. For each candidate file, grep `app/` and `tests/` for the stem.
  2. If no Python file references it, move it.
  3. If anything references it, log a warning and skip.

The destination is preserved on disk (not deleted) so recovery is
``mv app/medini/data/legacy/foo.parquet app/medini/data/foo.parquet``.

Usage:
    python -m app.medini.etl.archive_legacy_parquets --dry-run
    python -m app.medini.etl.archive_legacy_parquets
"""
from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
LEGACY_SUBDIR: Final = "legacy"

# Canonical files that must NEVER be archived (the Silver/Tier-0..3 layer).
_CANONICAL: Final[frozenset[str]] = frozenset({
    "persons.parquet", "events.parquet",
    "charts.parquet", "dasha_windows.parquet",
    "dasha_tree.parquet", "events_with_dasha.parquet",
    "chart_edges.parquet", "static_graph_edges.parquet",
    "person_id_map.parquet", "event_class_taxonomy.parquet",
    "resolved_persons.parquet",
    # Round-9 source corpora (still inputs to the bridges)
    "dasha_corpus_birth_data.parquet",
    "event_corpus_all.parquet",
    "wikidata_dated_events.parquet",
    "lunarastro_natal.parquet",
    "lunarastro_dasha_corpus.parquet",
    "lunarastro_natal_lord_houses.parquet",
    "wikidata_dasha_corpus.parquet",
    "wikidata_natal_lord_houses.parquet",
    "dasha_event_corpus.parquet",
    "natal_lord_houses.parquet",
    "dasha_mdadpd_corpus.parquet",
    "dasha_stage_d_features.parquet",
})

# Candidates pre-identified as legacy from Round 5/6/9 work. Filtered down
# at runtime by reference-check.
_CANDIDATES: Final[tuple[str, ...]] = (
    "ml_astro_15k.parquet", "ml_astro_round5.parquet",
    "ml_astro_tier_a.parquet", "ml_astro_tier_a_dasha_kinematic.parquet",
    "ml_astro_with_events.parquet", "ml_astro_with_lunar.parquet",
    "ml_astro_features.parquet", "ml_astro_features_full.parquet",
    "ml_astro_features_merged.parquet", "ml_astro_features_wayback.parquet",
    "ml_astro_all.parquet", "ml_astro_max.parquet", "ml_astro_voc.parquet",
    "event_corpus_round5_all.parquet",
    "event_corpus_career.parquet", "event_corpus_career_yogas.parquet",
    "event_corpus_marriage.parquet", "event_corpus_marriage_smoke.parquet",
    "event_corpus_work.parquet", "event_corpus_death_disease.parquet",
    "lunarastro_fame.parquet", "lunarastro_fame_yogas.parquet",
    "lunarastro_career.parquet", "lunarastro_career_yogas.parquet",
    "lunarastro_death.parquet", "lunarastro_health.parquet",
    "lunarastro_marriage.parquet", "lunarastro_politics.parquet",
    "dasha_corpus_yogas.parquet", "dasha_event_corpus_smoke.parquet",
    "dasha_mdadpd_smoke.parquet", "dasha_stage_d_features_smoke.parquet",
    "dasha_stage_d_features_subsample.parquet",
    "dasha_subsample_2000_persons.parquet",
    "lunarastro_natal_smoke.parquet",
)


def is_referenced(filename: str) -> tuple[bool, list[str]]:
    """Return ``(True, [reference_files])`` if any non-pycache, non-self
    file mentions the parquet stem; else ``(False, [])``.

    The archive script itself contains a list of all candidate filenames,
    so we exclude its own path from the search.
    """
    stem = filename.removesuffix(".parquet")
    own_path_fragment = "archive_legacy_parquets"
    try:
        result = subprocess.run(
            ["grep", "-r", "-l", "--exclude-dir=__pycache__", stem,
             "app/", "tests/"],
            capture_output=True, text=True, timeout=15,
        )
        if not result.stdout.strip():
            return False, []
        files = [
            f for f in result.stdout.strip().split("\n")
            if own_path_fragment not in f
        ]
        return (bool(files), files)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return True, ["(grep failed — assuming referenced)"]


def archive(data_dir: Path, dry_run: bool = False) -> dict[str, list[str]]:
    """Move unreferenced legacy parquets to ``data_dir/legacy/``.

    Returns a dict with keys: ``archived``, ``referenced_kept``, ``missing``.
    """
    legacy_dir = data_dir / LEGACY_SUBDIR
    if not dry_run:
        legacy_dir.mkdir(parents=True, exist_ok=True)

    archived: list[str] = []
    referenced_kept: list[tuple[str, list[str]]] = []
    missing: list[str] = []

    for filename in _CANDIDATES:
        if filename in _CANONICAL:
            continue  # safety net
        src = data_dir / filename
        if not src.exists():
            missing.append(filename)
            continue

        referenced, refs = is_referenced(filename)
        if referenced:
            referenced_kept.append((filename, refs))
            logger.info("REFERENCED keep %-50s  refs=%d",
                        filename, len(refs))
            continue

        dst = legacy_dir / filename
        if dry_run:
            logger.info("WOULD archive %s -> %s", filename, dst.name)
        else:
            shutil.move(str(src), str(dst))
            logger.info("ARCHIVED %s -> %s", filename, dst.name)
        archived.append(filename)

    return {
        "archived": archived,
        "referenced_kept": [name for name, _ in referenced_kept],
        "missing": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what would be archived without moving anything.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    result = archive(args.data_dir, dry_run=args.dry_run)
    logger.info(
        "Summary: archived=%d  referenced_kept=%d  missing=%d",
        len(result["archived"]), len(result["referenced_kept"]),
        len(result["missing"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
