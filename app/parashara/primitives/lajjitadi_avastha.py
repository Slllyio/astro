"""Lajjitadi shad-avastha — the six 'shame etc.' planetary states (BPHS ch.45 sl.11-18).

The fourth avastha family, completing the set the engine carries (Baladi, Jagradadi, Deeptadi). These
six are NOT mutually exclusive — a planet may hold several at once — so each is a condition tested
independently (BPHS-45:151-166, verbatim):

    Lajjita  (ashamed)  — in the 5th house AND conjunct a node, the Sun, Saturn or Mars
    Garvita  (proud)    — in exaltation or Moolatrikona
    Kshudita (hungry)   — in an enemy's sign, or conjunct/aspected by an enemy, or conjunct Saturn
    Trushita (thirsty)  — in a watery sign, aspected by a malefic but not by a benefic
    Mudita   (delighted)— in a friendly sign, or conjunct/aspected by a benefic, or conjunct Jupiter
    Kshobhita(agitated) — conjunct the Sun AND aspected/conjunct by a malefic or aspected by an enemy

"The houses occupied by a planet in Kshudita or Kshobhita avastha are destroyed" (BPHS-45:165).
Conjunction is same-sign (whole-sign); aspects use graha drishti; benefic/malefic follow the locked
avastha convention (benefics Jupiter/Venus/Mercury/Moon; malefics Sun/Mars/Saturn/Rahu/Ketu).
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives import graha_drishti as gd
from app.parashara.primitives.relationships import (
    EXALTATION,
    GRAHAS,
    MOOLATRIKONA,
    SIGN_LORDS,
    naisargika,
)

SOURCE: Final[Citation] = Citation("BPHS-45", 151)        # sl.11-18, "YET OTHER AVASTHAS"
DESTROYED_SOURCE: Final[Citation] = Citation("BPHS-45", 165)   # Kshudita/Kshobhita destroy the house

AVASTHAS: Final[tuple[str, ...]] = (
    "Lajjita", "Garvita", "Kshudita", "Trushita", "Mudita", "Kshobhita")
_WATERY_SIGNS: Final[frozenset[int]] = frozenset({4, 8, 12})   # Cancer, Scorpio, Pisces
_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
#: which houses are "destroyed" for a planet holding these (BPHS-45:165).
_DESTROY = frozenset({"Kshudita", "Kshobhita"})


def _is_enemy(of: str, other: str) -> bool:
    """Natural enemy? (nodes have no naisargika relation, so never an enemy in this sense)."""
    return of in MOOLATRIKONA and other in MOOLATRIKONA and naisargika(of, other) == "shatru"


def lajjitadi(planet: str, longitudes: Mapping[str, float], *, asc_sign: int) -> frozenset[str]:
    """The set of Lajjitadi avasthas `planet` holds (BPHS-45:11-18). Empty set if none apply."""
    if planet not in GRAHAS:
        raise ValueError(f"Lajjitadi is defined for the seven grahas, got {planet!r}")
    signs = {p: int(l % 360.0 // 30) + 1 for p, l in longitudes.items()}
    sign = signs[planet]
    house = ((sign - asc_sign) % 12) + 1
    companions = [p for p, s in signs.items() if s == sign and p != planet]
    aspecters = [p for p in gd.planets_aspecting_sign(sign, signs) if p != planet]

    out: set[str] = set()

    # Lajjita — 5th house + a node/Sun/Saturn/Mars companion.
    if house == 5 and any(c in ("Rahu", "Ketu", "Sun", "Saturn", "Mars") for c in companions):
        out.add("Lajjita")

    # Garvita — exaltation or Moolatrikona.
    if sign == EXALTATION.get(planet) or sign == MOOLATRIKONA.get(planet):
        out.add("Garvita")

    # Kshudita — enemy's sign / conjunct an enemy / aspected by an enemy / conjunct Saturn.
    if (_is_enemy(planet, SIGN_LORDS[sign])
            or any(_is_enemy(planet, c) for c in companions)
            or any(_is_enemy(planet, a) for a in aspecters)
            or (planet != "Saturn" and "Saturn" in companions)):
        out.add("Kshudita")

    # Trushita — watery sign, aspected by a malefic but not a benefic.
    if (sign in _WATERY_SIGNS and any(a in _MALEFICS for a in aspecters)
            and not any(a in _BENEFICS for a in aspecters)):
        out.add("Trushita")

    # Mudita — friendly sign / conjunct or aspected by a benefic / conjunct Jupiter.
    friendly_sign = planet in MOOLATRIKONA and naisargika(planet, SIGN_LORDS[sign]) == "mitra"
    if (friendly_sign
            or any(c in _BENEFICS for c in companions)
            or any(a in _BENEFICS for a in aspecters)
            or (planet != "Jupiter" and "Jupiter" in companions)):
        out.add("Mudita")

    # Kshobhita — conjunct the Sun AND (malefic conjunct/aspecting or enemy aspecting).
    if planet != "Sun" and "Sun" in companions and (
            any(c in _MALEFICS for c in companions)
            or any(a in _MALEFICS for a in aspecters)
            or any(_is_enemy(planet, a) for a in aspecters)):
        out.add("Kshobhita")

    return frozenset(out)


def destroys_its_house(avasthas: frozenset[str]) -> bool:
    """True if the planet's avasthas include a house-destroying one (Kshudita/Kshobhita, BPHS-45:165)."""
    return bool(avasthas & _DESTROY)


def all_lajjitadi(longitudes: Mapping[str, float], *, asc_sign: int) -> dict[str, frozenset[str]]:
    """Every graha's Lajjitadi avastha set."""
    return {g: lajjitadi(g, longitudes, asc_sign=asc_sign) for g in GRAHAS if g in longitudes}
