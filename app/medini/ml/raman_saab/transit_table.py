"""Precomputed sidereal sign-ingress tables for slow movers (Leg-2 backbone).

The Triple-Lock gochara leg needs Saturn's and Jupiter's transit signs at
~1000 shuffled death-ages × N persons ≈ millions of moments. Per-call
``swe.calc_ut`` would work but is slow and unvectorizable; instead we build a
sorted ingress table per planet over 1850–2035 once (~1 s), and answer
``sign_at(planet, jds)`` with a numpy ``searchsorted``.

Build: sample sidereal longitude on a 10-day grid; wherever the sign changes
between adjacent samples, bisect the boundary to ±0.5 day. Retrograde
re-entries produce multiple ingresses into the same sign — handled naturally
(each crossing is its own table row). A station "grazing" a boundary and
returning between two grid samples (< 10 days in the next sign) would be
missed; astronomically rare for Saturn/Jupiter and guarded by the
table-vs-direct property test in ``tests/test_transit_table.py``.

Ephemeris: Lahiri sidereal, ``FLG_MOSEPH`` (offline; consistent with the rest
of run 3). Rahu (TRUE_NODE; Ketu = Rahu+180) is included for future runs at
negligible cost, though the frozen run-3 trigger menu doesn't use it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

import numpy as np
import swisseph as swe

_GRID_DAYS: Final = 10.0
_BISECT_TOL_DAYS: Final = 0.5
_START = (1850, 1, 1)
_END = (2035, 1, 1)

_PLANET_IDS: Final[Mapping[str, int]] = {
    "Saturn": swe.SATURN,
    "Jupiter": swe.JUPITER,
    "Rahu": swe.TRUE_NODE,
    # Run 4: Mars, for the Mars-Saturn hard-contact transit trigger. Mars is
    # the fastest body here (~45 d/sign); the 10-day grid + bisection still
    # brackets every ingress except a station exactly at a sign boundary
    # (double-cross inside one grid cell) — rare enough for a confirmatory
    # multiplier, and pinned by the property test against direct ephemeris.
    "Mars": swe.MARS,
}

_LAHIRI_SET = False


def _ensure_lahiri() -> None:
    global _LAHIRI_SET
    if not _LAHIRI_SET:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        _LAHIRI_SET = True


def sidereal_lon(jd: float, planet_id: int,
                 sid_mode: int | None = None) -> float:
    """Sidereal longitude; default Lahiri (run-3 semantics preserved).

    Run 5 passes ``sid_mode=swe.SIDM_RAMAN`` for Raman-frame tables. The
    mode is set per call and restored to Lahiri afterwards so the run-3
    one-shot global stays truthful for existing callers.
    """
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
    if sid_mode is None:
        _ensure_lahiri()
        return float(swe.calc_ut(jd, planet_id, flags)[0][0]) % 360.0
    swe.set_sid_mode(sid_mode)
    try:
        return float(swe.calc_ut(jd, planet_id, flags)[0][0]) % 360.0
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)


def _sign(lon: float) -> int:
    return int(lon // 30.0) + 1


def _bisect_ingress(planet_id: int, jd_lo: float, jd_hi: float,
                    sign_lo: int, sid_mode: int | None = None) -> float:
    """JD where the sign changes away from sign_lo, to ±_BISECT_TOL_DAYS."""
    while jd_hi - jd_lo > _BISECT_TOL_DAYS:
        mid = (jd_lo + jd_hi) / 2.0
        if _sign(sidereal_lon(mid, planet_id, sid_mode)) == sign_lo:
            jd_lo = mid
        else:
            jd_hi = mid
    return jd_hi


@dataclass(frozen=True)
class IngressTable:
    """Sorted ingress JDs + the sign in force from each ingress onward."""
    planet: str
    ingress_jd: np.ndarray   # (k,) sorted float64; [0] = table start
    sign: np.ndarray         # (k,) int8, sign in force from ingress_jd[i]

    def sign_at(self, jds: np.ndarray) -> np.ndarray:
        idx = np.searchsorted(self.ingress_jd, jds, side="right") - 1
        idx = np.clip(idx, 0, len(self.sign) - 1)
        return self.sign[idx]


def build_table(planet: str, sid_mode: int | None = None) -> IngressTable:
    pid = _PLANET_IDS[planet]
    jd0 = swe.julday(*_START, 0.0, swe.GREG_CAL)
    jd1 = swe.julday(*_END, 0.0, swe.GREG_CAL)
    grid = np.arange(jd0, jd1 + _GRID_DAYS, _GRID_DAYS)
    signs = np.array([_sign(sidereal_lon(j, pid, sid_mode)) for j in grid],
                     dtype=np.int8)
    ingress_jd = [float(grid[0])]
    ingress_sign = [int(signs[0])]
    for i in range(1, len(grid)):
        if signs[i] != signs[i - 1]:
            jd_cross = _bisect_ingress(pid, float(grid[i - 1]), float(grid[i]),
                                       int(signs[i - 1]), sid_mode)
            ingress_jd.append(jd_cross)
            ingress_sign.append(int(signs[i]))
    return IngressTable(
        planet=planet,
        ingress_jd=np.array(ingress_jd, dtype=np.float64),
        sign=np.array(ingress_sign, dtype=np.int8),
    )


_CACHE: dict[tuple[str, int | None], IngressTable] = {}


def get_table(planet: str, sid_mode: int | None = None) -> IngressTable:
    """Process-cached ingress table (build cost ~0.5 s per planet).

    ``sid_mode=None`` keeps run-3 Lahiri semantics; pass ``swe.SIDM_RAMAN``
    for Raman-frame tables (cache is keyed by (planet, mode)).
    """
    key = (planet, sid_mode)
    if key not in _CACHE:
        _CACHE[key] = build_table(planet, sid_mode)
    return _CACHE[key]
