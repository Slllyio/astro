"""RAG citation enrichment for mundane forecast events.

For each event, queries the knowledge-library RAG index to attach the
top-N doctrine passages that discuss that exact phenomenon. Pulls from
the same ``KnowledgeSearchService`` singleton used by /interpret citations
so the model + vectors are loaded only once per process.

Query construction is event-shape specific:

* INGRESS:    "{planet} ingress {sign} effects mundane"
* STATION:    "{planet} retrograde station effects" (with topic filter)
* CONJUNCTION: "{a} {b} conjunction effects yoga"
* NEW_MOON / FULL_MOON: "new moon full moon {sign} effects"
* ECLIPSE:    "{family} eclipse {nakshatra} effects mundane"

Always returns silently on failure (missing index, model load issue) — the
forecast must continue to work when the corpus isn't present locally.
"""
from __future__ import annotations

import logging
from typing import Any

from app.medini.services.knowledge_search import (
    KnowledgeSearchService,
    SearchResult,
    get_default_service,
)

logger = logging.getLogger(__name__)

# Trim citations tighter than chart-interpretation citations — the forecast
# page shows many events at once, so per-event snippets need to stay short.
_FORECAST_SNIPPET_CHARS = 250


def _build_query(event: dict[str, Any]) -> tuple[str, str | None]:
    """Return (query, topic_filter or None) tuned to one event's shape."""
    t = event.get("type")

    if t == "INGRESS":
        planet = event.get("planet", "")
        to_sign = event.get("to_sign", "")
        return (
            f"{planet} ingress {to_sign} effects mundane",
            None,  # ingress material spans many topic leaves
        )

    if t == "STATION":
        planet = event.get("planet", "")
        to_state = event.get("to_state", "")
        return (
            f"{planet} {to_state} station retrograde effects",
            None,
        )

    if t == "CONJUNCTION":
        a, b = event.get("planet_a", ""), event.get("planet_b", "")
        return (
            f"{a} {b} conjunction yoga effects sambandha",
            None,  # could be 'yogas' topic but conjunction passages live
                   # in many places (planetary, yogas, dasha-result chapters)
        )

    if t in {"NEW_MOON", "FULL_MOON"}:
        label = "new moon amavasya" if t == "NEW_MOON" else "full moon purnima"
        sign = event.get("sign", "")
        return (
            f"{label} {sign} effects mundane",
            "primitives.panchanga",
        )

    if t == "ECLIPSE":
        family = event.get("family", "").lower()
        nak = event.get("luminary_nakshatra", "")
        return (
            f"{family} eclipse {nak} grahana effects mundane",
            None,
        )

    return ("Vedic mundane astrology event", None)


def _result_to_citation(r: SearchResult) -> dict[str, Any]:
    """Tighter shape than llm/citations.Citation — forecast page renders
    many events so every byte counts."""
    snippet = r.snippet
    if len(snippet) > _FORECAST_SNIPPET_CHARS:
        snippet = snippet[:_FORECAST_SNIPPET_CHARS].rstrip() + "..."
    return {
        "source": r.source,
        "title": r.title,
        "snippet": snippet,
        "source_url": r.source_url,
        "local_path": r.local_path,
        "score": round(r.score, 3),
    }


def citations_for_event(
    event: dict[str, Any],
    *,
    top: int = 2,
    service: KnowledgeSearchService | None = None,
) -> list[dict[str, Any]]:
    """Return up to ``top`` citations for one event. Never raises.

    Silent failure means a forecast page can render in full even when the
    RAG index is missing or the model is broken — citations just appear
    as empty lists per event.
    """
    if service is None:
        service = get_default_service()
    query, topic = _build_query(event)
    try:
        results = service.search(
            query, mode="hybrid", topic=topic, top=top, min_tokens=40,
            snippet_chars=_FORECAST_SNIPPET_CHARS,
        )
    except Exception as exc:  # noqa: BLE001 - intentional swallow at boundary
        logger.warning("forecast citation lookup failed for %s: %s",
                       event.get("type"), exc)
        return []
    return [_result_to_citation(r) for r in results]


def annotate_events(
    events: list[dict[str, Any]],
    *,
    top: int = 2,
    service: KnowledgeSearchService | None = None,
) -> list[dict[str, Any]]:
    """Attach a ``citations`` field to each event (immutable copy).

    Calls the RAG once per event sequentially — for a 30-day calendar with
    ~10-30 events this is < 1s after the model is warm. If perf becomes an
    issue later, batch-encoding all queries into one model call would
    parallelise the hot path.
    """
    if service is None:
        service = get_default_service()
    annotated: list[dict[str, Any]] = []
    for e in events:
        cits = citations_for_event(e, top=top, service=service)
        annotated.append({**e, "citations": cits})
    return annotated
