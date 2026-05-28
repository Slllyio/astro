"""Canonical event-class taxonomy bridge.

Pairs with ``person_id_map.parquet`` to kill the second source of schema
drift in this codebase: event-class vocabularies.

Currently the project has two taxonomies that don't bridge cleanly:
  * **Harmonized (5+other classes)** — used in ``events_with_dasha.parquet``
    and cross-corpus analyses. Maps to: marriage, career, fame,
    death_cause_unspecified, relationships, other.
  * **Granular ADB (56 classes)** — per-column event flags in
    ``dasha_mdadpd_corpus.parquet`` and ``dasha_event_corpus.parquet``.
    Covers death-by-disease, death_of_mother, personal, health, etc.

This table makes the mapping explicit and queryable, with an additional
**category** dimension (death / family / relationships / career / personal /
other) for BPHS-style domain rollups that don't fit either existing
taxonomy.

## Output schema (event_class_taxonomy.parquet)

  granular_class       TEXT  -- 56 ADB granular classes (lowercase snake_case)
  harmonized_class     TEXT  -- the cross-corpus class this maps to
  category             TEXT  -- BPHS domain rollup: death|family_loss|
                              -- relationships|career|fame|personal|misc
  is_death_subclass    BOOL  -- True for any death_by_*/death_of_*/death*
  description          TEXT  -- short human-readable note

## Usage

  SELECT *
  FROM dasha_mdadpd_corpus d
  JOIN event_class_taxonomy t
    ON ('event_' || t.granular_class) IN (...)  -- (post-pivot pattern)

Or more typically: pivot the wide ``event_*`` columns to long form once,
then JOIN this taxonomy for category rollup.

Usage:
    python -m app.medini.etl.build_event_class_taxonomy
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
OUTPUT_FILE: Final = "event_class_taxonomy.parquet"

# The full 56-class ADB taxonomy. Each tuple: (granular, harmonized, category, is_death, description).
_TAXONOMY: Final[tuple[tuple[str, str, str, bool, str], ...]] = (
    # Death (any cause) → harmonized death_cause_unspecified
    ("death",                          "death_cause_unspecified", "death",         True,  "Death, unspecified subclass"),
    ("death_by_accident",              "death_cause_unspecified", "death",         True,  "Accidental death"),
    ("death_by_disease",               "death_cause_unspecified", "death",         True,  "Death by illness"),
    ("death_by_execution",             "death_cause_unspecified", "death",         True,  "Capital punishment"),
    ("death_by_heart_attack",          "death_cause_unspecified", "death",         True,  "Cardiac death"),
    ("death_by_homicide",              "death_cause_unspecified", "death",         True,  "Death by violence (victim)"),
    ("death_by_suicide",               "death_cause_unspecified", "death",         True,  "Self-inflicted death"),
    ("death_by_war_or_terrorism",      "death_cause_unspecified", "death",         True,  "Conflict-related death"),
    ("death_cause_unspecified",        "death_cause_unspecified", "death",         True,  "Death, cause unknown"),
    ("death_mysterious",               "death_cause_unspecified", "death",         True,  "Unexplained death"),
    ("other_death",                    "death_cause_unspecified", "death",         True,  "Other death subclass"),
    # Death of family member → relationships (not personal death)
    ("death_of_child",                 "relationships",           "family_loss",   True,  "Death of child"),
    ("death_of_father",                "relationships",           "family_loss",   True,  "Death of father"),
    ("death_of_mate",                  "relationships",           "family_loss",   True,  "Death of spouse/partner"),
    ("death_of_mother",                "relationships",           "family_loss",   True,  "Death of mother"),
    ("death_of_sibling",               "relationships",           "family_loss",   True,  "Death of sibling"),
    ("death_of_significant_person",    "relationships",           "family_loss",   True,  "Death of close non-family"),
    # Marriage
    ("marriage",                       "marriage",                "relationships", False, "Marriage / wedding event"),
    # Relationship and family
    ("relationship",                   "relationships",           "relationships", False, "Relationship event (Round-9 alias)"),
    ("relationships",                  "relationships",           "relationships", False, "Relationship event"),
    ("family",                         "relationships",           "relationships", False, "Family-related event"),
    ("family_trauma",                  "relationships",           "relationships", False, "Family crisis or trauma"),
    ("other_relationship",             "relationships",           "relationships", False, "Other relationship subclass"),
    ("other_family",                   "relationships",           "relationships", False, "Other family subclass"),
    ("children",                       "relationships",           "relationships", False, "Children-related (birth, adoption, etc.)"),
    # Career and work
    ("career",                         "career",                  "career",        False, "Career event"),
    ("work",                           "career",                  "career",        False, "Work event"),
    ("business",                       "career",                  "career",        False, "Business event"),
    ("finance",                        "career",                  "career",        False, "Financial event"),
    ("financial",                      "career",                  "career",        False, "Financial event (alt spelling)"),
    ("other_work",                     "career",                  "career",        False, "Other work subclass"),
    ("other_financial",                "career",                  "career",        False, "Other financial subclass"),
    ("property",                       "career",                  "career",        False, "Property acquisition/sale"),
    # Fame
    ("fame",                           "fame",                    "fame",          False, "Fame event"),
    # Personal (health, identity, self) — folds into 'other' at harmonized level
    ("personal",                       "other",                   "personal",      False, "Personal event (self-directed)"),
    ("health",                         "other",                   "personal",      False, "Health event"),
    ("medical",                        "other",                   "personal",      False, "Medical event"),
    ("mental_health",                  "other",                   "personal",      False, "Mental health event"),
    ("spirituality",                   "other",                   "personal",      False, "Spiritual event"),
    ("education",                      "other",                   "personal",      False, "Education event"),
    ("travel",                         "other",                   "personal",      False, "Travel event"),
    # Crime, legal, accident (misc category, harmonized 'other')
    ("accidents",                      "other",                   "misc",          False, "Accident event"),
    ("crime",                          "other",                   "misc",          False, "Crime event (unspecified)"),
    ("other_crime",                    "other",                   "misc",          False, "Other crime subclass"),
    ("legal",                          "other",                   "misc",          False, "Legal event"),
    ("social_crime_perpetration",      "other",                   "misc",          False, "Crime committed by subject"),
    ("social_crime_victimization",     "other",                   "misc",          False, "Crime committed against subject"),
    ("financial_crime_perpetration",   "other",                   "misc",          False, "Financial crime committed by subject"),
    ("financial_crime_victimization",  "other",                   "misc",          False, "Financial crime against subject"),
    # Social, misc, general
    ("social",                         "other",                   "misc",          False, "Social event"),
    ("other_social",                   "other",                   "misc",          False, "Other social subclass"),
    ("general",                        "other",                   "misc",          False, "Unclassified event"),
    ("misc.",                          "other",                   "misc",          False, "Miscellaneous (Round-9 raw)"),
    ("other_misc.",                    "other",                   "misc",          False, "Other miscellaneous"),
    ("mundane",                        "other",                   "misc",          False, "Mundane event"),
    ("agriculture",                    "other",                   "misc",          False, "Agricultural event"),
)


def build_taxonomy() -> pd.DataFrame:
    """Return the canonical taxonomy as a DataFrame."""
    df = pd.DataFrame.from_records(
        _TAXONOMY,
        columns=[
            "granular_class", "harmonized_class", "category",
            "is_death_subclass", "description",
        ],
    )
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    taxonomy = build_taxonomy()
    out_path = args.data_dir / OUTPUT_FILE
    taxonomy.to_parquet(out_path, index=False)

    logger.info("Wrote %s with %d granular classes", out_path, len(taxonomy))
    logger.info("Harmonized class distribution:\n%s",
                taxonomy["harmonized_class"].value_counts().to_string())
    logger.info("Category distribution:\n%s",
                taxonomy["category"].value_counts().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
