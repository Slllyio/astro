"""Varga (divisional chart) lords for D2/D7/D12/D30.

Usage:
    from app.raman_saab.primitives import varga_lords as vl
    lord = vl.hora_lord_of(planet_lon)

These supply the varga lords that Saptavargaja-bala (Shadbala) needs
for D2, D7, D12, and D30.  D1/D3/D9 lords are already covered by
``dispositor.py``.  Pure functions — no ephemeris, no ``app/core``.
"""
from __future__ import annotations

from app.raman_saab.chart.constants import SIGN_LORDS


def _sign_deg(lon: float) -> tuple[int, float]:
    """Return (sign 1-12, degrees-within-sign 0-30) for a tropical/sidereal longitude."""
    lon %= 360.0
    return int(lon // 30) + 1, lon % 30.0


def hora_lord_of(lon: float) -> str:
    """D2 hora lord (Parashara).

    Odd sign: 1st half (0°–15°) → Sun; 2nd half → Moon.
    Even sign: reversed — 1st half → Moon; 2nd half → Sun.
    """
    sign, deg = _sign_deg(lon)
    first_half = deg < 15.0
    if sign % 2 == 1:                       # odd sign
        return "Sun" if first_half else "Moon"
    return "Moon" if first_half else "Sun"  # even sign


def saptamsa_lord_of(lon: float) -> str:
    """D7 saptamsa lord.

    Odd sign: count the 7 parts from the sign itself.
    Even sign: count from the 7th sign (sign + 6).
    Lord = SIGN_LORDS of the resulting sign.
    """
    sign, deg = _sign_deg(lon)
    part = int(deg * 7 / 30)               # 0..6
    start = sign if sign % 2 == 1 else ((sign - 1 + 6) % 12) + 1
    return SIGN_LORDS[((start - 1 + part) % 12) + 1]


def dwadasamsa_lord_of(lon: float) -> str:
    """D12 dwadasamsa lord.

    12 equal parts of 2.5° each, counting from the sign itself.
    Lord = SIGN_LORDS of the resulting sign.
    """
    sign, deg = _sign_deg(lon)
    part = int(deg / 2.5)                  # 0..11
    return SIGN_LORDS[((sign - 1 + part) % 12) + 1]


def varga_lord_of(lon: float, n: int) -> str:
    """Varga lord for the GBB saptavarga set {1,2,3,7,9,12,30}: the ruler of the
    divisional sign holding ``lon`` in D-``n``. Mirrors ``shadbala.sthana._varga_lord``
    (GBB-3:447-543) as a public dispatcher WITHOUT touching the Shadbala path; the
    special-scheme divisions (D2 hora, D7 saptamsa, D12 dwadasamsa, D30 thrimsamsa)
    use their dedicated lord functions, the sign-scheme ones (D1/D3/D9) the sign lord."""
    from app.raman_saab.chart import varga as _v
    if n == 2:
        return hora_lord_of(lon)
    if n == 7:
        return saptamsa_lord_of(lon)
    if n == 12:
        return dwadasamsa_lord_of(lon)
    if n == 30:
        return thrimsamsa_lord_of(lon)
    if n in (1, 3, 9):
        return SIGN_LORDS[_v.varga_sign(lon, n)]
    raise ValueError(f"varga_lord_of supports the saptavarga {{1,2,3,7,9,12,30}}, got D{n}")


def thrimsamsa_lord_of(lon: float) -> str:
    """D30 thrimsamsa lord.

    Unequal 5-fold partition, planets assigned directly (no sign counting).

    Odd signs  (Mars/Saturn/Jupiter/Mercury/Venus at upper bounds 5/10/18/25/30).
    Even signs (Venus/Mercury/Jupiter/Saturn/Mars at upper bounds 5/12/20/25/30).
    """
    sign, deg = _sign_deg(lon)
    odd = sign % 2 == 1
    bounds: list[tuple[int, str]] = (
        [(5, "Mars"), (10, "Saturn"), (18, "Jupiter"), (25, "Mercury"), (30, "Venus")]
        if odd else
        [(5, "Venus"), (12, "Mercury"), (20, "Jupiter"), (25, "Saturn"), (30, "Mars")]
    )
    for hi, planet in bounds:
        if deg < hi:
            return planet
    return bounds[-1][1]  # deg == 30.0 boundary guard
