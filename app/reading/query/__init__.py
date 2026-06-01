"""V1.5 free-form chart query layer.

Public API:
    ask_about_chart(reading, question, *, top_k=5, client=None) -> QueryResult

This package answers natural-language questions about a specific kundli's
ReadingOutput JSON. Answers are grounded in (a) the chart's own findings
and (b) doctrine passages retrieved from ``knowledge_library``.

Unlike the V1.0 narrative layer, the V1.5 query layer requires an LLM —
free-form questions cannot be deterministically templated. When the LLM
is unavailable, ``ask_about_chart`` returns a structured "cannot answer
without LLM available" response rather than fabricating prose.
"""
from app.reading.query.engine import QueryResult, ask_about_chart

__all__ = ["ask_about_chart", "QueryResult"]
