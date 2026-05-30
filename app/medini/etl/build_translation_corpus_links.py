"""Build corpus-passage links for the Doctrine Translation Engine.

Phase E of the Translation Engine work: each ``TranslationRecord`` in
``app.core.dkp_translation`` carries an empty
``corpus_passage_ids: tuple[str, ...]`` field. This ETL populates it by
matching the record's ``classical_references`` (e.g., "BPHS Ch.36") and
``domain`` against the 918-artefact knowledge_library manifest.

## Matching heuristic (deterministic, no embeddings)

For each record:

1. **Source match** — split classical_references on whitespace, extract
   the source root (e.g., "BPHS" → match manifest rows with
   ``source='bphs'``; "Phaladeepika" → ``source='phaladeepika'`` OR
   ``source='phaladeepika_dli'``).
2. **Domain → topic-tag match** — map our domain to the corpus topic
   taxonomy:
     - kinship       → predictive.marriage_timing, predictive.children
     - career_wealth → predictive.career_timing, predictive.wealth
     - dharma        → primitives.planets (proxy — guru/dharma broad),
                       strength_bala.shadbala (Jupiter strength)
     - health        → predictive.health_disease, predictive.death_timing
3. **Score per artefact** = (2 if source-match) + (1 if any topic-match)
   + (1 if record.key term appears in artefact title).
4. **Cap** to top-N per record (default 8) by score descending,
   tie-broken by source priority (classical texts > modern commentary
   > YouTube transcripts).

## Output

A JSON sidecar at ``app/core/dkp_translation_corpus_links.json``:

  {"<record.key>": ["<id1>", "<id2>", ...], ...}

The Translation Engine loads this at module import time (lazy, cached)
and exposes the IDs as ``record.corpus_passage_ids``. Falling back to
empty tuple if the sidecar is missing.

Run:
    python -m app.medini.etl.build_translation_corpus_links
    python -m app.medini.etl.build_translation_corpus_links --top-n 10
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final, Mapping

import pandas as pd

from app.core.dkp_translation import (
    Domain, TranslationRecord, all_translations,
)

logger = logging.getLogger(__name__)

DEFAULT_MANIFEST: Final = Path("data/knowledge_library/manifest.parquet")
DEFAULT_OUTPUT: Final = Path("app/core/dkp_translation_corpus_links.json")


# Map our Translation Engine source-references → manifest source names.
# Keys are lowercase substrings to search in classical_references.
_SOURCE_MAP: Final[Mapping[str, tuple[str, ...]]] = {
    "bphs": ("bphs",),
    "parashara": ("bphs",),
    "phaladeepika": ("phaladeepika", "phaladeepika_dli"),
    "saravali": ("saravali",),
    "jaimini": ("brihat_jataka",),  # closest classical analog
    "brihat jataka": ("brihat_jataka",),
    "hora sara": ("hora_sara_santhanam",),
    "raman": ("hindu_predictive_astrology_raman", "varshaphal_raman"),
    "brihat samhita": ("brihat_samhita_iyer",),
    "navamsa": ("navamsa_patel",),
    "ashtakavarga": ("ashtakavarga_patel",),
    # Modern but doctrinally adjacent
    "nadi": ("vedic_occultism_behari",),
    "mansagari": (),  # not in corpus directly; matches by topic only
}


# Domain → manifest topic-tag set
_DOMAIN_TOPICS: Final[Mapping[str, frozenset[str]]] = {
    Domain.KINSHIP: frozenset({
        "predictive.marriage_timing", "predictive.children",
    }),
    Domain.CAREER_WEALTH: frozenset({
        "predictive.career_timing", "predictive.wealth",
    }),
    Domain.DHARMA: frozenset({
        "strength_bala.shadbala",  # Jupiter strength proxy
        "primitives.planets",       # guru/dharma references
        "predictive.travel",        # 9H/12H foreign travel
    }),
    Domain.HEALTH: frozenset({
        "predictive.health_disease", "predictive.death_timing",
    }),
}


# Source priority for tie-breaking (lower = higher priority).
_SOURCE_PRIORITY: Final[Mapping[str, int]] = {
    "bphs": 0,
    "phaladeepika": 1,
    "phaladeepika_dli": 1,
    "saravali": 1,
    "brihat_jataka": 1,
    "hora_sara_santhanam": 2,
    "brihat_samhita_iyer": 2,
    "hindu_predictive_astrology_raman": 3,
    "varshaphal_raman": 3,
    "ashtakavarga_patel": 3,
    "navamsa_patel": 3,
    "vedic_occultism_behari": 4,
}
_DEFAULT_PRIORITY = 9


def _extract_source_matches(
    classical_refs: tuple[str, ...],
) -> set[str]:
    """Return the set of manifest source-names this record's refs point to."""
    found: set[str] = set()
    for ref in classical_refs:
        ref_lower = ref.lower()
        for key, sources in _SOURCE_MAP.items():
            if key in ref_lower:
                found.update(sources)
    return found


