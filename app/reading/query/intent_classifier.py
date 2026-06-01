"""Keyword-based intent classification for chart questions.

The classifier routes a free-form question to one of 6 intents:

- TIMING:  "when will...", "what year...", "in the future...", "by 2030"
- DOMAIN:  "career", "marriage", "health", "wealth", "children", "education"
- PLANET:  any planet name (Sun, Moon, Mars, Mercury, Jupiter, Venus,
           Saturn, Rahu, Ketu) — covers natal-position / dignity questions
- DASHA:   "mahadasha", "antardasha", "MD", "AD", "dasha period"
- YOGA:    "yoga", or a named yoga (Gajakesari, Lakshmi, Raja, ...)
- GENERIC: everything else

Returns an ``IntentClassification`` carrying the intent, a confidence
score (number of matched keywords / max possible), and the list of
matched entities (planet names, domain names, yoga names) for the
downstream finding selector to use.

This is intentionally a simple keyword classifier — no model, no
dependencies. The Spec Section 14 rationale: a classifier mistake is
non-fatal (the finding selector will gracefully degrade to GENERIC if
nothing matches), so paying for an ML model here is unwarranted.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final, Literal

Intent = Literal["TIMING", "DOMAIN", "PLANET", "DASHA", "YOGA", "GENERIC"]


# --------------------------------------------------------------------------- #
# Keyword sets                                                                 #
# --------------------------------------------------------------------------- #

# Match canonical planet names. Lowercased; matched as word-boundary tokens.
PLANETS: Final[tuple[str, ...]] = (
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
)

# Domain names align with the six DomainReading slots in the schema.
DOMAINS: Final[tuple[str, ...]] = (
    "career", "marriage", "children", "wealth", "health", "education",
)

# Topic synonyms that resolve to one of the canonical DOMAINS above.
# Maps lowercase synonym -> canonical domain name.
DOMAIN_SYNONYMS: Final[dict[str, str]] = {
    "job": "career",
    "work": "career",
    "profession": "career",
    "business": "career",
    "spouse": "marriage",
    "wife": "marriage",
    "husband": "marriage",
    "partner": "marriage",
    "relationship": "marriage",
    "love": "marriage",
    "child": "children",
    "son": "children",
    "daughter": "children",
    "kids": "children",
    "money": "wealth",
    "finance": "wealth",
    "wealth": "wealth",
    "income": "wealth",
    "richness": "wealth",
    "illness": "health",
    "disease": "health",
    "sickness": "health",
    "study": "education",
    "studies": "education",
    "school": "education",
    "college": "education",
    "degree": "education",
}

# Dasha keywords (Vimshottari mahadasha / antardasha).
DASHA_KEYWORDS: Final[tuple[str, ...]] = (
    "mahadasha", "antardasha", "dasha", "md", "ad",
    "vimshottari", "period",
)

# Timing-related keywords. Matched as substrings (with word-boundary regex).
TIMING_KEYWORDS: Final[tuple[str, ...]] = (
    "when", "what year", "in the future", "by 20", "in 20",
    "next", "soon", "future", "timing", "year",
)

# Yoga-related keywords. "yoga" alone catches generic questions; named
# yogas extend the match set.
YOGA_KEYWORDS: Final[tuple[str, ...]] = (
    "yoga", "gajakesari", "lakshmi", "raja", "neech bhanga",
    "kala sarpa", "panch maha", "kemadruma", "shubh", "pap",
)


# --------------------------------------------------------------------------- #
# Result dataclass                                                             #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class IntentClassification:
    """Result of ``classify_intent``.

    Attributes:
        intent: One of TIMING/DOMAIN/PLANET/DASHA/YOGA/GENERIC.
        confidence: Number of matched keywords scaled to [0, 1]. A pure
            GENERIC classification always has confidence 0.0 (no matches).
        extracted_entities: Tokens the classifier recognised — used by
            the finding selector. Order is deterministic (definition order).
    """

    intent: Intent
    confidence: float
    extracted_entities: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _word_boundary_search(token: str, text: str) -> bool:
    """Word-boundary regex match. ``re.escape`` protects against punctuation."""
    return bool(re.search(rf"\b{re.escape(token)}\b", text, flags=re.IGNORECASE))


def _scan_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    """Return the keywords in ``keywords`` that appear in ``text``.

    Multi-word keywords are scanned as substring matches (case-insensitive);
    single-word keywords use word-boundary regex.
    """
    low = text.lower()
    found: list[str] = []
    for kw in keywords:
        if " " in kw:
            if kw in low:
                found.append(kw)
        else:
            if _word_boundary_search(kw, text):
                found.append(kw)
    return found


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #


def classify_intent(question: str) -> IntentClassification:
    """Classify a question into one of six intents.

    Routing precedence (highest priority first):

    1. TIMING — any timing keyword is present.
       Timing is the highest-priority intent because a "when will I marry"
       question still needs MD/AD timeline data even though "marriage" also
       maps to DOMAIN.
    2. DASHA — explicit dasha keyword present (mahadasha, antardasha, MD, AD).
    3. YOGA — yoga keyword present.
    4. DOMAIN — domain keyword or synonym present.
    5. PLANET — planet name present.
    6. GENERIC — no recognised keywords.

    The first matched bucket wins. The confidence is the count of matched
    keywords in the winning bucket divided by ``min(matched, 3)`` capped at
    1.0 (a question matching 3+ keywords in any bucket is "very confident").
    """
    if not question or not question.strip():
        return IntentClassification(intent="GENERIC", confidence=0.0)

    # Pre-extract every interesting entity once; the downstream finding
    # selector wants all of them regardless of which intent wins.
    matched_timing = _scan_keywords(question, TIMING_KEYWORDS)
    matched_dasha = _scan_keywords(question, DASHA_KEYWORDS)
    matched_yoga = _scan_keywords(question, YOGA_KEYWORDS)
    matched_planet = _scan_keywords(question, PLANETS)
    matched_domain = _scan_keywords(question, DOMAINS)

    # Resolve domain synonyms (e.g. "wife" -> "marriage") and dedupe.
    low = question.lower()
    for syn, canonical in DOMAIN_SYNONYMS.items():
        if _word_boundary_search(syn, low) and canonical not in matched_domain:
            matched_domain.append(canonical)

    # All-extracted-entities set, deduplicated preserving order.
    all_entities: list[str] = []
    seen: set[str] = set()
    for bucket in (
        matched_planet, matched_domain, matched_dasha, matched_yoga, matched_timing,
    ):
        for entity in bucket:
            if entity not in seen:
                all_entities.append(entity)
                seen.add(entity)

    # Routing precedence
    if matched_timing:
        return IntentClassification(
            intent="TIMING",
            confidence=min(1.0, len(matched_timing) / 3.0),
            extracted_entities=all_entities,
        )
    if matched_dasha:
        return IntentClassification(
            intent="DASHA",
            confidence=min(1.0, len(matched_dasha) / 3.0),
            extracted_entities=all_entities,
        )
    if matched_yoga:
        return IntentClassification(
            intent="YOGA",
            confidence=min(1.0, len(matched_yoga) / 3.0),
            extracted_entities=all_entities,
        )
    if matched_domain:
        return IntentClassification(
            intent="DOMAIN",
            confidence=min(1.0, len(matched_domain) / 3.0),
            extracted_entities=all_entities,
        )
    if matched_planet:
        return IntentClassification(
            intent="PLANET",
            confidence=min(1.0, len(matched_planet) / 3.0),
            extracted_entities=all_entities,
        )

    return IntentClassification(intent="GENERIC", confidence=0.0)
