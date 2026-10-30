"""Chara dasha: the twelve-sign rasi dasa (BPHS ch.46 sl.155-167) and its antardashas (BPHS-51 sl.5-12).

Every rule is ruled on, with verbatim passages, in `docs/parashara/CHARA_DASHA_RULINGS.md`. In short:

* PADA (sl.155-156): "every three signs from Aries etc. have four padas". Odd padas (savya) are
  Aries-Gemini and Libra-Sagittarius; even padas (apasavya) are Cancer-Virgo and Capricorn-Pisces.
* SEQUENCE (sl.167): it begins at the Lagna sign and runs onwards if the 9th sign is in an odd pada,
  in reverse if even. It repeats after the twelve (46:4837).
* YEARS (sl.155-156): count from the sign to its lord's sign, onwards for an odd-pada sign and in
  reverse for an even-pada sign. Years = n - 1. BPHS's own printed 1-year dasas (Aries 46:4789,
  Pisces 46:5037) are reachable only this way.
  - CONVENTION (Jaimini commentary + Raman): a lord in its own sign gives 12 years.
  - CONVENTION (Jaimini commentary + Raman): an exalted lord adds one year and a debilitated lord
    removes one, applied to the n - 1 figure.
* DUAL LORDS (sl.157-166): Mars+Ketu own Scorpio, Saturn+Rahu own Aquarius.
  - Both lords in the sign: 12 years. One in it and one out: count to the other.
  - Otherwise, the stronger lord: the one with a planet; then more planets; then the stronger sign
    (dual > fixed > movable). If still equal, CONVENTION: a lone exalted lord, then the larger years.
    All three sources put exaltation LAST (BPHS 46:4725, Jaimini ch.9:800, Raman art.86).
* ANTARDASHAS (BPHS-51 sl.5, sl.7-12, as the translator works them at 51:601-670; the owner chose this
  on 2026-10-24, and sl.6's "or from the 7th, whichever is stronger" is recorded as dissent):
  - each is 1/12 of the dasa (sl.5);
  - movable dasa rasi: the twelve in order from itself;
  - fixed: itself, then every 6th rasi;
  - dual: itself and its kendras, then the kendras of its 5th, then of its 9th;
  - onwards if the dasa ("Paka") rasi is an odd SIGN, in reverse if even (not pada).

NODE EXALTATION: BPHS-47:280-284 gives Rahu Taurus and Ketu Scorpio. The engine's general table
(`relationships.EXALTATION`) omits the nodes, so they are added here for this rule only, because Rahu
and Ketu co-own Aquarius and Scorpio. BPHS states no node debilitation, so the nodes only ever add.
`rasi_dasha.rasi_timeline` is not used: its start-sign-parity traversal is Sthira's rule (sl.168-169),
while Chara's direction comes from the 9th sign's pada (sl.167).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.rasi_dasha import modality
from app.parashara.primitives.relationships import EXALTATION, SIGN_LORDS

PADA_SOURCE: Final[Citation] = Citation("BPHS-46", 4660)          # "every three signs… four padas"
YEARS_SOURCE: Final[Citation] = Citation("BPHS-46", 4658)         # "reckoned from the Rasi up to… its lord"
CO_LORD_SOURCE: Final[Citation] = Citation("BPHS-46", 4669)       # Mars+Ketu Scorpio, Saturn+Rahu Aquarius
DUAL_LORD_SOURCE: Final[Citation] = Citation("BPHS-46", 4703)     # both in own -> 12; one in own -> the other
STRENGTH_SOURCE: Final[Citation] = Citation("BPHS-46", 4710)      # planet > more planets > sign nature
EXALTATION_ADJ_SOURCE: Final[Citation] = Citation("BPHS-46", 4727)  # +1 exalted / -1 debilitated
SEQUENCE_SOURCE: Final[Citation] = Citation("BPHS-46", 4733)      # 9th in odd pada -> onwards from Lagna
REPEAT_SOURCE: Final[Citation] = Citation("BPHS-46", 4837)        # "will again become the starting point"
ARIES_ONE_YEAR: Final[Citation] = Citation("BPHS-46", 4789)       # worked: "Chara Dasa for Aries… one year"
PISCES_ONE_YEAR: Final[Citation] = Citation("BPHS-46", 5037)      # worked: "Chara Dasa of Pisces is one year"
#: CONVENTIONS (BPHS silent or ambiguous; the Jaimini Sutras' commentary decides, Raman agrees).
OWN_SIGN_TWELVE: Final[Citation] = Citation("JAIMINI-9", 752)     # "in his own house, the sign gives 12 years"
EXALTATION_ANY_SIGN: Final[Citation] = Citation("JAIMINI-9", 756)  # the lord exalted adds one year (every sign)
LARGER_YEARS_TIE: Final[Citation] = Citation("JAIMINI-9", 797)    # "take that lord who gives the larger number of years"
EXALTED_LORD_LAST: Final[Citation] = Citation("JAIMINI-9", 800)   # "If one of them is in exaltation, he should be preferred"
RAHU_EXALTATION: Final[Citation] = Citation("BPHS-47", 280)       # "exaltation of Rahu is Taurus"
KETU_EXALTATION: Final[Citation] = Citation("BPHS-47", 284)       # "exaltation of Ketu is Scorpio"
AD_FIXED_WORKED: Final[Citation] = Citation("BPHS-51", 602)     # worked: "Aquarius is a fixed and odd rasi… every sixth"
AD_LENGTH_SOURCE: Final[Citation] = Citation("BPHS-51", 529)      # "dividing the Dasa years by 12"
AD_ORDER_SOURCE: Final[Citation] = Citation("BPHS-51", 578)       # movable / fixed "every sixth" / dual kendras
AD_DIRECTION_SOURCE: Final[Citation] = Citation("BPHS-51", 587)   # "onwards, if the Dasa asraya rasi be an odd one"
AD_PAKA_IS_DASA_RASI: Final[Citation] = Citation("BPHS-51", 663)  # worked: "Here Pisces is Paka rasi"
AD_MOVABLE_FROM_ITSELF: Final[Citation] = Citation("BPHS-51", 670)  # CONVENTION: verse silent; translator's "(including Aries)"
AD_SL6_DISSENT: Final[Citation] = Citation("BPHS-51", 541)        # "from the Dasa rasi or from the rasi 7th… whichever is stronger"

SAVYA: Final[frozenset[int]] = frozenset({1, 2, 3, 7, 8, 9})     # odd padas
CO_LORDS: Final[Mapping[int, tuple[str, str]]] = {8: ("Mars", "Ketu"), 11: ("Saturn", "Rahu")}
_SIGN_STRENGTH: Final[Mapping[str, int]] = {"movable": 1, "fixed": 2, "dual": 3}   # BPHS-46:4721
OWN_SIGN_YEARS: Final[int] = 12
NODE_EXALTATION: Final[Mapping[str, int]] = {"Rahu": 2, "Ketu": 8}


@dataclass(frozen=True)
class CharaPeriod:
    sign: int
    years: float
    start_year: float     # years after birth
    end_year: float


def is_savya(sign: int) -> bool:
    """Odd pada (BPHS-46 sl.155-156): Aries-Gemini, Libra-Sagittarius."""
    return sign in SAVYA


def count(from_sign: int, to_sign: int, *, forward: bool) -> int:
    """Inclusive sign count 1..12 (the sign itself = 1)."""
    d = (to_sign - from_sign) % 12 if forward else (from_sign - to_sign) % 12
    return d + 1


def _adjust(planet: str, sign_of: int) -> int:
    """+1 exalted, -1 debilitated, else 0 (nodes: +1 in their BPHS-47 exaltation sign only)."""
    if planet in NODE_EXALTATION:
        return int(sign_of == NODE_EXALTATION[planet])
    ex = EXALTATION.get(planet)
    if ex is None:
        return 0
    return 1 if sign_of == ex else -1 if sign_of == (ex - 1 + 6) % 12 + 1 else 0


def _years_to(sign: int, lord: str, signs: Mapping[str, int]) -> int:
    """n - 1 counted in the sign's pada direction, then +-1 for the lord's dignity."""
    ls = signs[lord]
    if ls == sign:
        return OWN_SIGN_YEARS
    return count(sign, ls, forward=is_savya(sign)) - 1 + _adjust(lord, ls)


def _associates(planet: str, signs: Mapping[str, int]) -> int:
    return sum(1 for p, s in signs.items() if p != planet and s == signs[planet])


def dasa_lord(sign: int, signs: Mapping[str, int]) -> str:
    """The lord whose position fixes the sign's years (the stronger co-lord for Scorpio/Aquarius)."""
    if sign not in CO_LORDS:
        return SIGN_LORDS[sign]
    a, b = CO_LORDS[sign]
    a_in, b_in = signs[a] == sign, signs[b] == sign
    if a_in != b_in:                                # one in own sign -> count to the other
        return b if a_in else a
    def strength(p: str) -> tuple:
        n = _associates(p, signs)
        return (n > 0, n, _SIGN_STRENGTH[modality(signs[p])],
                _adjust(p, signs[p]) == 1, _years_to(sign, p, signs))
    return a if strength(a) >= strength(b) else b


