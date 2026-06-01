"""Prashna layer — route natural-language questions to bhava verdicts.

A user asks "will I get married this year?" and this module returns
the relevant bhava number (7) so the framework can deliver its
structured verdict. The mapping is **deterministic and explainable**:
each bhava carries Sanskrit + English + colloquial keywords from
classical doctrine.

## Why keyword routing, not LLM

The framework's value is doctrine-faithfulness. A keyword router has
audit-able mappings (each match cites which bhava and why); an LLM
router would obscure the routing logic and could drift from doctrine.
Keywords come from BPHS Ch.6 + Phaladeepika + common conversational
phrasings.

## How matching works

The user's question is lowercased and stemmed lightly; each bhava's
keyword set is scored by simple token overlap. Tie-breaking prefers
the bhava with the more specific match (longer keyword wins).

The returned ``PrashnaMatch`` carries the predicted bhava + score +
the matched keywords + a confidence label. The caller (FastAPI
endpoint) takes the bhava number and passes it to ``judge_bhava``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Mapping


# Per-bhava keyword sets — Sanskrit + English + colloquial.
# Order doesn't matter; matching is set-based.
_BHAVA_KEYWORDS: Final[Mapping[int, frozenset[str]]] = {
    1:  frozenset({"self", "body", "vitality", "personality",
                   "identity", "appearance", "physique", "tanu",
                   "lagna", "i am", "who am i", "myself"}),
    2:  frozenset({"wealth", "money", "savings", "voice",
                   "speech", "food", "dhana", "kutumba",
                   "bank", "financial", "treasure", "earnings",
                   "household", "diet", "make money", "make a lot of money"}),
    3:  frozenset({"siblings", "sibling", "brother", "sister",
                   "courage", "valour", "communication", "writing",
                   "neighbour", "hobby", "bhratru", "vikrama",
                   "skill", "creativity", "short travel"}),
    4:  frozenset({"mother", "mom", "mum", "mothers",
                   "home", "house", "property", "real estate",
                   "comfort", "vehicle",
                   "schooling", "land", "matr", "sukha",
                   "happiness", "domestic", "residence"}),
    5:  frozenset({"child", "children", "kid", "kids", "son", "daughter",
                   "pregnancy", "intelligence", "intellect", "romance",
                   "love affair", "speculation", "investment",
                   "putra", "vidya", "mantra", "spiritual practice",
                   "learning", "study", "exams", "exam", "have child",
                   "have a child", "have a kid"}),
    6:  frozenset({"enemies", "enemy", "disease", "illness", "sickness",
                   "debt", "loan", "service",
                   "litigation", "lawsuit", "competition", "fight",
                   "ari", "shatru", "rina", "obstacle"}),
    7:  frozenset({"spouse", "marriage", "marry", "marrying", "married",
                   "wedding", "partner", "partnership", "relationship",
                   "wife", "husband", "love", "yuvati",
                   "kalatra", "business partner", "open enemy",
                   "engagement", "dating", "matrimony"}),
    8:  frozenset({"longevity", "death", "lifespan", "transformation",
                   "inheritance", "inherit", "occult", "secret", "hidden",
                   "research", "ayur", "marana", "mrityu", "danger",
                   "accident", "surgery", "insurance", "tantra",
                   "underground", "scandal"}),
    9:  frozenset({"father", "dad", "fathers", "papa",
                   "guru", "teacher", "religion", "dharma",
                   "fortune", "luck", "higher learning", "philosophy",
                   "spirituality", "long travel", "pilgrimage",
                   "pitr", "bhagya", "mentor", "abroad",
                   "foreign", "destiny", "pious",
                   "travel abroad", "go abroad"}),
    10: frozenset({"career", "job", "profession", "work", "status",
                   "fame", "reputation", "ambition", "success",
                   "successful", "succeed",
                   "boss", "authority", "karma", "rajya",
                   "achievement", "promotion", "office", "business",
                   "leadership", "post", "position",
                   "successful at work", "successful at job"}),
    11: frozenset({"gains", "income", "profit", "friend", "friends",
                   "social", "network", "elder sibling", "wishes",
                   "desires", "aspirations", "labha", "kama",
                   "windfall", "lottery", "bonus", "hopes"}),
    12: frozenset({"loss", "expense", "expenditure", "moksha",
                   "liberation",
                   "isolation", "retreat", "bed", "sleep", "dream",
                   "vyaya", "sannyasa", "monastery",
                   "renunciation", "exile", "secret enemy"}),
}

# Health is the most overloaded keyword — it triggers both bhava 1
# (vitality) and bhava 6 (illness). We special-case it: only score it
# when the question lacks more specific relational subjects.
_HEALTH_AMBIGUOUS: Final[frozenset[str]] = frozenset({"health", "healthy"})


@dataclass(frozen=True)
class PrashnaMatch:
    """Result of routing a question to a bhava."""
    bhava: int
    confidence: str            # HIGH / MEDIUM / LOW / NONE
    matched_keywords: tuple[str, ...]
    score: int                 # raw weighted score
    candidates_considered: tuple[tuple[int, int], ...]  # (bhava, score) sorted


def _tokenise(text: str) -> set[str]:
    """Lowercase + split + simple word-boundary cleanup. No stemming
    library required — keeps the dependency footprint minimal."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return set(cleaned.split())


