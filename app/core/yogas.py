"""Vedic yoga detection on a natal D1 chart.

Detects the following yogas (v1 scope):
- Pancha Mahapurusha Yogas (Ruchaka, Bhadra, Hamsa, Malavya, Sasa)
- Gajakesari Yoga (Jupiter-Moon mutual kendra)
- Budha-Aditya Yoga (Sun-Mercury same-sign conjunction)

All sign indices are 1-indexed (1=Aries..12=Pisces) to match the project
convention used by `app.core.ephemeris_engine`.
"""
from __future__ import annotations

from typing import Literal, TypedDict

from app.core.ephemeris_engine import whole_sign_house


class Yoga(TypedDict):
    name: str                    # "Hamsa", "Gajakesari", etc.
    type: Literal["Pancha Mahapurusha", "Lunar", "Solar", "Other"]
    planets_involved: list[str]  # ["Jupiter"] or ["Sun", "Mercury"]
    description: str             # one-sentence summary


# Sign rulers (1-indexed signs: 1=Aries..12=Pisces).
SIGN_RULERS: dict[int, str] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun",
    6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter",
    10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

# Own signs of each planet (where it has rulership).
OWN_SIGNS: dict[str, set[int]] = {
    "Sun": {5},
    "Moon": {4},
    "Mars": {1, 8},
    "Mercury": {3, 6},
    "Jupiter": {9, 12},
    "Venus": {2, 7},
    "Saturn": {10, 11},
}

# Exaltation signs.
EXALTATION: dict[str, int] = {
    "Sun": 1,
    "Moon": 2,
    "Mars": 10,
    "Mercury": 6,
    "Jupiter": 4,
    "Venus": 12,
    "Saturn": 7,
}

# Kendra (angular) houses, counted from Lagna.
KENDRAS: set[int] = {1, 4, 7, 10}


def _planet_house(
    d1_chart: dict, ascendant_sign: int, planet_name: str
) -> int | None:
    """Return the whole-sign house (1..12) for a planet.

    Prefer a pre-computed `house` field on the planet entry; otherwise compute
    from `whole_sign_house(asc_sign, planet_sign)`. Returns None when the
    planet is absent from the chart or carries no `sign` field.
    """
    entry = d1_chart.get(planet_name)
    if not entry:
        return None
    house = entry.get("house")
    if isinstance(house, int) and 1 <= house <= 12:
        return house
    sign = entry.get("sign")
    if not isinstance(sign, int):
        return None
    return whole_sign_house(ascendant_sign, sign)


def _is_in_dignity(planet_name: str, sign: int) -> bool:
    """True when the planet is in its own sign or exaltation sign."""
    own = OWN_SIGNS.get(planet_name, set())
    exalt = EXALTATION.get(planet_name)
    return sign in own or sign == exalt


def _check_pmp(
    d1_chart: dict,
    ascendant_sign: int,
    planet: str,
    yoga_name: str,
    description: str,
) -> Yoga | None:
    """Generic Pancha Mahapurusha check for a single planet.

    Yoga forms when the planet is in own/exalted sign AND in a kendra
    from Lagna.
    """
    entry = d1_chart.get(planet)
    if not entry:
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int):
        return None
    if not _is_in_dignity(planet, sign):
        return None
    house = _planet_house(d1_chart, ascendant_sign, planet)
    if house not in KENDRAS:
        return None
    return Yoga(
        name=yoga_name,
        type="Pancha Mahapurusha",
        planets_involved=[planet],
        description=description,
    )


def _check_ruchaka(d1_chart: dict, ascendant_sign: int) -> Yoga | None:
    return _check_pmp(
        d1_chart,
        ascendant_sign,
        "Mars",
        "Ruchaka",
        "Mars in own/exalted sign occupying a kendra from Lagna, "
        "conferring courage, leadership, and martial strength.",
    )


def _check_bhadra(d1_chart: dict, ascendant_sign: int) -> Yoga | None:
    return _check_pmp(
        d1_chart,
        ascendant_sign,
        "Mercury",
        "Bhadra",
        "Mercury in own/exalted sign occupying a kendra from Lagna, "
        "conferring intellect, eloquence, and discriminative wisdom.",
    )


