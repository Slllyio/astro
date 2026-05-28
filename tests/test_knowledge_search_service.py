"""Unit tests for app.medini.services.knowledge_search.

Builds a synthetic 4-chunk RAG index in a tmp dir + injects a stub
SentenceTransformer so the tests run without downloading a real model.
The stub returns deterministic vectors keyed to specific query words so
the cosine-similarity ranking is predictable.

Covers:
  * index_exists / stats (pre + post load)
  * IndexUnavailable when files are absent
  * search() in all three modes
  * topic + source + min_tokens filters
  * empty-mask short-circuit
  * thread-safety of ensure_loaded (concurrent first-callers don't double-load)
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.medini.services.knowledge_search import (
    IndexUnavailable,
    KnowledgeSearchService,
    SearchResult,
    get_default_service,
    reset_default_service,
)


# --------------------------------------------------------------------------- #
# Synthetic mini-index                                                         #
# --------------------------------------------------------------------------- #

# 4-dim space chosen so each chunk lives on its own axis — easy to verify
# which chunk a query is "closest" to by which axis the query vector picks.
_CHUNKS: list[dict] = [
    {
        "chunk_id": "c0", "artefact_id": "a0", "source": "bphs",
        "title": "BPHS Ch.46 — Vimshottari", "source_url": "http://x/bphs",
        "local_path": "/local/bphs.md",
        "text": "vimshottari dasha mahadasha results lord period",
        "n_tokens": 60,
        "topics": np.array(["dasha.vimshottari"], dtype=object),
    },
    {
        "chunk_id": "c1", "artefact_id": "a1", "source": "phaladeepika",
        "title": "Phaladeepika — Yoga chapter", "source_url": "http://x/phala",
        "local_path": "/local/phala.md",
        "text": "raja yoga panchamahapurusha effects benefic combinations",
        "n_tokens": 80,
        "topics": np.array(["yogas.raja_yogas"], dtype=object),
    },
    {
        "chunk_id": "c2", "artefact_id": "a2", "source": "frawley",
        "title": "Frawley — Gemstones", "source_url": "http://x/frawley",
        "local_path": "/local/frawley.md",
        "text": "gemstones planetary remedies ruby pearl coral diamond",
        "n_tokens": 70,
        "topics": np.array(["remedies.gemstones"], dtype=object),
    },
    {
        "chunk_id": "c3", "artefact_id": "a3", "source": "bphs",
        "title": "BPHS Ch.7 — Short", "source_url": "http://x/bphs2",
        "local_path": "/local/bphs2.md",
        "text": "tiny chunk",
        "n_tokens": 10,  # below default min_tokens=30 so it should filter out
        "topics": np.array(["primitives.planets"], dtype=object),
    },
]

# One-hot vectors so cosine(query_axis_i, chunk_i) == 1.0
_VECTORS = np.eye(4, dtype=np.float32)


class _StubSentenceTransformer:
    """Test stand-in for sentence_transformers.SentenceTransformer.

    Returns a one-hot vector pointing at axis N where N is the first matched
    keyword in the query. Lets the test pre-compute which axis (= which
    chunk) a query should rank highest against.
    """
    def __init__(self, name: str) -> None:
        self.name = name
        # Match order matters: first match wins.
        self._axis_keywords = [
            (0, "vimshottari"), (0, "dasha"),
            (1, "yoga"), (1, "raja"),
            (2, "gemstone"), (2, "ruby"),
            (3, "tiny"),
        ]

    def encode(self, queries, convert_to_numpy=True, normalize_embeddings=True):
        out = np.zeros((len(queries), 4), dtype=np.float32)
        for i, q in enumerate(queries):
            ql = q.lower()
            axis = 0  # default
            for ax, kw in self._axis_keywords:
                if kw in ql:
                    axis = ax
                    break
            out[i, axis] = 1.0
        return out


@pytest.fixture
def mini_index_dir(tmp_path: Path) -> Path:
    """Write a synthetic chunks.parquet + vectors.npy + meta.json under tmp."""
    idx = tmp_path / "embeddings"
    idx.mkdir()
    df = pd.DataFrame(_CHUNKS)
    df.to_parquet(idx / "chunks.parquet", index=False)
    np.save(idx / "vectors.npy", _VECTORS)
    (idx / "meta.json").write_text(json.dumps({
        "model_name": "stub-model",
        "n_chunks": len(df),
        "vector_dim": 4,
    }), encoding="utf-8")
    return idx


@pytest.fixture
def stub_st(monkeypatch):
    """Inject the stub SentenceTransformer for the duration of one test."""
    import sys
    import types
    fake_module = types.ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = _StubSentenceTransformer  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    yield


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Drop the process-wide singleton between tests so embeddings dirs
    from one test don't leak into the next."""
    reset_default_service()
    yield
    reset_default_service()


