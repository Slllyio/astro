"""HTTP-level tests for the Geo-Astrological Engine endpoints (/medini/*).

These exercise the FastAPI router on top of the kurma_chakra module — pure
unit tests for the geographic logic itself live in test_kurma_chakra.py.
"""
from __future__ import annotations

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/medini/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["kurma_regions_loaded"] == 9
    assert body["nakshatra_count"] == 27


async def test_regions_returns_geojson_and_metadata(client: AsyncClient) -> None:
    response = await client.get("/medini/regions")
    assert response.status_code == 200
    body = response.json()

    # GeoJSON layer for the map.
    fc = body["geojson"]
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 9
    for feat in fc["features"]:
        assert feat["geometry"]["type"] == "Polygon"
        assert "region" in feat["properties"]
        assert "tattva" in feat["properties"]

    # Per-nakshatra detail table for the educational widget.
    assert len(body["nakshatra_table"]) == 27
    krittika = next(n for n in body["nakshatra_table"] if n["name"] == "Krittika")
    assert krittika["region"] == "Central"
    assert krittika["tattva"] == "Earth/Fire"

    # Region summaries for the legend.
    assert len(body["regions_summary"]) == 9
    central = next(r for r in body["regions_summary"] if r["region"] == "Central")
    assert "Sun" in central["region_planets"]


async def test_region_for_known_city(client: AsyncClient) -> None:
    response = await client.get(
        "/medini/region-for", params={"latitude": 12.97, "longitude": 77.59}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["region"] == "Central"
    assert body["tattva"] == "Earth/Fire"
    assert "Sun" in body["region_planets"]
    assert "Krittika" in body["nakshatras"]


async def test_region_for_invalid_lat_returns_400(client: AsyncClient) -> None:
    response = await client.get(
        "/medini/region-for", params={"latitude": 100.0, "longitude": 0.0}
    )
    assert response.status_code == 400


async def test_region_for_missing_params_returns_422(client: AsyncClient) -> None:
    """FastAPI's query-validation kicks in before the handler — missing
    required params return 422 (Pydantic validation), not 400."""
    response = await client.get("/medini/region-for")
    assert response.status_code == 422


async def test_kurma_widget_returns_html(client: AsyncClient) -> None:
    response = await client.get("/medini/kurma-widget")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    # Sanity-check the page is the expected widget — contains the title,
    # the data-fetch URL, and the Leaflet integration.
    assert "Kurma Chakra Grid" in body
    assert "/medini/regions" in body
    assert "leaflet" in body.lower()


async def test_kurma_widget_uses_safe_dom_construction(client: AsyncClient) -> None:
    """Defensive: the widget should build dynamic content via DOM helpers
    (createElement + textContent), not raw HTML strings. This is enforced
    at write-time by the project's security hook; this test pins the
    invariant at runtime as a regression guard."""
    response = await client.get("/medini/kurma-widget")
    body = response.text
    # The widget MUST contain createElement + textContent (the safe pattern).
    assert "createElement" in body, "expected createElement-based DOM construction"
    assert "textContent" in body, "expected textContent for plain-text insertion"