_RELATIONAL_BOOSTERS: Final[frozenset[str]] = frozenset({
    "mother", "mom", "mum", "father", "dad", "papa",
    "spouse", "wife", "husband", "partner",
    "child", "children", "kid", "son", "daughter",
    "sibling", "brother", "sister",
    "boss", "friend",
})


def _score_bhava_for_text(
    text: str, keywords: frozenset[str], bhava: int,
) -> tuple[int, list[str]]:
    """Score one bhava against a question.

    Weighting:
    * Multi-word phrase: +3 (most specific)
    * Relational subject keyword (mother/spouse/child/etc.): +2
    * Other single-word match: +1
    * "health" / "healthy": +1 only for bhava 1 (vitality); bhava 6
      ignores them since they're general enough that "i have a fever"
      doesn't really mean to ask about 6L afflictions.
    """
    text_lower = text.lower()
    tokens = _tokenise(text)
    score = 0
    matched: list[str] = []
    for kw in keywords:
        if " " in kw:
            if kw in text_lower:
                score += 3
                matched.append(kw)
        else:
            if kw in tokens:
                if kw in _RELATIONAL_BOOSTERS:
                    score += 2
                else:
                    score += 1
                matched.append(kw)
    # Health-specific tweak: 1H gets credit, others ignore it
    if bhava == 1:
        for hw in _HEALTH_AMBIGUOUS:
            if hw in tokens:
                score += 1
                matched.append(hw)
    return score, matched


def route_question(question: str) -> PrashnaMatch:
    """Map a natural-language question to its bhava.

    Args:
        question: Free-form user question.

    Returns:
        PrashnaMatch with the best-matching bhava + confidence. If no
        bhava scores above zero, returns ``bhava=1, confidence="NONE"``
        with an empty match — the caller can prompt for clarification.
    """
    scores: dict[int, tuple[int, list[str]]] = {}
    for b, kws in _BHAVA_KEYWORDS.items():
        s, m = _score_bhava_for_text(question, kws, b)
        if s > 0:
            scores[b] = (s, m)

    if not scores:
        return PrashnaMatch(
            bhava=1, confidence="NONE",
            matched_keywords=(), score=0,
            candidates_considered=(),
        )

    # Sort by score descending; ties broken by lowest bhava number
    # (deterministic, but ties are rare).
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1][0], kv[0]))
    top_bhava, (top_score, top_keywords) = ranked[0]

    second_score = ranked[1][1][0] if len(ranked) > 1 else 0
    margin = top_score - second_score
    if top_score >= 4 and margin >= 2:
        confidence = "HIGH"
    elif top_score >= 2 and margin >= 1:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return PrashnaMatch(
        bhava=top_bhava,
        confidence=confidence,
        matched_keywords=tuple(sorted(set(top_keywords))),
        score=top_score,
        candidates_considered=tuple((b, s) for b, (s, _) in ranked[:4]),
    )


def keywords_for_bhava(bhava: int) -> frozenset[str]:
    """Public access to the keyword set for a bhava (UI / debugging)."""
    if not 1 <= bhava <= 12:
        raise ValueError(f"bhava must be 1..12, got {bhava}")
    return _BHAVA_KEYWORDS[bhava]
