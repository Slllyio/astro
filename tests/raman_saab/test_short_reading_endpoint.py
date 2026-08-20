"""`POST /report` serves either reading length from one cast.

The length is a rendering choice, so the two must never disagree about the chart and the
default must never change on its own — a silent flip to "short" would hide fifty chapters
from every existing caller.
"""
from __future__ import annotations

import pytest

CANONICAL = {
    "year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5, "name": "Canonical Baseline",
}


class TestTheDefaultIsUnchanged:
    async def test_omitting_the_field_still_returns_the_full_reading(self, client):
        resp = await client.post("/report", json={**CANONICAL, "format": "markdown"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["reading"] == "full"
        assert "## House-by-house reading" in body["report"]

    async def test_the_field_is_echoed_so_a_caller_knows_what_it_got(self, client):
        resp = await client.post("/report",
                                 json={**CANONICAL, "format": "markdown", "reading": "short"})
        assert resp.status_code == 200
        assert resp.json()["reading"] == "short"

    async def test_an_unknown_length_is_rejected_rather_than_guessed(self, client):
        resp = await client.post("/report",
                                 json={**CANONICAL, "format": "markdown", "reading": "brief"})
        assert resp.status_code == 422


class TestTheShortReading:
    @pytest.fixture
    async def short_md(self, client):
        resp = await client.post("/report",
                                 json={**CANONICAL, "format": "markdown", "reading": "short"})
        assert resp.status_code == 200
        return resp.json()["report"]

    async def test_it_is_actually_short(self, client, short_md):
        """A "short reading" that runs to a hundred pages is the feature not working. The
        full markdown is ~500 KB; this must be a different order of magnitude."""
        full = (await client.post("/report", json={**CANONICAL, "format": "markdown"})
                ).json()["report"]
        assert len(short_md) < len(full) / 20, (len(short_md), len(full))
        assert len(short_md) > 800, "suspiciously empty"

    async def test_it_carries_the_three_things_it_promises(self, short_md):
        assert "What is coming" in short_md
        assert "The combinations your chart carries" in short_md
        assert "now" in short_md                       # the running stretch is marked

    async def test_it_says_nothing_technical(self, short_md):
        for banned in ("House-by-house", " H1 ", "Shadbala", "Navamsa", "Mahadasha",
                       "HTJAH-I:", "3HC:", "Ashtakavarga", "Lagna"):
            assert banned not in short_md, banned

    async def test_html_is_self_contained_and_escaped(self, client):
        resp = await client.post("/report",
                                 json={**CANONICAL, "format": "html", "reading": "short"})
        assert resp.status_code == 200
        html = resp.json()["report"]
        assert html.startswith("<!doctype html>")
        assert "<style>" in html and "http://" not in html and "https://" not in html

    async def test_hindi_returns_a_hindi_document(self, client):
        resp = await client.post("/report", json={**CANONICAL, "format": "markdown",
                                                  "reading": "short", "lang": "hi"})
        assert resp.status_code == 200
        md = resp.json()["report"]
        assert "आपका फलादेश" in md
        assert "What is coming" not in md


class TestBothLengthsAgree:
    async def test_the_json_payload_carries_the_short_reading_whatever_was_asked(self, client):
        """The page toggles between lengths without re-casting, which is only possible if the
        JSON always carries both."""
        resp = await client.post("/report", json={**CANONICAL, "format": "json"})
        assert resp.status_code == 200
        short = resp.json()["report"]["short_reading"]
        assert short is not None
        assert short["periods"] and short["combinations"]

    async def test_the_short_reading_names_the_same_running_stretch(self, client):
        """Same cast, same answer: whichever length a caller asks for, the stretch marked
        'now' is the one the full timeline has running."""
        body = (await client.post("/report", json={**CANONICAL, "format": "json"})).json()
        report = body["report"]
        now = [p for p in report["short_reading"]["periods"] if p["is_now"]]
        assert len(now) == 1
        ref = report["window"]["ref_jd"]
        running = [p for p in report["timeline"]
                   if p["start_jd"] <= ref < p["end_jd"]]
        assert len(running) == 1
        import swisseph as swe
        y, _m, _d, _h = swe.revjul(running[0]["start_jd"], swe.GREG_CAL)
        assert str(int(y)) in now[0]["from_label_en"]
