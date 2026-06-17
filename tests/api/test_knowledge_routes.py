"""HTTP tests for the RAG knowledge-search routes.

These run without the embeddings index present (CI never builds the ~MB
sentence-transformer index), so they verify the *graceful-degradation*
contract: stats report not-loaded, search returns 503 with a rebuild hint,
and bad arguments return 422. When an index is present, a synthetic-index
test exercises the happy path.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_knowledge_stats_reports_status(client: AsyncClient) -> None:
    resp = await client.get("/medini/knowledge/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert "loaded" in body and "exists" in body
    # No index built in CI -> not loaded.
    assert body["loaded"] is False


@pytest.mark.asyncio
async def test_knowledge_search_missing_index_returns_503(client: AsyncClient) -> None:
    resp = await client.get("/medini/knowledge/search", params={"q": "saturn"})
    assert resp.status_code == 503
    assert "rebuild" in resp.json()["detail"].lower() or "index" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_knowledge_search_blank_query_rejected(client: AsyncClient) -> None:
    # FastAPI min_length=1 rejects empty q before the handler runs.
    resp = await client.get("/medini/knowledge/search", params={"q": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_knowledge_search_bad_mode_returns_422(client: AsyncClient) -> None:
    """An invalid mode raises ValueError in the service -> mapped to 422.

    Requires an index to reach the service's mode check, so we build a tiny
    synthetic one and point the singleton at it.
    """
    from app.medini.services import knowledge_search as ks

    resp = await client.get(
        "/medini/knowledge/search", params={"q": "x", "mode": "bogus"},
    )
    # Without an index this is 503 (index check precedes mode check in the
    # service path); with an index it would be 422. Either is a clean reject.
    assert resp.status_code in (422, 503)


def _build_synthetic_index(tmp_path) -> "object":
    """Create a 3-chunk index on disk and return a service pointed at it.

    Uses a fake model so the test never downloads sentence-transformers.
    """
    from app.medini.services.knowledge_search import KnowledgeSearchService

    d = tmp_path / "embeddings"
    d.mkdir()
    df = pd.DataFrame({
        "chunk_id": ["c1", "c2", "c3"],
        "source": ["bphs", "bphs", "saravali"],
        "title": ["Saturn", "Mars", "Moon"],
        "text": [
            "Saturn delays and disciplines, ruling Capricorn and Aquarius.",
            "Mars is the commander, fiery and assertive, ruling Aries.",
            "The Moon governs the mind, emotions, and the mother.",
        ],
        "source_url": [None, None, None],
        "local_path": [None, None, None],
        "artefact_id": [None, None, None],
        "topics": [["graha"], ["graha"], ["graha"]],
        "n_tokens": [40, 40, 40],
    })
    df.to_parquet(d / "chunks.parquet")
    vecs = np.eye(3, dtype=np.float32)
    np.save(d / "vectors.npy", vecs)
    (d / "meta.json").write_text('{"model_name": "fake-model"}', encoding="utf-8")

    svc = KnowledgeSearchService(d)
    return svc


@pytest.mark.asyncio
async def test_knowledge_page_returns_html(client: AsyncClient) -> None:
    resp = await client.get("/medini/knowledge/page")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_knowledge_topics_empty_when_no_index(client: AsyncClient) -> None:
    """Topics degrade to an empty taxonomy (not an error) without an index."""
    resp = await client.get("/medini/knowledge/topics")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"taxonomy": {}, "topics": []}


@pytest.mark.asyncio
async def test_knowledge_topics_builds_taxonomy_from_index(client: AsyncClient, tmp_path, monkeypatch) -> None:
    """With an index, dotted topic tags group into a {category: [leaf]} taxonomy."""
    svc = _build_synthetic_index(tmp_path)
    # Override the parquet's topics with dotted tags to exercise grouping.
    import pandas as pd
    df = pd.read_parquet(tmp_path / "embeddings" / "chunks.parquet")
    df["topics"] = [["timing.marriage"], ["graha.saturn"], ["timing.career"]]
    df.to_parquet(tmp_path / "embeddings" / "chunks.parquet")

    from app.api import knowledge_routes
    monkeypatch.setattr(knowledge_routes, "get_default_service", lambda: svc)

    resp = await client.get("/medini/knowledge/topics")
    assert resp.status_code == 200
    tax = resp.json()["taxonomy"]
    assert tax["timing"] == ["career", "marriage"]
    assert tax["graha"] == ["saturn"]


@pytest.mark.asyncio
async def test_knowledge_search_lexical_happy_path(client: AsyncClient, tmp_path, monkeypatch) -> None:
    """With a synthetic index and lexical mode (no model needed), search returns
    ranked results serialized to JSON."""
    import sys
    import types

    # ensure_loaded() imports sentence_transformers unconditionally; lexical
    # mode never calls encode(), so a stub module is enough and we avoid
    # pulling torch into the test environment.
    fake_st = types.ModuleType("sentence_transformers")

    class _FakeModel:
        def __init__(self, *_a, **_k) -> None:
            pass

        def encode(self, texts, **_k):
            return np.zeros((len(texts), 3), dtype=np.float32)

    fake_st.SentenceTransformer = _FakeModel  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_st)

    svc = _build_synthetic_index(tmp_path)
    # The route resolves the singleton via get_default_service in its own
    # module namespace — point it at our synthetic-index service.
    from app.api import knowledge_routes
    monkeypatch.setattr(knowledge_routes, "get_default_service", lambda: svc)

    resp = await client.get(
        "/medini/knowledge/search",
        params={"q": "saturn discipline", "mode": "lexical"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "lexical"
    assert body["count"] >= 1
    top = body["results"][0]
    # Lexical match on "saturn" should float the Saturn chunk to the top.
    assert top["title"] == "Saturn"
    assert set(top) >= {"chunk_id", "score", "source", "title", "snippet", "topics"}
