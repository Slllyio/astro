"""V1.5 LLM narrative layer — turns ReadingOutput JSON into human prose.

This package wraps and extends the existing app/llm/ infrastructure (Ollama
client + prompt templates + RAG citations) for the new ReadingOutput shape
produced by `app.reading.proforma`.

Public API:
    narrate_reading(reading, *, mode="full", section=None, client=None)
        -> NarrativeOutput

Design discipline (per CLAUDE.md project conventions):
- Deterministic skeleton ALWAYS produced first; LLM only elaborates.
- Safe-language constraint: prose never says "will", "guaranteed",
  "definitely" — only "indicates", "may", "suggests", "favors", "tends to".
- Lazy-imports anything heavy (sentence_transformers stays unloaded here —
  RAG citations are sourced from the already-enriched `Citation` blocks
  inside the ReadingOutput).
"""
from __future__ import annotations

from app.reading.narrative.synthesize import NarrativeOutput, narrate_reading

__all__ = ["narrate_reading", "NarrativeOutput"]
