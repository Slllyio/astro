"""Integration tests for GET /electional/today — the FastAPI surface over the walled
`app.raman_saab.electional` subsystem. The native is the canonical Bangalore 1990 baseline
(CLAUDE.md), so the janma star/rasi the route derives are the pinned Revati/Pisces facts.
"""
from __future__ import annotations

import pytest

# Canonical baseline native: Bangalore 1990-07-15 12:00 IST (CLAUDE.md test-pinning policy).
_NATIVE = {
    "year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5, "ayanamsa": "lahiri",
}


class TestElectionalToday:
    @pytest.mark.asyncio
    async def test_canonical_birth_returns_the_full_electional_shape(self, client):
        """Every contracted key is present and the native's janma star/rasi are the pinned
        Moon-in-Revati (nakshatra 27) / Pisces (rasi 12) baseline facts."""
        resp = await client.get("/electional/today",
                                params={**_NATIVE, "date": "2026-08-03"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.keys() >= {"date", "moment", "native", "ok", "hard_failures", "score",
                               "tarabala", "chandrabala", "limbs", "panchaka",
                               "transit_elections", "negative_windows", "disclaimer"}
        assert body["date"] == "2026-08-03"
        assert body["native"] == {"janma_nakshatra": 27, "janma_rasi": 12}

    @pytest.mark.asyncio
    async def test_tarabala_and_limbs_are_cited_and_well_formed(self, client):
        """Tarabala is one of Raman's nine taras and every panchanga limb carries a
        MUHURTHA citation (MUHURTHA-3:34-63; MUHURTHA-2/3/8/18)."""
        resp = await client.get("/electional/today",
                                params={**_NATIVE, "date": "2026-08-03"})
        body = resp.json()
        tb = body["tarabala"]
        assert 1 <= tb["tara"] <= 9
        assert tb["name"] in {"Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhana",
                              "Naidhana", "Mitra", "Parama Mitra"}
        assert tb["source"].startswith("MUHURTHA-3:")
        limbs = {lv["limb"]: lv for lv in body["limbs"]}
        assert set(limbs) == {"tithi", "vara", "nakshatra", "yoga", "karana"}
        assert all(lv["source"].startswith("MUHURTHA-") for lv in limbs.values())
        assert 1 <= limbs["tithi"]["value"] <= 15
        assert 0 <= limbs["vara"]["value"] <= 6

    @pytest.mark.asyncio
    async def test_negative_windows_are_local_iso_times_in_order(self, client):
        """Rahu Kalam plus the day's durmuhurthas come back as ISO local timestamps, each a
        real forward-running window."""
        resp = await client.get("/electional/today",
                                params={**_NATIVE, "date": "2026-08-03"})
        windows = resp.json()["negative_windows"]
        assert any(w["label"] == "Rahu Kalam" for w in windows)
        assert any(w["label"].startswith("Durmuhurtha (nocturnal") for w in windows)
        for w in windows:
            assert w["start"] < w["end"]
            assert "+05:30" in w["start"]        # rendered at the caller's tz_offset

    @pytest.mark.asyncio
    async def test_transit_elections_cover_the_seven_grahas_with_asp15_citations(self, client):
        """ASP ch.XV states a band rule for each of the seven visible grahas and none for the
        nodes (chayagrahas carry no Bhinnashtakavarga election)."""
        resp = await client.get("/electional/today",
                                params={**_NATIVE, "date": "2026-08-03"})
        te = resp.json()["transit_elections"]
        assert {t["graha"] for t in te} == {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                            "Venus", "Saturn"}
        for t in te:
            assert 1 <= t["transit_sign"] <= 12
            assert 0 <= t["bindus"] <= 8
            assert t["verdict"] in {"auspicious", "mixed", "poor", "forbidden"}
            assert t["source"].startswith("ASP-15:")

    @pytest.mark.asyncio
    async def test_act_selects_ramans_panchaka_exception(self, client):
        """MUHURTHA-3:157-168: an unfavourable panchaka counts favourable unless it is in the
        act's own avoid-set, so naming an act can only ever relax the verdict, never tighten it."""
        params = {**_NATIVE, "date": "2026-08-03"}
        plain = (await client.get("/electional/today", params=params)).json()["panchaka"]
        with_act = (await client.get("/electional/today",
                                     params={**params, "act": "travel"})).json()["panchaka"]
        assert plain["remainder"] == with_act["remainder"]
        assert with_act["favourable"] >= plain["favourable"]

    @pytest.mark.asyncio
    async def test_defaults_to_today_when_no_date_given(self, client):
        from datetime import date

        resp = await client.get("/electional/today", params=_NATIVE)
        assert resp.status_code == 200, resp.text
        assert resp.json()["date"] == date.today().isoformat()

    @pytest.mark.asyncio
    async def test_rejects_out_of_range_birth_params(self, client):
        resp = await client.get("/electional/today", params={**_NATIVE, "month": 13})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_unknown_query_param(self, client):
        resp = await client.get("/electional/today", params={**_NATIVE, "bogus": 1})
        assert resp.status_code == 422        # extra="forbid"
