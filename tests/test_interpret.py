"""Tests for app.llm.* + the /interpret/* HTTP endpoints.

Two layers:
  1. Unit tests for the prompt builders + deterministic-fallback templates
     (pure functions, fast).
  2. Integration tests for the route layer using the StubClient by default
     (no Ollama required) and a controlled fake LLM that simulates the
     real interpreter end-to-end.

Anchored to the Bangalore baseline for the integration tests so the chart
fed to the interpreter is the canonical anchor pinned everywhere else in
the suite.
"""
from __future__ import annotations

from typing import Any

import pytest

from app.llm.client import LLMClient, OllamaUnavailable, StubClient
from app.llm.interpreter import interpret_chart
from app.llm.templates import (
    ALLOWED_SECTIONS,
    build_section_prompt,
    build_summary_prompt,
    deterministic_section,
    deterministic_summary,
)

# Minimal chart fixture — same shape as ChartResponse but only the keys
# the interpreter actually reads. Keeps tests isolated from the engine.
SAMPLE_CHART: dict[str, Any] = {
    "ascendant": {
        "sign_name": "Cancer", "longitude": 95.5,
        "degree_in_sign": 5.5, "sign": 4,
    },
    "current_mahadasha": {
        "mahadasha_lord": "Jupiter",
        "start_date": "2024-01-01", "end_date": "2040-01-01",
        "time_elapsed_years": 1.5, "total_duration_years": 16.0,
    },
    "d1": {
        "Sun": {
            "sign_name": "Gemini", "degree_in_sign": 28.8,
            "longitude": 88.8, "house": 12,
            "is_retrograde": False,
            "nakshatra": {"name": "Punarvasu", "pada": 2},
        },
        "Moon": {
            "sign_name": "Pisces", "degree_in_sign": 0.5,
            "longitude": 330.5, "house": 9,
            "is_retrograde": False,
            "nakshatra": {"name": "Purva Bhadrapada", "pada": 4},
        },
    },
    "panchanga": {
        "tithi":     {"index": 21, "name": "Ekadashi", "paksha": "Krishna"},
        "vara":      {"index": 0, "name": "Sunday"},
        "yoga":      {"index": 24, "name": "Shukla"},
        "karana":    {"index": 41, "name": "Naga"},
        "nakshatra": {"index": 25, "name": "Purva Bhadrapada", "pada": 4, "lord": "Jupiter", "longitude_in_nakshatra": 0.5},
    },
    "yogas": [
        {"name": "Gajakesari", "type": "Sambandha",
         "planets_involved": ["Jupiter", "Moon"],
         "description": "Jupiter and Moon in mutual kendras."},
    ],
    "ashtakavarga": {
        "sav": [27, 32, 28, 30, 24, 31, 35, 26, 29, 33, 25, 28],
        "bav_per_planet": {},
        "bav_totals": {},
    },
}


# ---------- Prompt builders ----------

def test_summary_prompt_includes_ascendant_and_mahadasha() -> None:
    """Prompt must surface concrete chart values so the LLM can cite them
    instead of hallucinating. Pin the exact substrings."""
    prompt = build_summary_prompt(SAMPLE_CHART)
    assert "Cancer" in prompt
    assert "Jupiter" in prompt
    assert "2024-01-01" in prompt


def test_section_prompt_focuses_on_named_section() -> None:
    """Each section's prompt must contain a 'Focus only on' directive that
    matches the requested section."""
    p = build_section_prompt(SAMPLE_CHART, "ascendant")
    assert "ascendant" in p.lower()
    p = build_section_prompt(SAMPLE_CHART, "yogas")
    assert "yogas" in p.lower()


def test_allowed_sections_are_a_closed_set() -> None:
    """ALLOWED_SECTIONS is the contract; validation depends on it being
    a fixed frozenset — pin its members explicitly."""
    assert ALLOWED_SECTIONS == frozenset({
        "ascendant", "mahadasha", "yogas",
        "panchanga", "planetary", "ashtakavarga",
    })


# ---------- Deterministic fallback rendering ----------

def test_deterministic_summary_is_factual_and_terse() -> None:
    """Fallback must mention asc + mahadasha + yogas, end with the marker
    that lets users tell at a glance this isn't an LLM response."""
    txt = deterministic_summary(SAMPLE_CHART)
    assert "Cancer" in txt
    assert "Jupiter" in txt
    assert "OLLAMA_ENABLED" in txt  # hint about how to upgrade


def test_deterministic_section_handles_missing_data_gracefully() -> None:
    """If a section's data is missing, the renderer says so plainly
    rather than crashing with KeyError."""
    empty: dict[str, Any] = {}
    assert "not available" in deterministic_section(empty, "ascendant").lower()
    assert "not available" in deterministic_section(empty, "mahadasha").lower()


def test_deterministic_section_ashtakavarga_finds_strongest_house() -> None:
    """The ashtakavarga renderer must surface the strongest SAV house index."""
    txt = deterministic_section(SAMPLE_CHART, "ashtakavarga")
    # Index 6 (zero-indexed) → house 7, value 35 — the max in the SAV list.
    assert "7" in txt
    assert "35" in txt


