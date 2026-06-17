"""HTTP endpoints for RAG search over the knowledge-library corpus.

A thin router over ``app.medini.services.knowledge_search`` — the process-wide
``KnowledgeSearchService`` singleton loads its index + sentence-transformer
model lazily on the first search. This module just maps query params onto
``service.search(...)`` and serializes the frozen ``SearchResult`` tuples to
JSON.

Graceful degradation: if the embeddings index hasn't been built, the service
raises ``IndexUnavailable`` and we return 503 with a rebuild hint rather than
500ing. Invalid arguments (bad ``mode``, empty ``q``) surface as 422.

Public — no auth, consistent with the rest of the Medini surface.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.medini.services.knowledge_search import (
    IndexUnavailable,
    get_default_service,
)

knowledge_router = APIRouter(
    prefix="/medini/knowledge", tags=["Knowledge Library (RAG)"],
)

# Templates live alongside the medini module (same convention as medini_routes).
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "medini" / "templates"


@knowledge_router.get("/stats")
async def knowledge_stats() -> dict:
    """Index metadata. Safe before load — reports ``loaded``/``exists`` without
    paying the model-load cost."""
    return get_default_service().stats()


@knowledge_router.get("/topics")
async def knowledge_topics() -> dict:
    """Topic taxonomy for the search-filter dropdown.

    Topic tags are dotted paths (``category.leaf``); this groups them into a
    ``{category: [leaf, ...]}`` taxonomy. Degrades to an empty taxonomy (not an
    error) when the index is absent, so the page's dropdown just shows "(any)".
    """
    try:
        topics = get_default_service().topics()
    except IndexUnavailable:
        return {"taxonomy": {}, "topics": []}

    taxonomy: dict[str, list[str]] = {}
    for tag in topics:
        category, _, leaf = tag.partition(".")
        if not leaf:
            category, leaf = "general", tag
        bucket = taxonomy.setdefault(category, [])
        if leaf not in bucket:
            bucket.append(leaf)
    for leaves in taxonomy.values():
        leaves.sort()
    return {"taxonomy": taxonomy, "topics": list(topics)}


@knowledge_router.get("/page", response_class=HTMLResponse)
async def knowledge_page() -> HTMLResponse:
    """The doctrine-search UI. Fetches /stats, /topics, and /search client-side."""
    html_path = _TEMPLATES_DIR / "knowledge_search.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge search template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@knowledge_router.get("/search")
async def knowledge_search(
    q: str = Query(..., min_length=1, description="Search query"),
    mode: str = Query("hybrid", description="semantic | hybrid | lexical"),
    topic: str | None = Query(None, description="Filter to a single topic"),
    source: str | None = Query(None, description="Filter to a single source"),
    top: int = Query(10, ge=1, le=50, description="Number of results"),
    min_tokens: int = Query(30, ge=0, description="Drop chunks shorter than this"),
    snippet_chars: int = Query(400, ge=1, le=2000, description="Snippet length"),
) -> dict:
    """Ranked chunks for ``q``. Blends semantic + lexical scoring per ``mode``.

    Returns 503 if the index is missing (with a rebuild command), 422 for an
    invalid ``mode`` or empty query.
    """
    service = get_default_service()
    try:
        results = service.search(
            q,
            mode=mode,  # type: ignore[arg-type]  # validated inside the service
            topic=topic,
            source=source,
            top=top,
            min_tokens=min_tokens,
            snippet_chars=snippet_chars,
        )
    except IndexUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc),
        ) from exc

    return {
        "query": q,
        "mode": mode,
        "count": len(results),
        "results": [asdict(r) for r in results],
    }
