"""Ashtakavarga reductions — Thrikona and Ekadhipathya Sodhana (HPA-26).

Raman: "The table prepared for each planet containing benefic dots must be subjected to two
reductions, viz., Thrikona reduction and Ekadhipathya reduction" (HPA-26:390-393). They are
ORDERED — "After the Thrikona reduction, the Ekadhipathya reduction must be applied"
(HPA-26:466-467) — and `reduced_bhinnashtakavarga` applies them in that order.

**The fidelity trap, in Raman's own footnote (HPA-26:423-431).** Thrikona Sodhana has two
distinct readings in the literature: subtract the least of the three trinal figures from each of
the other two, OR alter all three to equal the least. They give different tables. Raman states
which one he follows — *"we have adopted the former, for reasons we have dealt with in our book
on Ashtakavarga"* — so this module implements the SUBTRACT reading. Do not "simplify" it to the
equalise reading; it is not a rounding choice, it is the wrong book's doctrine.

Raman's own worked example (the Sun's BAV, HPA-26:432-462) is the regression fixture and pins
exactly this: 5,3,3 -> 2,0,0 and 5,2,5 -> 3,0,3.

Usage:
    from app.raman_saab.primitives.ashtakavarga_reduction import reduced_bhinnashtakavarga
    reduced = reduced_bhinnashtakavarga(chart, "Sun")     # {sign: bindus} after BOTH reductions
"""
from __future__ import annotations

from typing import Final, Mapping

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.ashtakavarga import PLANETS, bhinnashtakavarga

#: The four equilateral-triangle groups (HPA-26:397-402): Aries/Leo/Sagittarius,
#: Taurus/Virgo/Capricorn, Gemini/Libra/Aquarius, Cancer/Scorpio/Pisces.
TRIKONA_GROUPS: Final[tuple[tuple[int, int, int], ...]] = (
    (1, 5, 9), (2, 6, 10), (3, 7, 11), (4, 8, 12))

#: Signs exempt from Ekadhipathya (HPA-26:495-497): "Cancer and Leo as they are not
#: Ekadhipathya rasis are not subject to this reduction" — the Moon and the Sun each own ONE
#: sign, so there is no dual ownership to reduce.
_SOLE_OWNED: Final[frozenset[int]] = frozenset({4, 5})       # Cancer, Leo

#: The other five planets each own two signs (HPA-26:468-471).
EKADHIPATYA_PAIRS: Final[tuple[tuple[int, int], ...]] = (
    (1, 8),     # Mars    — Aries, Scorpio
    (2, 7),     # Venus   — Taurus, Libra
    (3, 6),     # Mercury — Gemini, Virgo
    (9, 12),    # Jupiter — Sagittarius, Pisces
    (10, 11),   # Saturn  — Capricorn, Aquarius
)


def trikona_shodhana(bav: Mapping[int, int]) -> dict[int, int]:
    """Thrikona (trinal) reduction of one Bhinnashtakavarga — HPA-26:403-421.

    Per trinal group, in the order Raman states the special cases:
      - rule 12: figures absent in TWO of the three -> the third is eliminated too
      - rule 11: a figure absent in ONE of the three -> no reduction at all
      - rule 13: all three equal -> all removed
      - rule 10: otherwise subtract the LEAST of the three from each (see the module docstring
        on why this is subtraction and not equalisation)

    Rules 12 and 11 are tested BEFORE 10 because a zero already present in the group changes the
    answer; the zeros rule 10 itself produces are not re-examined."""
    out = dict(bav)
    for group in TRIKONA_GROUPS:
        vals = [out[s] for s in group]
        zeros = sum(1 for v in vals if v == 0)
        if zeros >= 2:                       # rule 12
            for s in group:
                out[s] = 0
        elif zeros == 1:                     # rule 11 — leave the group untouched
            continue
        elif vals[0] == vals[1] == vals[2]:  # rule 13
            for s in group:
                out[s] = 0
        else:                                # rule 10
            least = min(vals)
            for s in group:
                out[s] -= least
    return out


def _occupied_signs(chart: RamanChart) -> frozenset[int]:
    """Signs tenanted by one of the seven grahas.

    The seven, not nine: the whole Ashtakavarga apparatus is built on the seven visible grahas
    plus the Lagna (see `ashtakavarga._REFS`), and Rahu/Ketu contribute no bindus to it, so
    letting them decide an occupancy question inside the same system would be inconsistent."""
    return frozenset(p.sign for name, p in chart.planets.items() if name in PLANETS)


def ekadhipatya_shodhana(bav: Mapping[int, int], chart: RamanChart) -> dict[int, int]:
    """Ekadhipathya (dual-ownership) reduction — HPA-26:464-497.

    For each pair of signs owned by one planet (Cancer and Leo exempt, rule 18):
      - rule 14: planets in BOTH signs            -> no reduction
      - rule 17: no figure in one of the two      -> no reduction
      - rule 15: exactly one occupied, where `o` is the occupied and `u` the unoccupied —
            (a) o < u  -> u := o          (b) o > u  -> u := 0          (c) o == u -> u := 0
      - rule 16: neither occupied —
            equal -> both eliminated;  unequal -> the larger reduced to the smaller

    Rule 17 is checked before 15/16 for the same reason as in the trinal pass: an existing zero
    suppresses the reduction rather than feeding it."""
    out = dict(bav)
    occupied = _occupied_signs(chart)
    for a, b in EKADHIPATYA_PAIRS:
        if a in _SOLE_OWNED or b in _SOLE_OWNED:      # rule 18 (defensive; the pairs exclude them)
            continue
        va, vb = out[a], out[b]
        occ_a, occ_b = a in occupied, b in occupied
        if occ_a and occ_b:                           # rule 14
            continue
        if va == 0 or vb == 0:                        # rule 17
            continue
        if occ_a or occ_b:                            # rule 15
            o_sign, u_sign = (a, b) if occ_a else (b, a)
            o_val, u_val = out[o_sign], out[u_sign]
            out[u_sign] = o_val if o_val < u_val else 0
        else:                                         # rule 16
            if va == vb:
                out[a] = out[b] = 0
            elif va > vb:
                out[a] = vb
            else:
                out[b] = va
    return out


def reduced_bhinnashtakavarga(chart: RamanChart, planet: str) -> dict[int, int]:
    """`planet`'s BAV after BOTH reductions, in Raman's stated order (HPA-26:466-467)."""
    return ekadhipatya_shodhana(trikona_shodhana(bhinnashtakavarga(chart, planet)), chart)
