"""HTTP serving surface for the Parashara engine — /parashara/reading{,/markdown,/html}.

Pins that engine #2 is reachable over HTTP (it was import-only before), that the app boots with the
router registered, and that each of the three surfaces returns valid content for a birth chart.
"""
from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from app.main import app

_BIRTH = {"year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
          "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_router_is_registered():
    paths = {r.path for r in app.routes if getattr(r, "path", "").startswith("/parashara")}
    assert {"/parashara/reading", "/parashara/reading/markdown",
            "/parashara/reading/html"} <= paths


def test_json_reading(client):
    r = client.post("/parashara/reading", json=_BIRTH)
    assert r.status_code == 200
    d = r.json()
    assert d["chart"]["asc_sign"] == 6                    # canonical Virgo lagna
    assert d["nisargayu_full"]["total_years"] > 0
    assert "arudhas" in d and "shodasavarga" in d


def test_markdown_reading(client):
    r = client.post("/parashara/reading/markdown", json=_BIRTH)
    assert r.status_code == 200
    assert "## Arudha padas" in r.text and "Shodasavarga" in r.text


def test_html_reading(client):
    r = client.post("/parashara/reading/html", json=_BIRTH)
    assert r.status_code == 200
    assert r.text.lstrip().startswith("<!doctype html>") and "<table>" in r.text


def test_bad_birth_data_is_422(client):
    r = client.post("/parashara/reading", json={"year": 1990})   # missing required fields
    assert r.status_code == 422
