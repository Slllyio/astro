"""Smoke tests for the full doctrine-corpus RAG enhancer.

Tests use a StubSearchService so they run without the actual RAG
infrastructure (model weights + vector index would need GB of disk).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from app.integration.corpus_rag_enhancer import (
    CorpusCitation,
    CorpusRAGEnhancedReading,
    enhance_with_corpus_rag,
)


# ---------------------------------------------------------------------------
# Stub RAG service
# ---------------------------------------------------------------------------

@dataclass
class _StubResult:
    """Mimics SearchResult dataclass."""
    chunk_id: str
    score: float
    source: str
    title: str
    snippet: str
    source_url: str | None = None


class StubSearchService:
    """In-memory stub. Returns a fixed result per query for determinism."""

    def __init__(self, available: bool = True, results_per_query: int = 2):
        self.available = available
        self.results_per_query = results_per_query
        self.search_calls = 0

    def index_exists(self) -> bool:
        return self.available

    def search(self, query: str, *, top: int = 5) -> tuple[_StubResult, ...]:
        self.search_calls += 1
        return tuple(
            _StubResult(
                chunk_id=f"stub_{i}_{abs(hash(query)) % 10000}",
                score=0.9 - 0.1 * i,
                source="BPHS",
                title=f"Stub chapter {i + 1}",
                snippet=f"Excerpt {i + 1} matching: {query[:60]}",
                source_url=f"https://example.com/bphs/{i}",
            )
            for i in range(min(self.results_per_query, top))
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _finding(*, id: str, rule: str, classification: str = "yoga",
             direction: str = "positive", verdict: str = "test") -> dict:
    return {
        "id": id, "rule": rule, "source_sequence": None,
        "classification": classification, "direction": direction,
        "verdict": verdict, "verdict_language": "en", "evidence": [],
        "confidence": {"score": 0.7, "votes": {}, "band": "medium"},
        "enrichment_level": 0, "citations": [],
        "consensus": None, "consensus_status": "not_computed",
        "dispute": None, "robustness": None, "contradicts_finding_ids": [],
    }


def _reading_with(findings: list[dict]) -> dict:
    return {
        "meta": {"schema_version": "1.2.0"},
        "chart": {}, "primitives": {}, "foundations": {}, "practitioner": {},
        "sequences": {},
        "domains": {
            "career": {
                "domain": "career",
                "promise": _finding(id="d.career.promise", rule="promise.career"),
                "triggers": [], "timing_windows": [],
                "afflictions": [], "cross_checks": findings,
                "remedies": [],
                "overall_verdict": _finding(id="d.career.overall", rule="overall.career"),
                "confidence": {"score": 0.7, "votes": {}, "band": "medium"},
            }
        },
        "contradictions": [], "warnings": [],
    }


# ---------------------------------------------------------------------------
# Available-index tests
# ---------------------------------------------------------------------------

class TestRAGAvailable:
    def test_returns_envelope(self):
        svc = StubSearchService(available=True)
        result = enhance_with_corpus_rag(
            _reading_with([_finding(id="t.1", rule="yogas.lakshmi", verdict="Lakshmi active")]),
            service=svc,
        )
        assert isinstance(result, CorpusRAGEnhancedReading)
        assert result.rag_index_available is True

    def test_each_finding_gets_corpus_citations(self):
        svc = StubSearchService(available=True, results_per_query=3)
        findings = [
            _finding(id=f"t.{i}", rule=f"rule_{i}", verdict=f"verdict {i}")
            for i in range(3)
        ]
        result = enhance_with_corpus_rag(
            _reading_with(findings),
            service=svc, top_k=3,
        )
        cross = result.reading["domains"]["career"]["cross_checks"]
        for f in cross:
            assert "corpus_citations" in f
            assert len(f["corpus_citations"]) == 3

    def test_citations_have_required_fields(self):
        svc = StubSearchService(available=True)
        result = enhance_with_corpus_rag(
            _reading_with([_finding(id="t.1", rule="r1", verdict="v1")]),
            service=svc,
        )
        cit = result.reading["domains"]["career"]["cross_checks"][0]["corpus_citations"][0]
        assert "chunk_id" in cit
        assert "score" in cit
        assert "snippet" in cit
        assert "title" in cit

    def test_envelope_counts_match(self):
        svc = StubSearchService(available=True, results_per_query=2)
        findings = [_finding(id=f"t.{i}", rule=f"r{i}", verdict=f"v{i}") for i in range(4)]
        result = enhance_with_corpus_rag(_reading_with(findings), service=svc)
        # 4 cross-check findings + 2 (promise, overall_verdict) of career = 6 findings
        # Each gets 2 citations = 12 total
        # findings_enriched counts findings that GOT >0 citations
        assert result.findings_enriched == 6
        assert result.citations_attached_total == 12

    def test_max_findings_caps_enrichment(self):
        svc = StubSearchService(available=True, results_per_query=2)
        findings = [_finding(id=f"t.{i}", rule=f"r{i}", verdict=f"v{i}") for i in range(10)]
        result = enhance_with_corpus_rag(
            _reading_with(findings), service=svc, max_findings=3,
        )
        # Only first 3 findings should have non-empty citations
        assert result.findings_enriched <= 3


# ---------------------------------------------------------------------------
# Unavailable-index tests
# ---------------------------------------------------------------------------

class TestRAGUnavailable:
    def test_returns_envelope_with_available_false(self):
        svc = StubSearchService(available=False)
        result = enhance_with_corpus_rag(_reading_with([]), service=svc)
        assert result.rag_index_available is False
        assert result.findings_enriched == 0
        assert result.citations_attached_total == 0

    def test_skipped_reason_set(self):
        svc = StubSearchService(available=False)
        result = enhance_with_corpus_rag(_reading_with([]), service=svc)
        assert result.skipped_reason is not None
        assert "not available" in result.skipped_reason.lower()

    def test_findings_still_get_empty_corpus_citations_field(self):
        """Shape stability: every finding has corpus_citations even when RAG off."""
        svc = StubSearchService(available=False)
        result = enhance_with_corpus_rag(
            _reading_with([_finding(id="t.1", rule="r", verdict="v")]),
            service=svc,
        )
        for f in result.reading["domains"]["career"]["cross_checks"]:
            assert "corpus_citations" in f
            assert f["corpus_citations"] == []


# ---------------------------------------------------------------------------
# Empty findings / edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_query_gets_empty_citations(self):
        """Finding with no rule and no verdict produces no search call."""
        svc = StubSearchService(available=True)
        finding_empty = _finding(id="t.empty", rule="", verdict="")
        finding_empty["rule"] = ""
        finding_empty["verdict"] = ""
        result = enhance_with_corpus_rag(_reading_with([finding_empty]), service=svc)
        cross = result.reading["domains"]["career"]["cross_checks"][0]
        assert cross["corpus_citations"] == []

    def test_walker_skips_non_finding_dicts(self):
        """A dict with only ``id`` isn't a Finding — must not be enriched."""
        svc = StubSearchService(available=True)
        reading = _reading_with([])
        reading["sequences"]["fake"] = {"id": "not-finding", "value": 42}
        result = enhance_with_corpus_rag(reading, service=svc)
        assert "corpus_citations" not in result.reading["sequences"]["fake"]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_envelope_json_roundtrip(self):
        svc = StubSearchService(available=True)
        result = enhance_with_corpus_rag(
            _reading_with([_finding(id="t.1", rule="r", verdict="v")]),
            service=svc,
        )
        as_json = json.dumps(result.model_dump(mode="json"))
        revived = CorpusRAGEnhancedReading.model_validate(json.loads(as_json))
        assert revived.rag_index_available == result.rag_index_available

    def test_integration_version_pinned(self):
        svc = StubSearchService(available=True)
        result = enhance_with_corpus_rag(_reading_with([]), service=svc)
        assert result.integration_version == "0.7.0"
