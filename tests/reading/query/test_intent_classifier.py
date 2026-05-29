"""Tests for ``app.reading.query.intent_classifier``.

Coverage targets:
- All six intent buckets (TIMING / DOMAIN / PLANET / DASHA / YOGA / GENERIC)
- Routing precedence (TIMING > DASHA > YOGA > DOMAIN > PLANET > GENERIC)
- Entity extraction (planet, domain, synonym, named yoga)
- Empty/whitespace question handling
- Confidence bounds [0.0, 1.0]
"""
from __future__ import annotations

import pytest

from app.reading.query.intent_classifier import (
    IntentClassification,
    classify_intent,
)


# ---------------------------------------------------------------------------
# Per-intent routing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "question",
    [
        "When will my marriage happen?",
        "What year will I get married?",
        "Will career growth come soon?",
        "When does my next mahadasha start?",
        "What does the future hold for my health?",
        "Timing for buying a house?",
    ],
)
def test_timing_questions_route_to_timing(question: str) -> None:
    """Any timing keyword should win over other matched intents.

    'marriage' is a DOMAIN keyword but a 'when...marriage?' question
    needs the timeline (MD/AD windows) more than the domain block.
    """
    result = classify_intent(question)
    assert result.intent == "TIMING"
    assert result.confidence > 0.0


@pytest.mark.parametrize(
    "question, expected_domain",
    [
        ("Tell me about my career prospects", "career"),
        ("How is my marriage looking?", "marriage"),
        ("My wife — what does the chart say?", "marriage"),
        ("How is my wealth profile?", "wealth"),
        ("Will I have children?", "children"),
        ("What about my education?", "education"),
        ("Anything about my job?", "career"),
        ("My finance situation", "wealth"),
    ],
)
def test_domain_questions_extract_correct_canonical_domain(
    question: str, expected_domain: str,
) -> None:
    """DOMAIN intent extracts the canonical domain name (synonyms resolved)."""
    result = classify_intent(question)
    # 'Will I have children?' has 'will' (timing kw) so it routes TIMING;
    # the synonym still appears in extracted_entities.
    assert expected_domain in result.extracted_entities


def test_planet_question_routes_to_planet() -> None:
    """A bare 'what about Saturn' question routes to PLANET."""
    result = classify_intent("What about Saturn in my chart?")
    assert result.intent == "PLANET"
    assert "saturn" in result.extracted_entities


@pytest.mark.parametrize(
    "question, planet",
    [
        ("Tell me about Mars", "mars"),
        ("Where is my Jupiter?", "jupiter"),
        ("How is Venus placed?", "venus"),
        ("What does Mercury indicate?", "mercury"),
        ("My Moon — strong or weak?", "moon"),
    ],
)
def test_planet_extraction(question: str, planet: str) -> None:
    """Every canonical planet name is detected as an entity."""
    result = classify_intent(question)
    assert planet in result.extracted_entities


def test_dasha_question_routes_to_dasha() -> None:
    """'mahadasha' keyword routes to DASHA, not GENERIC."""
    result = classify_intent("Tell me about my current mahadasha")
    assert result.intent == "DASHA"


def test_antardasha_routes_to_dasha() -> None:
    """'antardasha' keyword also routes to DASHA."""
    result = classify_intent("How is my antardasha looking?")
    assert result.intent == "DASHA"


def test_yoga_question_routes_to_yoga() -> None:
    """'yoga' keyword routes to YOGA."""
    result = classify_intent("Do I have any strong yoga in my chart?")
    assert result.intent == "YOGA"


def test_named_yoga_routes_to_yoga() -> None:
    """Specific yoga names route to YOGA."""
    result = classify_intent("Do I have Gajakesari yoga?")
    assert result.intent == "YOGA"
    assert "gajakesari" in result.extracted_entities


def test_generic_question() -> None:
    """A question with no recognised keywords routes to GENERIC."""
    result = classify_intent("Hello, please give me an overview")
    assert result.intent == "GENERIC"
    assert result.confidence == 0.0


def test_empty_question_returns_generic() -> None:
    """An empty question routes to GENERIC with confidence 0.0."""
    result = classify_intent("")
    assert result.intent == "GENERIC"
    assert result.confidence == 0.0


def test_whitespace_question_returns_generic() -> None:
    """A whitespace-only question routes to GENERIC."""
    result = classify_intent("   \n  ")
    assert result.intent == "GENERIC"


# ---------------------------------------------------------------------------
# Precedence
# ---------------------------------------------------------------------------


def test_timing_beats_dasha() -> None:
    """Timing keyword in a dasha question wins TIMING precedence."""
    result = classify_intent("When will my next mahadasha start?")
    assert result.intent == "TIMING"


def test_dasha_beats_planet() -> None:
    """Dasha keyword in a planet question wins DASHA precedence."""
    result = classify_intent("How is Saturn mahadasha looking?")
    assert result.intent == "DASHA"


def test_yoga_beats_planet() -> None:
    """Yoga keyword in a planet question wins YOGA precedence."""
    result = classify_intent("Does Jupiter form any yoga in my chart?")
    assert result.intent == "YOGA"


def test_domain_beats_planet() -> None:
    """Domain keyword in a planet question wins DOMAIN precedence."""
    result = classify_intent("How does Saturn affect my career?")
    assert result.intent == "DOMAIN"


# ---------------------------------------------------------------------------
# Confidence bounds + result shape
# ---------------------------------------------------------------------------


def test_confidence_is_bounded() -> None:
    """Confidence stays in [0.0, 1.0] even with many matched keywords."""
    result = classify_intent(
        "When mahadasha career marriage health wealth Saturn yoga timing"
    )
    assert 0.0 <= result.confidence <= 1.0


def test_returns_dataclass_with_expected_attrs() -> None:
    """``classify_intent`` returns an ``IntentClassification`` dataclass."""
    result = classify_intent("What about my career?")
    assert isinstance(result, IntentClassification)
    assert hasattr(result, "intent")
    assert hasattr(result, "confidence")
    assert hasattr(result, "extracted_entities")
    assert isinstance(result.extracted_entities, list)


def test_extracted_entities_are_deterministic() -> None:
    """Same input -> same extracted_entities (no random ordering)."""
    q = "How does Saturn affect my career and marriage?"
    a = classify_intent(q)
    b = classify_intent(q)
    assert a.extracted_entities == b.extracted_entities
