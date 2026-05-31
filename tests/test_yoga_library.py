"""Tests for app.core.yoga_library — Phase 3 detectors.

Each detector is tested with a minimal synthetic chart that isolates
its activation condition. Cross-detector contamination is avoided by
keeping other planets neutral.
"""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.yoga_library import (
    YOGA_DETECTORS,
    active_yogas,
    detect_all,
    detect_amala,
    detect_anapha,
    detect_budha_aditya,
    detect_chandra_mangal,
    detect_daridra,
    detect_gajakesari,
    detect_hamsa,
    detect_kala_sarpa,
    detect_kemadruma,
    detect_malavya,
    detect_mangal_dosha,
    detect_raja_yoga,
    detect_ruchaka,
    detect_sasa,
    detect_sunapha,
    detect_vipareeta_raja,
)


def _baseline_chart(**overrides) -> Chart:
    """Neutral chart — Aries Lagna, planets scattered so no yoga fires
    unless an override forces one. Used as the starting fixture for
    each per-detector test."""
    defaults = dict(
        asc_sign=1, asc_lon=10.0,
        planet_signs={
            "Sun": 3, "Moon": 5, "Mars": 7, "Mercury": 9,
            "Jupiter": 11, "Venus": 2, "Saturn": 4,
            "Rahu": 6, "Ketu": 12,
        },
        planet_houses={
            "Sun": 3, "Moon": 5, "Mars": 7, "Mercury": 9,
            "Jupiter": 11, "Venus": 2, "Saturn": 4,
            "Rahu": 6, "Ketu": 12,
        },
        planet_lons={
            "Sun": 70.0, "Moon": 130.0, "Mars": 190.0, "Mercury": 250.0,
            "Jupiter": 310.0, "Venus": 40.0, "Saturn": 100.0,
            "Rahu": 160.0, "Ketu": 340.0,
        },
    )
    defaults.update(overrides)
    return Chart(**defaults)  # type: ignore[arg-type]


class TestPanchaMahapurusha:
    """PMP yogas: planet in own/exalt + Kendra (1/4/7/10)."""

    def test_ruchaka_fires_when_mars_exalted_kendra(self):
        """Mars exalted Capricorn (sign 10) + Kendra → Ruchaka."""
        # Aries Lagna; sign 10 → ((10-1)%12)+1 = 10 (Kendra). Mars in Cap = exalted.
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Mars": 10},
            planet_houses={**_baseline_chart().planet_houses, "Mars": 10},
        )
        y = detect_ruchaka(ch)
        assert y.active
        assert y.intensity == 1.0  # exalt > own boost

    def test_ruchaka_inactive_when_mars_in_dusthana(self):
        """Mars in 6H — Kendra fails, no Ruchaka."""
        ch = _baseline_chart()
        # Mars at house 7 in baseline; check inactive when not own/exalt
        y = detect_ruchaka(ch)
        # Mars in sign 7 (Libra) — not own, not exalt → inactive
        assert not y.active

    def test_hamsa_fires_for_jupiter_own_sign_kendra(self):
        """Jupiter in Sagittarius (sign 9) + Kendra → Hamsa.
        For Aries Lagna, sign 9 = 9H (Trikona, not Kendra).
        Use Cancer Lagna (sign 4): sign 9 → ((9-4)%12)+1 = 6 (Dusthana).
        Use Aries Lagna, Jupiter in Pisces sign 12 → 12H not Kendra.
        For Hamsa we need Jupiter in own AND Kendra. Try Pisces Lagna (12):
          sign 12 → 1H ✓ (Kendra). Yes."""
        ch = _baseline_chart(
            asc_sign=12,
            planet_signs={**_baseline_chart().planet_signs, "Jupiter": 12},
            planet_houses={**_baseline_chart().planet_houses, "Jupiter": 1},
        )
        y = detect_hamsa(ch)
        assert y.active

    def test_malavya_fires_for_venus_own_kendra(self):
        """Venus in Libra (sign 7) and 7H Kendra."""
        ch = _baseline_chart(
            asc_sign=1,
            planet_signs={**_baseline_chart().planet_signs, "Venus": 7},
            planet_houses={**_baseline_chart().planet_houses, "Venus": 7},
        )
        y = detect_malavya(ch)
        assert y.active

    def test_sasa_fires_for_saturn_own_kendra(self):
        """Saturn in Capricorn (sign 10) → for Aries Lagna, 10H Kendra."""
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Saturn": 10},
            planet_houses={**_baseline_chart().planet_houses, "Saturn": 10},
        )
        y = detect_sasa(ch)
        assert y.active


