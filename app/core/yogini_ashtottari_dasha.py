"""Yogini + Ashtottari dashas — Gap C.

Vimshottari + Chara are the two confirmation tracks we already have.
Per BV Raman + KN Rao, serious readings cross-verify against at least
3 dasha systems. Two more critical systems:

## Yogini Dasha (BPHS Ch.45 — 8-period, 36-year cycle)

Often called "the women's dasha" because of historic use in female
charts, but used universally now. Particularly favored when timing
emotional / health / mind events.

Lord sequence (cyclic):
  Mangala (1y) → Pingala (2y) → Dhanya (3y) → Bhramari (4y) →
  Bhadrika (5y) → Ulka (6y) → Siddha (7y) → Sankata (8y)
Sum = 36 years per cycle.

Starting Yogini is determined by Janma Nakshatra (Moon's nakshatra
at birth): formula = (nakshatra_index + 3) mod 8.

## Ashtottari Dasha (BPHS Ch.46 — 8-period, 108-year cycle)

Activated when **Rahu is in a kendra (1/4/7/10) OR trine (5/9) from
the Lagna lord** per Mansagari / Phaladeepika. Otherwise, Vimshottari
suffices.

Lord sequence (cyclic) and years:
  Sun (6) → Moon (15) → Mars (8) → Mercury (17) → Saturn (10) →
  Jupiter (19) → Rahu (12) → Venus (21)
Sum = 108 years per cycle.

Starting lord determined by Moon's nakshatra-pada at birth (Krishna /
Shukla paksha + nakshatra mod 8). Simplified formula here uses
Moon's longitude / nakshatra index.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Locked year-length from CLAUDE.md
DAYS_PER_VEDIC_YEAR: Final[float] = 365.2425


# ─── Yogini Dasha ───────────────────────────────────────────────────


YOGINI_LORDS: Final[tuple[str, ...]] = (
    "Mangala", "Pingala", "Dhanya", "Bhramari",
    "Bhadrika", "Ulka", "Siddha", "Sankata",
)
YOGINI_PERIOD_YEARS: Final[tuple[int, ...]] = (1, 2, 3, 4, 5, 6, 7, 8)
# YOGINI_PRESIDING_PLANET (presiding graha for each Yogini)
YOGINI_PRESIDING_PLANET: Final[dict[str, str]] = {
    "Mangala": "Moon", "Pingala": "Sun", "Dhanya": "Jupiter",
    "Bhramari": "Mars", "Bhadrika": "Mercury", "Ulka": "Saturn",
    "Siddha": "Venus", "Sankata": "Rahu",
}


@dataclass(frozen=True)
class YoginiPeriod:
    """One Yogini MD period."""
    yogini_name: str
    presiding_planet: str
    period_years: int
    start_jd: float
    end_jd: float


def yogini_starting_index(moon_nakshatra_index: int) -> int:
    """Compute starting Yogini index from Moon's birth nakshatra.

    Per BPHS Ch.45: starting Yogini = (nakshatra_index + 3) mod 8.
    Returns index 0..7 into YOGINI_LORDS.
    """
    if not 0 <= moon_nakshatra_index <= 26:
        raise ValueError(
            f"moon_nakshatra_index must be 0..26, got {moon_nakshatra_index}"
        )
    return (moon_nakshatra_index + 3) % 8


def yogini_sequence(
    moon_nakshatra_index: int, birth_jd: float,
) -> tuple[YoginiPeriod, ...]:
    """Full Yogini Dasha cycle: 8 periods starting from birth.

    Returns the 8 MD periods in chronological order. Caller can extend
    by repeating the cycle for natives reaching the cycle end at age 36.
    """
    start_idx = yogini_starting_index(moon_nakshatra_index)
    cursor = birth_jd
    out: list[YoginiPeriod] = []
    for i in range(8):
        lord_idx = (start_idx + i) % 8
        years = YOGINI_PERIOD_YEARS[lord_idx]
        end = cursor + years * DAYS_PER_VEDIC_YEAR
        out.append(YoginiPeriod(
            yogini_name=YOGINI_LORDS[lord_idx],
            presiding_planet=YOGINI_PRESIDING_PLANET[YOGINI_LORDS[lord_idx]],
            period_years=years,
            start_jd=cursor, end_jd=end,
        ))
        cursor = end
    return tuple(out)


def yogini_active_at(
    moon_nakshatra_index: int, birth_jd: float, target_jd: float,
) -> YoginiPeriod | None:
    """Active Yogini MD at the given JD (with cycle wrap).

    Returns None if target_jd is before birth.
    """
    if target_jd < birth_jd:
        return None
    cycle = yogini_sequence(moon_nakshatra_index, birth_jd)
    cycle_length_days = cycle[-1].end_jd - birth_jd  # 36 years
    if cycle_length_days <= 0:
        return None
    effective_jd = birth_jd + ((target_jd - birth_jd) % cycle_length_days)
    for period in cycle:
        if period.start_jd <= effective_jd < period.end_jd:
            return period
    return None


# ─── Ashtottari Dasha ───────────────────────────────────────────────


ASHTOTTARI_LORDS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury",
    "Saturn", "Jupiter", "Rahu", "Venus",
)
ASHTOTTARI_PERIOD_YEARS: Final[tuple[int, ...]] = (
    6, 15, 8, 17, 10, 19, 12, 21,
)


@dataclass(frozen=True)
class AshtottariPeriod:
    """One Ashtottari MD period."""
    lord: str
    period_years: int
    start_jd: float
    end_jd: float


def ashtottari_starting_index(moon_nakshatra_index: int) -> int:
    """Compute starting Ashtottari MD index from Moon's nakshatra.

    Standard formula (Mansagari, Phaladeepika Ch.20): starting MD =
    nakshatra_index mod 8.

    Simplified — full classical version uses pada + paksha; this is the
    most-cited single-formula reduction.
    """
    if not 0 <= moon_nakshatra_index <= 26:
        raise ValueError(
            f"moon_nakshatra_index must be 0..26, got {moon_nakshatra_index}"
        )
    return moon_nakshatra_index % 8


def ashtottari_applicable(
    rahu_house: int, lagna_lord_house: int,
) -> bool:
    """Is Ashtottari Dasha applicable to this chart?

    Per Mansagari / Phaladeepika: applicable when Rahu is in a kendra
    (1/4/7/10) OR trine (5/9) from the Lagna lord. Otherwise use
    Vimshottari.

    Args:
        rahu_house: Rahu's natal house (1..12).
        lagna_lord_house: house of the Lagna lord (1..12).

    Returns:
        True if Rahu is in kendra/trine from Lagna lord.
    """
    if not (1 <= rahu_house <= 12 and 1 <= lagna_lord_house <= 12):
        raise ValueError("houses must be 1..12")
    distance = ((rahu_house - lagna_lord_house) % 12) + 1
    return distance in {1, 4, 5, 7, 9, 10}


def ashtottari_sequence(
    moon_nakshatra_index: int, birth_jd: float,
) -> tuple[AshtottariPeriod, ...]:
    """Full Ashtottari Dasha cycle: 8 periods starting from birth."""
    start_idx = ashtottari_starting_index(moon_nakshatra_index)
    cursor = birth_jd
    out: list[AshtottariPeriod] = []
    for i in range(8):
        lord_idx = (start_idx + i) % 8
        years = ASHTOTTARI_PERIOD_YEARS[lord_idx]
        end = cursor + years * DAYS_PER_VEDIC_YEAR
        out.append(AshtottariPeriod(
            lord=ASHTOTTARI_LORDS[lord_idx],
            period_years=years,
            start_jd=cursor, end_jd=end,
        ))
        cursor = end
    return tuple(out)


def ashtottari_active_at(
    moon_nakshatra_index: int, birth_jd: float, target_jd: float,
) -> AshtottariPeriod | None:
    """Active Ashtottari MD at the given JD (with cycle wrap)."""
    if target_jd < birth_jd:
        return None
    cycle = ashtottari_sequence(moon_nakshatra_index, birth_jd)
    cycle_length_days = cycle[-1].end_jd - birth_jd  # 108 years
    if cycle_length_days <= 0:
        return None
    effective_jd = birth_jd + ((target_jd - birth_jd) % cycle_length_days)
    for period in cycle:
        if period.start_jd <= effective_jd < period.end_jd:
            return period
    return None
