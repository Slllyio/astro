"""Kakshya micro-transit — the Prasthara Chakra's eight-fold sign division (ASP-13).

Raman, *Ashtakavarga System of Prediction* ch.XIII: "according to the scheme of Prasthara
Chakra, each sign of the zodiac stands divided into 8 parts or Kakshyas (of 3¾° each) ... In
its each transit of a sign, a planet has to pass through each Kakshya in the above order"
(ASP-13:421-427). The judgment rule rides on WHO donated the sign's bindus: transiting the
Kakshya of a lord that CONTRIBUTED a bindu to that sign (in the transiting planet's own
Ashtakavarga) inclines the period favourable; a non-contributor's Kakshya runs adverse —
Raman's own 1962 worked example reads Jupiter-in-Aquarius exactly this way, Kakshya by Kakshya
(ASP-13:452-476), and it is this module's regression fixture.

**Source-fidelity note on the ORDER.** The printed prose sentence (ASP-13:424-425) lists only
seven names — Mars is missing IN THE PRINT, a printer's slip (7 names for 8 parts). Raman's own
longitude table eighteen lines later (ASP-13:443-451) carries all eight: Saturn 300°0'-303°45',
Jupiter -307°30', **Mars -311°15'**, Sun -315°0', Venus -318°45', Mercury -322°30', Moon
-326°15', Lagna -330°0'. The table is the authority; the order below follows it.

The same order also divides DASA time (ASP-12): a Dasa or sub-period splits into 8 equal parts
ruled Saturn..Lagna, each judged by its ruler's bindu donation — `kakshya_order` serves both
uses; the time-division helpers live with the timing layer, not here.

Usage:
    from app.raman_saab.primitives.kakshya import kakshya_of, transit_kakshya_reading
    idx, lord = kakshya_of(lon)                       # 0..7, its ruling reference
    r = transit_kakshya_reading(chart, "Jupiter", transit_lon)
    r.favourable, r.kakshya_lord, r.contributors      # the ASP-13 judgment
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.ashtakavarga import bhinnashtakavarga, prasthara

#: The Prasthara order, per Raman's own longitude table (ASP-13:443-451 — NOT the prose
#: sentence, which drops Mars in the print; see the module docstring).
KAKSHYA_ORDER: Final[tuple[str, ...]] = (
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna")

#: 30° / 8 — "8 parts or Kakshyas (of 3¾° each)" (ASP-13:423-424).
KAKSHYA_SPAN: Final[float] = 3.75


def kakshya_of(lon: float) -> tuple[int, str]:
    """The Kakshya index (0..7) and its ruling reference for a zodiacal longitude.

    Floor division per the project's locked cusp convention (CLAUDE.md): a longitude exactly on
    a Kakshya boundary belongs to the Kakshya it begins — Raman's table writes the boundaries
    the same way (303°45' ends Saturn's and starts Jupiter's)."""
    deg_in_sign = (lon % 360.0) % 30.0
    idx = min(int(deg_in_sign // KAKSHYA_SPAN), 7)
    return idx, KAKSHYA_ORDER[idx]


@dataclass(frozen=True)
class KakshyaReading:
    """One transiting planet's Kakshya judgment on one longitude (ASP-13:452-476)."""

    planet: str                      # the TRANSITING planet whose Ashtakavarga is consulted
    sign: int                        # transited sign 1..12
    kakshya_index: int               # 0..7 within the sign
    kakshya_lord: str                # ruling reference of that Kakshya
    lord_contributed: bool           # did that lord donate a bindu to this sign?
    bindus_in_sign: int              # the sign's bindu count in the planet's own BAV
    contributors: frozenset[str]     # who donated them (the Prasthara Chakra)

    @property
    def favourable(self) -> bool:
        """The ASP-13 inclination: a contributor's Kakshya favours; a non-contributor's runs
        adverse ("there will be sickness because Saturn has not contributed a bindu ... Good
        income can be predicted when Jupiter transits the 3rd Kakshya ruled by Mars ... Mars
        has also contributed a bindu", ASP-13:459-474)."""
        return self.lord_contributed

    @property
    def sign_proportion(self) -> float:
        """The sign-level effect proportion, bindus/8 — Raman's own percentages: 5 bindus →
        "to the extent of 62%" (ASP-13:280-282), 6 → "75%" (ASP-13:416), 0 → "to the brim"
        (ASP-13:283-286). A separate, coarser dial than the Kakshya call above."""
        return self.bindus_in_sign / 8.0


def transit_kakshya_reading(chart: RamanChart, planet: str, transit_lon: float) -> KakshyaReading:
    """Judge `planet` transiting `transit_lon` against its own natal Ashtakavarga (ASP-13).

    The chart supplies the NATAL Prasthara; only the longitude is a transit quantity. `planet`
    must be one of the seven Ashtakavarga grahas — the nodes have no Ashtakavarga and raise."""
    sign = int((transit_lon % 360.0) // 30.0) + 1
    idx, lord = kakshya_of(transit_lon)
    contributors = prasthara(chart, planet)[sign]
    return KakshyaReading(
        planet=planet, sign=sign, kakshya_index=idx, kakshya_lord=lord,
        lord_contributed=lord in contributors,
        bindus_in_sign=bhinnashtakavarga(chart, planet)[sign],
        contributors=contributors)
