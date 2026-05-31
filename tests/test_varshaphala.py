"""Tests for app.core.varshaphala — S-4 Tajik/annual progression + D-3 solar return."""
from __future__ import annotations

import pytest

from app.core.varshaphala import (
    AnnualChart, Muntha, Saham, VarshaphalaReport,
    compute_annual_chart, compute_muntha, compute_sahams,
    compute_varshaphala, find_solar_return_jd, format_annual_chart,
    format_varshaphala,
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
    def test_returns_expected_sahams_when_all_planets_present(self):
        """L-2: expanded from 28 to 50 sahams via full Tajik Neelakanthi canon."""
        sahams = compute_sahams(
            asc_sign=6, asc_lon=173.99,
            planet_lons=_BASELINE_LONS,
        )
        # 50 named formulas; all fire when 7 visible grahas present
        assert len(sahams) == 50
        names = {s.name for s in sahams}
        # Original 8 still present
        for core in ("Punya", "Vidya", "Karma", "Yasas",
                     "Putra", "Vivaha", "Mrityu", "Bhratru"):
            assert core in names, f"core saham {core} missing"
        # D-2 additions still present
        for d2_saham in ("Pitru", "Matri", "Roga", "Apamrityu",
                         "Karagriha", "Bhagya", "Paradesh", "Samartha"):
            assert d2_saham in names, f"D-2 saham {d2_saham} missing"
        # NEW L-2 expansion (22)
        for l2_saham in ("VivahaM", "VivahaF", "Garbha", "Manmatha",
                         "Trikona", "Sampatti", "Rajya", "Yatra",
                         "Vyavasaya", "Brahma", "Tarakesha", "Adhana"):
            assert l2_saham in names, f"L-2 saham {l2_saham} missing"

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
        # L-2: 50 sahams (was 28 in D-2 pass)
        assert len(r.sahams) == 50

    def test_format_returns_string(self):
        r = compute_varshaphala(6, 173.99, _BASELINE_LONS, age_years=35.0)
        text = format_varshaphala(r)
        assert "VARSHAPHALA" in text
        assert "Muntha" in text
        for name in ("Punya", "Vidya", "Karma"):
            assert name in text


class TestSolarReturnSearch:
    """D-3: find_solar_return_jd converges to natal Sun longitude."""

    def test_converges_for_known_natal(self):
        """Search from birth_jd should converge within tolerance."""
        # Use a recent JD (Agatha's birth) and search for age 40
        natal_sun = 156.7
        birth_jd = 2411626.0
        return_jd = find_solar_return_jd(natal_sun, birth_jd, age_years=40)
        # Verify by recomputing Sun at that JD
        import swisseph as swe
        from app.core.ephemeris_engine import calculate_d1_position
        sun_at_return = calculate_d1_position(return_jd, swe.SUN)["longitude"]
        diff = ((natal_sun - sun_at_return + 180.0) % 360.0) - 180.0
        # Should be within 30 arcsec = 0.0083 deg
        assert abs(diff) < 0.01, f"diff = {diff} deg"

    def test_return_jd_in_correct_year(self):
        """Solar return at age N should land within ~30 days of birth+N years."""
        natal_sun = 156.7
        birth_jd = 2411626.0
        for age in (1, 10, 40):
            rj = find_solar_return_jd(natal_sun, birth_jd, age_years=age)
            expected = birth_jd + age * 365.2425
            assert abs(rj - expected) < 30, (
                f"age {age}: return_jd {rj} should be within 30 days of "
                f"expected {expected}"
            )


class TestAnnualChart:
    """D-3: compute_annual_chart casts the full Tajik chart."""

    def test_returns_annual_chart(self):
        ac = compute_annual_chart(
            natal_asc_sign=9, natal_asc_lon=270.0,
            natal_sun_lon=156.7,
            birth_jd=2411626.0,
            birth_lat=50.46, birth_lon_deg=-3.53,
            age_years=40,
        )
        assert isinstance(ac, AnnualChart)

    def test_annual_sun_matches_natal_sun(self):
        """By definition the annual Sun longitude == natal Sun longitude."""
        natal_sun = 156.7
        ac = compute_annual_chart(
            natal_asc_sign=9, natal_asc_lon=270.0,
            natal_sun_lon=natal_sun,
            birth_jd=2411626.0,
            birth_lat=50.46, birth_lon_deg=-3.53,
            age_years=40,
        )
        diff = abs(ac.annual_planet_lons["Sun"] - natal_sun)
        assert diff < 0.01, f"annual Sun {ac.annual_planet_lons['Sun']} differs from natal {natal_sun} by {diff} deg"

    def test_annual_planets_all_present(self):
        ac = compute_annual_chart(
            natal_asc_sign=9, natal_asc_lon=270.0,
            natal_sun_lon=156.7,
            birth_jd=2411626.0,
            birth_lat=50.46, birth_lon_deg=-3.53,
            age_years=40,
        )
        expected = {"Sun", "Moon", "Mars", "Mercury",
                    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        assert set(ac.annual_planet_signs.keys()) == expected
        assert set(ac.annual_planet_lons.keys()) == expected

    def test_annual_sahams_referenced_to_annual_lagna(self):
        """Annual Sahams use the annual Asc, not the natal Asc."""
        ac = compute_annual_chart(
            natal_asc_sign=9, natal_asc_lon=270.0,
            natal_sun_lon=156.7,
            birth_jd=2411626.0,
            birth_lat=50.46, birth_lon_deg=-3.53,
            age_years=40,
        )
        assert len(ac.annual_sahams) == 50  # L-2: full 50-saham canon
        # Smoke: at least the Punya saham was computed
        punya = next((s for s in ac.annual_sahams if s.name == "Punya"), None)
        assert punya is not None

    def test_format_returns_string(self):
        ac = compute_annual_chart(
            natal_asc_sign=9, natal_asc_lon=270.0,
            natal_sun_lon=156.7,
            birth_jd=2411626.0,
            birth_lat=50.46, birth_lon_deg=-3.53,
            age_years=40,
        )
        text = format_annual_chart(ac)
        assert "ANNUAL CHART" in text
        assert "Return JD" in text
        assert "Annual Lagna" in text
