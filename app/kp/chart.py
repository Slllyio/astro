"""Cast a KP chart: Krishnamurti ayanamsa, Placidus cusps, four lords per point.

Method as printed by Krishnamurti: erect the chart with Placidus ("Raphael's
Table of Houses", KPR3-RAPHAEL), then deduct the Krishnamurti ayanamsa from
the sayana cusps and planets (KPR3-SAYANA-MINUS). Swiss Ephemeris'
``SIDM_KRISHNAMURTI`` reproduces his printed values (22°41' vs 22°40' for
July 1922; 23°20' vs 23°20' for 1969), see ``tests/kp/test_chart.py``.

Global state: swisseph's sidereal mode is process-global. This module only
touches it inside :func:`kp_ayanamsa`, and restores the repo default
(Lahiri, CLAUDE.md locked convention) before returning, so a KP cast never
leaks into a Raman or Parashari cast.

Usage:
    from app.kp.chart import Birth, cast
    chart = cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))
    chart.cusps[6].sub_lord            # sub-lord of the 7th cusp
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from typing import Final

import swisseph as swe

from app.empirical.western.houses import house_cusps, house_of
from app.kp.subs import SIGN_LORDS, Lords, lords_of

logger = logging.getLogger(__name__)

PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_SWE_IDS: Final[dict[str, int]] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}
NODES: Final[frozenset[str]] = frozenset({"Rahu", "Ketu"})


class KPUndefined(ValueError):
    """Placidus cusps do not exist at this latitude (inside the polar circles)."""


@dataclass(frozen=True, slots=True)
class Birth:
    """Birth (or query) data in local civil time.

    ``uncertainty_minutes`` is the ± window the recorded time is trusted to.
    It does not change the cast; :mod:`app.kp.judgment` uses it to report
    whether a verdict survives the whole window. A rectified time from the
    rectification work plugs in here with its own (smaller) window.
    """

    year: int
    month: int
    day: int
    hour: int
    minute: int
    tz: float
    lat: float
    lon: float
    second: float = 0.0
    uncertainty_minutes: float = 0.0
    label: str = ""

    def jd_ut(self) -> float:
        """Julian Day (UT) of this moment."""
        local = self.hour + self.minute / 60 + self.second / 3600
        return swe.julday(self.year, self.month, self.day, local - self.tz, swe.GREG_CAL)

    def shifted(self, minutes: float) -> "Birth":
        """The same birth moved by ``minutes`` (calendar handled via JD)."""
        jd = self.jd_ut() + minutes / 1440 + self.tz / 24
        y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
        total = round(h * 3600, 3)
        hh, rem = divmod(total, 3600)
        mm, ss = divmod(rem, 60)
        return replace(self, year=y, month=m, day=d, hour=int(hh), minute=int(mm), second=ss)


@dataclass(frozen=True, slots=True)
class Point:
    """A planet or cusp with its KP lords and Placidus bhava."""

    name: str
    longitude: float
    lords: Lords
    bhava: int
    retrograde: bool = False

    @property
    def sign_lord(self) -> str:
        return self.lords.sign_lord

    @property
    def star_lord(self) -> str:
        return self.lords.star_lord

    @property
    def sub_lord(self) -> str:
        return self.lords.sub_lord

    @property
    def sub_sub_lord(self) -> str:
        return self.lords.sub_sub_lord


@dataclass(frozen=True, slots=True)
class KPChart:
    """A cast KP chart. ``cusps[0]`` is the Ascendant (cusp 1)."""

    birth: Birth
    jd_ut: float
    ayanamsa: float
    node_mode: str
    planets: dict[str, Point]
    cusps: tuple[Point, ...]
    sayana_cusps: tuple[float, ...] = field(repr=False)

    def cusp(self, house: int) -> Point:
        """Cusp of house ``house`` (1..12)."""
        return self.cusps[house - 1]

    def house_lord(self, house: int) -> str:
        """Lord of the sign on the cusp (KPR3-CUSP-LORD)."""
        return self.cusp(house).sign_lord

    def occupants(self, house: int) -> tuple[str, ...]:
        """Planets whose Placidus bhava is ``house`` (ruling R5)."""
        return tuple(p for p, pt in self.planets.items() if pt.bhava == house)

    def owned_houses(self, planet: str) -> tuple[int, ...]:
        """Houses whose cusp falls in a sign owned by ``planet`` (nodes own none)."""
        return tuple(h for h in range(1, 13) if self.house_lord(h) == planet)


def kp_ayanamsa(jd_ut: float) -> float:
    """Krishnamurti ayanamsa (true, with nutation) at ``jd_ut``.

    Sets swisseph's global mode to Krishnamurti only for this call and restores
    Lahiri, the repo default, afterwards.
    """
    try:
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        return swe.get_ayanamsa_ex_ut(jd_ut, swe.FLG_SWIEPH)[1]
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)


def cast(birth: Birth, *, node_mode: str = "mean") -> KPChart:
    """Cast the KP chart for ``birth``.

    Args:
      birth: Birth or query moment and place.
      node_mode: ``"mean"`` (default, ruling R4) or ``"true"`` lunar node.

    Raises:
      KPUndefined: Placidus is undefined at this latitude. No substitute
        house system is used.
    """
    if node_mode not in ("mean", "true"):
        raise ValueError("node_mode must be 'mean' or 'true'")
    jd = birth.jd_ut()
    ayan = kp_ayanamsa(jd)
    hc = house_cusps(jd, birth.lat, birth.lon, "placidus")
    if hc is None:
        raise KPUndefined(f"Placidus undefined at latitude {birth.lat}")
    sid_cusps = tuple((c - ayan) % 360.0 for c in hc.cusps)

    raw: dict[str, tuple[float, bool]] = {}
    for name, pid in _SWE_IDS.items():
        xx = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
        raw[name] = ((xx[0] - ayan) % 360.0, xx[3] < 0)
    node_id = swe.MEAN_NODE if node_mode == "mean" else swe.TRUE_NODE
    rahu = (swe.calc_ut(jd, node_id, swe.FLG_SWIEPH)[0][0] - ayan) % 360.0
    raw["Rahu"] = (rahu, True)
    raw["Ketu"] = ((rahu + 180.0) % 360.0, True)

    planets = {
        name: Point(name, lon, lords_of(lon), house_of(lon, sid_cusps), retro)
        for name, (lon, retro) in ((p, raw[p]) for p in PLANETS)
    }
    cusps = tuple(
        Point(f"Cusp {i + 1}", lon, lords_of(lon), i + 1) for i, lon in enumerate(sid_cusps)
    )
    return KPChart(birth, jd, ayan, node_mode, planets, cusps, hc.cusps)


def sign_index(longitude: float) -> int:
    """0-based sign index of a sidereal longitude."""
    return int((longitude % 360.0) // 30)


__all__ = [
    "PLANETS", "NODES", "SIGN_LORDS", "Birth", "Point", "KPChart", "KPUndefined",
    "kp_ayanamsa", "cast", "sign_index",
]
