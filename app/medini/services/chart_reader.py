"""Chart Reader — synthesize a doctrine-grounded reading for one person.

A pivot away from population statistics (which Round 9 closed as null)
toward what classical astrologers actually do: take one chart, look at
the structural elements, retrieve relevant doctrine passages, and
narrate.

Design:

1. **Compute** the chart via ``app.core.ephemeris_engine.calculate_all_charts``.
2. **Extract** key reading elements (ascendant, sun/moon/lagna lord,
   current MD/AD/PD, dignities, active yogas).
3. **Retrieve** relevant RAG passages for each element using the
   knowledge-library service.
4. **Synthesize** via the LLM client (Ollama when enabled, deterministic
   templated fallback otherwise) into a structured multi-section
   reading with inline [N] citations.

The output is a structured ``Reading`` dataclass with sections + cited
sources. Designed for both the production endpoint AND a research-test
harness comparing chart-grounded vs chart-blind LLM predictions.

Failure modes are silent: if Ollama isn't available, falls back to the
deterministic template. If the RAG isn't loaded, citations come back
empty but the structural sections still render. The reading never 500s.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings
from app.core.yogas import detect_yogas
from app.llm.client import LLMClient, OllamaClient, OllamaUnavailable
from app.medini.services.knowledge_search import (
    KnowledgeSearchService,
    SearchResult,
    get_default_service,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Citation:
    """One doctrine passage attached to a reading section."""
    source: str
    title: str
    snippet: str
    source_url: str | None
    local_path: str | None
    score: float


@dataclass(frozen=True)
class ReadingSection:
    """One section of the reading (ascendant / dasha / yogas / etc.)."""
    title: str
    text: str
    citations: tuple[Citation, ...] = ()


@dataclass(frozen=True)
class Reading:
    """A full chart reading."""
    chart_summary: dict[str, Any]  # asc, sun, moon, md/ad/pd, yogas
    sections: tuple[ReadingSection, ...]
    source: str  # "llm" or "deterministic"
    model: str | None
    n_citations_total: int


# --------------------------------------------------------------------------- #
# Chart-element extraction                                                     #
# --------------------------------------------------------------------------- #

def _extract_reading_elements(chart: dict[str, Any]) -> dict[str, Any]:
    """Pull the structural elements a reading is built around.

    Returns a dict with: ascendant, sun, moon, md_lord, ad_lord (if any),
    pd_lord (if any), yogas (detected from d1+ascendant).
    """
    asc = chart.get("ascendant", {})
    d1 = chart.get("d1", {})
    md = chart.get("current_mahadasha", {})
    out: dict[str, Any] = {
        "ascendant": asc,
        "sun": d1.get("Sun", {}),
        "moon": d1.get("Moon", {}),
        "current_mahadasha": md,
        "current_antardasha": chart.get("current_antardasha", {}),
        "current_pratyantar": chart.get("current_pratyantar", {}),
    }
    # Detect yogas
    if asc and d1:
        try:
            out["yogas"] = detect_yogas(d1, asc)
        except Exception as e:
            logger.warning("yoga detection failed: %s", e)
            out["yogas"] = []
    else:
        out["yogas"] = []
    return out


# --------------------------------------------------------------------------- #
# RAG retrieval per reading element                                            #
# --------------------------------------------------------------------------- #

def _retrieve_section(
    service: KnowledgeSearchService | None,
    query: str,
    *,
    topic: str | None = None,
    top: int = 3,
) -> tuple[Citation, ...]:
    """Run one RAG query; return citations. Silent failure → empty tuple."""
    if service is None:
        return ()
    try:
        results = service.search(
            query, mode="hybrid", topic=topic, top=top,
            min_tokens=40, snippet_chars=280,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("RAG retrieval failed for '%s...': %s",
                       query[:60], exc)
        return ()
    return tuple(
        Citation(
            source=r.source, title=r.title, snippet=r.snippet,
            source_url=r.source_url, local_path=r.local_path,
            score=round(r.score, 3),
        )
        for r in results
    )


def _build_section_queries(elements: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-section query construction. Each entry: title + query + topic-filter."""
    asc_sign = (elements.get("ascendant") or {}).get("sign_name", "")
    sun_sign = (elements.get("sun") or {}).get("sign_name", "")
    moon_sign = (elements.get("moon") or {}).get("sign_name", "")
    moon_nak = (elements.get("moon") or {}).get("nakshatra", {}).get("name", "")
    md_lord = (elements.get("current_mahadasha") or {}).get("mahadasha_lord", "")
    ad_lord = (elements.get("current_antardasha") or {}).get("antardasha_lord", "")
    yogas = elements.get("yogas") or []
    yoga_names = " ".join(y["name"] for y in yogas[:5])

    sections: list[dict[str, Any]] = []
    if asc_sign:
        sections.append({
            "title": f"Ascendant: {asc_sign}",
            "query": f"{asc_sign} ascendant lagna native characteristics personality",
            "topic": "primitives.houses",
        })
    if sun_sign:
        sections.append({
            "title": f"Sun in {sun_sign}",
            "query": f"Sun in {sun_sign} effects vitality soul",
            "topic": "primitives.planets",
        })
    if moon_sign:
        sections.append({
            "title": f"Moon in {moon_sign}" + (f" ({moon_nak})" if moon_nak else ""),
            "query": f"Moon in {moon_sign} mind emotions" + (
                f" {moon_nak} nakshatra" if moon_nak else ""
            ),
            "topic": "primitives.planets",
        })
    if md_lord:
        ad_part = f" antardasha of {ad_lord}" if ad_lord else ""
        sections.append({
            "title": f"Current Mahadasha: {md_lord}{(' / ' + ad_lord) if ad_lord else ''}",
            "query": f"{md_lord} mahadasha results effects{ad_part}",
            "topic": "dasha.vimshottari",
        })
    if yoga_names:
        sections.append({
            "title": f"Active yogas: {', '.join(y['name'] for y in yogas[:5])}",
            "query": f"{yoga_names} yoga effects",
            "topic": None,  # yogas span multiple topic branches
        })
    return sections


