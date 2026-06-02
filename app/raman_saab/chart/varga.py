from __future__ import annotations
from app.raman_saab.chart.constants import NAVAMSA_START

_NAK_SPAN = 360.0 / 27.0
_PADA_SPAN = _NAK_SPAN / 4.0

def navamsa_sign(lon: float) -> int:
    """D9 sign (1..12). Element-based start: Fire->Aries, Earth->Cap, Air->Libra, Water->Cancer."""
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30
    part = int(deg_in_sign // (30 / 9))               # 0..8
    start = NAVAMSA_START[sign_idx % 4]               # 1-indexed start sign
    return ((start - 1 + part) % 12) + 1

def nakshatra_pada(lon: float) -> tuple[int, int]:
    nak = int(lon // _NAK_SPAN) + 1                   # 1..27
    pada = int((lon % _NAK_SPAN) // _PADA_SPAN) + 1   # 1..4
    return nak, pada

def is_vargottama(*, sign: int, navamsa: int) -> bool:
    return sign == navamsa
