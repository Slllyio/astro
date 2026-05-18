"""Derive event-based ML targets from events_all.csv + persons corpus.

The Phase 5 round-2 trainer can only consume targets that appear as
substring matches inside a row's `categories_lower`. This script
joins the per-event corpus to the per-person corpus by name, derives
new event-based booleans, and EMITS THREE THINGS:

  1. raw_with_event_tags.csv
     Same shape as merged_with_lunar.csv but with new event-derived
     category tags appended to each row's `categories` field. The
     existing trainer can then target them via the usual substring
     match (e.g. `--target event_divorced`).

     Tags added (one per person, when applicable):
       event_divorced                ever had a divorce event (~479)
       event_married                 ever had a marriage event (~1,970)
       event_multi_marriage          had 2+ marriage events (~438)
       event_died_young              death event with age < 50 (~879)
       event_lived_long              death event with age >= 80 (~1,118)

  2. event_regression_targets.csv
     Per-person numeric targets that the existing binary classifier
     can't handle. Used by `train_regressor.py` (separate XGBoost
     regressor). Columns:
       name, age_first_marriage, age_at_death, total_event_count

  3. event_vocation_multiclass.csv
     Per-person primary vocation root (Politics / Sports / Writers /
     Entertainment / Business / Art / Science / Military / Education / Other)
     determined by argmax across existing Vocation : <Root> : ... category
     tags in the source raw.csv. Used by `train_multiclass.py`.

CLI:
    python -m app.medini.etl.derive_event_targets \\
        --persons-csv data/astro_databank/merged_with_lunar.csv \\
        --events-csv  data/astro_databank/events_all.csv \\
        --output-persons data/astro_databank/merged_with_events.csv \\
        --output-regression data/astro_databank/event_regression_targets.csv \\
        --output-multiclass data/astro_databank/event_vocation_multiclass.csv
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Allow large CSV cells.
csv.field_size_limit(10 ** 7)

# Substring patterns to detect each event type. Lower-cased; matched
# against (event_root || event_code).
DIVORCE_TOKENS = ("divorce",)
MARRIAGE_TOKENS = ("marriage",)
DEATH_TOKENS = ("death",)

# Vocation roots we care about for multi-class. Order = priority for
# tie-breaking (a person tagged with both Politics and Entertainment
# gets the higher-counted root). Plain English names matching the
# substring vocabulary of the existing tags.
VOCATION_ROOTS: tuple[str, ...] = (
    "politics", "sports", "writers", "entertainment", "business",
    "art", "science", "military", "education", "law", "medical",
    "beauty", "religion", "occult",
)

# Threshold for "lived_long"; classical Vedic uses 80+ for poorna ayur.
LONG_LIFE_THRESHOLD = 80
# Threshold for "died_young"; below half the expected natural span.
DIED_YOUNG_THRESHOLD = 50


# ---------- Helpers ----------

def _normalise_name(name: str) -> str:
    """Strip + lowercase for join keys. Matches the merger's dedup convention."""
    return (name or "").strip().lower()


def _build_birth_year_map(persons_csv: Path) -> dict[str, int]:
    """Read the source persons CSV → {lowercased_name: birth_year}.

    Multiple rows with the same name are uncommon (the merger collapses
    them); when present, last write wins. Year is parsed from the
    `date_of_birth` ISO string (YYYY-MM-DD).
    """
    if not persons_csv.exists():
        raise FileNotFoundError(f"persons CSV missing: {persons_csv}")
    mapping: dict[str, int] = {}
    with persons_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            name = _normalise_name(row.get("name", ""))
            dob = (row.get("date_of_birth") or "").strip()
            if not (name and dob):
                continue
            try:
                year = int(dob[:4])
            except ValueError:
                continue
            if 1700 <= year <= 2030:
                mapping[name] = year
    return mapping


def _has_event_matching(events_df: pd.DataFrame, tokens: tuple[str, ...]) -> pd.Series:
    """Boolean mask: does each row's event_root OR event_code contain ANY
    of the tokens (case-insensitive substring)?"""
    root = events_df["event_root"].fillna("").str.lower()
    code = events_df["event_code"].fillna("").str.lower()
    mask = pd.Series(False, index=events_df.index)
    for tok in tokens:
        mask = mask | root.str.contains(tok, regex=False) | code.str.contains(tok, regex=False)
    return mask


# ---------- Binary tag derivation ----------

