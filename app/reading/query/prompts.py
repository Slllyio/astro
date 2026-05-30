"""LLM prompt templates for the V1.5 free-form chart query layer.

Discipline:
- Hard CONSTRAINTS block in the prompt enumerates the safe-language list.
- We pass both the chart's findings AND retrieved doctrine passages so
  the model can ground its answer in BOTH the specific chart AND the
  classical doctrine — never one without the other.
- The model is told explicitly to refuse if the sources do not support
  an answer; the engine layer enforces this with a regex post-check too.
"""
from __future__ import annotations

import json
from typing import Any

# Words that must NEVER appear in an answer (mirrors the V1.0 narrative
# discipline). Word-boundary regex enforcement happens in ``engine.py``.
FORBIDDEN_WORDS: tuple[str, ...] = (
    "will",
    "guaranteed",
    "definitely",
    "certainly",
    "always",
)


_SYSTEM = (
    "You are a careful Vedic astrology consultant answering a specific "
    "question about a specific kundli. You speak warmly and plainly. "
    "You ground every claim in the structured CHART_FINDINGS and "
    "DOCTRINE_PASSAGES provided. You never invent placements, yoga names, "
    "or dasha periods that are not in those sources."
)


CHART_QA_PROMPT_TEMPLATE = """{system}

CRITICAL CONSTRAINTS (HARD):
- ONLY use facts present in CHART_FINDINGS and DOCTRINE_PASSAGES below
- Use "indicates", "may", "suggests", "favors", "tends to", "points toward"
- NEVER use: "will", "guaranteed", "definitely", "certainly", "always"
- If the sources do not support an answer, say so explicitly
- Cite the specific findings and passages you draw from
- Keep your answer concise: 3-5 sentences typical
- Do not invent dates, planet positions, or yoga names not in the sources

QUESTION: {question}

CHART_FINDINGS (from this specific reading):
{findings}

DOCTRINE_PASSAGES (from classical texts):
{passages}

Answer:"""


def _truncate_for_prompt(payload: Any, *, max_chars: int = 3500) -> str:
    """Serialize a JSON-ish object for the prompt, capped at ``max_chars``.

    Defensive against unbounded growth: Ollama's default context window
    is small and a 100-finding chart can otherwise blow it.
    """
    try:
        text = json.dumps(payload, default=str, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return "(payload could not be serialized)"
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... (truncated)"


def _format_passages(passages: list[dict[str, Any]], *, max_chars: int = 2500) -> str:
    """Render a list of passage dicts as a numbered block, capped in length.

    Each passage dict is expected to have ``source``, ``passage``, and
    optionally ``knowledge_doc_id``.
    """
    if not passages:
        return "(no doctrine passages retrieved)"
    parts: list[str] = []
    for i, p in enumerate(passages, start=1):
        source = str(p.get("source", "unknown"))
        text = str(p.get("passage", "")).strip()
        parts.append(f"[{i}] source={source}\n{text}")
    rendered = "\n\n".join(parts)
    if len(rendered) <= max_chars:
        return rendered
    return rendered[:max_chars] + "\n... (truncated)"


def build_chart_qa_prompt(
    question: str,
    findings: list[dict[str, Any]],
    passages: list[dict[str, Any]],
) -> str:
    """Build the LLM prompt for a chart question.

    Args:
        question: The user's free-form question.
        findings: Relevant Finding dicts selected by ``finding_selector``.
        passages: Doctrine passages from the RAG layer (each a dict with
            ``source`` and ``passage`` keys).
    """
    return CHART_QA_PROMPT_TEMPLATE.format(
        system=_SYSTEM,
        question=question.strip(),
        findings=_truncate_for_prompt(findings),
        passages=_format_passages(passages),
    )
