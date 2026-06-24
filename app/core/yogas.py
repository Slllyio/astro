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

from app.core.dignity import SIGN_RULERS
from app.core.ephemeris_engine import (
    calculate_divisional_longitude,
    whole_sign_house,
)
from app.core.shadbala import sthana_bala
from app.core.yoga_types import YogaInstance


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


# --------------------------------------------------------------------------- #
# Vipareeta Harsha Raj Yoga  (Phase 0 — structural causal model wedge)        #
# --------------------------------------------------------------------------- #

# Phase-0 Sthana-bala ceiling (60+45+30+60+15 virupa) — used to normalise
# strength into [0, 1] before consumption by the YSH-CM. Phase 1 raises
# this ceiling to full Shadbala (~390 virupa per BPHS).
_MAX_STHANA_BALA_PHASE_0: float = 60.0 + 45.0 + 30.0 + 60.0 + 15.0


def _sixth_lord(ascendant_sign: int) -> str:
    """Return the planet ruling the 6th sign-from-Lagna."""
    sixth_sign = ((ascendant_sign - 1 + 5) % 12) + 1
    return SIGN_RULERS[sixth_sign]


def _lord_of_house(ascendant_sign: int, house: int) -> str:
    """Return the planet ruling the (house)-th sign-from-Lagna.

    1-indexed houses: house=1 → ascendant sign's ruler; house=2 → 2nd sign; etc.
    """
    house_sign = ((ascendant_sign - 1 + house - 1) % 12) + 1
    return SIGN_RULERS[house_sign]


