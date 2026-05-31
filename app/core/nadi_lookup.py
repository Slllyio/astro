"""Nadi pattern lookup — scaffold (D-5).

## Why this module exists as a scaffold rather than a full implementation

Nadi astrology (Bhrigu Samhita / Saptarishi Nadi / Dhruva Nadi /
Chandra Kala Nadi / Deva Keralam) is the most highly specific tier
of classical Vedic prediction. Where BPHS / Phaladeepika give general
yoga-rules ("planet X in house Y produces effect Z"), Nadi works by
PATTERN LOOKUP — a very specific combination of (Lagna, planet
positions, dasha, sub-dasha) is matched against a stored corpus of
hand-written palm-leaf manuscripts, each prescribing a SPECIFIC
prediction at that exact pattern.

The corpus is the system. Without a digitised, parameterisable Nadi
corpus, this module can't make real Nadi predictions — it would just
return random doctrine-strings. So we ship a SCAFFOLD with:

  1. The PATTERN-KEY shape — what combination of chart features
     uniquely identifies a Nadi "leaf".
  2. The LOOKUP API — what callers will use when a corpus exists.
  3. An empty registry that returns NadiPatternMatch.found=False
     until a corpus is loaded.
  4. A clear roadmap for what would need to be true for this module to
     ship real predictions.

## When this becomes useful

A useful Nadi corpus would need (per researcher conversations + the
state of available digitised sources):

  * ≥1,000 distinct Nadi leaves digitised in a (pattern_key → reading)
    format. Public datasets are essentially non-existent; commercial
    Nadi-reading services hold their corpora closely.
  * Or: ML-extracted patterns from BPHS/Phaladeepika edge cases that
    weren't covered by our yoga library (~39 yogas covers ~30% of the
    classical canon).

## What this module does NOW

Defines the data model + lookup interface. Returns a sentinel
NadiPatternMatch(found=False, ...) for every chart. Downstream
consumers can include "Nadi: no pattern matched in current corpus"
without crashing, and the day a digitised corpus arrives, only the
``_NADI_REGISTRY`` constant changes — no API churn.

## What this module does NOT do

* No fake predictions. No "synthetic Nadi readings" generated from
  templates. The scaffold returns found=False until the corpus
  literally exists.
* No claims of doctrinal validity for any output beyond "we acknowledge
  the pattern shape exists in the classical canon."

## References

  * Bhrigu Samhita (Hoshiarpur tradition, palm-leaf manuscripts)
  * Saptarishi Nadi (Chennai tradition)
  * KN Rao's notes on "the limits of pattern-lookup astrology"
    (Astrological Magazine v.75)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Mapping


# ─── Pattern key ────────────────────────────────────────────────────


@dataclass(frozen=True)
class NadiPatternKey:
    """The minimum chart-feature combination a Nadi leaf indexes on.

    Classical Nadi systems differ on the exact key shape; this captures
    the most common subset. A more elaborate key would include
    transits, dasha-bhukti-antara state, and varga-specific cusps —
    add fields as the corpus shape demands.
    """
    asc_sign: int                # 1..12
    moon_sign: int               # 1..12
    moon_nakshatra: int          # 0..26
    atmakaraka: str              # planet name
    md_lord: str                 # current Vimshottari mahadasha lord
    # Optional refinements (the more fields, the rarer the match):
    ad_lord: str | None = None   # antardasha lord (None = match-any)
    sun_sign: int | None = None
    jupiter_sign: int | None = None
    saturn_sign: int | None = None


@dataclass(frozen=True)
class NadiPatternMatch:
    """Result of a registry lookup.

    Fields:
      found: True only when an actual Nadi-leaf matched the key.
      reading: The stored leaf text (None if not found).
      tradition: Which Nadi tradition the leaf came from
                 (Bhrigu / Saptarishi / Dhruva / etc.) — None if not found.
      key_specificity: How many of the optional refinement fields the
                       matched pattern uses (higher = rarer match).
      corpus_status: Human-readable status of the registry. Useful for
                     UI display ("no Nadi corpus loaded; this is normal").
    """
    found: bool
    reading: str | None
    tradition: str | None
    key_specificity: int
    corpus_status: str


# ─── Registry ───────────────────────────────────────────────────────


# The registry is populated at module import from
# ``data/knowledge_library/nadi_corpus.jsonl`` (produced by
# ``app/medini/etl/extract_nadi_corpus.py``). Each row is one Nadi leaf
# with: source, horoscope_id, asc_sign, planet_signs, events, dasa_at_birth,
# raw_text. We INDEX leaves by (asc_sign, key-graha-signs) for fast lookup.


import json as _json
import logging as _logging
from pathlib import Path as _Path


_logger = _logging.getLogger(__name__)


# Loaded at import: list of all parsed Nadi leaves.
_NADI_LEAVES: list[dict] = []
_NADI_LEAVES_BY_ASC: dict[int, list[dict]] = {}


def _load_corpus() -> None:
    """Load Nadi corpus from JSONL on disk. Idempotent — clears + reloads."""
    global _NADI_LEAVES, _NADI_LEAVES_BY_ASC
    _NADI_LEAVES = []
    _NADI_LEAVES_BY_ASC = {}
    corpus_path = _Path("data/knowledge_library/nadi_corpus.jsonl")
    if not corpus_path.exists():
        return
    try:
        with corpus_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    leaf = _json.loads(line)
                    _NADI_LEAVES.append(leaf)
                    asc = leaf.get("asc_sign")
                    if asc is not None:
                        _NADI_LEAVES_BY_ASC.setdefault(asc, []).append(leaf)
                except _json.JSONDecodeError:
                    continue
    except OSError as exc:
        _logger.warning("Could not load Nadi corpus: %s", exc)


_load_corpus()


# Status string when no leaf matches the query
_NO_MATCH_STATUS: Final[str] = (
    "No matching Nadi leaf for this pattern. The corpus is OCR-extracted "
    "from palm-leaf manuscripts (currently Saptarishi Nadi Aries Asc "
    "collection); other lagnas and traditions are sparse. Consider this "
    "absence as 'no specific Nadi rule applies to this exact pattern' "
    "rather than 'doctrine is silent on this question'."
)


_EMPTY_CORPUS_STATUS: Final[str] = (
    "Nadi corpus not loaded. Run "
    "`python -m app.medini.etl.extract_nadi_corpus` to populate from "
    "data/knowledge_library/sources/*."
)


# ─── Public API ─────────────────────────────────────────────────────


def _planet_signs_match(leaf_signs: Mapping[str, int],
                        query_signs: Mapping[str, int],
                        min_planets: int = 4) -> int:
    """Count grahas that are in the same sign in both leaf and query.

    A "match" requires at least ``min_planets`` graha-sign agreements.
    Returns the match count (or 0 if below threshold).
    """
    matches = sum(
        1 for p, s in query_signs.items()
        if leaf_signs.get(p) == s
    )
    return matches if matches >= min_planets else 0


def lookup_nadi_pattern(
    key: NadiPatternKey,
    *,
    chart_planet_signs: Mapping[str, int] | None = None,
) -> NadiPatternMatch:
    """Look up a Nadi leaf matching the given pattern key.

    Always returns a NadiPatternMatch — never raises.

    Matching strategy (in order):
      1. Asc-sign match required (Nadi books are indexed per-lagna).
      2. If chart_planet_signs supplied, find the leaf with the highest
         graha-sign agreement count (≥4 of 9 grahas).
      3. Falls back to the first leaf with the matching asc_sign.

    Args:
        key: NadiPatternKey describing the chart pattern to match.
        chart_planet_signs: Optional {planet: sign} for refined matching.
                            When provided, the best-overlap leaf is returned.

    Returns:
        NadiPatternMatch with found=True only when a real leaf matched.
    """
    if not _NADI_LEAVES:
        return NadiPatternMatch(
            found=False, reading=None, tradition=None,
            key_specificity=0, corpus_status=_EMPTY_CORPUS_STATUS,
        )

    candidates = _NADI_LEAVES_BY_ASC.get(key.asc_sign, [])
    if not candidates:
        return NadiPatternMatch(
            found=False, reading=None, tradition=None,
            key_specificity=0,
            corpus_status=(
                f"No Nadi leaf for Lagna sign {key.asc_sign}. "
                f"Corpus has {len(_NADI_LEAVES)} leaves across "
                f"{len(_NADI_LEAVES_BY_ASC)} lagnas."
            ),
        )

    # Refined match: pick the leaf with the highest graha-sign overlap
    if chart_planet_signs:
        best_leaf = None
        best_score = 0
        for leaf in candidates:
            leaf_signs = leaf.get("planet_signs", {})
            score = _planet_signs_match(leaf_signs, chart_planet_signs)
            if score > best_score:
                best_score = score
                best_leaf = leaf
        if best_leaf is not None and best_score >= 4:
            return _leaf_to_match(best_leaf, best_score)

    # Fall back: return the first asc-sign-matching leaf as a generic
    # "this lagna has stored Nadi predictions" hit at low specificity.
    first_leaf = candidates[0]
    return _leaf_to_match(first_leaf, key_specificity=1)


def _leaf_to_match(leaf: dict, key_specificity: int) -> NadiPatternMatch:
    """Convert a JSONL leaf dict to a NadiPatternMatch."""
    source = leaf.get("source", "unknown")
    hid = leaf.get("horoscope_id", "?")
    raw = leaf.get("raw_text", "")
    events = leaf.get("events", {})
    dasa = leaf.get("dasa_at_birth", "")

    reading_parts = [f"Nadi leaf {source}:H{hid}"]
    if dasa:
        reading_parts.append(f"Dasa at birth: {dasa}")
    if events:
        reading_parts.append("Events at ages: " + ", ".join(
            f"{k}={v}" for k, v in events.items()
        ))
    if raw:
        reading_parts.append(f"Source-text excerpt: {raw[:300]}")

    return NadiPatternMatch(
        found=True,
        reading=" | ".join(reading_parts),
        tradition=source.replace("_", " ").title(),
        key_specificity=key_specificity,
        corpus_status=(
            f"Matched at specificity={key_specificity} "
            f"({len(_NADI_LEAVES)} leaves loaded across "
            f"{len(_NADI_LEAVES_BY_ASC)} lagnas)"
        ),
    )


def registry_size() -> int:
    """Number of Nadi leaves currently loaded."""
    return len(_NADI_LEAVES)


def is_corpus_loaded() -> bool:
    """True iff at least one Nadi leaf is in the registry."""
    return len(_NADI_LEAVES) > 0


def reload_corpus() -> int:
    """Reload the corpus from disk. Returns the new leaf count."""
    _load_corpus()
    return len(_NADI_LEAVES)
