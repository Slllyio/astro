"""Tests for Remedies (Upayas) library — Gap L."""
from __future__ import annotations

import pytest

from app.core.remedies import (
    LAGNA_GEM_SAFETY, PlanetRemedy, RemedyPrescription,
    all_remedies, get_remedy, is_gem_safe_for_lagna, prescribe,
)


class TestRemedyLookup:
    def test_all_9_planets_have_remedies(self):
        """All 9 grahas (Sun..Saturn + Rahu + Ketu) have remedy bundles."""
        r = all_remedies()
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                    "Saturn", "Rahu", "Ketu"}
        assert set(r.keys()) == expected

    def test_get_sun_remedy(self):
        rs = get_remedy("Sun")
        assert isinstance(rs, PlanetRemedy)
        assert "Ruby" in rs.gemstone_primary
        assert "Sunday" in rs.gemstone_day

    def test_each_remedy_has_devanagari_mantra(self):
        """Every beej mantra contains Devanagari characters."""
        for planet, r in all_remedies().items():
            assert any('ऀ' <= ch <= 'ॿ' for ch in r.beej_mantra), \
                f"{planet} mantra has no Devanagari"

    def test_saturn_has_critical_safety_caveat(self):
        """Saturn's gemstone caveat must mention dangerous / trial / mandatory."""
        rs = get_remedy("Saturn")
        caveat_lower = rs.safety_caveat.lower()
        assert "dangerous" in caveat_lower or "trial" in caveat_lower or "mandatory" in caveat_lower

    def test_invalid_planet_raises(self):
        with pytest.raises(ValueError):
            get_remedy("Pluto")


class TestLagnaGemSafety:
    def test_all_12_lagnas_have_table(self):
        """All 12 Lagnas have a safety entry."""
        assert set(LAGNA_GEM_SAFETY.keys()) == set(range(1, 13))

    def test_aries_avoids_blue_sapphire(self):
        """Aries Lagna (1) avoids Blue Sapphire."""
        result = is_gem_safe_for_lagna("Blue Sapphire", 1)
        assert result == "avoid"

    def test_taurus_safe_for_neelam(self):
        """Taurus (2) — Saturn is Yogakaraka — neelam is safe."""
        result = is_gem_safe_for_lagna("Blue Sapphire", 2)
        assert result == "safe"

    def test_cancer_safe_for_pukhraj(self):
        """Cancer Lagna (4) — Jupiter is benefic — pukhraj safe."""
        result = is_gem_safe_for_lagna("Yellow Sapphire", 4)
        assert result == "safe"

    def test_libra_avoids_red_coral(self):
        """Libra (7) — Mars rules 2L+7L Maraka — coral avoided."""
        result = is_gem_safe_for_lagna("Red Coral", 7)
        assert result == "avoid"

    def test_unrated_gem_returns_unrated(self):
        """A gem not in the safety table returns 'unrated'."""
        result = is_gem_safe_for_lagna("Bogus Stone", 1)
        assert result == "unrated"

    def test_rejects_invalid_lagna(self):
        with pytest.raises(ValueError):
            is_gem_safe_for_lagna("Ruby", 13)


class TestPrescribe:
    def test_weak_benefic_yields_gem_and_mantra(self):
        rx = prescribe("Jupiter", "weak_benefic")
        assert "gemstone" in rx.recommended_remedies
        assert "mantra" in rx.recommended_remedies
        assert rx.gemstone_caveat == "PROCEED"

    def test_weak_malefic_avoids_gemstone(self):
        rx = prescribe("Saturn", "weak_malefic")
        assert "gemstone" not in rx.recommended_remedies
        assert rx.gemstone_caveat == "AVOID"

    def test_strong_affliction_requires_trial(self):
        rx = prescribe("Saturn", "strong_affliction")
        assert "daana" in rx.recommended_remedies
        assert rx.gemstone_caveat == "TRIAL_REQUIRED"

    def test_strong_benefic_recommends_lifestyle(self):
        rx = prescribe("Jupiter", "strong_benefic")
        assert "lifestyle" in rx.recommended_remedies
        assert rx.gemstone_caveat == "AVOID"

    def test_lord_of_dushtana_mantra_only(self):
        rx = prescribe("Saturn", "lord_of_dushtana")
        assert rx.recommended_remedies == ("mantra",)
        assert rx.gemstone_caveat == "AVOID"

    def test_lagna_safety_overlay_downgrades_proceed_to_trial(self):
        """When Lagna safety = cautious, even PROCEED becomes TRIAL_REQUIRED."""
        # Gemini Lagna (3) — Pukhraj is cautious. weak_benefic Jupiter normally PROCEED.
        rx = prescribe("Jupiter", "weak_benefic", lagna_sign=3)
        assert rx.gemstone_caveat == "TRIAL_REQUIRED"

    def test_lagna_safety_overlay_avoids_when_dangerous(self):
        """Lagna AVOID overrides PROCEED."""
        # Taurus (2) — Pukhraj is avoid.
        rx = prescribe("Jupiter", "weak_benefic", lagna_sign=2)
        assert rx.gemstone_caveat == "AVOID"