def _navamsa_sign(longitude: float) -> int:
    """Return the 1-indexed D9 (Navamsa) sign for an ecliptic longitude."""
    d9_lon = calculate_divisional_longitude(longitude, divisor=9)
    return int(d9_lon // 30) + 1


# Houses considered kendra (1, 4, 7, 10) and trikona (1, 5, 9). The
# union — {1, 4, 5, 7, 9, 10} — is the "benefic-lord" set used by the
# Vipareeta "alone in dusthana" gate (BPHS 36 + Phaladeepika Ch. 7).
_KENDRA_TRIKONA_HOUSES: frozenset[int] = frozenset({1, 4, 5, 7, 9, 10})


def _kendra_trikona_lords(asc_sign: int) -> set[str]:
    """Return the planets that rule any kendra or trikona house from Lagna.

    Used by the Vipareeta "alone in dusthana" gate: if the 6th lord
    placed in a dusthana shares its sign with any of these lords, the
    yoga is contaminated and does NOT fire (classical condition).
    """
    return {
        SIGN_RULERS[((asc_sign - 1 + h - 1) % 12) + 1]
        for h in _KENDRA_TRIKONA_HOUSES
    }


def detect_vipareeta_harsha(
    chart: dict, ascendant: dict
) -> YogaInstance | None:
    """Vipareeta Harsha Raja Yoga — 6th-lord in 6/8/12 from Lagna, alone.

    Classical rule (BPHS 36 + Mantreshwara *Phaladeepika* Ch. 7):
        The 6th-lord placed in another dusthana (6/8/12) confers Harsha —
        but ONLY when alone, i.e. NOT conjunct any lord of a kendra or
        trikona house (1/4/5/7/9/10). A contaminating benefic-lord
        conjunction destroys the "two negatives cancel" mechanism.

    Strength formula (INVERTED for Vipareeta — Phase-1 fix):
        Classical: weaker 6L → stronger Vipareeta outcome (the lord is
        incapable of delivering 6th-house results, so the inversion
        principle takes over). Empirically confirmed by the Round-9 wedge
        audit: low-Sthana-bala yoga-havers had 39.0% career-event rate vs
        29.8% for high-Sthana-bala — a 9.2pp swing.

        Therefore:  strength = 1 - (sthana_bala / max_ceiling[lord])
        Range: [0, 1]. 1.0 = deeply debilitated 6L in dusthana (strongest
        Harsha); 0.0 = exalted/own-sign 6L in dusthana (weakest Harsha,
        but still detected — the lord still delivers 6th results).

    Returns ``None`` when:
        - The chart lacks the 6L planet entry.
        - The 6L is not in 6/8/12.
        - The 6L is conjunct any kendra/trikona lord (benefic contamination).
    """
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )

    sixth_lord = _sixth_lord(asc_sign)
    lord_entry = chart.get(sixth_lord)
    if not lord_entry:
        return None

    lord_sign = lord_entry.get("sign")
    if not isinstance(lord_sign, int) or not (1 <= lord_sign <= 12):
        return None

    house_of_lord = whole_sign_house(asc_sign, lord_sign)
    if house_of_lord not in {6, 8, 12}:
        return None

    # Phase-1 audit fix: "alone in dusthana" gate. Reject the yoga if
    # any kendra/trikona LORD other than the 6L itself sits in the same
    # sign as the 6L. (The 6L being in its own 6th-house-sign is fine —
    # the rule is about OTHER benefic lords contaminating.)
    benefic_lords = _kendra_trikona_lords(asc_sign) - {sixth_lord}
    for other_lord in benefic_lords:
        other_entry = chart.get(other_lord)
        if not other_entry:
            continue
        other_sign = other_entry.get("sign")
        if isinstance(other_sign, int) and other_sign == lord_sign:
            # Benefic-lord contamination: yoga destroyed per Phaladeepika 7.
            return None

    longitude = lord_entry.get("longitude")
    if not isinstance(longitude, (int, float)):
        # Fallback to mid-sign for fixtures that don't carry longitude.
        longitude = (lord_sign - 1) * 30.0 + 15.0
    longitude = float(longitude)

    d9_sign = _navamsa_sign(longitude)
    sthana = sthana_bala(
        sixth_lord,
        longitude=longitude,
        d1_sign=lord_sign,
        d9_sign=d9_sign,
        house=house_of_lord,
    )
    # Phase-1 audit fix: Vipareeta strength is INVERTED. A weaker 6L
    # cannot deliver malefic 6th-house results, so the Harsha mechanism
    # fires more strongly. See module docstring + docs/bphs_reference.md.
    strength_raw = sthana["total"] / _MAX_STHANA_BALA_PHASE_0
    strength = max(0.0, min(1.0, 1.0 - strength_raw))

    # houses_activated: structural label (6 = the house ruled) + actual
    # placement house. Dedupe and sort for canonical ordering.
    houses = tuple(sorted({6, house_of_lord}))

    return YogaInstance(
        name="Vipareeta Harsha",
        category="vipareeta_raj",
        participants=(sixth_lord,),
        houses_activated=houses,
        promise_axis="career_via_adversity",
        lords_involved=(sixth_lord,),
        strength=strength,
    )


# --------------------------------------------------------------------------- #
# Vipareeta Sarala (8L in 6/8/12) and Vimala (12L in 6/8/12) — Phase 3B       #
# --------------------------------------------------------------------------- #