def derive_binary_event_tags(
    persons_csv: Path,
    events_csv: Path,
    output_csv: Path,
) -> dict[str, int]:
    """Compute per-person binary event tags and APPEND them to the
    `categories` column of a new persons CSV.

    Output shape == input shape; only the `categories` column changes.
    """
    if not (persons_csv.exists() and events_csv.exists()):
        raise FileNotFoundError("inputs missing")

    birth_years = _build_birth_year_map(persons_csv)
    events = pd.read_csv(events_csv, low_memory=False)
    events["_normalised_name"] = events["name"].fillna("").astype(str).str.strip().str.lower()
    events["_birth_year"] = events["_normalised_name"].map(birth_years)
    events["_event_year"] = pd.to_numeric(events["event_year"], errors="coerce")
    events["_age"] = events["_event_year"] - events["_birth_year"]

    # Build per-name tag set
    divorce_people = set(
        events.loc[_has_event_matching(events, DIVORCE_TOKENS), "_normalised_name"]
    )
    marriage_events = events.loc[_has_event_matching(events, MARRIAGE_TOKENS)]
    marriage_count = marriage_events["_normalised_name"].value_counts()
    married_people = set(marriage_count.index)
    multi_marriage_people = set(marriage_count[marriage_count >= 2].index)

    death_events = events.loc[
        _has_event_matching(events, DEATH_TOKENS) & events["_age"].between(0, 120)
    ]
    died_young = set(death_events.loc[
        death_events["_age"] < DIED_YOUNG_THRESHOLD, "_normalised_name"
    ])
    lived_long = set(death_events.loc[
        death_events["_age"] >= LONG_LIFE_THRESHOLD, "_normalised_name"
    ])

    stats = {
        "event_divorced_positives": len(divorce_people),
        "event_married_positives": len(married_people),
        "event_multi_marriage_positives": len(multi_marriage_people),
        "event_died_young_positives": len(died_young),
        "event_lived_long_positives": len(lived_long),
        "rows_written": 0,
        "rows_tagged": 0,
    }

    # Rewrite persons CSV with appended event tags
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with persons_csv.open("r", encoding="utf-8", newline="") as fin, \
         output_csv.open("w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("persons CSV has no header")
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            stats["rows_written"] += 1
            normalised = _normalise_name(row.get("name", ""))
            tags_to_add: list[str] = []
            if normalised in divorce_people:
                tags_to_add.append("event_divorced")
            if normalised in married_people:
                tags_to_add.append("event_married")
            if normalised in multi_marriage_people:
                tags_to_add.append("event_multi_marriage")
            if normalised in died_young:
                tags_to_add.append("event_died_young")
            if normalised in lived_long:
                tags_to_add.append("event_lived_long")
            if tags_to_add:
                cats = (row.get("categories") or "").strip()
                merged = cats + (";" if cats else "") + ";".join(tags_to_add)
                row["categories"] = merged
                stats["rows_tagged"] += 1
            writer.writerow(row)

    return stats


# ---------- Regression target derivation ----------

def derive_regression_targets(
    persons_csv: Path,
    events_csv: Path,
    output_csv: Path,
) -> dict[str, int]:
    """Per-person regression targets:
      - age_first_marriage  (years; NaN if no marriage event known)
      - age_at_death        (years; NaN if no death event)
      - total_event_count   (int)

    NaN values are emitted as empty strings so the downstream regressor
    can filter rows with missing target while still keeping the row
    in the corpus for other target types.
    """
    birth_years = _build_birth_year_map(persons_csv)
    events = pd.read_csv(events_csv, low_memory=False)
    events["_normalised_name"] = events["name"].fillna("").astype(str).str.strip().str.lower()
    events["_birth_year"] = events["_normalised_name"].map(birth_years)
    events["_event_year"] = pd.to_numeric(events["event_year"], errors="coerce")
    events["_age"] = events["_event_year"] - events["_birth_year"]

    # First marriage age per person
    marriage_events = events.loc[
        _has_event_matching(events, MARRIAGE_TOKENS) & events["_age"].between(0, 100)
    ]
    age_first_marriage = (
        marriage_events.groupby("_normalised_name")["_age"].min()
    )

    # Age at death per person (use max — earliest non-death tag with
    # "Death" misclassifies if a person has both "Death of Father" 1971
    # and "Death by Disease" 2000; we take max as a proxy for the person's
    # own death, but tag-filter to first-person death events later).
    own_death_mask = events["event_root"].fillna("").str.lower().str.startswith("death")
    own_deaths = events.loc[
        own_death_mask & events["_age"].between(10, 120)
    ]
    age_at_death = own_deaths.groupby("_normalised_name")["_age"].max()

    # Total events per person
    total_events = events.groupby("_normalised_name").size()

    # Build the union of names from all targets
    all_names = set(age_first_marriage.index) | set(age_at_death.index) | set(total_events.index)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    stats = {"rows_written": 0}
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "age_first_marriage", "age_at_death", "total_event_count",
        ])
        writer.writeheader()
        for name in sorted(all_names):
            writer.writerow({
                "name": name,
                "age_first_marriage": (
                    f"{age_first_marriage[name]:.1f}"
                    if name in age_first_marriage.index else ""
                ),
                "age_at_death": (
                    f"{age_at_death[name]:.1f}"
                    if name in age_at_death.index else ""
                ),
                "total_event_count": (
                    str(int(total_events[name]))
                    if name in total_events.index else ""
                ),
            })
            stats["rows_written"] += 1
    return stats