# --------------------------------------------------------------------------- #
# Synthesis (LLM + deterministic fallback)                                     #
# --------------------------------------------------------------------------- #

def _build_section_prompt(
    section_meta: dict[str, Any],
    citations: tuple[Citation, ...],
    chart_summary: dict[str, Any],
) -> str:
    """Per-section LLM prompt: chart facts + citations + tight tone-guard."""
    lines = [
        f"SECTION: {section_meta['title']}",
        "",
        "CHART FACTS",
    ]
    asc = chart_summary.get("ascendant", {})
    lines.append(f"  Ascendant: {asc.get('sign_name', '?')} "
                 f"{asc.get('degree_in_sign', 0):.1f}°")
    sun = chart_summary.get("sun", {})
    lines.append(f"  Sun: {sun.get('sign_name', '?')} "
                 f"{sun.get('degree_in_sign', 0):.1f}° (House {sun.get('house', '?')})")
    moon = chart_summary.get("moon", {})
    lines.append(f"  Moon: {moon.get('sign_name', '?')} "
                 f"{moon.get('degree_in_sign', 0):.1f}° (House {moon.get('house', '?')})")
    md = chart_summary.get("current_mahadasha", {})
    if md.get("mahadasha_lord"):
        lines.append(f"  MD: {md['mahadasha_lord']} ({md.get('start_date', '?')} → "
                     f"{md.get('end_date', '?')})")
    lines.append("")
    if citations:
        lines.append(f"DOCTRINE PASSAGES ({len(citations)}):")
        for i, c in enumerate(citations, 1):
            lines.append(f"  [{i}] {c.source} — {c.title[:70]}")
            lines.append(f"      \"{c.snippet[:280]}\"")
    else:
        lines.append("DOCTRINE PASSAGES: (none retrieved)")
    lines.extend([
        "",
        "TASK",
        "  Write a focused 2-3 sentence interpretation of THIS SECTION's",
        "  topic (not the whole chart). Use only:",
        "    (a) the EVENT FACTS above as ground truth about this chart",
        "    (b) the cited DOCTRINE PASSAGES (cite via [N])",
        "  Be concrete and conservative. DO NOT invent placements or",
        "  yoga claims that aren't in the facts or citations. No",
        "  'energies', no disclaimers. Start with the literal prefix",
        "  '[GROUNDED]:' when at least one citation is on-topic;",
        "  '[GENERAL]:' if no citation applies and you fall back to",
        "  general principles.",
        "",
        "OUTPUT (2-3 sentences):",
    ])
    return "\n".join(lines)


