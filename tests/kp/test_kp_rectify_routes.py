"""Tests for the /kp-rectify HTTP endpoints (router mounted on a bare app, no database)."""

from __future__ import annotations

import pytest

pytest.importorskip("swisseph")
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.kp_rectify_routes import kp_rectify_router  # noqa: E402

BASE = {"year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0, "tz": 5.5, "lat": 12.97, "lon": 77.59,
        "half_window": 10}


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = FastAPI()
    app.include_router(kp_rectify_router)
    return TestClient(app)


class TestKPRectifyRoutes:
    def test_page_is_served_without_inner_html(self, client):
        """The page loads and builds its DOM safely (no innerHTML anywhere)."""
        r = client.get("/kp-rectify/page")
        assert r.status_code == 200 and "Birth-Time Rectifier" in r.text
        assert "innerHTML" not in r.text

    def test_round_zero_returns_uniform_posterior_and_questions(self, client):
        """With no answers every candidate minute is equally likely and questions are offered."""
        r = client.post("/kp-rectify/round", json=BASE).json()
        ps = [p["p"] for p in r["posterior"]]
        assert len(ps) == 21 and max(ps) - min(ps) < 1e-9
        assert r["ask_everyone"] and r["handoff"] is None

    def test_answers_move_the_posterior(self, client):
        """A yes/no answer and a dated event change the posterior and are reported back."""
        body = {**BASE, "answers": [{"fact": "married", "answer": True},
                                    {"fact": "date_marriage", "answer": [2016, 5, 20]},
                                    {"fact": "date_abroad", "answer": None}]}
        r = client.post("/kp-rectify/round", json=body).json()
        assert len(r["effects"]) == 3 and r["effects"][2]["applies"] is False
        assert abs(sum(p["p"] for p in r["posterior"]) - 1) < 1e-9
        assert r["handoff"] is not None

    @pytest.mark.parametrize("answers", [[{"fact": "married", "answer": "maybe"}],
                                         [{"fact": "no_such_question", "answer": True}],
                                         [{"fact": "speech_style", "answer": "sings"}],
                                         [{"fact": "date_job", "answer": [1980, 1, 1]}]])
    def test_bad_answers_are_rejected(self, client, answers):
        """Malformed answers, unknown questions and dates before birth fail with 422."""
        assert client.post("/kp-rectify/round", json={**BASE, "answers": answers}).status_code == 422

    def test_window_is_bounded(self, client):
        """The candidate window is capped so one request cannot cast unbounded charts."""
        assert client.post("/kp-rectify/round", json={**BASE, "half_window": 500}).status_code == 422
