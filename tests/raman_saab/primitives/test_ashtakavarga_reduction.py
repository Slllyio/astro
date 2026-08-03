"""Ashtakavarga reductions — `primitives/ashtakavarga_reduction.py` (HPA-26).

Raman's own worked example on the Sun's Bhinnashtakavarga is the anchor: the trinal groups
5,3,3 -> 2,0,0 and 5,2,5 -> 3,0,3 (HPA-26:436-446).

The load-bearing test is `test_subtracts_the_least_rather_than_equalising`. Raman's footnote
(HPA-26:423-431) records TWO readings of Thrikona Sodhana — subtract the least from each, or
alter all three to equal the least — and states he follows the former. The two agree whenever
the group is already equal, so only an unequal group separates them.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives.ashtakavarga import BAV_TOTALS, PLANETS, bhinnashtakavarga
from app.raman_saab.primitives.ashtakavarga_reduction import (
    EKADHIPATYA_PAIRS,
    TRIKONA_GROUPS,
    ekadhipatya_shodhana,
    reduced_bhinnashtakavarga,
    trikona_shodhana,
)

_CANONICAL = BirthData("canonical", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def chart():
    return cast_chart(_CANONICAL, ayanamsa="raman")


def _bav(**signs: int) -> dict[int, int]:
    """A 12-sign table defaulting to 0, e.g. _bav(s1=5, s5=3, s9=3)."""
    out = {s: 0 for s in range(1, 13)}
    for key, val in signs.items():
        out[int(key[1:])] = val
    return out


class TestTrikonaRamansWorkedExample:
    def test_five_three_three_becomes_two_zero_zero(self):
        """HPA-26:436-441 — Aries/Leo/Sagittarius 5,3,3; subtract the least (3)."""
        out = trikona_shodhana(_bav(s1=5, s5=3, s9=3))
        assert (out[1], out[5], out[9]) == (2, 0, 0)

    def test_five_two_five_becomes_three_zero_three(self):
        """HPA-26:441-444 — Taurus/Virgo/Capricorn 5,2,5."""
        out = trikona_shodhana(_bav(s2=5, s6=2, s10=5))
        assert (out[2], out[6], out[10]) == (3, 0, 3)

    def test_subtracts_the_least_rather_than_equalising(self):
        """THE fidelity test (HPA-26:423-431). The rejected reading would turn 5,3,3 into
        3,3,3; Raman's adopted reading gives 2,0,0. Only an unequal group tells them apart."""
        out = trikona_shodhana(_bav(s1=5, s5=3, s9=3))
        assert (out[1], out[5], out[9]) != (3, 3, 3), "equalising reading — not Raman's"
        assert (out[1], out[5], out[9]) == (2, 0, 0)


class TestTrikonaSpecialCases:
    def test_rule_11_one_empty_sign_blocks_the_whole_group(self):
        """'No such elimination is necessary provided no figure is found in one of the three.'"""
        out = trikona_shodhana(_bav(s1=4, s5=0, s9=6))
        assert (out[1], out[5], out[9]) == (4, 0, 6)

    def test_rule_12_two_empty_signs_eliminate_the_third(self):
        """'In the absence of figures in two of the three, the figures in the third must also
        be eliminated' — this must be checked BEFORE rule 11, or a 0,0,N group would survive."""
        out = trikona_shodhana(_bav(s1=0, s5=0, s9=7))
        assert (out[1], out[5], out[9]) == (0, 0, 0)

    def test_rule_13_equal_figures_are_all_removed(self):
        out = trikona_shodhana(_bav(s4=3, s8=3, s12=3))
        assert (out[4], out[8], out[12]) == (0, 0, 0)

    def test_groups_are_independent(self):
        """A reduction in one trine must not touch another."""
        out = trikona_shodhana(_bav(s1=5, s5=3, s9=3, s2=4, s6=0, s10=6))
        assert (out[1], out[5], out[9]) == (2, 0, 0)
        assert (out[2], out[6], out[10]) == (4, 0, 6)      # rule 11, untouched

    def test_never_produces_a_negative_bindu(self, chart):
        for planet in PLANETS:
            out = trikona_shodhana(bhinnashtakavarga(chart, planet))
            assert all(v >= 0 for v in out.values()), planet


