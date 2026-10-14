"""Special yogas from BPHS ch.36 ("Many Other Yogas") — Gaja-Kesari plus the crisp named yogas.

Parashara's ch.36 is a gallery of named yogas. This encodes as firing detectors the ones whose
condition is CRISP and chart-computable, each citing its own sloka (the maraka/conjunction pattern —
one specific stated combination per rule, never a synthesized general principle):

    Gaja-Kesari (sl.3-4) — Jupiter in a kendra from lagna/Moon, benefic-joined/aspected, free of
                           debilitation/combustion/enemy sign (its strict BPHS form).
    Subha       (sl.1)   — a benefic in the ascendant, or benefics in both the 2nd and 12th.
    Asubha      (sl.1)   — a malefic in the ascendant, or malefics in both the 2nd and 12th.
    Amala       (sl.5)   — exclusively a benefic in the 10th from the lagna or the Moon.
    Parvata     (sl.7)   — a benefic in a kendra with the 7th and 8th free of malefics.
    Chamara     (sl.11)  — the lagna lord exalted in a kendra and aspected by Jupiter, OR two
                           benefics together in the 1st/7th/9th/10th.
    Srinatha    (sl.18)  — the 7th lord in the 10th, the 10th lord exalted and joined the 9th lord.

DEFERRED (not faked): the yogas whose condition hinges on a planet being "endowed with strength"
(Lakshmi sl.27, Sankha sl.13, Bheri sl.15, Mridanga sl.17, Sarada sl.19) — "strong" is a Shadbala
judgment this detector layer does not take; they remain in `yoga_catalogue` until encoded with a
cited strength threshold. Uses the ch.7 combustion orbs and ch.3 relationships; benefic/malefic are
moon-phase aware (nodes are malefic).
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
SUBHA_SOURCE: Final[Citation] = Citation("BPHS-36", 33)         # sl.1 — Subha / Asubha
AMALA_SOURCE: Final[Citation] = Citation("BPHS-36", 208)        # sl.5
PARVATA_SOURCE: Final[Citation] = Citation("BPHS-36", 297)      # sl.7
CHAMARA_SOURCE: Final[Citation] = Citation("BPHS-36", 409)      # sl.11
SRINATHA_SOURCE: Final[Citation] = Citation("BPHS-36", 469)     # sl.18
_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
#: Benefics that can supply the required conjunction/aspect (Jupiter is the subject, excluded).
_BENEFIC_CANDIDATES: Final[tuple[str, ...]] = ("Moon", "Mercury", "Venus")
_SEVEN: Final[frozenset[str]] = frozenset(
    {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"})


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


def _house_sign(asc_sign: int, house: int) -> int:
    return ((asc_sign + house - 2) % 12) + 1


def _lord_of(asc_sign: int, house: int) -> str:
    return SIGN_LORDS[_house_sign(asc_sign, house)]


def _benefics(signs: Mapping[str, int], *, moon_waxing: bool) -> set[str]:
    return {p for p in signs if p in _SEVEN and _is_benefic(p, signs, moon_waxing=moon_waxing)}


def _malefics(signs: Mapping[str, int], *, moon_waxing: bool) -> set[str]:
    # the seven that are not benefic, plus the nodes (always malefic)
    mal = {p for p in signs if p in _SEVEN and not _is_benefic(p, signs, moon_waxing=moon_waxing)}
    mal |= {p for p in ("Rahu", "Ketu") if p in signs}
    return mal


def _occupants(signs: Mapping[str, int], ref_sign: int, house: int) -> set[str]:
    target = _house_sign(ref_sign, house)
    return {p for p, s in signs.items() if s == target}


def subha(signs: Mapping[str, int], *, asc_sign: int, moon_waxing: bool) -> Optional[SpecialYoga]:
    """A benefic in the ascendant, or benefics in both the 2nd and 12th (BPHS-36:1)."""
    ben = _benefics(signs, moon_waxing=moon_waxing)
    if _occupants(signs, asc_sign, 1) & ben:
        return SpecialYoga("Subha", "a benefic occupies the ascendant", SUBHA_SOURCE)
    if (_occupants(signs, asc_sign, 2) & ben) and (_occupants(signs, asc_sign, 12) & ben):
        return SpecialYoga("Subha", "benefics occupy both the 2nd and the 12th", SUBHA_SOURCE)
    return None


def asubha(signs: Mapping[str, int], *, asc_sign: int, moon_waxing: bool) -> Optional[SpecialYoga]:
    """A malefic in the ascendant, or malefics in both the 2nd and 12th (BPHS-36:1)."""
    mal = _malefics(signs, moon_waxing=moon_waxing)
    if _occupants(signs, asc_sign, 1) & mal:
        return SpecialYoga("Asubha", "a malefic occupies the ascendant", SUBHA_SOURCE)
    if (_occupants(signs, asc_sign, 2) & mal) and (_occupants(signs, asc_sign, 12) & mal):
        return SpecialYoga("Asubha", "malefics occupy both the 2nd and the 12th", SUBHA_SOURCE)
    return None


def amala(signs: Mapping[str, int], *, asc_sign: int, moon_waxing: bool) -> Optional[SpecialYoga]:
    """Exclusively a benefic in the 10th from the lagna or the Moon (BPHS-36:5)."""
    ben = _benefics(signs, moon_waxing=moon_waxing)
    mal = _malefics(signs, moon_waxing=moon_waxing)
    for ref_name, ref_sign in (("lagna", asc_sign), ("Moon", signs.get("Moon", asc_sign))):
        occ = _occupants(signs, ref_sign, 10)
        if occ and (occ <= ben) and not (occ & mal):
            return SpecialYoga("Amala", f"only benefic(s) ({', '.join(sorted(occ))}) in the 10th "
                               f"from the {ref_name}", AMALA_SOURCE)
    return None


def parvata(signs: Mapping[str, int], *, asc_sign: int, moon_waxing: bool) -> Optional[SpecialYoga]:
    """A benefic in a kendra, with the 7th and 8th free of malefics (BPHS-36:7)."""
    ben = _benefics(signs, moon_waxing=moon_waxing)
    mal = _malefics(signs, moon_waxing=moon_waxing)
    benefic_in_kendra = any(_occupants(signs, asc_sign, k) & ben for k in _KENDRAS)
    seventh_clear = not (_occupants(signs, asc_sign, 7) & mal)
    eighth_clear = not (_occupants(signs, asc_sign, 8) & mal)
    if benefic_in_kendra and seventh_clear and eighth_clear:
        return SpecialYoga("Parvata", "a benefic in a kendra while the 7th and 8th are free of "
                           "malefics", PARVATA_SOURCE)
    return None


def chamara(signs: Mapping[str, int], *, asc_sign: int, moon_waxing: bool) -> Optional[SpecialYoga]:
    """Lagna lord exalted in a kendra and aspected by Jupiter, OR two benefics together in the
    1st/7th/9th/10th (BPHS-36:11)."""
    lord = _lord_of(asc_sign, 1)
    if lord in signs:
        lsign = signs[lord]
        if (((lsign - asc_sign) % 12) + 1 in _KENDRAS and lsign == EXALTATION.get(lord)
                and "Jupiter" in signs and aspects_sign("Jupiter", signs["Jupiter"], lsign)):
            return SpecialYoga("Chamara", "the lagna lord exalted in a kendra and aspected by "
                               "Jupiter", CHAMARA_SOURCE)
    ben = _benefics(signs, moon_waxing=moon_waxing)
    for h in (1, 7, 9, 10):
        if len(_occupants(signs, asc_sign, h) & ben) >= 2:
            return SpecialYoga("Chamara", f"two benefics together in the {h}th house", CHAMARA_SOURCE)
    return None


def srinatha(signs: Mapping[str, int], *, asc_sign: int) -> Optional[SpecialYoga]:
    """7th lord in the 10th, 10th lord exalted and joined the 9th lord (BPHS-36:18)."""
    l7, l10, l9 = _lord_of(asc_sign, 7), _lord_of(asc_sign, 10), _lord_of(asc_sign, 9)
    if l7 not in signs or l10 not in signs or l9 not in signs:
        return None
    l7_house = ((signs[l7] - asc_sign) % 12) + 1
    if (l7_house == 10 and signs[l10] == EXALTATION.get(l10) and signs[l10] == signs[l9]):
        return SpecialYoga("Srinatha", "the 7th lord in the 10th, the 10th lord exalted and with "
                           "the 9th lord", SRINATHA_SOURCE)
    return None


def detect(longitudes: Mapping[str, float], *, asc_sign: int, moon_waxing: bool,
           jupiter_retrograde: bool = False) -> tuple[SpecialYoga, ...]:
    """Every crisp ch.36 special yoga present in the chart, each cited to its own sloka."""
    signs = {g: int(l % 360.0 // 30) + 1 for g, l in longitudes.items()}
    out: list[SpecialYoga] = []
    gk = gaja_kesari(longitudes, asc_sign=asc_sign, moon_waxing=moon_waxing,
                     jupiter_retrograde=jupiter_retrograde)
    if gk is not None:
        out.append(gk)
    for detector in (subha, asubha, amala, parvata, chamara):
        y = detector(signs, asc_sign=asc_sign, moon_waxing=moon_waxing)
        if y is not None:
            out.append(y)
    sn = srinatha(signs, asc_sign=asc_sign)
    if sn is not None:
        out.append(sn)
    return tuple(out)