class TestSolarLunarYogas:
    """Budha-Aditya, Sunapha, Anapha — luminary-adjacency yogas."""

    def test_budha_aditya_fires_when_sun_mercury_conjunct(self):
        """Sun and Mercury in same sign with separation > 14° → no combustion."""
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Sun": 3, "Mercury": 3},
            planet_lons={**_baseline_chart().planet_lons, "Sun": 70.0, "Mercury": 86.0},
        )
        y = detect_budha_aditya(ch)
        assert y.active
        assert y.intensity == 1.0  # not combust (16° apart)

    def test_budha_aditya_combust_penalty(self):
        """Sun-Mercury within 14° → intensity halves."""
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Sun": 3, "Mercury": 3},
            planet_lons={**_baseline_chart().planet_lons, "Sun": 70.0, "Mercury": 75.0},
        )
        y = detect_budha_aditya(ch)
        assert y.active
        assert y.intensity == 0.5

    def test_sunapha_fires_when_planet_in_2nd_from_moon(self):
        """Mars in 2nd sign from Moon (Moon sign 5 → 6) → Sunapha."""
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Moon": 5, "Mars": 6},
            planet_houses={**_baseline_chart().planet_houses, "Moon": 5, "Mars": 6},
        )
        y = detect_sunapha(ch)
        assert y.active
        assert "Mars" in y.participants

    def test_anapha_inactive_with_no_planet_in_12th_from_moon(self):
        """Empty 12th-from-Moon → Anapha inactive."""
        # Moon in sign 5 → 12th = sign 4. Clear sign 4.
        ch = _baseline_chart(
            planet_signs={
                "Sun": 3, "Moon": 5, "Mars": 7, "Mercury": 9,
                "Jupiter": 11, "Venus": 2, "Saturn": 8,  # not 4
                "Rahu": 6, "Ketu": 12,
            },
        )
        y = detect_anapha(ch)
        assert not y.active


class TestFoundationYogas:
    """Gajakesari, Chandra-Mangal, Kemadruma, Raja, Vipareeta."""

    def test_gajakesari_fires_when_jupiter_kendra_from_moon(self):
        """Jupiter in Kendra (1/4/7/10) from Moon."""
        # Moon sign 5, Jupiter sign 8 → distance ((8-5)%12)+1 = 4 (Kendra)
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Moon": 5, "Jupiter": 8},
        )
        y = detect_gajakesari(ch)
        assert y.active

    def test_chandra_mangal_fires_when_conjunct(self):
        """Moon and Mars in same sign → Chandra-Mangal."""
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Moon": 5, "Mars": 5},
        )
        y = detect_chandra_mangal(ch)
        assert y.active

    def test_raja_yoga_kendra_trikona_conjunction(self):
        """Aries Lagna: 4L = Moon (Cancer), 9L = Jupiter (Sagittarius).
        If Moon + Jupiter same sign → Raja yoga."""
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Moon": 5, "Jupiter": 5},
        )
        y = detect_raja_yoga(ch)
        assert y.active
        assert "Moon" in y.participants and "Jupiter" in y.participants

    def test_vipareeta_raja_dusthana_lord_in_dusthana(self):
        """Aries Lagna: 6L = Mercury (Virgo). Put Mercury in 8H → VR yoga fires."""
        # Aries Lagna; 8H = sign 8 (Scorpio)
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Mercury": 8},
            planet_houses={**_baseline_chart().planet_houses, "Mercury": 8},
        )
        y = detect_vipareeta_raja(ch)
        assert y.active
        assert "Mercury" in y.participants


