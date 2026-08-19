"""Ashtakavarga sodhana (reductions) per HPA Ch. XXVI, rules 10-23.

Raman's dedicated *Ashtakavarga System of Prediction* has no retrievable
text (see docs/raman_doctrine/SOURCES.md), so this module implements the
reductions exactly as printed in **Hindu Predictive Astrology, Ch. XXVI
(pp. 302-311)**, whose worked example (the Sun's Ashtakavarga of the
specimen horoscope) is the golden test.

Trikona (triangular) reduction — rules 10-13, Raman's adopted view
("subtract the least of the three figures from the other two and retain
the remainders"; footnote p. 303 records the rejected alternative view):

  * R10: no zeros in the triad -> subtract the triad minimum from all
    three (the minimum positions become 0; all-equal (R13) degenerates
    to all zero).
  * R11: exactly one zero in the triad -> no reduction.
  * R12: two zeros -> the third figure is also eliminated.

Ekadhipatya (dual-ownership) reduction — rules 14-18, applied after
trikona to the five two-sign lordship pairs (Cancer and Leo exempt, R18).
Occupancy means a NON-SHADOW planet in the sign ("let alone Kethu in
Virgo, a shadowy planet", p. 306):

  * R17: a zero in either sign of the pair -> no reduction (takes
    precedence; the worked example applies it to 2/0, 3/0, 0/0, 2/0).
  * R14: both signs occupied -> no reduction.
  * R15: one occupied, one not: (a) occupied figure smaller -> unoccupied
    becomes equal to it; (b) occupied larger -> unoccupied eliminated;
    (c) equal -> unoccupied eliminated.
  * R16: both unoccupied: equal -> both eliminated; unequal -> larger
    reduced to the smaller.

Applications (rules 21-23, same chapter) use the post-reduction total
directly. The classical sodhya-pinda *gunakara* multipliers are NOT
implemented: HPA never prints them and the book that does is unavailable —
deferred until a rule from an available text demands them (recorded
design decision, "truest to Raman" over completeness).
"""
from __future__ import annotations

import dataclasses
from collections.abc import Collection, Sequence

# Sign indices are 1..12 (Aries..Pisces) repo-wide.
TRIKONA_GROUPS: tuple[tuple[int, int, int], ...] = (
    (1, 5, 9), (2, 6, 10), (3, 7, 11), (4, 8, 12),
)
# (sign_a, sign_b) pairs under one lord; Cancer(4)/Leo(5) exempt (R18).
EKADHIPATYA_PAIRS: tuple[tuple[int, int], ...] = (
    (1, 8),    # Mars
    (2, 7),    # Venus
    (3, 6),    # Mercury
    (9, 12),   # Jupiter
    (10, 11),  # Saturn
)
# Rule 23 dik (direction) of each trikona group, Aries-group first.
TRIKONA_DIRECTIONS: tuple[str, ...] = ("east", "south", "west", "north")


@dataclasses.dataclass(frozen=True)
class SodhanaResult:
    after_trikona: tuple[int, ...]      # 12 bindus, Aries..Pisces
    after_ekadhipatya: tuple[int, ...]  # 12 bindus after both reductions
    total: int                          # sum after both reductions


def _check_bav(bav: Sequence[int]) -> list[int]:
    row = [int(b) for b in bav]
    if len(row) != 12 or any(not 0 <= b <= 8 for b in row):
        raise ValueError(f"bav must be 12 bindu counts in 0..8, got {bav!r}")
    return row


def trikona_sodhana(bav: Sequence[int]) -> list[int]:
    """First reduction (rules 10-13). Input/output indexed 0..11 = Aries..Pisces."""
    row = _check_bav(bav)
    for group in TRIKONA_GROUPS:
        idx = [s - 1 for s in group]
        vals = [row[i] for i in idx]
        zeros = sum(1 for v in vals if v == 0)
        if zeros == 1:              # R11
            continue
        if zeros == 2:              # R12
            for i in idx:
                row[i] = 0
            continue
        if zeros == 3:
            continue
        least = min(vals)           # R10 (R13 degenerates to all-zero)
        for i in idx:
            row[i] -= least
    return row


def ekadhipatya_sodhana(bav: Sequence[int], occupied_signs: Collection[int]) -> list[int]:
    """Second reduction (rules 14-18).

    ``occupied_signs``: signs (1..12) holding at least one NON-shadow
    planet in the radix chart (Rahu/Ketu never count as occupants).
    """
    row = _check_bav(bav)
    occupied = {int(s) for s in occupied_signs}
    if not occupied <= set(range(1, 13)):
        raise ValueError(f"occupied_signs must be 1..12, got {occupied_signs!r}")
    for sign_a, sign_b in EKADHIPATYA_PAIRS:
        a, b = sign_a - 1, sign_b - 1
        if row[a] == 0 or row[b] == 0:          # R17 (precedes R15/R16)
            continue
        occ_a, occ_b = sign_a in occupied, sign_b in occupied
        if occ_a and occ_b:                      # R14
            continue
        if occ_a != occ_b:                       # R15
            o, u = (a, b) if occ_a else (b, a)
            if row[o] < row[u]:
                row[u] = row[o]
            else:                                # greater or equal
                row[u] = 0
        else:                                    # R16: both unoccupied
            if row[a] == row[b]:
                row[a] = row[b] = 0
            elif row[a] > row[b]:
                row[a] = row[b]
            else:
                row[b] = row[a]
    return row


def sodhana(bav: Sequence[int], occupied_signs: Collection[int]) -> SodhanaResult:
    """Both reductions in order; ``total`` is the figure rules 21-22 consume."""
    first = trikona_sodhana(bav)
    second = ekadhipatya_sodhana(first, occupied_signs)
    return SodhanaResult(
        after_trikona=tuple(first),
        after_ekadhipatya=tuple(second),
        total=sum(second),
    )


def maraka_nakshatra(total: int, bindus_in_9th_from_planet: int) -> int:
    """Rule 21: nakshatra index 1..27 from Aswini whose Saturn transit
    (or of its trines) marks danger to the father, dasa permitting."""
    rem = (int(total) * int(bindus_in_9th_from_planet)) % 27
    return rem if rem != 0 else 27


def maraka_rasi(total: int, bindus_in_8th_from_planet: int) -> int:
    """Rule 22: sign 1..12 from Aries (with its trines) whose Sun transit
    marks the native's own danger, dasa permitting."""
    rem = (int(total) * int(bindus_in_8th_from_planet)) % 12
    return rem if rem != 0 else 12


def best_direction(after_reduction: Sequence[int]) -> list[str]:
    """Rule 23: direction(s) of the trikona group(s) with the largest sum."""
    row = _check_bav(after_reduction)
    sums = [sum(row[s - 1] for s in group) for group in TRIKONA_GROUPS]
    top = max(sums)
    return [TRIKONA_DIRECTIONS[i] for i, s in enumerate(sums) if s == top]
