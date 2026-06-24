"""Tests for the unified-tabs frontend shell.

The shell sits at GET / and replaces the old `{"message": "Welcome..."}`
JSON greeter with an HTML page that frames every surface (Nadi calculator,
NumeroAstro portal, Kurma grid, Cosmic Weather, Eclipses, API docs) in a
single tab navigator. The Nadi calculator at GET /chart/page is the only
brand-new surface — every other tab target already existed.

These tests pin three things:
  1. GET /  is HTML and references every surface URL the shell promises.
  2. GET /chart/page is HTML and exposes form fields matching BirthDataInput.
  3. POST /chart/calculate still works (the shell's Nadi tab depends on it).
"""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_root_returns_html_not_json(client) -> None:
    """The root used to return a JSON welcome dict; the unified shell
    replaces it with HTML. Old callers that parsed JSON here will need
    to update — pin the contract change."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_root_shell_references_all_surface_urls(client) -> None:
    """The shell's tab nav must wire up every tab to a working URL.
    If a new tab is added without updating the shell, this test catches it."""
    response = await client.get("/")
    body = response.text
    # All tab targets the shell promises:
    for url in (
        "/chart/page",            # Nadi calculator
        "/portal/",               # NumeroAstro
        "/medini/kurma-widget",   # Kurma grid
        "/medini/cartography/page",  # Astrocartography
        "/medini/today/page",     # Cosmic Weather
        "/medini/forecast/page",  # Phase 2: Mundane Forecast
        "/medini/almanac/page",   # Phase 2: Mundane Almanac
        "/medini/eclipses/page",  # Eclipses
        "/medini/knowledge/page", # RAG search
        "/medini/reading/page",   # Round 10: per-chart RAG reading
        "/interpret/page",        # LLM narrative
        "/docs",                  # FastAPI swagger
    ):
        assert url in body, f"Shell missing surface URL: {url}"


@pytest.mark.asyncio
async def test_shell_tabs_for_new_phase2_surfaces(client) -> None:
    """Forecast + Almanac + Knowledge each get their own clickable tab in
    the nav AND their own surface card on the welcome screen. The data-tab
    attribute is what the JS dispatcher dispatches on; pin both spellings."""
    response = await client.get("/")
    body = response.text
    for tab in ("forecast", "almanac", "knowledge", "reading"):
        assert f'data-tab="{tab}"' in body, (
            f"Shell missing data-tab={tab} (tab nav or welcome card)"
        )
        assert f'#{tab}' in body, (
            f"Shell missing hash route for #{tab}"
        )


@pytest.mark.asyncio
async def test_root_shell_has_tab_navigation(client) -> None:
    """Sanity: the shell must have a recognisable nav element."""
    response = await client.get("/")
    body = response.text
    assert '<nav class="tabs"' in body
    assert "Vedic &amp; Nadi Astrology Engine" in body or "Vedic & Nadi Astrology Engine" in body


# ---------- /chart/page (Nadi calculator) ----------

@pytest.mark.asyncio
async def test_chart_page_returns_html(client) -> None:
    response = await client.get("/chart/page")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_chart_page_has_birth_data_form_fields(client) -> None:
    """The form's input ids must exactly match BirthDataInput field names
    so the JS payload-builder doesn't silently drift from the schema."""
    response = await client.get("/chart/page")
    body = response.text
    for field_id in (
        'id="year"',
        'id="month"',
        'id="day"',
        'id="hour"',
        'id="minute"',
        'id="latitude"',
        'id="longitude"',
        'id="tz_offset"',
    ):
        assert field_id in body, f"Nadi form missing field: {field_id}"


@pytest.mark.asyncio
async def test_chart_page_posts_to_calculate_endpoint(client) -> None:
    """The form must POST to /chart/calculate — the existing JSON endpoint."""
    response = await client.get("/chart/page")
    assert "/chart/calculate" in response.text


@pytest.mark.asyncio
async def test_chart_calculate_still_works_for_shell(client) -> None:
    """Regression guard: the unified shell depends on POST /chart/calculate
    continuing to accept the same BirthDataInput payload and return JSON.
    If anyone refactors this endpoint, the shell breaks silently — this
    test fails first."""
    response = await client.post(
        "/chart/calculate",
        json={
            "year": 1990, "month": 7, "day": 15,
            "hour": 12, "minute": 0,
            "latitude": 12.9716, "longitude": 77.5946,
            "tz_offset": 5.5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "d1" in body
    assert "ascendant" in body
    assert "current_mahadasha" in body
