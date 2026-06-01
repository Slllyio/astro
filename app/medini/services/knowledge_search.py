"""In-process RAG search service for the knowledge library.

A long-lived wrapper around the per-chunk index produced by
``app.medini.ml.build_rag_index``. Unlike ``app.medini.ml.search_rag.search``
(which is a one-shot CLI helper that re-reads parquet + vectors + reloads the
sentence-transformer model on every call), this service loads the model and
the vectors **once** per process and caches them — first call pays the load
cost (~2-3 s for the multilingual MiniLM model), subsequent calls return in
< 100 ms.

Thread-safe init via a module-level ``Lock``; the singleton accessor
``get_default_service()`` returns the process-wide instance so FastAPI route
handlers and the citation gatherer share one cache.

Design choices:

* **Lazy load**: ``ensure_loaded()`` is called at first ``search()``. This
  keeps app startup fast (~0 s extra on boot) and lets the app run without
  the embeddings file present — calls into the service just raise
  ``IndexUnavailable`` and callers can degrade gracefully.
* **Frozen result dataclass**: returns ``SearchResult`` tuples, not pandas
  rows, so the route layer (and citation gatherer) don't depend on pandas
  in their type signatures and can serialize trivially to JSON.
* **No mutation of cached arrays**: ``search()`` builds new score arrays on
  every call; the underlying ``vectors`` / ``chunks_df`` are treated as
  immutable.

This module deliberately does NOT re-implement the scoring math from
``search_rag``; it imports the helpers (``_tokenize``, ``_lexical_score``,
``_apply_filters``) to keep semantic+lexical+hybrid behavior identical
between the CLI and the live app.
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from app.medini.ml.search_rag import _apply_filters, _lexical_score

logger = logging.getLogger(__name__)


SearchMode = Literal["semantic", "hybrid", "lexical"]
_VALID_MODES: frozenset[str] = frozenset({"semantic", "hybrid", "lexical"})


class IndexUnavailable(RuntimeError):
    """Raised when the embeddings index is missing or unreadable.

    The route layer catches this and returns 503 with a hint to rebuild,
    so the live app degrades gracefully instead of 500ing.
    """


@dataclass(frozen=True)
class SearchResult:
    """One ranked chunk returned by ``KnowledgeSearchService.search``.

    Frozen so route handlers can pass it around without worrying about
    mutation. ``snippet`` is the truncated chunk body (full text is in the
    underlying parquet; expose on demand if needed later).
    """
    chunk_id: str
    score: float
    source: str
    title: str
    snippet: str
    source_url: str | None
    local_path: str | None
    artefact_id: str | None
    topics: tuple[str, ...]
    n_tokens: int


def _row_to_result(row: pd.Series, score: float, snippet_chars: int) -> SearchResult:
    """Convert a pandas row + score into a frozen SearchResult.

    The text is collapsed into a single line and truncated. Topics arrive
    from parquet as a numpy array — we cast to tuple so the dataclass stays
    hashable and immutable.
    """
    raw_text = (row.get("text") or "").strip().replace("\n", " ")
    snippet = raw_text[:snippet_chars] + ("..." if len(raw_text) > snippet_chars else "")
    topics_raw = row.get("topics")
    topics: tuple[str, ...] = (
        tuple(str(t) for t in topics_raw) if topics_raw is not None else ()
    )
    n_tokens = row.get("n_tokens")
    return SearchResult(
        chunk_id=str(row.get("chunk_id") or ""),
        score=float(score),
        source=str(row.get("source") or ""),
        title=str(row.get("title") or "").strip(),
        snippet=snippet,
        source_url=str(row["source_url"]) if row.get("source_url") else None,
        local_path=str(row["local_path"]) if row.get("local_path") else None,
        artefact_id=str(row["artefact_id"]) if row.get("artefact_id") else None,
        topics=topics,
        n_tokens=int(n_tokens) if n_tokens is not None and not pd.isna(n_tokens) else 0,
    )


class KnowledgeSearchService:
    """Lazily-loaded RAG index wrapper.

    Build one instance per embeddings directory. Most callers should use the
    module-level singleton via ``get_default_service()``.

    The model + vectors + chunks are loaded under a lock on the first
    ``search()`` call; concurrent first-callers wait on the lock instead of
    double-loading. The model object itself is thread-safe for ``encode()``.
    """

    def __init__(self, embeddings_dir: Path) -> None:
        self._embeddings_dir = Path(embeddings_dir)
        self._lock = threading.Lock()
        self._loaded = False
        # Populated by ensure_loaded():
        self._model: Any | None = None  # SentenceTransformer
        self._vectors: np.ndarray | None = None
        self._chunks_df: pd.DataFrame | None = None
        self._meta: dict[str, Any] | None = None

    @property
    def embeddings_dir(self) -> Path:
        return self._embeddings_dir

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def index_exists(self) -> bool:
        """Cheap pre-check that the index files are present on disk.

        Lets callers (e.g. a health endpoint) report status without paying
        the model-load cost.
        """
        return all(
            (self._embeddings_dir / name).exists()
            for name in ("chunks.parquet", "vectors.npy", "meta.json")
        )

    def ensure_loaded(self) -> None:
        """Load the index + model on first call. Idempotent + thread-safe.

        Raises ``IndexUnavailable`` if any of the three index files are
        missing; the route layer maps that to a 503 with rebuild instructions.
        """
        if self._loaded:
            return
        with self._lock:
            if self._loaded:  # second check inside the lock
                return
            if not self.index_exists():
                raise IndexUnavailable(
                    f"RAG index missing in {self._embeddings_dir}. "
                    f"Rebuild via: python -m app.medini.ml.build_rag_index"
                )
            chunks_path = self._embeddings_dir / "chunks.parquet"
            vectors_path = self._embeddings_dir / "vectors.npy"
            meta_path = self._embeddings_dir / "meta.json"

            logger.info("Loading RAG index from %s", self._embeddings_dir)
            self._chunks_df = pd.read_parquet(chunks_path)
            self._vectors = np.load(vectors_path)
            self._meta = json.loads(meta_path.read_text(encoding="utf-8"))

            # Lazy import — keep app boot fast for routes that never search.
            from sentence_transformers import SentenceTransformer
            model_name = self._meta["model_name"]
            self._model = SentenceTransformer(model_name)
            logger.info(
                "RAG index loaded: %d chunks, %d-dim vectors, model=%s",
                len(self._chunks_df), self._vectors.shape[1], model_name,
            )
            self._loaded = True

    def stats(self) -> dict[str, Any]:
        """Lightweight metadata about the loaded index (or whether it's loaded).

        Safe to call before loading — returns ``{loaded: False, exists: bool}``
        without triggering ``ensure_loaded()``.
        """
        if not self._loaded:
            return {
                "loaded": False,
                "exists": self.index_exists(),
                "embeddings_dir": str(self._embeddings_dir),
            }
        assert self._chunks_df is not None and self._vectors is not None
        return {
            "loaded": True,
            "embeddings_dir": str(self._embeddings_dir),
            "n_chunks": int(len(self._chunks_df)),
            "vector_dim": int(self._vectors.shape[1]),
            "model_name": (self._meta or {}).get("model_name"),
            "n_sources": int(self._chunks_df["source"].nunique()),
        }

    def search(
        self,
        query: str,
        *,
        mode: SearchMode = "hybrid",
        topic: str | None = None,
        source: str | None = None,
        min_tokens: int = 30,
        top: int = 10,
        snippet_chars: int = 400,
    ) -> tuple[SearchResult, ...]:
        """Run a search and return the top ``top`` ranked chunks.

        Same scoring semantics as ``app.medini.ml.search_rag.search`` —
        ``hybrid`` blends 0.7 * cosine + 0.3 * normalized lexical overlap;
        ``semantic`` is cosine only; ``lexical`` is pure token overlap.
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")
        if mode not in _VALID_MODES:
            raise ValueError(
                f"unknown mode {mode!r}; expected one of {sorted(_VALID_MODES)}"
            )
        if top <= 0:
            raise ValueError("top must be positive")

        self.ensure_loaded()
        assert self._chunks_df is not None and self._vectors is not None

        mask = _apply_filters(
            self._chunks_df, topic=topic, source=source, min_tokens=min_tokens,
        )
        if not mask.any():
            return ()

        scores = np.zeros(len(self._chunks_df), dtype=np.float64)

        if mode in {"semantic", "hybrid"}:
            assert self._model is not None
            q_vec = self._model.encode(
                [query], convert_to_numpy=True, normalize_embeddings=True,
            )[0].astype(np.float32)
            cos = self._vectors @ q_vec  # vectors are L2-normalised
            scores += cos
            if mode == "hybrid":
                lex = np.array(
                    [_lexical_score(query, t) for t in self._chunks_df["text"]],
                )
                if lex.max() > 0:
                    lex = lex / lex.max()
                scores = 0.7 * cos + 0.3 * lex
        else:  # lexical
            scores = np.array(
                [_lexical_score(query, t) for t in self._chunks_df["text"]],
            )

        scores[~mask] = -1e9
        top_idx = np.argsort(-scores)[:top]
        # Drop masked-out hits (score sentinel = -1e9)
        results: list[SearchResult] = []
        for i in top_idx:
            s = float(scores[i])
            if s <= -1e8:
                continue
            results.append(
                _row_to_result(self._chunks_df.iloc[i], s, snippet_chars=snippet_chars),
            )
        return tuple(results)


# --------------------------------------------------------------------------- #
# Process-wide singleton                                                       #
# --------------------------------------------------------------------------- #

_DEFAULT_EMBEDDINGS_DIR = Path("data/knowledge_library/embeddings")
_singleton_lock = threading.Lock()
_default_service: KnowledgeSearchService | None = None


def get_default_service(
    embeddings_dir: Path | None = None,
) -> KnowledgeSearchService:
    """Return the process-wide RAG service.

    Creating the service is cheap (no model load); the model loads on the
    first ``search()`` call. Pass ``embeddings_dir`` only in tests to point
    at a synthetic index; production code should let it default.
    """
    global _default_service
    if embeddings_dir is not None:
        # Caller-supplied dir always builds a fresh instance — used by tests
        # to avoid the singleton hanging on to a stale embeddings path.
        return KnowledgeSearchService(embeddings_dir)
    if _default_service is None:
        with _singleton_lock:
            if _default_service is None:
                _default_service = KnowledgeSearchService(_DEFAULT_EMBEDDINGS_DIR)
    return _default_service


def reset_default_service() -> None:
    """Drop the cached singleton — test helper, not for production paths."""
    global _default_service
    with _singleton_lock:
        _default_service = None
