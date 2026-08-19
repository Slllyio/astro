"""ashtakavarga_sodhana: HPA Ch. XXVI golden example + rule corner cases."""
import pytest

from app.core.ashtakavarga_sodhana import (
    best_direction,
    ekadhipatya_sodhana,
    maraka_nakshatra,
    maraka_rasi,
    sodhana,
    trikona_sodhana,
)

# HPA Ch. XXVI worked example: the Sun's Ashtakavarga of the specimen
# horoscope (table No. 4, pp. 302-307). Pre-reduction bindus Aries..Pisces.
# Triads pinned by the prose (5,3,3 / 5,2,5 / _,_,_ -> 0,0,2 / 3,0,2);
# Gemini/Libra/Aquarius reconstruct to 6,6,8 via the Sun's fixed BAV total
# of 48 and the printed post-reduction differences.
HPA_SUN_BAV = [5, 5, 6, 3, 3, 2, 6, 0, 3, 5, 8, 2]
# Occupancy relevant to the pairs, from the prose: Scorpio and Taurus
# occupied; Aries, Libra, Gemini, Virgo (Ketu = shadow, ignored),
# Sagittarius, Pisces (Rahu = shadow), Capricorn, Aquarius unoccupied.
# The Sun sits in Cancer (exempt sign).
HPA_OCCUPIED = {2, 4, 8}


class TestHPAGoldenExample:
    def test_trikona_reduction_matches_page_304(self):
        after = trikona_sodhana(HPA_SUN_BAV)
        # "2, 0, 0" (Aries/Leo/Sag), "3, 0, 3" (Taurus/Virgo/Cap),
        # "0, 0, 2" (Gemini/Libra/Aquarius), "3, 0, 2" (Cancer/Scorpio/Pisces)
        assert after == [2, 3, 0, 3, 0, 0, 0, 0, 0, 3, 2, 2]

    def test_ekadhipatya_reduction_matches_page_306(self):
        after = ekadhipatya_sodhana([2, 3, 0, 3, 0, 0, 0, 0, 0, 3, 2, 2], HPA_OCCUPIED)
        # only Capricorn/Aquarius change (rule 16: 3 reduced to 2)
        assert after == [2, 3, 0, 3, 0, 0, 0, 0, 0, 2, 2, 2]

    def test_total_after_all_reductions_is_14(self):
        assert sodhana(HPA_SUN_BAV, HPA_OCCUPIED).total == 14

    def test_rule_21_maraka_nakshatra_aswini(self):
        # 14 x 2 (bindus in Pisces, 9th from the Sun in Cancer) = 28;
        # 28 mod 27 = 1 -> Aswini.
        assert maraka_nakshatra(14, 2) == 1

    def test_rule_22_maraka_rasi_cancer(self):
        # 14 x 2 (bindus in Aquarius, 8th from the Sun) = 28;
        # 28 mod 12 = 4 -> Cancer (with its trines Scorpio, Pisces).
        assert maraka_rasi(14, 2) == 4

    def test_rule_23_directions_south_and_north(self):
        final = sodhana(HPA_SUN_BAV, HPA_OCCUPIED).after_ekadhipatya
        # triad sums 2 / 5 / 2 / 5 -> Taurus (south) and Cancer (north) tie
        assert best_direction(final) == ["south", "north"]


class TestTrikonaCorners:
    def test_one_zero_no_reduction(self):
        # R11: Cancer/Scorpio/Pisces 3,0,2 stays untouched
        row = [0] * 12
        row[3], row[7], row[11] = 3, 0, 2
        assert trikona_sodhana(row) == row

    def test_two_zeros_eliminates_third(self):
        row = [0] * 12
        row[0], row[4], row[8] = 7, 0, 0
        assert trikona_sodhana(row)[0] == 0

    def test_all_equal_eliminates_all(self):
        row = [0] * 12
        row[2], row[6], row[10] = 4, 4, 4
        out = trikona_sodhana(row)
        assert (out[2], out[6], out[10]) == (0, 0, 0)

    def test_rejects_bad_input(self):
        with pytest.raises(ValueError):
            trikona_sodhana([9] * 12)
        with pytest.raises(ValueError):
            trikona_sodhana([1] * 11)


class TestEkadhipatyaCorners:
    def _row(self, a_sign, a, b_sign, b):
        row = [0] * 12
        row[a_sign - 1], row[b_sign - 1] = a, b
        return row

    def test_r17_zero_in_pair_no_reduction(self):
        row = self._row(1, 2, 8, 0)
        assert ekadhipatya_sodhana(row, set()) == row

    def test_r14_both_occupied_no_reduction(self):
        row = self._row(2, 5, 7, 3)
        assert ekadhipatya_sodhana(row, {2, 7}) == row

    def test_r15a_occupied_smaller_levels_unoccupied(self):
        row = self._row(2, 3, 7, 5)  # Taurus occupied 3, Libra unoccupied 5
        out = ekadhipatya_sodhana(row, {2})
        assert (out[1], out[6]) == (3, 3)

    def test_r15b_occupied_greater_eliminates_unoccupied(self):
        row = self._row(2, 5, 7, 3)
        out = ekadhipatya_sodhana(row, {2})
        assert (out[1], out[6]) == (5, 0)

    def test_r15c_equal_eliminates_unoccupied(self):
        row = self._row(2, 4, 7, 4)
        out = ekadhipatya_sodhana(row, {7})
        assert (out[1], out[6]) == (0, 4)

    def test_r16_both_unoccupied_equal_eliminates_both(self):
        row = self._row(9, 3, 12, 3)
        out = ekadhipatya_sodhana(row, set())
        assert (out[8], out[11]) == (0, 0)

    def test_r16_both_unoccupied_unequal_levels_to_smaller(self):
        row = self._row(10, 3, 11, 2)
        out = ekadhipatya_sodhana(row, set())
        assert (out[9], out[10]) == (2, 2)

    def test_r18_cancer_leo_never_touched(self):
        row = [0] * 12
        row[3], row[4] = 5, 3  # Cancer, Leo — not an ekadhipatya pair
        assert ekadhipatya_sodhana(row, set()) == row

    def test_shadow_only_occupancy_must_be_precomputed_out(self):
        # Callers exclude Rahu/Ketu when building occupied_signs; passing
        # a sign occupied only by a shadow planet is the caller's bug and
        # simply behaves as occupied — document via the golden test above.
        with pytest.raises(ValueError):
            ekadhipatya_sodhana([1] * 12, {13})


class TestApplications:
    def test_maraka_nakshatra_wraps_zero_to_27(self):
        assert maraka_nakshatra(27, 1) == 27
        assert maraka_nakshatra(0, 5) == 27

    def test_maraka_rasi_wraps_zero_to_12(self):
        assert maraka_rasi(12, 1) == 12
        assert maraka_rasi(6, 2) == 12
