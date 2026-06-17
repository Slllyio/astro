"""Tests for app.llm.citations + the interpret-chart citations integration.

The citation gatherer is a thin layer on top of KnowledgeSearchService —
its main responsibilities are:

  1. Chart-aware query construction (different sections produce different
     queries; the MD lord and Asc sign get baked into the query string).
  2. Topic-filter selection (so a yogas drilldown doesn't pull dasha chunks).
  3. Failure swallowing — a missing index NEVER breaks interpretation.

These tests verify all three by passing an explicit stub-service to
gather_citations() so we don't depend on a real RAG index.
"""
from __future__ import annotations

from typing import Any

import pytest

from app.llm.citations import (
    Citation,
    _section_query,
    _summary_query,
    gather_citations,
)
import dataclasses

from app.llm.interpreter import Interpretation, interpret_chart
from app.medini.services.knowledge_search import SearchResult

# The citations integration into interpret_chart (Interpretation.citations) is
# in-flight round8 work not yet on this branch. The standalone gatherer
# (app.llm.citations) is present and fully tested above; only the end-to-end
# wiring is gated until Interpretation grows a `citations` field.
_HAS_CITATIONS_FIELD = "citations" in {
    f.name for f in dataclasses.fields(Interpretation)
}


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #

CHART: dict[str, Any] = {
    "ascendant": {"sign_name": "Virgo", "longitude": 173.99, "degree_in_sign": 23.99, "sign": 5},
    "current_mahadasha": {
        "mahadasha_lord": "Mercury", "start_date": "2024-01-01",
        "end_date": "2041-01-01", "time_elapsed_years": 1.0,
        "total_duration_years": 17.0,
    },
    "yogas": [
        {"name": "Bhadra", "type": "Panchamahapurusha"},
        {"name": "Gajakesari", "type": "Sambandha"},
    ],
}


def _fake_result(chunk_id: str, source: str, title: str, score: float) -> SearchResult:
    return SearchResult(
        chunk_id=chunk_id, score=score, source=source, title=title,
        snippet=f"snippet for {chunk_id} " + "x" * 350,
        source_url=f"http://x/{chunk_id}", local_path=f"/local/{chunk_id}.md",
        artefact_id=f"art-{chunk_id}", topics=("test.topic",), n_tokens=100,
    )


class StubService:
    """In-memory stand-in for KnowledgeSearchService.

    Records the call args so tests can assert the query construction logic
    without needing a real index or model. Returns a fixed result list.
    """
    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self.calls: list[dict] = []
        self.results = results or [
            _fake_result("c0", "bphs", "BPHS source", 0.95),
            _fake_result("c1", "phaladeepika", "Phaladeepika source", 0.80),
        ]

    def search(self, query: str, **kwargs) -> tuple[SearchResult, ...]:
        self.calls.append({"query": query, **kwargs})
        return tuple(self.results[:kwargs.get("top", 10)])


class RaisingService:
    """Always raises — exercises the silent-failure path."""
    def search(self, query: str, **kwargs):
        raise RuntimeError("index broken")


# --------------------------------------------------------------------------- #
# Query construction                                                           #
# --------------------------------------------------------------------------- #

class TestQueryConstruction:
    """Chart-aware query strings: include the actual chart placements so the
    RAG retrieves chart-specific evidence, not boilerplate."""

    def test_summary_query_includes_asc_sign_and_md_lord(self) -> None:
        """Anchor on Virgo + Mercury so search ranks Lagna + dasha-result
        chapters above unrelated material."""
        q, topic = _summary_query(CHART)
        assert "Virgo" in q
        assert "Mercury" in q
        assert topic is None

    def test_summary_query_handles_missing_md_gracefully(self) -> None:
        """If current_mahadasha is absent, fall back to just the ascendant."""
        q, _ = _summary_query({"ascendant": {"sign_name": "Pisces"}})
        assert "Pisces" in q
        assert "Mercury" not in q  # nothing about MD slipped in

    def test_summary_query_falls_back_when_chart_empty(self) -> None:
        """Empty chart → a generic Vedic query (never empty string, which
        would 422 on the search endpoint)."""
        q, _ = _summary_query({})
        assert q.strip() != ""

    def test_mahadasha_section_query_names_md_lord(self) -> None:
        """Section drilldown for `mahadasha` must surface the lord by name
        and pin the search to the vimshottari topic."""
        q, topic = _section_query(CHART, "mahadasha")
        assert "Mercury" in q
        assert topic == "dasha.vimshottari"

    def test_yogas_section_query_includes_yoga_names(self) -> None:
        """Yoga drilldown must include the yoga names so the RAG finds
        passages specific to Bhadra / Gajakesari, not generic 'raja yoga'."""
        q, topic = _section_query(CHART, "yogas")
        assert "Bhadra" in q
        assert "Gajakesari" in q
        # No topic filter — yoga material spans multiple leaves and a filter
        # would over-trim.
        assert topic is None

    def test_ascendant_section_query_uses_sign_name(self) -> None:
        q, topic = _section_query(CHART, "ascendant")
        assert "Virgo" in q
        assert topic == "primitives.houses"

    def test_unknown_section_falls_back_to_generic(self) -> None:
        """Unknown section name doesn't crash — returns something searchable
        rather than raising."""
        q, topic = _section_query(CHART, "wandering_stars")
        assert "wandering_stars" in q
        assert topic is None


