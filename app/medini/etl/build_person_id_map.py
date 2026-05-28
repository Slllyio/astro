"""Canonical ``name_norm`` ↔ ``person_id`` mapping table.

Bridges the Round-9 era data convention (`name_norm` join key) and the
new Silver-layer convention (namespaced ``person_id``). Eliminates the
single most fragile pattern in the codebase: every cross-era join had
to manually compose ``"ADB:" + birth_jd.round(4)`` or similar.

After this ETL runs, the mapping is queryable as ``person_id_map``
in the DuckDB catalog and any join from a Round-9 parquet to the new
Silver layer becomes a clean ``USING (name_norm)`` or ``USING (person_id)``.

## Output schema (person_id_map.parquet)

  corpus_tag         TEXT  -- "ADB" | "WD" | "LA" (Round-9 corpus origin)
  name_norm          TEXT  -- the Round-9 join key (lowercase normalised)
  birth_jd           FLOAT -- canonical link (per chart, ~9-second precision)
  person_id          TEXT  -- new Silver person_id where matched, or
                            -- synthetic "LA:{name_norm}" for LA persons
                            -- (LA isn't in persons.parquet yet)
  is_silver_resident BOOL  -- True if person_id matches a row in persons.parquet
  name_in_persons    TEXT  -- name field from persons.parquet (sanity check)

## Sources

  ADB: dasha_event_corpus.parquet     (name_norm + birth_jd)
  WD : wikidata_dasha_corpus.parquet  (name_norm + birth_jd)
  LA : lunarastro_dasha_corpus.parquet (name_norm + birth_jd; no person_id)
  +  persons.parquet (for ADB + WD person_id lookup via birth_jd)

## Known gap

Lunarastro's ~32k persons never got promoted to the Silver layer
(persons.parquet). They get synthetic ``person_id = "LA:" + name_norm``
in this mapping, and ``is_silver_resident = False``. Future work can
extend ``build_person_event_tables.py`` to ingest LA persons, at which
point this script regenerates with real ``LA:Q...``-style ids.

Usage:
    python -m app.medini.etl.build_person_id_map
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
OUTPUT_FILE: Final = "person_id_map.parquet"

_CORPUS_DASHA_FILES: Final[tuple[tuple[str, str], ...]] = (
    ("ADB", "dasha_event_corpus.parquet"),
    ("WD",  "wikidata_dasha_corpus.parquet"),
    ("LA",  "lunarastro_dasha_corpus.parquet"),
)


def _load_name_norm_to_birth_jd(
    data_dir: Path,
) -> dict[str, pd.DataFrame]:
    """Per-corpus (name_norm, birth_jd) pairings — one row per unique person."""
    out: dict[str, pd.DataFrame] = {}
    for tag, fname in _CORPUS_DASHA_FILES:
        path = data_dir / fname
        if not path.exists():
            logger.warning("Missing %s for corpus %s; skipping", path, tag)
            continue
        df = pd.read_parquet(path, columns=["name_norm", "birth_jd"])
        unique = df.drop_duplicates("name_norm").reset_index(drop=True)
        unique["corpus_tag"] = tag
        logger.info("Loaded %d unique persons from %s (%s)", len(unique), fname, tag)
        out[tag] = unique
    return out


def _build_silver_lookup(data_dir: Path) -> pd.DataFrame:
    """Build (rounded_birth_jd → person_id, name) from persons.parquet.

    The ADB person_id uses ``ADB:{birth_jd:.4f}`` so birth_jd rounding to
    4 decimals (~9 sec TT) is the natural matching key. Wikidata persons
    have NaN birth_jd in persons.parquet (only day-precision), so the
    matching key for WD has to be different — we use the birth_date.
    """
    persons = pd.read_parquet(
        data_dir / "persons.parquet",
        columns=["person_id", "name", "birth_date", "birth_jd", "source"],
    )
    persons["birth_jd_key"] = persons["birth_jd"].round(4)
    return persons


def build_mapping(data_dir: Path) -> pd.DataFrame:
    """Compose the canonical mapping table by joining corpora to persons."""
    corpora = _load_name_norm_to_birth_jd(data_dir)
    silver = _build_silver_lookup(data_dir)

    silver_adb = silver[silver["source"] == "astro_databank"].set_index(
        "birth_jd_key",
    )[["person_id", "name"]]

    out_rows: list[pd.DataFrame] = []

    # ADB: join on rounded birth_jd ≈ ADB person_id construction.
    if "ADB" in corpora:
        adb = corpora["ADB"].copy()
        adb["birth_jd_key"] = adb["birth_jd"].round(4)
        adb = adb.join(silver_adb, on="birth_jd_key", how="left", rsuffix="_silver")
        adb["is_silver_resident"] = adb["person_id"].notna()
        adb["name_in_persons"] = adb["name"]
        adb = adb.drop(columns=["birth_jd_key", "name"])
        out_rows.append(adb)
        n_matched = int(adb["is_silver_resident"].sum())
        logger.info("ADB: %d/%d matched to persons.parquet", n_matched, len(adb))

    # WD: name_norm is the lowercase of either the Q-id or person_name from
    # wikidata_dated_events.parquet. Build the bridge via that source.
    if "WD" in corpora:
        wd = corpora["WD"].copy()
        wd_events_path = data_dir / "wikidata_dated_events.parquet"
        if wd_events_path.exists():
            wd_events = pd.read_parquet(
                wd_events_path, columns=["person_id", "person_name"],
            ).drop_duplicates("person_id")
            # The lower-cased person_name is what became name_norm in the corpus.
            wd_events["name_norm"] = wd_events["person_name"].str.lower()
            # Some rows had person_name == Q-id; those are already matched.
            # Lookup: name_norm → "WD:" + Q-id.
            wd_lookup = (
                wd_events.drop_duplicates("name_norm")
                .set_index("name_norm")
            )
            wd["person_id"] = "WD:" + wd["name_norm"].map(wd_lookup["person_id"])
        else:
            wd["person_id"] = None
        wd["is_silver_resident"] = wd["person_id"].notna()
        wd["name_in_persons"] = None  # WD name_in_persons isn't useful (mostly Q-id-like)
        out_rows.append(wd)
        n_matched = int(wd["is_silver_resident"].sum())
        logger.info("WD : %d/%d matched to persons.parquet", n_matched, len(wd))

    # LA: matches persons.parquet via the "LA:" + name_norm convention.
    # Before LA promotion to Silver, persons rows didn't exist and
    # is_silver_resident was always False. After promotion, look up real
    # presence in persons.parquet.
    if "LA" in corpora:
        la = corpora["LA"].copy()
        la["person_id"] = "LA:" + la["name_norm"].astype(str)
        la_silver = silver[silver["source"] == "lunarastro"][
            ["person_id", "name"]
        ].set_index("person_id")
        la = la.join(la_silver, on="person_id", how="left", rsuffix="_silver")
        la["is_silver_resident"] = la["name"].notna()
        la["name_in_persons"] = la["name"]
        la = la.drop(columns=["name"])
        out_rows.append(la)
        n_matched = int(la["is_silver_resident"].sum())
        logger.info("LA : %d/%d matched to persons.parquet", n_matched, len(la))

    canonical_cols = [
        "corpus_tag", "name_norm", "birth_jd",
        "person_id", "is_silver_resident", "name_in_persons",
    ]
    result = pd.concat(out_rows, ignore_index=True)[canonical_cols]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    mapping = build_mapping(args.data_dir)
    out_path = args.data_dir / OUTPUT_FILE
    mapping.to_parquet(out_path, index=False)

    total = len(mapping)
    matched = int(mapping["is_silver_resident"].sum())
    by_corpus = mapping.groupby("corpus_tag").agg(
        rows=("name_norm", "count"),
        matched=("is_silver_resident", "sum"),
    )
    logger.info(
        "Wrote %s\n%s\nTotal: %d rows, %d (%.0f%%) matched to Silver",
        out_path, by_corpus.to_string(), total, matched, matched / total * 100,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
