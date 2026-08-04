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
async def test_shell_links_each_phase2_surface(client) -> None:
    """Forecast, Almanac, Knowledge and Reading each need a way in from the shell.

    Rewritten 2026-08-03: this used to assert `data-tab="…"` + a `#hash` route, which were
    the JS dispatcher's mechanism in the old tab shell. The Pothi-manuscript redesign
    replaced tabs with plain `<a href>` surface cards, so the old assertions pinned a
    mechanism rather than the contract. The contract is what survives: every surface is
    reachable from the home leaf."""
    response = await client.get("/")
    body = response.text
    for surface in ("forecast", "almanac", "knowledge", "reading"):
        assert f'href="/medini/{surface}/page"' in body, (
            f"Shell has no link to the {surface} surface"
        )


@pytest.mark.asyncio
async def test_root_shell_has_navigation(client) -> None:
    """Sanity: the shell must be the manuscript index, with its own navigation.

    The old assertion looked for `<nav class="tabs">` and the 'Vedic & Nadi Astrology
    Engine' banner — both removed by the Pothi redesign in favour of leaf navigation."""
    response = await client.get("/")
    body = response.text
    assert 'class="section-card"' in body, "shell renders no surface cards"
    assert 'manuscript.js' in body, "shell does not load the manuscript navigator"


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


# ---------------------------------------------------------------------------
# Marketing landing page (2026-08-05) — GET /landing
#
# A standalone pitch surface, separate from `/` (the working app shell). It is the
# one page deliberately built on CDN React/Tailwind/GSAP instead of this repo's
# self-contained vanilla convention, which is safe only because it carries no data
# surface. Its COPY, however, is bound by the Measured-Truth directive, and that is
# what these tests actually guard.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_landing_returns_html(client) -> None:
    """GET /landing serves the marketing page as HTML, not JSON."""
    response = await client.get("/landing")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_landing_states_both_fidelity_and_the_null_result(client) -> None:
    """Measured Truth, enforced on the marketing surface.

    The project's binding directive is that the two accuracy axes are reported side by
    side and never averaged or cherry-picked. A landing page that quoted 88.4% fidelity
    while quietly dropping the null real-outcome finding would be exactly the overclaim
    the directive exists to prevent — so both must be present."""
    body = (await client.get("/landing")).text
    assert "88.4%" in body, "the measured fidelity figure must appear"
    assert "NULL" in body, "the null real-outcome result must appear alongside it"
    assert "22,177" in body, "the tested-chart count must appear"


@pytest.mark.asyncio
async def test_landing_never_claims_to_predict(client) -> None:
    """No decree/prediction language on the pitch, mirroring the report's own guard."""
    body = (await client.get("/landing")).text.lower()
    for banned in ("predict your future", "will happen", "guaranteed", "foretell"):
        assert banned not in body, f"landing page overclaims: {banned!r}"


@pytest.mark.asyncio
async def test_landing_cdn_scripts_carry_integrity_hashes(client) -> None:
    """Every CDN script that CAN carry Subresource Integrity does.

    Tailwind is the sole documented exception: cdn.tailwindcss.com sends no
    Access-Control-Allow-Origin, and SRI requires a CORS fetch, so adding integrity
    there makes the browser block it and the page renders unstyled."""
    body = (await client.get("/landing")).text
    import re
    tags = re.findall(r'<script[^>]*src="(https://[^"]+)"[^>]*>', body)
    external = [t for t in tags if "cdn.tailwindcss.com" not in t]
    assert external, "expected external CDN scripts on the landing page"
    for src in external:
        seg = body[body.index(f'src="{src}"'):][:400]
        assert "integrity=\"sha384-" in seg, f"missing SRI hash for {src}"
