"""Multi-day mundane forecast engine — the "next 30 days of cosmic weather".

Where ``app.medini.mundane`` answers "what's happening RIGHT NOW (+/- 3 days)",
this module answers "what events will fire in the next N days?" by scanning
day-by-day through the horizon and consolidating duplicate detections.

Event taxonomy:

* INGRESS    — a planet crosses into a new sign (one event per ingress JD,
               not one per day-it's-detected).
* STATION    — a planet's velocity sign flips (retrograde<->direct station).
* CONJUNCTION — two planets within ``conjunction_orb`` — emitted with the
               exact JD of MINIMUM orb across the horizon, not every day
               the pair stays close.
* LUNATION   — new moon (Sun-Moon orb ~0) and full moon (~180); the most
               watched mundane "tick".
* ECLIPSE    — sourced from ``app.medini.eclipses.find_upcoming_eclipses``,
               re-shaped into the same event envelope.

Every event carries:

* ``jd``: the exact JD of the event (for sortability)
* ``date_utc``: human-readable ISO date
* ``planet`` or ``planets``: the actor(s) involved
* ``kurma``: the Kurma region activated (via nakshatra->region)
* ``description``: a one-line narrative the UI can show before severity/
                   doctrine grounding gets layered on by other modules

Pure functions; severity, domain attribution, and RAG-citation enrichment
live in separate modules so the engine stays focused on detection.
"""
from __future__ import annotations

import datetime as dt
import itertools
import logging
from typing import Any, Literal

import swisseph as swe

from app.core.ephemeris_engine import PLANETS
from app.medini.eclipses import find_upcoming_eclipses
from app.medini.mundane import (
    _circular_distance_180,
    _kurma_for_planet,
    current_jd_ut,
    planet_at_jd,
)

logger = logging.getLogger(__name__)

EventType = Literal[
    "INGRESS", "STATION", "CONJUNCTION", "NEW_MOON", "FULL_MOON", "ECLIPSE",
]

# Defaults tuned for a balanced 30-day feed: slow planets dominate ingresses
# so they're rare and important; tight orb keeps conjunctions to genuine
# alignments rather than near-misses.
DEFAULT_HORIZON_DAYS = 30
DEFAULT_CONJUNCTION_ORB = 2.0
DEFAULT_LUNATION_ORB = 0.5  # exact-ish — we want the day-of-lunation
DEFAULT_SCAN_STEP_DAYS = 1.0

# Per-planet velocity-hysteresis threshold (deg/day). Only emit a STATION
# event when the planet's velocity magnitude was ABOVE this on both sides
# of the flip; otherwise we're detecting wobble around stationary, not a
# real direction change. Rahu/Ketu in true-node mode oscillate near 0 for
# many days at "real" stations — without hysteresis we'd emit 3-5 spurious
# stations for one actual one. Tuned empirically against the May-Jun 2026
# anchor window which produced 3 Rahu stations in 12 days before this.
#
# Other planets (Mercury, Venus, Mars, etc.) have CLEAN turning points —
# they decelerate smoothly across zero. The strict hysteresis was eating
# legit Mercury stations, so we apply it only to the nodes and leave the
# other planets near-unfiltered. Threshold of 0.0 means "any direction
# change counts" (the original behaviour).
_STATION_HYSTERESIS_DEG_PER_DAY: dict[str, float] = {
    "Rahu":    0.03,
    "Ketu":    0.03,
    "Mercury": 0.0,   # clean turning point — no wobble to suppress
    "Venus":   0.0,
    "Mars":    0.0,
    "Jupiter": 0.0,
    "Saturn":  0.0,
}
_DEFAULT_STATION_HYSTERESIS = 0.0

# Planets whose retrograde station we DO track (Sun + Moon never retrograde
# geocentrically, so we'd emit zero events for them and just waste cycles).
_RETROGRADE_PLANETS = tuple(p for p in PLANETS if p not in ("Sun", "Moon"))


