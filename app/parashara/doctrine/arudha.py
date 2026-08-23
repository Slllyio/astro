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

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import SIGN_LORDS

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
