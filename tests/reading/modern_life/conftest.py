"""Shared fixtures for ``app.reading.modern_life`` tests."""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def bangalore_chart() -> dict:
    """The canonical Bangalore baseline chart (CLAUDE.md test-pinning policy).

    1990-07-15 12:00 IST at 12.97 N, 77.59 E. Virgo lagna ~173.99°,
    Mercury MD, Moon at Revati pada 3.
    """
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="session")
def asc_sign(bangalore_chart) -> int:
    return bangalore_chart["ascendant"]["sign"]


# ---------------------------------------------------------------------------
# Synthetic chart helpers — let detector tests force particular placements
# ---------------------------------------------------------------------------


def make_synthetic_chart(
    asc_sign: int = 1,
    d1_overrides: dict[str, int] | None = None,
    d10_overrides: dict[str, int] | None = None,
    d9_overrides: dict[str, int] | None = None,
    d24_overrides: dict[str, int] | None = None,
    moon_nakshatra_lord: str = "Mercury",
) -> dict:
    """Build a minimal synthetic chart for testing one detector at a time.

    ``d1_overrides`` etc map planet name -> sign (1..12). Planets not
    listed get a default Sun-sign placement (sign=1, Aries) which keeps
    the detector queries deterministic.
    """
    planets = (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    )

    def build_div(overrides: dict[str, int] | None) -> dict:
        out: dict[str, dict] = {}
        ov = overrides or {}
        for p in planets:
            sign = ov.get(p, 1)
            entry: dict = {
                "sign": sign,
                "sign_name": f"sign_{sign}",
                "degree_in_sign": 10.0,
                "longitude": (sign - 1) * 30 + 10.0,
                "is_retrograde": False,
                "name": p,
            }
            if p == "Moon":
                entry["nakshatra"] = {
                    "index": 1,
                    "name": "Synthetic",
                    "pada": 1,
                    "lord": moon_nakshatra_lord,
                    "longitude_in_nakshatra": 5.0,
                }
            out[p] = entry
        return out

    return {
        "d1":  build_div(d1_overrides),
        "d9":  build_div(d9_overrides),
        "d10": build_div(d10_overrides),
        "d24": build_div(d24_overrides),
        "ascendant": {
            "sign": asc_sign,
            "longitude": (asc_sign - 1) * 30 + 15.0,
            "sign_name": f"asc_{asc_sign}",
            "degree_in_sign": 15.0,
        },
    }


@pytest.fixture(scope="session")
def synthetic():
    """Factory fixture: ``synthetic(asc_sign=1, d1_overrides={...})`` builds a chart."""
    return make_synthetic_chart