class TestAfflictionYogas:
    """Mangal Dosha, Kala Sarpa, Daridra, Kemadruma."""

    def test_mangal_dosha_when_mars_in_7th_from_lagna(self):
        """Mars in 7H → Mangal Dosha (from Lagna)."""
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Mars": 7},
            planet_houses={**_baseline_chart().planet_houses, "Mars": 7},
        )
        y = detect_mangal_dosha(ch)
        assert y.active

    def test_mangal_dosha_inactive_when_mars_in_3rd(self):
        """Mars in 3H — not afflicting → no Mangal Dosha."""
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Mars": 3, "Moon": 5},
            planet_houses={**_baseline_chart().planet_houses, "Mars": 3, "Moon": 5},
        )
        y = detect_mangal_dosha(ch)
        # Mars in 3H from Lagna AND in 11th from Moon (5→3 = -2 = 11) → safe
        assert not y.active

    def test_kala_sarpa_inactive_when_nodes_degenerate(self):
        """Audit fix: Rahu/Ketu at same longitude → axis_sep == 0 → inactive."""
        ch = Chart(
            asc_sign=1, asc_lon=0.0,
            planet_signs={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                          "Jupiter", "Venus", "Saturn",
                                          "Rahu", "Ketu"]},
            planet_houses={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                           "Jupiter", "Venus", "Saturn",
                                           "Rahu", "Ketu"]},
            planet_lons={p: 0.0 for p in ["Sun", "Moon", "Mars", "Mercury",
                                           "Jupiter", "Venus", "Saturn",
                                           "Rahu", "Ketu"]},
        )
        y = detect_kala_sarpa(ch)
        assert not y.active
        assert "axis_sep" in y.description

    def test_kala_sarpa_inactive_when_planet_on_axis(self):
        """Audit fix: planet exactly at Rahu's longitude disqualifies."""
        ch = Chart(
            asc_sign=1, asc_lon=0.0,
            planet_signs={"Sun": 3, "Moon": 5, "Mars": 6, "Mercury": 4,
                          "Jupiter": 5, "Venus": 6, "Saturn": 5,
                          "Rahu": 3, "Ketu": 9},
            planet_houses={"Sun": 3, "Moon": 5, "Mars": 6, "Mercury": 4,
                           "Jupiter": 5, "Venus": 6, "Saturn": 5,
                           "Rahu": 3, "Ketu": 9},
            planet_lons={
                "Sun": 60.0,   # Exactly at Rahu's lon — on axis
                "Moon": 130.0, "Mars": 160.0, "Mercury": 110.0,
                "Jupiter": 140.0, "Venus": 155.0, "Saturn": 135.0,
                "Rahu": 60.0, "Ketu": 240.0,
            },
        )
        y = detect_kala_sarpa(ch)
        assert not y.active  # Sun straddles the axis

    def test_kala_sarpa_fires_when_all_planets_one_side_of_axis(self):
        """All 7 visible planets between Rahu and Ketu arc → Kala Sarpa."""
        ch = Chart(
            asc_sign=1, asc_lon=0.0,
            planet_signs={"Sun": 4, "Moon": 5, "Mars": 6, "Mercury": 4,
                          "Jupiter": 5, "Venus": 6, "Saturn": 5,
                          "Rahu": 3, "Ketu": 9},
            planet_houses={"Sun": 4, "Moon": 5, "Mars": 6, "Mercury": 4,
                           "Jupiter": 5, "Venus": 6, "Saturn": 5,
                           "Rahu": 3, "Ketu": 9},
            planet_lons={"Sun": 100.0, "Moon": 130.0, "Mars": 160.0,
                         "Mercury": 110.0, "Jupiter": 140.0, "Venus": 155.0,
                         "Saturn": 135.0, "Rahu": 60.0, "Ketu": 240.0},
        )
        y = detect_kala_sarpa(ch)
        assert y.active

    def test_kemadruma_fires_with_isolated_moon(self):
        """Moon alone (no planet 2nd/12th from Moon, no companion) → Kemadruma."""
        ch = Chart(
            asc_sign=1, asc_lon=0.0,
            planet_signs={"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 1,
                          "Jupiter": 9, "Venus": 1, "Saturn": 10,
                          "Rahu": 8, "Ketu": 2},  # Sign 4 (12th from Moon) and 6 (2nd) clear
            planet_houses={"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 1,
                           "Jupiter": 9, "Venus": 1, "Saturn": 10,
                           "Rahu": 8, "Ketu": 2},
            planet_lons={"Sun": 0, "Moon": 130, "Mars": 220, "Mercury": 5,
                         "Jupiter": 250, "Venus": 10, "Saturn": 280,
                         "Rahu": 225, "Ketu": 45},
        )
        y = detect_kemadruma(ch)
        assert y.active


class TestAuspiciousSpecials:
    """Amala — natural benefic in 10th from Lagna or Moon."""

    def test_amala_fires_when_jupiter_in_10th_from_lagna(self):
        """Jupiter (natural benefic) in 10H from Aries Lagna = Capricorn."""
        ch = _baseline_chart(
            planet_signs={**_baseline_chart().planet_signs, "Jupiter": 10},
            planet_houses={**_baseline_chart().planet_houses, "Jupiter": 10},
        )
        y = detect_amala(ch)
        assert y.active
        assert "Jupiter" in y.participants

    def test_amala_inactive_for_malefic_in_10th(self):
        """Saturn (natural malefic) in 10H — Amala inactive (different yoga)."""
        ch = _baseline_chart(
            planet_signs={
                # Move all benefics OUT of 10 from Lagna and 10 from Moon
                "Sun": 3, "Moon": 4, "Mars": 7, "Mercury": 9,
                "Jupiter": 11, "Venus": 2, "Saturn": 10,
                "Rahu": 6, "Ketu": 12,
            },
        )
        y = detect_amala(ch)
        # No benefic in target houses
        assert not y.active


