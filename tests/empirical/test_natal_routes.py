"""The natal decode API surface, mounted standalone.

Mounted on a throwaway FastAPI() rather than through ``app.main`` — the full
app transitively imports ``app/raman_saab/report_html.py``, whose PEP 701
f-strings do not parse on the container's Python 3.11 (they do in CI's 3.12).
The router itself is the unit under test either way.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.empirical_natal_routes import natal_router
from app.empirical.natal.render import NATAL_FRAMING

CANONICAL = {
    "year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5,
}


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(natal_router)
    return TestClient(app)


class TestPostNatal:
    """The decode endpoint's contract."""

    def test_canonical_birth_returns_framed_json(self, client):
        """A valid birth yields 200 with the framing leading the payload."""
        resp = client.post("/empirical/natal", json=CANONICAL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["framing"] == NATAL_FRAMING
        assert len(data["facets"]) == 7
        assert data["chart"]["positions"]["Sun"]["sign"] == "Cancer"

    def test_markdown_format_returns_text_with_framing(self, client):
        """format=markdown yields a text/markdown body carrying the framing."""
        resp = client.post("/empirical/natal", json={**CANONICAL, "format": "markdown"})
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/markdown")
        assert NATAL_FRAMING in resp.text

    def test_unknown_field_is_rejected(self, client):
        """extra=forbid: a typo'd key fails loudly instead of being ignored."""
        resp = client.post("/empirical/natal", json={**CANONICAL, "lattitude": 12.0})
        assert resp.status_code == 422

    def test_impossible_calendar_date_is_422_not_500(self, client):
        """Feb 30 is caught by validation, not silently arithmetic'd by swe."""
        resp = client.post("/empirical/natal", json={**CANONICAL, "month": 2, "day": 30})
        assert resp.status_code == 422

    def test_polar_birth_succeeds_with_missing_reason(self, client):
        """A polar Placidus birth is a 200 whose payload discloses the miss."""
        resp = client.post(
            "/empirical/natal",
            json={**CANONICAL, "latitude": 78.0, "longitude": 15.6, "tz_offset": 1.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart"]["houses"] is None
        assert data["chart"]["houses_missing_reason"] == "polar_latitude"
        assert all(f["degraded"] for f in data["facets"])

    def test_unknown_time_births_are_supported(self, client):
        """time_known=false decodes without houses, reason disclosed."""
        resp = client.post("/empirical/natal", json={**CANONICAL, "time_known": False})
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart"]["houses_missing_reason"] == "birth_time_unknown"

    def test_house_system_choice_is_honoured(self, client):
        """An explicit whole_sign request works even at polar latitude."""
        resp = client.post(
            "/empirical/natal",
            json={**CANONICAL, "latitude": 78.0, "house_system": "whole_sign"},
        )
        assert resp.status_code == 200
        assert resp.json()["chart"]["houses"]["system"] == "whole_sign"


class TestPage:
    """The human-facing form page."""

    def test_page_serves_html(self, client):
        """GET /empirical/natal/page returns the form."""
        resp = client.get("/empirical/natal/page")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")
        assert "Natal decode" in resp.text

    def test_page_never_uses_innerhtml(self, client):
        """Repo safe-DOM rule: responses land via textContent only."""
        html = client.get("/empirical/natal/page").text
        assert "innerHTML" not in html
        assert "textContent" in html
