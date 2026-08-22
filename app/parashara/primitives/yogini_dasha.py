"""Yogini dasha — the 36-year, 8-yogini nakshatra cycle (BPHS ch.46, slokas 199-200).

    "There are 8 Yoginis namely, 1. Mangala, 2. Pingala, 3. Dhanya, 4. Bhramari, 5. Bhadrika,
     6. Ulka, 7. Siddha and 8. Sankata. The Moon, the Sun, Jupiter, Mars, Mercury, Saturn, Venus
     and Rahu, are born from [them] in that order ... The Dasas of Mangala, Pingala ... are of 1,
     2, 3, 4, 5, 6, 7 and 8 years respectively. Add 3 to the Janma nakshatra and divide it by 8.
     The remainder 1 etc. will indicate the Yogini Dasa of Mangala etc." (BPHS-46:199)

Total 1+2+...+8 = 36 years. The seed is arithmetic and clean, and Parashara gives a worked example
(Mrigasira, nakshatra 5: 5+3=8, 8 mod 8 = 0 -> the 8th Yogini, Sankata) which is pinned in the
tests as the check that the seed is encoded right.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.nakshatra_dasha import DashaPeriod, dasha_timeline, total_years

#: (Yogini, ruling graha, years) in Parashara's order. The cycle IS this order (BPHS-46:199).
YOGINIS: Final[tuple[tuple[str, str, int], ...]] = (
    ("Mangala", "Moon", 1),
    ("Pingala", "Sun", 2),
    ("Dhanya", "Jupiter", 3),
    ("Bhramari", "Mars", 4),
    ("Bhadrika", "Mercury", 5),
    ("Ulka", "Saturn", 6),
    ("Siddha", "Venus", 7),
    ("Sankata", "Rahu", 8),
)

#: (lord, years) cycle for the generic framework.
CYCLE: Final[tuple[tuple[str, int], ...]] = tuple((graha, yrs) for _, graha, yrs in YOGINIS)

SOURCE: Final[Citation] = Citation("BPHS-46", 5789)
TOTAL_YEARS: Final[int] = 36


@dataclass(frozen=True)
class YoginiSeed:
    index: int          # 0-based index into YOGINIS/CYCLE
    yogini: str
    lord: str


def seed(janma_nakshatra: int) -> YoginiSeed:
    """The Yogini running at birth. BPHS-46:199 — (nakshatra + 3) mod 8; remainder 1 = Mangala,
    2 = Pingala, ..., 0 = the 8th (Sankata).

    Args:
        janma_nakshatra: 1..27 (Aswini = 1).
    """
    if not 1 <= janma_nakshatra <= 27:
        raise ValueError(f"janma_nakshatra must be 1..27, got {janma_nakshatra}")
    remainder = (janma_nakshatra + 3) % 8          # 0 => the 8th yogini
    index = (remainder - 1) % 8                     # remainder 1->0 (Mangala) ... 0->7 (Sankata)
    y = YOGINIS[index]
    return YoginiSeed(index=index, yogini=y[0], lord=y[1])


def timeline(janma_nakshatra: int, *, elapsed_fraction: float = 0.0) -> tuple[DashaPeriod, ...]:
    """The Yogini mahadasha timeline from birth for a given birth nakshatra."""
    return dasha_timeline(CYCLE, seed(janma_nakshatra).index, elapsed_fraction=elapsed_fraction)


assert total_years(CYCLE) == TOTAL_YEARS, "Yogini cycle must total 36 years"
