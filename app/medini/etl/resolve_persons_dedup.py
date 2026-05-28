"""Cross-corpus person dedup: link ADB / Wikidata / Lunarastro rows of the same human.

The data-engineer audit (4-agent dispatch) recommended a separate linkage
table rather than collapsing the source person_ids, so corpus-specific
analyses remain possible. Each ``canonical_id`` is the highest-precision
member of a match cluster:

  ADB > Wikidata > Lunarastro

ADB wins because it has time-of-birth (Rodden-rated); Wikidata is
day-precision; Lunarastro is mixed.

Match logic (deterministic, conservative):
  exact match on ``(name_key, birth_date)`` where
    name_key = lowercase, diacritics stripped, punctuation removed,
               whitespace collapsed.
  birth_date is the YYYY-MM-DD string.

We avoid fuzzy name matching in v1: false positives across a 43k corpus
contaminate downstream ML far worse than missing some genuine matches.
A second pass with Jaro-Winkler can be added once we measure false
negatives.

Output schema (resolved_persons.parquet):
  canonical_id  TEXT  -- best (highest-precision) source person_id
  source_ids    LIST<TEXT>  -- all merged source_ids (always includes canonical_id)
  name_key      TEXT  -- the normalized name used for matching
  birth_date    TEXT  -- the YYYY-MM-DD used for matching (or "" if missing)
  n_corpora     INT   -- 1..3
  match_method  TEXT  -- always "exact_name_date" in v1

Usage:
    python -m app.medini.etl.resolve_persons_dedup
"""
from __future__ import annotations

import argparse
import logging
import re
import unicodedata
from pathlib import Path
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
PERSONS_FILE: Final = "persons.parquet"
OUTPUT_FILE: Final = "resolved_persons.parquet"

# Priority for canonical_id selection within a match cluster.
_SOURCE_PRIORITY: Final[dict[str, int]] = {
    "astro_databank": 0,  # highest priority (time-of-birth precision)
    "wikidata": 1,
    "lunarastro": 2,
}

# Match-key regex: strip everything except lowercase ASCII letters and digits
# after Unicode normalization to NFKD (decomposes accents into combining marks
# which then get filtered out as non-ASCII).
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_name_key(name: str | None) -> str:
    """Normalize a name to a match key.

    Steps:
      1. NFKD decomposition (separates accents from base characters)
      2. ASCII-only filter (drops the combining diacritical marks)
      3. Lowercase
      4. Strip all non-alphanumeric characters (handles "agnès b." vs "Agnes B")
    """
    if name is None or pd.isna(name):
        return ""
    decomposed = unicodedata.normalize("NFKD", str(name))
    ascii_only = decomposed.encode("ascii", errors="ignore").decode("ascii")
    return _NON_ALNUM.sub("", ascii_only.lower())


def _pick_canonical(group_ids: list[str], group_sources: list[str]) -> str:
    """Choose the highest-priority person_id within a match cluster."""
    pairs = sorted(
        zip(group_ids, group_sources),
        key=lambda p: _SOURCE_PRIORITY.get(p[1], 999),
    )
    return pairs[0][0]


def resolve(persons: pd.DataFrame) -> pd.DataFrame:
    """Run the dedup pass.

    Persons missing a birth_date are excluded from match clustering
    (no birth date means no reliable join key) but still get their own
    singleton cluster.
    """
    df = persons.copy()
    df["name_key"] = df["name"].map(normalize_name_key)
    df["match_key"] = df["name_key"] + "||" + df["birth_date"].fillna("").astype(str)

    # Persons missing name_key OR birth_date are always singleton clusters.
    missing = (df["name_key"] == "") | (df["birth_date"].fillna("") == "")
    df.loc[missing, "match_key"] = df.loc[missing, "person_id"]  # unique per row

    grouped = df.groupby("match_key", sort=False).agg(
        source_ids=("person_id", list),
        sources=("source", list),
        name_key=("name_key", "first"),
        birth_date=("birth_date", "first"),
    ).reset_index(drop=True)

    grouped["canonical_id"] = grouped.apply(
        lambda r: _pick_canonical(r["source_ids"], r["sources"]), axis=1,
    )
    grouped["n_corpora"] = grouped["sources"].map(lambda s: len(set(s)))
    grouped["match_method"] = "exact_name_date"

    return grouped[[
        "canonical_id", "source_ids", "name_key", "birth_date",
        "n_corpora", "match_method",
    ]]


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    persons = pd.read_parquet(args.data_dir / PERSONS_FILE)
    logger.info("Loaded %d persons", len(persons))

    resolved = resolve(persons)
    matched = (resolved["n_corpora"] > 1).sum()
    logger.info(
        "Resolved %d clusters (%d cross-corpus matches found)",
        len(resolved), matched,
    )

    out_path = args.data_dir / OUTPUT_FILE
    resolved.to_parquet(out_path, index=False)
    logger.info("Wrote %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
