"""/rectify is retired: event-based birth-time rectification was circular and was removed
on 2026-11-05. Every old call must fail loudly (410) and carry the replacement policy, so a
client can never silently receive a time fitted to the user's own life events."""
from __future__ import annotations

import pytest

_OLD_BODY = {
    "mode": "rectify",
    "year": 2001, "month": 6, "day": 15,
    "latitude": 28.6, "longitude": 77.2, "tz_offset": 5.5,
    "stated_hour": 12, "stated_minute": 0,
    "events": [{"event_type": "marriage", "year": 2025, "month": 1}],
}


class TestRetired:
    @pytest.mark.asyncio
    async def test_post_is_gone_and_returns_no_time(self, client):
        resp = await client.post("/rectify", json=_OLD_BODY)
        assert resp.status_code == 410
        body = resp.json()
        assert body["status"] == "retired"
        text = str(body).lower()
        assert "candidates" not in body and "best" not in body
        assert "dated life events" in text

    @pytest.mark.asyncio
    async def test_event_types_is_gone(self, client):
        resp = await client.get("/rectify/event-types")
        assert resp.status_code == 410

    @pytest.mark.asyncio
    async def test_policy_names_the_sensitivity_report(self, client):
        resp = await client.get("/rectify/policy")
        assert resp.status_code == 200
        body = resp.json()
        joined = " ".join(body["what_the_engine_does_instead"])
        assert "60 minutes" in joined and "-20 .. +20" in joined


def test_the_rectification_engine_is_gone():
    """No module may come back that fits a birth time to life events."""
    import importlib.util
    for mod in ("app.raman_saab.rectification", "app.core.birth_time_rectification"):
        assert importlib.util.find_spec(mod) is None, mod
