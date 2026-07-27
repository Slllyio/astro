"""Integration tests for the /report/* endpoints — the FastAPI surface over
`detailed_report.build_detailed_report`. Uses the app-bound httpx client fixture. The birth
is the canonical Bangalore 1990 baseline (CLAUDE.md), so the response must reproduce its
pinned facts (Virgo lagna, Mercury/Sun ruler) end to end over HTTP.
"""
from __future__ import annotations

import pytest

_BIRTH = {
    "year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5, "ayanamsa": "lahiri",
}


class TestSections:
    @pytest.mark.asyncio
    async def test_lists_the_section_contract(self, client):
        resp = await client.get("/report/sections")
        assert resp.status_code == 200
        body = resp.json()
        ids = [s["id"] for s in body["sections"]]
        assert body["count"] == len(ids)
        # the synthesis sections added this arc are present, in document order
        for sid in ("ruler", "house_strength", "preponderance", "life_chapters", "nichod"):
            assert sid in ids
        assert ids.index("ruler") < ids.index("preponderance") < ids.index("nichod")


class TestReport:
    @pytest.mark.asyncio
    async def test_markdown_report_reproduces_canonical_facts(self, client):
        """End-to-end over HTTP: the Markdown report carries the pinned canonical facts and the
        structured summary agrees with the prose."""
        resp = await client.post("/report", json=_BIRTH)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["format"] == "markdown" and body["ayanamsa"] == "lahiri"
        assert "# Detailed reading" in body["report"]
        assert "## Ruler of the nativity" in body["report"]
        assert "## Preponderance of testimonies" in body["report"]
        s = body["summary"]
        assert s["lagna"] == "Virgo"
        assert s["ruler_of_nativity"]["lagna_lord"] == "Mercury"
        assert s["ruler_of_nativity"]["strongest_planet"] == "Sun"
        assert s["longevity"]["class"] in {"alpa", "madhya", "purna"}

    @pytest.mark.asyncio
    async def test_html_format_returns_a_standalone_document(self, client):
        resp = await client.post("/report", json={**_BIRTH, "format": "html"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["format"] == "html"
        assert "<!doctype html>" in body["report"].lower() or "<html" in body["report"].lower()
        assert 'id="ruler"' in body["report"]

    @pytest.mark.asyncio
    async def test_window_params_are_accepted(self, client):
        resp = await client.post("/report", json={**_BIRTH, "years_back": 5, "years_forward": 5})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_rejects_unsupported_ayanamsa(self, client):
        resp = await client.post("/report", json={**_BIRTH, "ayanamsa": "kp"})
        assert resp.status_code == 422        # pydantic Literal rejects before the handler

    @pytest.mark.asyncio
    async def test_rejects_unknown_field(self, client):
        resp = await client.post("/report", json={**_BIRTH, "bogus": 1})
        assert resp.status_code == 422        # extra="forbid"

    @pytest.mark.asyncio
    async def test_json_format_returns_the_structured_report(self, client):
        """format=json returns the structured grounding contract, not a rendered string."""
        resp = await client.post("/report", json={**_BIRTH, "format": "json"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["format"] == "json"
        rep = body["report"]
        assert isinstance(rep, dict)
        assert rep["ruler"]["lagna_lord"] == "Mercury"
        assert len(rep["house_strength"]) == 12
        assert rep["yogas"][0]["source"].keys() >= {"work", "line"}


class TestPage:
    @pytest.mark.asyncio
    async def test_report_page_serves_the_interactive_shell(self, client):
        """GET /report/page returns the static shell wired to POST /report?format=json and the
        /report/source click-to-source backend."""
        resp = await client.get("/report/page")
        assert resp.status_code == 200
        html = resp.text
        assert "<!DOCTYPE html>" in html
        assert "fetch('/report'" in html          # client fetches the JSON report
        assert "/report/source" in html            # click-to-source wiring
        assert "format:'json'" in html or 'format:"json"' in html
        # the page must render EVERY section of the full report — not a curated subset
        for heading in ("Your Reading", "Chart signature", "Ruler of the nativity",
                        "Planetary positions", "Yogas", "Ashtakavarga", "House-by-house",
                        "House strength cross-check", "Preponderance of testimonies",
                        "The twelve matters", "Longevity", "Life-narrative", "Life-chapters",
                        "Transits", "Divisional deep-reads", "Soul & destiny", "Pitru dosha",
                        "Integrated insights", "What stands out", "Information content",
                        "Nichod"):
            assert heading in html, f"interactive page dropped section: {heading}"
        # the grounded explainer + Q&A wiring is present
        assert "/report/explain" in html and "/report/ask" in html
        assert "never a prediction" in html
        # the "What matters most" digest panel + its grounded synthesis wiring
        assert "What matters most" in html
        assert "/report/insights" in html
        assert "Read this as one story" in html


class TestSource:
    @pytest.mark.asyncio
    async def test_resolves_a_canon_citation_to_verbatim_lines(self, client):
        """A Raman-canon citation token returns the exact source lines (click-to-source)."""
        resp = await client.get("/report/source", params={"cite": "HTJAH-I:468-478"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["resolved"] is True
        assert body["work"] == "HTJAH-I" and body["start"] == 468 and body["end"] == 478
        assert "strength of the house" in body["text"].lower()

    @pytest.mark.asyncio
    async def test_classical_noncitable_is_deferred_not_shown(self, client):
        """A CLASSICAL_NONCITABLE token (BPHS) is not resolved — the firewall holds — and the
        response says so truthfully rather than returning the verse."""
        resp = await client.get("/report/source", params={"cite": "BPHS-83-iii:70"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["resolved"] is False
        assert "classical" in body["note"].lower()

    @pytest.mark.asyncio
    async def test_malformed_cite_is_handled(self, client):
        resp = await client.get("/report/source", params={"cite": "not-a-citation"})
        assert resp.status_code == 200 and resp.json()["resolved"] is False


class TestExplainAndAsk:
    """The grounded LLM endpoints. In CI the LLM is disabled (no key), so both must serve the
    truthful deterministic fallback — never a fabricated explanation, always the honesty note."""

    @pytest.mark.asyncio
    async def test_explain_falls_back_to_engine_prose_without_a_key(self, client):
        resp = await client.post("/report/explain", json={**_BIRTH, "scope": "house:1"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source"] == "fallback"
        assert "not a validated prediction" in body["honesty_note"].lower()
        assert "House 1 reads" in body["text"]

    @pytest.mark.asyncio
    async def test_explain_summary_scope(self, client):
        resp = await client.post("/report/explain", json={**_BIRTH, "scope": "summary"})
        assert resp.status_code == 200
        assert resp.json()["source"] == "fallback"
        assert resp.json()["text"]

    @pytest.mark.asyncio
    async def test_ask_falls_back_and_carries_the_honesty_note(self, client):
        resp = await client.post("/report/ask",
                                 json={**_BIRTH, "question": "why is my career contested?"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source"] == "fallback"
        assert body["honesty_note"]

    @pytest.mark.asyncio
    async def test_ask_requires_a_question(self, client):
        resp = await client.post("/report/ask", json={**_BIRTH})
        assert resp.status_code == 422        # question is required

    @pytest.mark.asyncio
    async def test_insights_falls_back_to_the_ranked_digest(self, client):
        """The prioritized whole-chart synthesis. With no key it must serve the engine's OWN ranked
        digest as prose — the honesty headline plus the ranked items — never a fabricated reading."""
        resp = await client.post("/report/insights", json={**_BIRTH})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source"] == "fallback"
        assert "not a validated prediction" in body["honesty_note"].lower()
        assert "readings" in body["text"]            # the info-content headline is present
        assert len(body["text"]) > 100               # the ranked items, not an empty stub
