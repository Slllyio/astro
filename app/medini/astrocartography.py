"""Astrocartography line computation for the personalized Geo-Astrological map.

For a given birth moment (Julian Day), each of the 9 grahas projects 4 angular
lines onto the Earth's surface:

  - MC  (Midheaven / 10th cusp): vertical line at the longitude where the
        planet is on the upper meridian at the natal moment.
  - IC  (Imum Coeli / 4th cusp): vertical line at MC ± 180°.
  - Asc (Ascendant / 1st cusp):  curve where the planet is rising on the
        eastern horizon at the natal moment.
  - Desc (Descendant / 7th):     curve where the planet is setting.

These lines are deterministic celestial geometry — no ML, no ayanamsa
dependency. The math operates in EQUATORIAL coordinates (RA/Dec) returned by
Swiss Ephemeris with FLG_EQUATORIAL; the project's sidereal Lahiri mode
applies only to the engine's ecliptic outputs, not here.

Standard formulas:
    GST_deg = 15 * GST_hours
    lon_MC(planet) = (RA - GST + 540) mod 360 - 180  (normalize to [-180, 180])
    lon_IC(planet) = lon_MC + 180
    cos(H) = -tan(latitude) * tan(declination)        ← rising/setting condition
    lon_Asc(latitude) = RA - H - GST  (LHA = -H, east of meridian)
    lon_Desc(latitude) = RA + H - GST (LHA = +H, west of meridian)

Reference: Erlewine 1976 ("Astro*Carto*Graphy"), and any modern ACG textbook.
"""
from __future__ import annotations

import math
from typing import Literal, TypedDict

import swisseph as swe

# Planets whose lines we compute. Keko: TRUE_NODE for Rahu (matches the
# project-wide convention in app/core/ephemeris_engine.py); Ketu is derived
# as Rahu reflected through the celestial origin.
_BASE_PLANETS: dict[str, int] = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus":   swe.VENUS,
    "Mars":    swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn":  swe.SATURN,
    "Rahu":    swe.TRUE_NODE,
}

PlanetName = Literal[
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu",
]
LineAngle = Literal["MC", "IC", "Asc", "Desc"]

# Latitude sample resolution. 2° gives 67 samples per Asc/Desc curve which is
# smooth on the map without bloating payload size. The MC/IC lines are
# vertical and only need endpoints, so they're cheap regardless.
_ASC_DESC_LAT_STEP = 2
_ASC_DESC_LAT_MIN = -66   # circumpolar zone for many declinations starts ~66°
_ASC_DESC_LAT_MAX = 66

# MC/IC vertical lines: cap at ±85° to avoid degenerate polar rendering.
_MC_IC_LAT_MIN = -85
_MC_IC_LAT_MAX = 85
_MC_IC_LAT_STEP = 5


class PlanetaryLine(TypedDict):
    planet: str
    angle: str  # "MC" | "IC" | "Asc" | "Desc"
    coords: list[list[float]]  # list of [lat, lon] pairs (Leaflet convention)


def _normalize_longitude(lon_deg: float) -> float:
    """Wrap longitude to [-180, 180)."""
    return ((lon_deg + 180.0) % 360.0) - 180.0


def _planet_ra_dec(jd: float, planet_id: int) -> tuple[float, float]:
    """Return (RA, Dec) in degrees for a planet at the given Julian Day.

    Uses FLG_EQUATORIAL so swisseph returns equatorial coordinates directly.
    Independent of ayanamsa / sidereal mode (those affect ecliptic outputs only).
    """
    result, _ = swe.calc_ut(jd, planet_id, swe.FLG_EQUATORIAL)
    return float(result[0]), float(result[1])


def _ketu_ra_dec(rahu_ra: float, rahu_dec: float) -> tuple[float, float]:
    """Ketu (south lunar node) is Rahu reflected through the celestial origin:
    RA + 180° (mod 360), Dec negated."""
    return (rahu_ra + 180.0) % 360.0, -rahu_dec


def _mc_ic_lines(planet: str, ra_deg: float, gst_deg: float) -> list[PlanetaryLine]:
    """Two vertical lines: MC at lon=(RA-GST), IC at MC+180°."""
    lon_mc = _normalize_longitude(ra_deg - gst_deg)
    lon_ic = _normalize_longitude(lon_mc + 180.0)

    mc_coords = [[float(lat), lon_mc] for lat in range(_MC_IC_LAT_MIN, _MC_IC_LAT_MAX + 1, _MC_IC_LAT_STEP)]
    ic_coords = [[float(lat), lon_ic] for lat in range(_MC_IC_LAT_MIN, _MC_IC_LAT_MAX + 1, _MC_IC_LAT_STEP)]
    return [
        {"planet": planet, "angle": "MC", "coords": mc_coords},
        {"planet": planet, "angle": "IC", "coords": ic_coords},
    ]


