"""Baladi avastha — the five age-states of a planet by degree (BPHS ch.45, slokas 3-4).

    "Infant, youthful, adolescent, old and dead are the states of planets placed in the ascending
     order at the rate of six degrees in odd signs. This arrangement is reverse in the case of
     even signs." (BPHS-45:45)
    "One fourth, half, full, negligible and nil are the grades of results due to a planet in
     infant, youthful, adolescent, old and dead states." (BPHS-45:66)

Odd sign, by degree-in-sign:
    0-6 bala (infant) · 6-12 kumara (youthful) · 12-18 yuva (adolescent) ·
    18-24 vriddha (old) · 24-30 mrita (dead)
Even sign: the SAME bands, reversed order (0-6 mrita ... 24-30 bala).

This is a load-bearing input to ch.11's bhava judgment: a bhava flourishes when its lord is in
kumara/yuva (BPHS-11:14), and is annihilated when its lord is in vriddha/mrita (BPHS-11:16). The
even-sign reversal is the classic error — ch.11's own worked degrees ("6-18 of an odd sign",
"6-12 of an even sign for Vriddha") only reconcile once the reversal is applied, which the tests
pin.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.parashara.doctrine.sources import Citation

#: Odd-sign order, ascending by 6-degree band. Even signs reverse this list.
_ODD_ORDER: Final[tuple[str, ...]] = ("bala", "kumara", "yuva", "vriddha", "mrita")

#: Result grade per state (BPHS-45:66): 1/4, 1/2, full, negligible, nil.
RESULT_GRADE: Final[dict[str, float]] = {
    "bala": 0.25, "kumara": 0.5, "yuva": 1.0, "vriddha": 0.125, "mrita": 0.0,
}

STATE_SOURCE: Final[Citation] = Citation("BPHS-45", 45)
GRADE_SOURCE: Final[Citation] = Citation("BPHS-45", 66)


@dataclass(frozen=True)
class BaladiAvastha:
    state: str          # bala | kumara | yuva | vriddha | mrita
    grade: float        # result strength 0..1 (RESULT_GRADE)
    is_odd_sign: bool


def baladi_avastha(sign: int, degree_in_sign: float) -> BaladiAvastha:
    """The Baladi avastha of a planet at `degree_in_sign` (0..30) in `sign` (1=Aries..12=Pisces).

    Odd signs (Aries, Gemini, ... = odd sign-number) take the ascending order; even signs reverse
    it. The band is `int(degree // 6)`, clamped so an exact 30.0 lands in the last band.
    """
    if not 1 <= sign <= 12:
        raise ValueError(f"sign must be 1..12, got {sign}")
    if not 0.0 <= degree_in_sign <= 30.0:
        raise ValueError(f"degree_in_sign must be 0..30, got {degree_in_sign}")
    band = min(int(degree_in_sign // 6), 4)
    is_odd = (sign % 2 == 1)
    order = _ODD_ORDER if is_odd else tuple(reversed(_ODD_ORDER))
    state = order[band]
    return BaladiAvastha(state=state, grade=RESULT_GRADE[state], is_odd_sign=is_odd)


def baladi_from_longitude(longitude: float) -> BaladiAvastha:
    """Convenience: Baladi avastha straight from a sidereal longitude in degrees."""
    lon = longitude % 360.0
    sign = int(lon // 30) + 1
    return baladi_avastha(sign, lon % 30.0)