class TestEkadhipatya:
    def test_rule_18_cancer_and_leo_are_never_reduced(self, chart):
        """The Moon and Sun own ONE sign each, so there is no dual ownership to reduce."""
        assert all(4 not in pair and 5 not in pair for pair in EKADHIPATYA_PAIRS)

    def test_rule_14_both_occupied_means_no_reduction(self, chart):
        """Pick the pair the chart actually occupies twice, if any; else assert the rule holds
        vacuously by construction rather than fabricating a chart."""
        occupied = {p.sign for name, p in chart.planets.items() if name in PLANETS}
        both = [(a, b) for a, b in EKADHIPATYA_PAIRS if a in occupied and b in occupied]
        bav = _bav(**{f"s{s}": 5 for s in range(1, 13)})
        out = ekadhipatya_shodhana(bav, chart)
        for a, b in both:
            assert (out[a], out[b]) == (5, 5), f"pair {a}/{b} both occupied — must not reduce"

    def test_rule_17_a_zero_in_either_house_blocks_reduction(self, chart):
        bav = _bav(**{f"s{s}": 4 for s in range(1, 13)})
        a, b = EKADHIPATYA_PAIRS[0]
        bav[a] = 0
        out = ekadhipatya_shodhana(bav, chart)
        assert (out[a], out[b]) == (0, 4)

    def test_rule_16_unoccupied_pair_equal_is_eliminated(self, chart):
        """Both signs empty of planets and carrying equal figures -> both removed."""
        occupied = {p.sign for name, p in chart.planets.items() if name in PLANETS}
        free = [(a, b) for a, b in EKADHIPATYA_PAIRS
                if a not in occupied and b not in occupied]
        if not free:
            pytest.skip("this chart occupies at least one sign of every owned pair")
        a, b = free[0]
        out = ekadhipatya_shodhana(_bav(**{f"s{a}": 6, f"s{b}": 6}), chart)
        assert (out[a], out[b]) == (0, 0)

    def test_rule_16_unoccupied_pair_unequal_reduces_larger_to_smaller(self, chart):
        occupied = {p.sign for name, p in chart.planets.items() if name in PLANETS}
        free = [(a, b) for a, b in EKADHIPATYA_PAIRS
                if a not in occupied and b not in occupied]
        if not free:
            pytest.skip("this chart occupies at least one sign of every owned pair")
        a, b = free[0]
        out = ekadhipatya_shodhana(_bav(**{f"s{a}": 6, f"s{b}": 2}), chart)
        assert (out[a], out[b]) == (2, 2)


class TestPipeline:
    def test_reduction_never_increases_a_bindu(self, chart):
        """Both passes only ever remove. A reduced table above its raw table means a sign
        borrowed bindus from somewhere, which no rule permits."""
        for planet in PLANETS:
            raw = bhinnashtakavarga(chart, planet)
            red = reduced_bhinnashtakavarga(chart, planet)
            assert all(red[s] <= raw[s] for s in range(1, 13)), planet
            assert sum(red.values()) <= BAV_TOTALS[planet]

    def test_covers_all_twelve_signs(self, chart):
        red = reduced_bhinnashtakavarga(chart, "Sun")
        assert set(red) == set(range(1, 13))

    def test_order_is_trikona_then_ekadhipatya(self, chart):
        """HPA-26:466 'After the Thrikona reduction, the Ekadhipathya reduction must be
        applied.' Pinning the composition guards against a future refactor swapping them."""
        raw = bhinnashtakavarga(chart, "Sun")
        expected = ekadhipatya_shodhana(trikona_shodhana(raw), chart)
        assert reduced_bhinnashtakavarga(chart, "Sun") == expected

    def test_every_trine_and_pair_is_accounted_for(self):
        assert sorted(s for g in TRIKONA_GROUPS for s in g) == list(range(1, 13))
        paired = sorted(s for p in EKADHIPATYA_PAIRS for s in p)
        assert paired == sorted(set(range(1, 13)) - {4, 5})