def _deterministic_section(
    section_meta: dict[str, Any],
    citations: tuple[Citation, ...],
) -> str:
    """Templated fallback when LLM unavailable."""
    head = f"This section covers {section_meta['title']}."
    if not citations:
        return head + " No doctrine citations available."
    body = " " + " ".join(
        f"[{i}] {c.source} states: \"{c.snippet[:120]}...\""
        for i, c in enumerate(citations[:2], 1)
    )
    return head + body


def _llm_section(
    section_meta: dict[str, Any],
    citations: tuple[Citation, ...],
    chart_summary: dict[str, Any],
    client: LLMClient,
) -> tuple[str, str]:
    """Returns (text, actual_source). Silent fallback to deterministic on error."""
    prompt = _build_section_prompt(section_meta, citations, chart_summary)
    try:
        text = client.complete(prompt).strip()
        # Strip optional mode marker
        for prefix in ("[GROUNDED]:", "[GROUNDED]", "[GENERAL]:", "[GENERAL]"):
            if text.upper().startswith(prefix):
                text = text[len(prefix):].strip()
                break
        return text or _deterministic_section(section_meta, citations), "llm"
    except OllamaUnavailable:
        logger.info("LLM unavailable for section %s; using deterministic",
                    section_meta.get("title"))
        return _deterministic_section(section_meta, citations), "deterministic"
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM call failed for section %s: %s",
                       section_meta.get("title"), exc)
        return _deterministic_section(section_meta, citations), "deterministic"


# --------------------------------------------------------------------------- #
# Public                                                                       #
# --------------------------------------------------------------------------- #

def _default_llm_client() -> LLMClient | None:
    if not settings.OLLAMA_ENABLED:
        return None
    return OllamaClient(
        host=settings.OLLAMA_HOST,
        model=settings.OLLAMA_MODEL,
        timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
    )


def read_chart(
    chart: dict[str, Any],
    *,
    rag_service: KnowledgeSearchService | None = None,
    llm_client: LLMClient | None = None,
    top_citations_per_section: int = 3,
) -> Reading:
    """Synthesize a full doctrine-grounded reading for one chart.

    Args:
      chart: output of ``calculate_all_charts``.
      rag_service: knowledge-library RAG service; None → no citations.
      llm_client: LLM client; None → use settings default; failure → deterministic.
      top_citations_per_section: number of doctrine passages retrieved per section.
    """
    elements = _extract_reading_elements(chart)
    section_metas = _build_section_queries(elements)

    if rag_service is None:
        try:
            rag_service = get_default_service()
        except Exception:
            rag_service = None

    if llm_client is None:
        llm_client = _default_llm_client()

    actual_source = "deterministic"
    out_sections: list[ReadingSection] = []
    total_cit = 0
    for sm in section_metas:
        citations = _retrieve_section(
            rag_service, sm["query"], topic=sm.get("topic"),
            top=top_citations_per_section,
        )
        total_cit += len(citations)
        if llm_client is not None:
            text, src = _llm_section(sm, citations, elements, llm_client)
            if src == "llm":
                actual_source = "llm"
        else:
            text = _deterministic_section(sm, citations)
        out_sections.append(
            ReadingSection(title=sm["title"], text=text, citations=citations)
        )

    model_name = getattr(llm_client, "model", None) if actual_source == "llm" else None
    return Reading(
        chart_summary=elements,
        sections=tuple(out_sections),
        source=actual_source,
        model=str(model_name) if model_name else None,
        n_citations_total=total_cit,
    )
