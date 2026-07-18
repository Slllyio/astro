"""Integration tests for the /rectify/* endpoints — the FastAPI surface over the
birth-time rectification engine. Uses the app-bound httpx client fixture.
"""
from __future__ import annotations

import pytest

_RECT_CASE = {
    "mode": "rectify",
    "year": 1989, "month": 10, "day": 12,
    "latitude": 27.23, "longitude": 79.03, "tz_offset": 5.5,
    "stated_hour": 10, "stated_minute": 2, "window_minutes": 30,
    "events": [
        {"event_type": "career_start", "year": 2016, "month": 2},
        {"event_type": "marriage", "year": 2017, "month": 12, "day": 4},
        {"event_type": "childbirth", "year": 2018, "month": 9},
        {"event_type": "childbirth", "year": 2024, "month": 3, "day": 26},
        {"event_type": "career_change", "year": 2026, "month": 3},
    ],
    "facts": [{"subject": "mother", "observed": "afflicted"}],
}


class TestEventTypes:
    @pytest.mark.asyncio
    async def test_lists_the_taxonomy_with_citations(self, client):
        resp = await client.get("/rectify/event-types")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 15
        keys = {e["key"] for e in body["event_types"]}
        assert {"marriage", "childbirth", "career_start"} <= keys
        marriage = next(e for e in body["event_types"] if e["key"] == "marriage")
        assert marriage["house"] == 7 and ":" in marriage["citation"]


class TestRectify:
    @pytest.mark.asyncio
    async def test_reproduces_the_rect_case_conclusion(self, client):
        """End-to-end over HTTP: raman wins with a positive margin, both tracks present,
        the resolution statement is interval-only, and next questions are offered."""
        resp = await client.post("/rectify", json=_RECT_CASE)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ranked"][0]["ayanamsa"] == "raman"
        assert body["ayanamsa_verdict"]["winner"] == "raman"
        assert body["ayanamsa_verdict"]["margin"] > 0
        ays = {row["ayanamsa"] for row in body["ayanamsa_verdict"]["best_by_ayanamsa"]}
        assert ays == {"raman", "lahiri"}
        assert "CLASS INTERVAL" in body["resolution_statement"]
        # channel subtotals are exposed, never one opaque number
        assert set(body["ranked"][0]["channels"]) >= {
            "event_lords", "event_houses", "facts", "arithmetic", "total"}
        # each event carries its active-house panel
        assert all("active_panel" in es for es in body["ranked"][0]["events"])
        assert body["suggestions"]

    @pytest.mark.asyncio
    async def test_discover_mode_needs_no_time(self, client):
        payload = {"mode": "discover", "year": 1989, "month": 10, "day": 12,
                   "latitude": 27.23, "longitude": 79.03, "tz_offset": 5.5,
                   "events": [{"event_type": "marriage", "year": 2017, "month": 12, "day": 4}],
                   "top_k": 4}
        resp = await client.post("/rectify", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["mode"] == "discover"
        assert body["ranked"]
        lo, hi = body["ranked"][0]["class_interval_local"]
        assert lo != hi                       # a class interval, never a point


class TestValidation:
    @pytest.mark.asyncio
    async def test_rectify_without_time_is_400(self, client):
        payload = {**_RECT_CASE}
        payload.pop("stated_hour")
        resp = await client.post("/rectify", json=payload)
        assert resp.status_code == 400
        assert "stated_hour" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_no_evidence_is_400(self, client):
        payload = {"mode": "rectify", "year": 1989, "month": 10, "day": 12,
                   "latitude": 27.23, "longitude": 79.03, "tz_offset": 5.5,
                   "stated_hour": 10, "stated_minute": 2}
        resp = await client.post("/rectify", json=payload)
        assert resp.status_code == 400
        assert "evidence" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_unknown_event_type_is_400(self, client):
        payload = {"mode": "rectify", "year": 1989, "month": 10, "day": 12,
                   "latitude": 27.23, "longitude": 79.03, "tz_offset": 5.5,
                   "stated_hour": 10, "stated_minute": 2,
                   "events": [{"event_type": "coronation", "year": 2010}]}
        resp = await client.post("/rectify", json=payload)
        assert resp.status_code == 400
        assert "coronation" in resp.json()["detail"] or "valid" in resp.json()["detail"]
