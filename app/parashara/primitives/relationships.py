"""Planetary relationships — natural, temporary, and the 5-fold compound (BPHS ch.3, slokas 55-58).

This is the input Vimsopaka needs (its Varga Viswa scale is keyed on the compound relationship),
and it is root doctrine in its own right.

**Derived from Parashara's rule, not copied from a table.** Sloka 55 gives a *formula*, and the
chapter then prints a table "for an easy grasp". Encoding the formula and letting the table act as
a check is the faithful direction: a copied table is only as good as the OCR of its columns, while
the rule reproduces it and shows its working. `tests/parashara/primitives/test_relationships.py`
pins the two worked examples Parashara gives in his own notes.

## Natural / naisargika (BPHS-3:934, sloka 55)

    "Note the signs which are the 4th, 2nd, 12th, 5th, 9th and the 8th from the Moolatrikona of a
     planet. The planets ruling such signs are its friends, apart from the lord of its exaltation
     sign. Lords other than these are its enemies. If a planet becomes its friend as well as its
     enemy ... then it is neutral or equal."

So: friend-houses {2,4,5,8,9,12} from moolatrikona, PLUS the exaltation lord always; the rest
({3,6,7,10,11}) are enemies; and a planet arriving on BOTH lists is equal. A planet owns two signs,
which is exactly how both lists can name it — Parashara's own example: Venus owns the 2nd and the
7th from Mars's moolatrikona, "hence he is neutral to Mars".

## Temporary / tatkalika (BPHS-3:1045, sloka 56)

    "The planet posited in the 10th, 4th, 11th, 3rd, 2nd or the 12th from another becomes mutual
     friend. There is enmity otherwise."

Positional and therefore chart-specific: {2,3,4,10,11,12} away = temporary friend, else enemy.
There is no temporary "neutral" — the sloka admits only the two.

## Compound / panchadha maitri (BPHS-3:1063, slokas 57-58)

    natural + temporary  ->  compound
    friend   + friend    ->  adhi_mitra   (extremely friendly)
    friend   + neutral   ->  mitra        ("friendship on one count and neutrality on another")
    friend   + enemy     ->  sama         ("enmity ... combined with affinity ... turns into equality")
    neutral  + friend    ->  mitra
    neutral  + enemy     ->  shatru       ("enmity and neutralship cause only enmity")
    enemy    + enemy     ->  adhi_shatru  (extreme enmity)

Usage:
    from app.parashara.primitives.relationships import naisargika, compound
    naisargika("Saturn", "Mars")                  # 'sama' - Parashara's own worked example
    compound("Jupiter", "Mars", house_distance=4) # 'adhi_mitra'
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

#: The seven grahas Parashara's relationship doctrine covers. Rahu/Ketu have no moolatrikona or
#: exaltation lordship in this scheme, so the sloka's formula simply does not reach them; callers
#: must decide how to treat the nodes rather than have a default invented for them here.
GRAHAS: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

#: sign number (1=Aries..12=Pisces) -> its lord.
SIGN_LORDS: Final[Mapping[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

#: Moolatrikona SIGN per graha (BPHS ch.3). The degree-span matters elsewhere; sloka 55 counts
#: from the sign alone.
MOOLATRIKONA: Final[Mapping[str, int]] = {
    "Sun": 5, "Moon": 2, "Mars": 1, "Mercury": 6, "Jupiter": 9, "Venus": 7, "Saturn": 11,
}

#: Exaltation sign per graha — its lord is "always friendly" (sloka 55).
EXALTATION: Final[Mapping[str, int]] = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6, "Jupiter": 4, "Venus": 12, "Saturn": 7,
}

#: Houses from the moolatrikona whose lords are natural friends (sloka 55).
_FRIEND_HOUSES: Final[frozenset[int]] = frozenset({2, 4, 5, 8, 9, 12})
#: Houses from another planet that make a temporary friend (sloka 56).
_TEMPORARY_FRIEND_HOUSES: Final[frozenset[int]] = frozenset({2, 3, 4, 10, 11, 12})

NAISARGIKA_SOURCE: Final[Citation] = Citation("BPHS-3", 934)
TEMPORARY_SOURCE: Final[Citation] = Citation("BPHS-3", 1045)
COMPOUND_SOURCE: Final[Citation] = Citation("BPHS-3", 1063)


def _signs_owned(planet: str) -> tuple[int, ...]:
    return tuple(s for s, lord in SIGN_LORDS.items() if lord == planet)


def naisargika(of: str, towards: str) -> str:
    """Natural relationship of `of` towards `towards`: 'mitra' | 'sama' | 'shatru'.

    Applies sloka 55 directly: count each sign `towards` owns from `of`'s moolatrikona; a
    friend-house or the exaltation lordship makes a friend, the rest make an enemy, and landing on
    both lists ("friend as well as its enemy") makes it equal.
    """
    if of not in MOOLATRIKONA or towards not in MOOLATRIKONA:
        raise ValueError(f"relationship is defined for {GRAHAS}, got {of!r} -> {towards!r}")
    if of == towards:
        return "sama"

    mt = MOOLATRIKONA[of]
    friendly = towards == SIGN_LORDS[EXALTATION[of]]   # exaltation lord is ALWAYS friendly
    inimical = False
    for sign in _signs_owned(towards):
        house = ((sign - mt) % 12) + 1                 # 1-indexed house from the moolatrikona
        if house in _FRIEND_HOUSES:
            friendly = True
        else:
            inimical = True

    if friendly and inimical:
        return "sama"                                  # "none prevails but equality"
    return "mitra" if friendly else "shatru"


def temporary(house_distance: int) -> str:
    """Temporary relationship from one graha's house-distance to another: 'mitra' | 'shatru'.

    `house_distance` is 1-indexed as Parashara counts (the planet's own sign is the 1st). Sloka 56
    admits only friend or enemy — there is no temporary neutral.
    """
    d = ((int(house_distance) - 1) % 12) + 1
    return "mitra" if d in _TEMPORARY_FRIEND_HOUSES else "shatru"


#: (natural, temporary) -> compound. Slokas 57-58, stated as a table so the mapping is readable
#: and cannot drift into an if-cascade nobody can check against the text.
_COMPOUND: Final[Mapping[tuple[str, str], str]] = {
    ("mitra", "mitra"): "adhi_mitra",
    ("mitra", "shatru"): "sama",
    ("sama", "mitra"): "mitra",
    ("sama", "shatru"): "shatru",
    ("shatru", "mitra"): "sama",
    ("shatru", "shatru"): "adhi_shatru",
}


def compound(of: str, towards: str, *, house_distance: int) -> str:
    """The 5-fold compound relationship — the value Vimsopaka's Varga Viswa is keyed on.

    Returns one of 'adhi_mitra' | 'mitra' | 'sama' | 'shatru' | 'adhi_shatru'.
    """
    nat = naisargika(of, towards)
    tmp = temporary(house_distance)
    return _COMPOUND[(nat, tmp)]


def dignity_in_sign(planet: str, sign: int) -> int:
    """+1 if `planet` is in own sign or exaltation, -1 if debilitated or in an enemy's sign, else 0.

    The ch.3 dignity read used identically for D1 and divisional signs — the ONE shared answer to
    "is this graha dignified in this sign" (richer_bhava and the synthesis corroboration previously
    carried diverging private copies; unified 2026-08-29). Nodes (no exaltation in ch.3's scheme)
    return 0.
    """
    if planet not in EXALTATION:
        return 0
    if sign == EXALTATION[planet] or SIGN_LORDS.get(sign) == planet:
        return 1
    if sign == ((EXALTATION[planet] - 1 + 6) % 12) + 1:          # debilitation = 7th from exaltation
        return -1
    if naisargika(planet, SIGN_LORDS[sign]) == "shatru":         # an enemy's sign
        return -1
    return 0


def varga_viswa_key(planet: str, varga_sign: int, *,
                    compound_relation: str | None = None) -> str:
    """The Varga Viswa key for `planet` sitting in `varga_sign` within some division.

    Own sign scores the full 20 regardless of relationship ("the Vimsopaka strength remains as 20
    ... only when the planet is in own house Vargas", BPHS-7:270), so own-sign short-circuits.
    Otherwise the caller supplies the compound relationship to that sign's lord.
    """
    lord = SIGN_LORDS[varga_sign]
    if lord == planet:
        return "own"
    if compound_relation is None:
        raise ValueError(
            f"{planet} in sign {varga_sign} is not its own; a compound relation to {lord} "
            f"is required to score the Varga Viswa")
    return compound_relation
