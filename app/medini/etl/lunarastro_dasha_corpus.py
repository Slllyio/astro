"""Build a dasha-event corpus for the lunarastro 62k people.

Same shape as ``app/medini/data/dasha_event_corpus.parquet`` (per
(person, MD-window) row with binary ``event_<class>`` labels), but
built from the lunarastro kundli CSV instead of Astro-Databank.

Three-stage build:

1. **Event extraction.** Walk ``category == 'event'`` rows in the
   lunarastro kundli CSV. Each row's ``description`` is a
   comma-separated list of inline "EventPhrase YEAR (optional parens)"
   fragments. Regex out (phrase, year) tuples; map phrase to an event
   class using lunarastro_to_screening's ``_CLASS_DEFS`` patterns.
2. **MD-window generation.** For each (name_norm, birth_jd) in the
   lunarastro_natal parquet, compute the Vimshottari mahadasha
   sequence over a 100-year observation window using
   ``mahadasha_sequence`` from ``build_dasha_event_corpus``.
3. **Event-to-window join.** For each event (class, year), find which
   MD window the year falls in; set ``event_<class>=1`` for that row.

The output is joinable on (name_norm, dasha_lord, ...) with the
``lunarastro_natal_lord_houses.parquet`` for the mix scorer.

Usage:
    python -m app.medini.etl.lunarastro_dasha_corpus
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

from app.medini.etl.build_dasha_event_corpus import mahadasha_sequence
from app.medini.etl.lunarastro_to_screening import _CLASS_DEFS

logger = logging.getLogger(__name__)


# Event classes mirroring those in dasha_doctrine_score's _HOUSE_MAP.
# Each maps to one or more regex patterns to match against the event
# phrase. Patterns are precision-first — broader matches handled by
# class fallbacks below.
_EVENT_PATTERNS: dict[str, tuple[str, ...]] = {
    "marriage":         (r"\bmarriage\b", r"\bmarried\b", r"\bwedding\b",
                         r"\bwidowed\b"),
    "relationships":    (r"\brelationship\b", r"\bdivorc", r"\bseparation\b",
                         r"\bbreak\s?up\b", r"\bengagement\b"),
    "relationship":     (r"\brelationship\b", r"\bdivorc", r"\bseparation\b"),
    # Specific death subtypes (precision-first; processed BEFORE generic death)
    "death_by_disease": (r"\bdeath by\b.*(cancer|tuberculosis|illness|stroke|heart|disease)",),
    "death_of_father":  (r"\bdeath of father\b",),
    "death_of_mother":  (r"\bdeath of mother\b",),
    "death_of_mate":    (r"\bdeath of mate\b", r"\bdeath of spouse\b"),
    "death_of_child":   (r"\bdeath of child\b", r"\bdeath of son\b",
                         r"\bdeath of daughter\b"),
    "death_cause_unspecified": (r"^death\b(?!\s+of\s|\s+by\s)", r"\bdied\b"),
    "fame":             (r"\baward", r"\bnobel\b", r"\bnotable\b", r"\bprize\b",
                         r"\bhonou?r\b", r"\belection\b", r"\belected\b",
                         r"\bpublic office\b", r"\bcoronation\b"),
    "career":           (r"\bcareer\b", r"\bcareerpath\b", r"\bbusiness\b",
                         r"\bnew job\b", r"\bjob\b", r"\bcareer change\b",
                         r"\bpromotion\b"),
    "work":             (r"\bvocation\b", r"\bemployment\b", r"\bworked\b",
                         r"\bretired\b", r"\bretirement\b", r"\bnew job\b"),
    "personal":         (r"\bbirth\b", r"\bgraduation\b", r"\bmilestone\b",
                         r"\bmid-?life\b", r"\bspiritual\b", r"\bordained\b"),
    "family":           (r"\bchild\b", r"\bson born\b", r"\bdaughter born\b",
                         r"\bsiblings\b", r"\bfamily\b", r"\bparent\b"),
    "health":           (r"\bdiagnos", r"\billness\b", r"\bsurgery\b",
                         r"\bdisease\b", r"\bhospital", r"\binjur"),
    "finance":          (r"\bbankrupt", r"\bfortune\b", r"\binheritance\b",
                         r"\bfinancial\b", r"\binvestment\b", r"\bdebt\b"),
    "legal":            (r"\blawsuit\b", r"\barrest\b", r"\bconvict\b",
                         r"\bjail\b", r"\bprison\b", r"\btrial\b",
                         r"\bsentenc", r"\bindict"),
    "education":        (r"\bgraduat", r"\bdegree\b", r"\bphd\b", r"\bdoctorate\b",
                         r"\benrolled\b", r"\bschool start", r"\buniversit"),
}

# Pre-compile patterns for speed.
_COMPILED_EVENT_PATTERNS: dict[str, tuple[re.Pattern, ...]] = {
    cls: tuple(re.compile(p, re.IGNORECASE) for p in patterns)
    for cls, patterns in _EVENT_PATTERNS.items()
}

# Year detection — accept 4-digit years 1700-2030 (the lunarastro corpus
# spans roughly that range per the scout report).
_YEAR_RE = re.compile(r"\b(1[789]\d{2}|20[0-2]\d|2030)\b")


def _extract_events_from_description(desc: str) -> list[tuple[str, int]]:
    """Walk a comma-separated description and yield (class, year) tuples.

    Each comma-separated segment is treated as one event candidate. Year
    extracted via _YEAR_RE; if no year, the segment is skipped (no per-time
    attribution possible). The segment text is then matched against
    _EVENT_PATTERNS to assign an event class.

    A single segment may match MULTIPLE classes (e.g., "Marriage 1944"
    matches `marriage` AND `family`). All matches are emitted — the
    downstream join then sets event_<class>=1 for every matched class.
    """
    if not isinstance(desc, str) or not desc.strip():
        return []
    out: list[tuple[str, int]] = []
    segments = re.split(r",(?=\s*[A-Z])", desc)  # split on comma before capital
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        m = _YEAR_RE.search(seg)
        if not m:
            continue
        year = int(m.group(0))
        # phrase = text before the year (so subclasses like "Death of Father"
        # vs generic "Death by Disease" are discriminated)
        phrase = seg[:m.start()].strip().rstrip("()") or seg
        # Special-case: "death_cause_unspecified" only fires when "Death "
        # appears WITHOUT "of" or "by" qualifier; preserve order
        matched_classes: list[str] = []
        for cls, patterns in _COMPILED_EVENT_PATTERNS.items():
            for p in patterns:
                if p.search(phrase):
                    matched_classes.append(cls)
                    break  # one match per class is enough
        for cls in matched_classes:
            out.append((cls, year))
    return out


# --------------------------------------------------------------------------- #
# Corpus assembly                                                              #
# --------------------------------------------------------------------------- #

def _year_to_jd(year: int) -> float:
    """Approximate JD for July 1 of the given year (mid-year)."""
    return float(swe.julday(year, 7, 1, 12.0, swe.GREG_CAL))


def build_corpus(
    kundli_csv: Path,
    lunarastro_natal_path: Path,
    *,
    observation_years: int = 100,
) -> pd.DataFrame:
    """Build the lunarastro dasha-event corpus."""
    # 1. Load natal
    natal_df = pd.read_parquet(lunarastro_natal_path)
    natal_df = natal_df.drop_duplicates(subset=["name_norm", "birth_jd"])
    logger.info("loaded lunarastro_natal: %d people", len(natal_df))

    # 2. Extract events
    kundli = pd.read_csv(kundli_csv, low_memory=False)
    events_rows = kundli[kundli["category"] == "event"]
    logger.info("event-category rows: %d", len(events_rows))

    # Map each event row to extracted (class, year) tuples
    # Index by name_norm so the join is cheap
    name_lower = events_rows["name"].fillna("").astype(str).str.strip().str.lower()
    events_rows = events_rows.assign(name_norm=name_lower)

    extracted: dict[str, list[tuple[str, int]]] = {}
    for _, row in events_rows.iterrows():
        name = row["name_norm"]
        if not name:
            continue
        events = _extract_events_from_description(row.get("description", ""))
        if events:
            extracted.setdefault(name, []).extend(events)
    n_extracted_total = sum(len(v) for v in extracted.values())
    logger.info(
        "extracted %d (class, year) tuples across %d unique people",
        n_extracted_total, len(extracted),
    )

    # 3. Generate MD windows per person + label events
    event_classes = sorted(_EVENT_PATTERNS.keys())
    out_rows: list[dict] = []
    for _, person in natal_df.iterrows():
        name = person.get("name_norm")
        if not name:
            continue
        birth_jd = person.get("birth_jd")
        moon_lon = person.get("lon_moon")
        if pd.isna(birth_jd) or pd.isna(moon_lon):
            continue
        try:
            windows = mahadasha_sequence(
                float(moon_lon), float(birth_jd),
                observation_years=observation_years,
            )
        except Exception as e:
            logger.warning("MD sequence failed for %s: %s", name, e)
            continue
        person_events = extracted.get(name, [])
        # Convert event years to JDs for in-window lookup
        person_event_jds = [
            (cls, _year_to_jd(year)) for cls, year in person_events
            if 1700 < year < 2030
        ]
        for win in windows:
            row = {
                "name_norm": name,
                "birth_jd": float(birth_jd),
                "moon_longitude": float(moon_lon),
                "seq_idx": win.seq_idx,
                "dasha_lord": win.lord,
                "dasha_start_jd": win.start_jd,
                "dasha_end_jd": win.end_jd,
                "dasha_duration_years": win.duration_years,
            }
            n_events_in_window = 0
            for cls in event_classes:
                row[f"event_{cls}"] = 0
            for cls, event_jd in person_event_jds:
                if win.start_jd <= event_jd < win.end_jd:
                    row[f"event_{cls}"] = 1
                    n_events_in_window += 1
            row["n_events_in_window"] = n_events_in_window
            out_rows.append(row)
    out_df = pd.DataFrame(out_rows)
    logger.info(
        "wrote %d MD windows across %d people",
        len(out_df), out_df["name_norm"].nunique(),
    )
    # Event count per class
    for cls in event_classes:
        n = int(out_df[f"event_{cls}"].sum())
        logger.info("  event_%s: %d windows positive", cls, n)
    return out_df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.lunarastro_dasha_corpus",
    )
    parser.add_argument(
        "--kundli-csv", type=Path,
        default=Path("C:/Users/S.C.C/Downloads/Astro_Data 2/Astro_Data/output/kundlis.csv"),
    )
    parser.add_argument(
        "--lunarastro-natal", type=Path,
        default=Path("app/medini/data/lunarastro_natal.parquet"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("app/medini/data/lunarastro_dasha_corpus.parquet"),
    )
    parser.add_argument("--observation-years", type=int, default=100)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    out_df = build_corpus(
        args.kundli_csv, args.lunarastro_natal,
        observation_years=args.observation_years,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(args.output, index=False)
    print(f"wrote {args.output}: rows={len(out_df):,} "
          f"unique_people={out_df['name_norm'].nunique():,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
