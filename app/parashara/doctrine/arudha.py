"""Arudha padas — the twelve bhava arudhas incl. the Arudha Lagna (BPHS ch.29-30).

The Arudha (pada) of a house is "the sign arrived at by counting as many signs from the house lord
as he is away from the house" (BPHS-29:36) — i.e. as far from the lord as the lord is from the house,
the clean form `pada = 2*lord_sign - house_sign`. The Arudha of the ascendant is the Arudha Lagna
(AL), the "perceived self"; the Arudha of the 12th is the Upapada (UL, read for marriage, ch.30).

Special exceptions (BPHS-29:241, sl.4-5): a pada may never fall on the house itself or the 7th from
it. The doubling lands on the house when the lord is in the 1st/7th, and on the 7th when the lord is
in the 4th/10th, so those four positions are redirected. BPHS's three worked exceptions fix it:
  * lord in the 1st  -> the 10th from the house   (worked: Jupiter in Sagittarius -> Virgo)
  * lord in the 7th  -> the 4th  from the house   (worked: Saturn in Leo, Aquarius asc -> Taurus)
  * lord in the 4th  -> the 4th  from the house   (worked: Sun in Scorpio, Leo asc -> Scorpio, the 4th)
  * lord in the 10th -> the 10th from the house   (INFERRED, symmetric to the 4th case — BPHS gives
    no 10th example; documented, not silently assumed)
All three printed cases are reproduced exactly; the base rule is pinned by Scorpio asc / Mars in
Cancer -> Pisces. (The Santhanam ch.29 Notes narrate the count loosely — for the 7th case they call
the raw pada "the 7th" though the literal count gives the house; the redirect target Taurus is what
the text lands on, and this code lands there by the house-relative rule above.)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import EXALTATION, SIGN_LORDS

RULE_SOURCE: Final[Citation] = Citation("BPHS-29", 36)         # the counting rule
EXCEPTION_SOURCE: Final[Citation] = Citation("BPHS-29", 241)   # sl.4-5, the 1st/7th exceptions

#: Arudha of house N -> its classical pada name.
PADA_NAMES: Final[Mapping[int, str]] = {
    1: "Lagna Pada (Arudha Lagna)", 2: "Dhana Pada", 3: "Vikrama Pada", 4: "Matru Pada",
    5: "Putra Pada", 6: "Roga Pada", 7: "Dara Pada", 8: "Marana Pada", 9: "Pitru Pada",
    10: "Karma Pada", 11: "Labha Pada", 12: "Vyaya Pada (Upapada)",
}


def _nth_from(sign: int, n: int) -> int:
    """The nth house (1-indexed) counted from `sign`."""
    return ((sign - 1 + (n - 1)) % 12) + 1


def arudha_pada(house_sign: int, lord_sign: int) -> int:
    """The Arudha sign (1..12) of a house at `house_sign` whose lord is in `lord_sign` (BPHS-29).

    Never returns the house itself or its 7th (BPHS-29:241); the four lord-positions that would are
    redirected per the chapter's worked exceptions."""
    d = ((lord_sign - house_sign) % 12) + 1           # the lord's house from this house, 1..12
    if d == 1:                                        # lord in the 1st -> the 10th from the house
        return _nth_from(house_sign, 10)
    if d in (4, 7):                                   # lord in the 4th or 7th -> the 4th from the house
        return _nth_from(house_sign, 4)
    if d == 10:                                       # lord in the 10th -> the 10th (symmetric, inferred)
        return _nth_from(house_sign, 10)
    return ((2 * lord_sign - house_sign - 1) % 12) + 1


def bhava_arudhas(chart) -> dict[int, int]:
    """{house 1..12: its Arudha pada sign}, using each house's whole-sign lord's actual placement."""
    out: dict[int, int] = {}
    for house in range(1, 13):
        house_sign = ((chart.asc_sign + house - 2) % 12) + 1
        lord = SIGN_LORDS[house_sign]
        lord_sign = int(chart.longitudes[lord] % 360.0 // 30) + 1
        out[house] = arudha_pada(house_sign, lord_sign)
    return out


def arudha_lagna(chart) -> int:
    """The Arudha Lagna (AL) — the pada of the ascendant, the 'perceived self'."""
    return bhava_arudhas(chart)[1]


def upapada(chart) -> int:
    """The Upapada Lagna (UL) — the pada of the 12th house (BPHS ch.30), read for marriage."""
    return bhava_arudhas(chart)[12]


# --------------------------------------------------------------------------- #
# Spouse from the Upapada — BPHS ch.30 sl.7-12                                 #
# --------------------------------------------------------------------------- #

UPAPADA_SPOUSE_SOURCE: Final[Citation] = Citation("BPHS-30", 113)   # sl.7-12, EFFECT OF 2ND FROM UPAPADA

#: signs owned by a natural benefic (Jupiter, Venus, Mercury, Moon).
_BENEFIC_SIGNS: Final[frozenset[int]] = frozenset({4, 3, 6, 7, 2, 9, 12})
_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})


def _debilitation(planet: str) -> int:
    return ((EXALTATION[planet] + 6 - 1) % 12) + 1


