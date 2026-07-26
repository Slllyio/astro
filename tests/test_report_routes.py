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