def _key_terms(record_key: str) -> tuple[str, ...]:
    """Extract lower-cased search terms from a record key.

    "Mangal Dosha" → ("mangal", "dosha")
    "bhava_8_planet_Saturn" → ("saturn", "8")
    "Saraswati_career" → ("saraswati",)
    """
    # Drop trailing _domain suffix used to disambiguate records
    cleaned = (
        record_key.replace("bhava_", "")
                  .replace("_planet_", " ")
                  .replace("_or_", " ")
                  .replace("_", " ")
    )
    parts = cleaned.lower().split()
    # Keep meaningful tokens (planet names, doctrine words)
    return tuple(p for p in parts if len(p) >= 3 and p not in {
        "the", "and", "with", "career", "dharma", "health", "kinship",
        "for", "from",
    })


def _score_artefact(
    record: TranslationRecord, source: str, topics: list[str], title: str,
    source_matches: set[str], domain_topics: frozenset[str],
    key_terms: tuple[str, ...],
) -> int:
    """Compute the match score for one (record, artefact) pair."""
    score = 0
    if source in source_matches:
        score += 2
    if any(t in domain_topics for t in topics):
        score += 1
    title_lower = title.lower() if title else ""
    if any(term in title_lower for term in key_terms):
        score += 1
    return score


def _rank_and_cap(
    candidates: list[tuple[int, int, str]], top_n: int,
) -> list[str]:
    """Sort candidates by (score desc, priority asc) and return top-N IDs."""
    # candidates = [(score, source_priority, id), ...]
    candidates.sort(key=lambda t: (-t[0], t[1]))
    return [c[2] for c in candidates[:top_n] if c[0] > 0]


def composite_key(record: TranslationRecord) -> str:
    """Composite sidecar key — disambiguates same-yoga-different-domain records.

    Yogas like "Vipareeta Raja" and "Saraswati" appear in multiple
    domains; the corpus matches differ per domain because topic tags
    differ. Using ``"{key}::{domain}"`` keeps both lists separately
    addressable. Engine lookup uses the same composite key.
    """
    return f"{record.key}::{record.domain}"


def build_links(
    manifest: pd.DataFrame, records: tuple[TranslationRecord, ...],
    top_n: int = 8,
) -> dict[str, list[str]]:
    """Build the corpus_passage_ids dict keyed by composite_key(record)."""
    out: dict[str, list[str]] = {}
    for record in records:
        source_matches = _extract_source_matches(record.classical_references)
        domain_topics = _DOMAIN_TOPICS.get(record.domain, frozenset())
        key_terms = _key_terms(record.key)

        candidates: list[tuple[int, int, str]] = []
        for _, row in manifest.iterrows():
            topics_list = list(row["topics"]) if row["topics"] is not None else []
            score = _score_artefact(
                record,
                source=str(row["source"]),
                topics=topics_list,
                title=str(row["title"]),
                source_matches=source_matches,
                domain_topics=domain_topics,
                key_terms=key_terms,
            )
            if score > 0:
                priority = _SOURCE_PRIORITY.get(str(row["source"]), _DEFAULT_PRIORITY)
                candidates.append((score, priority, str(row["id"])))

        out[composite_key(record)] = _rank_and_cap(candidates, top_n)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--top-n", type=int, default=8)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    manifest = pd.read_parquet(args.manifest)
    records = all_translations()
    logger.info("Loaded %d artefacts and %d translation records",
                len(manifest), len(records))

    links = build_links(manifest, records, top_n=args.top_n)
    n_with_matches = sum(1 for v in links.values() if v)
    avg_matches = (
        sum(len(v) for v in links.values()) / max(len(links), 1)
    )
    logger.info("Matched %d / %d records (avg %.1f passages per record)",
                n_with_matches, len(links), avg_matches)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(links, indent=2, sort_keys=True), encoding="utf-8",
    )
    logger.info("Wrote sidecar to %s (%d bytes)",
                args.output, args.output.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
