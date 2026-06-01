"""Unit tests for app.medini.services.chart_reader + reading routes.

Stubs out:
  * RAG service → fixed canned SearchResults so we don't depend on the
    embeddings index being loaded.
  * LLM client → StubClient with canned responses so we don't depend on
    Ollama being running.

End-to-end happy paths + failure paths (RAG fails, LLM fails) both
verify that the reading still returns a valid Reading object with the
expected sections.
"""
from __future__ import annotations

import pytest

from app.llm.client import OllamaUnavailable, StubClient
from app.medini.services.chart_reader import (
    Reading,
    ReadingSection,
    _build_section_queries,
    _extract_reading_elements,
    read_chart,
)
from app.medini.services.knowledge_search import SearchResult


# --------------------------------------------------------------------------- #
# Sample chart fixture (Bangalore baseline)                                   #
# --------------------------------------------------------------------------- #

SAMPLE_CHART = {
    "ascendant": {
        "sign": 6, "sign_name": "Virgo",
        "longitude": 173.99, "degree_in_sign": 23.99,
    },
    "current_mahadasha": {
        "mahadasha_lord": "Mercury",
        "start_date": "1978-03-26", "end_date": "1995-03-26",
        "time_elapsed_years": 12.3, "total_duration_years": 17.0,
    },
    "current_antardasha": {
        "antardasha_lord": "Mercury",
        "start_date": "1978-03-26", "end_date": "1980-08-26",
    },
    "current_pratyantar": {},
    "d1": {
        "Sun": {
            "sign_name": "Cancer", "sign": 4, "degree_in_sign": 28.0,
            "longitude": 118.0, "house": 11,
            "nakshatra": {"name": "Ashlesha", "pada": 4},
        },
        "Moon": {
            "sign_name": "Pisces", "sign": 12, "degree_in_sign": 13.5,
            "longitude": 343.5, "house": 7,
            "nakshatra": {"name": "Revati", "pada": 3},
        },
        "Mars": {"sign_name": "Cancer", "sign": 4, "degree_in_sign": 5.0,
                 "longitude": 95.0, "house": 11},
        "Jupiter": {"sign_name": "Cancer", "sign": 4, "degree_in_sign": 19.0,
                    "longitude": 109.0, "house": 11},
        "Mercury": {"sign_name": "Cancer", "sign": 4, "degree_in_sign": 10.0,
                    "longitude": 100.0, "house": 11},
        "Venus": {"sign_name": "Gemini", "sign": 3, "degree_in_sign": 5.0,
                  "longitude": 65.0, "house": 10},
        "Saturn": {"sign_name": "Sagittarius", "sign": 9, "degree_in_sign": 4.0,
                   "longitude": 244.0, "house": 4},
        "Rahu": {"sign_name": "Capricorn", "sign": 10, "degree_in_sign": 1.0,
                 "longitude": 271.0, "house": 5},
        "Ketu": {"sign_name": "Cancer", "sign": 4, "degree_in_sign": 1.0,
                 "longitude": 91.0, "house": 11},
    },
}


# --------------------------------------------------------------------------- #
# Stubs                                                                        #
# --------------------------------------------------------------------------- #

class StubRagService:
    """Records search() args, returns canned SearchResults."""
    def __init__(self, results: list[SearchResult] | None = None):
        self.calls: list[dict] = []
        self.results = results or [
            SearchResult(
                chunk_id="c0", score=0.62, source="bphs",
                title="BPHS Ch.X - sample passage",
                snippet="sample snippet text " + "x" * 100,
                source_url="http://x/bphs", local_path="/local/bphs.md",
                artefact_id="art-0", topics=("primitives.houses",),
                n_tokens=100,
            ),
        ]

    def search(self, query: str, **kwargs):
        self.calls.append({"query": query, **kwargs})
        return tuple(self.results[:kwargs.get("top", 10)])


class RaisingRagService:
    def search(self, *a, **k):
        raise RuntimeError("rag down")


# --------------------------------------------------------------------------- #
# Element extraction + section queries                                         #
# --------------------------------------------------------------------------- #

class TestExtractElements:
    def test_pulls_asc_sun_moon_md(self) -> None:
        elements = _extract_reading_elements(SAMPLE_CHART)
        assert elements["ascendant"]["sign_name"] == "Virgo"
        assert elements["sun"]["sign_name"] == "Cancer"
        assert elements["moon"]["sign_name"] == "Pisces"
        assert elements["current_mahadasha"]["mahadasha_lord"] == "Mercury"

    def test_detects_yogas(self) -> None:
        """Sample chart has Mars/Jupiter/Mercury/Sun in Cancer — Bhadra
        yoga (Mercury in own/exalted in kendra) may fire; whatever's
        detected, the structure must be a list of dicts with name."""
        elements = _extract_reading_elements(SAMPLE_CHART)
        assert isinstance(elements["yogas"], list)
        for y in elements["yogas"]:
            assert "name" in y


class TestSectionQueries:
    def test_includes_asc_section(self) -> None:
        elements = _extract_reading_elements(SAMPLE_CHART)
        sections = _build_section_queries(elements)
        assert any("Virgo" in s["title"] for s in sections)
        assert any("Virgo" in s["query"] for s in sections)

    def test_includes_md_section_with_lord(self) -> None:
        elements = _extract_reading_elements(SAMPLE_CHART)
        sections = _build_section_queries(elements)
        md_secs = [s for s in sections if "Mahadasha" in s["title"]]
        assert len(md_secs) == 1
        assert "Mercury" in md_secs[0]["query"]
        assert md_secs[0]["topic"] == "dasha.vimshottari"

    def test_skips_sections_with_no_data(self) -> None:
        """Empty chart → no sections."""
        empty = {"ascendant": {}, "d1": {}, "current_mahadasha": {}}
        sections = _build_section_queries(_extract_reading_elements(empty))
        assert sections == []


