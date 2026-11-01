"""Timing by ruling planets: when will the matter happen? (KPR6 pp.123-131).

Krishnamurti's procedure, as he works it in Reader 6:

1. Take the ruling planets (RPs) at the moment of judgment (KPR6-RP): day
   lord, Moon's star and sign lords, Ascendant's sign and star lords; a node
   in a sign owned by an RP counts too.
2. Reject RPs deposited in the star of a retrograde planet (KPR6-RP-RETRO).
3. The fruitful planets are the RPs that are also significators of the
   matter's houses (KPR6-RP-COMMON, his trunk-call case).
4. Move a body to the next zodiac position governed by the fruitful planets:
   the Ascendant for minutes or hours, the Moon for days within a month, the
   Sun for months, Jupiter for years (KPR6-RP-BODY).

Which position? Krishnamurti chooses by judgment. Ruling RH3 states one
deterministic rule that reproduces all three of his printed answers (trunk
call, servant, friend's arrival): the first position whose sign, star and
sub lords are all fruitful and as many DIFFERENT planets as possible (three,
or all of them if fewer than three). The sub-sub (RH4) is the first fruitful
planet not yet used; if every fruitful planet is used, the lord of the
Ascendant at judgment. Both are reconstructions from his cases and say so.

Usage:
    from app.kp.chart import Birth
    from app.kp.horary.timing import fruitful_planets, next_rising
    t = next_rising(Birth(1969, 9, 21, 9, 0, tz=5.5, lat=7.47, lon=80.62),
                    ("Sun", "Jupiter", "Venus"), lagna_lord="Venus")
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Final, Iterable

import swisseph as swe

from app.kp.chart import Birth, KPChart, kp_ayanamsa
from app.kp.ruling import ruling_planets
from app.kp.significators import houses_signified, planet_significations
from app.kp.subs import DASA_ORDER, DASA_YEARS, divisions

BODIES: Final[dict[str, int | None]] = {"lagna": None, "Moon": swe.MOON, "Sun": swe.SUN, "Jupiter": swe.JUPITER}
#: Scan step (days) and horizon (days) per body.
_SCAN: Final[dict[str, tuple[float, float]]] = {
    "lagna": (1 / 1440, 1.0), "Moon": (1 / 96, 31.0), "Sun": (0.25, 370.0), "Jupiter": (1.0, 4400.0),
}


def usable_ruling_planets(chart: KPChart) -> tuple[str, ...]:
    """RPs (with node agents) minus those in the star of a retrograde planet (KPR6-RP-RETRO)."""
    rp = ruling_planets(chart)
    out = []
    for p in (*rp.planets, *rp.node_agents):
        star_lord = chart.planets[p].star_lord
        if chart.planets[star_lord].retrograde and star_lord not in ("Rahu", "Ketu"):
            continue
        out.append(p)
    return tuple(dict.fromkeys(out))


def fruitful_planets(chart: KPChart, houses: Iterable[int]) -> tuple[str, ...]:
    """Usable RPs that also signify at least one of ``houses`` (KPR6-RP-COMMON)."""
    hs = frozenset(houses)
    sigs = planet_significations(chart)
    return tuple(p for p in usable_ruling_planets(chart) if houses_signified(chart, p, sigs) & hs)


def _subsubs(a: Fraction, b: Fraction, sub_lord: str) -> list[tuple[Fraction, Fraction, str]]:
    i = DASA_ORDER.index(sub_lord)
    out, x = [], a
    for k in range(9):
        lord = DASA_ORDER[(i + k) % 9]
        y = x + (b - a) * DASA_YEARS[lord] / 120
        out.append((x, y, lord))
        x = y
    return out


@dataclass(frozen=True, slots=True)
class Position:
    """A zodiac position (sidereal) governed by fruitful planets."""

    start: float
    end: float
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str | None
    sub_sub_start: float | None


def positions(fruitful: tuple[str, ...], *, lagna_lord: str | None = None) -> list[Position]:
    """Every sub (in zodiac order from Aries 0) meeting ruling RH3, with its RH4 sub-sub."""
    fr = set(fruitful)
    need = min(3, len(fr))
    out = []
    for d in divisions():
        lords = (d.sign_lord, d.star_lord, d.sub_lord)
        if not set(lords) <= fr or len(set(lords)) < need:
            continue
        # the sub-sub table runs over the whole sub; a division may be half a sign-split sub
        full = next((a, b) for a, b, s, u in _subs_cached() if a <= d.start < b)
        unused = [p for p in fruitful if p not in lords]
        pref = unused[0] if unused else (lagna_lord if lagna_lord in fr else fruitful[0])
        ss = next(((x, y, l) for x, y, l in _subsubs(full[0], full[1], d.sub_lord)
                   if l == pref and y > d.start and x < d.end), None)
        out.append(Position(float(d.start), float(d.end), *lords,
                            ss[2] if ss else None, float(max(ss[0], d.start)) if ss else None))
    return out


def _subs_cached():
    from app.kp.subs import subs
    return subs()


def _body_lon(body: str, jd: float, lat: float, lon: float) -> float:
    ayan = kp_ayanamsa(jd)
    if body == "lagna":
        trop = swe.houses_ex(jd, lat, lon, b"P")[1][0]
    else:
        trop = swe.calc_ut(jd, BODIES[body], swe.FLG_SWIEPH)[0][0]
    return (trop - ayan) % 360.0


def _in(x: float, a: float, b: float) -> bool:
    return a <= x < b


@dataclass(frozen=True, slots=True)
class Rising:
    """When the body reaches a fruitful position."""

    body: str
    position: Position
    jd_ut: float
    target: float

    def local(self, tz: float) -> str:
        y, m, d, h = swe.revjul(self.jd_ut + tz / 24, swe.GREG_CAL)
        mins = round(h * 60)
        return f"{y:04d}-{m:02d}-{d:02d} {mins // 60:02d}:{mins % 60:02d}"


def next_rising(judged: Birth, fruitful: tuple[str, ...], *, body: str = "lagna",
                lagna_lord: str | None = None, use_sub_sub: bool = True) -> Rising | None:
    """First moment after ``judged`` that ``body`` enters a fruitful position (RH3/RH4).

    The target is the start of the RH4 sub-sub when ``use_sub_sub`` and it
    exists, otherwise the start of the sub. ``None`` if nothing is reached
    inside the body's horizon (a day for the Ascendant, a month for the Moon,
    a year for the Sun, about twelve years for Jupiter).
    """
    if body not in BODIES:
        raise ValueError(f"body must be one of {sorted(BODIES)}")
    pos = positions(fruitful, lagna_lord=lagna_lord)
    if not pos:
        return None
    targets = [(p, p.sub_sub_start if (use_sub_sub and p.sub_sub_start is not None) else p.start) for p in pos]
    step, horizon = _SCAN[body]
    jd0 = judged.jd_ut()
    prev = _body_lon(body, jd0, judged.lat, judged.lon)
    jd = jd0
    while jd < jd0 + horizon:
        nxt = jd + step
        cur = _body_lon(body, nxt, judged.lat, judged.lon)
        for p, t in targets:
            if _crossed(prev, cur, t):
                lo, hi = jd, nxt
                for _ in range(40):
                    mid = (lo + hi) / 2
                    if _crossed(prev, _body_lon(body, mid, judged.lat, judged.lon), t):
                        hi = mid
                    else:
                        lo = mid
                return Rising(body, p, hi, t)
        jd, prev = nxt, cur
    return None


def _crossed(a: float, b: float, t: float) -> bool:
    """Did a forward move from ``a`` to ``b`` (short arc, direct) pass longitude ``t``?"""
    d = (b - a) % 360.0
    if d > 180.0:  # retrograde step: a direct crossing did not happen
        return False
    return 0.0 < (t - a) % 360.0 <= d


__all__ = ["BODIES", "usable_ruling_planets", "fruitful_planets", "Position", "positions",
           "Rising", "next_rising"]