def _jd_to_iso_date(jd_ut: float) -> str:
    """JD (UT) -> 'YYYY-MM-DD' for the calendar/group-by-day display."""
    y, m, d, _ = swe.revjul(jd_ut, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _jd_to_iso_datetime(jd_ut: float) -> str:
    """JD (UT) -> ISO 8601 datetime (sortable, machine-parseable)."""
    y, m, d, h_decimal = swe.revjul(jd_ut, swe.GREG_CAL)
    h = int(h_decimal)
    mi = int((h_decimal - h) * 60)
    s = int(round((((h_decimal - h) * 60) - mi) * 60))
    s = max(0, min(59, s))
    return dt.datetime(
        int(y), int(m), int(d), h, mi, s, tzinfo=dt.timezone.utc,
    ).isoformat()


# --------------------------------------------------------------------------- #
# Day-by-day scanners with deduplication                                       #
# --------------------------------------------------------------------------- #

def scan_ingresses(
    jd_start: float, horizon_days: int,
    step_days: float = DEFAULT_SCAN_STEP_DAYS,
) -> list[dict[str, Any]]:
    """Walk through the horizon, emit one INGRESS per actual sign change.

    Compares each planet's sign at consecutive scan points; the first scan
    point where the new sign appears is the event JD. (This is conservative
    by up to step_days; for the consumer-facing feed that's fine — finer
    resolution would just spam the page without changing the date-of-event.)
    """
    events: list[dict[str, Any]] = []
    n_steps = int(horizon_days / step_days) + 1

    for planet_name in PLANETS.keys():
        prev_sign: int | None = None
        for i in range(n_steps):
            jd = jd_start + i * step_days
            pos = planet_at_jd(jd, planet_name)
            cur_sign = pos["sign"]
            if prev_sign is not None and cur_sign != prev_sign:
                prev_pos = planet_at_jd(jd - step_days, planet_name)
                events.append({
                    "type": "INGRESS",
                    "jd": jd,
                    "date_utc": _jd_to_iso_date(jd),
                    "datetime_utc": _jd_to_iso_datetime(jd),
                    "planet": planet_name,
                    "from_sign": prev_pos["sign_name"],
                    "to_sign": pos["sign_name"],
                    "kurma": _kurma_for_planet(pos),
                    "description": (
                        f"{planet_name} ingresses {pos['sign_name']} "
                        f"(from {prev_pos['sign_name']})"
                    ),
                })
            prev_sign = cur_sign
    return events


def scan_stations(
    jd_start: float, horizon_days: int,
    step_days: float = DEFAULT_SCAN_STEP_DAYS,
) -> list[dict[str, Any]]:
    """Walk the horizon, emit one STATION per velocity-sign flip.

    Only checks planets that can geocentrically retrograde (skips Sun, Moon).

    Applies per-planet velocity-magnitude **hysteresis** to suppress wobble
    around stationary: an event is emitted only if the planet's velocity
    magnitude **before** the flip was above the hysteresis threshold AND
    the magnitude **after** the flip crosses the threshold within a short
    confirmation window (3 scan steps). Without this, true-node Rahu/Ketu
    near their turning points produce 3-5 spurious flips for one real
    station because the node oscillates around 0 velocity for days.
    """
    events: list[dict[str, Any]] = []
    n_steps = int(horizon_days / step_days) + 1

    for planet_name in _RETROGRADE_PLANETS:
        hysteresis = _STATION_HYSTERESIS_DEG_PER_DAY.get(
            planet_name, _DEFAULT_STATION_HYSTERESIS,
        )
        # Pre-compute the velocity-sign and magnitude track so the
        # hysteresis check can look ahead a few steps.
        track: list[tuple[float, dict[str, Any]]] = []
        for i in range(n_steps):
            jd = jd_start + i * step_days
            pos = planet_at_jd(jd, planet_name)
            track.append((jd, pos))

        prev_retro: bool | None = None
        prev_pos: dict[str, Any] | None = None
        for i, (jd, pos) in enumerate(track):
            cur_retro = pos["is_retrograde"]
            if prev_retro is not None and cur_retro != prev_retro:
                assert prev_pos is not None
                # Hysteresis: previous step's velocity magnitude must exceed
                # the threshold (so we were genuinely moving) AND at least
                # one of the next 3 steps must also exceed it (so we settle
                # into the new direction rather than wobbling back).
                prev_vel_mag = abs(prev_pos["velocity"])
                next_three = track[i:i + 3]
                future_settled = any(
                    abs(p[1]["velocity"]) > hysteresis
                    and p[1]["is_retrograde"] == cur_retro
                    for p in next_three
                )
                if prev_vel_mag > hysteresis and future_settled:
                    to_state = "retrograde" if cur_retro else "direct"
                    from_state = "direct" if cur_retro else "retrograde"
                    events.append({
                        "type": "STATION",
                        "jd": jd,
                        "date_utc": _jd_to_iso_date(jd),
                        "datetime_utc": _jd_to_iso_datetime(jd),
                        "planet": planet_name,
                        "from_state": from_state,
                        "to_state": to_state,
                        "kurma": _kurma_for_planet(pos),
                        "description": (
                            f"{planet_name} stations {to_state} "
                            f"(was {from_state})"
                        ),
                    })
            prev_retro = cur_retro
            prev_pos = pos
    return events


def _orb_for_pair(jd: float, a: str, b: str) -> float:
    """Minimum-image orb in degrees between two planets at one JD."""
    pa = planet_at_jd(jd, a)
    pb = planet_at_jd(jd, b)
    return _circular_distance_180(pa["longitude"], pb["longitude"])


def scan_conjunctions(
    jd_start: float, horizon_days: int,
    *,
    orb_degrees: float = DEFAULT_CONJUNCTION_ORB,
    step_days: float = DEFAULT_SCAN_STEP_DAYS,
) -> list[dict[str, Any]]:
    """Find minimum-orb conjunctions per pair across the horizon.

    Walks each pair day-by-day, tracks the running minimum orb, and emits
    a single CONJUNCTION event per pair if and only if the minimum dipped
    below ``orb_degrees``. This avoids spamming the calendar with 14 daily
    'Saturn within 1.8° of Pluto' rows when one tightly-orbed event would
    say it once.
    """
    events: list[dict[str, Any]] = []
    n_steps = int(horizon_days / step_days) + 1
    planet_names = list(PLANETS.keys())

    for a, b in itertools.combinations(planet_names, 2):
        if {a, b} == {"Sun", "Moon"}:
            continue  # lunations are handled separately
        best_jd: float | None = None
        best_orb = float("inf")
        for i in range(n_steps):
            jd = jd_start + i * step_days
            orb = _orb_for_pair(jd, a, b)
            if orb < best_orb:
                best_orb = orb
                best_jd = jd
        if best_jd is not None and best_orb <= orb_degrees:
            pa = planet_at_jd(best_jd, a)
            events.append({
                "type": "CONJUNCTION",
                "jd": best_jd,
                "date_utc": _jd_to_iso_date(best_jd),
                "datetime_utc": _jd_to_iso_datetime(best_jd),
                "planet_a": a,
                "planet_b": b,
                "orb_degrees": best_orb,
                "sign": pa["sign_name"],
                "kurma": _kurma_for_planet(pa),
                "description": (
                    f"{a} conjunct {b} within {best_orb:.2f}° in {pa['sign_name']}"
                ),
            })
    return events


def scan_lunations(
    jd_start: float, horizon_days: int,
    *,
    orb_degrees: float = DEFAULT_LUNATION_ORB,
    step_days: float = DEFAULT_SCAN_STEP_DAYS,
) -> list[dict[str, Any]]:
    """Detect new moon (Sun-Moon = 0°) and full moon (= 180°) within horizon.

    Uses a geometric crossing test rather than a tight-orb minimum search.
    Reason: with a 1-day scan step the Moon moves ~13° per step, so an
    orb-window detector (looking for moments where |angle| < 0.5°) almost
    never lands inside the orb — it would miss every lunation. Instead we
    track the monotonically-increasing Sun-Moon angular separation and
    flag a CROSSING:

      * NEW_MOON: the angle wraps from near-360° back to near-0°
      * FULL_MOON: the angle crosses 180° going up

    The reported JD is interpolated linearly between the two scan points,
    which lands within a few hours of truth — plenty for a mundane
    "lunation on the 14th" feed.

    The ``orb_degrees`` kwarg is preserved for API compatibility but no
    longer materially gates detection — the crossing test is exact up to
    interpolation. Pass orb_degrees=0 (or anything) and behaviour is
    identical.
    """
    _ = orb_degrees  # accepted for backward compat; not used in geometric test
    events: list[dict[str, Any]] = []
    n_steps = int(horizon_days / step_days) + 1

    def sun_moon_angle(jd: float) -> float:
        sun = planet_at_jd(jd, "Sun")
        moon = planet_at_jd(jd, "Moon")
        return (moon["longitude"] - sun["longitude"]) % 360.0

    prev_jd = jd_start
    prev_angle = sun_moon_angle(prev_jd)
    for i in range(1, n_steps):
        cur_jd = jd_start + i * step_days
        cur_angle = sun_moon_angle(cur_jd)

        # NEW_MOON: angle wraps around (prev close to 360, cur close to 0).
        # Detect via prev > cur AND the step crosses the 0/360 boundary.
        if prev_angle > cur_angle:
            # Interpolate at the crossing of 360->0
            # frac of step at which angle hits 360 (== 0): how much further
            # to go past prev_jd before angle resets.
            distance_to_zero = 360.0 - prev_angle
            distance_in_step = (360.0 - prev_angle) + cur_angle
            frac = distance_to_zero / distance_in_step if distance_in_step > 0 else 0.5
            cross_jd = prev_jd + frac * (cur_jd - prev_jd)
            events.append(_lunation_event(cross_jd, "NEW_MOON"))

        # FULL_MOON: angle crosses 180 going up (prev < 180 <= cur)
        if prev_angle < 180.0 <= cur_angle:
            frac = (180.0 - prev_angle) / (cur_angle - prev_angle) if cur_angle != prev_angle else 0.5
            cross_jd = prev_jd + frac * (cur_jd - prev_jd)
            events.append(_lunation_event(cross_jd, "FULL_MOON"))

        prev_jd = cur_jd
        prev_angle = cur_angle

    return events


def _lunation_event(jd: float, kind: Literal["NEW_MOON", "FULL_MOON"]) -> dict[str, Any]:
    """Build a lunation event — keyed off the Moon's position so the Kurma
    tagging follows the Moon (the dynamic luminary, not the Sun)."""
    moon = planet_at_jd(jd, "Moon")
    label = "New Moon" if kind == "NEW_MOON" else "Full Moon"
    return {
        "type": kind,
        "jd": jd,
        "date_utc": _jd_to_iso_date(jd),
        "datetime_utc": _jd_to_iso_datetime(jd),
        "planet": "Moon",
        "sign": moon["sign_name"],
        "kurma": _kurma_for_planet(moon),
        "description": f"{label} in {moon['sign_name']}",
    }


def scan_eclipses(
    jd_start: float, horizon_days: int,
) -> list[dict[str, Any]]:
    """Re-shape upcoming eclipses into the forecast event envelope.

    Pulls eclipses one family at a time until either the count exhausts or
    the JD falls outside the horizon. Re-uses the existing ``eclipses.py``
    detection — same Kurma tagging, same nakshatra mapping.
    """
    horizon_end = jd_start + horizon_days
    events: list[dict[str, Any]] = []
    # Look up 5 of each — for a 30-day window almost always overshoots,
    # then we slice by horizon.
    raw = find_upcoming_eclipses(jd_start, count=5)
    for ecl in raw:
        jd = ecl["jd"]
        if jd < jd_start or jd > horizon_end:
            continue
        family = ecl["family"]  # SOLAR or LUNAR
        events.append({
            "type": "ECLIPSE",
            "jd": jd,
            "date_utc": _jd_to_iso_date(jd),
            "datetime_utc": _jd_to_iso_datetime(jd),
            "family": family,
            "subtype": ecl.get("subtype"),
            "luminary_nakshatra": ecl.get("nakshatra"),
            "kurma": {
                "region": ecl.get("region"),
                "tattva": ecl.get("tattva"),
                "nakshatra": ecl.get("nakshatra"),
            },
            "max_location": ecl.get("max_location"),  # solar only
            "description": (
                f"{family.title()} eclipse ({ecl.get('subtype', '')}) "
                f"in {ecl.get('nakshatra', '?')}"
            ),
        })
    return events


# --------------------------------------------------------------------------- #
# Aggregator                                                                   #
# --------------------------------------------------------------------------- #

def multi_day_forecast(
    jd_start: float | None = None,
    *,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    conjunction_orb: float = DEFAULT_CONJUNCTION_ORB,
    lunation_orb: float = DEFAULT_LUNATION_ORB,
    step_days: float = DEFAULT_SCAN_STEP_DAYS,
) -> dict[str, Any]:
    """Aggregate every event type over the horizon and group by date.

    Returns a payload with:

      * ``horizon_days`` / ``jd_start`` / ``date_start_utc``
      * ``events``: all events sorted by jd ascending
      * ``by_day``: {YYYY-MM-DD: [events]} for the calendar view
      * ``summary``: counts per event type

    Severity scoring + domain attribution + RAG-citation enrichment are
    layered on top by the route handler (so this function stays pure and
    the enrichment can be turned on/off per request).
    """
    if jd_start is None:
        jd_start = current_jd_ut()
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive")

    events: list[dict[str, Any]] = []
    events.extend(scan_ingresses(jd_start, horizon_days, step_days))
    events.extend(scan_stations(jd_start, horizon_days, step_days))
    events.extend(scan_conjunctions(
        jd_start, horizon_days,
        orb_degrees=conjunction_orb, step_days=step_days,
    ))
    events.extend(scan_lunations(
        jd_start, horizon_days,
        orb_degrees=lunation_orb, step_days=step_days,
    ))
    events.extend(scan_eclipses(jd_start, horizon_days))

    events.sort(key=lambda e: e["jd"])

    by_day: dict[str, list[dict[str, Any]]] = {}
    for e in events:
        by_day.setdefault(e["date_utc"], []).append(e)

    summary = {
        "total": len(events),
        "by_type": {
            t: sum(1 for e in events if e["type"] == t)
            for t in ("INGRESS", "STATION", "CONJUNCTION",
                      "NEW_MOON", "FULL_MOON", "ECLIPSE")
        },
    }

    return {
        "jd_start": jd_start,
        "date_start_utc": _jd_to_iso_date(jd_start),
        "horizon_days": horizon_days,
        "events": events,
        "by_day": by_day,
        "summary": summary,
    }
