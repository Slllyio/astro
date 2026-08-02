"""Integration tests for /medini/knowledge/* HTTP endpoints.

Strategy:

* Replace ``app.api.knowledge_routes.get_default_service`` with a fixture
  that returns a KnowledgeSearchService pointed at a synthetic tmp-dir
  mini-index (same fixture as the service unit tests, vendored here so the
  two test files stay independent).
* ``stub_st`` injects a fake sentence-transformer module so the route's
  first search doesn't try to download a real model.
* For the "index missing" path we don't write any embeddings files —
  the route should map IndexUnavailable to a 503 with the rebuild hint
  in the body, not 500.

The HTML page test reads the static template — it has no JS-runtime
coverage; that's manual / e2e territory and out of scope for this unit
test suite.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.medini.services.knowledge_search import (
    KnowledgeSearchService,
    reset_default_service,
)


_CHUNKS = [
    {
        "chunk_id": "c0", "artefact_id": "a0", "source": "bphs",
        "title": "BPHS Ch.46", "source_url": "http://x/bphs",
        "local_path": "/local/bphs.md",
        "text": "vimshottari dasha mahadasha results",
        "n_tokens": 60,
        "topics": np.array(["dasha.vimshottari"], dtype=object),
    },
    {
        "chunk_id": "c1", "artefact_id": "a1", "source": "frawley",
        "title": "Frawley Gemstones", "source_url": "http://x/frawley",
        "local_path": "/local/frawley.md",
        "text": "gemstones planetary remedies ruby pearl",
        "n_tokens": 70,
        "topics": np.array(["remedies.gemstones"], dtype=object),
    },
]
_VECTORS = np.eye(2, dtype=np.float32)


class _StubST:
    def __init__(self, name: str) -> None:
        self.name = name

    def encode(self, queries, convert_to_numpy=True, normalize_embeddings=True):
        out = np.zeros((len(queries), 2), dtype=np.float32)
        for i, q in enumerate(queries):
            out[i, 0 if "vimshottari" in q.lower() or "dasha" in q.lower() else 1] = 1.0
        return out


@pytest.fixture
def tmp_index(tmp_path: Path) -> Path:
    idx = tmp_path / "embeddings"
    idx.mkdir()
    pd.DataFrame(_CHUNKS).to_parquet(idx / "chunks.parquet", index=False)
    np.save(idx / "vectors.npy", _VECTORS)
    (idx / "meta.json").write_text(
        json.dumps({"model_name": "stub", "vector_dim": 2}), encoding="utf-8",
    )
    return idx


@pytest.fixture
def stub_st(monkeypatch):
    mod = types.ModuleType("sentence_transformers")
    mod.SentenceTransformer = _StubST  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", mod)
    yield


@pytest.fixture
def loaded_service(tmp_index: Path, monkeypatch, stub_st) -> KnowledgeSearchService:
    """Build a service pointed at the tmp index, patch the route module's
    singleton getter so every endpoint call returns this instance."""
    svc = KnowledgeSearchService(tmp_index)
    monkeypatch.setattr(
        "app.api.knowledge_routes.get_default_service", lambda: svc,
    )
    reset_default_service()
    yield svc
    reset_default_service()


@pytest.fixture
def missing_service(tmp_path: Path, monkeypatch) -> KnowledgeSearchService:
    """Service pointed at an empty dir — index_exists() == False, search
    raises IndexUnavailable, route must 503."""
    empty = tmp_path / "no-embeddings"
    empty.mkdir()
    svc = KnowledgeSearchService(empty)
    monkeypatch.setattr(
        "app.api.knowledge_routes.get_default_service", lambda: svc,
    )
    reset_default_service()
    yield svc
    reset_default_service()


# --------------------------------------------------------------------------- #
# /stats                                                                       #
# --------------------------------------------------------------------------- #

class TestStatsEndpoint:
    @pytest.mark.asyncio
    async def test_stats_when_index_missing(self, client, missing_service):
        """Index dir empty → stats reports loaded=False, exists=False, no 5xx."""
        resp = await client.get("/medini/knowledge/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["loaded"] is False
        assert body["exists"] is False

    @pytest.mark.asyncio
    async def test_stats_does_not_trigger_load(self, client, loaded_service):
        """Hitting /stats must NOT warm the model — service.is_loaded stays
        False until a search arrives. This keeps health checks cheap."""
        resp = await client.get("/medini/knowledge/stats")
        assert resp.status_code == 200
        assert loaded_service.is_loaded is False
        body = resp.json()
        assert body["loaded"] is False
        assert body["exists"] is True


# --------------------------------------------------------------------------- #
# /search                                                                      #
# --------------------------------------------------------------------------- #

class TestSearchEndpoint:
    @pytest.mark.asyncio
    async def test_search_returns_ranked_results(self, client, loaded_service):
        """Happy path: query → 200 with ranked results envelope + filters echo."""
        resp = await client.get(
            "/medini/knowledge/search",
            params={"q": "vimshottari dasha", "mode": "semantic", "top": 5},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["query"] == "vimshottari dasha"
        assert body["mode"] == "semantic"
        assert body["n_results"] >= 1
        # Top hit should be the dasha chunk
        top = body["results"][0]
        assert top["chunk_id"] == "c0"
        assert top["source"] == "bphs"
        assert "topics" in top
        # Filters echo lets the UI know exactly what it asked for
        assert body["filters"] == {
            "topic": None, "source": None, "min_tokens": 30,
        }

    @pytest.mark.asyncio
    async def test_search_503_when_index_missing(self, client, missing_service):
        """Index absent → 503 with rebuild hint, not 500."""
        resp = await client.get(
            "/medini/knowledge/search", params={"q": "anything"},
        )
        assert resp.status_code == 503
        body = resp.json()
        assert "RAG index missing" in body["detail"]["error"]
        assert "build_rag_index" in body["detail"]["hint"]

    @pytest.mark.asyncio
    async def test_search_empty_query_rejected_by_pydantic(
        self, client, loaded_service,
    ):
        """min_length=1 on Query → 422 before service.search runs."""
        resp = await client.get("/medini/knowledge/search", params={"q": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_search_top_clamped(self, client, loaded_service):
        """top is bounded [1, 50]; out-of-range → 422."""
        resp = await client.get(
            "/medini/knowledge/search",
            params={"q": "anything", "top": 999},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_search_unknown_mode_rejected(self, client, loaded_service):
        """Literal type on `mode` → 422 for any non-allowed value."""
        resp = await client.get(
            "/medini/knowledge/search",
            params={"q": "anything", "mode": "magic"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_search_topic_filter_applied(self, client, loaded_service):
        """A topic filter that excludes the top semantic hit must yield 0
        or only-other-topic results."""
        resp = await client.get(
            "/medini/knowledge/search",
            params={"q": "vimshottari", "topic": "remedies.gemstones"},
        )
        assert resp.status_code == 200
        body = resp.json()
        for r in body["results"]:
            assert "remedies.gemstones" in r["topics"]


# --------------------------------------------------------------------------- #
# /topics                                                                      #
# --------------------------------------------------------------------------- #

class TestTopicsEndpoint:
    @pytest.mark.asyncio
    async def test_topics_returns_taxonomy_shape(self, client):
        """Topics endpoint reads the real topics.yaml when present; if not,
        returns {taxonomy: {}, n_topics: 0}. Either is acceptable — we just
        verify the shape so clients can rely on it."""
        resp = await client.get("/medini/knowledge/topics")
        assert resp.status_code == 200
        body = resp.json()
        assert "taxonomy" in body
        assert "n_topics" in body
        assert isinstance(body["taxonomy"], dict)
        for cat, leaves in body["taxonomy"].items():
            assert isinstance(cat, str)
            assert isinstance(leaves, list)
            assert all(isinstance(l, str) for l in leaves)


# --------------------------------------------------------------------------- #
# /page                                                                        #
# --------------------------------------------------------------------------- #

class TestKnowledgePage:
    @pytest.mark.asyncio
    async def test_page_renders_html(self, client):
        """Static template — endpoint reads + returns it. 200 + text/html.

        The title assertion tracks the Pothi redesign (2026-08-03): the page is now
        'ज्ञानकोशः — Doctrine Search', not the old 'Knowledge Library Search' banner."""
        resp = await client.get("/medini/knowledge/page")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Doctrine Search" in resp.text
