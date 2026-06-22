"""Transit-trigger layer — narrows a high-risk dāśā window to the weeks when a
death-sensitive transit is active.

The dāśā shows the *period* (years); classical doctrine says the *transit* (gochara)
pinpoints the moment. We tested this on 8,578 exact-date deaths against a per-person
uniform baseline (transit longitude on a random day is ~uniform over 360°):

  * The only carrier is **transit Saturn** (the slowest graha, the natural maraka)
    conjoining a death-sensitive natal point by degree. Tighter orb → higher lift
    (the hallmark of a real conjunction, not an artifact).
  * Validated trigger — transit Saturn within ±3° of (natal maraka set ∪ natal Sun):
    **lift 1.131, p=0.001**, fires on ~7.7% of death days.
  * Transit Jupiter / Mars / Rahu / Ketu are null; transit Saturn over the 8th-lord
    or Moon is null. (Honest negative results — kept, not papered over.)

So this module exposes exactly that validated trigger and a function that, within a
flagged dāśā window, returns the sub-intervals when Saturn is within orb — turning a
multi-year window into a handful of multi-week danger bands.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import swisseph as swe

from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR, calculate_d1_position
from app.medini.analysis.doctrine_validator import _MARAKA_GRAHAS, _maraka_set

# Validated default: transit Saturn within ±3° of a natal maraka or the natal Sun.
DEFAULT_ORB_DEG: float = 3.0
TRIGGER_PLANET: str = "Saturn"


def _ang_sep(a: float, b: float) -> float:
    """Smallest separation between two ecliptic longitudes (degrees, 0–180)."""
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def saturn_transit_lon(jd: float) -> float:
    """Sidereal (Lahiri) longitude of Saturn at a Julian Day."""
    return float(calculate_d1_position(jd, swe.SATURN)["longitude"]) % 360.0


def death_trigger_points(
    asc_sign: int, graha_houses: dict[str, int], natal_lons: dict[str, float],
) -> list[float]:
    """The validated death-sensitive natal longitudes for the Saturn trigger:
    the maraka_full set (2nd/7th lords + their occupants + natal Saturn) plus the
    natal Sun. `natal_lons` maps graha name → natal longitude (deg)."""
    points = _maraka_set(asc_sign, graha_houses, "full") | {"Sun"}
    return [natal_lons[g] % 360.0 for g in points
            if g in natal_lons and natal_lons[g] is not None]


def is_triggered(jd: float, trigger_points: list[float],
                 orb: float = DEFAULT_ORB_DEG) -> bool:
    """Is transit Saturn within `orb` of any trigger point at this JD?"""
    if not trigger_points:
        return False
    sat = saturn_transit_lon(jd)
    return any(_ang_sep(sat, p) < orb for p in trigger_points)


@dataclass(frozen=True)
class TriggerInterval:
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    days: float


def _jd_to_iso(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def active_trigger_intervals(
    start_jd: float, end_jd: float, trigger_points: list[float],
    orb: float = DEFAULT_ORB_DEG, step_days: float = 3.0,
) -> list[TriggerInterval]:
    """Scan [start_jd, end_jd] and return the contiguous sub-intervals where transit
    Saturn is within `orb` of a trigger point — the weeks-scale danger bands inside a
    multi-year dāśā window. (Saturn ~0.034°/day, so a ±3° pass lasts months around
    direct motion and is split by retrograde loops; a 3-day scan resolves them.)"""
    if not trigger_points or end_jd <= start_jd:
        return []
    intervals: list[TriggerInterval] = []
    jd = start_jd
    run_start: float | None = None
    prev = start_jd
    while jd <= end_jd:
        hot = is_triggered(jd, trigger_points, orb)
        if hot and run_start is None:
            run_start = jd
        elif not hot and run_start is not None:
            intervals.append(_mk_interval(run_start, prev))
            run_start = None
        prev = jd
        jd += step_days
    if run_start is not None:
        intervals.append(_mk_interval(run_start, min(prev, end_jd)))
    return intervals


def _mk_interval(a: float, b: float) -> TriggerInterval:
    return TriggerInterval(
        start_jd=a, end_jd=b, start_date=_jd_to_iso(a), end_date=_jd_to_iso(b),
        days=round(b - a, 1),
    )


# --------------------------------------------------------------------------- #
# Validation entrypoint — reproduce the corpus lift on exact-date deaths.      #
# --------------------------------------------------------------------------- #

def _validate(orb: float = DEFAULT_ORB_DEG) -> dict[str, Any]:
    """Re-run the death-day vs per-person-uniform-baseline test over the catalog."""
    import math

    import numpy as np

    from app.medini.analysis.doctrine_validator import _norm_sf, open_catalog

    con = open_catalog()
    hc = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in _MARAKA_GRAHAS)
    lc = ", ".join(f"c.{g.lower()}_lon AS {g.lower()}_lon" for g in _MARAKA_GRAHAS)
    rows = con.execute(
        f"""SELECT c.asc_sign, {hc}, {lc}, t.transit_lon
            FROM events e JOIN charts c ON e.person_id=c.person_id
            JOIN event_transits t ON e.event_id=t.event_id AND t.transit_planet='Saturn'
            WHERE e.event_class='death_cause_unspecified'
              AND e.event_date_precision='day' AND c.asc_sign IS NOT NULL"""
    ).fetchall()
    con.close()

    nc = len(_MARAKA_GRAHAS)
    grid = np.arange(0, 360, 0.25)

    def frac(points: list[float]) -> float:
        cov = np.zeros(len(grid), bool)
        for p in points:
            cov |= np.minimum(np.abs(grid - p), 360 - np.abs(grid - p)) < orb
        return float(cov.mean())

    obs = n = 0
    exp = 0.0
    for r in rows:
        asc = int(r[0]); houses = r[1:1 + nc]; lons = r[1 + nc:1 + 2 * nc]; sat = r[-1]
        if sat is None:
            continue
        gh = {g: (int(h) if h is not None else 0) for g, h in zip(_MARAKA_GRAHAS, houses)}
        natal = {g: l for g, l in zip(_MARAKA_GRAHAS, lons)}
        pts = death_trigger_points(asc, gh, natal)
        if not pts:
            continue
        n += 1
        exp += frac(pts)
        if any(_ang_sep(float(sat), p) < orb for p in pts):
            obs += 1
    er = exp / n; orr = obs / n
    se = math.sqrt(n * er * (1 - er)); z = (obs - exp) / se; p = 2 * _norm_sf(abs(z))
    return {"orb": orb, "n": n, "observed": round(orr, 4), "expected": round(er, 4),
            "lift": round(orr / er, 3), "z": round(z, 2), "p_value": round(p, 5)}


if __name__ == "__main__":
    for o in (3.0, 5.0):
        print(_validate(o))