# --------------------------------------------------------------------------- #
# read_chart end-to-end                                                        #
# --------------------------------------------------------------------------- #

class TestReadChart:
    def test_returns_reading_dataclass(self) -> None:
        rag = StubRagService()
        stub_llm = StubClient(canned_response="[GROUNDED]: synthesized prose [1]")
        r = read_chart(SAMPLE_CHART, rag_service=rag, llm_client=stub_llm)
        assert isinstance(r, Reading)
        assert r.source == "llm"
        assert len(r.sections) >= 2
        assert all(isinstance(s, ReadingSection) for s in r.sections)

    def test_strips_mode_marker_from_llm_output(self) -> None:
        rag = StubRagService()
        stub_llm = StubClient(canned_response="[GROUNDED]: actual prose body.")
        r = read_chart(SAMPLE_CHART, rag_service=rag, llm_client=stub_llm)
        for s in r.sections:
            assert not s.text.upper().startswith("[GROUNDED]")
            assert not s.text.upper().startswith("[GENERAL]")

    def test_falls_back_to_deterministic_when_llm_unavailable(self) -> None:
        rag = StubRagService()

        class FailingLLM:
            model = "broken"
            def complete(self, prompt: str) -> str:
                raise OllamaUnavailable("daemon down")

        r = read_chart(SAMPLE_CHART, rag_service=rag, llm_client=FailingLLM())
        assert r.source == "deterministic"
        assert all(s.text for s in r.sections)  # deterministic still has text

    def test_rag_failure_yields_empty_citations_not_crash(self) -> None:
        """Per-section RAG failure must not break the reading."""
        stub_llm = StubClient(canned_response="prose")
        r = read_chart(
            SAMPLE_CHART, rag_service=RaisingRagService(), llm_client=stub_llm,
        )
        assert r.n_citations_total == 0
        # Reading still succeeded; LLM saw "no citations" prompt
        assert all(s.text for s in r.sections)

    def test_no_llm_no_rag_still_returns_reading(self) -> None:
        """Both no-op (no LLM, RAG broken) → deterministic with empty citations.

        Note: passing rag_service=None falls back to the production
        singleton (correct end-user behaviour); to test the
        no-citations path explicitly we pass a RaisingRagService."""
        r = read_chart(
            SAMPLE_CHART,
            rag_service=RaisingRagService(),
            llm_client=None,
        )
        assert isinstance(r, Reading)
        assert r.source == "deterministic"
        assert r.n_citations_total == 0

    def test_citations_are_truncated_per_section(self) -> None:
        rag = StubRagService()
        stub_llm = StubClient(canned_response="x")
        r = read_chart(
            SAMPLE_CHART, rag_service=rag, llm_client=stub_llm,
            top_citations_per_section=2,
        )
        for s in r.sections:
            assert len(s.citations) <= 2

    def test_each_rag_call_uses_section_topic(self) -> None:
        """When _build_section_queries sets a topic filter, the
        retrieval call must propagate it (so e.g. dasha section retrieves
        from dasha.vimshottari corpus)."""
        rag = StubRagService()
        stub_llm = StubClient(canned_response="x")
        read_chart(SAMPLE_CHART, rag_service=rag, llm_client=stub_llm)
        topics_used = [c["topic"] for c in rag.calls]
        # MD section MUST request topic="dasha.vimshottari"
        assert "dasha.vimshottari" in topics_used


# --------------------------------------------------------------------------- #
# HTTP route tests                                                             #
# --------------------------------------------------------------------------- #

class TestReadingPage:
    @pytest.mark.asyncio
    async def test_page_renders(self, client):
        resp = await client.get("/medini/reading/page")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Chart Reader" in resp.text


class TestReadingEndpoint:
    @pytest.mark.asyncio
    async def test_post_returns_reading_envelope(self, client, monkeypatch):
        """POST with valid birth data returns the reading envelope.
        Patch read_chart to bypass RAG + LLM so the test is fast +
        offline-safe."""
        from app.medini.services.chart_reader import (
            Reading, ReadingSection, Citation,
        )

        def fake_read(chart, **kwargs):
            return Reading(
                chart_summary={"ascendant": chart.get("ascendant", {})},
                sections=(
                    ReadingSection(
                        title="Test section", text="test reading text",
                        citations=(
                            Citation(
                                source="bphs", title="t", snippet="s",
                                source_url=None, local_path=None, score=0.5,
                            ),
                        ),
                    ),
                ),
                source="deterministic", model=None, n_citations_total=1,
            )
        monkeypatch.setattr(
            "app.api.reading_routes.read_chart", fake_read,
        )

        resp = await client.post(
            "/medini/reading",
            json={
                "year": 1990, "month": 7, "day": 15,
                "hour": 12, "minute": 0,
                "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "chart_summary" in body
        assert "sections" in body and len(body["sections"]) == 1
        assert body["sections"][0]["title"] == "Test section"
        assert len(body["sections"][0]["citations"]) == 1
        assert body["source"] == "deterministic"
        assert body["n_citations_total"] == 1
