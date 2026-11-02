"""The traditional marriage conditions Krishnamurti lists in Reader 4 (ruling R28).

Reader 4 (KPR4 pp.70-73; the same list in KPR3) gives, "according to Hindu system", 23
conditions under which "Marriage is celebrated in youth or in proper age", three more "according
to Western System", and seven under which "Marriage is Promised but it comes off late in life".
He gives them as the received tradition, before his own sub-lord method. So this module only
DESCRIBES which of them a chart meets. It never feeds a KP verdict, a window or a selection.

Ruling R28 (``docs/kp/KP_RULINGS.md``) fixes how each one is read:

* Frame: "Hindu system", so houses are counted by sign from the Lagna sign, "lord of N" is the
  lord of that sign, "conjoined" means in the same sign, and an aspect is the traditional full
  sign aspect (Saturn on the 3rd, 7th and 10th sign from his own, plus the 7th for the others).
  The one exception is condition (b), which names the 7th CUSP, so it uses the KP 7th cusp.
* Benefics: Jupiter, Venus, Mercury and the Moon, the natural benefics.
* "Favourable" or "beneficial" house, for marriage: the 2nd, 7th and 11th, Krishnamurti's own
  marriage houses in the same chapter ("houses 2, 7 and 11 are examined", KPR4 p.70).
* Left out, and listed with the reason in ``EXCLUDED``: conditions that rest on "strong", "well
  posited", "stronger than" or "favourable connection", which he never defines here; the
  Western ones, which need aspect orbs and Uranus; and (s), whose wording can be read two ways.

Usage:
    from app.kp.chart import Birth, cast
    from app.kp.marriage_conditions import marriage_conditions
    for c in marriage_conditions(cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))):
        print(c.key, c.met, c.detail)
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from app.kp.chart import KPChart, sign_index
from app.kp.subs import SIGN_LORDS

logger = logging.getLogger(__name__)

SEVEN: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
FRUITFUL_SIGNS: Final[frozenset[int]] = frozenset({1, 3, 7, 8, 11})  # Tau, Can, Sco, Sag, Pis
MARRIAGE_HOUSES: Final[frozenset[int]] = frozenset({2, 7, 11})
OWN_OR_EXALTED_VENUS: Final[frozenset[int]] = frozenset({1, 6, 11})  # Taurus, Libra, Pisces
JUPITER_EXALTED: Final[int] = 3  # Cancer
_SPECIAL_ASPECTS: Final[dict[str, tuple[int, ...]]] = {
    "Saturn": (3, 7, 10), "Mars": (4, 7, 8), "Jupiter": (5, 7, 9),
}

CITATIONS: Final[tuple[str, ...]] = ("KPR4-MARRIAGE-YOUTH", "KPR4-MARRIAGE-LATE", "KPR4-MARRIAGE-HOUSES")


@dataclass(frozen=True, slots=True)
class Condition:
    """One listed condition: whether this chart meets it, and the facts used."""

    key: str          # "youth.a" .. "youth.w", "late.a" .. "late.f"
    group: str        # "youth" (celebrated in proper age) or "late" (promised but late)
    text: str         # the condition as printed, KPR4 pp.70-73
    met: bool
    detail: str


@dataclass(frozen=True, slots=True)
class Signs:
    """Sign placements, 0 = Aries. Kept separate from the chart so tests can hand-build one."""

    lagna: int
    cusp7: int
    planet: Mapping[str, int]

    def house(self, body: str) -> int:
        """House of a planet, counted by sign from the Lagna sign (1-12)."""
        return (self.planet[body] - self.lagna) % 12 + 1

    def lord(self, house: int) -> str:
        return SIGN_LORDS[(self.lagna + house - 1) % 12]

    def together(self, a: str, b: str) -> bool:
        return a != b and self.planet[a] == self.planet[b]

    def aspects(self, by: str, target: str) -> bool:
        """Traditional full sign aspect of ``by`` on ``target`` (the 7th, plus special ones)."""
        if by == target:
            return False
        nth = (self.planet[target] - self.planet[by]) % 12 + 1
        return nth in _SPECIAL_ASPECTS.get(by, (7,))

    def exchange(self, h1: int, h2: int) -> bool:
        a, b = self.lord(h1), self.lord(h2)
        if a == b:
            return False
        return SIGN_LORDS[self.planet[a]] == b and SIGN_LORDS[self.planet[b]] == a


def signs_of(chart: KPChart) -> Signs:
    return Signs(
        sign_index(chart.cusps[0].longitude),
        sign_index(chart.cusps[6].longitude),
        {p: sign_index(chart.planets[p].longitude) for p in chart.planets},
    )


def _benefics_in(s: Signs, houses: frozenset[int], *, base: int, skip: str = "") -> list[str]:
    return [b for b in sorted(BENEFICS) if b != skip and (s.planet[b] - base) % 12 + 1 in houses]


def _youth(s: Signs) -> list[tuple[str, str, bool, str]]:
    h = s.house
    l1, l2, l7, l11 = s.lord(1), s.lord(2), s.lord(7), s.lord(11)
    gap = (s.planet[l7] - s.planet[l1]) % 12 + 1
    ben_lagna = _benefics_in(s, MARRIAGE_HOUSES, base=s.lagna)
    ben_moon = _benefics_in(s, MARRIAGE_HOUSES, base=s.planet["Moon"], skip="Moon")
    jup_with = [b for b in sorted(BENEFICS - {"Jupiter"}) if s.together("Jupiter", b)]
    return [
        ("a", "Moon and Venus occupy fruitful signs, Taurus, Cancer, Scorpio, Pisces and also Sagittarius",
         s.planet["Moon"] in FRUITFUL_SIGNS and s.planet["Venus"] in FRUITFUL_SIGNS,
         f"Moon sign {s.planet['Moon'] + 1}, Venus sign {s.planet['Venus'] + 1}"),
        ("b", "the 7th cusp falls in any of these signs", s.cusp7 in FRUITFUL_SIGNS,
         f"7th cusp in sign {s.cusp7 + 1}"),
        ("c", "Jupiter or Venus occupy the houses 2, 7 or 11",
         h("Jupiter") in MARRIAGE_HOUSES or h("Venus") in MARRIAGE_HOUSES,
         f"Jupiter in {h('Jupiter')}, Venus in {h('Venus')}"),
        ("d", "Jupiter is conjoined with Moon in 1, 5, 10, 11",
         s.together("Jupiter", "Moon") and h("Moon") in {1, 5, 10, 11},
         f"Jupiter in {h('Jupiter')}, Moon in {h('Moon')}"),
        ("e", "Venus is conjoined with Moon in 1, 5, 10, or 11",
         s.together("Venus", "Moon") and h("Moon") in {1, 5, 10, 11},
         f"Venus in {h('Venus')}, Moon in {h('Moon')}"),
        ("g", "lord of Lagna is conjoined with lord of 7 and occupies a favourable house",
         s.together(l1, l7) and h(l1) in MARRIAGE_HOUSES, f"{l1} in {h(l1)}, {l7} in {h(l7)}"),
        ("h", "lord of Lagna and lord of 7 are in 3 and 11 or 5 and 9 to each other",
         gap in {3, 11, 5, 9}, f"{l7} is {gap} signs from {l1}"),
        ("i", "benefics occupy 2 or 7 or 11 counted from Lagna and Moon sign",
         bool(ben_lagna) and bool(ben_moon),
         f"from Lagna: {', '.join(ben_lagna) or 'none'}; from Moon: {', '.join(ben_moon) or 'none'}"),
        ("l", "Venus is in his own or exalted sign and lord of 7 in beneficial house",
         s.planet["Venus"] in OWN_OR_EXALTED_VENUS and h(l7) in MARRIAGE_HOUSES,
         f"Venus sign {s.planet['Venus'] + 1}, {l7} in {h(l7)}"),
        ("m", "Mercury in 7 and Venus conjoined with lord of 7",
         h("Mercury") == 7 and s.together("Venus", l7), f"Mercury in {h('Mercury')}, lord of 7 {l7}"),
        ("n", "lord of 7 is in 11 and Venus in 2", h(l7) == 11 and h("Venus") == 2,
         f"{l7} in {h(l7)}, Venus in {h('Venus')}"),
        ("o", "Venus is in Lagna and Lord of Lagna is in 7", h("Venus") == 1 and h(l1) == 7,
         f"Venus in {h('Venus')}, {l1} in {h(l1)}"),
        ("p", "mutual exchange between lords of 1 and 7 (Madhana Gopala yoga)", s.exchange(1, 7),
         f"{l1} and {l7}"),
        ("q", "Jupiter is exalted in 7th house conjoined with benefics",
         h("Jupiter") == 7 and s.planet["Jupiter"] == JUPITER_EXALTED and bool(jup_with),
         f"Jupiter in {h('Jupiter')}, with {', '.join(jup_with) or 'no benefic'}"),
        ("t", "lord of Lagna is in 10 and lord of 2 is in 11", h(l1) == 10 and h(l2) == 11,
         f"{l1} in {h(l1)}, {l2} in {h(l2)}"),
        ("u", "benefics in 1 or 2 or 7", bool(_benefics_in(s, frozenset({1, 2, 7}), base=s.lagna)),
         ", ".join(_benefics_in(s, frozenset({1, 2, 7}), base=s.lagna)) or "none"),
        ("v", "lords of 2 and 11 in mutual exchange", s.exchange(2, 11), f"{l2} and {l11}"),
        ("w", "lord of 2 and 7 in 11", h(l2) == 11 and h(l7) == 11, f"{l2} in {h(l2)}, {l7} in {h(l7)}"),
    ]


def _late(s: Signs) -> list[tuple[str, str, bool, str]]:
    h = s.house
    l7 = s.lord(7)
    sat_lagna = h("Saturn")
    sat_moon = (s.planet["Saturn"] - s.planet["Moon"]) % 12 + 1
    sat_owns = [n for n in range(1, 13) if s.lord(n) == "Saturn"]
    return [
        ("a", "Saturn is in 1, 3, 5, 7 or 10 counted from Lagna or Moon sign and does not own "
              "beneficial houses",
         (sat_lagna in {1, 3, 5, 7, 10} or sat_moon in {1, 3, 5, 7, 10})
         and not set(sat_owns) & MARRIAGE_HOUSES,
         f"Saturn {sat_lagna} from Lagna, {sat_moon} from Moon, owns {sat_owns}"),
        ("c", "Mars is in the 8th house", h("Mars") == 8, f"Mars in {h('Mars')}"),
        ("d", "Moon and Saturn conjoin together especially in 1, 2, or 11", s.together("Moon", "Saturn"),
         f"Moon in {h('Moon')}, Saturn in {sat_lagna}"
         + (" (one of the houses he stresses)" if s.together("Moon", "Saturn") and sat_lagna in {1, 2, 11}
            else "")),
        ("f", "the lord of 7 and Venus are aspected by Saturn",
         s.aspects("Saturn", l7) and s.aspects("Saturn", "Venus"),
         f"lord of 7 {l7}; Saturn sign {s.planet['Saturn'] + 1}"),
    ]


EXCLUDED: Final[dict[str, str]] = {
    "youth.f": "'not aspected by Saturn but is stronger than Saturn': strength is not defined here",
    "youth.j": "'favourable connection with benefics' is not defined",
    "youth.k": "'strong and well posited' is not defined",
    "youth.r": "'Venus is strong in the 7th house': strength is not defined",
    "youth.s": "'lord of 7, Venus occupies the 2nd' reads either as two planets or as Venus being "
               "the lord of 7",
    "youth.x": "Western system: 'harmonious aspects' needs aspect orbs",
    "youth.y": "Western system, the bride's chart: 'good aspects' needs aspect orbs",
    "youth.z": "a benefic 'transiting very close' to a cusp at birth: no distance given",
    "late.b": "'adverse aspects from Jupiter or Uranus' is a Western aspect with Uranus",
    "late.e": "'evil aspects from Jupiter or Uranus' is a Western aspect with Uranus",
    "late.g": "'squared by Jupiter or Uranus' is a Western aspect with Uranus",
}


def conditions_from_signs(s: Signs) -> tuple[Condition, ...]:
    out = [Condition(f"youth.{k}", "youth", t, bool(m), d) for k, t, m, d in _youth(s)]
    out += [Condition(f"late.{k}", "late", t, bool(m), d) for k, t, m, d in _late(s)]
    return tuple(out)


def marriage_conditions(chart: KPChart) -> tuple[Condition, ...]:
    """Which of Reader 4's traditional marriage conditions the chart meets (descriptive only)."""
    return conditions_from_signs(signs_of(chart))


__all__ = [
    "BENEFICS", "CITATIONS", "EXCLUDED", "Condition", "Signs", "conditions_from_signs",
    "marriage_conditions", "signs_of",
]
