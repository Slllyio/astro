"""Functional nature of the planets BY ASCENDANT (BPHS ch.34) — yogakarakas, benefics, marakas.

Distinct from ch.3's NATURAL benefic/malefic (already encoded): this classifies each graha for a
GIVEN lagna by the houses it lords (BPHS-34:52-65 + the summary rules sl. at :72-103):

  * a graha owning BOTH a kendra (4/7/10) and a trikona (5/9) is a **yogakaraka** — the best
    (BPHS-34:90: "For Libra ascendant Saturn is classified as unsullied yogakaraka because he owns
    the 4th and the 5th");
  * the lagna lord is auspicious (lagna is kendra AND trikona, exempt from the kendra blemish);
  * a trikona (5/9) lord is auspicious (a wealth-giver);
  * a 3rd/6th/11th lord, or the 8th lord (not the Sun/Moon), is a malefic;
  * a 2nd/7th lord is a maraka (killer);
  * **Kendradhipatya dosha**: a NATURAL benefic (Moon/Mercury/Jupiter/Venus) that owns only a kendra
    loses its benefic power (becomes malefic-by-lordship); a natural malefic owning only a kendra is
    merely neutral.

Verified against Parashara's own 12-lagna key (sl.19-44): the six classical yogakarakas
(Cancer/Leo -> Mars, Taurus/Libra -> Saturn, Capricorn/Aquarius -> Venus) all fall out, and the Aries
key (benefics Jupiter+Sun, malefics Saturn/Mercury/Venus, Venus the maraka) reproduces exactly.
"""
from __future__ import annotations

from typing import Final

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import SIGN_LORDS

SOURCE: Final[Citation] = Citation("BPHS-34", 52)            # functional-lordship rules
YOGAKARAKA_SOURCE: Final[Citation] = Citation("BPHS-34", 90)  # kendra+trikona = yogakaraka

_KENDRAS: Final[frozenset[int]] = frozenset({4, 7, 10})
_TRIKONAS: Final[frozenset[int]] = frozenset({5, 9})
_EVIL: Final[frozenset[int]] = frozenset({3, 6, 11})
_MARAKA: Final[frozenset[int]] = frozenset({2, 7})
#: Natural benefics that suffer the kendra blemish (Moon taken as benefic here; ch.3 refines by paksha).
_NATURAL_BENEFICS: Final[frozenset[str]] = frozenset({"Moon", "Mercury", "Jupiter", "Venus"})


def houses_owned(planet: str, asc_sign: int) -> tuple[int, ...]:
    """The house(s) (1..12 from the lagna) `planet` lords for this ascendant."""
    return tuple(sorted(((s - asc_sign) % 12) + 1
                        for s, lord in SIGN_LORDS.items() if lord == planet))


def yogakaraka(asc_sign: int) -> tuple[str, ...]:
    """The yogakaraka graha(s) for `asc_sign` — those owning both a kendra and a trikona (BPHS-34:90)."""
    out = []
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        owned = set(houses_owned(planet, asc_sign))
        if owned & _KENDRAS and owned & _TRIKONAS:
            out.append(planet)
    return tuple(out)


def functional_nature(planet: str, asc_sign: int) -> str:
    """`planet`'s functional class for `asc_sign` (BPHS ch.34): yogakaraka | benefic | malefic |
    neutral. (Maraka is a separate attribute — see `is_maraka` — because the 2nd/7th lord's killing
    power layers on top of its benefic/malefic nature; the 7th is also a kendra.)"""
    owned = set(houses_owned(planet, asc_sign))
    if not owned:
        return "neutral"
    if owned & _KENDRAS and owned & _TRIKONAS:
        return "yogakaraka"
    if 1 in owned:
        return "benefic"                              # lagna lord — kendra blemish exempt
    if owned & _TRIKONAS:
        return "benefic"
    if owned & _EVIL or (8 in owned and planet not in ("Sun", "Moon")):
        return "malefic"
    if owned & _KENDRAS:                              # only a kendra, no trikona
        return "malefic" if planet in _NATURAL_BENEFICS else "neutral"   # kendradhipatya dosha
    return "neutral"


def is_maraka(planet: str, asc_sign: int) -> bool:
    """True if `planet` lords a maraka (killer) house — the 2nd or 7th (BPHS-34:54, ch.44)."""
    return bool(set(houses_owned(planet, asc_sign)) & _MARAKA)


def classify_all(asc_sign: int) -> dict[str, str]:
    """The functional class of all seven grahas for `asc_sign`."""
    return {p: functional_nature(p, asc_sign)
            for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")}
