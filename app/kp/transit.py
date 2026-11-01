"""KP transits (Reader 5): what a transit brings, and where a running period fructifies.

Two cited rules (KPR5):

* **Reading a transit** (KPR5-SOURCE): a planet transiting a point gives
  - WHAT happens: the houses signified (in the natal chart) by the lord of the
    star it transits;
  - the SOURCE: the houses signified by the transiting planet itself;
  - WHETHER it materialises and is favourable: the houses signified by the
    lord of the sub it transits.
* **Sensitive points of a period** (KPR5-DBA-POINTS): when A dasa, B bhukti,
  C antara runs, the event comes when the Ascendant, the luminaries or the
  period lords transit a zodiac position whose sign, star and sub lords are
  A, B and C in some order. :func:`sensitive_points` lists those positions
  (the 249-division table), and :func:`transit_hits` finds when the Sun,
  the Moon or a period lord passes through them inside the period.

The Ascendant's transit is computed for wherever the native then lives
(KPR5-PLACE), so it is left to the caller (:func:`app.kp.horary.timing`).

Usage:
    from app.kp.chart import Birth, cast
    from app.kp.transit import read_transits, sensitive_points
    chart = cast(Birth(1924, 12, 23, 21, 0, tz=5.5, lat=18.65, lon=72.92))
    rows = read_transits(chart, jd_ut)
    sensitive_points(("Mars", "Saturn", "Mercury"))
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Final

import swisseph as swe

from app.kp.chart import KPChart, kp_ayanamsa
from app.kp.dasa import Period
from app.kp.significators import houses_signified, planet_significations
from app.kp.subs import Division, divisions, lords_of

_SWE: Final[dict[str, int]] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}


def transit_longitude(planet: str, jd_ut: float, node_mode: str = "mean") -> float:
    """Sidereal (Krishnamurti) longitude of a transiting body."""
    ayan = kp_ayanamsa(jd_ut)
    if planet in _SWE:
        trop = swe.calc_ut(jd_ut, _SWE[planet], swe.FLG_SWIEPH)[0][0]
    else:
        nid = swe.MEAN_NODE if node_mode == "mean" else swe.TRUE_NODE
        trop = swe.calc_ut(jd_ut, nid, swe.FLG_SWIEPH)[0][0]
        if planet == "Ketu":
            trop += 180.0
    return (trop - ayan) % 360.0


@dataclass(frozen=True, slots=True)
class TransitReading:
    """One transiting planet read against the natal chart (KPR5-SOURCE)."""

    planet: str
    longitude: float
    star_lord: str
    sub_lord: str
    source_houses: frozenset[int]
    what_houses: frozenset[int]
    whether_houses: frozenset[int]

    def explain(self) -> str:
        return (f"{self.planet} in the star of {self.star_lord}, sub of {self.sub_lord}: "
                f"what = houses {sorted(self.what_houses)} (star lord), "
                f"source = {sorted(self.source_houses)} ({self.planet}), "
                f"whether = {sorted(self.whether_houses)} (sub lord)")


def read_transits(chart: KPChart, jd_ut: float) -> tuple[TransitReading, ...]:
    """Read every transiting planet at ``jd_ut`` against ``chart`` (KPR5-SOURCE)."""
    sigs = planet_significations(chart)
    hs = {p: houses_signified(chart, p, sigs) for p in sigs}
    out = []
    for p in chart.planets:
        lon = transit_longitude(p, jd_ut, chart.node_mode)
        lo = lords_of(lon)
        out.append(TransitReading(p, lon, lo.star_lord, lo.sub_lord, hs[p], hs[lo.star_lord], hs[lo.sub_lord]))
    return tuple(out)


def sensitive_points(lords: tuple[str, ...]) -> tuple[Division, ...]:
    """Divisions whose (sign, star, sub) lords are the given three lords in any order (KPR5-DBA-POINTS).

    Repeats count: Venus dasa, Mars bhukti, Venus antara asks for one Mars and
    two Venus among the three lords.
    """
    if len(lords) != 3:
        raise ValueError("give the dasa, bhukti and antara lords")
    want = Counter(lords)
    return tuple(d for d in divisions() if Counter((d.sign_lord, d.star_lord, d.sub_lord)) == want)


@dataclass(frozen=True, slots=True)
class TransitHit:
    """A body inside a sensitive point of a running period."""

    body: str
    division: Division
    start_jd: float
    end_jd: float


def transit_hits(period: Period, *, bodies: tuple[str, ...] = ("Sun", "Moon"),
                 include_period_lords: bool = True, step_days: float = 0.05,
                 node_mode: str = "mean") -> tuple[TransitHit, ...]:
    """When ``bodies`` (and the period's own lords) transit the period's sensitive points.

    Only antara-level periods (three lords) are accepted. Returns contiguous
    intervals inside the period, in time order.
    """
    if len(period.lords) != 3:
        raise ValueError("transit_hits needs a dasa-bhukti-antara period")
    pts = sensitive_points(tuple(period.lords))
    if not pts:
        return ()
    who = list(bodies)
    if include_period_lords:
        who += [l for l in dict.fromkeys(period.lords) if l not in who]
    out: list[TransitHit] = []
    for b in who:
        cur: tuple[Division, float] | None = None
        jd = period.start_jd
        while jd < period.end_jd:
            lon = transit_longitude(b, jd, node_mode)
            inside = next((d for d in pts if float(d.start) <= lon < float(d.end)), None)
            if inside is not None and cur is None:
                cur = (inside, jd)
            elif cur is not None and inside is not cur[0]:
                out.append(TransitHit(b, cur[0], cur[1], jd))
                cur = (inside, jd) if inside is not None else None
            jd += step_days
        if cur is not None:
            out.append(TransitHit(b, cur[0], cur[1], period.end_jd))
    return tuple(sorted(out, key=lambda h: h.start_jd))


__all__ = ["transit_longitude", "TransitReading", "read_transits", "sensitive_points",
           "TransitHit", "transit_hits"]
