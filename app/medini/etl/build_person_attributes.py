"""Enrich the canonical store with structured person attributes mined from the
holos / VedAstro `categories` field.

The holos corpus ships a semicolon-separated `categories` string per person in the
Astro-Databank `Root : Field : Detail` grammar, e.g.::

    Vocation : Entertain/Music : Vocalist;Notable : Famous : Top 5% of Profession;
    Lifestyle : Financial : Rags to riches;Family : Relationship : Marriage - Very happy

That is a goldmine of ML *labels* (vocation, fame, finances, health, relationships)
that `build_silver_from_corpora` deliberately dropped from the relational core. This
builder parses it into two tables keyed by the same `person_id`:

  person_attributes.parquet  long: (person_id, root, field, detail, source) — one row
                             per structured tag; the queryable source of truth.
  person_labels.parquet      compact: one row per person with derived, objectively-
                             defined labels (primary_vocation + presence flags) for
                             stratified analysis and multiclass/binary training.

Wikipedia-category noise ("Birthplace …", "1947 births", "Pages with …") is dropped
by whitelisting the real Astro-Databank attribute roots.

CLI:
    python -m app.medini.etl.build_person_attributes
"""
from __future__ import annotations

import argparse
import csv
import logging
from collections import Counter
from pathlib import Path
from typing import Final

import pandas as pd

from app.medini.etl.build_silver_from_corpora import (
    DEFAULT_DATA_DIR,
    DEFAULT_RAW_DIR,
    _decimal_hour,
)
from app.core.ephemeris_engine import calculate_jd

logger = logging.getLogger(__name__)
csv.field_size_limit(10 ** 7)

# Corpora whose raw.csv carries a usable categories string + person_id prefix.
_CORPORA: Final = (("raw_holos.csv", "holos", "HO"), ("raw.csv", "vedastro", "VA"))

# The genuine Astro-Databank attribute roots (everything else in the field is
# Wikipedia-category noise: birthplaces, "NNNN births", maintenance categories).
_ATTR_ROOTS: Final = frozenset({
    "Vocation", "Family", "Notable", "Personal", "Traits",
    "Lifestyle", "Diagnoses", "Passions", "Mundane", "Mind", "Personality",
})


def _person_id(prefix: str, row: dict) -> str | None:
    """Recompute the canonical person_id for a raw row (matches persons.parquet)."""
    date = (row.get("date_of_birth") or "").strip()
    lat, lon, tz = row.get("latitude"), row.get("longitude"), row.get("tz_offset")
    if not date or not lat or not lon or tz in (None, ""):
        return None
    try:
        y, m, d = (int(x) for x in date.split("-"))
        if not (1 <= y <= 2100):
            return None
        jd = calculate_jd(y, m, d, _decimal_hour(row.get("time_of_birth")), float(tz))
    except (ValueError, TypeError):
        return None
    return f"{prefix}:{jd:.4f}"


def _parse_tags(categories: str) -> list[tuple[str, str, str]]:
    """Split a categories string into (root, field, detail) for whitelisted roots."""
    out: list[tuple[str, str, str]] = []
    for tag in (categories or "").split(";"):
        parts = [p.strip() for p in tag.split(":")]
        if len(parts) < 2 or parts[0] not in _ATTR_ROOTS:
            continue
        root = parts[0]
        field = parts[1]
        detail = parts[2] if len(parts) >= 3 else ""
        out.append((root, field, detail))
    return out


def _derive_labels(tags: list[tuple[str, str, str]]) -> dict:
    """Compact, objectively-defined labels from a person's tags."""
    voc = Counter(f for r, f, _ in tags if r == "Vocation" and f)
    fields = {(r, f) for r, f, _ in tags}
    details = " ; ".join(d for *_, d in tags).lower()
    return {
        "primary_vocation": (voc.most_common(1)[0][0] if voc else None),
        "n_vocation_fields": len(voc),
        "is_famous": ("Notable", "Famous") in fields,
        "has_award": ("Notable", "Awards") in fields,
        "has_major_disease": ("Diagnoses", "Major Diseases") in fields,
        "has_psychological_dx": ("Diagnoses", "Psychological") in fields,
        "has_marriage": ("Family", "Relationship") in fields and "marriage" in details,
        "financial_gain": "gain" in details or "riches" in details or "success in field" in details,
    }


def build(data_dir: Path = DEFAULT_DATA_DIR, raw_dir: Path = DEFAULT_RAW_DIR) -> dict:
    persons = set(pd.read_parquet(data_dir / "persons.parquet", columns=["person_id"])["person_id"])

    attr_rows: list[dict] = []
    label_rows: list[dict] = []
    seen_persons: set[str] = set()

    for filename, source, prefix in _CORPORA:
        path = raw_dir / filename
        if not path.exists():
            continue
        for row in csv.DictReader(path.open(encoding="utf-8")):
            pid = _person_id(prefix, row)
            if pid is None or pid not in persons or pid in seen_persons:
                continue
            tags = _parse_tags(row.get("categories") or "")
            if not tags:
                continue
            seen_persons.add(pid)
            for root, field, detail in tags:
                attr_rows.append({
                    "person_id": pid, "root": root, "field": field,
                    "detail": detail, "source": source,
                })
            label_rows.append({"person_id": pid, "source": source, **_derive_labels(tags)})

    attrs = pd.DataFrame(attr_rows, columns=["person_id", "root", "field", "detail", "source"])
    labels = pd.DataFrame(label_rows)
    attrs.to_parquet(data_dir / "person_attributes.parquet", index=False)
    labels.to_parquet(data_dir / "person_labels.parquet", index=False)

    stats = {
        "persons_with_attributes": len(seen_persons),
        "attribute_rows": len(attrs),
        "top_vocations": labels["primary_vocation"].value_counts().head(8).to_dict() if len(labels) else {},
        "famous": int(labels["is_famous"].sum()) if len(labels) else 0,
    }
    logger.info("wrote person_attributes (%d rows) + person_labels (%d persons)", len(attrs), len(labels))
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.medini.etl.build_person_attributes")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    print(build(args.data_dir, args.raw_dir))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
