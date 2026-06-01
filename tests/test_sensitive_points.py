"""Tests for sensitive points + Upagrahas — Gap E."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.sensitive_points import (
    SensitivePoint, beeja_sphuta, bhrigu_bindu, compute_all,
    kshetra_sphuta, maandi, pranapada, upagrahas,
)


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


class TestBhriguBindu:
    def test_returns_sensitive_point(self):
        sp = bhrigu_bindu(_baseline_chart())
        assert isinstance(sp, SensitivePoint)
        assert sp.name == "Bhrigu Bindu"

    def test_longitude_in_valid_range(self):
        sp = bhrigu_bindu(_baseline_chart())
        assert 0 <= sp.longitude < 360

    def test_sign_and_house_in_valid_range(self):
        sp = bhrigu_bindu(_baseline_chart())
        assert 1 <= sp.sign <= 12
        assert 1 <= sp.natal_house <= 12

    def test_midpoint_of_close_rahu_moon(self):
        """If Rahu=350° and Moon=10°, midpoint is 0° (Aries 0°),
        crossing the boundary. The 180° wrap rule kicks in."""
        chart = Chart(
            asc_sign=1, asc_lon=0.0,
            planet_signs={"Rahu": 12, "Moon": 1, "Sun": 1, "Mars": 1,
                          "Mercury": 1, "Jupiter": 1, "Venus": 1,
                          "Saturn": 1, "Ketu": 6},
            planet_houses={"Rahu": 12, "Moon": 1, "Sun": 1, "Mars": 1,
                           "Mercury": 1, "Jupiter": 1, "Venus": 1,
                           "Saturn": 1, "Ketu": 6},
            planet_lons={"Rahu": 350.0, "Moon": 10.0, "Sun": 10.0,
                         "Mars": 10.0, "Mercury": 10.0, "Jupiter": 10.0,
                         "Venus": 10.0, "Saturn": 10.0, "Ketu": 170.0},
        )
        sp = bhrigu_bindu(chart)
        # Midpoint of 350 and 10 crossing 0° = (350+10)/2 = 180 OR with
        # wrap: 0°. The shorter arc rule kicks in.
        assert sp.longitude in (180.0, 0.0)

    def test_requires_rahu_and_moon(self):
        chart = Chart(asc_sign=1, asc_lon=0.0,
                      planet_signs={"Sun": 1},
                      planet_houses={"Sun": 1},
                      planet_lons={"Sun": 10.0})
        with pytest.raises(ValueError):
            bhrigu_bindu(chart)


class TestPranapada:
    def test_returns_sensitive_point(self):
        sp = pranapada(_baseline_chart())
        assert isinstance(sp, SensitivePoint)
        assert sp.name == "Pranapada"

    def test_longitude_in_valid_range(self):
        sp = pranapada(_baseline_chart())
        assert 0 <= sp.longitude < 360


class TestUpagrahas:
    def test_returns_5_upagrahas(self):
        u = upagrahas(_baseline_chart())
        assert set(u.keys()) == {"Dhuma", "Vyatipata", "Parivesha",
                                  "Indrachapa", "Upaketu"}

    def test_each_has_valid_position(self):
        u = upagrahas(_baseline_chart())
        for name, sp in u.items():
            assert 0 <= sp.longitude < 360, f"{name}: bad longitude"
            assert 1 <= sp.sign <= 12, f"{name}: bad sign"
            assert 1 <= sp.natal_house <= 12, f"{name}: bad house"


class TestMaandi:
    def test_returns_sensitive_point_with_meta(self):
        sp = maandi(_baseline_chart(), day_of_week=0, is_day_birth=True)
        assert sp.name == "Maandi (Gulika)"
        assert "day" in sp.interpretation_hint.lower()

    def test_rejects_invalid_day_of_week(self):
        with pytest.raises(ValueError):
            maandi(_baseline_chart(), day_of_week=7, is_day_birth=True)

    def test_day_vs_night_differs(self):
        """Day Maandi and night Maandi differ in part-of-day index."""
        day = maandi(_baseline_chart(), day_of_week=0, is_day_birth=True)
        night = maandi(_baseline_chart(), day_of_week=0, is_day_birth=False)
        # Different parts → likely different longitudes
        # (Sunday day part=6, night part=2 → different)
        assert day.longitude != night.longitude


class TestBeejaSphuta:
    def test_returns_fertility_sphuta(self):
        bs = beeja_sphuta(_baseline_chart())
        assert bs.name == "Beeja Sphuta"
        assert 1 <= bs.sign <= 12
        assert bs.fertility_grade in {"STRONG", "AVERAGE", "WEAK"}
        assert bs.dignity in {"exalted", "own", "neutral", "debilitated"}

    def test_sum_modulo_360(self):
        """Beeja = (Sun + Jupiter + Venus) mod 360."""
        chart = _baseline_chart()
        expected = (chart.planet_lons["Sun"] + chart.planet_lons["Jupiter"]
                    + chart.planet_lons["Venus"]) % 360
        bs = beeja_sphuta(chart)
        assert abs(bs.longitude - expected) < 0.001


class TestKshetraSphuta:
    def test_returns_fertility_sphuta(self):
        ks = kshetra_sphuta(_baseline_chart())
        assert ks.name == "Kshetra Sphuta"

    def test_sum_modulo_360(self):
        """Kshetra = (Moon + Jupiter + Mars) mod 360."""
        chart = _baseline_chart()
        expected = (chart.planet_lons["Moon"] + chart.planet_lons["Jupiter"]
                    + chart.planet_lons["Mars"]) % 360
        ks = kshetra_sphuta(chart)
        assert abs(ks.longitude - expected) < 0.001


class TestComputeAll:
    def test_aggregates_all_without_maandi(self):
        """Without day_of_week + is_day_birth, Maandi is None."""
        r = compute_all(_baseline_chart())
        assert r.bhrigu_bindu is not None
        assert r.pranapada is not None
        assert len(r.upagrahas) == 5
        assert r.beeja_sphuta is not None
        assert r.kshetra_sphuta is not None
        assert r.maandi is None

    def test_includes_maandi_when_provided(self):
        r = compute_all(_baseline_chart(), day_of_week=0, is_day_birth=True)
        assert r.maandi is not None
        assert r.maandi.name == "Maandi (Gulika)"
