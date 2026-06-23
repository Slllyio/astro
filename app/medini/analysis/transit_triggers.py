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
# On a trigger-active day the death rate is ~1.13× baseline (validated lift).
TRANSIT_LIFT: float = 1.13

_PLANET_ID = {"Saturn": swe.SATURN, "Jupiter": swe.JUPITER, "Mars": swe.MARS}


def _ang_sep(a: float, b: float) -> float:
    """Smallest separation between two ecliptic longitudes (degrees, 0–180)."""
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def transit_lon(jd: float, planet: str = TRIGGER_PLANET) -> float:
    """Sidereal (Lahiri) longitude of a transiting planet at a Julian Day (exact)."""
    return float(calculate_d1_position(jd, _PLANET_ID[planet])["longitude"]) % 360.0


# Bucketed cache for the bulk fraction estimate (backtest scores ~9M epochs). The
# slow movers shift <0.2°/5d, far inside a multi-degree orb, so 5-day buckets are
# exact enough here. NOT used by the day-resolution bands (those call transit_lon).
_LON_BUCKET_DAYS: float = 5.0
_lon_cache: dict[tuple[int, str], float] = {}


def _transit_lon_cached(jd: float, planet: str) -> float:
    key = (int(jd / _LON_BUCKET_DAYS), planet)
    v = _lon_cache.get(key)
    if v is None:
        v = transit_lon(key[0] * _LON_BUCKET_DAYS, planet)
        _lon_cache[key] = v
    return v


def saturn_transit_lon(jd: float) -> float:
    """Sidereal (Lahiri) longitude of Saturn at a Julian Day (back-compat)."""
    return transit_lon(jd, "Saturn")


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
                 orb: float = DEFAULT_ORB_DEG, planet: str = TRIGGER_PLANET) -> bool:
    """Is the transiting `planet` within `orb` of any trigger point at this JD?"""
    if not trigger_points:
        return False
    lon = transit_lon(jd, planet)
    return any(_ang_sep(lon, p) < orb for p in trigger_points)


def trigger_active_fraction(
    start_jd: float, end_jd: float, trigger_points: list[float],
    planet: str = TRIGGER_PLANET, orb: float = DEFAULT_ORB_DEG,
    n_samples: int = 24,
) -> float:
    """Fraction of a window when `planet` is within `orb` of a trigger point.

    Estimated by evenly sampling `n_samples` epochs across [start_jd, end_jd] — cheap
    enough to call for every window in the backtest (vs the day-by-day
    `active_trigger_intervals` used for the human-facing bands)."""
    if not trigger_points or end_jd <= start_jd:
        return 0.0
    hits = 0
    for i in range(n_samples):
        jd = start_jd + (i + 0.5) * (end_jd - start_jd) / n_samples
        lon = _transit_lon_cached(jd, planet)
        if any(_ang_sep(lon, p) < orb for p in trigger_points):
            hits += 1
    return hits / n_samples


def transit_factor(
    start_jd: float, end_jd: float, trigger_points: list[float],
    planet: str = TRIGGER_PLANET, orb: float = DEFAULT_ORB_DEG,
    lift: float = TRANSIT_LIFT, n_samples: int = 24,
) -> float:
    """Between-window death-risk multiplier from the transit trigger: a window that is
    trigger-active for fraction f carries propensity (1-f)·1 + f·lift = 1 + (lift-1)·f."""
    f = trigger_active_fraction(start_jd, end_jd, trigger_points, planet, orb, n_samples)
    return 1.0 + (lift - 1.0) * f


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


