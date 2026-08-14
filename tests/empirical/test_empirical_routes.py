"""The read-only API surface.

Mounted standalone rather than through ``app.main``: these routes have no
dependency on the rest of the application, and testing them in isolation keeps
the suite from failing for reasons that have nothing to do with them.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import empirical_routes
from app.api.empirical_routes import empirical_router


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(empirical_router)
    return TestClient(app)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Point the routes at a temp survivor file."""
    path = tmp_path / "survivors.json"
    monkeypatch.setattr(empirical_routes, "_SURVIVORS_PATH", path)
    return path


class TestEndpoints:
    """All three surfaces answer, in every state."""

    def test_survivors_returns_json(self, client):
        """The JSON surface is always available."""
        assert client.get("/empirical/survivors").status_code == 200

    def test_report_returns_markdown(self, client):
        """The human surface renders the same payload."""
        response = client.get("/empirical/report")
        assert response.status_code == 200
        assert "Empirical engine" in response.text

    def test_health_does_not_imply_a_result(self, client):
        """Health reports what exists, not what was found."""
        body = client.get("/empirical/health").json()
        assert "survivor_set_present" in body
        assert "framing" in body


class TestMissingSurvivorSet:
    """Nothing built here is not the same as nothing found."""

    def test_absent_file_is_not_a_measured_null(self, client, isolated):
        """An unbuilt deployment must not claim to have measured a null."""
        body = client.get("/empirical/survivors").json()
        assert body["stage"] == "unbuilt"
        assert body["n_claims"] == 0

    def test_absent_file_does_not_500(self, client, isolated):
        """A missing artifact is an expected state, not a server error."""
        assert client.get("/empirical/survivors").status_code == 200


class TestMalformedSurvivorSet:
    """A claim that never earned its place must not reach a reader."""

    def test_invalid_claim_is_refused_with_500(self, client, isolated):
        """Serving a negative-delta claim would be worse than serving nothing."""
        isolated.write_text(json.dumps({
            "claims": [{
                "test_id": "BAD", "feature_bank": "western", "target": "x",
                "delta": -0.5, "ci_low": -1.0, "ci_high": 0.0, "p_value": 0.001,
                "n": 100, "base_rate": 0.2, "coverage": 0.5,
            }],
            "stage": "confirmatory",
        }))
        response = client.get("/empirical/survivors")
        assert response.status_code == 500
        assert "validation" in response.json()["detail"]


class TestDisclosure:
    """Every response carries its framing."""

    def test_framing_present_on_json(self, client):
        """Population association, not individual prediction."""
        assert "not a prediction about you" in client.get("/empirical/survivors").json()["framing"]

    def test_framing_present_on_markdown(self, client):
        """Same disclosure on the human surface."""
        assert "not a prediction about you" in client.get("/empirical/report").text
