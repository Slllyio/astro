"""Tests for ``app.reading.query.engine.ask_about_chart``.

Coverage targets:
- LLM-unavailable path returns structured "cannot answer" message
- LLM-available path returns grounded answer + populated citations
- Safe-language filter suppresses forbidden-word answers
- QueryResult shape (answer / citations / referenced_finding_ids /
  confidence / intent / llm_used)
- Citations carry both source AND passage AND knowledge_doc_id keys
- Engine surfaces the routed intent + the finding IDs it forwarded
- Defensive input validation (empty question, non-dict reading)

The Bangalore baseline reading is the canonical anchor; the LLM client
and the RAG service are mocked so tests run offline.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.reading.query.engine import QueryResult, ask_about_chart


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _StubLLM:
    """Minimal LLMClient stub returning a canned answer."""

    def __init__(self, response: str = "Saturn placed in 12th indicates introspective tendencies."):
        self.response = response
        self.last_prompt: str | None = None

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


@pytest.fixture
def patch_rag_unavailable(monkeypatch):
    """Make ``_retrieve_passages`` return [] without touching the real index.

    The Bangalore baseline reading uses ``_run_core_pipeline`` which already
    skips RAG, but tests calling ``ask_about_chart`` would still try to
    initialise the singleton service. Patching the retrieval helper keeps
    those calls offline.
    """
    from app.reading.query import engine as engine_module

    monkeypatch.setattr(
        engine_module, "_retrieve_passages", lambda *args, **kw: [],
    )


@pytest.fixture
def patch_rag_with_passages(monkeypatch):
    """Make ``_retrieve_passages`` return a fixed list of fake passages."""
    from app.reading.query import engine as engine_module

    fake_passages = [
        {
            "source": "BPHS",
            "passage": "Saturn in the 12th house produces a contemplative nature.",
            "relevance": 0.91,
            "knowledge_doc_id": "bphs_ch_24_v_3",
        },
        {
            "source": "Phaladeepika",
            "passage": "The 12th lord placed in its own house tends to indicate gains through foreign sources.",
            "relevance": 0.83,
            "knowledge_doc_id": "phaladeepika_ch_4_v_15",
        },
    ]
    monkeypatch.setattr(
        engine_module, "_retrieve_passages", lambda *args, **kw: list(fake_passages),
    )
    return fake_passages


# ---------------------------------------------------------------------------
# LLM-unavailable path
# ---------------------------------------------------------------------------


def test_no_llm_returns_structured_cannot_answer(
    bangalore_reading: dict, patch_rag_unavailable,
) -> None:
    """When client=None and OLLAMA_ENABLED=False, return structured fallback."""
    result = ask_about_chart(
        bangalore_reading,
        "When will my marriage happen?",
        client=None,
    )
    assert isinstance(result, QueryResult)
    assert result.llm_used is False
    assert result.confidence == 0.0
    assert "cannot answer" in result.answer.lower() or "without" in result.answer.lower()


def test_no_llm_still_returns_intent_and_finding_ids(
    bangalore_reading: dict, patch_rag_unavailable,
) -> None:
    """Structured fallback still carries the routed intent + finding IDs."""
    result = ask_about_chart(
        bangalore_reading,
        "Tell me about my mahadasha",
        client=None,
    )
    assert result.intent == "DASHA"
    # The Bangalore baseline has MD judgments — IDs should be present.
    assert len(result.referenced_finding_ids) >= 1


# ---------------------------------------------------------------------------
# LLM-available path
# ---------------------------------------------------------------------------


def test_with_llm_returns_grounded_answer(
    bangalore_reading: dict, patch_rag_with_passages,
) -> None:
    """When an LLM client is supplied, the answer comes from the LLM."""
    client = _StubLLM("Saturn in the 12th indicates tendencies toward reflection.")
    result = ask_about_chart(
        bangalore_reading,
        "Tell me about Saturn in my chart",
        client=client,
    )
    assert result.llm_used is True
    assert "Saturn" in result.answer
    assert result.confidence > 0.0


def test_with_llm_citations_populated(
    bangalore_reading: dict, patch_rag_with_passages,
) -> None:
    """Citations from the RAG layer are forwarded to the result."""
    client = _StubLLM("A grounded answer about Saturn.")
    result = ask_about_chart(
        bangalore_reading,
        "Tell me about Saturn",
        client=client,
    )
    assert len(result.citations) == len(patch_rag_with_passages)
    for c in result.citations:
        assert "source" in c
        assert "passage" in c
        assert "knowledge_doc_id" in c
        assert "relevance" in c


def test_with_llm_prompt_includes_question_and_findings(
    bangalore_reading: dict, patch_rag_with_passages,
) -> None:
    """The LLM prompt carries the question AND the findings AND passages."""
    client = _StubLLM("An answer that mentions reflection.")
    ask_about_chart(
        bangalore_reading,
        "Tell me about Saturn in my chart",
        client=client,
    )
    assert client.last_prompt is not None
    assert "Saturn" in client.last_prompt
    # The doctrine-passage stub text should appear in the prompt.
    assert "BPHS" in client.last_prompt or "Phaladeepika" in client.last_prompt


# ---------------------------------------------------------------------------
# Safe-language filter
# ---------------------------------------------------------------------------


def test_forbidden_word_in_answer_is_suppressed(
    bangalore_reading: dict, patch_rag_unavailable,
) -> None:
    """An LLM answer containing 'will' is suppressed with structured message."""
    client = _StubLLM("Saturn will guarantee setbacks in the next mahadasha.")
    result = ask_about_chart(
        bangalore_reading,
        "What does Saturn indicate?",
        client=client,
    )
    assert result.llm_used is False
    assert result.confidence == 0.0
    # The structured suppression message is returned instead.
    assert "suppress" in result.answer.lower() or "forbidden" in result.answer.lower()


@pytest.mark.parametrize("word", ["will", "guaranteed", "definitely", "certainly", "always"])
def test_each_forbidden_word_individually_suppressed(
    bangalore_reading: dict, patch_rag_unavailable, word: str,
) -> None:
    """Every forbidden word triggers suppression."""
    client = _StubLLM(f"This {word} happen in 2030.")
    result = ask_about_chart(
        bangalore_reading,
        "When does it happen?",
        client=client,
    )
    assert result.llm_used is False


def test_safe_synonyms_pass(
    bangalore_reading: dict, patch_rag_unavailable,
) -> None:
    """Safe modal verbs ('may', 'indicates') pass the filter."""
    client = _StubLLM(
        "Saturn placed in the 12th indicates a contemplative tendency and may "
        "favor introspective work during the current mahadasha."
    )
    result = ask_about_chart(
        bangalore_reading,
        "What does Saturn indicate?",
        client=client,
    )
    assert result.llm_used is True
    assert "Saturn" in result.answer


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


def test_query_result_has_expected_attrs(
    bangalore_reading: dict, patch_rag_unavailable,
) -> None:
    """QueryResult exposes the documented attribute set."""
    client = _StubLLM("Indicative answer about the chart.")
    result = ask_about_chart(
        bangalore_reading, "Anything interesting?", client=client,
    )
    for attr in (
        "answer", "citations", "referenced_finding_ids",
        "confidence", "intent", "llm_used",
    ):
        assert hasattr(result, attr)


# ---------------------------------------------------------------------------
# Defensive validation
# ---------------------------------------------------------------------------


def test_non_dict_reading_raises_type_error() -> None:
    """``ask_about_chart`` rejects non-dict reading inputs."""
    with pytest.raises(TypeError):
        ask_about_chart("not a dict", "question", client=_StubLLM())  # type: ignore[arg-type]


def test_empty_question_raises_value_error(bangalore_reading: dict) -> None:
    """Empty / whitespace question raises ValueError."""
    with pytest.raises(ValueError):
        ask_about_chart(bangalore_reading, "", client=_StubLLM())
    with pytest.raises(ValueError):
        ask_about_chart(bangalore_reading, "   ", client=_StubLLM())


def test_top_k_must_be_positive(bangalore_reading: dict) -> None:
    """top_k=0 or negative raises ValueError."""
    with pytest.raises(ValueError):
        ask_about_chart(bangalore_reading, "question", top_k=0, client=_StubLLM())
    with pytest.raises(ValueError):
        ask_about_chart(bangalore_reading, "question", top_k=-1, client=_StubLLM())


# ---------------------------------------------------------------------------
# LLM error handling
# ---------------------------------------------------------------------------


def test_llm_exception_returns_structured_fallback(
    bangalore_reading: dict, patch_rag_unavailable,
) -> None:
    """If the LLM client raises, the result is the structured fallback."""

    class _BrokenLLM:
        def complete(self, prompt: str) -> str:
            raise RuntimeError("ollama down")

    result = ask_about_chart(
        bangalore_reading, "Anything?", client=_BrokenLLM(),
    )
    assert result.llm_used is False
    assert result.confidence == 0.0


def test_empty_llm_response_returns_fallback(
    bangalore_reading: dict, patch_rag_unavailable,
) -> None:
    """If the LLM returns empty string, the fallback is used."""
    client = _StubLLM("")
    result = ask_about_chart(
        bangalore_reading, "Anything?", client=client,
    )
    assert result.llm_used is False


# ---------------------------------------------------------------------------
# Intent routing surfaces through to the engine
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "question, expected_intent",
    [
        ("When will my marriage happen?", "TIMING"),
        ("Tell me about my mahadasha", "DASHA"),
        ("Do I have Gajakesari yoga?", "YOGA"),
        ("How is my career?", "DOMAIN"),
        ("What about Saturn?", "PLANET"),
    ],
)
def test_engine_surfaces_intent(
    bangalore_reading: dict, patch_rag_unavailable,
    question: str, expected_intent: str,
) -> None:
    """The result's ``intent`` attribute matches the classifier's routing."""
    result = ask_about_chart(bangalore_reading, question, client=_StubLLM("indicates"))
    assert result.intent == expected_intent
