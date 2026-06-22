"""Smoke test: the full FastAPI app boots and the Life-Stage Timing feature is
reachable end-to-end (landing card → predictor page → calibrated JSON).

Guards against the death-timing predictor becoming an orphan route, and against
the app failing to boot when optional routers (forecast/knowledge) are absent on
a given branch.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client() -> TestClient:
    os.environ.setdefault("PORTAL_ENABLED", "false")
    os.environ.setdefault("DAEMON_ENABLED", "false")
    from app.main import app
    return TestClient(app)


def test_app_boots_and_index_links_predictor(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    # the landing page surfaces the death-timing predictor
    assert "/medini/doctrine/death-window/page" in r.text


def test_predictor_page_reachable_through_app(client: TestClient) -> None:
    r = client.get("/medini/doctrine/death-window/page")
    assert r.status_code == 200
    assert "dw-form" in r.text


def test_calibrated_prediction_through_app(client: TestClient) -> None:
    r = client.get("/medini/doctrine/death-window", params={
        "year": 1955, "month": 3, "day": 20,
        "latitude": 19.07, "longitude": 72.88, "tz_offset": 5.5,
        "top_n": 5, "calibrate": "true",
    })
    # 200 with calibration if the catalog is built; 503 if not — both are valid
    # "feature is wired" outcomes (never a 500 from a broken route).
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        body = r.json()
        assert body["calibrated"] is True
        assert body["windows"] and body["windows"][0]["probability"] is not None
        assert body["prob_within_10y"] is not None
