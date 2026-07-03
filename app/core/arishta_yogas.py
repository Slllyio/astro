"""Arishta (early-affliction) combinations and their bhanga (cancellation).

Implements the cleanly computable subset of B. V. Raman's Balarishta
doctrine from **Hindu Predictive Astrology, Ch. XIV "Ayurdaya or
Longevity" (pp. 112-116)** as chart primitives. Each check cites the
numbered combination it encodes; combinations needing inputs the chart
cannot supply deterministically (sunrise offsets, dasa context) are left
to the compendium as ``partial``/``manual`` records — this module never
guesses.

All functions take whole-sign inputs consistent with the repo: planet
houses are 1..12 from the lagna, aspects are whole-sign graha drishti
(``app.core.drishti_argala``), benefic/malefic sets are the natural ones
shared with ``bhava_judge``.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping

from app.core.dignity import SIGN_RULERS
from app.core.drishti_argala import aspects_from_planet
from app.core.shodashavarga import compute_divisional_longitude

NATURAL_BENEFICS: frozenset[str] = frozenset({"Jupiter", "Venus", "Mercury"})
NATURAL_MALEFICS: frozenset[str] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
_BENEFIC_DREKKANA_LORDS = frozenset({"Mercury", "Jupiter", "Venus"})


@dataclasses.dataclass(frozen=True)
class ArishtaFinding:
    key: str        # stable id, e.g. "balarishta_2"
    citation: str   # HPA Ch. XIV combination number
    present: bool
    detail: str


def _aspected_by(house: int, planet_houses: Mapping[str, int], planets) -> list[str]:
    return [p for p in planets
            if p in planet_houses
            and house in aspects_from_planet(p, planet_houses[p])]


def malefics_in_last_navamsa(planet_lons: Mapping[str, float]) -> list[str]:
    """HPA Ch. XIV, Balarishta (1): malefics in the last navamsa of a sign."""
    out = []
    for planet in sorted(NATURAL_MALEFICS):
        if planet not in planet_lons:
            continue
        deg_in_sign = float(planet_lons[planet]) % 30.0
        if int(deg_in_sign // (30.0 / 9.0)) == 8:
            out.append(planet)
    return out


def moon_with_malefics_in_kendra(planet_houses: Mapping[str, int]) -> bool:
    """Balarishta (2): the Moon in a kendra with malefics (same house)."""
    moon = planet_houses.get("Moon")
    if moon not in (1, 4, 7, 10):
        return False
    return any(planet_houses.get(m) == moon for m in NATURAL_MALEFICS)


def moon_afflicted_in_7_8_12(planet_houses: Mapping[str, int]) -> bool:
    """Balarishta (3): Moon in 7/8/12 with malefics, unaspected by benefics."""
    moon = planet_houses.get("Moon")
    if moon not in (7, 8, 12):
        return False
    with_malefic = any(planet_houses.get(m) == moon for m in NATURAL_MALEFICS)
    benefic_aspect = _aspected_by(moon, planet_houses, NATURAL_BENEFICS)
    return with_malefic and not benefic_aspect


def malefics_in_2_6_8_12(planet_houses: Mapping[str, int]) -> list[str]:
    """Balarishta (5): malefics occupying the 2nd, 6th, 8th or 12th."""
    return [m for m in sorted(NATURAL_MALEFICS)
            if planet_houses.get(m) in (2, 6, 8, 12)]


def moon_in_benefic_drekkana(moon_lon: float) -> bool:
    """Bhanga (3)/(6): the Moon in a drekkana of Mercury, Jupiter or Venus."""
    d3_sign = int(compute_divisional_longitude(float(moon_lon), 3) % 360.0 // 30) + 1
    return SIGN_RULERS[d3_sign] in _BENEFIC_DREKKANA_LORDS


def jupiter_strong_in_lagna(planet_houses: Mapping[str, int],
                            strength: Mapping[str, float],
                            threshold: float = 0.5) -> bool:
    """Bhanga (1): Jupiter powerfully posited in the ascendant."""
    return planet_houses.get("Jupiter") == 1 and strength.get("Jupiter", 0.0) >= threshold


def lagna_lord_strong_with_benefic_aspect(
    lagna_lord: str,
    planet_houses: Mapping[str, int],
    strength: Mapping[str, float],
    threshold: float = 0.5,
) -> bool:
    """Bhanga (2): lagna lord powerfully situated with benefic aspects."""
    if strength.get(lagna_lord, 0.0) < threshold:
        return False
    house = planet_houses.get(lagna_lord)
    if house is None:
        return False
    others = NATURAL_BENEFICS - {lagna_lord}
    return bool(_aspected_by(house, planet_houses, others))


def full_moon_hemmed_by_benefics(planet_houses: Mapping[str, int],
                                 moon_waxing: bool,
                                 moon_sun_elongation: float) -> bool:
    """Bhanga (7): the (near-)Full Moon between two benefics (subha-kartari)."""
    if not moon_waxing or not 120.0 <= float(moon_sun_elongation) % 360.0 <= 240.0:
        return False
    moon = planet_houses.get("Moon")
    if moon is None:
        return False
    before = ((moon - 2) % 12) + 1
    after = (moon % 12) + 1
    benefic_in = lambda h: any(planet_houses.get(b) == h for b in NATURAL_BENEFICS)
    return benefic_in(before) and benefic_in(after)


def evaluate_arishta(
    planet_lons: Mapping[str, float],
    planet_houses: Mapping[str, int],
    lagna_lord: str,
    strength: Mapping[str, float],
    moon_waxing: bool,
) -> tuple[list[ArishtaFinding], list[ArishtaFinding]]:
    """All implemented checks -> (arishta findings, bhanga findings).

    Doctrine (HPA p. 116): afflictions with counteracting configurations
    mean suffering survived, not early death — consumers must weigh the
    two lists together, never the first alone.
    """
    elong = (float(planet_lons.get("Moon", 0.0)) - float(planet_lons.get("Sun", 0.0))) % 360.0
    last_nav = malefics_in_last_navamsa(planet_lons)
    m2 = moon_with_malefics_in_kendra(planet_houses)
    m3 = moon_afflicted_in_7_8_12(planet_houses)
    m5 = malefics_in_2_6_8_12(planet_houses)
    arishtas = [
        ArishtaFinding("balarishta_1", "HPA Ch.XIV Balarishta (1)", bool(last_nav),
                       f"malefics in last navamsa: {', '.join(last_nav) or 'none'}"),
        ArishtaFinding("balarishta_2", "HPA Ch.XIV Balarishta (2)", m2,
                       "Moon in kendra with malefics" if m2 else "not present"),
        ArishtaFinding("balarishta_3", "HPA Ch.XIV Balarishta (3)", m3,
                       "Moon in 7/8/12 with malefics, no benefic aspect" if m3 else "not present"),
        ArishtaFinding("balarishta_5", "HPA Ch.XIV Balarishta (5)", bool(m5),
                       f"malefics in 2/6/8/12: {', '.join(m5) or 'none'}"),
    ]
    b1 = jupiter_strong_in_lagna(planet_houses, strength)
    b2 = lagna_lord_strong_with_benefic_aspect(lagna_lord, planet_houses, strength)
    b3 = "Moon" in planet_lons and moon_in_benefic_drekkana(planet_lons["Moon"])
    b7 = full_moon_hemmed_by_benefics(planet_houses, moon_waxing, elong)
    bhangas = [
        ArishtaFinding("bhanga_1", "HPA Ch.XIV Bhanga (1)", b1,
                       "Jupiter strong in lagna" if b1 else "not present"),
        ArishtaFinding("bhanga_2", "HPA Ch.XIV Bhanga (2)", b2,
                       "lagna lord strong with benefic aspect" if b2 else "not present"),
        ArishtaFinding("bhanga_3", "HPA Ch.XIV Bhanga (3)/(6)", b3,
                       "Moon in benefic drekkana" if b3 else "not present"),
        ArishtaFinding("bhanga_7", "HPA Ch.XIV Bhanga (7)", b7,
                       "full Moon hemmed by benefics" if b7 else "not present"),
    ]
    return arishtas, bhangas
