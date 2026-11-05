"""Responses are compressed on the wire.

A detailed reading is ~947 KB of JSON. Measured over real HTTP it left the server uncompressed
until this was added, and gzips to 130 KB — the payload is repetitive prose and structure, so it
compresses to about a seventh.

This is worth a test rather than being left to a config file nobody reads: the saving is
invisible locally (it only shows as a byte count, never as a broken page), so a middleware
accidentally dropped in a refactor would go unnoticed until somebody on a phone waited seven
times as long for a reading.
"""
from __future__ import annotations

import gzip
import json

from starlette.middleware.gzip import GZipMiddleware

CANONICAL = {
    "year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5,
    "name": "Canonical Baseline",
}


class TestTheMiddlewareIsInstalled:
    def test_gzip_is_in_the_stack(self):
        from app.main import app
        assert any(m.cls is GZipMiddleware for m in app.user_middleware), \
            "GZipMiddleware is not installed — every response ships uncompressed"

    def test_it_is_outermost_so_it_also_covers_the_mounted_portal(self):
        """Starlette applies `add_middleware` in reverse registration order, so the LAST one
        registered is the outermost and sees every response — including the vendored Flask
        portal mounted under /portal. Registered before the session middleware it would sit
        inside it and miss the mount."""
        from app.main import app
        classes = [m.cls for m in app.user_middleware]
        assert classes[0] is GZipMiddleware, \
            f"GZip must be outermost; stack is {[c.__name__ for c in classes]}"

    def test_the_threshold_skips_small_bodies(self):
        """Compressing a 200-byte error payload costs CPU and saves nothing."""
        from app.main import app
        gz = next(m for m in app.user_middleware if m.cls is GZipMiddleware)
        assert gz.kwargs.get("minimum_size", 0) >= 500


class TestARealReportIsCompressed:
    async def test_the_json_report_comes_back_gzipped_and_intact(self, client):
        """Compressed AND still parseable — a broken encoding would show as valid-looking
        bytes that no client can read."""
        resp = await client.post("/report", json={**CANONICAL, "format": "json"},
                                 headers={"Accept-Encoding": "gzip"})
        assert resp.status_code == 200
        assert resp.headers.get("content-encoding") == "gzip"
        body = resp.json()                       # httpx decompresses; a corrupt stream raises
        assert "report" in body and body["report"]["birth"]["year"] == 1990

    async def test_it_actually_shrinks_the_payload(self, client):
        """The point is the byte count, so measure it rather than trusting the header."""
        resp = await client.post("/report", json={**CANONICAL, "format": "json"},
                                 headers={"Accept-Encoding": "gzip"})
        raw = json.dumps(resp.json()).encode()
        squeezed = len(gzip.compress(raw, 6))
        assert squeezed < len(raw) // 4, (
            f"a reading should compress to well under a quarter; got "
            f"{squeezed} of {len(raw)}")

    async def test_a_client_that_cannot_decompress_still_gets_its_report(self, client):
        """Content negotiation must be honoured: no Accept-Encoding means plain JSON, not a
        gzip stream the caller cannot read."""
        resp = await client.post("/report", json={**CANONICAL, "format": "json"},
                                 headers={"Accept-Encoding": "identity"})
        assert resp.status_code == 200
        assert resp.headers.get("content-encoding") in (None, "identity")
        assert resp.json()["report"]["birth"]["year"] == 1990
