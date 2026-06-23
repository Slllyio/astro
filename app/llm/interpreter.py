"""Composes LLM client + prompt templates into a chart-narration service.

Public entry point: `interpret_chart(chart, *, mode, section=None, client=None)`.
The route layer feeds it a ChartResponse-shaped dict and gets back a narrative
plus metadata about which path was taken (LLM vs fallback).

When the LLM call fails or OLLAMA_ENABLED is False, we render the
deterministic template instead. The endpoint never 500s on missing/broken
LLM — the caller simply gets a less fluent response.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from app.core.config import settings
# ``Citation`` now lives in ``app.llm.citations`` but callers (``reading_prose``, tests)
# still import it from here, its original home — re-exported for back-compat.
from app.llm.citations import Citation, gather_citations
from app.llm.client import LLMClient, OllamaClient, OllamaUnavailable
from app.llm.templates import (
    ALLOWED_SECTIONS,
    build_section_prompt,
    build_summary_prompt,
    deterministic_section,
    deterministic_summary,
)

logger = logging.getLogger(__name__)

InterpretMode = Literal["summary", "section"]


@dataclass(frozen=True)
class Interpretation:
    """Result of a narration call.

    `source` lets the caller (and the response payload) tell whether the
    text came from the LLM or the fallback template — useful for users
    deciding whether to enable Ollama.
    """
    text: str
    mode: InterpretMode
    section: str | None
    source: Literal["llm", "fallback"]
    model: str | None  # populated only when source == "llm"
    # supporting passages, populated by the reading-prose bridge; empty for the
    # plain chart-narration path. Defaulted so existing constructors are unaffected.
    citations: tuple[Citation, ...] = ()


def _default_client() -> LLMClient | None:
    """Build the default LLM client from settings, or None if disabled.

    Caller passing `client=None` to interpret_chart triggers this lookup;
    passing an explicit client (e.g. StubClient in tests) bypasses it.
    """
    if not settings.OLLAMA_ENABLED:
        return None
    return OllamaClient(
        host=settings.OLLAMA_HOST,
        model=settings.OLLAMA_MODEL,
        timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
    )


def interpret_chart(
    chart: dict[str, Any],
    *,
    mode: InterpretMode,
    section: str | None = None,
    client: LLMClient | None = None,
) -> Interpretation:
    """Narrate a chart in `summary` or `section` mode.

    `section` must be in ALLOWED_SECTIONS when mode == "section", and must
    be None otherwise. Validation is on the caller (the route does this
    via the path parameter type), but we re-check defensively.

    If `client` is None, falls back to settings (Ollama if enabled, else
    template). If the LLM call raises OllamaUnavailable, also falls back.
    """
    if mode == "section":
        if section is None:
            raise ValueError("section is required when mode='section'")
        if section not in ALLOWED_SECTIONS:
            raise ValueError(
                f"unknown section {section!r}; allowed: {sorted(ALLOWED_SECTIONS)}"
            )
    elif section is not None:
        raise ValueError("section must be None when mode='summary'")

    effective_client = client if client is not None else _default_client()

    # Optional doctrine grounding: when enabled, attach top supporting passages.
    # gather_citations never raises (it swallows index/runtime failures → ()), so the
    # narrative is always produced even if grounding is unavailable.
    citations: tuple[Citation, ...] = ()
    if settings.INTERPRET_CITATIONS_ENABLED:
        citations = gather_citations(chart, mode=mode, section=section)

    # Build the prompt regardless — both paths need it for inspection
    # (deterministic fallback ignores the prompt; tests inspect it).
    if mode == "summary":
        prompt = build_summary_prompt(chart)
    else:
        prompt = build_section_prompt(chart, section)  # type: ignore[arg-type]

    # No LLM available → render the deterministic template directly.
    if effective_client is None:
        text = (
            deterministic_summary(chart)
            if mode == "summary"
            else deterministic_section(chart, section)  # type: ignore[arg-type]
        )
        return Interpretation(
            text=text, mode=mode, section=section,
            source="fallback", model=None, citations=citations,
        )

    # LLM available — try, fall back on transport failure.
    try:
        text = effective_client.complete(prompt)
        model_name = getattr(effective_client, "model", "unknown")
        return Interpretation(
            text=text, mode=mode, section=section,
            source="llm", model=str(model_name), citations=citations,
        )
    except OllamaUnavailable:
        logger.warning("LLM unavailable; serving deterministic fallback")
        text = (
            deterministic_summary(chart)
            if mode == "summary"
            else deterministic_section(chart, section)  # type: ignore[arg-type]
        )
        return Interpretation(
            text=text, mode=mode, section=section,
            source="fallback", model=None, citations=citations,
        )