def years(sign: int, signs: Mapping[str, int]) -> int:
    """The chara dasa years of `sign` (0 is possible: n = 2 with a debilitated lord)."""
    if sign in CO_LORDS and all(signs[p] == sign for p in CO_LORDS[sign]):
        return OWN_SIGN_YEARS                       # both lords in the sign
    return _years_to(sign, dasa_lord(sign, signs), signs)


def sequence(asc_sign: int, signs: Mapping[str, int]) -> tuple[tuple[int, int], ...]:
    """The twelve (sign, years) from the Lagna sign, onwards iff the 9th sign is in an odd pada."""
    step = 1 if is_savya((asc_sign - 1 + 8) % 12 + 1) else -1
    order = [(asc_sign - 1 + step * i) % 12 + 1 for i in range(12)]
    return tuple((s, years(s, signs)) for s in order)


def timeline(asc_sign: int, signs: Mapping[str, int], *, horizon: float = 120.0) -> tuple[CharaPeriod, ...]:
    """Mahadashas from birth to `horizon` years, the twelve repeating (46:4837). Zero-year signs are skipped."""
    seq = sequence(asc_sign, signs)
    if sum(y for _, y in seq) <= 0:
        return ()
    out, cursor = [], 0.0
    while cursor < horizon:
        for s, y in seq:
            if y > 0:
                out.append(CharaPeriod(sign=s, years=y, start_year=cursor, end_year=cursor + y))
                cursor += y
    return tuple(out)


