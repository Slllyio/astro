"""Tests for D-4: complete Kala-bala sub-components in app.core.shadbala."""
from __future__ import annotations

import pytest

from app.core.shadbala import (
    hora_bala, kala_bala, nathonata_bala,
    tribhaga_bala, vara_bala,
)


class TestNathonata:
    """Diurnal planets peak at noon, nocturnal at midnight, Mercury always full."""

    def test_sun_peaks_at_noon(self):
        assert nathonata_bala("Sun", hour_of_day=12.0, is_day_birth=True) == 60.0

    def test_sun_zero_at_midnight(self):
        # Midnight = hour 0 or 24
        assert nathonata_bala("Sun", hour_of_day=0.0, is_day_birth=False) == 0.0

    def test_moon_peaks_at_midnight(self):
        assert nathonata_bala("Moon", hour_of_day=0.0, is_day_birth=False) == 60.0

    def test_moon_zero_at_noon(self):
        assert nathonata_bala("Moon", hour_of_day=12.0, is_day_birth=True) == 0.0

    def test_mercury_always_full(self):
        for h in (0.0, 6.0, 12.0, 18.0):
            assert nathonata_bala("Mercury", hour_of_day=h, is_day_birth=True) == 60.0

    def test_nodes_get_zero(self):
        assert nathonata_bala("Rahu", hour_of_day=12.0, is_day_birth=True) == 0.0
        assert nathonata_bala("Ketu", hour_of_day=12.0, is_day_birth=True) == 0.0

    def test_diurnal_nocturnal_sum_to_60(self):
        """Diurnal + nocturnal strength always sums to 60 (zero-sum split)."""
        for h in (3.0, 9.0, 12.0, 15.0, 21.0):
            d = nathonata_bala("Sun", h, True)
            n = nathonata_bala("Moon", h, True)
            assert abs(d + n - 60.0) < 0.01, f"h={h}: {d}+{n} != 60"


class TestTribhaga:
    """Day/night split into 3 portions, each ruled by a specific planet.
    Jupiter always gets 60 (rules all portions)."""

    def test_jupiter_always_full(self):
        for h in (7.0, 11.0, 15.0, 19.0, 23.0, 3.0):
            assert tribhaga_bala("Jupiter", h, True) == 60.0

    def test_mercury_rules_day_first_third(self):
        """6:00-10:00 → Mercury."""
        assert tribhaga_bala("Mercury", 7.0, True) == 60.0
        assert tribhaga_bala("Sun", 7.0, True) == 0.0

    def test_sun_rules_day_middle_third(self):
        assert tribhaga_bala("Sun", 11.0, True) == 60.0

    def test_saturn_rules_day_last_third(self):
        assert tribhaga_bala("Saturn", 15.0, True) == 60.0

    def test_moon_rules_night_first_third(self):
        """18:00-22:00 → Moon."""
        assert tribhaga_bala("Moon", 19.0, False) == 60.0

    def test_venus_rules_night_middle_third(self):
        """22:00-02:00 → Venus."""
        assert tribhaga_bala("Venus", 23.0, False) == 60.0
        assert tribhaga_bala("Venus", 1.0, False) == 60.0

    def test_mars_rules_night_last_third(self):
        assert tribhaga_bala("Mars", 4.0, False) == 60.0

    def test_nodes_get_zero(self):
        assert tribhaga_bala("Rahu", 11.0, True) == 0.0


class TestVaraBala:
    """Lord of the birth weekday gets +45."""

    def test_sunday_sun(self):
        assert vara_bala("Sun", day_of_week=0) == 45.0
        assert vara_bala("Moon", day_of_week=0) == 0.0

    def test_monday_moon(self):
        assert vara_bala("Moon", day_of_week=1) == 45.0

    def test_saturday_saturn(self):
        assert vara_bala("Saturn", day_of_week=6) == 45.0

    def test_rejects_invalid_dow(self):
        with pytest.raises(ValueError):
            vara_bala("Sun", day_of_week=7)
        with pytest.raises(ValueError):
            vara_bala("Sun", day_of_week=-1)


class TestHoraBala:
    """24-hora cycle from day-lord through Chaldean sequence."""

    def test_first_hora_after_sunrise_is_day_lord(self):
        """First hora after sunrise = day-lord. Sunday's first hora = Sun."""
        # 7 AM Sunday → 1 hour after sunrise → still in Sun's hora
        assert hora_bala("Sun", hour_of_day=6.5, day_of_week=0) == 60.0

    def test_second_hora_advances_chaldean(self):
        """Second hora = Venus (next in Chaldean sequence after Sun).

        Chaldean: Saturn -> Jupiter -> Mars -> Sun -> Venus -> Mercury -> Moon
        After Sun comes Venus.
        """
        assert hora_bala("Venus", hour_of_day=7.5, day_of_week=0) == 60.0

    def test_monday_first_hora_is_moon(self):
        assert hora_bala("Moon", hour_of_day=6.5, day_of_week=1) == 60.0

    def test_only_one_planet_per_hora(self):
        """At any (hour, day) only ONE planet has 60; others 0."""
        n_with_60 = sum(
            hora_bala(p, hour_of_day=10.0, day_of_week=3) == 60.0
            for p in ("Sun", "Moon", "Mars", "Mercury",
                      "Jupiter", "Venus", "Saturn")
        )
        assert n_with_60 == 1


class TestKalaBalaAggregator:
    """kala_bala() sums the 5 sub-components with graceful degradation."""

    def test_paksha_only_when_no_time_inputs(self):
        """With no hour_of_day/dow, only paksha contributes."""
        r = kala_bala("Sun", sun_lon=0.0, moon_lon=180.0)
        # Sun's paksha at full moon = malefic peak inverted = 0
        # All other components = 0 (no inputs)
        assert r["paksha"] == 0.0
        assert r["nathonata"] == 0.0
        assert r["tribhaga"] == 0.0
        assert r["vara"] == 0.0
        assert r["hora"] == 0.0
        assert r["total"] == 0.0

    def test_full_inputs_compute_all_components(self):
        """With all inputs, all 5 sub-components compute."""
        r = kala_bala(
            "Sun", sun_lon=0.0, moon_lon=180.0,
            hour_of_day=12.0, is_day_birth=True, day_of_week=0,
        )
        # Sun at noon → nathonata=60
        # 12:00 day → Sun's tribhaga portion (10-14) → 60
        # Sunday → Sun's vara → 45
        # First hora after 6am Sunday = Sun → 60
        assert r["nathonata"] == 60.0
        assert r["tribhaga"] == 60.0
        assert r["vara"] == 45.0
        # Total = sum of 5 components
        assert r["total"] == r["paksha"] + r["nathonata"] + r["tribhaga"] + r["vara"] + r["hora"]

    def test_returns_dict_with_total_field(self):
        r = kala_bala("Moon", 0.0, 180.0)
        assert "total" in r
        assert "paksha" in r