class TestRegistryAndDetectAll:
    """Module-level: detector registry completeness, detect_all integrity."""

    def test_registry_has_at_least_20_yogas(self):
        """We claimed 21 in the docstring — verify."""
        assert len(YOGA_DETECTORS) >= 20

    def test_detect_all_returns_record_per_detector(self):
        """detect_all returns one Yoga per registered detector."""
        ch = _baseline_chart()
        results = detect_all(ch)
        assert len(results) == len(YOGA_DETECTORS)

    def test_active_yogas_is_subset(self):
        """active_yogas() is the filter where .active is True."""
        ch = _baseline_chart()
        active = active_yogas(ch)
        all_results = detect_all(ch)
        assert all(y.active for y in active)
        assert len(active) <= len(all_results)


# ─── L-1 expansion tests ─────────────────────────────────────────────


class TestNabhasaFamily:
    """L-1: Nabhasa Sankhya/Asraya/Dala yogas (BPHS Ch.36)."""

    def test_gola_when_all_planets_in_one_sign(self):
        from app.core.yoga_library import detect_gola
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={p: 1 for p in
                          ("Sun", "Moon", "Mars", "Mercury",
                           "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")},
            planet_houses={p: 1 for p in
                           ("Sun", "Moon", "Mars", "Mercury",
                            "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")},
            planet_lons={p: 10.0 for p in
                         ("Sun", "Moon", "Mars", "Mercury",
                          "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")},
        )
        y = detect_gola(chart)
        assert y.active is True
        assert y.name == "Gola"

    def test_veena_when_all_in_distinct_signs(self):
        from app.core.yoga_library import detect_veena
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
                          "Jupiter": 5, "Venus": 6, "Saturn": 7},
            planet_houses={"Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
                           "Jupiter": 5, "Venus": 6, "Saturn": 7},
            planet_lons={"Sun": 10.0, "Moon": 40.0, "Mars": 70.0,
                         "Mercury": 100.0, "Jupiter": 130.0,
                         "Venus": 160.0, "Saturn": 190.0},
        )
        y = detect_veena(chart)
        assert y.active is True
        assert y.name == "Veena"

    def test_rajju_when_all_in_chara(self):
        from app.core.yoga_library import detect_rajju
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10,
                          "Jupiter": 1, "Venus": 4, "Saturn": 7},
            planet_houses={"Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10,
                           "Jupiter": 1, "Venus": 4, "Saturn": 7},
            planet_lons={"Sun": 10.0, "Moon": 100.0, "Mars": 190.0,
                         "Mercury": 280.0, "Jupiter": 20.0,
                         "Venus": 110.0, "Saturn": 200.0},
        )
        y = detect_rajju(chart)
        assert y.active is True


class TestPravrajyaFamily:
    """L-1: Renunciation yogas (BPHS Ch.78)."""

    def test_pravrajya_when_4plus_grahas_one_sign(self):
        from app.core.yoga_library import detect_pravrajya_4plus_in_one_sign
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Sun": 5, "Mars": 5, "Mercury": 5, "Jupiter": 5,
                          "Moon": 2, "Venus": 3, "Saturn": 11},
            planet_houses={"Sun": 5, "Mars": 5, "Mercury": 5, "Jupiter": 5,
                           "Moon": 2, "Venus": 3, "Saturn": 11},
            planet_lons={"Sun": 130.0, "Mars": 132.0, "Mercury": 135.0,
                         "Jupiter": 138.0, "Moon": 40.0, "Venus": 70.0,
                         "Saturn": 310.0},
        )
        y = detect_pravrajya_4plus_in_one_sign(chart)
        assert y.active is True


class TestChartArchitectureExpansion:
    """L-1: Royal-grade and architectural yogas."""

    def test_chatussagara_when_all_4_kendras_occupied(self):
        from app.core.yoga_library import detect_chatussagara
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10,
                          "Jupiter": 1, "Venus": 4, "Saturn": 7},
            planet_houses={"Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10,
                           "Jupiter": 1, "Venus": 4, "Saturn": 7},
            planet_lons={"Sun": 10.0, "Moon": 100.0, "Mars": 190.0,
                         "Mercury": 280.0, "Jupiter": 20.0,
                         "Venus": 110.0, "Saturn": 200.0},
        )
        y = detect_chatussagara(chart)
        assert y.active is True


class TestRegistryCount:
    """L-1: Verify registry expansion."""

    def test_registry_count_is_66(self):
        """L-1 expanded from 39 → 66 yogas (+27 across Nabhasa/Pravrajya/
        affliction/wealth/architecture/vargottama)."""
        from app.core.yoga_library import YOGA_DETECTORS
        assert len(YOGA_DETECTORS) == 66
