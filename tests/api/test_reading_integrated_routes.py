"""HTTP integration tests for /reading/integrated/* routes.

Uses ``FastAPI(router=...) + TestClient`` directly rather than importing
``app.main.app`` because main.py imports two modules
(forecast_routes, knowledge_routes) that don't exist on this branch.
That's a pre-existing main.py issue independent of our routes — the
routes themselves are correct and runnable on a minimal app.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.api.reading_integrated_routes import router

# Minimal FastAPI app wrapping ONLY our integrated router for testing.
# This sidesteps app/main.py's broken imports.
test_app = FastAPI()
test_app.include_router(router)
client = TestClient(test_app)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

def _finding_dict(*, id: str, rule: str, classification: str = "yoga",
                  direction: str = "positive", verdict: str = "test") -> dict:
    return {
        "id": id, "rule": rule, "source_sequence": None,
        "classification": classification, "direction": direction,
        "verdict": verdict, "verdict_language": "en", "evidence": [],
        "confidence": {"score": 0.7, "votes": {}, "band": "medium"},
        "enrichment_level": 0, "citations": [], "consensus": None,
        "consensus_status": "not_computed", "dispute": None,
        "robustness": None, "contradicts_finding_ids": [],
    }


def _minimal_reading(findings: list[dict]) -> dict:
    return {
        "meta": {"schema_version": "1.2.0"},
        "chart": {"latitude": 12.97, "longitude": 77.59, "dob": "1990-07-15"},
        "primitives": {}, "foundations": {}, "practitioner": {},
        "sequences": {"vimshottari": {"current_md_lord": "Mercury"}},
        "domains": {
            "career": {
                "domain": "career",
                "promise": _finding_dict(
                    id="d.career.promise", rule="promise.career", verdict="promise",
                ),
                "triggers": [], "timing_windows": [],
                "afflictions": [], "cross_checks": [],
                "remedies": [],
                "overall_verdict": _finding_dict(
                    id="d.career.overall", rule="overall.career", verdict="overall",
                ),
                "confidence": {
                    "score": 0.7,
                    "votes": {"house": True, "lord": True, "karaka": True},
                    "band": "high",
                },
            }
        },
        "contradictions": [], "warnings": [],
    }


def _minimal_reading_with_findings(findings_inline: list[dict]) -> dict:
    """Add findings into a domain's cross_checks for enhancer coverage."""
    reading = _minimal_reading([])
    reading["domains"]["career"]["cross_checks"] = findings_inline
    return reading


# ---------------------------------------------------------------------------
# GET /info
# ---------------------------------------------------------------------------

class TestInfoRoute:
    """GET /reading/integrated/info returns metadata."""

    def test_info_returns_200(self):
        resp = client.get("/reading/integrated/info")
        assert resp.status_code == 200

    def test_info_returns_integration_version(self):
        data = client.get("/reading/integrated/info").json()
        assert "integration_version" in data
        assert data["integration_version"] == "0.5.0"

    def test_info_includes_adapter_names(self):
        data = client.get("/reading/integrated/info").json()
        adapters = set(data["adapters"])
        assert {"enhance", "modulate_all_domains",
                "compare_chara_dasha", "compare_functional_roles"}.issubset(adapters)

    def test_info_includes_dkp_registry_size(self):
        data = client.get("/reading/integrated/info").json()
        # 27 records as of 2026-05-29 doctrine registry
        assert data["dkp_translation_registry_size"] == 27


# ---------------------------------------------------------------------------
# POST /enhance
# ---------------------------------------------------------------------------

