"""Free-form chart question engine.

Public API:
    ask_about_chart(reading, question, *, top_k=5, client=None) -> QueryResult

Pipeline:
    1. Classify question intent (TIMING / DOMAIN / PLANET / DASHA / YOGA / GENERIC).
    2. Extract relevant Finding dicts from the reading per intent.
    3. Retrieve doctrine passages from ``knowledge_library`` via the
       lazy-imported ``KnowledgeSearchService`` — the imports happen INSIDE
       the function body so the V1.0 lazy-import discipline is preserved.
    4. Build a grounded LLM prompt (question + findings + passages).
    5. LLM generates the answer.
    6. Filter the answer through a safe-language regex; if any forbidden
       word slips through, return a structured "answer suppressed" result
       rather than serving rule-violating prose.
    7. Return ``QueryResult`` carrying answer + citations +
       referenced_finding_ids + confidence + intent + llm_used.

LLM discipline:
    A free-form answer cannot be synthesised deterministically the way the
    V1.0 narrative skeletons can. When no LLM client is available, this
    module returns a structured "cannot answer without LLM available"
    response with ``llm_used=False`` and ``answer`` carrying the
    explanation — never a fabricated answer.

Lazy-import discipline (V1.0 lockfile):
    ``sentence_transformers``, ``torch``, ``knowledge_search`` and
    ``app.llm.client`` are imported INSIDE function bodies, never at
    module top. A regression test asserts that importing
    ``app.reading.query`` does NOT pull sentence_transformers into
    ``sys.modules``.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.reading.query.finding_selector import (
    _id,
    select_findings,
)
from app.reading.query.intent_classifier import (
    IntentClassification,
    classify_intent,
)
from app.reading.query.prompts import (
    FORBIDDEN_WORDS,
    build_chart_qa_prompt,
)

logger = logging.getLogger(__name__)


# Build the safe-language regex once. Word-boundary anchors so "willingness"
# does NOT match "will". Same pattern shape as the narrative layer.
_FORBIDDEN_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_WORDS) + r")\b",
    flags=re.IGNORECASE,
)


# Truncation cap on the passage text we store inside a Citation. Mirrors
# rag_citations.py to keep payload size predictable.
_PASSAGE_MAX_CHARS: int = 500


# --------------------------------------------------------------------------- #
# Result dataclass                                                             #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class QueryResult:
    """Structured response to a free-form chart question.

    Attributes:
        answer: The grounded prose answer. When the LLM is unavailable or
            the answer was suppressed for a safe-language violation, this
            carries an explanatory message instead.
        citations: List of citation dicts (``source``, ``passage``,
            ``relevance``, ``knowledge_doc_id``). May be empty if the RAG
            index is unavailable or no passages cleared the relevance bar.
        referenced_finding_ids: IDs of the findings forwarded to the LLM
            as grounding. Useful for the UI to highlight the relevant
            blocks in the structured reading.
        confidence: A [0, 1] score derived from the intent confidence and
            the count of supporting findings + passages. ``0.0`` when the
            LLM was unavailable or the answer was suppressed.
        intent: The routed intent name (TIMING / DOMAIN / PLANET / ...).
        llm_used: True iff the LLM produced the final answer (i.e. NOT a
            fallback "LLM unavailable" or "answer suppressed" message).
    """

    answer: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    referenced_finding_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    intent: str = "GENERIC"
    llm_used: bool = False


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


_LLM_UNAVAILABLE_MESSAGE = (
    "I cannot answer this question without a language model available. "
    "The chart's structured findings are present and can be inspected "
    "directly, but free-form answers require an LLM client. Enable "
    "OLLAMA_ENABLED in the engine configuration or pass an explicit "
    "client to ask_about_chart()."
)

_ANSWER_SUPPRESSED_MESSAGE = (
    "The generated answer contained a forbidden predictive word and was "
    "suppressed to preserve the project's safe-language discipline. "
    "Please rephrase the question or inspect the structured findings "
    "directly."
)


def _resolve_default_client() -> Any | None:
    """Build the default LLM client from settings, or None if disabled.

    Lazy-imports ``app.core.config`` and ``app.llm.client`` so the query
    module's import cost stays minimal in the LLM-disabled path.
    """
    try:
        from app.core.config import settings
    except Exception:  # pragma: no cover - settings always importable in app
        return None
    if not getattr(settings, "OLLAMA_ENABLED", False):
        return None
    try:
        from app.llm.client import OllamaClient

        return OllamaClient(
            host=settings.OLLAMA_HOST,
            model=settings.OLLAMA_MODEL,
            timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # pragma: no cover - import failure unusual
        logger.warning("Could not build default Ollama client: %s", exc)
        return None


def _passes_safe_language(text: str) -> bool:
    """True iff ``text`` contains none of the forbidden predictive words."""
    return _FORBIDDEN_PATTERN.search(text) is None


def _build_rag_query(question: str, classification: IntentClassification) -> str:
    """Build the RAG query string.

    Combines the intent label + any extracted entities with the user's
    question — this gives the vector encoder both the natural-language
    signal and the doctrine-specific terms (planet names, yoga names) to
    anchor on.
    """
    parts: list[str] = []
    if classification.extracted_entities:
        parts.append(" ".join(classification.extracted_entities))
    parts.append(classification.intent.lower())
    parts.append(question.strip())
    return " ".join(p for p in parts if p)


def _retrieve_passages(
    rag_query: str, *, top_k: int,
) -> list[dict[str, Any]]:
    """Retrieve doctrine passages via the lazy-imported RAG service.

    Returns a list of dicts (NOT Citation objects) so the engine remains
    decoupled from the schema layer. Each dict carries ``source``,
    ``passage``, ``relevance``, and ``knowledge_doc_id``.

    Returns ``[]`` when the index is unavailable; the engine surfaces
    the warning in logs but does not raise — answering without doctrine
    passages is degraded but not broken (the chart findings are still
    available as grounding).
    """
    # Lazy-imports — never at module top. The lazy-import regression test
    # in tests/reading/query/test_lazy_imports.py asserts that loading
    # this module alone does NOT pull sentence_transformers into sys.modules.
    try:
        from app.medini.services.knowledge_search import (
            IndexUnavailable,
            get_default_service,
        )
    except Exception as exc:  # pragma: no cover - import failure unusual
        logger.warning("Could not import knowledge_search: %s", exc)
        return []

    svc = get_default_service()
    try:
        svc.ensure_loaded()
    except IndexUnavailable as exc:
        logger.warning(
            "RAG index unavailable; query answer will be ungrounded: %s", exc,
        )
        return []
    except Exception as exc:  # pragma: no cover - other load failure
        logger.warning("RAG ensure_loaded failed: %s", exc)
        return []

    try:
        results = svc.search(rag_query, mode="hybrid", top=top_k)
    except Exception as exc:
        logger.warning("RAG search failed: %s", exc)
        return []

    out: list[dict[str, Any]] = []
    for r in results:
        # Defensively support either ``text`` or ``snippet`` on the result.
        text = getattr(r, "snippet", None) or getattr(r, "text", "") or ""
        out.append(
            {
                "source": str(getattr(r, "source", "") or ""),
                "passage": text[:_PASSAGE_MAX_CHARS],
                "relevance": float(getattr(r, "score", 0.0) or 0.0),
                "knowledge_doc_id": str(getattr(r, "artefact_id", "") or ""),
            },
        )
    return out


def _compute_confidence(
    intent_confidence: float,
    n_findings: int,
    n_passages: int,
) -> float:
    """Aggregate confidence: 0.5 * intent + 0.25 * findings + 0.25 * passages.

    findings/passages count is normalised to ``min(n, 3) / 3`` so the
    score is bounded in [0, 1] and a single finding doesn't dominate.
    """
    findings_factor = min(n_findings, 3) / 3.0
    passages_factor = min(n_passages, 3) / 3.0
    return min(
        1.0,
        0.5 * intent_confidence + 0.25 * findings_factor + 0.25 * passages_factor,
    )


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #


def ask_about_chart(
    reading: dict[str, Any],
    question: str,
    *,
    top_k: int = 5,
    client: Any | None = None,
) -> QueryResult:
    """Answer a free-form question about a specific kundli.

    Args:
        reading: ReadingOutput-shaped dict (as produced by
            ``app.reading.proforma.compute``).
        question: The user's free-form natural-language question.
        top_k: Maximum number of doctrine passages to retrieve.
        client: Optional explicit LLM client. When None, an Ollama client
            is built from settings if OLLAMA_ENABLED; otherwise the
            structured "cannot answer" response is returned.

    Returns:
        ``QueryResult``. Always usable (never raises on LLM failure or
        index unavailability).

    Raises:
        TypeError: if ``reading`` is not a dict.
        ValueError: if ``question`` is empty/blank.
    """
    if not isinstance(reading, dict):
        raise TypeError("reading must be a dict matching ReadingOutput shape")
    if not question or not question.strip():
        raise ValueError("question must be a non-empty string")
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    # ---- Step 1-2: classify intent + select grounding findings ----
    classification = classify_intent(question)
    findings = select_findings(reading, classification)
    finding_ids = [fid for fid in (_id(f) for f in findings) if fid]

    # ---- Step 3: retrieve doctrine passages (lazy import inside) ----
    rag_query = _build_rag_query(question, classification)
    passages = _retrieve_passages(rag_query, top_k=top_k)

    # ---- Step 4: LLM client resolution ----
    effective_client = client if client is not None else _resolve_default_client()

    if effective_client is None:
        # No LLM available: structured fallback (no fabrication).
        return QueryResult(
            answer=_LLM_UNAVAILABLE_MESSAGE,
            citations=passages,
            referenced_finding_ids=finding_ids,
            confidence=0.0,
            intent=classification.intent,
            llm_used=False,
        )

    # ---- Step 5: build prompt + call LLM ----
    prompt = build_chart_qa_prompt(question, findings, passages)
    try:
        raw = effective_client.complete(prompt)
    except Exception as exc:  # noqa: BLE001 - any client failure -> fallback
        logger.warning(
            "LLM call failed for chart question; returning structured fallback: %s",
            exc,
        )
        return QueryResult(
            answer=_LLM_UNAVAILABLE_MESSAGE,
            citations=passages,
            referenced_finding_ids=finding_ids,
            confidence=0.0,
            intent=classification.intent,
            llm_used=False,
        )

    answer_text = (raw or "").strip()
    if not answer_text:
        return QueryResult(
            answer=_LLM_UNAVAILABLE_MESSAGE,
            citations=passages,
            referenced_finding_ids=finding_ids,
            confidence=0.0,
            intent=classification.intent,
            llm_used=False,
        )

    # ---- Step 6: safe-language filter ----
    if not _passes_safe_language(answer_text):
        logger.info(
            "LLM answer contained a forbidden word; suppressing per safe-language policy",
        )
        return QueryResult(
            answer=_ANSWER_SUPPRESSED_MESSAGE,
            citations=passages,
            referenced_finding_ids=finding_ids,
            confidence=0.0,
            intent=classification.intent,
            llm_used=False,
        )

    # ---- Step 7: return grounded result ----
    confidence = _compute_confidence(
        classification.confidence, len(findings), len(passages),
    )
    return QueryResult(
        answer=answer_text,
        citations=passages,
        referenced_finding_ids=finding_ids,
        confidence=confidence,
        intent=classification.intent,
        llm_used=True,
    )
