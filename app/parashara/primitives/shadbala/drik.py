"""Drik bala — aspectual strength (BPHS ch.27, sloka 19). The sixth and final bala.

    "Reduce one fourth of the Drishti Pinda if a planet has malefic aspects on it and add a fourth
     if it is aspected by a benefic. Super-add the entire aspect of Mercury and Jupiter to get the
     net strength of a planet." (BPHS-27:3609)

Each aspecting graha's Drishti Pinda is its graded rasi drishti on the target
(`graha_drishti.drishti_value`, ch.26 sl.2-5). Combined per sloka 19:

    drik = Σ (+drishti/4 for a benefic aspector, −drishti/4 for a malefic)
           + the FULL drishti of Mercury and Jupiter (the "super-add", over their quarter share).

The Merc/Jupiter super-add is the sloka's own clause — their aspects are held wholly benefic, so
their drishti is added entire in addition to the quarter every benefic contributes. Benefic/malefic
is the ch.3 natural nature (Moon by paksha, Mercury by company). **Drik bala is the one bala that
can be NEGATIVE** — a planet hemmed by malefic aspects loses aspectual strength.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.functional_nature import natural_benefic
from app.parashara.primitives.graha_drishti import drishti_value

SOURCE: Final[Citation] = Citation("BPHS-27", 3609)

_ASPECTORS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")   # nodes cast no drishti here


def _is_benefic(planet: str, planet_signs: Mapping[str, int], *, moon_waxing: bool) -> bool:
    sign = planet_signs.get(planet)
    companions = [p for p, s in planet_signs.items() if s == sign and p != planet]
    if planet == "Moon":
        return natural_benefic("Moon", moon_waxing=moon_waxing, companions=companions)
    if planet == "Mercury":
        return natural_benefic("Mercury", companions=companions)
    return natural_benefic(planet)


def drik_bala(target: str, planet_signs: Mapping[str, int], *, moon_waxing: bool) -> float:
    """Aspectual strength of `target` in virupas (may be negative), BPHS-27:19."""
    if target not in planet_signs:
        raise ValueError(f"{target} not in the chart")
    tsign = planet_signs[target]
    net = 0.0
    super_add = 0.0
    for aspector in _ASPECTORS:
        if aspector == target or aspector not in planet_signs:
            continue
        dv = drishti_value(aspector, planet_signs[aspector], tsign)
        if dv == 0.0:
            continue
        benefic = _is_benefic(aspector, planet_signs, moon_waxing=moon_waxing)
        net += dv / 4.0 if benefic else -dv / 4.0
        if aspector in ("Mercury", "Jupiter"):
            super_add += dv                          # "super-add the entire aspect"
    return net + super_add