# --------------------------------------------------------------------------- #
# gather_citations                                                             #
# --------------------------------------------------------------------------- #

class TestGatherCitations:
    def test_returns_typed_citations(self) -> None:
        """Output must be a tuple of Citation dataclasses (immutable + JSON-
        safe), not raw SearchResults."""
        out = gather_citations(
            CHART, mode="section", section="mahadasha", service=StubService(),
        )
        assert isinstance(out, tuple)
        assert all(isinstance(c, Citation) for c in out)

    def test_top_n_propagates_to_service(self) -> None:
        """top=N must flow through to the underlying search call."""
        stub = StubService()
        gather_citations(
            CHART, mode="section", section="yogas", top=2, service=stub,
        )
        assert stub.calls[0]["top"] == 2

    def test_section_query_uses_topic_filter(self) -> None:
        """mahadasha section must request topic=dasha.vimshottari so the
        ranker prefers dasha-result chapters."""
        stub = StubService()
        gather_citations(
            CHART, mode="section", section="mahadasha", service=stub,
        )
        assert stub.calls[0]["topic"] == "dasha.vimshottari"

    def test_summary_uses_no_topic_filter(self) -> None:
        """Summary citations span the whole corpus — no topic filter."""
        stub = StubService()
        gather_citations(CHART, mode="summary", section=None, service=stub)
        assert stub.calls[0]["topic"] is None

    def test_service_failure_returns_empty_tuple(self) -> None:
        """Index broken / model crash / any RuntimeError → () so the
        interpretation flow continues uninterrupted."""
        out = gather_citations(
            CHART, mode="section", section="yogas", service=RaisingService(),
        )
        assert out == ()

    def test_missing_section_with_mode_section_returns_empty(self) -> None:
        """mode='section' + section=None is a programmer error upstream —
        degrade silently, don't crash the interpreter."""
        out = gather_citations(
            CHART, mode="section", section=None, service=StubService(),
        )
        assert out == ()

    def test_citation_snippet_is_trimmed(self) -> None:
        """Citation snippets are shorter than SearchResult snippets so the
        UI stays scannable."""
        out = gather_citations(
            CHART, mode="section", section="mahadasha", service=StubService(),
        )
        for c in out:
            assert len(c.snippet) <= 305  # 300 + ellipsis padding


# --------------------------------------------------------------------------- #
# interpret_chart citations attachment                                         #
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(
    not _HAS_CITATIONS_FIELD,
    reason="Interpretation.citations integration is in-flight round8 work not on this branch",
)
class TestInterpretChartCitations:
    """End-to-end: settings flag + gather_citations wired into interpret_chart."""

    def test_citations_empty_when_flag_disabled(self, monkeypatch) -> None:
        """INTERPRET_CITATIONS_ENABLED=False (default) → empty citations
        even if the RAG service is reachable."""
        from app.core import config
        monkeypatch.setattr(config.settings, "INTERPRET_CITATIONS_ENABLED", False)
        result = interpret_chart(CHART, mode="summary")
        assert result.citations == ()

    def test_citations_populated_when_flag_enabled(self, monkeypatch) -> None:
        """Flag on + stub service injected → citations attached to result."""
        stub = StubService()
        from app.core import config
        monkeypatch.setattr(config.settings, "INTERPRET_CITATIONS_ENABLED", True)
        monkeypatch.setattr(
            "app.llm.citations.get_default_service", lambda: stub,
        )

        result = interpret_chart(CHART, mode="summary")
        assert len(result.citations) == 2
        assert result.citations[0].source == "bphs"
        assert isinstance(result.citations[0], Citation)

    def test_citations_swallow_service_failure(self, monkeypatch) -> None:
        """If the RAG raises mid-interpretation, citations are empty but
        the text+source fields are still populated (the contract that
        interpret_chart can't fail because of grounding)."""
        from app.core import config
        monkeypatch.setattr(config.settings, "INTERPRET_CITATIONS_ENABLED", True)
        monkeypatch.setattr(
            "app.llm.citations.get_default_service", lambda: RaisingService(),
        )
        result = interpret_chart(CHART, mode="summary")
        assert result.citations == ()
        assert result.text  # narrative still rendered
        assert result.source in {"llm", "fallback"}
