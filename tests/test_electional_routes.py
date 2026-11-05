"""Integration tests for GET /electional/today and /electional/scan — the FastAPI surface
over the walled
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


class TestElectionalScan:
    """GET /electional/scan — "WHEN today is clean": the same essentials judgment
    (MUHURTHA-10:226-228) re-applied at interval samples across the sunrise-to-sunrise day."""

    @pytest.mark.asyncio
    async def test_scan_returns_ranked_spans_with_the_framing_intact(self, client):
        """The Measured-Truth framing travels with the spans: the method disclaimer plus the
        scan's own resolution note. Spans are chronological and each carries its rank."""
        resp = await client.get("/electional/scan",
                                params={**_NATIVE, "date": "2026-08-03"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.keys() >= {"date", "interval_minutes", "scan_window", "native",
                               "sample_count", "clean_sample_count", "clean_spans", "best",
                               "blocked_windows", "samples", "disclaimer", "scan_note"}
        assert "never a validated prediction" in body["disclaimer"]
        assert "MUHURTHA-10:226-228" in body["scan_note"]
        assert body["interval_minutes"] == 30
        assert body["native"] == {"janma_nakshatra": 27, "janma_rasi": 12}
        spans = body["clean_spans"]
        assert spans, "2026-08-03 has clean spans for this native"
        assert [s["start_jd"] for s in spans] == sorted(s["start_jd"] for s in spans)
        assert sorted(s["rank"] for s in spans) == list(range(1, len(spans) + 1))
        assert body["best"]["score"] == max(s["score"] for s in spans)
        for s in spans:
            assert s["end_jd"] > s["start_jd"] and s["duration_minutes"] > 0
            assert 0 <= s["score"] <= s["score_max"] <= 8
            assert len(s["passing"]) + len(s["failing"]) == 8
            assert "+05:30" in s["start"] and "+05:30" in s["end"]

    @pytest.mark.asyncio
    async def test_spans_never_overlap_each_other_or_a_blocked_window(self, client):
        """A Rahu Kalam / Durmuhurtha window is a hard failure, so it can never fall inside a
        span the scan calls clean — and two clean spans can never overlap."""
        resp = await client.get("/electional/scan",
                                params={**_NATIVE, "date": "2026-08-03"})
        body = resp.json()
        spans, windows = body["clean_spans"], body["blocked_windows"]
        assert any(w["label"] == "Rahu Kalam" for w in windows)
        stamps = {w["label"]: (w["start"], w["end"]) for w in windows}
        for s in spans:
            for label, (w_start, w_end) in stamps.items():
                assert not (w_start < s["end"] and w_end > s["start"]), f"{label} in {s}"
        for a, b in zip(spans, spans[1:]):
            assert b["start_jd"] >= a["end_jd"]

    @pytest.mark.asyncio
    async def test_every_span_start_reads_clean_on_the_single_moment_route(self, client):
        """Equivalence: the scan claims nothing /electional/today would not. Each span's own
        start instant, re-read one moment at a time, passes with the same essentials score."""
        params = {**_NATIVE, "date": "2026-08-03"}
        spans = (await client.get("/electional/scan", params=params)).json()["clean_spans"]
        assert spans
        for s in spans[:4]:
            hour, minute = (int(x) for x in s["start"][11:16].split(":"))
            # the scan runs sunrise -> next sunrise, so a late span belongs to the NEXT
            # civil date; the single-moment route is asked about that same instant.
            one = (await client.get("/electional/today",
                                    params={**params, "date": s["start"][:10],
                                            "election_hour": hour,
                                            "election_minute": minute})).json()
            assert one["ok"] is True, (s["start"], one["hard_failures"])
            # the span's own start sample: its score sits between the span's guaranteed
            # minimum and the best score any sample of that span reached.
            assert s["score"] <= one["score"] <= s["score_max"]

    @pytest.mark.asyncio
    async def test_samples_cover_the_scan_window_at_the_requested_interval(self, client):
        """The interval is a parameter; every sample is judged and reported (nothing hidden),
        and the clean-sample count matches the samples that actually passed."""
        resp = await client.get("/electional/scan",
                                params={**_NATIVE, "date": "2026-08-03",
                                        "interval_minutes": 60})
        body = resp.json()
        assert body["interval_minutes"] == 60
        samples = body["samples"]
        assert 20 <= len(samples) == body["sample_count"] <= 25
        assert body["clean_sample_count"] == sum(1 for s in samples if s["ok"])
        assert all(set(s) == {"local_iso", "jd", "ok", "score", "hard_failures"}
                   for s in samples)
        assert not any(s["hard_failures"] for s in samples if s["ok"])
        assert body["scan_window"]["start"] >= body["scan_window"]["sunrise"]
        assert body["scan_window"]["end"] == body["scan_window"]["next_sunrise"]

    @pytest.mark.asyncio
    async def test_act_relaxation_can_only_open_spans_never_close_them(self, client):
        """MUHURTHA-3:157-168 again, now across a whole day: naming an act can only lift a
        panchaka hard failure, so the act's scan can never have FEWER clean samples."""
        params = {**_NATIVE, "date": "2026-08-03"}
        plain = (await client.get("/electional/scan", params=params)).json()
        with_act = (await client.get("/electional/scan",
                                     params={**params, "act": "travel"})).json()
        assert with_act["clean_sample_count"] >= plain["clean_sample_count"]

    @pytest.mark.asyncio
    async def test_rejects_an_out_of_range_interval_and_unknown_params(self, client):
        assert (await client.get("/electional/scan",
                                 params={**_NATIVE, "interval_minutes": 1})).status_code == 422
        assert (await client.get("/electional/scan",
                                 params={**_NATIVE, "bogus": 1})).status_code == 422
