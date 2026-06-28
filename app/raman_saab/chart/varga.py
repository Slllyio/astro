from __future__ import annotations
from app.raman_saab.chart.constants import NAVAMSA_START

_NAK_SPAN = 360.0 / 27.0
_PADA_SPAN = _NAK_SPAN / 4.0


def _sign_deg(lon: float) -> tuple[int, float]:
    """(sign 1..12, degrees-within-sign 0..30)."""
    lon %= 360.0
    return int(lon // 30) + 1, lon % 30.0


def navamsa_sign(lon: float) -> int:
    """D9 sign (1..12). Element-based start: Fire->Aries, Earth->Cap, Air->Libra, Water->Cancer."""
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30
    part = int(deg_in_sign // (30 / 9))               # 0..8
    start = NAVAMSA_START[sign_idx % 4]               # 1-indexed start sign
    return ((start - 1 + part) % 12) + 1


def drekkana_sign(lon: float) -> int:
    """D3 — 3 parts of 10 deg; part 0 -> same sign, 1 -> 5th, 2 -> 9th (Parashara)."""
    sign, deg = _sign_deg(lon)
    part = int(deg // 10)                             # 0..2
    return ((sign - 1 + part * 4) % 12) + 1


def saptamsa_sign(lon: float) -> int:
    """D7 — 7 parts; odd sign counts from itself, even sign from the 7th (Parashara)."""
    sign, deg = _sign_deg(lon)
    part = int(deg * 7 / 30)                          # 0..6
    start = sign if sign % 2 == 1 else ((sign - 1 + 6) % 12) + 1
    return ((start - 1 + part) % 12) + 1


def dasamsa_sign(lon: float) -> int:
    """D10 — 10 parts of 3 deg; odd sign counts from itself, even sign from the 9th (Parashara)."""
    sign, deg = _sign_deg(lon)
    part = int(deg * 10 / 30)                         # 0..9
    start = sign if sign % 2 == 1 else ((sign - 1 + 8) % 12) + 1
    return ((start - 1 + part) % 12) + 1


def dwadasamsa_sign(lon: float) -> int:
    """D12 — 12 parts of 2.5 deg, counted from the sign itself (Parashara)."""
    sign, deg = _sign_deg(lon)
    part = int(deg / 2.5)                             # 0..11
    return ((sign - 1 + part) % 12) + 1


_VARGA_FN = {
    1: lambda lon: _sign_deg(lon)[0],
    3: drekkana_sign,
    7: saptamsa_sign,
    9: navamsa_sign,
    10: dasamsa_sign,
    12: dwadasamsa_sign,
}

#: Divisional charts BV Raman judges for matter-specific significations.
SUPPORTED_VARGAS: frozenset[int] = frozenset(_VARGA_FN)


def varga_sign(lon: float, n: int) -> int:
    """Sign (1..12) a longitude occupies in the D-`n` divisional chart.
    Supported n: 1 (rasi), 3 (drekkana), 7 (saptamsa), 9 (navamsa), 10 (dasamsa), 12 (dwadasamsa)."""
    try:
        return _VARGA_FN[n](lon)
    except KeyError:
        raise ValueError(f"unsupported varga D{n}; supported: {sorted(SUPPORTED_VARGAS)}") from None

def nakshatra_pada(lon: float) -> tuple[int, int]:
    nak = int(lon // _NAK_SPAN) + 1                   # 1..27
    pada = int((lon % _NAK_SPAN) // _PADA_SPAN) + 1   # 1..4
    return nak, pada

def is_vargottama(*, sign: int, navamsa: int) -> bool:
    return sign == navamsa