def _detect_vipareeta_dusthana(
    chart: dict,
    ascendant: dict,
    *,
    dusthana_house: int,
    yoga_name: str,
    promise_axis: str,
) -> YogaInstance | None:
    """Generic Vipareeta-detector for Harsha (6L), Sarala (8L), Vimala (12L).

    Same classical rule as Harsha (BPHS 36 + Phaladeepika Ch. 7): the
    dusthana lord placed in another dusthana, ALONE — not conjunct any
    kendra/trikona lord. Strength inverted (weak lord → strong yoga).
    """
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )
    if dusthana_house not in {6, 8, 12}:
        raise ValueError(
            f"dusthana_house must be 6, 8, or 12; got {dusthana_house!r}"
        )

    dusthana_lord = _lord_of_house(asc_sign, dusthana_house)
    lord_entry = chart.get(dusthana_lord)
    if not lord_entry:
        return None
    lord_sign = lord_entry.get("sign")
    if not isinstance(lord_sign, int) or not (1 <= lord_sign <= 12):
        return None

    house_of_lord = whole_sign_house(asc_sign, lord_sign)
    if house_of_lord not in {6, 8, 12}:
        return None

    # Alone-in-dusthana gate: no kendra/trikona lord co-located with the
    # dusthana lord (the dusthana lord itself is excluded — its own
    # rulership doesn't disqualify the yoga).
    benefic_lords = _kendra_trikona_lords(asc_sign) - {dusthana_lord}
    for other_lord in benefic_lords:
        other_entry = chart.get(other_lord)
        if not other_entry:
            continue
        other_sign = other_entry.get("sign")
        if isinstance(other_sign, int) and other_sign == lord_sign:
            return None

    longitude = lord_entry.get("longitude")
    if not isinstance(longitude, (int, float)):
        longitude = (lord_sign - 1) * 30.0 + 15.0
    longitude = float(longitude)

    d9_sign = _navamsa_sign(longitude)
    sthana = sthana_bala(
        dusthana_lord,
        longitude=longitude,
        d1_sign=lord_sign,
        d9_sign=d9_sign,
        house=house_of_lord,
    )
    # Vipareeta inversion (BPHS 36 + Phaladeepika 6.39).
    strength_raw = sthana["total"] / _MAX_STHANA_BALA_PHASE_0
    strength = max(0.0, min(1.0, 1.0 - strength_raw))

    houses = tuple(sorted({dusthana_house, house_of_lord}))

    return YogaInstance(
        name=yoga_name,
        category="vipareeta_raj",
        participants=(dusthana_lord,),
        houses_activated=houses,
        promise_axis=promise_axis,
        lords_involved=(dusthana_lord,),
        strength=strength,
    )


def detect_vipareeta_sarala(
    chart: dict, ascendant: dict
) -> YogaInstance | None:
    """Vipareeta Sarala Raja Yoga — 8L placed in 6/8/12 from Lagna, alone.

    Sarala (literally "easy / straightforward") confers longevity,
    overcoming danger, and unexpected gains through transformation.
    BPHS 36 sibling to Harsha (6L); same alone-in-dusthana rule and
    same inverted strength formula.
    """
    return _detect_vipareeta_dusthana(
        chart, ascendant,
        dusthana_house=8,
        yoga_name="Vipareeta Sarala",
        promise_axis="longevity_via_transformation",
    )


def detect_vipareeta_vimala(
    chart: dict, ascendant: dict
) -> YogaInstance | None:
    """Vipareeta Vimala Raja Yoga — 12L placed in 6/8/12 from Lagna, alone.

    Vimala ("pure / spotless") confers wealth through prudence,
    spiritual gain, and renunciation of loss. BPHS 36 sibling to Harsha
    and Sarala; same alone-in-dusthana rule and inverted strength.
    """
    return _detect_vipareeta_dusthana(
        chart, ascendant,
        dusthana_house=12,
        yoga_name="Vipareeta Vimala",
        promise_axis="prudent_wealth_via_loss",
    )


# --------------------------------------------------------------------------- #
# Moon-based yogas: Sunapha, Anapha, Durudhura, Kemadruma — Phase 3B          #
# --------------------------------------------------------------------------- #
#
# Per BPHS 73-74 (Chandra-yoga-adhyaya):
#   Sunapha:   any planet (excluding Sun, Rahu, Ketu) in the 2nd house
#              from the Moon. Confers self-earned wealth.
#   Anapha:    same planets in the 12th from the Moon. Confers fame and
#              social standing.
#   Durudhura: BOTH 2nd and 12th from Moon are occupied. Confers
#              comforts and a strong support network.
#   Kemadruma: NONE of 2nd, 12th from Moon, AND no planet in the same
#              sign as the Moon (conjunction-style support also absent).
#              Confers poverty / isolation. Phase-3B implements the basic
#              detection; classical cancellation rules (Moon in kendra
#              from Lagna, benefic aspect on Moon, etc.) are Phase 3B.2.

