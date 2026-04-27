"""Kurma Chakra: maps the 27 nakshatras to 9 geographic regions per the
Brihat Samhita Ch 14, projected onto modern WGS-84 lat/lon bands.

Source of truth for the table: e:/astro/Geo-Astrological Planetary
Intelligence Engine.pdf, page 3. Each direction holds three consecutive
(in zodiacal order) nakshatras starting from Krittika; the cycle wraps
through Revati so Ashwini and Bharani fall in the North-East.

The geographic projection in v1 is a coarse 9-cell axis-aligned tiling of
the globe, anchored on India (Bangalore -> Central). Authentic Brihat
Samhita boundaries are India-centric; this module's bbox values are a
"modernization for global application" per the PDF, intentionally rough so
v1 ships without PostGIS. Phase 4 polish can swap to authentic multi-polygons
without touching consumers of `region_for_*` (the API stays identical).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.nakshatra import NAKSHATRAS

KurmaRegion = Literal[
    "Central",
    "East",
    "South-East",
    "South",
    "South-West",
    "West",
    "North-West",
    "North",
    "North-East",
]


@dataclass(frozen=True)
class RegionInfo:
    region: KurmaRegion
    tattva: str
    region_planets: tuple[str, ...]
    nakshatras: tuple[str, ...]
    nakshatra_indices: tuple[int, ...]
    description: str
    bbox: tuple[float, float, float, float]  # (lat_min, lat_max, lon_min, lon_max)


# Lat/lon bbox tiling: 3 lat bands x 3 lon bands = 9 cells, anchored so India
# falls in Central. Lower bound inclusive, upper bound exclusive (standard).
#   Lat bands: -90..-30 (south), -30..30 (mid), 30..90 (north)
#   Lon bands: -180..60 (west of India), 60..100 (India + Indian Ocean), 100..180 (east of India)
REGIONS_TABLE: dict[KurmaRegion, dict] = {
    "Central": {
        "tattva": "Earth/Fire",
        "region_planets": ("Sun", "Moon", "Mars"),
        "nakshatras": ("Krittika", "Rohini", "Mrigashira"),
        "nakshatra_indices": (2, 3, 4),
        "description": "Center-point multi-polygons (continental interiors, Central Asia, India)",
        "bbox": (-30.0, 30.0, 60.0, 100.0),
    },
    "East": {
        "tattva": "Water/Air",
        "region_planets": ("Rahu", "Jupiter", "Saturn"),
        "nakshatras": ("Ardra", "Punarvasu", "Pushya"),
        "nakshatra_indices": (5, 6, 7),
        "description": "Eastern continental seaboards, specific longitudinal bounds",
        "bbox": (-30.0, 30.0, 100.0, 180.0),
    },
    "South-East": {
        "tattva": "Fire/Water",
        "region_planets": ("Mercury", "Ketu", "Venus"),
        "nakshatras": ("Ashlesha", "Magha", "Purva Phalguni"),
        "nakshatra_indices": (8, 9, 10),
        "description": "Equatorial and sub-equatorial volcanic and tectonic zones",
        "bbox": (-90.0, -30.0, 100.0, 180.0),
    },
    "South": {
        "tattva": "Earth/Fire",
        "region_planets": ("Sun", "Moon", "Mars"),
        "nakshatras": ("Uttara Phalguni", "Hasta", "Chitra"),
        "nakshatra_indices": (11, 12, 13),
        "description": "Southern latitudinal bounds, southern peninsulas",
        "bbox": (-90.0, -30.0, 60.0, 100.0),
    },
    "South-West": {
        "tattva": "Air/Water",
        "region_planets": ("Rahu", "Jupiter", "Saturn"),
        "nakshatras": ("Swati", "Vishakha", "Anuradha"),
        "nakshatra_indices": (14, 15, 16),
        "description": "South-western coastlines and archipelago formations",
        "bbox": (-90.0, -30.0, -180.0, 60.0),
    },
    "West": {
        "tattva": "Water/Fire",
        "region_planets": ("Mercury", "Ketu", "Venus"),
        "nakshatras": ("Jyeshta", "Moola", "Purva Ashadha"),
        "nakshatra_indices": (17, 18, 19),
        "description": "Western continental margins and desert boundaries",
        "bbox": (-30.0, 30.0, -180.0, 60.0),
    },
    "North-West": {
        "tattva": "Earth/Air",
        "region_planets": ("Sun", "Moon", "Mars"),
        "nakshatras": ("Uttara Ashadha", "Shravana", "Dhanishta"),
        "nakshatra_indices": (20, 21, 22),
        "description": "High-altitude north-western plateaus and steppes",
        "bbox": (30.0, 90.0, -180.0, 60.0),
    },
    "North": {
        "tattva": "Air/Water",
        "region_planets": ("Rahu", "Jupiter", "Saturn"),
        "nakshatras": ("Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada"),
        "nakshatra_indices": (23, 24, 25),
        "description": "Northern polar and sub-polar latitudinal bounds",
        "bbox": (30.0, 90.0, 60.0, 100.0),
    },
    "North-East": {
        "tattva": "Water/Fire",
        "region_planets": ("Mercury", "Ketu", "Venus"),
        # The Vimshottari cycle wraps: index 26 (Revati), then 0 (Ashwini), 1 (Bharani).
        "nakshatras": ("Revati", "Ashwini", "Bharani"),
        "nakshatra_indices": (26, 0, 1),
        "description": "North-eastern tectonic ridges and island chains",
        "bbox": (30.0, 90.0, 100.0, 180.0),
    },
}

ALL_REGIONS: tuple[KurmaRegion, ...] = tuple(REGIONS_TABLE.keys())  # 9 entries

# Inverted index: nakshatra_index -> region. Built once at import time.
_NAK_TO_REGION: dict[int, KurmaRegion] = {
    idx: region
    for region, info in REGIONS_TABLE.items()
    for idx in info["nakshatra_indices"]
}


def region_for_nakshatra(nakshatra_index: int) -> KurmaRegion:
    """Map a nakshatra index (0..26) to its Kurma Chakra region."""
    if not (0 <= nakshatra_index <= 26):
        raise ValueError(f"nakshatra_index must be 0..26, got {nakshatra_index}")
    return _NAK_TO_REGION[nakshatra_index]


def region_for_coordinates(latitude: float, longitude: float) -> KurmaRegion:
    """Map WGS-84 lat/lon to a Kurma region via the 9-cell global tiling.

    Boundaries: standard tile convention (lower bound inclusive, upper
    bound exclusive). Edge cases at lat=90 and lon=180 are snapped to the
    appropriate adjacent cell.
    """
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError(f"latitude must be -90..90, got {latitude}")
    # Normalize longitude to [-180, 180); 180 wraps to -180.
    lon = ((longitude + 180.0) % 360.0) - 180.0

    for region_name, info in REGIONS_TABLE.items():
        lat_min, lat_max, lon_min, lon_max = info["bbox"]
        if (lat_min <= latitude < lat_max) and (lon_min <= lon < lon_max):
            return region_name

    # Edge: lat exactly == 90. Pick the polar cell whose lon band matches.
    if latitude >= 90.0:
        if lon < 60.0:
            return "North-West"
        if lon < 100.0:
            return "North"
        return "North-East"

    raise RuntimeError(f"no region matched ({latitude}, {longitude})")


def tattva_for_region(region: KurmaRegion) -> str:
    return REGIONS_TABLE[region]["tattva"]


def info_for_region(region: KurmaRegion) -> RegionInfo:
    info = REGIONS_TABLE[region]
    return RegionInfo(
        region=region,
        tattva=info["tattva"],
        region_planets=tuple(info["region_planets"]),
        nakshatras=tuple(info["nakshatras"]),
        nakshatra_indices=tuple(info["nakshatra_indices"]),
        description=info["description"],
        bbox=tuple(info["bbox"]),
    )


def all_regions_geojson() -> dict:
    """Return the 9 regions as a GeoJSON FeatureCollection.

    Each feature is a Polygon (5-point ring closing on itself) plus
    properties carrying the region's astrological metadata. Frontend
    Leaflet/Deck.gl renders this directly.
    """
    features = []
    for region_name in ALL_REGIONS:
        info = REGIONS_TABLE[region_name]
        lat_min, lat_max, lon_min, lon_max = info["bbox"]
        # GeoJSON uses [lon, lat] order. Counter-clockwise winding for outer ring.
        coords = [
            [lon_min, lat_min],
            [lon_max, lat_min],
            [lon_max, lat_max],
            [lon_min, lat_max],
            [lon_min, lat_min],
        ]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": {
                "region": region_name,
                "tattva": info["tattva"],
                "region_planets": list(info["region_planets"]),
                "nakshatras": list(info["nakshatras"]),
                "nakshatra_indices": list(info["nakshatra_indices"]),
                "description": info["description"],
            },
        })
    return {"type": "FeatureCollection", "features": features}


def all_nakshatra_regions() -> list[dict]:
    """Per-nakshatra region/tattva info for all 27 nakshatras, ordered by index.

    The educational widget consumes this for its nakshatra-detail panel.
    Joins the canonical NAKSHATRAS tuple from app.core.nakshatra with the
    region table so the source of truth for nakshatra names stays single.
    """
    out = []
    for idx in range(27):
        region = region_for_nakshatra(idx)
        info = REGIONS_TABLE[region]
        out.append({
            "index": idx,
            "name": NAKSHATRAS[idx],
            "region": region,
            "tattva": info["tattva"],
            "region_planets": list(info["region_planets"]),
        })
    return out
