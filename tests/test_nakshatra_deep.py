"""Tests for nakshatra deep layer — Gap H."""
from __future__ import annotations

import pytest

from app.core.nakshatra_deep import (
    NakshatraAttributes, TaraVerdict,
    attributes_for_longitude, attributes_for_nakshatra,
    gana_koota_score, nadi_koota_dosha, pada_to_navamsha_sign,
    tara_chakra, yoni_koota_score,
)


class TestAttributesLookup:
    def test_returns_27_nakshatras(self):
        """All 27 nakshatras must have attributes."""
        for i in range(27):
            attrs = attributes_for_nakshatra(i)
            assert isinstance(attrs, NakshatraAttributes)
            assert attrs.index == i

    def test_ashwini_attributes(self):
        """Ashwini = Ketu lord, Ashwini Kumaras devata, Deva gana, Horse yoni."""
        a = attributes_for_nakshatra(0)
        assert a.name == "Ashwini"
        assert a.lord == "Ketu"
        assert a.devata == "Ashwini Kumaras"
        assert a.gana == "Deva"
        assert a.yoni == "Horse"

    def test_rohini_devata_brahma(self):
        """Rohini's devata is Brahma per Brihat Samhita Ch.8."""
        assert attributes_for_nakshatra(3).devata == "Brahma"

    def test_jyeshtha_indra_devata(self):
        """Jyeshtha (index 17) is presided over by Indra."""
        assert attributes_for_nakshatra(17).devata == "Indra"

    def test_revati_pushan_devata(self):
        """Revati (index 26) devata is Pushan."""
        assert attributes_for_nakshatra(26).devata == "Pushan"

    def test_all_have_valid_gana(self):
        """Gana must be Deva / Manushya / Rakshasa."""
        valid_ganas = {"Deva", "Manushya", "Rakshasa"}
        for i in range(27):
            assert attributes_for_nakshatra(i).gana in valid_ganas

    def test_all_have_valid_nadi(self):
        """Nadi must be Adya / Madhya / Antya."""
        valid_nadis = {"Adya", "Madhya", "Antya"}
        for i in range(27):
            assert attributes_for_nakshatra(i).nadi in valid_nadis

    def test_rejects_out_of_range(self):
        with pytest.raises(ValueError):
            attributes_for_nakshatra(27)
        with pytest.raises(ValueError):
            attributes_for_nakshatra(-1)


class TestAttributesForLongitude:
    def test_zero_degrees_is_ashwini(self):
        """Longitude 0° = start of Ashwini."""
        assert attributes_for_longitude(0.0).name == "Ashwini"

    def test_thirteen_degrees_twenty_minutes_is_bharani(self):
        """Longitude 13°20' = start of Bharani."""
        assert attributes_for_longitude(13.34).name == "Bharani"


class TestTaraChakra:
    def test_same_nakshatra_is_janma(self):
        """Target = Janma → Tara label 'Janma'."""
        v = tara_chakra(janma_index=0, target_index=0)
        assert v.tara_label == "Janma"
        assert v.distance == 1

    def test_second_from_janma_is_sampat(self):
        """One nakshatra after Janma = Sampat (auspicious)."""
        v = tara_chakra(janma_index=0, target_index=1)
        assert v.tara_label == "Sampat"
        assert v.is_auspicious is True

    def test_seventh_from_janma_is_vadha(self):
        """6 steps after Janma = Vadha (most inauspicious)."""
        v = tara_chakra(janma_index=0, target_index=6)
        assert v.tara_label == "Vadha"
        assert v.is_auspicious is False

    def test_ninth_from_janma_is_ati_maitra(self):
        """8 steps after Janma = Ati-Maitra (most auspicious)."""
        v = tara_chakra(janma_index=0, target_index=8)
        assert v.tara_label == "Ati-Maitra"
        assert v.is_auspicious is True

    def test_cycle_repeats_at_10th(self):
        """10th nakshatra (distance 10) cycles back to Janma."""
        v = tara_chakra(janma_index=0, target_index=9)
        assert v.tara_label == "Janma"
        assert v.distance == 10

    def test_wraps_correctly_past_27(self):
        """Target before Janma wraps via modulo."""
        v = tara_chakra(janma_index=25, target_index=0)
        # From index 25 forward to index 0 = distance 3 (Vipat)
        assert v.distance == 3
        assert v.tara_label == "Vipat"


class TestPadaToNavamshaSign:
    def test_ashwini_pada_1_is_aries_navamsha(self):
        """First pada of Ashwini = first navamsha cell = Aries (sign 1)."""
        assert pada_to_navamsha_sign(0, 1) == 1

    def test_ashwini_pada_4_is_cancer_navamsha(self):
        """Ashwini pada 4 = 4th cell from Aries = Cancer (sign 4)."""
        assert pada_to_navamsha_sign(0, 4) == 4

    def test_pada_wraps_through_signs(self):
        """108 padas cycle through 12 signs 9 times. Pada 108 (nakshatra=26
        pada=4) maps to 12 (Pisces) since 26*4+3=107, 107%12=11+1=12."""
        assert pada_to_navamsha_sign(26, 4) == 12

    def test_rejects_invalid_pada(self):
        with pytest.raises(ValueError):
            pada_to_navamsha_sign(0, 0)
        with pytest.raises(ValueError):
            pada_to_navamsha_sign(0, 5)


class TestGanaKootaScore:
    def test_same_deva_gana_perfect_score(self):
        """Both Deva = score 6."""
        # Ashwini (0) is Deva, Mrigashira (4) is Deva
        assert gana_koota_score(0, 4) == 6

    def test_manushya_rakshasa_is_zero(self):
        """Manushya-Rakshasa = doctrinal incompatibility, score 0."""
        # Bharani (1) is Manushya, Krittika (2) is Rakshasa
        assert gana_koota_score(1, 2) == 0

    def test_deva_manushya_is_five(self):
        """Deva-Manushya = score 5."""
        # Ashwini (0) Deva, Bharani (1) Manushya
        assert gana_koota_score(0, 1) == 5


class TestNadiKootaDosha:
    def test_same_nadi_is_dosha(self):
        """Same Nadi between partners = Dosha (True)."""
        # Both Ashwini (0) Adya
        assert nadi_koota_dosha(0, 0) is True

    def test_different_nadi_no_dosha(self):
        """Different Nadi = no Dosha (False)."""
        # Ashwini (0) Adya, Bharani (1) Madhya
        assert nadi_koota_dosha(0, 1) is False


class TestYoniKootaScore:
    def test_same_yoni_perfect_score(self):
        """Same Yoni between partners = score 4."""
        # Ashwini and Shatabhisha both Horse yoni
        assert yoni_koota_score(0, 23) == 4

    def test_different_yoni_neutral_score(self):
        """Different Yoni without enemy-pair = score 2."""
        # Ashwini (Horse) vs Bharani (Elephant)
        assert yoni_koota_score(0, 1) == 2
