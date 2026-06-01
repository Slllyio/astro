"""Full doctrine-corpus RAG enhancer (Tier 2B).

Where ``dkp_enhancer`` attaches matches from the curated 27-record
Doctrine Translation Engine, this module attaches matches from the
**full 918-artefact / 6.28M-word doctrine corpus** indexed by
``app.medini.services.knowledge_search.KnowledgeSearchService``.

For each Finding in the reading, the enhancer:
1. Constructs a search query from the finding's rule + verdict text.
2. Runs a hybrid RAG search (vector + lexical) against the corpus.
3. Attaches the top-K snippets as a parallel ``corpus_citations`` sidecar.

Gracefully degrades when the RAG index is unavailable (embeddings
directory missing, model not downloaded) — every finding gets an
empty ``corpus_citations`` list and the envelope's
``rag_index_available`` flag is False.

Public surface
--------------
- ``enhance_with_corpus_rag(reading, *, service=None, top_k=3,
                            max_findings=None)`` -> ``CorpusRAGEnhancedReading``
- ``CorpusRAGEnhancedReading`` — Pydantic envelope.
- ``CorpusCitation`` — one snippet record.

The full corpus is ~6.28M words; the singleton service from
``app.medini.services.knowledge_search.get_default_service()`` is used
unless a service is injected via the ``service`` param (for tests/mocking).
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, Protocol

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public schema
# ---------------------------------------------------------------------------

class CorpusCitation(BaseModel):
    """One snippet from the doctrine corpus attached to a finding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    score: float = Field(ge=0.0)
    source: str
    title: str
    snippet: str
    source_url: str | None = None


class CorpusRAGEnhancedReading(BaseModel):
    """Envelope: original reading + per-finding corpus citations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "0.7.0"
    rag_index_available: bool
    reading: dict[str, Any]
    findings_enriched: int
    citations_attached_total: int
    skipped_reason: str | None = None


# ---------------------------------------------------------------------------
# RAG service Protocol (so tests can inject a stub)
# ---------------------------------------------------------------------------

class _SearchResultLike(Protocol):
    """Subset of the real ``SearchResult`` dataclass used by the enhancer."""
    chunk_id: str
    score: float
    source: str
    title: str
    snippet: str
    source_url: str | None


class _SearchServiceLike(Protocol):
    """Subset of ``KnowledgeSearchService`` consumed here.

    The real service has more methods; the enhancer needs only ``index_exists``
    and ``search``."""
    def index_exists(self) -> bool: ...
    def search(self, query: str, *, top: int = 5) -> tuple[_SearchResultLike, ...]: ...


# ---------------------------------------------------------------------------
# Finding walker (shared structural identifier with dkp_enhancer)
# ---------------------------------------------------------------------------

def _walk_findings(node: Any) -> Iterable[dict[str, Any]]:
    if isinstance(node, dict):
        if {"id", "rule", "classification", "verdict"}.issubset(node.keys()):
            yield node
        else:
            for v in node.values():
                yield from _walk_findings(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_findings(item)


def _query_for_finding(finding: dict[str, Any]) -> str:
    """Build a corpus-search query from a finding's rule + verdict."""
    rule = finding.get("rule", "") or ""
    verdict = finding.get("verdict", "") or ""
    # Keep query short — RAG works best with focused queries.
    if rule and verdict:
        return f"{rule} {verdict[:120]}"
    return rule or verdict


def _result_to_citation(result: _SearchResultLike) -> CorpusCitation:
    return CorpusCitation(
        chunk_id=result.chunk_id,
        score=float(result.score),
        source=result.source,
        title=result.title,
        snippet=result.snippet,
        source_url=getattr(result, "source_url", None),
    )


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def enhance_with_corpus_rag(
    reading: dict[str, Any] | BaseModel,
    *,
    service: _SearchServiceLike | None = None,
    top_k: int = 3,
    max_findings: int | None = None,
) -> CorpusRAGEnhancedReading:
    """Attach top-K corpus-RAG citations to each finding in the reading.

    Parameters
    ----------
    reading
        A Track-A ReadingOutput dict or Pydantic model.
    service
        Optional ``KnowledgeSearchService``-like instance. If None, uses
        the default singleton (loaded lazily on first call). Tests
        inject a stub here.
    top_k
        How many corpus citations to attach per finding (default 3).
    max_findings
        Optional cap on how many findings to enrich. None = enrich all.
        Useful for keeping latency bounded on large readings.
    """
    if isinstance(reading, BaseModel):
        reading_dict: dict[str, Any] = reading.model_dump(mode="json")
    else:
        reading_dict = dict(reading)

    # Resolve service.
    if service is None:
        try:
            from app.medini.services.knowledge_search import get_default_service
            service = get_default_service()
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning(f"could not import default KnowledgeSearchService: {exc}")
            return CorpusRAGEnhancedReading(
                rag_index_available=False,
                reading=reading_dict,
                findings_enriched=0,
                citations_attached_total=0,
                skipped_reason=f"service import failed: {exc}",
            )

    try:
        index_ok = service.index_exists()
    except Exception as exc:  # pragma: no cover
        logger.warning(f"RAG index_exists check raised: {exc}")
        index_ok = False

    if not index_ok:
        # Every finding still gets an empty corpus_citations key for shape stability.
        for finding in _walk_findings(reading_dict):
            finding["corpus_citations"] = []
        return CorpusRAGEnhancedReading(
            rag_index_available=False,
            reading=reading_dict,
            findings_enriched=0,
            citations_attached_total=0,
            skipped_reason="RAG index not available on this host",
        )

    findings_enriched = 0
    citations_total = 0
    findings_seen = 0

    for finding in _walk_findings(reading_dict):
        findings_seen += 1
        if max_findings is not None and findings_seen > max_findings:
            finding["corpus_citations"] = []
            continue
        query = _query_for_finding(finding)
        if not query.strip():
            finding["corpus_citations"] = []
            continue
        try:
            results = service.search(query, top=top_k)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"corpus search failed for {finding.get('id')}: {exc}")
            finding["corpus_citations"] = []
            continue
        citations = [_result_to_citation(r).model_dump(mode="json") for r in results]
        finding["corpus_citations"] = citations
        if citations:
            findings_enriched += 1
            citations_total += len(citations)

    return CorpusRAGEnhancedReading(
        rag_index_available=True,
        reading=reading_dict,
        findings_enriched=findings_enriched,
        citations_attached_total=citations_total,
        skipped_reason=None,
    )