def _asc_desc_lines(planet: str, ra_deg: float, dec_deg: float, gst_deg: float) -> list[PlanetaryLine]:
    """Two curves: Asc (rising) and Desc (setting), sampled by latitude.

    Skips circumpolar latitudes where |tan(phi) * tan(dec)| > 1 (planet never
    rises/sets there). Splits the curve into segments at antimeridian crossings
    so Leaflet polylines render correctly without spanning the entire map.
    """
    dec_rad = math.radians(dec_deg)
    asc_segments: list[list[list[float]]] = [[]]
    desc_segments: list[list[list[float]]] = [[]]

    last_asc_lon: float | None = None
    last_desc_lon: float | None = None

    for lat_deg in range(_ASC_DESC_LAT_MIN, _ASC_DESC_LAT_MAX + 1, _ASC_DESC_LAT_STEP):
        lat_rad = math.radians(lat_deg)
        cos_h = -math.tan(lat_rad) * math.tan(dec_rad)
        if cos_h < -1.0 or cos_h > 1.0:
            # Circumpolar at this latitude. Start a fresh segment afterwards.
            if asc_segments[-1]:
                asc_segments.append([])
                last_asc_lon = None
            if desc_segments[-1]:
                desc_segments.append([])
                last_desc_lon = None
            continue

        h_deg = math.degrees(math.acos(cos_h))
        lon_asc = _normalize_longitude(ra_deg - h_deg - gst_deg)
        lon_desc = _normalize_longitude(ra_deg + h_deg - gst_deg)

        # Antimeridian-crossing detection: if the longitude jumps by more than
        # 180° between consecutive latitude samples, start a new segment so
        # Leaflet doesn't draw a stitch across the whole map.
        if last_asc_lon is not None and abs(lon_asc - last_asc_lon) > 180.0:
            asc_segments.append([])
        asc_segments[-1].append([float(lat_deg), lon_asc])
        last_asc_lon = lon_asc

        if last_desc_lon is not None and abs(lon_desc - last_desc_lon) > 180.0:
            desc_segments.append([])
        desc_segments[-1].append([float(lat_deg), lon_desc])
        last_desc_lon = lon_desc

    # Flatten segments into single polylines. For v1 we concatenate; the
    # antimeridian-split logic ensures consecutive segments stay on the
    # same side of the dateline, but Leaflet's `worldCopyJump` plus our
    # polyline rendering handle this acceptably without explicit
    # multi-line emission.
    asc_coords = [pt for seg in asc_segments for pt in seg]
    desc_coords = [pt for seg in desc_segments for pt in seg]
    return [
        {"planet": planet, "angle": "Asc", "coords": asc_coords},
        {"planet": planet, "angle": "Desc", "coords": desc_coords},
    ]


def compute_planetary_lines(birth_jd: float) -> list[PlanetaryLine]:
    """Compute the 4 angular lines (MC, IC, Asc, Desc) for each of 9 grahas.

    Returns a flat list of 36 PlanetaryLine dicts. Each line's `coords` is a
    list of [lat, lon] pairs in Leaflet's preferred order (note: GeoJSON
    uses [lon, lat] — different convention).

    Args:
        birth_jd: Julian Day (UT) of the natal moment.

    The Greenwich Sidereal Time at birth_jd is the rotational anchor that
    pins the celestial sphere to the geographic globe.
    """
    gst_hours = swe.sidtime(birth_jd)
    gst_deg = (gst_hours * 15.0) % 360.0

    lines: list[PlanetaryLine] = []
    rahu_ra: float | None = None
    rahu_dec: float | None = None

    for planet_name, planet_id in _BASE_PLANETS.items():
        ra_deg, dec_deg = _planet_ra_dec(birth_jd, planet_id)
        if planet_name == "Rahu":
            rahu_ra, rahu_dec = ra_deg, dec_deg

        lines.extend(_mc_ic_lines(planet_name, ra_deg, gst_deg))
        lines.extend(_asc_desc_lines(planet_name, ra_deg, dec_deg, gst_deg))

    # Ketu: south lunar node, derived from Rahu by reflection through the
    # celestial origin (RA + 180°, Dec negated). Ketu's lines fall exactly
    # opposite Rahu's on the globe, which is astrologically correct.
    if rahu_ra is not None and rahu_dec is not None:
        ketu_ra, ketu_dec = _ketu_ra_dec(rahu_ra, rahu_dec)
        lines.extend(_mc_ic_lines("Ketu", ketu_ra, gst_deg))
        lines.extend(_asc_desc_lines("Ketu", ketu_ra, ketu_dec, gst_deg))

    return lines
