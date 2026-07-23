"""Soul-destiny API + CLI surface — `app/api/soul_routes.py` + `tools/raman_saab/soul_reading.py`.

The router is mounted on an ISOLATED FastAPI app (not app.main) so no daemon/lifespan starts. Uses
the public canonical baseline — never private birth data. Confirms the reading serialises to JSON,
the group nets nothing, and the CLI birth-parser handles both the flat and date/time-string shapes.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.soul_routes import soul_router
from tools.raman_saab.soul_reading import _birth

_BASELINE = {"year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
             "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5}


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(soul_router)
    return TestClient(app)


class TestSoulApi:
    def test_about_declares_report_only_and_experiment(self) -> None:
        """GET /soul/about surfaces the report-only stance + the EXPERIMENT firewall caveat."""
        body = _client().get("/soul/about").json()
        assert body["report_only"] is True
        assert "experiment" in body and "main" in body["experiment"]

    def test_post_soul_serialises_the_reading(self) -> None:
        """POST /soul on the public baseline returns the full reading as JSON."""
        r = _client().post("/soul", json=_BASELINE)
        assert r.status_code == 200
        body = r.json()
        assert {"core", "jaimini_overlay", "nakshatra_signature", "narrative", "notes"} <= set(body)
        assert 1 <= body["jaimini_overlay"]["karakamsa_sign"] <= 12

    def test_post_group_nets_nothing(self) -> None:
        """POST /soul/group returns the interlock synthesis with NO combined verdict."""
        members = [{**_BASELINE, "role": "a"}, {**_BASELINE, "day": 16, "role": "b"}]
        r = _client().post("/soul/group", json={"members": members})
        assert r.status_code == 200
        body = r.json()
        assert "shared_soul_frames" in body and "narrative" in body
        assert "group_verdict" not in body

    def test_forbids_unknown_fields(self) -> None:
        """extra='forbid' rejects typo'd request keys (422)."""
        r = _client().post("/soul", json={**_BASELINE, "lattitude": 1.0})
        assert r.status_code == 422


class TestSoulCli:
    def test_birth_parser_handles_flat_shape(self) -> None:
        """The CLI parses a flat {year,month,day,...} birth block (fixture shape)."""
        b = _birth({"year": 1989, "month": 10, "day": 12, "hour": 10, "minute": 2,
                    "tz_offset": 5.5, "latitude": 27.23, "longitude": 79.03})
        assert (b.year, b.month, b.day, b.hour, b.minute) == (1989, 10, 12, 10, 2)

    def test_birth_parser_handles_date_time_strings(self) -> None:
        """The CLI parses the {date:'YYYY-MM-DD', time:'HH:MM'} shape (family_charts.json)."""
        b = _birth({"date": "1989-10-10", "time": "15:15", "tz_offset": 5.5,
                    "latitude": 26.45, "longitude": 80.33})
        assert (b.year, b.month, b.day, b.hour, b.minute) == (1989, 10, 10, 15, 15)
