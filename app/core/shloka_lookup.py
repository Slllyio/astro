"""Shloka rule lookup — query the harvested classical rule corpus.

The Translation Engine (``app/core/dkp_translation.py``) carries 27
hand-curated TranslationRecords with full 5-layer translation
(shloka → ancient → DKP shift → modern → invariant). That's the
CANONICAL doctrinal interpretation tier.

This module is the SUPPLEMENTARY layer: 2,566+ rule-statement
sentences harvested from foundational classical sources
(``app/medini/etl/harvest_shlokas.py``):

  * Brihat Jataka (Varahamihira)
  * Phaladeepika (Mantreshvara)
  * Saravali (Kalyana Varma)
  * Crux of Vedic Astrology (Sanjay Rath)
  * Advance Techniques (KN Rao)
  * Studies in Jaimini Astrology (Raman)
  * Jaimini Sutras
  * Ashtakavarga (Patel)
  * Frawley's Astrology of the Seers
  * etc.

Each rule has: source, chapter, condition, outcome, topics (auto-tagged
domain + planet labels), raw_text (provenance).

## When to use the Translation Engine vs this module

  * Translation Engine: when you have a SPECIFIC yoga or bhava-placement
    and want the desh-kaal-paristhiti-corrected modern reading with
    full 5-layer interpretive depth.

  * shloka_lookup: when you want to BROWSE classical rules touching a
    domain or planet for evidence-aggregation, citation, or to surface
    additional doctrinal context the curated 27 records don't cover.

## What this is NOT

  * Not validated shlokas. The harvester is permissive; many rules are
    chapter summaries or commentary not actual canonical shlokas.
  * Not deduplicated across sources. Two books may cite the same BPHS
    rule with slightly different wording; you get both rows.
  * Not OCR-clean. Some sentences carry artifacts. Use ``raw_text`` as
    the source-of-truth and consider the condition/outcome split a
    hint not a guarantee.

For canonical-grade translation, route through the Translation Engine.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ShlokaRule:
    """One harvested classical rule statement."""
    source: str
    chapter: str
    rule_id: int
    condition: str
    outcome: str
    topics: tuple[str, ...]
    raw_text: str


_RULES: list[ShlokaRule] = []
_RULES_BY_TOPIC: dict[str, list[ShlokaRule]] = {}
_RULES_BY_SOURCE: dict[str, list[ShlokaRule]] = {}


def _load_corpus() -> None:
    """Load the harvested shloka corpus from JSONL. Idempotent."""
    global _RULES, _RULES_BY_TOPIC, _RULES_BY_SOURCE
    _RULES = []
    _RULES_BY_TOPIC = {}
    _RULES_BY_SOURCE = {}
    corpus_path = Path("data/knowledge_library/classical_shloka_rules.jsonl")
    if not corpus_path.exists():
        return
    try:
        with corpus_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    rule = ShlokaRule(
                        source=rec.get("source", "unknown"),
                        chapter=rec.get("chapter", ""),
                        rule_id=int(rec.get("rule_id", 0)),
                        condition=rec.get("condition", ""),
                        outcome=rec.get("outcome", ""),
                        topics=tuple(rec.get("topics", [])),
                        raw_text=rec.get("raw_text", ""),
                    )
                    _RULES.append(rule)
                    _RULES_BY_SOURCE.setdefault(rule.source, []).append(rule)
                    for topic in rule.topics:
                        _RULES_BY_TOPIC.setdefault(topic, []).append(rule)
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
    except OSError as exc:
        logger.warning("Could not load shloka corpus: %s", exc)


_load_corpus()


# ─── Public API ─────────────────────────────────────────────────────


def corpus_size() -> int:
    """Number of shloka rules currently loaded."""
    return len(_RULES)


def is_corpus_loaded() -> bool:
    """True iff at least one shloka rule is in the registry."""
    return len(_RULES) > 0


def sources_present() -> tuple[str, ...]:
    """Distinct sources with at least one harvested rule."""
    return tuple(sorted(_RULES_BY_SOURCE.keys()))


def topics_present() -> tuple[str, ...]:
    """Distinct topic tags across the corpus."""
    return tuple(sorted(_RULES_BY_TOPIC.keys()))


def rules_for_topic(topic: str, limit: int = 50) -> tuple[ShlokaRule, ...]:
    """Return rules tagged with the given topic.

    Topics are auto-tagged by the harvester from domain keywords
    (marriage, wealth, career, etc.) + planet names (Sun, Moon, ...).
    Returns at most ``limit`` rules.
    """
    matches = _RULES_BY_TOPIC.get(topic, [])
    return tuple(matches[:limit])


def rules_for_source(source: str, limit: int = 50) -> tuple[ShlokaRule, ...]:
    """Return rules from the given source (e.g. 'brihat_jataka')."""
    matches = _RULES_BY_SOURCE.get(source, [])
    return tuple(matches[:limit])


def rules_mentioning(*needles: str, limit: int = 50) -> tuple[ShlokaRule, ...]:
    """Return rules whose raw_text mentions ALL given substrings (AND).

    Case-insensitive. Useful for ad-hoc queries like
    ``rules_mentioning("Saturn", "7th house")``.
    """
    if not _RULES:
        return ()
    needles_lower = [n.lower() for n in needles]
    matches = [
        r for r in _RULES
        if all(n in r.raw_text.lower() for n in needles_lower)
    ]
    return tuple(matches[:limit])


def rules_for_domain_and_planet(
    domain: str, planet: str, limit: int = 20,
) -> tuple[ShlokaRule, ...]:
    """Convenience: rules tagged BOTH a domain AND a planet.

    Example:
        rules_for_domain_and_planet("marriage", "Venus")
    """
    domain_set = set(_RULES_BY_TOPIC.get(domain, []))
    planet_set = set(_RULES_BY_TOPIC.get(planet, []))
    both = domain_set & planet_set
    # Sort by source authority (foundational sources first)
    authority = {
        "brihat_jataka": 1, "phaladeepika": 2, "saravali": 3,
        "jaimini_sutras": 4, "brihat_samhita_iyer": 5,
        "crux_of_vedic_astrology_rath": 6,
        "studies_jaimini_raman": 7, "advance_techniques_kn_rao": 8,
        "ashtakavarga_patel": 9,
        "fundamentals_vedic_astrology": 10,
        "astrology_seers_frawley": 11,
    }
    sorted_rules = sorted(
        both, key=lambda r: (authority.get(r.source, 99), r.rule_id),
    )
    return tuple(sorted_rules[:limit])


def reload_corpus() -> int:
    """Reload the corpus from disk."""
    _load_corpus()
    return len(_RULES)