# ---------- Multi-class target derivation ----------

def derive_multiclass_vocation(
    persons_csv: Path,
    output_csv: Path,
) -> dict[str, int]:
    """For each person, determine the primary vocation root by counting
    how many `Vocation : <Root> : *` tags appear in their categories
    string. Emit (name, vocation_root) pairs; rows with no clear
    vocation root are written with label "other".

    Multi-class is one-of-K — each row has exactly one label so the
    classifier can be trained as a softmax.
    """
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    stats = {
        "rows_total": 0,
        "rows_with_vocation": 0,
        "rows_other": 0,
    }
    label_counts: Counter[str] = Counter()

    with persons_csv.open("r", encoding="utf-8", newline="") as fin, \
         output_csv.open("w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=["name", "vocation_root"])
        writer.writeheader()

        for row in reader:
            stats["rows_total"] += 1
            cats_lower = (row.get("categories") or "").lower()
            # Score each root by substring count
            scores = {
                root: cats_lower.count(root)
                for root in VOCATION_ROOTS
            }
            # Tie-break: highest count wins; among zeros, label "other"
            top_root, top_score = max(scores.items(), key=lambda kv: kv[1])
            if top_score == 0:
                label = "other"
                stats["rows_other"] += 1
            else:
                label = top_root
                stats["rows_with_vocation"] += 1
            label_counts[label] += 1
            writer.writerow({
                "name": row.get("name", ""),
                "vocation_root": label,
            })

    stats["label_distribution"] = dict(label_counts)
    return stats


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.derive_event_targets",
        description=(
            "Derive event-based ML targets from events_all.csv + persons "
            "corpus. Produces three outputs: augmented persons CSV, "
            "regression-targets CSV, multi-class vocation CSV."
        ),
    )
    parser.add_argument(
        "--persons-csv", type=Path,
        default=Path("data/astro_databank/merged_with_lunar.csv"),
        help="Source persons CSV. Must have name + date_of_birth + categories.",
    )
    parser.add_argument(
        "--events-csv", type=Path,
        default=Path("data/astro_databank/events_all.csv"),
        help="Source events CSV from app.medini.etl.events_extractor + lapaas_importer.",
    )
    parser.add_argument(
        "--output-persons", type=Path,
        default=Path("data/astro_databank/merged_with_events.csv"),
        help="Where to write the persons CSV with new event-derived tags.",
    )
    parser.add_argument(
        "--output-regression", type=Path,
        default=Path("data/astro_databank/event_regression_targets.csv"),
        help="Where to write per-person regression target CSV.",
    )
    parser.add_argument(
        "--output-multiclass", type=Path,
        default=Path("data/astro_databank/event_vocation_multiclass.csv"),
        help="Where to write multi-class vocation labels.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    logger.info("Step 1: deriving binary event tags...")
    binary_stats = derive_binary_event_tags(
        args.persons_csv, args.events_csv, args.output_persons,
    )
    logger.info("Binary stats: %s", binary_stats)

    logger.info("Step 2: deriving regression targets...")
    reg_stats = derive_regression_targets(
        args.persons_csv, args.events_csv, args.output_regression,
    )
    logger.info("Regression stats: %s", reg_stats)

    logger.info("Step 3: deriving multi-class vocation labels...")
    mc_stats = derive_multiclass_vocation(
        args.output_persons, args.output_multiclass,
    )
    logger.info("Multi-class stats: %s", mc_stats)

    return 0


if __name__ == "__main__":
    sys.exit(main())
