"""HTTP + unit tests for the multi-day Mundane Forecast / Almanac.

Covers the two route modules wired into ``app.main`` (``forecast_router`` and
``almanac_router``) plus the pure ``range_forecast`` scanner they delegate to.
The ephemeris is real (Lahiri sidereal via swisseph) — a 14-day scan is well
under a second, and we want to verify actual event detection, not a mock.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.medini.mundane import current_jd_ut, range_forecast

_EVENT_TYPES = {"INGRESS", "STATION", "CONJUNCTION"}


# --------------------------- range_forecast unit --------------------------- #

def test_range_forecast_forward_shape_and_direction() -> None:
    """A forward scan returns the documented envelope, all events UPCOMING."""
    start = current_jd_ut()
    out = range_forecast(start, start + 30, direction="UPCOMING")

    assert out["direction"] == "UPCOMING"
    assert out["jd_start"] == start
    assert out["jd_end"] == start + 30
    assert out["span_days"] == pytest.approx(30.0)
    assert set(out["summary"]) == {
        "event_count", "ingress_count", "station_count", "conjunction_count",
    }
    assert out["summary"]["event_count"] == len(out["events"])
    for e in out["events"]:
        assert e["type"] in _EVENT_TYPES
        assert e["direction"] == "UPCOMING"
        assert "timestamp_utc" in e and "kurma" in e
        assert start <= e["jd"] <= start + 30


def test_range_forecast_events_sorted_by_jd() -> None:
    start = current_jd_ut()
    events = range_forecast(start, start + 45, direction="UPCOMING")["events"]
    jds = [e["jd"] for e in events]
    assert jds == sorted(jds)


def test_range_forecast_summary_counts_match_event_types() -> None:
    start = current_jd_ut()
    out = range_forecast(start, start + 60, direction="UPCOMING")
    s = out["summary"]
    assert s["ingress_count"] == sum(1 for e in out["events"] if e["type"] == "INGRESS")
    assert s["station_count"] == sum(1 for e in out["events"] if e["type"] == "STATION")
    assert s["conjunction_count"] == sum(1 for e in out["events"] if e["type"] == "CONJUNCTION")
    assert s["event_count"] == s["ingress_count"] + s["station_count"] + s["conjunction_count"]


def test_range_forecast_no_sun_or_moon_stations() -> None:
    """Sun/Moon never station — they must not appear as STATION events."""
    start = current_jd_ut()
    out = range_forecast(start, start + 60, direction="UPCOMING")
    stations = [e for e in out["events"] if e["type"] == "STATION"]
    assert all(e["planet"] not in ("Sun", "Moon") for e in stations)


def test_range_forecast_rejects_empty_or_inverted_window() -> None:
    start = current_jd_ut()
    with pytest.raises(ValueError):
        range_forecast(start, start, direction="UPCOMING")
    with pytest.raises(ValueError):
        range_forecast(start, start - 5, direction="UPCOMING")


def test_range_forecast_rejects_nonpositive_step() -> None:
    start = current_jd_ut()
    with pytest.raises(ValueError):
        range_forecast(start, start + 5, direction="UPCOMING", step_days=0)


def test_range_forecast_ingress_refinement_lands_on_boundary() -> None:
    """A detected ingress must be refined to a moment whose position sits at a
    sign boundary (within a small tolerance), confirming the bisection works."""
    from app.medini.mundane import planet_at_jd

    start = current_jd_ut()
    out = range_forecast(start, start + 90, direction="UPCOMING")
    ingresses = [e for e in out["events"] if e["type"] == "INGRESS"]
    if not ingresses:
        pytest.skip("no ingress in the next 90 days for this run")
    e = ingresses[0]
    deg = planet_at_jd(e["jd"], e["planet"])["degree_in_sign"]
    # Refined to the crossing: degrees-in-sign should be very close to 0 or 30.
    assert min(deg, 30.0 - deg) < 0.05


# ------------------------------- HTTP routes ------------------------------- #

@pytest.mark.asyncio
async def test_forecast_endpoint_defaults(client: AsyncClient) -> None:
    resp = await client.get("/medini/forecast")
    assert resp.status_code == 200
    body = resp.json()
    assert body["direction"] == "UPCOMING"
    assert body["span_days"] == pytest.approx(14.0)  # _DEFAULT_DAYS
    assert "events" in body and "activated_regions" in body


@pytest.mark.asyncio
async def test_almanac_endpoint_is_backward(client: AsyncClient) -> None:
    resp = await client.get("/medini/almanac", params={"days": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["direction"] == "PAST"
    assert body["span_days"] == pytest.approx(10.0)
    assert body["jd_end"] > body["jd_start"]
    for e in body["events"]:
        assert e["direction"] == "PAST"


@pytest.mark.asyncio
async def test_forecast_respects_jd_and_days(client: AsyncClient) -> None:
    jd = current_jd_ut()
    resp = await client.get("/medini/forecast", params={"jd": jd, "days": 7})
    assert resp.status_code == 200
    body = resp.json()
    assert body["jd_start"] == pytest.approx(jd)
    assert body["jd_end"] == pytest.approx(jd + 7)


@pytest.mark.asyncio
@pytest.mark.parametrize("days", [0, 91, -1])
async def test_forecast_days_out_of_bounds_rejected(client: AsyncClient, days: int) -> None:
    resp = await client.get("/medini/forecast", params={"days": days})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_forecast_conjunction_orb_bounds(client: AsyncClient) -> None:
    assert (await client.get("/medini/forecast", params={"conjunction_orb": 0})).status_code == 422
    assert (await client.get("/medini/forecast", params={"conjunction_orb": 99})).status_code == 422
    ok = await client.get("/medini/forecast", params={"conjunction_orb": 5, "days": 5})
    assert ok.status_code == 200


# ------------------------------- page routes ------------------------------- #

@pytest.mark.asyncio
async def test_forecast_page_returns_html(client: AsyncClient) -> None:
    resp = await client.get("/medini/forecast/page")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "/medini/forecast" in resp.text  # the page fetches its own endpoint


@pytest.mark.asyncio
async def test_almanac_page_returns_html_and_targets_almanac(client: AsyncClient) -> None:
    resp = await client.get("/medini/almanac/page")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    # The almanac page must point its client-side fetch at the almanac endpoint.
    assert 'data-endpoint="/medini/almanac"' in resp.text
