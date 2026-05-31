"""Tests for app.core.varshaphala — S-4 Tajik/annual progression."""
from __future__ import annotations

import pytest

from app.core.varshaphala import (
    Muntha, Saham, VarshaphalaReport, compute_muntha,
    compute_sahams, compute_varshaphala, format_varshaphala,
)


_BASELINE_LONS = {
    "Sun": 88.6, "Moon": 351.0, "Mars": 120.5, "Mercury": 95.2,
    "Jupiter": 101.8, "Venus": 102.0, "Saturn": 268.4,
    "Rahu": 348.5, "Ketu": 168.5,
}


class TestMuntha:
    def test_age_0_muntha_in_lagna(self):
        """At age 0, Muntha is in the natal Lagna (1H)."""
        m = compute_muntha(asc_sign=6, age_years=0.0)
        assert m.sign == 6
        assert m.house_from_lagna == 1

    def test_age_1_muntha_in_2h(self):
        """At age 1, Muntha advances to 2H."""
        m = compute_muntha(asc_sign=6, age_years=1.0)
        assert m.house_from_lagna == 2

    def test_age_12_muntha_back_to_1h(self):
        """At age 12, Muntha completes a full cycle back to Lagna."""
        m = compute_muntha(asc_sign=6, age_years=12.0)
        assert m.sign == 6
        assert m.house_from_lagna == 1

    def test_age_36_muntha_3_cycles_back_to_1h(self):
        m = compute_muntha(asc_sign=8, age_years=36.0)
        assert m.sign == 8
        assert m.house_from_lagna == 1

    def test_munthesha_lord_correct(self):
        """Muntha in Aries (sign 1) → munthesha = Mars."""
        m = compute_muntha(asc_sign=1, age_years=0.0)
        assert m.munthesha == "Mars"
        m = compute_muntha(asc_sign=1, age_years=4.0)  # → sign 5 (Leo)
        assert m.munthesha == "Sun"

    def test_negative_age_raises(self):
        with pytest.raises(ValueError):
            compute_muntha(asc_sign=1, age_years=-1.0)

    def test_fractional_age_truncates(self):
        """age 11.99 still rounds DOWN to 11 (year-not-yet-completed)."""
        m = compute_muntha(asc_sign=1, age_years=11.99)
        assert m.house_from_lagna == 12


class TestSahams:
    def test_returns_8_sahams(self):
        sahams = compute_sahams(
            asc_sign=6, asc_lon=173.99,
            planet_lons=_BASELINE_LONS,
        )
        assert len(sahams) == 8
        names = {s.name for s in sahams}
        assert names == {"Punya", "Vidya", "Karma", "Yasas",
                         "Putra", "Vivaha", "Mrityu", "Bhratru"}

    def test_saham_sign_in_1_12(self):
        sahams = compute_sahams(6, 173.99, _BASELINE_LONS)
        for s in sahams:
            assert 1 <= s.sign <= 12

    def test_saham_house_in_1_12(self):
        sahams = compute_sahams(6, 173.99, _BASELINE_LONS)
        for s in sahams:
            assert 1 <= s.house_from_lagna <= 12

    def test_saham_longitude_in_0_360(self):
        sahams = compute_sahams(6, 173.99, _BASELINE_LONS)
        for s in sahams:
            assert 0.0 <= s.longitude < 360.0

    def test_punya_formula_correct(self):
        """Punya = Asc + Moon - Sun, mod 360."""
        sahams = compute_sahams(1, 10.0, {"Sun": 100.0, "Moon": 200.0})
        # Only Punya should fire (other formulas need more planets)
        punya = next((s for s in sahams if s.name == "Punya"), None)
        assert punya is not None
        expected_lon = (10.0 + 200.0 - 100.0) % 360.0  # 110.0
        assert abs(punya.longitude - expected_lon) < 0.01
        # 110 is in sign 4 (Cancer)
        assert punya.sign == 4

    def test_missing_planet_skips_saham(self):
        """Vidya needs Mercury + Jupiter; if Mercury missing, skip."""
        sahams = compute_sahams(1, 10.0,
                                 {"Sun": 100.0, "Moon": 200.0,
                                  "Jupiter": 50.0})  # no Mercury
        names = {s.name for s in sahams}
        assert "Vidya" not in names
        assert "Punya" in names  # only needs Sun+Moon


class TestWellPlacedFlag:
    def test_kendra_placement_well_placed(self):
        """A saham in 1/4/7/10 is well-placed."""
        sahams = compute_sahams(6, 173.99, _BASELINE_LONS)
        for s in sahams:
            if s.house_from_lagna in (1, 4, 5, 7, 9, 10):
                assert s.is_well_placed is True

    def test_dushtana_placement_not_well_placed(self):
        """A saham in 6/8/12 is not well-placed."""
        sahams = compute_sahams(6, 173.99, _BASELINE_LONS)
        for s in sahams:
            if s.house_from_lagna in (6, 8, 12):
                assert s.is_well_placed is False


class TestAggregate:
    def test_returns_full_report(self):
        r = compute_varshaphala(6, 173.99, _BASELINE_LONS, age_years=35.0)
        assert isinstance(r, VarshaphalaReport)
        assert r.muntha.age_years == 35.0
        assert len(r.sahams) == 8

    def test_format_returns_string(self):
        r = compute_varshaphala(6, 173.99, _BASELINE_LONS, age_years=35.0)
        text = format_varshaphala(r)
        assert "VARSHAPHALA" in text
        assert "Muntha" in text
        for name in ("Punya", "Vidya", "Karma"):
            assert name in text