def chart_signs(chart) -> dict[str, int]:
    """Graha -> sign 1..12 from a ParasharaChart (nodes included: they co-own Scorpio/Aquarius)."""
    return {p: int(lon % 360.0 // 30) + 1 for p, lon in chart.longitudes.items()}


def antardasha_signs(dasa_sign: int) -> tuple[int, ...]:
    """The twelve antardasha signs of a chara dasa, in order (BPHS-51 sl.7-12, the 51:601-670 worked note)."""
    step = 1 if dasa_sign % 2 == 1 else -1
    at = lambda base, k: (base - 1 + step * k) % 12 + 1          # noqa: E731 - k-th onward/back from base
    kind = modality(dasa_sign)
    if kind == "movable":
        return tuple(at(dasa_sign, k) for k in range(12))
    if kind == "fixed":
        return tuple(at(dasa_sign, 5 * k) for k in range(12))     # every 6th rasi
    return tuple(at(at(dasa_sign, 4 * b), 3 * k) for b in range(3) for k in range(4))   # kendras of 1st/5th/9th


def antardashas(period: CharaPeriod) -> tuple[CharaPeriod, ...]:
    """The period's twelve antardashas, each 1/12 of it (BPHS-51 sl.5)."""
    part = period.years / 12
    return tuple(CharaPeriod(sign=s, years=part, start_year=period.start_year + i * part,
                             end_year=period.start_year + (i + 1) * part)
                 for i, s in enumerate(antardasha_signs(period.sign)))