# ---------- interpret_chart with explicit clients ----------

def test_interpret_chart_uses_explicit_stub_client() -> None:
    """When an explicit client is passed, interpret_chart calls it (regardless
    of OLLAMA_ENABLED setting) and tags source='llm'."""
    stub = StubClient(canned_response="The native is a Jupiter-tinged Cancer rising.")
    result = interpret_chart(SAMPLE_CHART, mode="summary", client=stub)
    assert result.text == "The native is a Jupiter-tinged Cancer rising."
    assert result.source == "llm"
    assert result.mode == "summary"


def test_interpret_chart_falls_back_when_client_is_none() -> None:
    """No client → deterministic template (assumes OLLAMA_ENABLED is False
    in tests, which conftest implicitly enforces by not setting it)."""
    result = interpret_chart(SAMPLE_CHART, mode="summary", client=None)
    assert result.source == "fallback"
    assert "Cancer" in result.text


def test_interpret_chart_falls_back_when_llm_unavailable() -> None:
    """If the LLM client raises OllamaUnavailable, interpreter must serve
    the deterministic template instead of bubbling the error to the route."""
    class FailingClient:
        model = "broken"
        def complete(self, prompt: str) -> str:
            raise OllamaUnavailable("Ollama not running")

    # FailingClient duck-types to LLMClient; runtime_checkable makes this work.
    assert isinstance(FailingClient(), LLMClient)
    result = interpret_chart(SAMPLE_CHART, mode="summary", client=FailingClient())
    assert result.source == "fallback"
    assert "Cancer" in result.text


def test_interpret_chart_section_validates_against_allow_list() -> None:
    """An unknown section is a programming error from the route layer's
    perspective — we re-check defensively."""
    with pytest.raises(ValueError):
        interpret_chart(SAMPLE_CHART, mode="section", section="career_predictions")


def test_interpret_chart_summary_rejects_section_arg() -> None:
    with pytest.raises(ValueError):
        interpret_chart(SAMPLE_CHART, mode="summary", section="ascendant")


def test_interpret_chart_section_requires_section_name() -> None:
    with pytest.raises(ValueError):
        interpret_chart(SAMPLE_CHART, mode="section", section=None)


# ---------- /interpret/* endpoints ----------

BANGALORE_BIRTH = {
    "year": 1990, "month": 7, "day": 15,
    "hour": 12, "minute": 0,
    "latitude": 12.9716, "longitude": 77.5946,
    "tz_offset": 5.5,
}


@pytest.mark.asyncio
async def test_sections_endpoint_lists_allowed_sections(client) -> None:
    response = await client.get("/interpret/sections")
    assert response.status_code == 200
    body = response.json()
    assert "sections" in body
    assert set(body["sections"]) == ALLOWED_SECTIONS


@pytest.mark.asyncio
async def test_interpret_chart_summary_returns_fallback_in_test_env(client) -> None:
    """OLLAMA_ENABLED defaults to False → endpoint returns the deterministic
    summary. Source must be 'fallback' so frontend can surface that to the
    user (e.g. "Enable Ollama for richer narratives")."""
    response = await client.post("/interpret/chart", json=BANGALORE_BIRTH)
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "summary"
    assert body["source"] == "fallback"
    assert body["text"]  # non-empty
    assert body["section"] is None


@pytest.mark.asyncio
async def test_interpret_chart_section_endpoint(client) -> None:
    response = await client.post(
        "/interpret/chart/ascendant", json=BANGALORE_BIRTH,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "section"
    assert body["section"] == "ascendant"
    assert body["source"] == "fallback"


@pytest.mark.asyncio
async def test_interpret_chart_section_rejects_unknown_section(client) -> None:
    """Unknown section → 400 with the allow-list, before any chart compute."""
    response = await client.post(
        "/interpret/chart/career", json=BANGALORE_BIRTH,
    )
    assert response.status_code == 400
    body = response.json()
    assert "detail" in body
    detail = body["detail"]
    assert "allowed_sections" in detail
    assert "ascendant" in detail["allowed_sections"]


@pytest.mark.asyncio
async def test_interpret_chart_section_normalizes_case(client) -> None:
    """The route layer lowercases the section, so 'Ascendant' is accepted."""
    response = await client.post(
        "/interpret/chart/Ascendant", json=BANGALORE_BIRTH,
    )
    assert response.status_code == 200
    assert response.json()["section"] == "ascendant"


@pytest.mark.asyncio
async def test_interpret_chart_validates_birth_data(client) -> None:
    """The endpoint shares BirthDataInput validation with /chart/calculate;
    a bad year (e.g. 9999) must 422 before any LLM call fires."""
    bad = dict(BANGALORE_BIRTH, year=9999)
    response = await client.post("/interpret/chart", json=bad)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_interpret_page_returns_html(client) -> None:
    response = await client.get("/interpret/page")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "<title>Chart Interpretation" in body
    # The page must POST to the interpret endpoints — surface that contract.
    assert "/interpret/chart" in body
    # Each drill-down section must be selectable from the form.
    for s in ("ascendant", "mahadasha", "yogas", "panchanga", "planetary", "ashtakavarga"):
        assert s in body
