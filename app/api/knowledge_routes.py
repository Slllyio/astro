"""HTTP endpoints for the knowledge-library RAG search surface.

Mounted at ``/medini/knowledge/*`` (groups under the Medini umbrella since
the corpus is the doctrine substrate that grounds Medini's predictions and
narratives — but stays in its own router so the file doesn't bloat).

Endpoints:

* GET /medini/knowledge/stats        — index loaded?, n_chunks, model, n_sources
* GET /medini/knowledge/search       — ranked chunks (query, mode, filters)
* GET /medini/knowledge/topics       — taxonomy listing (for UI dropdowns)
* GET /medini/knowledge/page         — minimal HTML search UI

The index is loaded lazily on the first search call (~2-3 s for the model).
A request that arrives while the embeddings file is missing returns 503
with rebuild instructions, not 500 — the app stays up even if the corpus
isn't built locally.

Rate-limited at the slowapi default profile (per-IP) — the model load is the
expensive bit but a single search is < 100 ms once warm; we don't need
per-account quotas yet.
"""
from __future__ import annotations

import asyncio
import dataclasses
import logging
from pathlib import Path
from typing import Literal

import yaml
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.medini.services.knowledge_search import (
    IndexUnavailable,
    SearchResult,
    get_default_service,
)

logger = logging.getLogger(__name__)

knowledge_router = APIRouter(
    prefix="/medini/knowledge",
    tags=["Knowledge Library (RAG)"],
)

# Templates + taxonomy live alongside the library data files so the same
# path conventions apply as the kurma widget / cartography pages.
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "medini" / "templates"
_TOPICS_YAML = Path("data/knowledge_library/topics.yaml")


def _result_to_dict(r: SearchResult) -> dict:
    """Frozen dataclass → JSON-safe dict for the response payload."""
    return dataclasses.asdict(r)


@knowledge_router.get("/stats")
async def knowledge_stats() -> dict:
    """Report whether the index is built + loaded, with chunk/source counts.

    Cheap — never triggers the model load. If the index files are present
    on disk but ``loaded=False``, the first search call will warm them.
    """
    service = get_default_service()
    return service.stats()


@knowledge_router.get("/topics")
async def list_topics() -> dict:
    """Return the taxonomy from ``topics.yaml`` as ``{category: [leaf, ...]}``.

    The search UI uses this to populate the topic-filter dropdown; clients
    that want richer metadata (descriptions, BPHS refs) can read the YAML
    directly. We expose only the structural shape here.
    """
    if not _TOPICS_YAML.exists():
        # Library not built locally — return empty taxonomy so the UI still
        # renders, just without the dropdown options.
        return {"taxonomy": {}, "n_topics": 0}
    taxonomy_raw = yaml.safe_load(_TOPICS_YAML.read_text(encoding="utf-8")) or {}
    taxonomy = {
        category: sorted(leaves.keys())
        for category, leaves in taxonomy_raw.items()
    }
    n_topics = sum(len(v) for v in taxonomy.values())
    return {"taxonomy": taxonomy, "n_topics": n_topics}


@knowledge_router.get("/search")
async def search_knowledge(
    q: str = Query(..., min_length=1, max_length=400, description="Query text"),
    mode: Literal["semantic", "hybrid", "lexical"] = "hybrid",
    topic: str | None = Query(None, description="e.g. dasha.vimshottari"),
    source: str | None = Query(None, description="Substring match: e.g. bphs"),
    top: int = Query(10, ge=1, le=50),
    min_tokens: int = Query(30, ge=0),
    snippet_chars: int = Query(400, ge=50, le=2000),
) -> dict:
    """Search the knowledge library and return ranked chunks.

    The model + vectors are loaded on the first call (~2-3 s warmup); all
    subsequent calls return in < 100 ms. The endpoint runs the search
    sync function on a worker thread so the event loop stays responsive
    during the embed step.
    """
    service = get_default_service()

    def _search() -> tuple[SearchResult, ...]:
        return service.search(
            q, mode=mode, topic=topic, source=source,
            top=top, min_tokens=min_tokens, snippet_chars=snippet_chars,
        )

    try:
        # asyncio.to_thread offloads the (potentially slow) first-call model
        # load + encode so the event loop keeps serving other requests.
        results = await asyncio.to_thread(_search)
    except IndexUnavailable as exc:
        # 503 means "we know how to do this but the substrate isn't ready" —
        # rebuild instructions go in the body so the operator can self-serve.
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": str(exc),
                "hint": (
                    "Build the knowledge library and RAG index first: "
                    "`python -m app.medini.etl.build_knowledge_manifest && "
                    "python -m app.medini.ml.build_rag_index`"
                ),
            },
        ) from exc
    except ValueError as exc:
        # Bad mode / empty query: 400 with the message, not 500.
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=str(exc),
        ) from exc

    return {
        "query": q,
        "mode": mode,
        "filters": {
            "topic": topic, "source": source, "min_tokens": min_tokens,
        },
        "n_results": len(results),
        "results": [_result_to_dict(r) for r in results],
    }


@knowledge_router.get("/page", response_class=HTMLResponse)
async def knowledge_page() -> HTMLResponse:
    """Server-rendered HTML search page.

    Plain ``fetch()`` against the JSON endpoint — no framework, same shape
    as the other Medini pages (kurma-widget, cartography). The page renders
    even when the index isn't loaded; submitting a search will then return
    a 503 and the UI surfaces the rebuild hint.
    """
    html_path = _TEMPLATES_DIR / "knowledge_search.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge search template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