# Planets eligible to form Sunapha/Anapha/Durudhura. Sun, Rahu, Ketu are
# excluded per BPHS 73 (the Sun's overwhelming light precludes other
# subtler influence; nodes are bodyless points).
_MOON_YOGA_PLANETS: frozenset[str] = frozenset(
    {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
)


def _planets_in_sign_from_moon(
    chart: dict, moon_sign: int, offset_houses: int
) -> tuple[str, ...]:
    """Return the (eligible) planets occupying the sign at ``offset_houses``
    from the Moon. ``offset_houses=1`` means 2nd house (1 step ahead);
    ``offset_houses=-1`` means 12th house (1 step behind).
    """
    target_sign = ((moon_sign - 1 + offset_houses) % 12) + 1
    found: list[str] = []
    for planet in _MOON_YOGA_PLANETS:
        entry = chart.get(planet)
        if not entry:
            continue
        p_sign = entry.get("sign")
        if isinstance(p_sign, int) and p_sign == target_sign:
            found.append(planet)
    return tuple(found)


def detect_sunapha(chart: dict, ascendant: dict) -> YogaInstance | None:
    """Sunapha Yoga — at least one planet (other than Sun/Rahu/Ketu) in
    the 2nd house from the Moon. BPHS 73.1.

    Confers self-acquired wealth, intelligence, and independence.
    """
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )
    moon_entry = chart.get("Moon")
    if not moon_entry:
        return None
    moon_sign = moon_entry.get("sign")
    if not isinstance(moon_sign, int):
        return None
    participants = _planets_in_sign_from_moon(chart, moon_sign, offset_houses=1)
    if not participants:
        return None
    # Strength = average normalised Sthana-bala of participants (no
    # inversion — straight benefic interpretation).
    strengths = []
    for p in participants:
        p_entry = chart[p]
        p_lon = p_entry.get("longitude", (p_entry["sign"] - 1) * 30.0 + 15.0)
        p_d9 = _navamsa_sign(p_lon)
        sb = sthana_bala(
            p, longitude=p_lon, d1_sign=p_entry["sign"],
            d9_sign=p_d9, house=whole_sign_house(asc_sign, p_entry["sign"]),
        )
        strengths.append(sb["total"] / _MAX_STHANA_BALA_PHASE_0)
    avg = sum(strengths) / len(strengths)
    strength = max(0.0, min(1.0, avg))

    moon_house = whole_sign_house(asc_sign, moon_sign)
    second_from_moon_house = ((moon_house - 1 + 1) % 12) + 1
    return YogaInstance(
        name="Sunapha",
        category="moon",
        participants=participants,
        houses_activated=(moon_house, second_from_moon_house),
        promise_axis="self_acquired_wealth",
        lords_involved=participants,
        strength=strength,
    )


def detect_anapha(chart: dict, ascendant: dict) -> YogaInstance | None:
    """Anapha Yoga — at least one planet (other than Sun/Rahu/Ketu) in
    the 12th house from the Moon. BPHS 73.2.

    Confers fame, social standing, and personal magnetism.
    """
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )
    moon_entry = chart.get("Moon")
    if not moon_entry:
        return None
    moon_sign = moon_entry.get("sign")
    if not isinstance(moon_sign, int):
        return None
    participants = _planets_in_sign_from_moon(chart, moon_sign, offset_houses=-1)
    if not participants:
        return None
    strengths = []
    for p in participants:
        p_entry = chart[p]
        p_lon = p_entry.get("longitude", (p_entry["sign"] - 1) * 30.0 + 15.0)
        p_d9 = _navamsa_sign(p_lon)
        sb = sthana_bala(
            p, longitude=p_lon, d1_sign=p_entry["sign"],
            d9_sign=p_d9, house=whole_sign_house(asc_sign, p_entry["sign"]),
        )
        strengths.append(sb["total"] / _MAX_STHANA_BALA_PHASE_0)
    avg = sum(strengths) / len(strengths)
    strength = max(0.0, min(1.0, avg))

    moon_house = whole_sign_house(asc_sign, moon_sign)
    twelfth_from_moon_house = ((moon_house - 1 - 1) % 12) + 1
    return YogaInstance(
        name="Anapha",
        category="moon",
        participants=participants,
        houses_activated=(moon_house, twelfth_from_moon_house),
        promise_axis="fame_and_social_standing",
        lords_involved=participants,
        strength=strength,
    )


