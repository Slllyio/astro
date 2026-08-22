"""Bhava karakas — the natural significator planet of each house (BPHS ch.32, sl.31-34).

    "The significators of the house in order are: the Sun, Jupiter, Mars, the Moon, Jupiter, Mars,
     Venus, Saturn, Jupiter, Mercury, Jupiter and Saturn." (BPHS-32:452)

So the 1st house is signified by the Sun, the 2nd and 5th by Jupiter, the 3rd and 6th by Mars, the
4th by the Moon, the 7th by Venus, the 8th and 12th by Saturn, the 9th and 11th by Jupiter, the 10th
by Mercury. A fixed table (chart-invariant), the karaka whose placement and strength colour each
bhava's reading — a queryable reference, not per-nativity output.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-32", 452)   # sl.31-34, "significators of the house in order"

#: House (1..12) -> its natural significator graha (BPHS-32:452).
BHAVA_KARAKA: Final[Mapping[int, str]] = {
    1: "Sun", 2: "Jupiter", 3: "Mars", 4: "Moon", 5: "Jupiter", 6: "Mars",
    7: "Venus", 8: "Saturn", 9: "Jupiter", 10: "Mercury", 11: "Jupiter", 12: "Saturn"}


def karaka_of(house: int) -> str:
    """The natural significator graha of `house` (1..12), per BPHS ch.32."""
    if not 1 <= house <= 12:
        raise ValueError("house must be 1..12")
    return BHAVA_KARAKA[house]
