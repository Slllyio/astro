"""Birth-time correction by ruling planets (KPR6 pp.139-143).

Krishnamurti: "The ruling planets at the time of judgment will rule (a) the
sign, star sub and sub sub of the position of lagna" (KPR6-RECTIFY). Given a
stated birth window, the engine lists every Ascendant position inside the
window whose sign, star and sub lords are ruling planets of the moment the
question is judged, as ruling RH3 states (different planets as far as
possible), with the RH4 sub-sub, and the clock time it rises.

He picks one candidate by judgment when several remain (in his first case he
used a number the native gave and rejected two RPs as "weaker"); the engine
lists them all and never picks. In his second case the rule leaves one
candidate, Virgo 23°10' (KPR6-RECT-CASE2), which the tests pin.

It uses the moment of judgment, never the native's life events. The
event-based KP rectifier (unmerged PR #30) was not carried forward: fitting a
birth time to dated events and then reading those periods back is circular
(docs/raman_saab/BIRTH_TIME_POLICY.md). Its output is a candidate list for the
user, not a validated birth time, and nothing in the engine adopts it.

Usage:
    from app.kp.chart import Birth
    from app.kp.horary.rectify import rp_candidates
    c = rp_candidates(Birth(1948, 11, 13, 3, 0, tz=5.5, lat=17.73, lon=83.38), 90,
                      judged=Birth(1967, 12, 24, 18, 45, tz=5.5, lat=13.08, lon=80.27))
"""

from __future__ import annotations

from dataclasses import dataclass

import swisseph as swe

from app.kp.chart import Birth, cast
from app.kp.horary.timing import Position, _body_lon, _crossed, positions, usable_ruling_planets


@dataclass(frozen=True, slots=True)
class Candidate:
    position: Position
    longitude: float
    jd_ut: float
    local_time: str


def rp_candidates(start: Birth, window_minutes: float, *, judged: Birth,
                  ruling: tuple[str, ...] | None = None) -> tuple[Candidate, ...]:
    """Ascendant positions governed by the judgment-moment RPs that rise in ``[start, start+window]``.

    ``ruling`` overrides the computed usable RPs (to reproduce a printed case).
    """
    jchart = cast(judged)
    rps = ruling or usable_ruling_planets(jchart)
    pos = positions(tuple(rps), lagna_lord=jchart.cusp(1).sign_lord)
    jd0 = start.jd_ut()
    jd1 = jd0 + window_minutes / 1440
    out: list[Candidate] = []
    step = 1 / 1440
    jd, prev = jd0, _body_lon("lagna", jd0, start.lat, start.lon)
    while jd < jd1:
        nxt = min(jd + step, jd1)
        cur = _body_lon("lagna", nxt, start.lat, start.lon)
        for p in pos:
            t = p.sub_sub_start if p.sub_sub_start is not None else p.start
            if _crossed(prev, cur, t):
                lo, hi = jd, nxt
                for _ in range(40):
                    mid = (lo + hi) / 2
                    if _crossed(prev, _body_lon("lagna", mid, start.lat, start.lon), t):
                        hi = mid
                    else:
                        lo = mid
                y, mo, d, h = swe.revjul(hi + start.tz / 24, swe.GREG_CAL)
                s = round(h * 3600)
                out.append(Candidate(p, t, hi, f"{y:04d}-{mo:02d}-{d:02d} {s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"))
        jd, prev = nxt, cur
    return tuple(out)


__all__ = ["Candidate", "rp_candidates"]
