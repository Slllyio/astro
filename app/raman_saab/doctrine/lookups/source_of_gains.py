"""H11 — source-of-gains lookups: planet-in-11th and 2nd-lord-placement variant.

Raman (HTJAH-II:14373-14374): "The source of gains is indicated by the nature
of planet in the 11th house." The seven-row planet table below carries that
block verbatim (HTJAH-II:14373-14386).

The 2nd-house variant (HTJAH-I:2503-2512): "Various combinations are given in
ancient astrological books to indicate the source and time of financial gains.
The position of the lord of the 2nd is important." Twelve rows keyed by the
house the 2nd lord occupies (cited by house_02_dhana.md rule 67).

Pure doctrine data returned as judge metadata — no scoring logic.

Data source: docs/raman_saab/methodology/house_11_labha.md (rules 24-30) and
house_02_dhana.md (rule 67), verified against the corpus.

Usage:
    from app.raman_saab.doctrine.lookups.source_of_gains import (
        source_of_gains, gains_via_second_lord
    )
    source_of_gains("Sun")        # -> "fortune as an inheritance"
    gains_via_second_lord(8)      # -> "legacies and enemies"
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping

from app.raman_saab.doctrine.sources import Citation


@dataclass(frozen=True)
class GainsChannel:
    """Income channel signified by a planet occupying the 11th house."""
    planet: str
    channel: str
    sources: tuple[Citation, ...]


@dataclass(frozen=True)
class SecondLordGains:
    """Source of gain when the 2nd lord occupies a given house (1-12)."""
    house: int
    channel: str
    sources: tuple[Citation, ...]


def _ii(*lines: int) -> tuple[Citation, ...]:
    return tuple(Citation("HTJAH-II", ln) for ln in lines)


def _i(*lines: int) -> tuple[Citation, ...]:
    return tuple(Citation("HTJAH-I", ln) for ln in lines)


# Planet in the 11th -> source of gains (HTJAH-II:14373-14386).
PLANET_IN_11TH_GAINS: Final[Mapping[str, GainsChannel]] = MappingProxyType({
    "Sun": GainsChannel("Sun", "fortune as an inheritance", _ii(14374, 14375)),
    "Moon": GainsChannel(
        "Moon",
        "mother, sea-products, pearls, milk, farms, fruit orchards and breweries",
        _ii(14375, 14376, 14377)),
    "Mars": GainsChannel(
        "Mars",
        "factories, litigation, lands and rentals and self-exertion",
        _ii(14377, 14381)),
    "Mercury": GainsChannel(
        "Mercury", "teaching, writing, friends or uncles", _ii(14382)),
    "Jupiter": GainsChannel(
        "Jupiter",
        "knowledge — scientific, religious, literary — and well-placed sons",
        _ii(14383, 14384)),
    "Venus": GainsChannel(
        "Venus", "dance, drama, cinema, fine arts, music and women",
        _ii(14384, 14385)),
    "Saturn": GainsChannel(
        "Saturn", "industries, labour and agriculture", _ii(14386)),
})

# 2nd lord placed in house N -> source of gain (HTJAH-I:2504-2512).
SECOND_LORD_HOUSE_GAINS: Final[Mapping[int, SecondLordGains]] = MappingProxyType({
    1: SecondLordGains(
        1, "own exertions, generally manual labour", _i(2504, 2505)),
    2: SecondLordGains(
        2, "riches acquired without effort, if the 1st and 2nd lords have "
           "exchanged houses", _i(2505, 2506)),
    3: SecondLordGains(
        3, "gain from travels and journeys (loss from relatives and brothers)",
        _i(2507)),
    4: SecondLordGains(4, "mother and inheritance", _i(2507, 2508)),
    5: SecondLordGains(
        5, "ancestral properties, speculation and chance games", _i(2508)),
    6: SecondLordGains(
        6, "broker's business (loss from relatives)", _i(2509)),
    7: SecondLordGains(
        7, "gain after marriage (but loss from sickness, etc., of wife)",
        _i(2509, 2510)),
    8: SecondLordGains(8, "legacies and enemies", _i(2510)),
    9: SecondLordGains(9, "father, voyages and shipping", _i(2510)),
    10: SecondLordGains(
        10, "profession, eminent people and government favours", _i(2511)),
    11: SecondLordGains(11, "different means", _i(2511, 2512)),
    12: SecondLordGains(
        12, "servants and unscrupulous means including illegal gratifications",
        _i(2512)),
})


def source_of_gains(planet: str) -> str:
    """Income channel for a planet in the 11th house (HTJAH-II:14373-14386).

    Only the 7 visible planets are printed; anything else raises ValueError.
    """
    record = PLANET_IN_11TH_GAINS.get(planet)
    if record is None:
        raise ValueError(f"no printed 11th-house income channel for {planet!r}")
    return record.channel


def gains_via_second_lord(house: int) -> str:
    """Source of gain for the 2nd lord placed in house 1-12 (HTJAH-I:2504-2512)."""
    record = SECOND_LORD_HOUSE_GAINS.get(house)
    if record is None:
        raise ValueError(f"house must be 1-12, got {house!r}")
    return record.channel
