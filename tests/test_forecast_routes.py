"""Integration tests for /medini/forecast/* endpoints.

The forecast engine itself touches swisseph (real ephemeris) — we exercise
end-to-end with small horizons (3 days) to keep tests fast, plus a mock
of the RAG service for the citations layer (so we don't depend on the
embeddings file being built).
"""
from __future__ import annotations

import pytest

from app.medini.services.knowledge_search import (
    SearchResult,
    reset_default_service,
)


def _fake_result(chunk_id: str) -> SearchResult:
    return SearchResult(
        chunk_id=chunk_id, score=0.5, source="bphs",
        title=f"BPHS {chunk_id}", snippet="x" * 100,
        source_url=f"http://x/{chunk_id}", local_path=f"/local/{chunk_id}.md",
        artefact_id=f"art-{chunk_id}", topics=(), n_tokens=100,
    )


class StubService:
    def search(self, *args, **kwargs):
        return (_fake_result("c0"),)


# --------------------------------------------------------------------------- #
# /domains                                                                      #
# --------------------------------------------------------------------------- #

class TestDomainsEndpoint:
    @pytest.mark.asyncio
    async def test_returns_full_catalog(self, client):
        """All entries in the DOMAINS dict come through with required fields."""
        resp = await client.get("/medini/forecast/domains")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 12  # we have 13 domains, allow slack
        for d in body["domains"]:
            assert {"key", "label", "icon", "description"} <= set(d)


# --------------------------------------------------------------------------- #
# /forecast                                                                     #
# --------------------------------------------------------------------------- #