def detect_durudhura(chart: dict, ascendant: dict) -> YogaInstance | None:
    """Durudhura Yoga — planets in BOTH 2nd and 12th from Moon. BPHS 73.3.

    Confers comforts, conveyances, and a strong support network.
    Composed from the simultaneous presence of Sunapha + Anapha
    participants (returned as a single yoga to avoid double-counting).
    """
    sun = detect_sunapha(chart, ascendant)
    ana = detect_anapha(chart, ascendant)
    if sun is None or ana is None:
        return None
    # Union of participants; strength = mean of the two component strengths.
    participants = tuple(sorted(set(sun.participants) | set(ana.participants)))
    strength = max(0.0, min(1.0, (sun.strength + ana.strength) / 2.0))
    houses = tuple(sorted(set(sun.houses_activated) | set(ana.houses_activated)))
    return YogaInstance(
        name="Durudhura",
        category="moon",
        participants=participants,
        houses_activated=houses,
        promise_axis="comforts_and_support",
        lords_involved=participants,
        strength=strength,
    )


def detect_kemadruma(chart: dict, ascendant: dict) -> YogaInstance | None:
    """Kemadruma Yoga — Moon isolated: no planet (other than Sun/Rahu/Ketu)
    in 2nd, 12th, or same sign as the Moon. BPHS 73.4.

    Affliction yoga (poverty / isolation). Phase 3B implements the basic
    detection; classical cancellation rules (Moon in kendra from Lagna,
    benefic aspect on Moon, Moon in own/exalted sign) are Phase 3B.2.
    Returned strength represents the strength of the AFFLICTION (lower
    Moon-bala = stronger Kemadruma harm).
    """
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )
    moon_entry = chart.get("Moon")
    if not moon_entry:
        return None
    moon_sign = moon_entry.get("sign")
    if not isinstance(moon_sign, int):
        return None

    second = _planets_in_sign_from_moon(chart, moon_sign, offset_houses=1)
    twelfth = _planets_in_sign_from_moon(chart, moon_sign, offset_houses=-1)
    # Also check for planets conjunct Moon (same sign) — classical
    # interpretation says conjunction also relieves Kemadruma.
    conjuncts = tuple(
        p for p in _MOON_YOGA_PLANETS
        if chart.get(p, {}).get("sign") == moon_sign
    )
    if second or twelfth or conjuncts:
        return None

    # Strength of affliction = inverse Moon Sthana-bala (weak Moon → strong
    # Kemadruma effect, classical interpretation).
    moon_lon = moon_entry.get("longitude", (moon_sign - 1) * 30.0 + 15.0)
    moon_d9 = _navamsa_sign(moon_lon)
    sb = sthana_bala(
        "Moon", longitude=moon_lon, d1_sign=moon_sign,
        d9_sign=moon_d9, house=whole_sign_house(asc_sign, moon_sign),
    )
    affliction_strength = max(0.0, min(1.0, 1.0 - sb["total"] / _MAX_STHANA_BALA_PHASE_0))

    moon_house = whole_sign_house(asc_sign, moon_sign)
    second_house = ((moon_house - 1 + 1) % 12) + 1
    twelfth_house = ((moon_house - 1 - 1) % 12) + 1
    return YogaInstance(
        name="Kemadruma",
        category="moon",
        participants=("Moon",),
        houses_activated=tuple(sorted({moon_house, second_house, twelfth_house})),
        promise_axis="affliction_poverty_isolation",
        lords_involved=("Moon",),
        strength=affliction_strength,
    )


