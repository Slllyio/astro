"""English ordinal formatting shared by the render modules.

The naive ``f"{n}th"`` printed "the 2th house" / "the 3th" in the matter-varga
and related report blocks (docs/raman_saab/REPORT_CRITIQUE_2026-08-17.md).
This is the one correct helper; render modules import it instead of hand-rolling
the suffix.

Usage:
    from app.raman_saab.ordinals import ordinal
    ordinal(2)    # "2nd"
    ordinal(12)   # "12th"
    ordinal(23)   # "23rd"
"""
from __future__ import annotations

from typing import Final

_SUFFIX: Final[dict[int, str]] = {1: "st", 2: "nd", 3: "rd"}


def ordinal(n: int) -> str:
    """1 -> '1st', 2 -> '2nd', 3 -> '3rd', 4 -> '4th', 11/12/13 -> '11th/12th/13th',
    21 -> '21st', 22 -> '22nd', 23 -> '23rd', 111 -> '111th'."""
    if n % 100 in (11, 12, 13):
        return f"{n}th"
    return f"{n}{_SUFFIX.get(n % 10, 'th')}"
