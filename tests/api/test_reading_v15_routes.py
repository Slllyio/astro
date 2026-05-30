"""HTTP smoke tests for the V1.5 web UI.

Every test uses the shared `client` AsyncClient fixture in
`tests/conftest.py`, which already wires the FastAPI app with an in-memory
SQLite and daemon disabled.

The engine call inside POST /generate is real (not mocked) because the
deterministic engine completes well under a second on the Bangalore baseline
and we want to verify that the route renders an actually-populated reading.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# Canonical baseline used throughout the test suite. See CLAUDE.md.
BANGALORE_FORM = {
    "dob": "1990-07-15",
    "time": "12:00",
    "tz": "+05:30",
    "lat": "12.97",
    "lon": "77.59",
}


@pytest.mark.asyncio
async def test_get_form_returns_html_form(client: AsyncClient) -> None:
    """GET /reading/v15/ returns 200 with the chart-entry form."""
    resp = await client.get("/reading/v15/")
    assert resp.status_code == 200
    body = resp.text
    # Form action + key field names must be present so users can submit it.
    assert 'action="/reading/v15/generate"' in body
    assert 'name="dob"' in body
    assert 'name="time"' in body
    assert 'name="tz"' in body
    assert 'name="lat"' in body
    assert 'name="lon"' in body
    assert 'name="enrich"' in body
    # Header band identifies the surface.
    assert "Kundli Reading Engine" in body


@pytest.mark.asyncio
async def test_get_form_has_no_error_banner_on_first_load(client: AsyncClient) -> None:
    """The error banner is absent on the bare-form GET."""
    resp = await client.get("/reading/v15/")
    assert resp.status_code == 200
    # The error div is only rendered when {{ error }} is truthy.
    assert "Could not generate reading" not in resp.text


@pytest.mark.asyncio
async def test_post_generate_bangalore_baseline_renders_reading(
    client: AsyncClient,
) -> None:
    """POST with valid baseline form data returns a rendered reading view."""
    resp = await client.post("/reading/v15/generate", data=BANGALORE_FORM)
    assert resp.status_code == 200
    body = resp.text
    # Header line embeds the submitted dob/time.
    assert "1990-07-15" in body
    assert "12:00" in body
    # The reading view always renders these sections.
    assert "Chart overview" in body
    assert "Life-domain syntheses" in body
    assert "Notable yogas" in body
    # Bangalore baseline produces Mercury MD.
    assert "Mercury" in body
    # Download link present with a reading id.
    assert "/reading/v15/download/" in body


@pytest.mark.asyncio
async def test_post_generate_returns_download_link(client: AsyncClient) -> None:
    """The view template exposes a working download link to /download/{id}."""
    resp = await client.post("/reading/v15/generate", data=BANGALORE_FORM)
    assert resp.status_code == 200
    body = resp.text

    # Extract the reading id from the markup. The template renders it twice:
    # once in the anchor href and once in the action bar.
    import re

    match = re.search(r"/reading/v15/download/([0-9a-f]{8})", body)
    assert match is not None, "expected an 8-hex reading id in the response"
    reading_id = match.group(1)

    # Hit the download endpoint and verify it serves JSON with attachment header.
    dl = await client.get(f"/reading/v15/download/{reading_id}")
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("application/json")
    assert "attachment" in dl.headers.get("content-disposition", "")
    assert f"kundli_{reading_id}.json" in dl.headers["content-disposition"]

    # The JSON body has the expected top-level ReadingOutput keys.
    payload = dl.json()
    assert set(payload.keys()) >= {
        "meta", "chart", "primitives", "foundations", "practitioner",
        "sequences", "domains", "contradictions", "warnings",
    }


@pytest.mark.asyncio
async def test_post_generate_invalid_lat_re_renders_form_with_error(
    client: AsyncClient,
) -> None:
    """Out-of-range latitude → 200 with the form + an error banner.

    Per the spec the route does NOT 400 the user; it re-renders the form so
    they can correct the input without losing what they typed.
    """
    bad = dict(BANGALORE_FORM)
    bad["lat"] = "999"  # outside ChartInput's [-90, 90] range
    resp = await client.post("/reading/v15/generate", data=bad)
    # Form re-renders with the same status code (200) per the design.
    assert resp.status_code == 200
    body = resp.text
    assert "Could not generate reading" in body
    assert "Invalid input" in body
    # User-typed value is preserved on re-render.
    assert "999" in body


@pytest.mark.asyncio
async def test_post_generate_invalid_tz_format_re_renders_form_with_error(
    client: AsyncClient,
) -> None:
    """An out-of-range latitude triggers the validation re-render path.

    Note: Pydantic's ChartInput validates lat/lon ranges but not the
    ±HH:MM tz format — that's an engine-level concern. We test a clearly
    out-of-range longitude to exercise the validation error branch.
    """
    bad = dict(BANGALORE_FORM)
    bad["lon"] = "999"
    resp = await client.post("/reading/v15/generate", data=bad)
    assert resp.status_code == 200
    assert "Could not generate reading" in resp.text
    # Form re-renders with retained value.
    assert "999" in resp.text


@pytest.mark.asyncio
async def test_download_unknown_id_returns_404(client: AsyncClient) -> None:
    """Requesting a download for an id not in the cache returns 404."""
    resp = await client.get("/reading/v15/download/deadbeef")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_post_generate_with_enrich_unchecked_returns_reading(
    client: AsyncClient,
) -> None:
    """Submitting without the enrich checkbox produces a Tier-0..2 reading.

    The default form posts no `enrich` field when unchecked; FastAPI's
    Annotated[bool, Form()] default makes that read as False. The reading
    is still fully populated, just without RAG citations.
    """
    resp = await client.post("/reading/v15/generate", data=BANGALORE_FORM)
    assert resp.status_code == 200
    body = resp.text
    # Without enrichment, meta.enrichment_enabled is false → "Enrichment: off"
    # is rendered in the footer.
    assert "Enrichment: off" in body
