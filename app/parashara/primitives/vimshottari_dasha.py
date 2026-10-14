"""Vimshottari dasha — the 120-year, 9-lord primary system (BPHS ch.46, slokas 12-15).

The default dasha of Parashari astrology, which Parashara himself calls "the most appropriate and the
best of all Dasas" (BPHS-46, sl.12-14). Encoded from his OWN formulation, which reckons from Krittika:

    "Beginning from Krittika the lords of Dasas are the Sun, the Moon, Mars, Rahu, Jupiter, Saturn,
     Mercury, Ketu and Venus in that order. Thus if the nakshatras from Krittika to the Janma
     Nakshatra are divided by nine, the remainder will signify the lord of the commencing Dasa."
     (BPHS-46:128)
    "The periods ... of the Sun, the Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu and Venus are
     6, 10, 7, 18, 16, 19, 17, 7 and 20 ... total ... 120 years." (BPHS-46:142)

Parashara's Krittika-start description is identical to the familiar Aswini->Ketu scheme (Aswini and
Bharani, the two nakshatras before Krittika, seed Ketu and Venus — the two lords before the Sun in
the cycle); this module encodes his own words and the standard result falls out. It is the same
nakshatra-dasha machine as Ashtottari/Yogini, so it reuses that framework; only the cycle and seed
differ. Vimshottari is the general system — no special adoption condition, unlike Ashtottari.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.nakshatra_dasha import DashaPeriod, dasha_timeline, total_years

#: (lord, years) in Parashara's stated succession, beginning from the Sun (BPHS-46:128,142). The
#: cyclic order is what governs mahadasha succession; it equals the standard Ketu..Mercury cycle
#: entered at the Sun.
CYCLE: Final[tuple[tuple[str, int], ...]] = (
    ("Sun", 6), ("Moon", 10), ("Mars", 7), ("Rahu", 18), ("Jupiter", 16),
    ("Saturn", 19), ("Mercury", 17), ("Ketu", 7), ("Venus", 20),
)

#: Krittika is the 3rd nakshatra (Aswini = 1); Parashara counts the seed from it.
_KRITTIKA: Final[int] = 3

SEED_SOURCE: Final[Citation] = Citation("BPHS-46", 128)       # sl.12-14 — order + seed rule
DURATIONS_SOURCE: Final[Citation] = Citation("BPHS-46", 142)  # sl.15 — the nine durations
TOTAL_YEARS: Final[int] = 120


@dataclass(frozen=True)
class VimshottariSeed:
    index: int          # 0-based index into CYCLE
    lord: str


def seed(janma_nakshatra: int) -> VimshottariSeed:
    """The Vimshottari lord running at birth (BPHS-46:128): count nakshatras from Krittika to the
    Janma nakshatra, take the remainder mod 9, index into the cycle."""
    if not 1 <= janma_nakshatra <= 27:
        raise ValueError(f"janma_nakshatra must be 1..27, got {janma_nakshatra}")
    index = (janma_nakshatra - _KRITTIKA) % 9
    return VimshottariSeed(index=index, lord=CYCLE[index][0])


def timeline(janma_nakshatra: int, *, elapsed_fraction: float = 0.0) -> tuple[DashaPeriod, ...]:
    """The Vimshottari mahadasha timeline from birth (see the module note on `elapsed_fraction`)."""
    s = seed(janma_nakshatra)
    return dasha_timeline(CYCLE, s.index, elapsed_fraction=elapsed_fraction)


assert total_years(CYCLE) == TOTAL_YEARS, "Vimshottari cycle must total 120 years"