# --------------------------------------------------------------------------- #
# Pancha Mahapurusha as YogaInstance — Phase 3B upgrade                       #
# --------------------------------------------------------------------------- #
#
# The existing ``detect_yogas`` returns the legacy ``Yoga`` TypedDict for
# backward compat with chart-rendering code. Phase-3B introduces parallel
# detectors that return the structured ``YogaInstance`` carrying continuous
# strength — what the YSH-CM model in Phase 6 will consume.
#
# Per BPHS 36.1-6 each star-planet's PMP fires when it sits in:
#   own sign OR exaltation sign  AND  in a kendra from Lagna.
# Strength is NOT inverted (these are positive yogas: strong placement →
# strong yoga).

_PMP_DEFINITIONS: tuple[tuple[str, str, str], ...] = (
    # (planet, yoga_name, promise_axis)
    ("Mars",    "Ruchaka",  "courage_leadership_martial_strength"),
    ("Mercury", "Bhadra",   "intellect_eloquence_discrimination"),
    ("Jupiter", "Hamsa",    "wisdom_virtue_spiritual_grace"),
    ("Venus",   "Malavya",  "beauty_comforts_refinement"),
    ("Saturn",  "Sasa",     "authority_endurance_disciplined_achievement"),
)


def _detect_pmp_instance(
    chart: dict, ascendant: dict, planet: str, yoga_name: str, promise_axis: str
) -> YogaInstance | None:
    """Generic Pancha Mahapurusha detector returning YogaInstance.

    Shares the classical formation rule (own/exalted + kendra) with the
    legacy ``_check_pmp`` but emits the structured Phase-3B output.
    """
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )
    entry = chart.get(planet)
    if not entry:
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int):
        return None
    if not _is_in_dignity(planet, sign):
        return None
    house = _planet_house(chart, asc_sign, planet)
    if house not in KENDRAS:
        return None

    longitude = entry.get("longitude")
    if not isinstance(longitude, (int, float)):
        longitude = (sign - 1) * 30.0 + 15.0
    longitude = float(longitude)
    d9_sign = _navamsa_sign(longitude)
    sthana = sthana_bala(
        planet, longitude=longitude, d1_sign=sign,
        d9_sign=d9_sign, house=house,
    )
    strength = max(0.0, min(1.0, sthana["total"] / _MAX_STHANA_BALA_PHASE_0))

    return YogaInstance(
        name=yoga_name,
        category="mahapurusha",
        participants=(planet,),
        houses_activated=(house,),
        promise_axis=promise_axis,
        lords_involved=(planet,),
        strength=strength,
    )


def detect_pancha_mahapurusha(
    chart: dict, ascendant: dict
) -> list[YogaInstance]:
    """Return all Pancha Mahapurusha yogas present as YogaInstances.

    BPHS 36.1-6 — five star-planet yogas, returned in canonical order
    (Ruchaka, Bhadra, Hamsa, Malavya, Sasa). Empty list when none fire.
    """
    results: list[YogaInstance] = []
    for planet, yoga_name, promise_axis in _PMP_DEFINITIONS:
        inst = _detect_pmp_instance(
            chart, ascendant, planet, yoga_name, promise_axis
        )
        if inst is not None:
            results.append(inst)
    return results


# --------------------------------------------------------------------------- #
# Gajakesari + Budha-Aditya as YogaInstance — Phase 3B upgrade                #
# --------------------------------------------------------------------------- #

def detect_gajakesari_instance(
    chart: dict, ascendant: dict
) -> YogaInstance | None:
    """Gajakesari — Jupiter and Moon in mutual kendra (1st, 4th, 7th, 10th
    from each other). BPHS 36.10. Strength = average of both planets'
    Sthana-bala fractions."""
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )
    jup = chart.get("Jupiter")
    moon = chart.get("Moon")
    if not jup or not moon:
        return None
    j_sign = jup.get("sign")
    m_sign = moon.get("sign")
    if not isinstance(j_sign, int) or not isinstance(m_sign, int):
        return None
    if ((m_sign - j_sign) % 12) not in {0, 3, 6, 9}:
        return None

    strengths = []
    for planet, entry in [("Jupiter", jup), ("Moon", moon)]:
        lon = entry.get("longitude", (entry["sign"] - 1) * 30.0 + 15.0)
        d9 = _navamsa_sign(lon)
        sb = sthana_bala(
            planet, longitude=lon, d1_sign=entry["sign"],
            d9_sign=d9, house=whole_sign_house(asc_sign, entry["sign"]),
        )
        strengths.append(sb["total"] / _MAX_STHANA_BALA_PHASE_0)
    strength = max(0.0, min(1.0, sum(strengths) / 2.0))

    j_house = whole_sign_house(asc_sign, j_sign)
    m_house = whole_sign_house(asc_sign, m_sign)
    return YogaInstance(
        name="Gajakesari",
        category="lunar",
        participants=("Jupiter", "Moon"),
        houses_activated=tuple(sorted({j_house, m_house})),
        promise_axis="fame_intelligence_lasting_reputation",
        lords_involved=("Jupiter", "Moon"),
        strength=strength,
    )


