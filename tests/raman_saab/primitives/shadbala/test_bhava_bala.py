"""Tests for Bhava Bala (house strength) — three components.

Reference: B.V. Raman, Graha & Bhava Balas §8.

Usage:
    py -3.12 -m pytest tests/raman_saab/primitives/shadbala/test_bhava_bala.py -q
"""
from __future__ import annotations

import dataclasses
import pytest

from app.raman_saab.primitives.shadbala import bhava_bala as bb
from app.raman_saab.chart.model import RamanChart


# ---------------------------------------------------------------------------
# sign_class_ref — sign → NIL house (Nara/Jalachara/Chatushpada/Keeta)
# ---------------------------------------------------------------------------

class TestSignClassRef:
    def test_chatushpada_leo(self):
        """Leo (sign 5) is Chatushpada → NIL house 4."""
        assert bb.sign_class_ref(5) == 4

    def test_keeta_scorpio(self):
        """Scorpio (sign 8) is Keeta → NIL house 1."""
        assert bb.sign_class_ref(8) == 1

    def test_nara_libra(self):
        """Libra (sign 7) is Nara → NIL house 7."""
        assert bb.sign_class_ref(7) == 7

    def test_jalachara_cancer(self):
        """Cancer (sign 4) is Jalachara → NIL house 10."""
        assert bb.sign_class_ref(4) == 10

    def test_nara_gemini(self):
        """Gemini (sign 3) is Nara → NIL house 7."""
        assert bb.sign_class_ref(3) == 7

    def test_nara_virgo(self):
        """Virgo (sign 6) is Nara → NIL house 7."""
        assert bb.sign_class_ref(6) == 7

    def test_nara_aquarius(self):
        """Aquarius (sign 11) is Nara → NIL house 7."""
        assert bb.sign_class_ref(11) == 7

    def test_chatushpada_aries(self):
        """Aries (sign 1) is Chatushpada → NIL house 4."""
        assert bb.sign_class_ref(1) == 4

    def test_chatushpada_taurus(self):
        """Taurus (sign 2) is Chatushpada → NIL house 4."""
        assert bb.sign_class_ref(2) == 4

    def test_jalachara_pisces(self):
        """Pisces (sign 12) is Jalachara → NIL house 10."""
        assert bb.sign_class_ref(12) == 10

    def test_sagittarius_first_half_is_nara(self):
        """Sagittarius first half (deg < 15) is Nara → NIL house 7."""
        assert bb.sign_class_ref(9, deg=5.0) == 7

    def test_sagittarius_second_half_is_chatushpada(self):
        """Sagittarius second half (deg >= 15) is Chatushpada → NIL house 4."""
        assert bb.sign_class_ref(9, deg=15.0) == 4

    def test_capricorn_first_half_is_chatushpada(self):
        """Capricorn first half (deg < 15) is Chatushpada → NIL house 4."""
        assert bb.sign_class_ref(10, deg=0.0) == 4

    def test_capricorn_second_half_is_jalachara(self):
        """Capricorn second half (deg >= 15) is Jalachara → NIL house 10."""
        assert bb.sign_class_ref(10, deg=20.0) == 10


# ---------------------------------------------------------------------------
# bhavadig_bala — core verified examples from the plan
# ---------------------------------------------------------------------------

class TestBhavadigBala:
    def test_worked_example_8th_in_leo(self):
        """8th bhava, madhya in Leo (Chatushpada, ref 4): |4-8|=4 → 40.0."""
        assert bb.bhavadig_bala(8, sign=5) == 40.0

    def test_nara_lagna_max(self):
        """Nara sign (Libra=7) at the 1st bhava → |7-1|=6 → 60.0 (maximum)."""
        assert bb.bhavadig_bala(1, sign=7) == 60.0

    def test_nara_7th_zero(self):
        """Nara sign (Libra=7) at the 7th bhava → |7-7|=0 → 0.0 (minimum)."""
        assert bb.bhavadig_bala(7, sign=7) == 0.0

    def test_keeta_1st(self):
        """Scorpio (Keeta, ref 1) at 1st bhava → |1-1|=0 → 0.0."""
        assert bb.bhavadig_bala(1, sign=8) == 0.0

    def test_keeta_7th(self):
        """Scorpio (Keeta, ref 1) at 7th bhava → |1-7|=6 → 60.0."""
        assert bb.bhavadig_bala(7, sign=8) == 60.0

    def test_jalachara_10th_zero(self):
        """Cancer (Jalachara, ref 10) at 10th bhava → |10-10|=0 → 0.0."""
        assert bb.bhavadig_bala(10, sign=4) == 0.0

    def test_jalachara_4th_max(self):
        """Cancer (Jalachara, ref 10) at 4th bhava → |10-4|=6 → 60.0."""
        assert bb.bhavadig_bala(4, sign=4) == 60.0

    def test_wrap_around_more_than_6(self):
        """When |ref−bhava|>6, use 12 minus that value: e.g. ref=1, bhava=10 → |1-10|=9>6 → 12-9=3 → 30."""
        assert bb.bhavadig_bala(10, sign=8) == 30.0  # Scorpio(Keeta,ref=1), |1-10|=9>6 -> 12-9=3 -> 30