def evaluate_date_sharpening(orb: float = DEFAULT_ORB_DEG, test_only: bool = True,
                             limit: int | None = None) -> dict:
    """Given the CORRECT dāśā window, does the Saturn-trigger narrow the death-DATE?

    For each day-precise death we compare two point estimates of the death date:
      A. the window midpoint (no transit info), and
      B. the midpoint of the window's nearest Saturn-trigger band
         (`active_trigger_intervals`), falling back to A when no band exists.
    Reports median |error| in days for each, the median days saved, and coverage (the
    fraction of deaths whose actual date lands inside a trigger band). Held-out by
    default (the same 25% person split as the backtest) so it can't be over-fit."""
    import statistics

    from app.medini.analysis.death_backtest import _in_test
    from app.medini.analysis.doctrine_validator import open_catalog

    con = open_catalog()
    hc = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in _MARAKA_GRAHAS)
    lc = ", ".join(f"c.{g.lower()}_lon AS {g.lower()}_lon" for g in _MARAKA_GRAHAS)
    rows = con.execute(
        f"""SELECT e.person_id, e.event_jd, w.start_jd, w.end_jd, c.asc_sign, {hc}, {lc}
            FROM events_with_dasha e
            JOIN events ev ON ev.event_id = e.event_id
            JOIN dasha_windows w ON w.person_id = e.person_id
                                AND w.md_seq = e.md_seq AND w.ad_seq = e.ad_seq
            JOIN charts c ON c.person_id = e.person_id
            WHERE e.event_class = 'death_cause_unspecified'
              AND ev.event_date_precision = 'day' AND c.asc_sign IS NOT NULL
              AND e.event_jd IS NOT NULL
            {f'LIMIT {int(limit)}' if limit else ''}"""
    ).fetchall()
    con.close()

    nc = len(_MARAKA_GRAHAS)
    err_window: list[float] = []
    err_trigger: list[float] = []
    err_w_inside: list[float] = []        # window-midpoint error, deaths inside a band
    err_t_inside: list[float] = []        # nearest-band-midpoint error, same deaths
    inside = n = 0
    for r in rows:
        pid, ejd, sjd, ejd_w, asc = r[0], float(r[1]), float(r[2]), float(r[3]), int(r[4])
        if test_only and not _in_test(pid, 0.25):
            continue
        houses = r[5:5 + nc]; lons = r[5 + nc:5 + 2 * nc]
        gh = {g: (int(h) if h is not None else 0) for g, h in zip(_MARAKA_GRAHAS, houses)}
        natal = {g: l for g, l in zip(_MARAKA_GRAHAS, lons)}
        pts = death_trigger_points(asc, gh, natal)
        bands = active_trigger_intervals(sjd, ejd_w, pts, orb) if pts else []
        n += 1
        e_w = abs(ejd - (sjd + ejd_w) / 2.0)
        err_window.append(e_w)
        if bands:
            mids = [(b.start_jd + b.end_jd) / 2.0 for b in bands]
            e_t = min(abs(ejd - m) for m in mids)
            err_trigger.append(e_t)
            if any(b.start_jd <= ejd <= b.end_jd for b in bands):
                inside += 1
                err_w_inside.append(e_w)
                err_t_inside.append(e_t)
        else:
            err_trigger.append(e_w)                              # no band → fall back to A

    def _med(x):
        return round(statistics.median(x), 1) if x else 0.0
    med_w, med_t = _med(err_window), _med(err_trigger)
    return {
        "n": n, "orb": orb, "test_only": test_only,
        "median_err_days_window_midpoint": med_w,
        "median_err_days_trigger_band": med_t,
        "median_days_saved": round(med_w - med_t, 1),
        "coverage_actual_in_band": round(inside / n, 4) if n else 0.0,
        # conditional on the trigger actually firing on the death (the ~7% it covers):
        "n_inside_band": inside,
        "median_err_inside_window_midpoint": _med(err_w_inside),
        "median_err_inside_trigger_band": _med(err_t_inside),
        "median_days_saved_when_inside": round(_med(err_w_inside) - _med(err_t_inside), 1),
    }


if __name__ == "__main__":
    print("=== transit-trigger corpus validation (lift on death days) ===")
    for o in (3.0, 5.0):
        print(_validate(o))
    print("\n=== sub-window date sharpening (held-out; correct window given) ===")
    print(evaluate_date_sharpening())