def detect_budha_aditya_instance(
    chart: dict, ascendant: dict
) -> YogaInstance | None:
    """Budha-Aditya — Sun and Mercury conjunct (same sign). BPHS 36.7.
    Phase-3B note: Phase 2b will optionally add the combustion-aware
    classical filter (some traditions exclude combust Mercury cases)."""
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )
    sun = chart.get("Sun")
    mercury = chart.get("Mercury")
    if not sun or not mercury:
        return None
    s_sign = sun.get("sign")
    m_sign = mercury.get("sign")
    if not isinstance(s_sign, int) or not isinstance(m_sign, int):
        return None
    if s_sign != m_sign:
        return None

    strengths = []
    for planet, entry in [("Sun", sun), ("Mercury", mercury)]:
        lon = entry.get("longitude", (entry["sign"] - 1) * 30.0 + 15.0)
        d9 = _navamsa_sign(lon)
        sb = sthana_bala(
            planet, longitude=lon, d1_sign=entry["sign"],
            d9_sign=d9, house=whole_sign_house(asc_sign, entry["sign"]),
        )
        strengths.append(sb["total"] / _MAX_STHANA_BALA_PHASE_0)
    strength = max(0.0, min(1.0, sum(strengths) / 2.0))

    house = whole_sign_house(asc_sign, s_sign)
    return YogaInstance(
        name="Budha-Aditya",
        category="solar",
        participants=("Sun", "Mercury"),
        houses_activated=(house,),
        promise_axis="intelligence_scholarship_clarity",
        lords_involved=("Sun", "Mercury"),
        strength=strength,
    )


# --------------------------------------------------------------------------- #
# Raj Yoga + Dhana Yoga (ascendant-conditioned) — Phase 3B                    #
# --------------------------------------------------------------------------- #
#
# Raj Yoga (BPHS 36 family): a kendra-house lord (1/4/7/10) conjunct a
# trikona-house lord (1/5/9). The 1st-house lord is BOTH kendra and trikona,
# so we exclude self-pair matches. Phase-3B detector returns at most ONE
# YogaInstance per chart (the strongest kendra-trikona conjunction); a
# multi-Raj-Yoga catalog can be Phase 3B.2.
#
# Dhana Yoga (BPHS 41 family): 2nd lord + 11th lord conjunction (wealth-
# producing). One of many Dhana-yoga variants; canonical and most-cited.

def _conjunction_in_sign(
    chart: dict, planet_a: str, planet_b: str
) -> int | None:
    """Return the shared sign if planet_a and planet_b are in same sign,
    else None. Treats nodes/missing planets as "not present"."""
    if planet_a == planet_b:
        return None  # need distinct planets for a yoga
    a = chart.get(planet_a)
    b = chart.get(planet_b)
    if not a or not b:
        return None
    sa = a.get("sign")
    sb = b.get("sign")
    if not isinstance(sa, int) or not isinstance(sb, int):
        return None
    return sa if sa == sb else None


