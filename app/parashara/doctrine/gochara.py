"""Gochara — transit judged by Ashtakavarga (BPHS ch.70), Parashara's own transit method.

BPHS has no separate "benefic houses from the Moon" gochara chapter; its transit doctrine is
ASHTAKAVARGA-based: a planet transiting a sign gives results according to that sign's benefic points
in the planet's own Bhinnashtakavarga —

    "Auspicious functions should be performed when [a planet] transits the rasi which has more
     [benefic points] in its Ashtakavarga." (BPHS-70:316, sl.19-20)

So a transit through a high-count sign is favourable, a low-count sign unfavourable. Each graha's BAV
gives 0..8 per sign (8 references); the midpoint is 4, so >=5 is favourable and <=3 unfavourable.
This reuses the checksum-guarded ashtakavarga tables directly.

Deferred (not faked): the Pinda-scaled transit predictions of ch.70 (Saturn-transit -> the harmed
nakshatra via the Yoga/Sodhya Pinda) need the Ekadhipatya/Pinda reductions, whose ch.68 worked
examples are internally inconsistent — see `ashtakavarga.trikona_shodhana`'s note. This module encodes
only the Pinda-free bindu-count rule.

Note on terminology: this edition names the benefic mark "rekha" and the zero "bindu"; the ENGINE's
ashtakavarga counts the benefic marks (SAV totals 337), so "bindus" here means the benefic count —
more is better, matching the sloka.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives import ashtakavarga as _av

SOURCE: Final[Citation] = Citation("BPHS-70", 316)   # sl.19-20 — transit by ashtakavarga count


@dataclass(frozen=True)
class TransitJudgment:
    planet: str
    transit_sign: int        # 1..12 the planet is transiting
    bindus: int              # the planet's BAV benefic count in that sign (0..8)
    quality: str             # favourable | mixed | unfavourable
    source: Citation


def _quality(bindus: int) -> str:
    if bindus >= 5:
        return "favourable"
    if bindus <= 3:
        return "unfavourable"
    return "mixed"


def transit_quality(planet: str, transit_sign: int, natal_planet_signs: Mapping[str, int], *,
                    asc_sign: int) -> TransitJudgment:
    """Judge `planet` transiting `transit_sign` by its own Bhinnashtakavarga count there (BPHS-70)."""
    if not 1 <= transit_sign <= 12:
        raise ValueError("transit_sign must be 1..12")
    bav = _av.bhinnashtakavarga(planet, natal_planet_signs, asc_sign=asc_sign)
    b = bav[transit_sign]
    return TransitJudgment(planet=planet, transit_sign=transit_sign, bindus=b,
                           quality=_quality(b), source=SOURCE)


def all_transits(natal_planet_signs: Mapping[str, int], transit_signs: Mapping[str, int], *,
                 asc_sign: int) -> dict[str, TransitJudgment]:
    """Gochara judgment for each transiting graha, from the natal ashtakavarga (BPHS-70).

    `natal_planet_signs` are the birth positions (build the BAV); `transit_signs` are where the grahas
    are on the transit date (1..12). Judged for the seven grahas the ashtakavarga covers.
    """
    out: dict[str, TransitJudgment] = {}
    for planet in _av.PLANETS:
        ts = transit_signs.get(planet)
        if ts is not None:
            out[planet] = transit_quality(planet, ts, natal_planet_signs, asc_sign=asc_sign)
    return out
