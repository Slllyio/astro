"""Panchanga limb suitability — exactly Raman's stated rules, nothing imported from the
non-citable S-2 layer (MUHURTHA-2 / MUHURTHA-3 / MUHURTHA-8 / MUHURTHA-18)."""
from __future__ import annotations

from app.raman_saab.electional.panchanga_suitability import (
    DISCARDED_KARANAS, INAUSPICIOUS_YOGAS, UNSUITABLE_TITHIS, UNSUITABLE_VARAS,
    limb_suitability)


class TestLimbSuitability:
    def test_the_printed_tithi_list_verbatim(self):
        """MUHURTHA-2:202-204 as printed: 4, 8, 12, 14 (deliberately NOT 'corrected' to the
        classical 4/9/14 rikta triad — the module docstring records the divergence)."""
        assert UNSUITABLE_TITHIS == {4, 8, 12, 14}

    def test_tuesday_and_saturday_are_avoided(self):
        """MUHURTHA-2:194-200."""
        assert UNSUITABLE_VARAS == {2, 6}

    def test_the_appendix_yoga_list_by_number(self):
        """MUHURTHA-18:861-864 — nine yogas, mapped to the MUHURTHA-2:133-145 enumeration."""
        assert INAUSPICIOUS_YOGAS == {1, 6, 9, 10, 13, 15, 17, 19, 27}

    def test_vishti_is_the_one_discarded_karana(self):
        """MUHURTHA-8:1171; Vishti is karana 7 in MUHURTHA-2:151-160."""
        assert DISCARDED_KARANAS == {7}

    def test_a_clean_moment_passes_all_five_limbs(self):
        limbs = limb_suitability(tithi_in_paksha=2, weekday=3, nakshatra=8, yoga=2, karana=1)
        assert [lv.limb for lv in limbs] == ["tithi", "vara", "nakshatra", "yoga", "karana"]
        assert all(lv.suitable for lv in limbs)

    def test_bharani_fails_the_nakshatra_limb(self):
        """MUHURTHA-3:88-91: 'Bharani is condemned for all good work'."""
        limbs = limb_suitability(tithi_in_paksha=2, weekday=3, nakshatra=2, yoga=2, karana=1)
        by = {lv.limb: lv.suitable for lv in limbs}
        assert by["nakshatra"] is False and by["tithi"] is True
