"""Special yogas from BPHS ch.36 ("Many Other Yogas"). First: Gaja-Kesari, in its strict BPHS form.

Parashara's Gaja-Kesari is narrower than the popular "Jupiter in a kendra from the Moon":

    "Should Jupiter be in an angle from the ascendant or from the Moon, and be conjunct or aspected by
     (another) benefic, avoiding at the same time debilitation, combustion and inimical sign,
     Gajakesari yoga is caused." (BPHS-36:96)

So all four conditions must hold together — kendra (from lagna OR Moon), a benefic's conjunction or
aspect, and Jupiter free of debilitation, combustion and an enemy's sign. This module encodes exactly
that (using the ch.7 combustion orbs and the ch.3 natural relationships), not the loose version the
chapter's own Notes criticise.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Optional

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.combustion import is_combust
from app.parashara.primitives.functional_nature import natural_benefic
from app.parashara.primitives.graha_drishti import aspects_sign
from app.parashara.primitives.relationships import EXALTATION, SIGN_LORDS, naisargika

GAJA_KESARI_SOURCE: Final[Citation] = Citation("BPHS-36", 96)   # sl.3-4
_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
#: Benefics that can supply the required conjunction/aspect (Jupiter is the subject, excluded).
_BENEFIC_CANDIDATES: Final[tuple[str, ...]] = ("Moon", "Mercury", "Venus")


@dataclass(frozen=True)
class SpecialYoga:
    name: str
    reason: str
    source: Citation


def _house(ref_sign: int, sign: int) -> int:
    return ((sign - ref_sign) % 12) + 1


def _debilitation_sign(planet: str) -> int:
    return ((EXALTATION[planet] - 1 + 6) % 12) + 1          # 7th from exaltation


def _is_benefic(planet: str, signs: Mapping[str, int], *, moon_waxing: bool) -> bool:
    if planet == "Moon":
        return moon_waxing
    if planet == "Mercury":
        companions = [p for p, s in signs.items() if s == signs["Mercury"] and p != "Mercury"]
        return natural_benefic("Mercury", companions=companions)
    return natural_benefic(planet)                          # Venus (and Jupiter) — always benefic


def _benefic_conjoins_or_aspects(target: str, signs: Mapping[str, int], *, moon_waxing: bool) -> bool:
    """True if a benefic OTHER than `target` is in `target`'s sign or casts a full aspect on it."""
    tsign = signs[target]
    for b in _BENEFIC_CANDIDATES:
        if b == target or b not in signs:
            continue
        if not _is_benefic(b, signs, moon_waxing=moon_waxing):
            continue
        if signs[b] == tsign or aspects_sign(b, signs[b], tsign):
            return True
    return False


def gaja_kesari(longitudes: Mapping[str, float], *, asc_sign: int, moon_waxing: bool,
                jupiter_retrograde: bool = False) -> Optional[SpecialYoga]:
    """Detect Gaja-Kesari in its strict BPHS form (BPHS-36:96), or None."""
    if "Jupiter" not in longitudes or "Moon" not in longitudes or "Sun" not in longitudes:
        return None
    signs = {g: int(l % 360.0 // 30) + 1 for g, l in longitudes.items()}
    jup = signs["Jupiter"]
    # 1. angle from the ascendant OR from the Moon
    if _house(asc_sign, jup) not in _KENDRAS and _house(signs["Moon"], jup) not in _KENDRAS:
        return None
    # 2. not debilitated, 3. not combust, 4. not in an enemy's sign
    if jup == _debilitation_sign("Jupiter"):
        return None
    if is_combust("Jupiter", longitudes["Jupiter"], longitudes["Sun"], retrograde=jupiter_retrograde):
        return None
    if naisargika("Jupiter", SIGN_LORDS[jup]) == "shatru":
        return None
    # 5. conjunct or aspected by another benefic
    if not _benefic_conjoins_or_aspects("Jupiter", signs, moon_waxing=moon_waxing):
        return None
    return SpecialYoga("Gaja-Kesari",
                       "Jupiter in a kendra from lagna/Moon, aspected or joined by a benefic, and "
                       "free of debilitation, combustion and an enemy's sign", GAJA_KESARI_SOURCE)


def detect(longitudes: Mapping[str, float], *, asc_sign: int, moon_waxing: bool,
           jupiter_retrograde: bool = False) -> tuple[SpecialYoga, ...]:
    """Every ch.36 special yoga present (currently Gaja-Kesari)."""
    gk = gaja_kesari(longitudes, asc_sign=asc_sign, moon_waxing=moon_waxing,
                     jupiter_retrograde=jupiter_retrograde)
    return (gk,) if gk is not None else ()