@dataclass(frozen=True)
class SpouseFromUpapada:
    upapada: int                 # UL sign
    second_sign: int             # the 2nd from the Upapada — the marriage house
    benefic_sign: bool           # the 2nd-from-UL is a benefic-owned sign
    benefic_related: bool        # a benefic occupies or aspects it
    occupants: tuple[str, ...]   # planets in the 2nd-from-UL
    afflicted: bool              # an occupant debilitated, or with a debilitated/malefic -> loss of wife
    excellent: bool              # an occupant exalted/own, or aspected -> many good wives
    gemini_special: bool         # the 2nd-from-UL is Gemini -> many wives
    verdict: str                 # "favourable" | "afflicted" | "mixed" | "neutral"


def spouse_from_upapada(chart) -> SpouseFromUpapada:
    """BPHS ch.30 sl.7-12: marriage read from the 2nd from the Upapada. A benefic sign / benefic
    occupying or aspecting it gives a good spouse and progeny; an occupant debilitated (or with a
    debilitated/malefic) means destruction of the wife; an occupant exalted/own or aspected means
    many charming virtuous wives; Gemini there also many. Only the clean core clauses are encoded;
    the finer conditions (own-lord -> death at advanced age, 2nd-lord placements) are left descriptive."""
    from app.parashara.primitives import graha_drishti as gd

    ul = upapada(chart)
    second = _nth_from(ul, 2)
    signs = {p: int(chart.longitudes[p] % 360.0 // 30) + 1 for p in chart.longitudes}
    occupants = tuple(sorted(p for p, s in signs.items() if s == second))
    aspecters = set(gd.planets_aspecting_sign(second, signs))

    benefic_sign = second in _BENEFIC_SIGNS
    benefic_related = any(p in _BENEFICS for p in set(occupants) | aspecters)

    def debilitated(p: str) -> bool:
        return signs.get(p) == _debilitation(p)

    afflicted = any(
        debilitated(occ)
        or any(q != occ and signs[q] == second and (debilitated(q) or q not in _BENEFICS)
               for q in signs)
        for occ in occupants)
    excellent = any(signs[occ] == EXALTATION.get(occ) or SIGN_LORDS[signs[occ]] == occ
                    for occ in occupants) or bool(occupants and aspecters)
    gemini_special = second == 3

    favourable = benefic_sign or benefic_related or excellent or gemini_special
    verdict = ("mixed" if favourable and afflicted else "favourable" if favourable
               else "afflicted" if afflicted else "neutral")
    return SpouseFromUpapada(upapada=ul, second_sign=second, benefic_sign=benefic_sign,
                             benefic_related=benefic_related, occupants=occupants,
                             afflicted=afflicted, excellent=excellent,
                             gemini_special=gemini_special, verdict=verdict)


# --------------------------------------------------------------------------- #
# Pada and finance — BPHS ch.29 sl.8-15                                        #
# --------------------------------------------------------------------------- #

FINANCE_SOURCE: Final[Citation] = Citation("BPHS-29", 329)         # sl.8-11, 11th from Lagna Pada
UNINTERRUPTED_SOURCE: Final[Citation] = Citation("BPHS-29", 344)   # sl.12, 12th unaspected
QUANTUM_SOURCE: Final[Citation] = Citation("BPHS-29", 357)         # sl.13-15, quantum by count

#: For the wealth verdict, benefics confer virtuous means, malefics questionable (BPHS-29:334).
_DHANA_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})


@dataclass(frozen=True)
class PadaFinance:
    arudha_lagna: int            # AL sign
    eleventh_sign: int           # the 11th from AL — the wealth house
    related: tuple[str, ...]     # planets occupying OR aspecting the 11th from AL
    nature: str                  # "virtuous" | "questionable" | "both" | "none"
    quantum: int                 # number of planets related to the 11th (the gain magnitude)
    amplified: bool              # a related planet is exalted or in own sign (plenty of gains)
    uninterrupted: bool          # 11th related AND the 12th from AL is neither occupied nor aspected


def pada_finance(chart) -> PadaFinance:
    """BPHS ch.29 sl.8-15: wealth from the planets occupying or aspecting the 11th from the Arudha
    Lagna. Benefics -> virtuous means, malefics -> questionable; the count sets the quantum; an
    exalted/own planet there means plenty; the 12th-from-AL being unaspected makes gains uninterrupted."""
    from app.parashara.primitives import graha_drishti as gd

    al = arudha_lagna(chart)
    eleventh = _nth_from(al, 11)
    twelfth = _nth_from(al, 12)
    signs = {p: int(chart.longitudes[p] % 360.0 // 30) + 1 for p in chart.longitudes}

    def related_to(target: int) -> list[str]:
        occ = [p for p, s in signs.items() if s == target]
        asp = list(gd.planets_aspecting_sign(target, signs))
        return sorted(set(occ) | set(asp))

    r11 = related_to(eleventh)
    benefic = any(p in _DHANA_BENEFICS for p in r11)
    malefic = any(p not in _DHANA_BENEFICS for p in r11)
    nature = ("both" if benefic and malefic else "virtuous" if benefic
              else "questionable" if malefic else "none")
    amplified = any(signs[p] == EXALTATION.get(p) or SIGN_LORDS[signs[p]] == p for p in r11)
    uninterrupted = bool(r11) and not related_to(twelfth)
    return PadaFinance(arudha_lagna=al, eleventh_sign=eleventh, related=tuple(r11),
                       nature=nature, quantum=len(r11), amplified=amplified,
                       uninterrupted=uninterrupted)
