"""Tests for app.medini.eclipses (Eclipse Impact Mapper).

Pinned anchor: 2026-01-01 00:00 UT. Real eclipses around this date are
deterministic outputs of swisseph + the Brihat Samhita Kurma table —
they are externally verifiable against NASA's eclipse catalog.
"""
from __future__ import annotations

import pytest
import swisseph as swe

from app.medini.eclipses import (
    _jd_to_iso_date,
    _lunar_subtype,
    _solar_subtype,
    find_upcoming_eclipses,
    upcoming_eclipses_payload,
)

# Anchor: start of 2026, fully deterministic.
JD_2026_01_01 = swe.julday(2026, 1, 1, 0.0, swe.GREG_CAL)


@pytest.fixture(scope="module", autouse=True)
def _ensure_lahiri_set():
    swe.set_ephe_path(None)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    yield


# ---------- Subtype decoders ----------

def test_solar_subtype_decodes_total() -> None:
    assert _solar_subtype(swe.ECL_TOTAL) == "TOTAL"


def test_solar_subtype_decodes_annular() -> None:
    assert _solar_subtype(swe.ECL_ANNULAR) == "ANNULAR"


def test_solar_subtype_decodes_hybrid() -> None:
    assert _solar_subtype(swe.ECL_ANNULAR_TOTAL) == "HYBRID"


def test_solar_subtype_falls_back_to_partial() -> None:
    """Any retflag with no specific bits set falls back to PARTIAL."""
    assert _solar_subtype(0) == "PARTIAL"


def test_lunar_subtype_decodes_total() -> None:
    assert _lunar_subtype(swe.ECL_TOTAL) == "TOTAL"


def test_lunar_subtype_decodes_partial() -> None:
    assert _lunar_subtype(swe.ECL_PARTIAL) == "PARTIAL"


def test_lunar_subtype_falls_back_to_penumbral() -> None:
    assert _lunar_subtype(0) == "PENUMBRAL"


# ---------- JD → ISO ----------

def test_jd_to_iso_date_format() -> None:
    assert _jd_to_iso_date(JD_2026_01_01) == "2026-01-01"


# ---------- find_upcoming_eclipses ----------

def test_find_upcoming_eclipses_returns_count_per_family() -> None:
    """count=3 means up to 3 solar AND up to 3 lunar = 6 total."""
    eclipses = find_upcoming_eclipses(jd_now=JD_2026_01_01, count=3)
    solar = [e for e in eclipses if e["family"] == "SOLAR"]
    lunar = [e for e in eclipses if e["family"] == "LUNAR"]
    assert len(solar) == 3
    assert len(lunar) == 3
    assert len(eclipses) == 6


def test_find_upcoming_eclipses_sorted_by_date() -> None:
    eclipses = find_upcoming_eclipses(jd_now=JD_2026_01_01, count=5)
    jds = [e["jd"] for e in eclipses]
    assert jds == sorted(jds)


def test_find_upcoming_eclipses_includes_kurma_tagging() -> None:
    eclipses = find_upcoming_eclipses(jd_now=JD_2026_01_01, count=2)
    for e in eclipses:
        astro = e["astrology"]
        assert "luminary" in astro
        assert "nakshatra_name" in astro
        assert "kurma_region" in astro
        assert "kurma_tattva" in astro
        # Solar eclipses use Sun's nakshatra; lunar use Moon's
        assert astro["luminary"] == ("Sun" if e["family"] == "SOLAR" else "Moon")


def test_find_upcoming_eclipses_solar_has_geographic_point() -> None:
    """Solar eclipses must surface lat/lon of greatest eclipse."""
    eclipses = find_upcoming_eclipses(jd_now=JD_2026_01_01, count=2)
    solar = [e for e in eclipses if e["family"] == "SOLAR"]
    assert solar, "expected at least 1 solar eclipse in 2026"
    for e in solar:
        assert e["greatest_lat"] is not None
        assert e["greatest_lon"] is not None
        assert -90.0 <= e["greatest_lat"] <= 90.0
        assert -180.0 <= e["greatest_lon"] <= 180.0


def test_find_upcoming_eclipses_lunar_has_no_geographic_point() -> None:
    """Lunar eclipses are visible from anywhere on the night side; we
    don't compute a single geographic point for them."""
    eclipses = find_upcoming_eclipses(jd_now=JD_2026_01_01, count=2)
    lunar = [e for e in eclipses if e["family"] == "LUNAR"]
    assert lunar, "expected at least 1 lunar eclipse in 2026"
    for e in lunar:
        assert e["greatest_lat"] is None
        assert e["greatest_lon"] is None


def test_find_upcoming_eclipses_pinned_2026_02_solar() -> None:
    """The 2026-02-17 annular solar eclipse is verifiable from NASA's
    eclipse catalog. Pin it as a regression anchor."""
    eclipses = find_upcoming_eclipses(jd_now=JD_2026_01_01, count=1)
    solar = next(e for e in eclipses if e["family"] == "SOLAR")
    assert solar["date"] == "2026-02-17"
    assert solar["subtype"] == "ANNULAR"


def test_find_upcoming_eclipses_pinned_2026_08_total_solar() -> None:
    """The 2026-08-12 total solar eclipse is one of the most anticipated
    of the decade (visible across Iceland, Spain). Pin it."""
    eclipses = find_upcoming_eclipses(jd_now=JD_2026_01_01, count=3)
    solar_totals = [e for e in eclipses if e["family"] == "SOLAR" and e["subtype"] == "TOTAL"]
    assert any(e["date"] == "2026-08-12" for e in solar_totals)


# ---------- upcoming_eclipses_payload ----------

def test_payload_summary_shape() -> None:
    payload = upcoming_eclipses_payload(jd_now=JD_2026_01_01, count=3)
    assert "eclipses" in payload
    assert "summary" in payload
    s = payload["summary"]
    assert s["total_count"] == len(payload["eclipses"])
    assert s["solar_count"] + s["lunar_count"] == s["total_count"]
    if payload["eclipses"]:
        assert s["next"] == payload["eclipses"][0]


def test_payload_default_jd_uses_current_time() -> None:
    """jd_now=None → uses current UT moment. Just verify it returns
    *some* eclipses (there are always eclipses in the next year)."""
    payload = upcoming_eclipses_payload(jd_now=None, count=2)
    assert payload["summary"]["total_count"] >= 1


# ---------- /medini/eclipses route ----------

@pytest.mark.asyncio
async def test_eclipses_endpoint_returns_payload(client) -> None:
    response = await client.get(f"/medini/eclipses?jd={JD_2026_01_01}&count=2")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["solar_count"] == 2
    assert body["summary"]["lunar_count"] == 2
    # Each eclipse has the kurma tag
    for e in body["eclipses"]:
        assert "kurma_region" in e["astrology"]


@pytest.mark.asyncio
async def test_eclipses_page_returns_html(client) -> None:
    response = await client.get("/medini/eclipses/page")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "<title>Eclipse Impact Mapper" in body
    assert "/medini/eclipses" in body
    assert "/medini/regions" in body
