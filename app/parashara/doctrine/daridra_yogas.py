"""Daridra (penury) yogas — BPHS ch.42, the crisp combinations, each a cited detector.

The honest counterpart to the ch.41 wealth yogas: Parashara's stated combinations for poverty. Only
the crisp, chart-computable ones are fired, each citing its own sloka (the maraka/conjunction
pattern — a specific stated combination per rule):

  sl.2 — the lagna lord in the 12th and the 12th lord in the lagna, touched by a maraka.
  sl.3 — the lagna lord in the 6th and the 6th lord in the lagna, touched by a maraka.
  sl.4 — the ascendant or the Moon conjunct Ketu, with the lagna lord in the 8th.
  sl.6 — the lagna lord conjunct a 6th/8th/12th lord or Saturn, devoid of benefic aspect.

DEFERRED (not faked): the compound/dignity-laden verses (sl.5 2nd-lord enemy/debilitation; sl.7-15
using navamsa-lord, Atmakaraka frames, "deposed" lords) — legitimate but each needs a chain of soft
conditions; they remain in `yoga_catalogue`. "Touched by a maraka" = a maraka planet (ch.44) conjunct
or aspecting the house; conjunction is same-sign; aspects use graha drishti.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.maraka import maraka_planets
from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.graha_drishti import aspects_sign
from app.parashara.primitives.relationships import SIGN_LORDS

_WORK: Final[str] = "BPHS-42"
SOURCE: Final[Citation] = Citation(_WORK, 27)          # sl.1 header
_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})


@dataclass(frozen=True)
class DaridraYoga:
    name: str
    reason: str
    source: Citation


def _house_sign(asc_sign: int, house: int) -> int:
    return ((asc_sign + house - 2) % 12) + 1


def detect(longitudes: Mapping[str, float], *, asc_sign: int) -> tuple[DaridraYoga, ...]:
    """Every crisp ch.42 penury yoga present, each cited to its own sloka."""
    signs = {p: int(l % 360.0 // 30) + 1 for p, l in longitudes.items()}

    def house_of(planet: str) -> int:
        return ((signs[planet] - asc_sign) % 12) + 1 if planet in signs else 0

    def lord(house: int) -> str:
        return SIGN_LORDS[_house_sign(asc_sign, house)]

    marakas = {m.planet for m in maraka_planets(signs, asc_sign=asc_sign)}

    def maraka_touches_lagna() -> bool:
        return any(signs.get(m) == asc_sign or aspects_sign(m, signs[m], asc_sign)
                   for m in marakas if m in signs)

    asc_lord = lord(1)
    out: list[DaridraYoga] = []

    # sl.2 — lagna lord in 12th, 12th lord in lagna, touched by a maraka
    if (house_of(asc_lord) == 12 and house_of(lord(12)) == 1 and maraka_touches_lagna()):
        out.append(DaridraYoga("Daridra (lagna/12th lord exchange with maraka)",
                               "the lagna lord in the 12th and the 12th lord in the lagna, touched by "
                               "a maraka", Citation(_WORK, 33)))

    # sl.3 — lagna lord in 6th, 6th lord in lagna, touched by a maraka
    if (house_of(asc_lord) == 6 and house_of(lord(6)) == 1 and maraka_touches_lagna()):
        out.append(DaridraYoga("Daridra (lagna/6th lord exchange with maraka)",
                               "the lagna lord in the 6th and the 6th lord in the lagna, touched by a "
                               "maraka", Citation(_WORK, 42)))

    # sl.4 — ascendant or Moon conjunct Ketu, lagna lord in the 8th
    ketu_sign = signs.get("Ketu")
    if (ketu_sign is not None and (ketu_sign == asc_sign or ketu_sign == signs.get("Moon"))
            and house_of(asc_lord) == 8):
        out.append(DaridraYoga("Daridra (Ketu on lagna/Moon, lagna lord in the 8th)",
                               "the ascendant or the Moon conjunct Ketu while the lagna lord is in "
                               "the 8th", Citation(_WORK, 50)))

    # sl.6 — lagna lord conjunct a 6/8/12 lord or Saturn, and devoid of benefic aspect
    dusthana_lords = {lord(h) for h in (6, 8, 12)} - {asc_lord}
    companions = {p for p, s in signs.items() if s == signs.get(asc_lord) and p != asc_lord}
    with_evil = bool(companions & dusthana_lords) or ("Saturn" in companions)
    benefic_aspect = any(b in signs and aspects_sign(b, signs[b], signs[asc_lord])
                         for b in _BENEFICS if b != asc_lord)
    if asc_lord in signs and with_evil and not benefic_aspect:
        out.append(DaridraYoga("Daridra (lagna lord with an evil lord, no benefic aspect)",
                               "the lagna lord conjunct a 6th/8th/12th lord or Saturn and without a "
                               "benefic's aspect", Citation(_WORK, 70)))

    return tuple(out)
