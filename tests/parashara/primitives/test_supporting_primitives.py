"""The three primitives ch.11's bhava judgment stands on: functional nature, Baladi avastha,
graha drishti — each pinned against its own BPHS sloka."""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import passage, verify
from app.parashara.primitives import functional_nature as fn
from app.parashara.primitives import graha_drishti as gd
from app.parashara.primitives.baladi_avastha import RESULT_GRADE, baladi_avastha


class TestFunctionalNature:
    def test_the_fixed_malefics(self):
        """BPHS-3:187 — 'Sun, Saturn, Mars, decreasing Moon, Rahu and Ketu are malefics'."""
        for p in ("Sun", "Saturn", "Mars", "Rahu", "Ketu"):
            assert fn.natural_benefic(p) is False, p

    def test_the_fixed_benefics(self):
        for p in ("Jupiter", "Venus"):
            assert fn.natural_benefic(p) is True, p

    def test_waxing_moon_is_benefic_waning_is_malefic(self):
        assert fn.natural_benefic("Moon", moon_waxing=True) is True
        assert fn.natural_benefic("Moon", moon_waxing=False) is False

    def test_waning_moon_in_benefic_company_turns_benefic(self):
        """BPHS-3:208 — 'Should the Moon be conjunct a benefic ... she turns a benefic, even if in
        a waning state.'"""
        assert fn.natural_benefic("Moon", moon_waxing=False, companions=["Jupiter"]) is True

    def test_waning_moon_aspected_by_benefic_turns_benefic(self):
        """BPHS-3:208 also says 'or aspected by a benefic' — the aspect half the audit found missing.
        A waning Moon with no benefic companion but a benefic aspect must still turn benefic."""
        assert fn.natural_benefic("Moon", moon_waxing=False,
                                  companions=[], aspected_by_benefic=True) is True
        # ...and stays malefic with neither conjunction nor aspect.
        assert fn.natural_benefic("Moon", moon_waxing=False,
                                  companions=[], aspected_by_benefic=False) is False

    def test_mercury_takes_the_nature_of_his_company(self):
        """'Mercury, however, is a malefic if he joins a malefic' — otherwise benefic."""
        assert fn.natural_benefic("Mercury") is True
        assert fn.natural_benefic("Mercury", companions=["Saturn"]) is False
        assert fn.natural_benefic("Mercury", companions=["Venus"]) is True

    def test_moon_without_paksha_raises(self):
        with pytest.raises(ValueError, match="paksha"):
            fn.natural_benefic("Moon")

    def test_source_resolves(self):
        assert verify(fn.SOURCE) and verify(fn.MOON_BENEFIC_COMPANY_SOURCE)
        assert "BENEFIC" in passage("BPHS-3:187")["text"].upper()


class TestBaladiAvastha:
    def test_odd_sign_ascending_bands(self):
        """BPHS-45:45 — odd signs ascend by 6 degrees: bala, kumara, yuva, vriddha, mrita."""
        aries = 1
        assert baladi_avastha(aries, 3).state == "bala"
        assert baladi_avastha(aries, 9).state == "kumara"
        assert baladi_avastha(aries, 15).state == "yuva"
        assert baladi_avastha(aries, 21).state == "vriddha"
        assert baladi_avastha(aries, 27).state == "mrita"

    def test_even_sign_reverses_the_order(self):
        """'This arrangement is reverse in the case of even signs' — Taurus 0-6 is mrita, not bala.
        This reversal is the classic error, and ch.11's own worked degrees only reconcile with it."""
        taurus = 2
        assert baladi_avastha(taurus, 3).state == "mrita"
        assert baladi_avastha(taurus, 9).state == "vriddha"
        assert baladi_avastha(taurus, 15).state == "yuva"
        assert baladi_avastha(taurus, 27).state == "bala"

    def test_reconciles_with_ch11s_worked_degrees(self):
        """BPHS-11:14 says the flourishing kumara/yuva band is '6 to 18 of an odd sign', and the
        spent Vriddha is '6 to 12 of an even sign'. Both must fall out of ch.45's table."""
        assert baladi_avastha(1, 8).state in ("kumara", "yuva")    # odd, 6-18
        assert baladi_avastha(1, 17).state in ("kumara", "yuva")
        assert baladi_avastha(2, 9).state == "vriddha"             # even, 6-12

    def test_result_grades(self):
        """BPHS-45:66 — 1/4, 1/2, full, negligible, nil."""
        assert RESULT_GRADE["yuva"] == 1.0
        assert RESULT_GRADE["mrita"] == 0.0
        assert RESULT_GRADE["bala"] == 0.25 and RESULT_GRADE["kumara"] == 0.5

    def test_boundaries_and_bounds(self):
        assert baladi_avastha(1, 0.0).state == "bala"
        assert baladi_avastha(1, 30.0).state == "mrita"     # exact 30 clamps into last band
        with pytest.raises(ValueError):
            baladi_avastha(13, 5)
        with pytest.raises(ValueError):
            baladi_avastha(1, 31)


class TestGrahaDrishti:
    def test_all_planets_aspect_the_seventh(self):
        """BPHS-26:47 — 'All planets aspect the 7th fully.'"""
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            assert 7 in gd.full_aspect_distances(p), p

    def test_the_three_special_aspects(self):
        """Saturn 3rd/10th, Jupiter 5th/9th, Mars 4th/8th."""
        assert gd.full_aspect_distances("Saturn") == frozenset({7, 3, 10})
        assert gd.full_aspect_distances("Jupiter") == frozenset({7, 5, 9})
        assert gd.full_aspect_distances("Mars") == frozenset({7, 4, 8})

    def test_a_planet_without_special_aspects_only_sees_the_seventh(self):
        assert gd.full_aspect_distances("Venus") == frozenset({7})

    def test_aspects_sign_counts_whole_sign_distance(self):
        # Mars in Aries (1) aspects the 4th (Cancer, 4), 7th (Libra, 7), 8th (Scorpio, 8).
        assert gd.aspects_sign("Mars", 1, 4) is True
        assert gd.aspects_sign("Mars", 1, 7) is True
        assert gd.aspects_sign("Mars", 1, 8) is True
        assert gd.aspects_sign("Mars", 1, 5) is False

    def test_a_planet_does_not_aspect_its_own_sign(self):
        assert gd.aspects_sign("Jupiter", 5, 5) is False

    def test_planets_aspecting_sign(self):
        signs = {"Saturn": 1, "Jupiter": 1, "Venus": 4}
        # target = sign 10: Saturn (1->10 = 10th, special) yes; Jupiter (5/9 from Aries = 5,9) no;
        # Venus (7th from 4 = 10) yes.
        got = gd.planets_aspecting_sign(10, signs)
        assert set(got) == {"Saturn", "Venus"}

    def test_source_resolves(self):
        assert verify(gd.SOURCE)
        assert "ASPECT" in passage("BPHS-26:47")["text"].upper()
