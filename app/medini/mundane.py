"""Daily Mundane Forecast — the "cosmic weather" feed.

For any given moment (default: now in UT), compute three classes of
significant astrological events:

  - INGRESS:     a planet just changed signs or is about to.
  - STATION:     a planet is transitioning direct↔retrograde (velocity sign flip).
  - CONJUNCTION: two planets within a tight orb (default 2°).

Each event is tagged with the Kurma Chakra region it activates (via the
planet's current nakshatra → region mapping). The result drives the
`/medini/today` page's map highlights and event feed.

Pure functions; no IO, no DB, no daemon dependency. Ad-hoc compute on
each request — fast enough (<10ms per planet for ±3-day window).
"""
from __future__ import annotations

import datetime as dt
import itertools
from typing import Any, Literal

import swisseph as swe

from app.core.ephemeris_engine import PLANETS, ZODIAC_SIGNS
from app.core.nakshatra import nakshatra_for_longitude
from app.medini.kurma_chakra import (
    KurmaRegion,
    info_for_region,
    region_for_nakshatra,
    tattva_for_region,
)

EventType = Literal["INGRESS", "STATION", "CONJUNCTION"]
EventDirection = Literal["PAST", "UPCOMING"]

# Default ±days windows for ingress/station detection. Tuned so the daily
# feed surfaces meaningful events without being too noisy.
DEFAULT_INGRESS_WINDOW_DAYS = 3.0
DEFAULT_STATION_WINDOW_DAYS = 2.0
DEFAULT_CONJUNCTION_ORB = 2.0  # degrees

# Planets whose Sun-Moon pair we EXCLUDE from conjunction detection — the
# Sun-Moon angle changes constantly through the lunar cycle, so flagging it
# every ~28 days adds noise without insight. New Moon already shows up
# elsewhere (panchanga / eclipses).
_SUN_MOON_PAIR = frozenset({"Sun", "Moon"})


# ---------- Low-level helpers ----------

def current_jd_ut() -> float:
    """Julian Day in UT for the current real-world moment."""
    now = dt.datetime.now(dt.timezone.utc)
    decimal_hour = now.hour + now.minute / 60.0 + now.second / 3600.0
    return swe.julday(now.year, now.month, now.day, decimal_hour, swe.GREG_CAL)