# --------------------------------------------------------------------------- #
# Tests                                                                        #
# --------------------------------------------------------------------------- #

class TestIndexAvailability:
    """Pre-load disk checks: separate from search to keep startup paths fast."""

    def test_index_exists_returns_false_when_dir_empty(self, tmp_path: Path) -> None:
        """A bare embeddings dir must report not-existent — the route layer
        relies on this to return 503 instead of 500."""
        svc = KnowledgeSearchService(tmp_path)
        assert svc.index_exists() is False
        assert svc.is_loaded is False

    def test_index_exists_returns_true_with_all_three_files(
        self, mini_index_dir: Path,
    ) -> None:
        """All of chunks.parquet + vectors.npy + meta.json must be present."""
        svc = KnowledgeSearchService(mini_index_dir)
        assert svc.index_exists() is True

    def test_stats_before_load_does_not_trigger_load(
        self, mini_index_dir: Path,
    ) -> None:
        """stats() is a health-check style call — must be cheap and never
        trigger the model import."""
        svc = KnowledgeSearchService(mini_index_dir)
        s = svc.stats()
        assert s == {
            "loaded": False, "exists": True,
            "embeddings_dir": str(mini_index_dir),
        }
        assert svc.is_loaded is False

    def test_ensure_loaded_raises_index_unavailable_when_files_missing(
        self, tmp_path: Path,
    ) -> None:
        """Service must surface IndexUnavailable (not FileNotFoundError) so
        the route layer can map it to a clean 503."""
        svc = KnowledgeSearchService(tmp_path)
        with pytest.raises(IndexUnavailable):
            svc.ensure_loaded()


