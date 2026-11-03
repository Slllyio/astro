"""KP ruling planets at a moment (birth or query).

Krishnamurti lists five (KPR3-RP): the day lord, the Moon's star lord, the
Moon's sign lord, the Ascendant's sign lord, and the star lord of the rising
degree. The same book lists only the first four at KPR3-RP-FOUR, and his
worked example there also counts a planet aspecting the Moon. The engine
returns the five-item list (ruling R9) and, separately, the nodes that stand
for any of them (``node_agents``), so a reader can see both without the
engine merging them silently.

Day lord: the weekday runs sunrise to sunrise (ruling R10: stated in the KP
E-zine, not in Reader 3). A moment before local sunrise belongs to the
previous weekday.

Usage:
    from app.kp.ruling import ruling_planets
    rp = ruling_planets(chart)
    rp.planets       # ('Jupiter', 'Rahu', 'Venus', ...)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import swisseph as swe

from app.kp.chart import NODES, KPChart
from app.kp.significators import node_represents

#: swisseph day_of_week: 0 = Monday.
WEEKDAY_LORDS: Final[tuple[str, ...]] = (
    "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun",
)


@dataclass(frozen=True, slots=True)
class RulingPlanets:
    """The five ruling planets, in Krishnamurti's order, plus node agents."""

    day_lord: str
    moon_star_lord: str
    moon_sign_lord: str
    lagna_sign_lord: str
    lagna_star_lord: str
    node_agents: tuple[str, ...]
    sunrise_jd_ut: float | None

    @property
    def planets(self) -> tuple[str, ...]:
        """Distinct ruling planets in Krishnamurti's order."""
        seq = (self.day_lord, self.moon_star_lord, self.moon_sign_lord,
               self.lagna_sign_lord, self.lagna_star_lord)
        return tuple(dict.fromkeys(seq))


def _sunrise_ut(jd_ut: float, lat: float, lon: float) -> float | None:
    """Most recent local sunrise at or before ``jd_ut`` (disc centre, no refraction tweaks)."""
    start = jd_ut - 1.0
    try:
        res, tret = swe.rise_trans(start, swe.SUN, swe.CALC_RISE, (lon, lat, 0.0))
    except swe.Error:  # pragma: no cover - polar day/night
        return None
    if res != 0:
        return None
    rise = tret[0]
    while True:
        res, tret = swe.rise_trans(rise + 0.01, swe.SUN, swe.CALC_RISE, (lon, lat, 0.0))
        if res != 0 or tret[0] > jd_ut:
            return rise
        rise = tret[0]


def ruling_planets(chart: KPChart) -> RulingPlanets:
    """Ruling planets for the chart's moment and place."""
    b = chart.birth
    rise = _sunrise_ut(chart.jd_ut, b.lat, b.lon)
    # Weekday of the civil date on which the governing sunrise fell (local time).
    ref = rise if rise is not None else chart.jd_ut
    day_lord = WEEKDAY_LORDS[swe.day_of_week(ref + b.tz / 24 + 0.5) % 7]
    moon = chart.planets["Moon"]
    asc = chart.cusp(1)
    core = (day_lord, moon.star_lord, moon.sign_lord, asc.sign_lord, asc.star_lord)
    agents = tuple(
        n for n in sorted(NODES)
        if n not in core and any(r in core for r in node_represents(chart, n))
    )
    return RulingPlanets(*core, node_agents=agents, sunrise_jd_ut=rise)


__all__ = ["WEEKDAY_LORDS", "RulingPlanets", "ruling_planets"]