class TestEnhanceRoute:
    """POST /reading/integrated/enhance returns IntegratedReadingOutput."""

    def test_enhance_returns_200(self):
        reading = _minimal_reading_with_findings([
            _finding_dict(id="t.1", rule="yogas_extended.lakshmi", verdict="Lakshmi"),
        ])
        resp = client.post("/reading/integrated/enhance", json={"reading": reading})
        assert resp.status_code == 200

    def test_enhance_attaches_translation_for_lakshmi(self):
        reading = _minimal_reading_with_findings([
            _finding_dict(id="t.1", rule="yogas_extended.lakshmi", verdict="Lakshmi"),
        ])
        data = client.post("/reading/integrated/enhance", json={"reading": reading}).json()
        assert "dkp_translations_summary" in data
        assert "Lakshmi" in data["dkp_translations_summary"]["records"]

    def test_enhance_envelope_has_integration_version(self):
        data = client.post(
            "/reading/integrated/enhance",
            json={"reading": _minimal_reading([])},
        ).json()
        assert data["integration_version"] == "0.1.0"  # envelope version

    def test_enhance_with_missing_body_returns_422(self):
        resp = client.post("/reading/integrated/enhance", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /modulate
# ---------------------------------------------------------------------------

class TestModulateRoute:
    """POST /reading/integrated/modulate runs DKP modulation."""

    def test_modulate_returns_200(self):
        resp = client.post(
            "/reading/integrated/modulate",
            json={"reading": _minimal_reading([])},
        )
        assert resp.status_code == 200

    def test_modulate_returns_per_domain(self):
        data = client.post(
            "/reading/integrated/modulate",
            json={"reading": _minimal_reading([])},
        ).json()
        assert "per_domain" in data
        assert len(data["per_domain"]) >= 1  # career was populated
        assert data["per_domain"][0]["bhava"] == 10  # career → 10H

    def test_modulate_respects_overrides(self):
        """Client-supplied overrides feed into DKPContext and affect completeness."""
        data = client.post(
            "/reading/integrated/modulate",
            json={
                "reading": _minimal_reading([]),
                "dkp_context_overrides": {
                    "current_residence_country": "India",
                    "climate_mahabhuta": "vata",
                    "ashrama": "grihastha",
                    "marital_status": "married",
                    "profession": "software_engineer",
                    "prashna": "career_change",
                    "active_mundane_event": "post_pandemic",
                    "age_years": 36.0,
                },
            },
        ).json()
        # Rich context should yield non-zero completeness
        assert data["context_completeness"] >= 8

    def test_modulate_invalid_override_field_returns_400(self):
        resp = client.post(
            "/reading/integrated/modulate",
            json={
                "reading": _minimal_reading([]),
                "dkp_context_overrides": {"not_a_real_field": "value"},
            },
        )
        assert resp.status_code == 400
        assert "Invalid dkp_context_overrides" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /compare-chara
# ---------------------------------------------------------------------------

class TestCompareCharaRoute:
    """POST /reading/integrated/compare-chara runs the Chara comparator."""

    def _build_chara_input(self) -> dict:
        """Run Track A directly to get a valid CharaDashaResult dict."""
        from app.reading.sequences.chara_dasha import run_sequence
        result = run_sequence(
            {"birth_jd": 2448088.2708333, "d1": {}},
            asc_sign=6, moon_sign=11,
        )
        return result.model_dump(mode="json")

    def test_compare_chara_returns_200(self):
        chara_dict = self._build_chara_input()
        resp = client.post(
            "/reading/integrated/compare-chara",
            json={
                "track_a_chara_dasha": chara_dict,
                "lagna_sign": 6,
                "birth_jd": 2448088.2708333,
            },
        )
        assert resp.status_code == 200

    def test_compare_chara_reports_known_divergence(self):
        """For Virgo, both engines emit 12 MDs but signs+boundaries differ."""
        chara_dict = self._build_chara_input()
        data = client.post(
            "/reading/integrated/compare-chara",
            json={
                "track_a_chara_dasha": chara_dict,
                "lagna_sign": 6,
                "birth_jd": 2448088.2708333,
            },
        ).json()
        assert data["count_agrees"] is True
        # The Track-B bug: signs and boundaries diverge
        assert data["all_signs_agree"] is False
        assert data["all_boundaries_agree"] is False

    def test_compare_chara_invalid_chara_shape_returns_400(self):
        resp = client.post(
            "/reading/integrated/compare-chara",
            json={
                "track_a_chara_dasha": {"not_a_chara": "result"},
                "lagna_sign": 6,
                "birth_jd": 2448088.2708333,
            },
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /compare-functional
# ---------------------------------------------------------------------------

class TestCompareFunctionalRoute:
    """GET /reading/integrated/compare-functional?lagna_sign=N."""

    def test_compare_functional_returns_200(self):
        resp = client.get("/reading/integrated/compare-functional?lagna_sign=6")
        assert resp.status_code == 200

    def test_compare_functional_returns_nine_planets(self):
        data = client.get("/reading/integrated/compare-functional?lagna_sign=6").json()
        assert len(data["per_planet"]) == 9

    def test_compare_functional_flags_rahu_and_ketu_absent_in_b(self):
        data = client.get("/reading/integrated/compare-functional?lagna_sign=6").json()
        assert "Rahu" in data["planets_only_in_a"]
        assert "Ketu" in data["planets_only_in_a"]

    def test_compare_functional_lagna_out_of_range_returns_422(self):
        resp = client.get("/reading/integrated/compare-functional?lagna_sign=13")
        assert resp.status_code == 422

    @pytest.mark.parametrize("lagna_sign", [1, 6, 12])
    def test_compare_functional_runs_for_diverse_lagnas(self, lagna_sign):
        resp = client.get(f"/reading/integrated/compare-functional?lagna_sign={lagna_sign}")
        assert resp.status_code == 200
        assert resp.json()["lagna_sign"] == lagna_sign


# ---------------------------------------------------------------------------
# POST /generate-and-enhance (smoke only — heavier route)
# ---------------------------------------------------------------------------

class TestGenerateAndEnhanceRoute:
    """POST /reading/integrated/generate-and-enhance is a wrapper around
    Track A's compute() + enhance(). We smoke-test with --no-enrich for speed."""

    def test_generate_and_enhance_smoke(self):
        """Full Bangalore baseline run; enrich=False keeps it fast."""
        resp = client.post(
            "/reading/integrated/generate-and-enhance",
            json={
                "dob": "1990-07-15",
                "time": "12:00",
                "tz": "+05:30",
                "lat": 12.97,
                "lon": 77.59,
                "enrich": False,
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # Envelope shape
        assert "reading" in data
        assert "dkp_translations_summary" in data
        # Track A actually emitted something
        assert data["reading"]["meta"]["schema_version"] in ("1.0.0", "1.1.0", "1.2.0")

    def test_generate_and_enhance_invalid_lat_returns_422(self):
        resp = client.post(
            "/reading/integrated/generate-and-enhance",
            json={
                "dob": "1990-07-15", "time": "12:00", "tz": "+05:30",
                "lat": 999.0, "lon": 77.59,
            },
        )
        assert resp.status_code == 422
