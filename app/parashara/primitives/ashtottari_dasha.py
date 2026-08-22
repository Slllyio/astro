"""Ashtottari dasha — the 108-year, 8-lord conditional system (BPHS ch.46, slokas 17-22).

    "The duration of Astottari Dasa for the Sun, the Moon, Mars, Mercury, Saturn, Jupiter, Rahu and
     Venus are 6, 15, 8, 17, 10, 19, 12 and 21 ... only 8 planets play the role of Dasa lords, Ketu
     having been denied this privilege." (BPHS-46:1627)

    Applicability (BPHS-46:1610, sl.17-20): "the learneds have recommended the adoption of Astottari
     Dasa, when Rahu is not in Lagna, in any other Kendra, or trikona to the lord of the Ascendant."

    Seed (sl.17-20): "From 4 nakshatras from Ardra commences the Dasa of the Sun, from 3 nakshatras
     after that begins the Dasa of the Moon; 4 nakshatras after that Mars; 3 Mercury; 4 Saturn;
     3 Jupiter; Rahu 4 after that; and Venus 3 from the last. The lord at birth is found by counting
     in this order up to the Janma nakshatra."

So Ashtottari counts across the 28-nakshatra scheme (27 + Abhijit), starting at Ardra, in groups of
[4,3,4,3,4,3,4,3] = 28 assigned to Sun, Moon, Mars, Mercury, Saturn, Jupiter, Rahu, Venus. Total
6+15+8+17+10+19+12+21 = 108.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.nakshatra_dasha import DashaPeriod, dasha_timeline, total_years

#: (lord, years) in Parashara's order (BPHS-46:1627). Ketu excluded.
CYCLE: Final[tuple[tuple[str, int], ...]] = (
    ("Sun", 6), ("Moon", 15), ("Mars", 8), ("Mercury", 17),
    ("Saturn", 10), ("Jupiter", 19), ("Rahu", 12), ("Venus", 21),
)

#: Nakshatra-group sizes seeding each lord, starting from Ardra (sl.17-20): 4,3,4,3,4,3,4,3 = 28.
_GROUP_SIZES: Final[tuple[int, ...]] = (4, 3, 4, 3, 4, 3, 4, 3)
#: Ardra is the 6th nakshatra (Aswini = 1). Counting uses the 28-scheme with Abhijit inserted
#: between Uttarashada (21) and Sravana (22) — Ardra's ordinal is unaffected (it precedes Abhijit).
_ARDRA: Final[int] = 6

SOURCE: Final[Citation] = Citation("BPHS-46", 1627)
APPLICABILITY_SOURCE: Final[Citation] = Citation("BPHS-46", 1610)
SEED_SOURCE: Final[Citation] = Citation("BPHS-46", 1610)
TOTAL_YEARS: Final[int] = 108


def _seed_table() -> tuple[str, ...]:
    """The 28-slot nakshatra->lord table, index 0 = Ardra, filled in groups of [4,3,...]."""
    table: list[str] = []
    for (lord, _), size in zip(CYCLE, _GROUP_SIZES):
        table.extend([lord] * size)
    assert len(table) == 28, "Ashtottari seed table must span the 28-nakshatra scheme"
    return tuple(table)


_SEED = _seed_table()


@dataclass(frozen=True)
class AshtottariSeed:
    index: int          # 0-based index into CYCLE
    lord: str


def seed(janma_nakshatra: int, *, is_abhijit: bool = False) -> AshtottariSeed:
    """The Ashtottari lord running at birth, counting from Ardra across the 28-nakshatra scheme.

    Args:
        janma_nakshatra: 1..27 (Aswini = 1).
        is_abhijit: True when the birth star is Abhijit (the 28th, between Uttarashada and Sravana).
            Abhijit occupies the seed slot immediately after Uttarashada.
    """
    if is_abhijit:
        # Abhijit sits between Uttarashada (21) and Sravana (22) -> 28-scheme position 22.
        pos28 = 22
    else:
        if not 1 <= janma_nakshatra <= 27:
            raise ValueError(f"janma_nakshatra must be 1..27, got {janma_nakshatra}")
        # Position in the 28-scheme: nakshatras after Uttarashada (>21) shift by one for Abhijit.
        pos28 = janma_nakshatra + (1 if janma_nakshatra >= 22 else 0)
    offset = (pos28 - _ARDRA) % 28          # 0 = Ardra
    lord = _SEED[offset]
    index = next(i for i, (l, _) in enumerate(CYCLE) if l == lord)
    return AshtottariSeed(index=index, lord=lord)


def timeline(janma_nakshatra: int, *, is_abhijit: bool = False,
             elapsed_fraction: float = 0.0) -> tuple[DashaPeriod, ...]:
    """The Ashtottari mahadasha timeline from birth."""
    s = seed(janma_nakshatra, is_abhijit=is_abhijit)
    return dasha_timeline(CYCLE, s.index, elapsed_fraction=elapsed_fraction)


def is_applicable(*, rahu_house_from_lagna: int, rahu_house_from_lagna_lord: Optional[int]) -> bool:
    """BPHS-46:1610 — adopt Ashtottari when Rahu is NOT in the Lagna, NOT in any other Kendra, and
    NOT in a trikona from the lord of the Ascendant.

    Args:
        rahu_house_from_lagna: Rahu's house counted from the ascendant (1..12).
        rahu_house_from_lagna_lord: Rahu's house counted from the ascendant LORD's position
            (1..12), or None if the lord's position is unknown (then the trikona-from-lord clause
            is treated conservatively as not-disqualifying).
    """
    kendras = {1, 4, 7, 10}          # "Lagna ... or any other Kendra"
    if rahu_house_from_lagna in kendras:
        return False
    if rahu_house_from_lagna_lord is not None and rahu_house_from_lagna_lord in {1, 5, 9}:
        return False                 # trikona to the lord of the Ascendant
    return True


assert total_years(CYCLE) == TOTAL_YEARS, "Ashtottari cycle must total 108 years"