class TestSearchSemantic:
    """Cosine-only mode — pure cosine ranking against the stub vectors."""

    def test_query_matches_dasha_chunk(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        """Query containing 'vimshottari' must rank c0 first (axis 0)."""
        svc = KnowledgeSearchService(mini_index_dir)
        results = svc.search("vimshottari mahadasha", mode="semantic", top=3)
        assert results[0].chunk_id == "c0"
        assert results[0].source == "bphs"
        assert results[0].score == pytest.approx(1.0)

    def test_query_matches_yoga_chunk(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        svc = KnowledgeSearchService(mini_index_dir)
        results = svc.search("raja yoga benefic", mode="semantic", top=3)
        assert results[0].chunk_id == "c1"
        assert results[0].score == pytest.approx(1.0)


class TestSearchHybrid:
    """Hybrid blends 0.7 cos + 0.3 lex; lexical hits should boost matching chunks."""

    def test_hybrid_score_is_blend_not_pure_cos(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        """For a query matching the cosine-axis AND containing the chunk's
        lexical tokens, the hybrid score must equal 0.7*1 + 0.3*1 = 1.0."""
        svc = KnowledgeSearchService(mini_index_dir)
        results = svc.search(
            "vimshottari dasha mahadasha", mode="hybrid", top=1,
        )
        # cosine = 1.0 (axis 0), lexical hits all match → normalized lex = 1.0
        assert results[0].score == pytest.approx(1.0)


class TestSearchLexical:
    """Pure lexical mode — no model load required, just token overlap."""

    def test_lexical_does_not_require_model(
        self, mini_index_dir: Path,
    ) -> None:
        """Without the stub_st fixture the model import would normally fail
        in CI; lexical mode must short-circuit before touching the model."""
        # Construct service WITHOUT stub_st — confirms lexical path is
        # independent of sentence_transformers presence.
        svc = KnowledgeSearchService(mini_index_dir)
        # Bypass the model load by faking loaded state — chunks_df + vectors
        # only.
        svc._chunks_df = pd.read_parquet(mini_index_dir / "chunks.parquet")
        svc._vectors = np.load(mini_index_dir / "vectors.npy")
        svc._meta = json.loads((mini_index_dir / "meta.json").read_text())
        svc._loaded = True

        results = svc.search("ruby pearl", mode="lexical", top=3)
        assert results[0].chunk_id == "c2"


class TestFilters:
    """min_tokens, topic, source — these MUST trim the candidate set before
    scoring so masked rows can't sneak into the top-k."""

    def test_min_tokens_filter_excludes_short_chunks(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        """Default min_tokens=30 must drop c3 (n_tokens=10)."""
        svc = KnowledgeSearchService(mini_index_dir)
        results = svc.search("tiny", mode="semantic", top=10, min_tokens=30)
        assert all(r.chunk_id != "c3" for r in results)

    def test_min_tokens_zero_includes_short_chunks(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        """min_tokens=0 lifts the filter so c3 becomes eligible."""
        svc = KnowledgeSearchService(mini_index_dir)
        results = svc.search("tiny", mode="semantic", top=10, min_tokens=0)
        assert any(r.chunk_id == "c3" for r in results)

    def test_topic_filter_restricts_results(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        """Even a query that semantically matches c0 must return [] when
        the topic filter excludes c0's topic."""
        svc = KnowledgeSearchService(mini_index_dir)
        results = svc.search(
            "vimshottari", mode="semantic", topic="yogas.raja_yogas", top=5,
        )
        assert all(r.chunk_id != "c0" for r in results)

    def test_source_substring_filter(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        """Source filter is a substring contains check (matches 'bphs' in
        both c0 and c3 if min_tokens permits)."""
        svc = KnowledgeSearchService(mini_index_dir)
        results = svc.search("anything", mode="lexical", source="bphs", top=10)
        assert all(r.source == "bphs" for r in results)

    def test_empty_mask_returns_empty_tuple(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        """If filters mask out every chunk, search returns () — not raise."""
        svc = KnowledgeSearchService(mini_index_dir)
        out = svc.search(
            "x", mode="semantic", topic="does.not.exist", top=10,
        )
        assert out == ()


class TestValidation:
    """Argument-level checks that fire before any expensive work."""

    @pytest.mark.parametrize("bad_query", ["", "   ", "\n\t"])
    def test_empty_query_raises_value_error(
        self, mini_index_dir: Path, bad_query: str,
    ) -> None:
        """Empty queries can't produce meaningful results; reject early."""
        svc = KnowledgeSearchService(mini_index_dir)
        with pytest.raises(ValueError, match="non-empty"):
            svc.search(bad_query)

    def test_unknown_mode_raises(self, mini_index_dir: Path) -> None:
        svc = KnowledgeSearchService(mini_index_dir)
        with pytest.raises(ValueError, match="unknown mode"):
            svc.search("anything", mode="magic")  # type: ignore[arg-type]

    def test_non_positive_top_raises(self, mini_index_dir: Path) -> None:
        svc = KnowledgeSearchService(mini_index_dir)
        with pytest.raises(ValueError, match="top must be positive"):
            svc.search("anything", top=0)


class TestStatsAfterLoad:
    """Post-load stats include n_chunks, vector_dim, source count."""

    def test_stats_reports_loaded_state(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        svc = KnowledgeSearchService(mini_index_dir)
        svc.search("vimshottari", top=1)  # triggers load
        s = svc.stats()
        assert s["loaded"] is True
        assert s["n_chunks"] == 4
        assert s["vector_dim"] == 4
        assert s["model_name"] == "stub-model"
        assert s["n_sources"] == 3  # bphs, phaladeepika, frawley


class TestThreadSafety:
    """ensure_loaded must be safe under concurrent first-callers."""

    def test_concurrent_ensure_loaded_does_not_double_load(
        self, mini_index_dir: Path, monkeypatch,
    ) -> None:
        """Two threads hitting ensure_loaded at the same time must produce
        exactly one model construction — verify by counting StubSentenceTransformer
        instantiations."""
        call_count = {"n": 0}

        class CountingStub(_StubSentenceTransformer):
            def __init__(self, name: str) -> None:
                super().__init__(name)
                call_count["n"] += 1

        import sys
        import types
        mod = types.ModuleType("sentence_transformers")
        mod.SentenceTransformer = CountingStub  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "sentence_transformers", mod)

        svc = KnowledgeSearchService(mini_index_dir)

        threads = [threading.Thread(target=svc.ensure_loaded) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert call_count["n"] == 1, (
            f"expected exactly one model load under concurrent ensure_loaded, "
            f"got {call_count['n']}"
        )


class TestSingleton:
    """Module-level get_default_service caching behavior."""

    def test_singleton_returns_same_instance(self) -> None:
        a = get_default_service()
        b = get_default_service()
        assert a is b

    def test_explicit_embeddings_dir_bypasses_singleton(
        self, mini_index_dir: Path,
    ) -> None:
        """Passing embeddings_dir produces a fresh instance — used in tests
        so per-test indexes don't leak."""
        a = get_default_service(embeddings_dir=mini_index_dir)
        b = get_default_service(embeddings_dir=mini_index_dir)
        assert a is not b  # explicit-dir path always builds anew


class TestSearchResultDataclass:
    """SearchResult contract — fields, immutability, JSON-safety."""

    def test_search_result_is_frozen(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        svc = KnowledgeSearchService(mini_index_dir)
        r = svc.search("vimshottari", top=1)[0]
        with pytest.raises(Exception):  # FrozenInstanceError
            r.score = 999.0  # type: ignore[misc]

    def test_search_result_topics_is_tuple(
        self, mini_index_dir: Path, stub_st,
    ) -> None:
        """topics must be hashable (= tuple of str), not a numpy array."""
        svc = KnowledgeSearchService(mini_index_dir)
        r = svc.search("vimshottari", top=1)[0]
        assert isinstance(r.topics, tuple)
        assert all(isinstance(t, str) for t in r.topics)