class TestForecastEndpoint:
    @pytest.mark.asyncio
    async def test_default_request_returns_envelope(self, client):
        """No params → 30-day horizon, severity+domains on, citations off."""
        resp = await client.get(
            "/medini/forecast", params={"horizon_days": 3},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["horizon_days"] == 3
        assert "events" in body
        assert "by_day" in body
        assert "summary" in body
        assert body["layers_applied"]["severity"] is True
        assert body["layers_applied"]["citations"] is False

    @pytest.mark.asyncio
    async def test_horizon_clamped_to_90(self, client):
        """Out-of-range horizon → 422 (Pydantic Query validation)."""
        resp = await client.get(
            "/medini/forecast", params={"horizon_days": 365},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_severity_layer_optional(self, client):
        """include_severity=false → no severity field on events."""
        resp = await client.get(
            "/medini/forecast",
            params={"horizon_days": 3, "include_severity": "false"},
        )
        assert resp.status_code == 200
        body = resp.json()
        for e in body["events"]:
            assert "severity" not in e
        assert body["layers_applied"]["severity"] is False

    @pytest.mark.asyncio
    async def test_domains_layer_optional(self, client):
        resp = await client.get(
            "/medini/forecast",
            params={"horizon_days": 3, "include_domains": "false"},
        )
        assert resp.status_code == 200
        body = resp.json()
        for e in body["events"]:
            assert "domains" not in e

    @pytest.mark.asyncio
    async def test_top_events_present_when_severity_on(self, client):
        resp = await client.get(
            "/medini/forecast", params={"horizon_days": 7},
        )
        body = resp.json()
        assert "top_events" in body
        assert len(body["top_events"]) <= 5
        # top_events must be sorted by severity desc
        sevs = [e["severity"] for e in body["top_events"]]
        assert sevs == sorted(sevs, reverse=True)

    @pytest.mark.asyncio
    async def test_citations_layer_with_stub_service(self, client, monkeypatch):
        """include_citations=true triggers the RAG path; patch the singleton
        to a stub so the test doesn't require the embeddings file."""
        monkeypatch.setattr(
            "app.medini.forecast_citations.get_default_service",
            lambda: StubService(),
        )
        reset_default_service()
        resp = await client.get(
            "/medini/forecast",
            params={"horizon_days": 2, "include_citations": "true"},
        )
        assert resp.status_code == 200
        body = resp.json()
        for e in body["events"]:
            assert "citations" in e
            assert isinstance(e["citations"], list)
        assert body["layers_applied"]["citations"] is True

    @pytest.mark.asyncio
    async def test_daily_summary_layer_attaches_per_day_summary(self, client):
        """include_daily_summary=true → daily_summaries dict keyed by date
        with the deterministic template (Ollama disabled in tests)."""
        resp = await client.get(
            "/medini/forecast",
            params={"horizon_days": 5, "include_daily_summary": "true"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "daily_summaries" in body
        assert body["layers_applied"]["daily_summary"] is True
        # Every key in by_day must have a summary
        for date in body["by_day"].keys():
            assert date in body["daily_summaries"]
            summary = body["daily_summaries"][date]
            assert summary["source"] == "deterministic"  # OLLAMA disabled in tests
            assert isinstance(summary["summary"], str) and summary["summary"]


# --------------------------------------------------------------------------- #
# /medini/almanac (backward-looking)                                            #
# --------------------------------------------------------------------------- #

class TestAlmanacEndpoint:
    @pytest.mark.asyncio
    async def test_almanac_returns_backward_envelope(self, client):
        """Same shape as forecast but `days_back` and `direction=backward`."""
        resp = await client.get(
            "/medini/almanac", params={"days_back": 5},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["direction"] == "backward"
        assert body["days_back"] == 5
        assert "horizon_days" not in body  # renamed in almanac envelope
        assert "events" in body
        assert "by_day" in body

    @pytest.mark.asyncio
    async def test_almanac_clamps_days_back_to_90(self, client):
        resp = await client.get(
            "/medini/almanac", params={"days_back": 200},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_almanac_events_are_before_or_equal_to_now(self, client):
        """Almanac walks backward — every event JD must be < now + 1 day
        (giving some slack for the daily scan step)."""
        import swisseph as swe
        import datetime as dt
        now = dt.datetime.now(dt.timezone.utc)
        jd_now = swe.julday(
            now.year, now.month, now.day,
            now.hour + now.minute/60.0, swe.GREG_CAL,
        )
        resp = await client.get(
            "/medini/almanac", params={"days_back": 7},
        )
        assert resp.status_code == 200
        for e in resp.json()["events"]:
            assert e["jd"] <= jd_now + 1.0, (
                f"almanac event in the future: jd={e['jd']} > now={jd_now}"
            )

    @pytest.mark.asyncio
    async def test_almanac_supports_daily_summary_layer(self, client):
        resp = await client.get(
            "/medini/almanac",
            params={"days_back": 5, "include_daily_summary": "true"},
        )
        body = resp.json()
        assert "daily_summaries" in body
        assert body["layers_applied"]["daily_summary"] is True

    @pytest.mark.asyncio
    async def test_almanac_top_events_use_newest_tiebreak(self, client):
        """top_events are severity-desc, ties broken by NEWEST (-jd) so the
        most-recent severe event surfaces first in almanac view."""
        resp = await client.get(
            "/medini/almanac", params={"days_back": 30},
        )
        body = resp.json()
        # Group by severity and verify within each group jds are descending
        if not body.get("top_events"):
            return
        prev_sev = None
        prev_jd = None
        for e in body["top_events"]:
            sev = e.get("severity", 0)
            if prev_sev is not None and sev == prev_sev:
                assert e["jd"] <= prev_jd, "ties not newest-first"
            prev_sev = sev
            prev_jd = e["jd"]


class TestAlmanacPage:
    @pytest.mark.asyncio
    async def test_page_renders(self, client):
        resp = await client.get("/medini/almanac/page")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Mundane Almanac" in resp.text


# --------------------------------------------------------------------------- #
# /forecast/cache-clear                                                         #
# --------------------------------------------------------------------------- #

class TestCacheClear:
    @pytest.mark.asyncio
    async def test_cache_clear_drops_both_caches(self, client):
        """POST /forecast/cache-clear empties daily-summary + event-text
        LRUs and reports how many entries were dropped."""
        from app.medini.forecast_cache import (
            get_daily_summary_cache,
            reset_daily_summary_cache,
        )
        from app.medini.forecast_event_text import (
            get_event_text_cache,
            reset_event_text_cache,
        )
        reset_daily_summary_cache()
        reset_event_text_cache()
        # Seed both caches with one entry each so the clear has something
        # observable to drop.
        get_daily_summary_cache().put("k1", "v1")
        get_event_text_cache().put("k2", ("v2", True))

        resp = await client.post("/medini/forecast/cache-clear")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {
            "cleared": True,
            "daily_summary_entries_dropped": 1,
            "event_text_entries_dropped": 1,
        }
        # Caches are now empty
        assert get_daily_summary_cache().size == 0
        assert get_event_text_cache().size == 0

    @pytest.mark.asyncio
    async def test_cache_clear_get_not_allowed(self, client):
        """Cache-clear mutates state — must be POST, not GET."""
        resp = await client.get("/medini/forecast/cache-clear")
        assert resp.status_code in (405, 404)  # Method not allowed


# --------------------------------------------------------------------------- #
# /forecast/page                                                                #
# --------------------------------------------------------------------------- #

class TestForecastPage:
    @pytest.mark.asyncio
    async def test_page_renders(self, client):
        resp = await client.get("/medini/forecast/page")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Mundane Forecast" in resp.text


# --------------------------------------------------------------------------- #
# Today page cross-link                                                         #
# --------------------------------------------------------------------------- #

class TestTodayCrosslink:
    @pytest.mark.asyncio
    async def test_today_page_links_to_forecast(self, client):
        """The /today page must surface a link to /forecast so users can
        find the new view from where they already are."""
        resp = await client.get("/medini/today/page")
        assert resp.status_code == 200
        assert "/medini/forecast/page" in resp.text
