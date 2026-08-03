"""Tarabala/Chandrabala — pinned to Raman's own worked examples (MUHURTHA-3)."""
from __future__ import annotations

from app.raman_saab.electional.tarabala import (
    CHANDRABALA_BAD_HOUSES, JANMA_STAR_FAVOURABLE_ACTS, JANMA_STAR_INAUSPICIOUS_ACTS,
    NEGATIVE_OPENING_GHATIS, TARA_NAMES, chandrabala, tarabala)


class TestTarabala:
    def test_ramans_worked_example_aswini_to_sravana_is_kshema(self):
        """MUHURTHA-3:57-63: Aswini native, Sravana day -> count 22, remainder 4 = Kshema,
        'Tarabala is good'."""
        tb = tarabala(1, 22)
        assert tb.tara == 4 and tb.name == "Kshema" and tb.favourable

    def test_bharani_is_naidhana_to_a_mrigasira_native(self):
        """MUHURTHA-3:72-79: 'neither Tarabala (as Bharani will be naidhana to Mrigasira)'."""
        tb = tarabala(5, 2)
        assert tb.name == "Naidhana" and not tb.favourable

    def test_same_star_is_janma_and_the_ninth_is_parama_mitra(self):
        """The count is inclusive: the Janma star itself is tara 1; nine along is tara 9."""
        assert tarabala(10, 10).name == "Janma"
        assert tarabala(10, 18).name == "Parama Mitra" and tarabala(10, 18).favourable

    def test_negative_opening_ghatis_match_the_print(self):
        """MUHURTHA-3:179-195: Janma 1, Vipat 7, Pratyak 3, Naidhana 8 ghatis."""
        assert NEGATIVE_OPENING_GHATIS == {1: 1, 3: 7, 5: 3, 7: 8}
        assert tarabala(5, 2).negative_opening_ghatis == 8      # naidhana
        assert tarabala(1, 22).negative_opening_ghatis == 0     # kshema — none

    def test_the_nine_taras_carry_ramans_names_in_order(self):
        assert TARA_NAMES[0] == "Janma" and TARA_NAMES[8] == "Parama Mitra"
        assert len(TARA_NAMES) == 9

    def test_janma_star_activity_split_is_disjoint(self):
        """MUHURTHA-3:197-206 — the favourable and inauspicious lists never overlap."""
        assert not (JANMA_STAR_FAVOURABLE_ACTS & JANMA_STAR_INAUSPICIOUS_ACTS)


class TestChandrabala:
    def test_ramans_double_failure_example_moon_in_the_12th(self):
        """MUHURTHA-3:72-79: Taurus Janma Rasi, election Moon in Aries = the 12th -> no
        Chandrabala."""
        assert chandrabala(2, 1) is False

    def test_the_bad_houses_are_6_8_12(self):
        assert CHANDRABALA_BAD_HOUSES == {6, 8, 12}
        janma = 3
        for moon in range(1, 13):
            house = (moon - janma) % 12 + 1
            assert chandrabala(janma, moon) == (house not in {6, 8, 12})
