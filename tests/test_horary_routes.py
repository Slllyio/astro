"""Integration tests for POST /horary/ask — the FastAPI surface over the walled
`app.raman_saab.horary` subsystem. The excluded-topic refusal is the load-bearing case: it
must come back as a 200 carrying `refusal`, because a 500 would be an outage, not a policy.
"""
from __future__ import annotations

import pytest

_ASK = {
    "question": "will the alliance be settled?",
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5,
    "moment": "2026-08-03T10:30:00",
}


class TestPrasnaAsk:
    @pytest.mark.asyncio
    async def test_topic_resolves_to_its_karyesa_house_and_returns_the_full_shape(self, client):
        """PRASNA-49:119-126 — marriage is judged from the 7th lord; the verdict, its cited
        evidence and the ten VARSHA-7 sahams all come back."""
        resp = await client.post("/horary/ask", json={**_ASK, "topic": "marriage"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["query_house"] == 7 and body["refusal"] is None
        v = body["verdict"]
        assert isinstance(v["fulfilled"], bool)
        assert 1 <= v["success_quarters"] <= 4
        assert v["success_percent"] == v["success_quarters"] * 25
        assert v["karyesa"] in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert body["evidence"] and all("PRASNA-49:" in e for e in body["evidence"])
        assert [s["name"] for s in body["sahams"]] == [
            "Punya", "Guru", "Kirti", "Mitra", "Raja", "Putra", "Jeeva", "Vyapara",
            "Vivaha", "Satru"]
        assert all(s["source"].startswith("VARSHA-7:") and 1 <= s["rasi"] <= 12
                   for s in body["sahams"])

    @pytest.mark.asyncio
    async def test_explicit_query_house_bypasses_the_topic_table(self, client):
        resp = await client.post("/horary/ask", json={**_ASK, "query_house": 11})
        assert resp.status_code == 200, resp.text
        assert resp.json()["query_house"] == 11

    @pytest.mark.asyncio
    async def test_death_topic_is_refused_with_http_200(self, client):
        """The coded exclusion (firewall-lift scope rule 3) fires inside judge_prasna: a
        refusal is a policy answer, so it is a 200 with `refusal` set and no verdict."""
        resp = await client.post("/horary/ask",
                                 json={**_ASK, "topic": "death", "query_house": 8})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["refusal"] and "excluded by design" in body["refusal"]
        assert "verdict" not in body and "sahams" not in body

    @pytest.mark.asyncio
    @pytest.mark.parametrize("topic", ["lifespan", "serious_illness", "self_harm"])
    async def test_every_excluded_topic_refuses_without_a_house(self, client, topic):
        """An excluded topic is refused even when it names no house — the route must not 400
        its way past the coded gate."""
        resp = await client.post("/horary/ask", json={**_ASK, "topic": topic})
        assert resp.status_code == 200, resp.text
        assert resp.json()["refusal"] is not None

    @pytest.mark.asyncio
    async def test_invalid_house_is_rejected(self, client):
        for house in (0, 13):
            resp = await client.post("/horary/ask", json={**_ASK, "query_house": house})
            assert resp.status_code == 422, house

    @pytest.mark.asyncio
    async def test_unknown_topic_without_a_house_is_a_400(self, client):
        resp = await client.post("/horary/ask", json={**_ASK, "topic": "lottery"})
        assert resp.status_code == 400
        assert "query_house" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_rejects_unknown_field(self, client):
        resp = await client.post("/horary/ask", json={**_ASK, "topic": "wealth", "bogus": 1})
        assert resp.status_code == 422        # extra="forbid"

    @pytest.mark.asyncio
    async def test_moment_defaults_to_now(self, client):
        payload = {k: v for k, v in _ASK.items() if k != "moment"}
        resp = await client.post("/horary/ask", json={**payload, "topic": "career"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["query_house"] == 10
