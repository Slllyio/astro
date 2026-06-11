"""H6 — disease-diagnosis lookups: planet -> organ / tridosha / season.

Three printed grids from Raman's 6th-house diagnostic apparatus (HTJAH-I):

  1. Planet -> organ (HTJAH-I:6437-6441): "The following planets govern the
     organs mentioned against them: The Sun - stomach; the Moon—heart;
     Mars—head; Mercury—chest; Jupiter—thighs; Saturn—legs, and the bones
     tibia and fibula; and Rahu—the feet." **Venus and Ketu are absent** from
     the printed allocation — ``organ_of`` returns ``None`` for them.
  2. Planet -> tridosha (HTJAH-I:6444-6458): "The Thridoshas are governed by
     different planets as follows" — 7 visible planets; nodes absent.
  3. Planet -> season of appearance (HTJAH-I:6462-6477): "The diseases will
     make their appearance during the seasons indicated by the planets."

Pure doctrine data returned as judge metadata — no scoring logic.

Data source: docs/raman_saab/methodology/house_06_ari.md (Disease Diagnosis
reference tables), verified against the corpus.

Usage:
    from app.raman_saab.doctrine.lookups.disease_map import (
        organ_of, tridosha_of, season_of
    )
    organ_of("Sun")        # -> "stomach"
    tridosha_of("Mars")    # -> "pitta (bile)"
    season_of("Venus")     # -> "Vasantha (spring)"
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping

from app.raman_saab.doctrine.sources import Citation


@dataclass(frozen=True)
class PlanetOrgan:
    """Organ governed by a planet (HTJAH-I:6437-6441)."""
    planet: str
    organ: str
    sources: tuple[Citation, ...]


@dataclass(frozen=True)
class PlanetTridosha:
    """Tridosha composition governed by a planet (HTJAH-I:6444-6458)."""
    planet: str
    tridosha: str
    sources: tuple[Citation, ...]


@dataclass(frozen=True)
class PlanetSeason:
    """Season in which the planet's diseases appear (HTJAH-I:6462-6477)."""
    planet: str
    season: str
    sources: tuple[Citation, ...]


_GRAHAS: Final[frozenset[str]] = frozenset((
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
    "Rahu", "Ketu",
))


def _i(*lines: int) -> tuple[Citation, ...]:
    return tuple(Citation("HTJAH-I", ln) for ln in lines)


# Planet -> organ (HTJAH-I:6439-6441). Venus and Ketu are NOT printed.
PLANET_ORGANS: Final[Mapping[str, PlanetOrgan]] = MappingProxyType({
    "Sun": PlanetOrgan("Sun", "stomach", _i(6439)),
    "Moon": PlanetOrgan("Moon", "heart", _i(6439)),
    "Mars": PlanetOrgan("Mars", "head", _i(6439)),
    "Mercury": PlanetOrgan("Mercury", "chest", _i(6439)),
    "Jupiter": PlanetOrgan("Jupiter", "thighs", _i(6439)),
    "Saturn": PlanetOrgan(
        "Saturn", "legs, and the bones tibia and fibula", _i(6439, 6441)),
    "Rahu": PlanetOrgan("Rahu", "feet", _i(6441)),
})

# Planet -> tridosha composition (HTJAH-I:6446-6458). 7 visible planets only.
PLANET_TRIDOSHAS: Final[Mapping[str, PlanetTridosha]] = MappingProxyType({
    "Sun": PlanetTridosha(
        "Sun", "mostly pitta (bile) and a little of vatha (wind)", _i(6446)),
    "Moon": PlanetTridosha(
        "Moon", "mostly vatha (wind) and a little of kapha (phlegm)", _i(6448)),
    "Mars": PlanetTridosha("Mars", "pitta (bile)", _i(6450)),
    "Mercury": PlanetTridosha(
        "Mercury",
        "mostly vatha (wind), a little of pitta (bile) and still less of "
        "kapha (phlegm)", _i(6452)),
    "Jupiter": PlanetTridosha(
        "Jupiter", "more of kapha (phlegm) and a little of vatha (wind)",
        _i(6454)),
    "Venus": PlanetTridosha(
        "Venus", "more of vatha (wind) and a little of kapha (phlegm)",
        _i(6456)),
    "Saturn": PlanetTridosha(
        "Saturn", "more of vatha (wind) and a little pitta (bile)", _i(6458)),
})

# Planet -> season of disease-appearance (HTJAH-I:6465-6477).
PLANET_SEASONS: Final[Mapping[str, PlanetSeason]] = MappingProxyType({
    "Venus": PlanetSeason("Venus", "Vasantha (spring)", _i(6467)),
    "Sun": PlanetSeason("Sun", "Grishma (summer)", _i(6469)),
    "Mars": PlanetSeason("Mars", "Grishma (summer)", _i(6469)),
    "Moon": PlanetSeason("Moon", "Varsha (rainy season)", _i(6471)),
    "Mercury": PlanetSeason("Mercury", "Sarat (autumn)", _i(6473)),
    "Jupiter": PlanetSeason("Jupiter", "Hemantha (winter)", _i(6475)),
    "Saturn": PlanetSeason("Saturn", "Sisira (winter)", _i(6477)),
})


def _checked(planet: str) -> str:
    if planet not in _GRAHAS:
        raise ValueError(f"unknown graha: {planet!r}")
    return planet


def organ_of(planet: str) -> str | None:
    """Organ governed by the planet (HTJAH-I:6439-6441).

    Returns None for Venus/Ketu (absent from the printed allocation);
    raises ValueError for non-grahas.
    """
    record = PLANET_ORGANS.get(_checked(planet))
    return record.organ if record is not None else None


def tridosha_of(planet: str) -> str | None:
    """Tridosha composition governed by the planet (HTJAH-I:6446-6458).

    Returns None for Rahu/Ketu (the printed list covers the 7 visible
    planets); raises ValueError for non-grahas.
    """
    record = PLANET_TRIDOSHAS.get(_checked(planet))
    return record.tridosha if record is not None else None


def season_of(planet: str) -> str | None:
    """Season in which the planet's diseases appear (HTJAH-I:6465-6477).

    Returns None for Rahu/Ketu (absent from the printed table); raises
    ValueError for non-grahas.
    """
    record = PLANET_SEASONS.get(_checked(planet))
    return record.season if record is not None else None
