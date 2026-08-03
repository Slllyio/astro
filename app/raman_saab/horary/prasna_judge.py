"""Karyasiddhi — the Prasna Tantra success judgment (PRASNA-49:100-190).

The significator (Karyapa/Karyesa) is the lord of the house the query pertains to: wealth
-> 2nd lord, marriage -> 7th lord (PRASNA-49:119-126). Full fulfilment (stanzas 3-4,
PRASNA-49:107-116) when ANY of: (1) the ascendant lord aspects the ascendant AND the
significator aspects the house; (2) the ascendant lord aspects the house AND the
significator aspects the ascendant; (3) the ascendant lord and the significator are in
mutual aspect; (4) the Moon aspects both the significator and the ascendant lord.

Degrees of success (stanzas 5-8, PRASNA-49:137-190): 25% when the ascendant has neither
its lord's nor a benefic's aspect; 50% when benefics aspect the ascendant lord; 75% when
at least one benefic aspects the ascendant or its lord, or the ascendant lord or 2-3
benefics are in the 10th, or three benefics aspect the ascendant; 100% when the ascendant
is aspected by its own lord, or the Moon is unafflicted and benefics aspect the lagna.

Aspect model: "The aspects considered in this book are those of the Tajaka system"
(PRASNA-2:258-262) — planet-to-planet checks use the tajika_aspects orb machinery;
planet-to-HOUSE checks are sign-granular (the book's own charts are rasi diagrams), using
the tajika angles as sign distances {1, 3, 5, 7, 9, 11 from the house, i.e. 0/60/90/120/
180 in sign steps} — conjunction, sextile, square, trine, opposition.

EXCLUDED QUERY TOPICS (the /ai-interpret precedent, firewall-lift scope rule 3): death,
lifespan, serious illness, self-harm — refused IN CODE, no register lifts it.

Usage:
    from app.raman_saab.horary.prasna_judge import judge_prasna
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.horary.tajika_aspects import in_aspect
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS

#: Sign distances (1-based, from=1 means same sign) realizing the tajika aspect set.
_ASPECT_SIGN_DISTANCES: Final[frozenset[int]] = frozenset({1, 3, 5, 7, 9, 11})

#: Refused query topics — coded, never lifted by phrasing.
EXCLUDED_TOPICS: Final[frozenset[str]] = frozenset({
    "death", "lifespan", "serious_illness", "self_harm"})

REFUSAL = ("the engine does not judge that query — death, lifespan, serious illness and "
           "self-harm questions are excluded by design")

_DISCLAIMER = ("What Neelakantha's Prasna Tantra (tr. B. V. Raman) says of this query "
               "moment — a statement of the method, never a validated prediction.")


@dataclass(frozen=True)
class KaryasiddhiVerdict:
    fulfilled: bool                    # any stanza 3-4 configuration holds
    success_quarters: int              # 1..4 (25/50/75/100%), stanzas 5-8
    karyesa: str
    evidence: tuple[str, ...]          # which configurations/rungs fired, cited
    refusal: Optional[str]             # set (and all else zeroed) for excluded topics
    disclaimer: str


def _sign_of(lon: float) -> int:
    return int(lon % 360.0 // 30.0) + 1


def _aspects_house(lon: float, house_sign: int) -> bool:
    dist = (house_sign - _sign_of(lon)) % 12 + 1
    return dist in _ASPECT_SIGN_DISTANCES


def judge_prasna(*, positions: dict[str, float], lagna_lon: float, query_house: int,
                 topic: Optional[str] = None) -> KaryasiddhiVerdict:
    """Judge one query. `positions` maps the seven grahas to longitudes at the query
    moment; `query_house` is 1..12 from the Prasna Lagna; `topic` triggers the coded
    exclusions when it names one."""
    if topic is not None and topic in EXCLUDED_TOPICS:
        return KaryasiddhiVerdict(False, 0, "", (), REFUSAL, _DISCLAIMER)

    lagna_sign = _sign_of(lagna_lon)
    karya_sign = (lagna_sign - 1 + query_house - 1) % 12 + 1
    lagna_lord = SIGN_LORDS[lagna_sign]
    karyesa = SIGN_LORDS[karya_sign]
    ll_lon = positions[lagna_lord]
    ka_lon = positions[karyesa]
    moon_lon = positions["Moon"]

    evidence: list[str] = []
    cite34 = "PRASNA-49:107"
    if _aspects_house(ll_lon, lagna_sign) and _aspects_house(ka_lon, karya_sign):
        evidence.append(f"lagna lord aspects lagna AND karyesa aspects the house ({cite34})")
    if _aspects_house(ll_lon, karya_sign) and _aspects_house(ka_lon, lagna_sign):
        evidence.append(f"lagna lord aspects the house AND karyesa aspects lagna ({cite34})")
    if lagna_lord != karyesa and in_aspect(lagna_lord, ll_lon, karyesa, ka_lon):
        evidence.append(f"lagna lord and karyesa in mutual aspect ({cite34})")
    if (lagna_lord != "Moon" and karyesa != "Moon"
            and in_aspect("Moon", moon_lon, lagna_lord, ll_lon)
            and in_aspect("Moon", moon_lon, karyesa, ka_lon)):
        evidence.append(f"the Moon aspects both the karyesa and the lagna lord ({cite34})")
    fulfilled = bool(evidence)

    # stanzas 5-8 ladder (PRASNA-49:137-190) — highest satisfied rung wins.
    benefics = {p: positions[p] for p in NATURAL_BENEFICS if p in positions}
    lord_aspects_lagna = _aspects_house(ll_lon, lagna_sign)
    benefics_on_lagna = [p for p, lon in benefics.items() if _aspects_house(lon, lagna_sign)]
    benefics_on_lord = [p for p, lon in benefics.items()
                        if p != lagna_lord and in_aspect(p, lon, lagna_lord, ll_lon)]
    tenth_sign = (lagna_sign - 1 + 9) % 12 + 1
    in_tenth = [p for p, lon in positions.items() if _sign_of(lon) == tenth_sign]
    moon_unafflicted = not any(
        in_aspect("Moon", moon_lon, m, positions[m])
        for m in ("Mars", "Saturn") if m != "Moon")

    if lord_aspects_lagna or (moon_unafflicted and benefics_on_lagna):
        quarters = 4
        evidence.append("100%: lagna aspected by its lord / unafflicted Moon with benefic "
                        "aspect on lagna (PRASNA-49:186-190)")
    elif (benefics_on_lagna or benefics_on_lord or lagna_lord in in_tenth
          or sum(1 for p in in_tenth if p in NATURAL_BENEFICS) in (2, 3)
          or len(benefics_on_lagna) >= 3):
        quarters = 3
        evidence.append("75%: benefic on lagna/lord, or lord or 2-3 benefics in the 10th "
                        "(PRASNA-49:178-184)")
    elif benefics_on_lord:
        quarters = 2
        evidence.append("50%: benefics aspect the lagna lord (PRASNA-49:176)")
    else:
        quarters = 1
        evidence.append("25%: the lagna has neither its lord's nor a benefic's aspect "
                        "(PRASNA-49:168-174)")

    return KaryasiddhiVerdict(fulfilled, quarters, karyesa, tuple(evidence), None,
                              _DISCLAIMER)
