"""Reconstruct a RamanChart from Raman's PRINTED Rāśi + Navāṁśa sign diagrams.

Raman's worked charts in *How to Judge a Horoscope* give sign placements only (no
degrees). The strength verdict needs only signs (Rāśi) + navāṁśa signs — daśā, which
needs the Moon's degree, drives timing not strength — so a faithful chart is
recoverable from his two diagrams alone:

  * park each planet at its printed Rāśi sign, and
  * choose the one navāṁśa **pada** whose D9 equals its printed Navāṁśa sign.

The D9 pada→sign map is the engine's own (``app.core.ephemeris_engine
.calculate_divisional_longitude``, divisor 9), so the reconstructed chart reproduces
Raman's printed Navāṁśa *exactly*, not by approximation. Only 9 of the 12 signs are
reachable as the navāṁśa of a given rāśi sign, so an unreachable (rāśi, navāṁśa) pair
is a mis-extraction — a free extraction-error detector (``navamsa_pada`` returns None).
"""
from __future__ import annotations

from app.medini.doctrine import raman_chart as rc

# 1-based sign names, Aries=1 … Pisces=12.
SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
SIGN_INDEX = {name.lower(): i + 1 for i, name in enumerate(SIGNS)}

_PADA = 30.0 / 9.0  # 3°20′
# navāṁśa of pada 0 of a rāśi sign starts at: fire→Aries, earth→Capricorn,
# air→Libra, water→Cancer (element = (sign-1) % 4), matching the engine.
_START = {0: 0, 1: 9, 2: 6, 3: 3}
# strength is daśā-independent, but the constructor needs a birth_jd; J2000 is fine.
_FIXED_JD = 2451545.0


def sign_num(name: str) -> int:
    """'Cancer'/'cancer'/'4' → 4. Raises on an unknown sign."""
    s = str(name).strip().lower()
    if s.isdigit():
        n = int(s)
        if 1 <= n <= 12:
            return n
    if s in SIGN_INDEX:
        return SIGN_INDEX[s]
    raise ValueError(f"unknown sign {name!r}")


def navamsa_sign_of_pada(rasi_sign: int, pada: int) -> int:
    """The navāṁśa sign (1-12) of pada k (0-8) of a rāśi sign (1-12)."""
    start = _START[(rasi_sign - 1) % 4]
    return (start + pada) % 12 + 1


def navamsa_pada(rasi_sign: int, navamsa_sign: int) -> int | None:
    """The pada (0-8) of ``rasi_sign`` whose navāṁśa is ``navamsa_sign``, or None if
    the pair is impossible (navāṁśa unreachable from that rāśi sign → mis-extraction)."""
    start = _START[(rasi_sign - 1) % 4]
    k = (navamsa_sign - 1 - start) % 12
    return k if k <= 8 else None


def longitude_for(rasi_sign: int, navamsa_sign: int) -> float | None:
    """A longitude (pada midpoint) in ``rasi_sign`` whose D9 sign == ``navamsa_sign``.
    None if the (rāśi, navāṁśa) pair is inconsistent."""
    k = navamsa_pada(rasi_sign, navamsa_sign)
    if k is None:
        return None
    return (rasi_sign - 1) * 30.0 + k * _PADA + _PADA / 2.0


def consistency_errors(rasi: dict, navamsa: dict) -> list[str]:
    """Names (planets / 'Lagna') whose printed (rāśi, navāṁśa) pair is impossible."""
    bad = []
    for name, r in rasi.items():
        n = navamsa.get(name)
        if n is None:
            bad.append(f"{name}: no navamsa sign")
        elif navamsa_pada(sign_num(r), sign_num(n)) is None:
            bad.append(f"{name}: navamsa {n} unreachable from rasi {r}")
    return bad


def chart_from_raman(rasi: dict, navamsa: dict, lagna_rasi, lagna_navamsa):
    """Build a RamanChart from printed Rāśi + Navāṁśa sign diagrams.

    ``rasi``/``navamsa`` map each of the 9 GRAHAS to a sign (name or 1-12). Raises
    ValueError if any (rāśi, navāṁśa) pair is inconsistent — call
    ``consistency_errors`` first to screen a record."""
    lons: dict[str, float] = {}
    for g in rc.GRAHAS:
        if g not in rasi or g not in navamsa:
            raise ValueError(f"missing rasi/navamsa placement for {g}")
        L = longitude_for(sign_num(rasi[g]), sign_num(navamsa[g]))
        if L is None:
            raise ValueError(
                f"{g}: navamsa {navamsa[g]} unreachable from rasi {rasi[g]}")
        lons[g] = L
    lagna_lon = longitude_for(sign_num(lagna_rasi), sign_num(lagna_navamsa))
    if lagna_lon is None:
        raise ValueError(
            f"Lagna: navamsa {lagna_navamsa} unreachable from rasi {lagna_rasi}")
    # ayanamsa='raman' is a label only — from_positions applies no shift, so the
    # signs (and padas) land exactly where placed.
    return rc.from_positions(lons, lagna_lon, birth_jd=_FIXED_JD, ayanamsa="raman")
