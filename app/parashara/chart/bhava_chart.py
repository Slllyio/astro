"""Compute BPHS ch.11 bhava factors from a real chart, and judge every house.

Joins the primitives — functional nature (ch.3), Baladi avastha (ch.45), graha drishti (ch.26),
relationships/lordships (ch.3) — into the `BhavaFactors` the ch.11 verdict layer consumes. Houses
are whole-sign from the lagna, Parashara's reckoning.

Chart input is the same lightweight shape the rest of this engine uses: sidereal longitudes per
graha plus the ascendant sign, so the judge is testable without a heavy chart model. `moon_waxing`
is required because a graha's benefic nature (ch.3 sl.11) depends on it.
"""
from __future__ import annotations

from typing import Mapping

from app.parashara.judges.bhava_prosperity import BhavaFactors, BhavaVerdict, judge_prosperity
from app.parashara.primitives import functional_nature as fn
from app.parashara.primitives import graha_drishti as gd
from app.parashara.primitives.baladi_avastha import baladi_from_longitude
from app.parashara.primitives.jagradadi_avastha import jagradadi_avastha
from app.parashara.primitives.relationships import EXALTATION, MOOLATRIKONA, SIGN_LORDS, naisargika

_LUMINARIES = ("Sun", "Moon")


def _sign_of(lon: float) -> int:
    return int(lon % 360.0 // 30) + 1


def _house_sign(house: int, asc_sign: int) -> int:
    """Whole-sign: the sign occupying `house` counted from the ascendant sign."""
    return ((asc_sign - 1) + (house - 1)) % 12 + 1


def _signs_owned(planet: str) -> tuple[int, ...]:
    return tuple(s for s, lord in SIGN_LORDS.items() if lord == planet)


def _is_benefic(planet: str, planet_signs: Mapping[str, int], *, moon_waxing: bool) -> bool:
    """Benefic nature in context — companions are the other grahas sharing the sign (ch.3 sl.11)."""
    sign = planet_signs.get(planet)
    companions = [p for p, s in planet_signs.items() if s == sign and p != planet]
    if planet == "Moon":
        return fn.natural_benefic("Moon", moon_waxing=moon_waxing, companions=companions)
    if planet == "Mercury":
        return fn.natural_benefic("Mercury", companions=companions)
    return fn.natural_benefic(planet) if planet in (fn.FIXED_BENEFICS | fn.FIXED_MALEFICS) else True


def _dusthana_lords(asc_sign: int) -> frozenset[str]:
    """Lords of the 6th, 8th and 12th houses from the lagna."""
    return frozenset(SIGN_LORDS[_house_sign(h, asc_sign)] for h in (6, 8, 12))


def _defeated_in_war(planet: str, longitudes: Mapping[str, float]) -> bool:
    """Graha yuddha: two non-luminaries within 1 degree in the SAME sign war; the higher-longitude
    one loses (BPHS-11:16d, "the one with lesser longitude is declared winner"). Luminaries do not
    enter war."""
    if planet in _LUMINARIES or planet not in longitudes:
        return False
    lon = longitudes[planet] % 360.0
    sign = _sign_of(lon)
    for other, olon in longitudes.items():
        if other == planet or other in _LUMINARIES:
            continue
        olon %= 360.0
        if _sign_of(olon) == sign and abs(lon - olon) <= 1.0 and lon > olon:
            return True
    return False


def _malefic_antidoted(lord: str, malefic: str, planet_signs: Mapping[str, int]) -> bool:
    """BPHS-11:16(b): a malefic joined to the lord is benign if it is exalted, or friendly to the
    lord. Nodes have neither exaltation nor a naisargika relation, so they are never antidoted here."""
    if planet_signs.get(malefic) == EXALTATION.get(malefic):
        return True
    if lord in MOOLATRIKONA and malefic in MOOLATRIKONA:      # naisargika is defined for the 7 only
        return naisargika(lord, malefic) == "mitra"
    return False


def bhava_factors(house: int, longitudes: Mapping[str, float], *,
                  asc_sign: int, moon_waxing: bool) -> BhavaFactors:
    """Compute the ch.11 factors for one house from the chart."""
    planet_signs = {p: _sign_of(l) for p, l in longitudes.items()}
    hsign = _house_sign(house, asc_sign)
    lord = SIGN_LORDS[hsign]

    occupants = [p for p, s in planet_signs.items() if s == hsign]
    aspecters = gd.planets_aspecting_sign(hsign, planet_signs)

    benefic = {p: _is_benefic(p, planet_signs, moon_waxing=moon_waxing) for p in planet_signs}

    lord_sign = planet_signs.get(lord)
    lord_companions = [p for p, s in planet_signs.items() if s == lord_sign and p != lord]
    lord_house = ((lord_sign - asc_sign) % 12) + 1 if lord_sign is not None else 0

    dusthana = _dusthana_lords(asc_sign)
    dusthana_companion = any(c in dusthana for c in lord_companions)
    malefic_companions = [c for c in lord_companions if not benefic.get(c, False)]
    malefic_companion = bool(malefic_companions)
    # BPHS-11:16(b): the malefic conjunction "evil is minimized" if the malefic is friendly to the
    # bhava lord, or they join in a favourable house, or the malefic is exalted. All three limbs are
    # in the verbatim text; two are pure table lookups. "Favourable house" = kendra+trikona (the
    # classical auspicious set). Nodes have no naisargika/exaltation, so a nodal malefic is never
    # individually antidoted (conservative). ponytail: kendra+trikona for "favourable"; widen only
    # with a doctrine call.
    malefic_mitigated = bool(malefic_companions) and (
        lord_house in (1, 4, 5, 7, 9, 10)
        or all(_malefic_antidoted(lord, c, planet_signs) for c in malefic_companions)
    )

    lord_av = baladi_from_longitude(longitudes[lord]) if lord in longitudes else None

    return BhavaFactors(
        house=house,
        benefic_occupant=any(benefic.get(p, False) for p in occupants),
        benefic_aspect=any(benefic.get(p, False) for p in aspecters),
        lord_avastha=lord_av.state if lord_av else "yuva",
        lord_own_or_exalt=(lord_sign in _signs_owned(lord)) or (lord_sign == EXALTATION.get(lord)),
        lord_in_tenth=(lord_house == 10),
        lord_aspects_bhava=(lord in planet_signs and gd.aspects_sign(lord, lord_sign, hsign)),
        lord_conjunct_malefic=malefic_companion,
        # BPHS-11:16(b)'s own antidotes: malefic friendly to the lord / exalted / in a favourable
        # house (computed above). Previously hardcoded False, which over-fired annihilation whenever
        # the lord failed to aspect its bhava even though the offending malefic was benign.
        lord_malefic_conjunction_mitigated=malefic_mitigated,
        lord_conjunct_dusthana_lord=dusthana_companion,
        lord_is_itself_dusthana_lord=(lord in dusthana),
        lord_defeated_in_war=_defeated_in_war(lord, longitudes),
        # Suptavastha (BPHS-11:158/271): the lord debilitated or in an enemy's sign == Jagradadi
        # sushupti. Nodes have no Jagradadi, so a nodal lord contributes no Supta condition.
        lord_in_supta=(lord_sign is not None and lord in EXALTATION
                       and jagradadi_avastha(lord, lord_sign).state == "sushupti"),
    )


def judge_bhava(house: int, longitudes: Mapping[str, float], *,
                asc_sign: int, moon_waxing: bool) -> BhavaVerdict:
    """Judge one house end-to-end from the chart (BPHS ch.11)."""
    return judge_prosperity(bhava_factors(house, longitudes, asc_sign=asc_sign,
                                          moon_waxing=moon_waxing))


def judge_all_bhavas(longitudes: Mapping[str, float], *,
                     asc_sign: int, moon_waxing: bool) -> dict[int, BhavaVerdict]:
    """Judge all twelve houses."""
    return {h: judge_bhava(h, longitudes, asc_sign=asc_sign, moon_waxing=moon_waxing)
            for h in range(1, 13)}
