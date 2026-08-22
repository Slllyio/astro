"""Nakshatra-seeded dasha framework — the shape every BPHS conditional dasha shares (ch.46).

Vimshottari, Ashtottari, Yogini and the -sama variants are all the same machine: a fixed cyclic
sequence of (lord, years), entered at a starting lord chosen from the birth nakshatra, with the
birth mahadasha already partly elapsed. Only three things vary between systems — the cycle, the
seed rule, and the total — so those are the inputs here and each system supplies its own.

This module is the arithmetic; the systems (`yogini_dasha`, `ashtottari_dasha`) carry the doctrine
and the citations. The balance-at-birth follows Parashara's Bhayat/Bhabhog method (BPHS-46:21-22),
taken here as an already-computed `elapsed_fraction` of the birth mahadasha so the framework stays
pure — deriving that fraction from the Moon's ghatika position is the caller's step and needs
birth-time precision, not this table math.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class DashaPeriod:
    lord: str
    start_year: float      # years after birth this mahadasha begins (0.0 = running at birth)
    years: float           # its full length
    end_year: float        # start_year + (remaining length for the birth period)


def dasha_timeline(cycle: Sequence[tuple[str, float]], start_index: int, *,
                   elapsed_fraction: float = 0.0) -> tuple[DashaPeriod, ...]:
    """One full cycle of mahadashas from birth.

    Args:
        cycle: the system's ordered (lord, years) sequence — its whole span is the total.
        start_index: index into `cycle` of the mahadasha running at birth (the seed result).
        elapsed_fraction: how much of that birth mahadasha is already spent at birth, 0..1. The
            first period therefore contributes only its remaining `(1 - elapsed_fraction)` years.

    Returns one period per lord, in order from birth, wrapping once through the cycle.
    """
    n = len(cycle)
    if not 0 <= start_index < n:
        raise ValueError(f"start_index {start_index} out of range for a {n}-lord cycle")
    if not 0.0 <= elapsed_fraction < 1.0:
        raise ValueError(f"elapsed_fraction must be in [0, 1), got {elapsed_fraction}")

    out: list[DashaPeriod] = []
    cursor = 0.0
    for step in range(n):
        lord, years = cycle[(start_index + step) % n]
        length = years * (1.0 - elapsed_fraction) if step == 0 else years
        out.append(DashaPeriod(lord=lord, start_year=cursor, years=years,
                               end_year=cursor + length))
        cursor += length
    return tuple(out)


def total_years(cycle: Sequence[tuple[str, float]]) -> float:
    """The system's full cycle length — its defining constant (108 Ashtottari, 36 Yogini, ...)."""
    return sum(years for _, years in cycle)
