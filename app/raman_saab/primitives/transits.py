"""Gochara (transits) — Raman's timing layer on top of the natal chart.

Raman judged a transit by THREE things together: (1) the transiting planet's house FROM THE NATAL
MOON (classical Gochara benefic/malefic houses), (2) the Ashtakavarga support — the bindus the
planet earns in the transited sign in its OWN Bhinnashtakavarga (4+ is supportive, fewer poor), and
(3) the slow planets (Saturn, Jupiter, Rahu/Ketu) for the major turns, including Saturn's Sade-Sati
(transit of the 12th/1st/2nd from the Moon).

Usage:
    from app.raman_saab.primitives import transits as tr
    rows = tr.gochara(natal_chart, 2026, 6, 28)        # current transits vs the nativity
    sade = tr.sade_sati(natal_chart, 2026, 6, 28)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.primitives import ashtakavarga as av

#: Houses FROM THE MOON in which a transiting planet gives benefic results (classical Gochara).
_GOCHARA_GOOD: Final[dict[str, frozenset[int]]] = {
    "Sun": frozenset({3, 6, 10, 11}),
    "Moon": frozenset({1, 3, 6, 7, 10, 11}),
    "Mars": frozenset({3, 6, 11}),
    "Mercury": frozenset({2, 4, 6, 8, 10, 11}),
    "Jupiter": frozenset({2, 5, 7, 9, 11}),
    "Venus": frozenset({1, 2, 3, 4, 5, 8, 9, 11, 12}),
    "Saturn": frozenset({3, 6, 11}),
    "Rahu": frozenset({3, 6, 11}),
    "Ketu": frozenset({3, 6, 11}),
}

#: The slow/significant transit planets Raman watches for major events.
SIGNIFICANT: Final[tuple[str, ...]] = ("Jupiter", "Saturn", "Rahu", "Ketu", "Mars")


@dataclass(frozen=True)
class TransitRow:
    planet: str
    sign: int                 # transit sign (1..12)
    house_from_moon: int      # 1..12 from natal Moon (the Gochara frame)
    house_from_lagna: int     # 1..12 from natal Lagna
    gochara_good: bool        # benefic house from the Moon
    bav_bindus: int | None    # bindus in the transited sign in the planet's OWN ashtakavarga
    supported: bool | None    # bav_bindus >= 4 (Ashtakavarga support)


def transit_chart(year: int, month: int, day: int, *, ayanamsa: str = "lahiri") -> RamanChart:
    """Sidereal planet positions at noon UT on the given date (location-independent for signs)."""
    return cast_chart(BirthData(name="transit", year=year, month=month, day=day, hour=12,
                                minute=0, tz_offset=0.0, latitude=0.0, longitude=0.0),
                      ayanamsa=ayanamsa)


def gochara(natal: RamanChart, year: int, month: int, day: int, *,
            ayanamsa: str = "lahiri", planets: tuple[str, ...] = SIGNIFICANT) -> tuple[TransitRow, ...]:
    """Transit rows for `planets` on the date, judged from the natal Moon + natal Lagna + each
    planet's own Ashtakavarga support."""
    tc = transit_chart(year, month, day, ayanamsa=ayanamsa)
    moon = natal.planets.get("Moon")
    moon_sign = moon.sign if moon else natal.asc_sign
    rows: list[TransitRow] = []
    for planet in planets:
        p = tc.planets.get(planet)
        if p is None:
            continue
        ts = p.sign
        hfm = ((ts - moon_sign) % 12) + 1
        hfl = ((ts - natal.asc_sign) % 12) + 1
        bav = av.bhinnashtakavarga(natal, planet)[ts] if planet in av.PLANETS else None
        rows.append(TransitRow(
            planet=planet, sign=ts, house_from_moon=hfm, house_from_lagna=hfl,
            gochara_good=hfm in _GOCHARA_GOOD.get(planet, frozenset()),
            bav_bindus=bav, supported=None if bav is None else bav >= 4))
    return tuple(rows)


def sade_sati(natal: RamanChart, year: int, month: int, day: int, *,
              ayanamsa: str = "lahiri") -> str | None:
    """Saturn's Sade-Sati phase if active (transit of the 12th/1st/2nd from the natal Moon)."""
    tc = transit_chart(year, month, day, ayanamsa=ayanamsa)
    moon = natal.planets.get("Moon")
    sat = tc.planets.get("Saturn")
    if moon is None or sat is None:
        return None
    h = ((sat.sign - moon.sign) % 12) + 1
    return {12: "Sade-Sati: rising (12th from Moon)", 1: "Sade-Sati: peak (over the Moon)",
            2: "Sade-Sati: setting (2nd from Moon)"}.get(h)
