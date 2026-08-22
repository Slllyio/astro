"""Rasi-dasha framework — the shape the SIGN-based dashas share (BPHS ch.46).

The conditional dashas in `nakshatra_dasha` are cycles of planetary LORDS seeded from a nakshatra.
The rasi dashas (Sthira, Chara, Yogardha, Kalachakra…) are a different machine: the twelve SIGNS
themselves are the periods, entered at a start sign and traversed in a direction fixed by that
sign's parity —

    "The Dasas are counted onwards from the odd signs and in the reverse order from the even signs."
    (BPHS-46, Sthira sl.168-169)

So: start-sign odd -> forward (Aries->Taurus->…); start-sign even -> reverse (…->Taurus->Aries).
Each sign's span is system-specific (Sthira 7/8/9 by modality; Chara different), so the span is a
callable the system supplies. This module is the traversal + direction arithmetic only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass(frozen=True)
class RasiDashaPeriod:
    sign: int              # 1..12 (Aries..Pisces)
    start_year: float      # years after birth this sign's dasha begins
    years: float


def _traverse(start_sign: int) -> list[int]:
    """The 12 signs from `start_sign`, forward if it is odd, reverse if it is even (BPHS-46)."""
    if not 1 <= start_sign <= 12:
        raise ValueError(f"start_sign must be 1..12, got {start_sign}")
    step = 1 if start_sign % 2 == 1 else -1
    return [((start_sign - 1) + step * i) % 12 + 1 for i in range(12)]


def rasi_timeline(start_sign: int, span_for: Callable[[int], float]) -> tuple[RasiDashaPeriod, ...]:
    """The 12-sign dasha timeline from `start_sign`, each sign's length given by `span_for(sign)`.

    Direction is set by the start sign's parity (odd -> onwards, even -> reverse), Parashara's rule.
    """
    out: list[RasiDashaPeriod] = []
    cursor = 0.0
    for sign in _traverse(start_sign):
        yrs = float(span_for(sign))
        out.append(RasiDashaPeriod(sign=sign, start_year=cursor, years=yrs))
        cursor += yrs
    return tuple(out)


def total_years(span_for: Callable[[int], float]) -> float:
    """Full cycle length = every sign's span summed (order-independent)."""
    return sum(span_for(s) for s in range(1, 13))


# --- sign modality (used by the modality-span systems) ---
_MOVABLE = frozenset({1, 4, 7, 10})     # chara: Aries, Cancer, Libra, Capricorn
_FIXED = frozenset({2, 5, 8, 11})       # sthira: Taurus, Leo, Scorpio, Aquarius
_DUAL = frozenset({3, 6, 9, 12})        # dwiswabhava: Gemini, Virgo, Sagittarius, Pisces


def modality(sign: int) -> str:
    """'movable' | 'fixed' | 'dual' for a sign (1..12)."""
    if sign in _MOVABLE:
        return "movable"
    if sign in _FIXED:
        return "fixed"
    if sign in _DUAL:
        return "dual"
    raise ValueError(f"sign must be 1..12, got {sign}")