def planet_at_jd(jd: float, planet_name: str) -> dict[str, Any]:
    """Compute position + sign + velocity at a given JD for one planet.

    Uses sidereal Lahiri + FLG_SPEED so velocity is non-zero. Returns the
    minimum information the mundane-forecast functions need (no need to
    recompute the full chart).
    """
    planet_id = PLANETS[planet_name]
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    result, _ = swe.calc_ut(jd, planet_id, flags)
    lon = float(result[0])
    vel = float(result[3])
    sign_idx = int(lon // 30)
    return {
        "planet": planet_name,
        "longitude": lon,
        "sign": sign_idx + 1,
        "sign_name": ZODIAC_SIGNS[sign_idx],
        "degree_in_sign": lon % 30.0,
        "velocity": vel,
        "is_retrograde": vel < 0,
    }


def _circular_distance_180(lon_a: float, lon_b: float) -> float:
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def _kurma_for_planet(planet_data: dict[str, Any]) -> dict[str, Any]:
    """Tag a planet position with its Kurma region info (region/tattva/etc).
    Useful for downstream rendering — the map highlights regions activated
    by today's planets."""
    nak = nakshatra_for_longitude(planet_data["longitude"])
    region = region_for_nakshatra(nak["index"])
    return {
        "nakshatra": nak["name"],
        "nakshatra_index": nak["index"],
        "region": region,
        "tattva": tattva_for_region(region),
    }


# ---------- Detectors ----------

def detect_ingress(
    planet_name: str,
    jd_now: float,
    window_days: float = DEFAULT_INGRESS_WINDOW_DAYS,
) -> dict[str, Any] | None:
    """Detect a sign ingress for `planet_name` within ±window_days of jd_now.

    Returns None if no ingress in window. Compares the planet's sign at
    jd_now-window vs jd_now (PAST ingress) and jd_now vs jd_now+window
    (UPCOMING ingress). PAST takes priority if both apply (rare).
    """
    cur = planet_at_jd(jd_now, planet_name)
    past = planet_at_jd(jd_now - window_days, planet_name)
    future = planet_at_jd(jd_now + window_days, planet_name)

    if past["sign"] != cur["sign"]:
        return {
            "type": "INGRESS",
            "planet": planet_name,
            "from_sign": past["sign_name"],
            "to_sign": cur["sign_name"],
            "direction": "PAST",
            "kurma": _kurma_for_planet(cur),
            "description": (
                f"{planet_name} ingressed from {past['sign_name']} "
                f"into {cur['sign_name']}"
            ),
        }
    if future["sign"] != cur["sign"]:
        return {
            "type": "INGRESS",
            "planet": planet_name,
            "from_sign": cur["sign_name"],
            "to_sign": future["sign_name"],
            "direction": "UPCOMING",
            "kurma": _kurma_for_planet(cur),
            "description": (
                f"{planet_name} approaching ingress from "
                f"{cur['sign_name']} to {future['sign_name']}"
            ),
        }
    return None


def detect_station(
    planet_name: str,
    jd_now: float,
    window_days: float = DEFAULT_STATION_WINDOW_DAYS,
) -> dict[str, Any] | None:
    """Detect a retrograde/direct station within ±window_days.

    Sun and Moon are excluded — they never retrograde geocentrically, and
    flagging their always-direct state would be noise. Nodes (Rahu/Ketu)
    are technically always retrograde in mean motion; their station-flip
    detection is meaningful only for the True Node (which oscillates).
    """
    if planet_name in ("Sun", "Moon"):
        return None

    cur = planet_at_jd(jd_now, planet_name)
    past = planet_at_jd(jd_now - window_days, planet_name)
    future = planet_at_jd(jd_now + window_days, planet_name)

    cur_dir = "retrograde" if cur["is_retrograde"] else "direct"
    past_dir = "retrograde" if past["is_retrograde"] else "direct"
    future_dir = "retrograde" if future["is_retrograde"] else "direct"

    if past_dir != cur_dir:
        return {
            "type": "STATION",
            "planet": planet_name,
            "from_state": past_dir,
            "to_state": cur_dir,
            "direction": "PAST",
            "kurma": _kurma_for_planet(cur),
            "description": (
                f"{planet_name} stationed: now {cur_dir} (was {past_dir})"
            ),
        }
    if future_dir != cur_dir:
        return {
            "type": "STATION",
            "planet": planet_name,
            "from_state": cur_dir,
            "to_state": future_dir,
            "direction": "UPCOMING",
            "kurma": _kurma_for_planet(cur),
            "description": (
                f"{planet_name} approaching station: turning {future_dir}"
            ),
        }
    return None


def detect_close_conjunctions(
    jd_now: float,
    orb_degrees: float = DEFAULT_CONJUNCTION_ORB,
) -> list[dict[str, Any]]:
    """Pairs of planets within orb_degrees of each other right now.

    Excludes Sun-Moon (changes too rapidly to be a useful "today" signal).
    Conjunctions are reported once per pair; the lower-indexed planet name
    is `planet_a`, the higher is `planet_b`.
    """
    positions = {name: planet_at_jd(jd_now, name) for name in PLANETS.keys()}

    conjunctions: list[dict[str, Any]] = []
    for name_a, name_b in itertools.combinations(positions.keys(), 2):
        if frozenset({name_a, name_b}) == _SUN_MOON_PAIR:
            continue
        pa, pb = positions[name_a], positions[name_b]
        orb = _circular_distance_180(pa["longitude"], pb["longitude"])
        if orb <= orb_degrees:
            conjunctions.append({
                "type": "CONJUNCTION",
                "planet_a": name_a,
                "planet_b": name_b,
                "orb_degrees": orb,
                "sign": pa["sign_name"],
                "kurma": _kurma_for_planet(pa),
                "description": (
                    f"{name_a} conjunct {name_b} within {orb:.2f}° in {pa['sign_name']}"
                ),
            })
    return conjunctions


# ---------- The aggregator ----------

def daily_mundane_forecast(
    jd_now: float | None = None,
    *,
    ingress_window_days: float = DEFAULT_INGRESS_WINDOW_DAYS,
    station_window_days: float = DEFAULT_STATION_WINDOW_DAYS,
    conjunction_orb: float = DEFAULT_CONJUNCTION_ORB,
) -> dict[str, Any]:
    """Produce a full "cosmic weather" forecast for the given moment.

    Returns a dict with:
      - `jd`: the moment used (UT Julian Day)
      - `timestamp_utc`: ISO 8601 string for human consumption
      - `events`: list of detected ingresses + stations + conjunctions
      - `planet_positions`: snapshot of all 9 grahas
      - `activated_regions`: 9 Kurma regions, each with the planets currently in it
        (drives the map highlight intensity — a region with 3 planets is
        "more activated" than one with 0)
    """
    if jd_now is None:
        jd_now = current_jd_ut()

    timestamp_utc = (
        dt.datetime.fromtimestamp(0, tz=dt.timezone.utc)
        .replace()  # placeholder; overwritten below
    )
    # Convert JD-UT back to a wall clock for display
    y, m, d, h_decimal = swe.revjul(jd_now, swe.GREG_CAL)
    h = int(h_decimal)
    mi = int((h_decimal - h) * 60)
    s = int(round((((h_decimal - h) * 60) - mi) * 60))
    s = max(0, min(59, s))
    timestamp_utc = dt.datetime(int(y), int(m), int(d), h, mi, s, tzinfo=dt.timezone.utc)

    events: list[dict[str, Any]] = []
    planet_positions: list[dict[str, Any]] = []

    for planet_name in PLANETS.keys():
        # Position snapshot
        pos = planet_at_jd(jd_now, planet_name)
        pos["kurma"] = _kurma_for_planet(pos)
        planet_positions.append(pos)

        # Ingress + station detection per planet
        ingress = detect_ingress(planet_name, jd_now, window_days=ingress_window_days)
        if ingress is not None:
            events.append(ingress)
        station = detect_station(planet_name, jd_now, window_days=station_window_days)
        if station is not None:
            events.append(station)

    events.extend(detect_close_conjunctions(jd_now, orb_degrees=conjunction_orb))

    # Compute activated regions: each region's planet count
    activated: dict[KurmaRegion, list[str]] = {}
    for pos in planet_positions:
        region = pos["kurma"]["region"]
        activated.setdefault(region, []).append(pos["planet"])

    activated_regions = []
    for region, planets in activated.items():
        info = info_for_region(region)
        activated_regions.append({
            "region": region,
            "tattva": info.tattva,
            "planets_present": planets,
            "intensity": len(planets),  # 0..9; higher = more cosmic action here
        })
    # Sort by intensity descending so the map's hottest region is index 0.
    activated_regions.sort(key=lambda r: r["intensity"], reverse=True)

    return {
        "jd": jd_now,
        "timestamp_utc": timestamp_utc.isoformat(),
        "events": events,
        "planet_positions": planet_positions,
        "activated_regions": activated_regions,
        "summary": {
            "event_count": len(events),
            "ingress_count": sum(1 for e in events if e["type"] == "INGRESS"),
            "station_count": sum(1 for e in events if e["type"] == "STATION"),
            "conjunction_count": sum(1 for e in events if e["type"] == "CONJUNCTION"),
        },
    }
