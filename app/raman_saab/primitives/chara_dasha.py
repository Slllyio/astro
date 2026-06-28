"""Jaimini Chara Dasha (KN Rao convention) — a sign-based dasha sequence.

Unlike Vimshottari (planet/nakshatra based), Chara Dasha runs over the twelve RASHIS. Conventions
vary across traditions; this implements the widely-taught **KN Rao** rules, documented explicitly:

* ORDER: start from the Lagna sign; proceed DIRECT (zodiacal) if the Lagna is an ODD sign
  (Aries/Gemini/Leo/Libra/Sagittarius/Aquarius), REVERSE (anti-zodiacal) if EVEN.
* DURATION of a sign S's dasha: count from S to the sign occupied by S's lord — the count is
  DIRECT if S is odd, REVERSE if S is even; years = count - 1; if the lord is IN S, the dasha is
  12 years.
* DUAL-LORD SIGNS: Scorpio uses Mars, Aquarius uses Saturn (the traditional lords; the KN Rao
  Ketu/Rahu-strength refinement and the exalt/debil +-1-year tweak are deliberately omitted and
  noted here, to keep the convention unambiguous).

Usage:
    from app.raman_saab.primitives import chara_dasha as cd
    seq = cd.chara_dasha(chart)            # [(sign 1..12, years), ...] from birth, 12 periods
    cur = cd.chara_dasha_on(chart, age_years)
"""
from __future__ import annotations

from typing import Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart


def _duration_years(sign: int, chart: RamanChart) -> int:
    lord = SIGN_LORDS[sign]                          # Scorpio->Mars, Aquarius->Saturn (traditional)
    lp = chart.planets.get(lord)
    if lp is None:
        return 1
    lord_sign = lp.sign
    if sign % 2 == 1:                               # odd -> direct count
        count = ((lord_sign - sign) % 12) + 1
    else:                                           # even -> reverse count
        count = ((sign - lord_sign) % 12) + 1
    years = count - 1
    return 12 if years == 0 else years              # lord in own sign -> full 12


def chara_dasha(chart: RamanChart) -> list[tuple[int, int]]:
    """The 12-period Chara Dasha sequence [(sign, years), ...] from birth."""
    lagna = chart.asc_sign
    direct = lagna % 2 == 1
    seq: list[tuple[int, int]] = []
    for i in range(12):
        s = ((lagna - 1 + i) % 12) + 1 if direct else ((lagna - 1 - i) % 12) + 1
        seq.append((s, _duration_years(s, chart)))
    return seq


def chara_dasha_on(chart: RamanChart, age_years: float) -> Optional[tuple[int, int]]:
    """The (sign, years) Chara Dasha running at `age_years` after birth, or None if past the
    sequence (the 12 periods do not sum to a fixed total in Chara Dasha)."""
    elapsed = 0.0
    for sign, years in chara_dasha(chart):
        if elapsed <= age_years < elapsed + years:
            return (sign, years)
        elapsed += years
    return None
