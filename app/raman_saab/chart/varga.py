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


def hora_sign(lon: float) -> int:
    """D2 — odd sign: 0-15 deg -> Leo(Sun), 15-30 -> Cancer(Moon); even sign reversed."""
    sign, deg = _sign_deg(lon)
    first = deg < 15.0
    if sign % 2 == 1:
        return 5 if first else 4
    return 4 if first else 5


def chaturthamsa_sign(lon: float) -> int:
    """D4 — 4 parts of 7.5 deg; part 0 -> same, 1 -> 4th, 2 -> 7th, 3 -> 10th (kendras)."""
    sign, deg = _sign_deg(lon)
    part = int(deg / 7.5)                             # 0..3
    return ((sign - 1 + part * 3) % 12) + 1


def shodasamsa_sign(lon: float) -> int:
    """D16 — 16 parts; start movable->Aries, fixed->Leo, dual->Sagittarius."""
    sign, deg = _sign_deg(lon)
    start = (1, 5, 9)[(sign - 1) % 3]
    return ((start - 1 + int(deg * 16 / 30)) % 12) + 1


def vimsamsa_sign(lon: float) -> int:
    """D20 — 20 parts; start movable->Aries, fixed->Sagittarius, dual->Leo."""
    sign, deg = _sign_deg(lon)
    start = (1, 9, 5)[(sign - 1) % 3]
    return ((start - 1 + int(deg * 20 / 30)) % 12) + 1


def siddhamsa_sign(lon: float) -> int:
    """D24 — 24 parts; odd sign starts Leo, even sign starts Cancer."""
    sign, deg = _sign_deg(lon)
    start = 5 if sign % 2 == 1 else 4
    return ((start - 1 + int(deg * 24 / 30)) % 12) + 1


def bhamsa_sign(lon: float) -> int:
    """D27 — 27 parts; start by element Fire->Aries, Earth->Cancer, Air->Libra, Water->Capricorn."""
    sign, deg = _sign_deg(lon)
    start = (1, 4, 7, 10)[(sign - 1) % 4]
    return ((start - 1 + int(deg * 27 / 30)) % 12) + 1


def trimsamsa_sign(lon: float) -> int:
    """D30 — unequal 5-fold; planet-sign mapping (odd vs even sign)."""
    sign, deg = _sign_deg(lon)
    bounds = ([(5, 1), (10, 11), (18, 9), (25, 3), (30, 7)] if sign % 2 == 1
              else [(5, 2), (12, 6), (20, 12), (25, 10), (30, 8)])
    for hi, s in bounds:
        if deg < hi:
            return s
    return bounds[-1][1]


def khavedamsa_sign(lon: float) -> int:
    """D40 — 40 parts; odd sign starts Aries, even sign starts Libra."""
    sign, deg = _sign_deg(lon)
    start = 1 if sign % 2 == 1 else 7
    return ((start - 1 + int(deg * 40 / 30)) % 12) + 1


def akshavedamsa_sign(lon: float) -> int:
    """D45 — 45 parts; start movable->Aries, fixed->Leo, dual->Sagittarius."""
    sign, deg = _sign_deg(lon)
    start = (1, 5, 9)[(sign - 1) % 3]
    return ((start - 1 + int(deg * 45 / 30)) % 12) + 1


def shashtiamsa_sign(lon: float) -> int:
    """D60 — 60 parts of 0.5 deg, counted from the sign itself."""
    sign, deg = _sign_deg(lon)
    return ((sign - 1 + int(deg * 60 / 30)) % 12) + 1


_VARGA_FN = {
    1: lambda lon: _sign_deg(lon)[0],
    2: hora_sign,
    3: drekkana_sign,
    4: chaturthamsa_sign,
    7: saptamsa_sign,
    9: navamsa_sign,
    10: dasamsa_sign,
    12: dwadasamsa_sign,
    16: shodasamsa_sign,
    20: vimsamsa_sign,
    24: siddhamsa_sign,
    27: bhamsa_sign,
    30: trimsamsa_sign,
    40: khavedamsa_sign,
    45: akshavedamsa_sign,
    60: shashtiamsa_sign,
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
