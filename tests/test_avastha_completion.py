"""Tests for avastha completion — Gap F."""
from __future__ import annotations

import pytest

from app.core.avastha_completion import (
    AvasthaReport, BaladiAvastha, DeeptadiAvastha,
    avastha_report, baladi_avastha, baladi_for_chart,
    composite_avastha_multiplier, deeptadi_avastha, deeptadi_for_chart,
)
from app.core.chart_model import Chart


def _baseline_chart() -> Chart:
    return Chart(
        asc_sign=6, asc_lon=173.99,
        planet_signs={"Sun": 3, "Moon": 12, "Mars": 4, "Mercury": 3,
                      "Jupiter": 4, "Venus": 4, "Saturn": 9,
                      "Rahu": 12, "Ketu": 6},
        planet_houses={"Sun": 10, "Moon": 7, "Mars": 11, "Mercury": 10,
                       "Jupiter": 11, "Venus": 11, "Saturn": 4,
                       "Rahu": 7, "Ketu": 1},
        planet_lons={"Sun": 88.6, "Moon": 351.0, "Mars": 120.5,
                     "Mercury": 95.2, "Jupiter": 101.8, "Venus": 102.0,
                     "Saturn": 268.4, "Rahu": 348.5, "Ketu": 168.5},
    )


class TestBaladi:
    def test_odd_sign_zone_0_is_bala(self):
        """Odd sign, 0-6° = Bala (infant)."""
        b = baladi_avastha("Sun", sign=1, deg_in_sign=3.0)
        assert b.stage == "Bala"
        assert b.strength_multiplier == 0.25

    def test_odd_sign_zone_2_is_yuva(self):
        """Odd sign, 12-18° = Yuva (youth), full strength."""
        b = baladi_avastha("Sun", sign=1, deg_in_sign=15.0)
        assert b.stage == "Yuva"
        assert b.strength_multiplier == 1.0

    def test_odd_sign_zone_4_is_mrita(self):
        """Odd sign, 24-30° = Mrita (dead), almost nothing."""
        b = baladi_avastha("Sun", sign=1, deg_in_sign=27.0)
        assert b.stage == "Mrita"
        assert b.strength_multiplier < 0.2

    def test_even_sign_reverses(self):
        """Even sign reverses: 0-6° = Mrita, 24-30° = Bala."""
        b = baladi_avastha("Moon", sign=2, deg_in_sign=3.0)
        assert b.stage == "Mrita"
        # And the other end
        b2 = baladi_avastha("Moon", sign=2, deg_in_sign=27.0)
        assert b2.stage == "Bala"

    def test_rejects_invalid_sign(self):
        with pytest.raises(ValueError):
            baladi_avastha("Sun", sign=13, deg_in_sign=5.0)

    def test_overshoot_degree_normalised_modulo(self):
        """deg_in_sign > 30 is silently normalised via modulo (tolerant
        of upstream sign/longitude rounding artifacts)."""
        # 35.0 % 30 = 5.0 = Bala for odd sign
        b = baladi_avastha("Sun", sign=1, deg_in_sign=35.0)
        assert b.stage == "Bala"


class TestBaladiForChart:
    def test_returns_entry_per_planet_with_lon(self):
        """All 9 chart planets with longitudes get a Baladi entry."""
        bs = baladi_for_chart(_baseline_chart())
        # Baseline has all 9 grahas with lon
        assert len(bs) == 9
        assert all(isinstance(b, BaladiAvastha) for b in bs.values())


class TestDeeptadi:
    def test_exalted_planet_is_deepta(self):
        """Jupiter exalted in Cancer (sign 4) → Deepta state."""
        chart = _baseline_chart()
        # In baseline, Jupiter is in sign 4 (Cancer) — exalted
        d = deeptadi_avastha("Jupiter", chart)
        assert d.state == "Deepta"
        assert d.strength_multiplier > 1.0

    def test_own_sign_planet_is_swastha(self):
        """Mercury in Gemini (own sign) → Swastha."""
        chart = Chart(
            asc_sign=6, asc_lon=173.99,
            planet_signs={"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                          "Jupiter": 9, "Venus": 7, "Saturn": 10,
                          "Rahu": 3, "Ketu": 9},
            planet_houses={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                          "Jupiter", "Venus", "Saturn",
                                          "Rahu", "Ketu"]},
            planet_lons={"Sun": 130.0, "Moon": 100.0, "Mars": 5.0,
                         "Mercury": 75.0, "Jupiter": 250.0, "Venus": 195.0,
                         "Saturn": 285.0, "Rahu": 70.0, "Ketu": 250.0},
        )
        d = deeptadi_avastha("Mercury", chart)
        assert d.state == "Swastha"

    def test_combust_planet_is_vikala_when_not_dignified(self):
        """A non-dignified planet within combustion orb of Sun → Vikala."""
        chart = Chart(
            asc_sign=1, asc_lon=0.0,
            planet_signs={p: 5 for p in ["Sun", "Mercury", "Mars",
                                          "Jupiter", "Venus", "Saturn",
                                          "Moon", "Rahu", "Ketu"]},
            planet_houses={p: 5 for p in ["Sun", "Mercury", "Mars",
                                           "Jupiter", "Venus", "Saturn",
                                           "Moon", "Rahu", "Ketu"]},
            planet_lons={"Sun": 130.0, "Mercury": 132.0,  # Mercury 2° away
                         "Mars": 10.0, "Jupiter": 250.0, "Venus": 195.0,
                         "Saturn": 285.0, "Moon": 100.0,
                         "Rahu": 70.0, "Ketu": 250.0},
        )
        # Mercury at 132° = sign 5 (Leo). NOT Mercury's own sign or exalt.
        # And within 2° of Sun → combust → Vikala.
        d = deeptadi_avastha("Mercury", chart)
        assert d.state == "Vikala"


class TestDeeptadiForChart:
    def test_returns_only_visible_planets(self):
        """Rahu and Ketu are excluded from Deeptadi (no dispositor logic)."""
        ds = deeptadi_for_chart(_baseline_chart())
        assert "Rahu" not in ds
        assert "Ketu" not in ds
        assert "Sun" in ds and "Saturn" in ds


class TestAvasthaReport:
    def test_returns_both_baladi_and_deeptadi(self):
        r = avastha_report(_baseline_chart())
        assert isinstance(r, AvasthaReport)
        assert len(r.baladi) > 0
        assert len(r.deeptadi) > 0


class TestCompositeMultiplier:
    def test_product_of_baladi_and_deeptadi(self):
        """Composite multiplier = baladi.mult × deeptadi.mult."""
        chart = _baseline_chart()
        mult = composite_avastha_multiplier("Jupiter", chart)
        # Jupiter is exalted (Deepta = 1.2). Its degree (101.8 - 90 = 11.8°)
        # in sign 4 (even) maps to Vridda zone (18-24° in reverse table).
        # Wait — 11.8° in EVEN sign reversed table: zones are reversed.
        # In even sign 0-6°=Mrita, 6-12°=Vridda, 12-18°=Yuva, 18-24°=Kumara,
        # 24-30°=Bala. Jupiter at 11.8° = Vridda (0.5 multiplier).
        # So composite = 0.5 * 1.2 = 0.6.
        assert 0.5 <= mult <= 0.7

    def test_missing_planet_returns_one(self):
        chart = Chart(asc_sign=1, asc_lon=0.0, planet_signs={},
                      planet_houses={}, planet_lons={})
        assert composite_avastha_multiplier("Sun", chart) == 1.0