# ---------------------------------------------------------------------------
# BhavaDrig — aspectual component sign-test
# ---------------------------------------------------------------------------

class TestBhavaDrigBalaSign:
    def test_benefic_aspecting_madhya_gives_positive(self):
        """Jupiter (benefic) at 0° aspectings a bhava-madhya at 180° should yield positive BhavaDrig.

        Jupiter is at 0°; the bhava-madhya is at 180°. Separation K = (180 - 0) % 360 = 180° → dristi = 60.
        Jupiter gets full dristi (not ¼). Net = +60/4 = +15 (positive).
        """
        c = RamanChart.from_stated_positions(
            {"Jupiter": {"lon": 0.0, "bhava": 1}},
            asc_lon=0.0, ayanamsa="raman",
        )
        val = bb.bhava_drig_bala(180.0, c)
        assert val > 0.0, f"Expected positive BhavaDrig, got {val}"

    def test_malefic_aspecting_madhya_gives_negative(self):
        """Saturn (malefic) at 0° aspecting a bhava-madhya at 180° → negative BhavaDrig."""
        c = RamanChart.from_stated_positions(
            {"Saturn": {"lon": 0.0, "bhava": 1}},
            asc_lon=0.0, ayanamsa="raman",
        )
        val = bb.bhava_drig_bala(180.0, c)
        assert val < 0.0, f"Expected negative BhavaDrig, got {val}"

    def test_no_planets_gives_zero(self):
        """No planets aspecting the madhya → BhavaDrig = 0."""
        c = RamanChart.from_stated_positions({}, asc_lon=0.0, ayanamsa="raman")
        val = bb.bhava_drig_bala(90.0, c)
        assert val == 0.0

    def test_jupiter_mercury_get_full_dristi(self):
        """Jupiter and Mercury get full (1x) dristi weight; others get 1/4.

        Jupiter at 0°, Mercury at 0°, bhava-madhya at 180°. Both benefics at 180° sep.
        dristi_value(180) = 60. Full weight for both → pinda = 60+60 = 120.
        Result = 120/4 = 30.0.
        """
        c = RamanChart.from_stated_positions(
            {"Jupiter": {"lon": 0.0, "bhava": 1},
             "Mercury": {"lon": 0.0, "bhava": 1}},
            asc_lon=0.0, ayanamsa="raman",
        )
        val = bb.bhava_drig_bala(180.0, c)
        assert abs(val - 30.0) < 0.01, f"Expected 30.0, got {val}"

    def test_sun_gets_quarter_dristi(self):
        """Sun (malefic, ¼ weight) at 0°, bhava-madhya at 180°.

        dristi_value(180) = 60; ¼ weight → contribution = 15.
        Malefic → pinda = -15. Result = -15/4 = -3.75.
        """
        c = RamanChart.from_stated_positions(
            {"Sun": {"lon": 0.0, "bhava": 1}},
            asc_lon=0.0, ayanamsa="raman",
        )
        val = bb.bhava_drig_bala(180.0, c)
        assert abs(val - (-3.75)) < 0.01, f"Expected -3.75, got {val}"


# ---------------------------------------------------------------------------
# bhava_bala — integration: passthrough and sum structure
# ---------------------------------------------------------------------------

class TestBhavaBalaIntegration:
    def test_bhavadhipati_passthrough(self):
        """bhava_bala sums the three components; Bhavadhipati is just the passed-in shadbala value."""
        c = RamanChart.from_stated_positions({}, asc_lon=0.0, ayanamsa="raman")
        # bhava 7 in Libra (Nara, ref 7) → Bhavadig = 0.
        # No planets → BhavaDrig = 0.
        # lord_shadbala = 120.0 Shashtiamsas.
        # Total = 120 + 0 + 0 = 120.
        result = bb.bhava_bala(7, c, lord_shadbala=120.0, bhava_madhya=180.0, bhava_sign=7)
        assert result == 120.0

    def test_bhava_bala_is_non_negative_with_benefic_lord(self):
        """A chart with a strong benefic lord should give a positive total."""
        c = RamanChart.from_stated_positions(
            {"Jupiter": {"lon": 0.0, "bhava": 1}},
            asc_lon=0.0, ayanamsa="raman",
        )
        # bhava 1 in Aries (Chatushpada, ref 4) → Bhavadig = |4-1|=3 → 30.
        # Jupiter at 0°, madhya at 0° → sep = 0° → dristi_value(0)=0 → no aspect contribution.
        # lord_shadbala = 200.0.
        result = bb.bhava_bala(1, c, lord_shadbala=200.0, bhava_madhya=0.0, bhava_sign=1)
        assert result > 0.0

    def test_bhava_bala_returns_float(self):
        """bhava_bala always returns a float."""
        c = RamanChart.from_stated_positions({}, asc_lon=0.0, ayanamsa="raman")
        result = bb.bhava_bala(1, c, lord_shadbala=0.0, bhava_madhya=0.0, bhava_sign=1)
        assert isinstance(result, float)
