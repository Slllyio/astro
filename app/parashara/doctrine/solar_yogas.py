"""Solar yogas (BPHS ch.38) — Vesi, Vasi and Ubhayachari, reckoned from the Sun.

The Sun's analogue of the lunar Sunapha/Anapha/Durudhara:

    "Barring the Moon, if a planet among Mars etc. be in the 2nd from the Sun Vesi yoga, in the 12th
     Vasi yoga, and planets in both the 2nd and the 12th Ubhayachari yoga are caused." (BPHS-38:27)

So a tara-graha (Mars, Mercury, Jupiter, Venus, Saturn) in the 2nd from the Sun gives Vesi, in the
12th Vasi, in both Ubhayachari. The Moon is excluded by the text, the Sun is the reference, and the
nodes do not participate. Benefics causing the yoga give the stated good effects, malefics the
contrary (BPHS-38 sl.4).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

_WORK: Final[str] = "BPHS-38"
SOURCE: Final[Citation] = Citation(_WORK, 27)        # sl.1 — definition
EFFECTS_SOURCE: Final[Citation] = Citation(_WORK, 38)  # sl.2-3 — effects
#: Barring the Moon (excluded by the text) and the Sun (the reference); nodes do not participate.
_TARA: Final[tuple[str, ...]] = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")


@dataclass(frozen=True)
class SolarYoga:
    name: str
    reason: str
    source: Citation


def _house(sun_sign: int, sign: int) -> int:
    return ((sign - sun_sign) % 12) + 1


def detect(planet_signs: Mapping[str, int], *, sun_sign: int) -> tuple[SolarYoga, ...]:
    """Vesi / Vasi / Ubhayachari for the chart (BPHS-38), each cited. `sun_sign` and the values of
    `planet_signs` are 1..12."""
    houses = {p: _house(sun_sign, planet_signs[p]) for p in _TARA if p in planet_signs}
    in_2nd = [p for p, d in houses.items() if d == 2]
    in_12th = [p for p, d in houses.items() if d == 12]
    if in_2nd and in_12th:
        return (SolarYoga("Ubhayachari",
                          f"grahas in both the 2nd ({', '.join(in_2nd)}) and 12th "
                          f"({', '.join(in_12th)}) from the Sun", SOURCE),)
    if in_2nd:
        return (SolarYoga("Vesi", f"{', '.join(in_2nd)} in the 2nd from the Sun", SOURCE),)
    if in_12th:
        return (SolarYoga("Vasi", f"{', '.join(in_12th)} in the 12th from the Sun", SOURCE),)
    return ()
