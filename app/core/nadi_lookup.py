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


# ─── Registry — currently empty ─────────────────────────────────────


# The registry maps NadiPatternKey → NadiPatternMatch. Empty for now;
# populated when a digitised corpus arrives. Loaders would read from
# data/nadi_corpora/*.jsonl files into this dict at module import.
_NADI_REGISTRY: Final[Mapping[NadiPatternKey, NadiPatternMatch]] = {}


# Status string returned for every query until a corpus is loaded.
_EMPTY_CORPUS_STATUS: Final[str] = (
    "No digitised Nadi corpus is loaded. This module is a scaffold for "
    "when one exists. Public Nadi-corpus datasets are essentially "
    "non-existent; the classical tradition keeps palm-leaf manuscripts "
    "closely held. Use the framework's BPHS+Phaladeepika+Mansagari "
    "yoga library + convergence engine for actionable predictions."
)


# ─── Public API ─────────────────────────────────────────────────────


def lookup_nadi_pattern(key: NadiPatternKey) -> NadiPatternMatch:
    """Look up a Nadi leaf matching the given pattern key.

    Always returns a NadiPatternMatch — never raises. When no corpus is
    loaded (current state), returns found=False with a helpful
    corpus_status string.

    Args:
        key: NadiPatternKey describing the chart pattern to match.

    Returns:
        NadiPatternMatch with found=True only when a real leaf matched.
    """
    # Try exact match first
    if key in _NADI_REGISTRY:
        return _NADI_REGISTRY[key]
    # Try less-specific keys (drop optional refinements one by one)
    fallback_key = NadiPatternKey(
        asc_sign=key.asc_sign,
        moon_sign=key.moon_sign,
        moon_nakshatra=key.moon_nakshatra,
        atmakaraka=key.atmakaraka,
        md_lord=key.md_lord,
        # All refinements dropped
    )
    if fallback_key in _NADI_REGISTRY:
        match = _NADI_REGISTRY[fallback_key]
        # Mark as lower-specificity match
        return NadiPatternMatch(
            found=match.found, reading=match.reading,
            tradition=match.tradition,
            key_specificity=0,
            corpus_status="matched at base specificity (no refinements)",
        )
    return NadiPatternMatch(
        found=False, reading=None, tradition=None,
        key_specificity=0, corpus_status=_EMPTY_CORPUS_STATUS,
    )


def registry_size() -> int:
    """Number of Nadi leaves currently loaded. Useful for status display."""
    return len(_NADI_REGISTRY)


def is_corpus_loaded() -> bool:
    """True iff at least one Nadi leaf is in the registry."""
    return len(_NADI_REGISTRY) > 0
