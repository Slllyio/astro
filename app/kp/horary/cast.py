"""Erect a KP horary chart from a number between 1 and 249 (KPR6, Example 1).

Krishnamurti's procedure (KPR6 pp.104-108):

1. The number fixes the Ascendant at the START of that sub (the 249-division
   table, :func:`app.kp.subs.horary_number_longitude`).
2. Add the Krishnamurti ayanamsa of the day of judgment to get the sayana
   Ascendant.
3. Find the other cusps for the LATITUDE of the place where the astrologer
   judges (not where the querent is), from a table of houses; he names
   Raphael's (Placidus). The engine computes the same Placidus cusps exactly:
   it finds the sidereal time (ARMC) at which that sayana Ascendant rises at
   that latitude and takes the Placidus cusps for it. Ruling RH1.
4. Deduct the ayanamsa again; planets are for the moment judgment starts.

Usage:
    from app.kp.chart import Birth
    from app.kp.horary.cast import cast_horary
    ch = cast_horary(43, Birth(1969, 12, 11, 10, 0, tz=5.5, lat=13.07, lon=80.27))
"""

from __future__ import annotations

from dataclasses import replace
from typing import Final

import swisseph as swe

from app.empirical.western.houses import house_of
from app.kp.chart import Birth, KPChart, KPUndefined, Point, cast, kp_ayanamsa
from app.kp.subs import horary_number_longitude, lords_of

MAX_NUMBER: Final = 249


def _asc_for_armc(armc: float, lat: float, eps: float) -> float:
    return swe.houses_armc(armc, lat, eps, b"P")[1][0]


def armc_for_ascendant(asc_tropical: float, lat: float, eps: float) -> float:
    """ARMC (degrees) at which ``asc_tropical`` rises at ``lat`` (bisection on the monotone map)."""
    def diff(a: float) -> float:
        return ((_asc_for_armc(a, lat, eps) - asc_tropical + 180.0) % 360.0) - 180.0
    # The Ascendant increases monotonically with ARMC; scan for the sign change then bisect.
    step = 5.0
    a0 = 0.0
    d0 = diff(a0)
    for k in range(1, 73):
        a1 = k * step
        d1 = diff(a1 % 360.0)
        if d0 <= 0.0 < d1 and d1 - d0 < 90.0:
            lo, hi = a0, a1
            for _ in range(60):
                mid = (lo + hi) / 2
                if diff(mid % 360.0) > 0:
                    hi = mid
                else:
                    lo = mid
            return ((lo + hi) / 2) % 360.0
        a0, d0 = a1, d1
    raise KPUndefined(f"no ARMC raises {asc_tropical:.4f} at latitude {lat}")


def cast_horary(number: int, judged: Birth, *, node_mode: str = "mean") -> KPChart:
    """Horary chart for ``number`` judged at ``judged`` (moment and place of judgment).

    Raises:
      ValueError: number outside 1..249 (Krishnamurti: beyond 249 the matter
        "never materialised"; he never divided by 249, KPR6 p.110).
      KPUndefined: Placidus undefined at that latitude.
    """
    if not 1 <= number <= MAX_NUMBER:
        raise ValueError("horary number must be between 1 and 249")
    natal_style = cast(judged, node_mode=node_mode)  # planets at the moment of judgment
    jd = natal_style.jd_ut
    ayan = kp_ayanamsa(jd)
    asc_sid = float(horary_number_longitude(number))
    asc_trop = (asc_sid + ayan) % 360.0
    eps = swe.calc_ut(jd, swe.ECL_NUT)[0][0]  # true obliquity
    armc = armc_for_ascendant(asc_trop, judged.lat, eps)
    trop = swe.houses_armc(armc, judged.lat, eps, b"P")[0][:12]
    trop = (asc_trop,) + tuple(trop[1:])  # cusp 1 exactly at the number's sub
    sid = tuple((c - ayan) % 360.0 for c in trop)
    sid = (asc_sid,) + sid[1:]
    cusps = tuple(Point(f"Cusp {i + 1}", lon, lords_of(lon), i + 1) for i, lon in enumerate(sid))
    planets = {n: replace(p, bhava=house_of(p.longitude, sid)) for n, p in natal_style.planets.items()}
    return replace(natal_style, cusps=cusps, planets=planets, sayana_cusps=tuple(trop))


__all__ = ["MAX_NUMBER", "armc_for_ascendant", "cast_horary"]