def detect_raja_yoga(
    chart: dict, ascendant: dict
) -> YogaInstance | None:
    """Raj Yoga: kendra-lord + trikona-lord conjunct in same sign.

    Ascendant-conditioned. Tries all kendra-trikona lord pairs and
    returns the one with the highest combined Sthana-bala. Phase 3B
    emits a single Raj-Yoga slot per chart; a multi-yoga catalog with
    every pair separately can be Phase 3B.2.

    Confers political success, leadership, and royal patronage in the
    classical reading. Both lords' strengths are averaged into the
    yoga's strength score.
    """
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )

    # Lords for this ascendant. The set ignores duplicate rulerships
    # (Mars rules 1 AND 8 for Aries; we keep its kendra/trikona role
    # cleanly separated).
    kendra_lords = {
        _lord_of_house(asc_sign, h) for h in (1, 4, 7, 10)
    }
    trikona_lords = {
        _lord_of_house(asc_sign, h) for h in (1, 5, 9)
    }

    best: YogaInstance | None = None
    best_score = -1.0
    for k_lord in kendra_lords:
        for t_lord in trikona_lords:
            if k_lord == t_lord:
                continue  # 1L self-pair excluded
            shared_sign = _conjunction_in_sign(chart, k_lord, t_lord)
            if shared_sign is None:
                continue

            # Score: average Sthana-bala fraction of both lords.
            strengths = []
            for planet in (k_lord, t_lord):
                e = chart[planet]
                lon = e.get("longitude", (e["sign"] - 1) * 30.0 + 15.0)
                d9 = _navamsa_sign(lon)
                sb = sthana_bala(
                    planet, longitude=lon, d1_sign=e["sign"],
                    d9_sign=d9, house=whole_sign_house(asc_sign, e["sign"]),
                )
                strengths.append(sb["total"] / _MAX_STHANA_BALA_PHASE_0)
            strength = max(0.0, min(1.0, sum(strengths) / 2.0))
            if strength <= best_score:
                continue

            shared_house = whole_sign_house(asc_sign, shared_sign)
            best_score = strength
            best = YogaInstance(
                name="Raja Yoga",
                category="raja",
                participants=tuple(sorted((k_lord, t_lord))),
                houses_activated=(shared_house,),
                promise_axis="political_success_leadership",
                lords_involved=tuple(sorted((k_lord, t_lord))),
                strength=strength,
            )
    return best


def detect_dhana_yoga(
    chart: dict, ascendant: dict
) -> YogaInstance | None:
    """Dhana Yoga (canonical 2L + 11L conjunction). BPHS 41.

    The 2nd house signifies accumulated wealth, the 11th signifies
    gains/income. Their lords' conjunction is the most-cited Dhana-Yoga
    variant. Phase 3B emits one Dhana slot; Phase 3B.2 can add more
    Dhana variants (5L+9L, 2L+5L, etc.).
    """
    asc_sign = ascendant.get("sign")
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"ascendant must carry int 'sign' in 1..12, got {asc_sign!r}"
        )
    second_lord = _lord_of_house(asc_sign, 2)
    eleventh_lord = _lord_of_house(asc_sign, 11)
    if second_lord == eleventh_lord:
        return None  # Some ascendants have the same lord for both houses
    shared_sign = _conjunction_in_sign(chart, second_lord, eleventh_lord)
    if shared_sign is None:
        return None

    strengths = []
    for planet in (second_lord, eleventh_lord):
        e = chart[planet]
        lon = e.get("longitude", (e["sign"] - 1) * 30.0 + 15.0)
        d9 = _navamsa_sign(lon)
        sb = sthana_bala(
            planet, longitude=lon, d1_sign=e["sign"],
            d9_sign=d9, house=whole_sign_house(asc_sign, e["sign"]),
        )
        strengths.append(sb["total"] / _MAX_STHANA_BALA_PHASE_0)
    strength = max(0.0, min(1.0, sum(strengths) / 2.0))

    return YogaInstance(
        name="Dhana Yoga",
        category="dhana",
        participants=tuple(sorted((second_lord, eleventh_lord))),
        houses_activated=(whole_sign_house(asc_sign, shared_sign),),
        promise_axis="wealth_through_income",
        lords_involved=tuple(sorted((second_lord, eleventh_lord))),
        strength=strength,
    )
