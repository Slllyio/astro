"""Integration tests for the /vargas/* endpoints — the FastAPI surface over the
Shodasavarga judge. Uses the app-bound httpx client fixture. The birth is the
field_case_01 nativity, so the HTTP response must reproduce the pinned varga facts.
"""
from __future__ import annotations

import pytest

_BIRTH = {
    "year": 1989, "month": 10, "day": 12, "hour": 10, "minute": 2,
    "latitude": 27.23, "longitude": 79.03, "tz_offset": 5.5, "ayanamsa": "raman",
}


class TestDivisions:
    @pytest.mark.asyncio
    async def test_lists_the_domain_table_with_citations(self, client):
        resp = await client.get("/vargas/divisions")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 16
        by_n = {d["n"]: d for d in body["divisions"]}
        assert set(by_n) == {1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60}
        assert "children" in by_n[7]["domain"]           # the Raman-explicit row
        assert by_n[7]["citation"].startswith("HPA-11:")


class TestVargaReport:
    @pytest.mark.asyncio
    async def test_reproduces_field_case_varga_facts(self, client):
        """End-to-end over HTTP: the 16-division report reproduces the pinned facts —
        D9 vargottama lagna, D7 Mars+Ketu on the children-varga lagna, D10 own-sign
        career lagna lord."""
        resp = await client.post("/vargas", json=_BIRTH)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ayanamsa"] == "raman"
        assert body["lagna"]["sign_name"] == "Scorpio"
        by_n = {r["n"]: r for r in body["readings"]}
        assert len(by_n) == 16

        assert by_n[9]["lagna"]["vargottama"] is True
        assert by_n[7]["malefics_on_lagna"] == ["Mars", "Ketu"]
        d10 = by_n[10]["lagna_lord"]
        assert d10["planet"] == "Jupiter" and d10["dignity"] == "own" and d10["house"] == 1

        merc = next(v for v in body["vargavisesha"] if v["planet"] == "Mercury")
        assert merc["label"] == "Parvathamsa" and merc["own_varga_count"] == 3

    @pytest.mark.asyncio
    async def test_lahiri_frame_is_accepted(self, client):
        resp = await client.post("/vargas", json={**_BIRTH, "ayanamsa": "lahiri"})
        assert resp.status_code == 200
        assert resp.json()["ayanamsa"] == "lahiri"

    @pytest.mark.asyncio
    async def test_rejects_unsupported_ayanamsa(self, client):
        resp = await client.post("/vargas", json={**_BIRTH, "ayanamsa": "kp"})
        assert resp.status_code == 422        # pydantic Literal rejects before the handler

    @pytest.mark.asyncio
    async def test_rejects_unknown_field(self, client):
        resp = await client.post("/vargas", json={**_BIRTH, "bogus": 1})
        assert resp.status_code == 422        # extra="forbid"
