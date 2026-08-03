"""Rasi & Graha Gunakara — the Ashtakavarga pinda multipliers (HPA-26:1130-1404).

After both reductions ("Now again we must divert our attention to Bhinnashtakavarga Tables of
all the seven planets *after reduction*", HPA-26:1128-1131) Raman derives, per planet:

  - **Rasi Gunakara** (zodiacal factors, HPA-26:1139-1153): each sign's reduced bindus times a
    fixed per-sign factor, all twelve products summed. "This is constant for all horoscopes."
  - **Graha Gunakara** (planetary factors, HPA-26:1303-1315): for each of the seven grahas, the
    reduced bindus in the SIGN THAT GRAHA OCCUPIES times a fixed per-planet factor, summed.

**Naming fidelity.** The literature widely calls these sums (and their total) the *Sodhya
Pinda* — rasi pinda + graha pinda. Raman does not use that term anywhere in HPA-26; he names
the two Gunakaras and puts their sum straight into Ayurdaya: "Add together the Rasi figures
and Graha figures ... multiply the result by 7 and divide the product by 27. The quotient
gives the years of Ayurdaya" (HPA-26:1400-1404). This module therefore exposes Raman's own
terms; `total` on the breakdown is what other texts call the planet's Sodhya Pinda, and the
docstring is the only place that alias appears.

**Scope.** HPA-26 applies the pinda to LONGEVITY. The transit-multiplier application (the
pinda scaling Gochara results) belongs to Raman's *Ashtakavarga System of Prediction*, which
is not yet in the registered corpus — encode that application only when that book is
registered, citing it, not this chapter.

Raman's worked example is the fixture: the Sun's reduced table gives Rasi 112, and with the
example occupancies (Sun-Cancer, Moon/Saturn-Taurus, Mars/Mercury/Venus-Leo, Jupiter-Scorpio)
Graha 45; "The sign total is 112 and the planet total is 45, i.e., 112+45=157" (HPA-26:1394).

Usage:
    from app.raman_saab.primitives.ashtakavarga_pinda import ashtakavarga_pinda
    pb = ashtakavarga_pinda(chart, "Sun")     # .rasi, .graha, .total
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.ashtakavarga import PLANETS
from app.raman_saab.primitives.ashtakavarga_reduction import reduced_bhinnashtakavarga

#: Zodiacal factors, Aries..Pisces (HPA-26:1149-1153): "Aries 7, Taurus 10, Gemini 8, Cancer 4,
#: Leo 10, Virgo 5, Libra 7, Scorpio 8, Sagittarius 9, Capricorn 5, Aquarius 11, and Pisces 12.
#: This is constant for all horoscopes."
RASI_GUNAKARA: Final[dict[int, int]] = {
    1: 7, 2: 10, 3: 8, 4: 4, 5: 10, 6: 5, 7: 7, 8: 8, 9: 9, 10: 5, 11: 11, 12: 12}

#: Planetary factors (HPA-26:1311-1315): "Sun 5, Moon 5, Mars 8, Mercury 5, Jupiter 10,
#: Venus 7 and Saturn 5. This is constant for all days."
GRAHA_GUNAKARA: Final[dict[str, int]] = {
    "Sun": 5, "Moon": 5, "Mars": 8, "Mercury": 5, "Jupiter": 10, "Venus": 7, "Saturn": 5}


@dataclass(frozen=True)
class PindaBreakdown:
    """One planet's Gunakara figures. `total = rasi + graha` is what the wider literature
    calls the planet's Sodhya Pinda (Raman himself does not use the term — module docstring)."""

    planet: str
    rasi: int
    graha: int

    @property
    def total(self) -> int:
        return self.rasi + self.graha


def rasi_gunakara(reduced_bav: Mapping[int, int]) -> int:
    """Sum of (reduced bindus x zodiacal factor) over all twelve signs (HPA-26:1139-1148)."""
    return sum(reduced_bav[s] * RASI_GUNAKARA[s] for s in range(1, 13))


def graha_gunakara(reduced_bav: Mapping[int, int], occupancy: Mapping[str, int]) -> int:
    """Sum over the seven grahas of (reduced bindus in the sign that graha OCCUPIES x its
    planetary factor) — HPA-26:1305-1310.

    `occupancy` maps graha -> occupied sign (1..12). Only the seven Gunakara grahas count;
    anything else in the mapping (nodes, Lagna) is ignored, mirroring the factor table itself.
    Every bindu table this multiplies is the OWNING planet's Ashtakavarga — in Raman's example
    the Moon's factor multiplies the SUN's bindus in Taurus, because the table under
    consideration is the Sun's (HPA-26:1322-1329)."""
    return sum(reduced_bav[occupancy[g]] * GRAHA_GUNAKARA[g]
               for g in GRAHA_GUNAKARA if g in occupancy)


def ashtakavarga_pinda(chart: RamanChart, planet: str) -> PindaBreakdown:
    """`planet`'s Gunakara breakdown on a cast chart, from its fully-reduced Ashtakavarga."""
    reduced = reduced_bhinnashtakavarga(chart, planet)
    occupancy = {name: p.sign for name, p in chart.planets.items() if name in PLANETS}
    return PindaBreakdown(planet=planet, rasi=rasi_gunakara(reduced),
                          graha=graha_gunakara(reduced, occupancy))
