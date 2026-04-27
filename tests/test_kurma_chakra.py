"""Tests for the Kurma Chakra grid: nakshatra->region mapping, point-in-region
lookup, and GeoJSON serialization. Pinned to the table on page 3 of the
Project Medini-Intelligence PDF (Brihat Samhita Ch 14)."""
from __future__ import annotations

import pytest

from app.medini.kurma_chakra import (
    ALL_REGIONS,
    REGIONS_TABLE,
    all_nakshatra_regions,
    all_regions_geojson,
    info_for_region,
    region_for_coordinates,
    region_for_nakshatra,
    tattva_for_region,
)


# Pinning: every nakshatra index 0..26 -> region per the PDF's Brihat Samhita
# table. Three nakshatras per region; cycle wraps so 26 (Revati), 0 (Ashwini),
# 1 (Bharani) all live in North-East.
EXPECTED_NAKSHATRA_REGIONS = [
    (0,  "Ashwini",            "North-East"),
    (1,  "Bharani",            "North-East"),
    (2,  "Krittika",           "Central"),
    (3,  "Rohini",             "Central"),
    (4,  "Mrigashira",         "Central"),
    (5,  "Ardra",              "East"),
    (6,  "Punarvasu",          "East"),
    (7,  "Pushya",             "East"),
    (8,  "Ashlesha",           "South-East"),
    (9,  "Magha",              "South-East"),
    (10, "Purva Phalguni",     "South-East"),
    (11, "Uttara Phalguni",    "South"),
    (12, "Hasta",              "South"),
    (13, "Chitra",             "South"),
    (14, "Swati",              "South-West"),
    (15, "Vishakha",           "South-West"),
    (16, "Anuradha",           "South-West"),
    (17, "Jyeshta",            "West"),
    (18, "Moola",              "West"),
    (19, "Purva Ashadha",      "West"),
    (20, "Uttara Ashadha",     "North-West"),
    (21, "Shravana",           "North-West"),
    (22, "Dhanishta",          "North-West"),
    (23, "Shatabhisha",        "North"),
    (24, "Purva Bhadrapada",   "North"),
    (25, "Uttara Bhadrapada",  "North"),
    (26, "Revati",             "North-East"),
]


@pytest.mark.parametrize("idx,name,expected_region", EXPECTED_NAKSHATRA_REGIONS)
def test_region_for_nakshatra(idx: int, name: str, expected_region: str) -> None:
    assert region_for_nakshatra(idx) == expected_region


def test_region_for_nakshatra_validates_range() -> None:
    with pytest.raises(ValueError):
        region_for_nakshatra(-1)
    with pytest.raises(ValueError):
        region_for_nakshatra(27)


def test_27_nakshatras_partition_into_9_regions_of_3_each() -> None:
    """Sanity: every region holds exactly 3 nakshatras; total = 27 = 9*3."""
    counts: dict[str, int] = {}
    for idx in range(27):
        r = region_for_nakshatra(idx)
        counts[r] = counts.get(r, 0) + 1
    assert sum(counts.values()) == 27
    assert len(counts) == 9
    assert all(c == 3 for c in counts.values())


# Point-in-region: pinned cities. Some pins (e.g. Bangalore in Central) are
# astrologically authoritative. Others (NYC in North-West) are best-effort
# generalizations of an India-centric system to the global grid.
@pytest.mark.parametrize("city,lat,lon,expected", [
    ("Bangalore",     12.97,  77.59, "Central"),
    ("Delhi",         28.61,  77.21, "Central"),
    ("Mumbai",        19.07,  72.87, "Central"),
    ("Tokyo",         35.68, 139.69, "North-East"),
    ("NYC",           40.71, -74.01, "North-West"),
    ("Sydney",       -33.87, 151.21, "South-East"),
    ("London",        51.50,  -0.13, "North-West"),
    ("Cape Town",    -33.92,  18.42, "South-West"),
    ("Buenos Aires", -34.60, -58.38, "South-West"),
    ("Singapore",      1.35, 103.82, "East"),
])
def test_region_for_coordinates_pinned_cities(
    city: str, lat: float, lon: float, expected: str
) -> None:
    assert region_for_coordinates(lat, lon) == expected, f"{city} should be in {expected}"


def test_region_for_coordinates_lon_normalization() -> None:
    """Longitudes outside [-180, 180] should normalize correctly: 200 == -160."""
    assert region_for_coordinates(0.0, 200.0) == region_for_coordinates(0.0, -160.0)


def test_region_for_coordinates_validates_lat() -> None:
    with pytest.raises(ValueError):
        region_for_coordinates(-91.0, 0.0)
    with pytest.raises(ValueError):
        region_for_coordinates(91.0, 0.0)


def test_region_for_coordinates_polar_edges() -> None:
    """Lat == 90 must snap to one of the three north cells based on lon band."""
    assert region_for_coordinates(90.0, 0.0) == "North-West"
    assert region_for_coordinates(90.0, 80.0) == "North"
    assert region_for_coordinates(90.0, 150.0) == "North-East"


def test_tattva_for_region() -> None:
    # Spot-checks per PDF table.
    assert tattva_for_region("Central") == "Earth/Fire"
    assert tattva_for_region("South") == "Earth/Fire"
    assert tattva_for_region("North-East") == "Water/Fire"
    assert tattva_for_region("South-East") == "Fire/Water"


def test_info_for_region_shape() -> None:
    info = info_for_region("Central")
    assert info.region == "Central"
    assert info.tattva == "Earth/Fire"
    assert info.region_planets == ("Sun", "Moon", "Mars")
    assert info.nakshatras == ("Krittika", "Rohini", "Mrigashira")
    assert info.nakshatra_indices == (2, 3, 4)
    assert "Central" in info.description or "interior" in info.description.lower()
    assert len(info.bbox) == 4


def test_all_regions_count() -> None:
    assert len(ALL_REGIONS) == 9
    assert len(REGIONS_TABLE) == 9


def test_all_regions_geojson_shape() -> None:
    fc = all_regions_geojson()
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 9
    for feat in fc["features"]:
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "Polygon"
        coords = feat["geometry"]["coordinates"][0]
        assert len(coords) == 5, "Polygon ring must have 5 points (closes on itself)"
        assert coords[0] == coords[-1], "ring must close (first point equals last)"
        # GeoJSON convention: [lon, lat]. Sanity-check lon is in [-180, 180].
        for lon, lat in coords:
            assert -180.0 <= lon <= 180.0
            assert -90.0 <= lat <= 90.0
        for key in ("region", "tattva", "region_planets", "nakshatras",
                    "nakshatra_indices", "description"):
            assert key in feat["properties"], f"missing property {key}"


def test_all_nakshatra_regions() -> None:
    rows = all_nakshatra_regions()
    assert len(rows) == 27
    # Spot-check: Krittika is index 2, in Central, Earth/Fire tattva.
    krittika = rows[2]
    assert krittika["name"] == "Krittika"
    assert krittika["region"] == "Central"
    assert krittika["tattva"] == "Earth/Fire"
    assert "Sun" in krittika["region_planets"]
    # Wrap edge: Revati (26) is North-East alongside Ashwini (0) and Bharani (1).
    revati = rows[26]
    assert revati["name"] == "Revati"
    assert revati["region"] == "North-East"