def _check_hamsa(d1_chart: dict, ascendant_sign: int) -> Yoga | None:
    return _check_pmp(
        d1_chart,
        ascendant_sign,
        "Jupiter",
        "Hamsa",
        "Jupiter in own/exalted sign occupying a kendra from Lagna, "
        "conferring wisdom, virtue, and spiritual grace.",
    )


def _check_malavya(d1_chart: dict, ascendant_sign: int) -> Yoga | None:
    return _check_pmp(
        d1_chart,
        ascendant_sign,
        "Venus",
        "Malavya",
        "Venus in own/exalted sign occupying a kendra from Lagna, "
        "conferring beauty, comforts, and refined sensibilities.",
    )


def _check_sasa(d1_chart: dict, ascendant_sign: int) -> Yoga | None:
    return _check_pmp(
        d1_chart,
        ascendant_sign,
        "Saturn",
        "Sasa",
        "Saturn in own/exalted sign occupying a kendra from Lagna, "
        "conferring authority, endurance, and disciplined achievement.",
    )


def _check_gajakesari(d1_chart: dict) -> Yoga | None:
    """Jupiter and Moon in mutual kendra (1, 4, 7, or 10 houses apart).

    Whole-sign math: ((moon_sign - jupiter_sign) % 12) in {0, 3, 6, 9}.
    """
    jup = d1_chart.get("Jupiter")
    moon = d1_chart.get("Moon")
    if not jup or not moon:
        return None
    j_sign = jup.get("sign")
    m_sign = moon.get("sign")
    if not isinstance(j_sign, int) or not isinstance(m_sign, int):
        return None
    if ((m_sign - j_sign) % 12) not in {0, 3, 6, 9}:
        return None
    return Yoga(
        name="Gajakesari",
        type="Lunar",
        planets_involved=["Jupiter", "Moon"],
        description=(
            "Jupiter and Moon in mutual kendra (1st, 4th, 7th, or 10th from "
            "each other), conferring fame, intelligence, and lasting "
            "reputation."
        ),
    )


def _check_budha_aditya(d1_chart: dict) -> Yoga | None:
    """Sun and Mercury conjunct in the same sign.

    v1 ignores combustion; some traditions count the yoga regardless.
    """
    sun = d1_chart.get("Sun")
    mercury = d1_chart.get("Mercury")
    if not sun or not mercury:
        return None
    s_sign = sun.get("sign")
    m_sign = mercury.get("sign")
    if not isinstance(s_sign, int) or not isinstance(m_sign, int):
        return None
    if s_sign != m_sign:
        return None
    return Yoga(
        name="Budha-Aditya",
        type="Solar",
        planets_involved=["Sun", "Mercury"],
        description=(
            "Sun and Mercury conjunct in the same sign, conferring "
            "intelligence, scholarship, and clarity of expression."
        ),
    )


def detect_yogas(d1_chart: dict, ascendant: dict) -> list[Yoga]:
    """Return all yogas present in the chart.

    Order: Pancha Mahapurusha first (alphabetical by yoga name), then
    Gajakesari, then Budha-Aditya.
    """
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must include 1..12 'sign', got {asc_sign!r}"
        )

    results: list[Yoga] = []

    # Pancha Mahapurusha — alphabetical: Bhadra, Hamsa, Malavya, Ruchaka, Sasa.
    pmp_checks = (
        _check_bhadra,
        _check_hamsa,
        _check_malavya,
        _check_ruchaka,
        _check_sasa,
    )
    for check in pmp_checks:
        yoga = check(d1_chart, asc_sign)
        if yoga is not None:
            results.append(yoga)

    gajakesari = _check_gajakesari(d1_chart)
    if gajakesari is not None:
        results.append(gajakesari)

    budha_aditya = _check_budha_aditya(d1_chart)
    if budha_aditya is not None:
        results.append(budha_aditya)

    return results
