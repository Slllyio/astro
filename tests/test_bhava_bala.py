"""Tests for app.core.bhava_bala — S-2 intrinsic bhava strength."""
from __future__ import annotations

import pytest

from app.core.bhava_bala import (
    BhavaStrengthReport, compute_bhava_bala, compute_bhava_bala_for,
    format_bhava_bala,
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


class TestPerBhava:
    def test_returns_report(self):
        r = compute_bhava_bala_for(_baseline_chart(), 1)
        assert isinstance(r, BhavaStrengthReport)
        assert r.bhava == 1

    def test_lord_correct_for_virgo_lagna(self):
        """Virgo Lagna (sign 6) → 1H sign = 6 (Virgo) → lord = Mercury."""
        r = compute_bhava_bala_for(_baseline_chart(), 1)
        assert r.lord == "Mercury"

    def test_rejects_invalid_bhava(self):
        with pytest.raises(ValueError):
            compute_bhava_bala_for(_baseline_chart(), 13)
        with pytest.raises(ValueError):
            compute_bhava_bala_for(_baseline_chart(), 0)

    def test_composite_in_0_10_range(self):
        for b in range(1, 13):
            r = compute_bhava_bala_for(_baseline_chart(), b)
            assert 0.0 <= r.composite_bhava_bala <= 10.0


class TestFullChart:
    def test_all_12_bhavas_reported(self):
        reports = compute_bhava_bala(_baseline_chart())
        assert set(reports.keys()) == set(range(1, 13))

    def test_labels_valid(self):
        reports = compute_bhava_bala(_baseline_chart())
        for r in reports.values():
            assert r.strength_label in (
                "very strong", "strong", "average", "weak", "very weak",
            )


class TestKendraStrengthAdvantage:
    def test_kendra_bhavas_have_dig_bonus(self):
        reports = compute_bhava_bala(_baseline_chart())
        for kendra in (1, 4, 7, 10):
            assert reports[kendra].dig_bala >= 1.0, (
                f"bhava {kendra} should have +1.0 dig_bala (kendra)"
            )

    def test_dushtana_bhavas_have_dig_penalty(self):
        reports = compute_bhava_bala(_baseline_chart())
        for d in (8, 12):
            assert reports[d].dig_bala < 0, (
                f"bhava {d} should have negative dig_bala (pure dushtana)"
            )


class TestDoctrinalLordPlacement:
    def test_exalted_lord_boosts_bhavadhipati(self):
        """Mars exalted in Capricorn (sign 10) gives lord-strong boost."""
        # Chart with Aries Lagna (sign 1, lord Mars) and Mars exalted
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Mars": 10, "Sun": 1, "Moon": 1},
            planet_houses={"Mars": 10, "Sun": 1, "Moon": 1},
            planet_lons={"Mars": 280.0, "Sun": 10.0, "Moon": 10.0},
        )
        r = compute_bhava_bala_for(chart, 1)
        assert r.lord == "Mars"
        # Mars exalted in Capricorn = +1.5 + 0.5 (kendra) = base 1.0 + 2.0 = 3.0
        assert r.bhavadhipati_bala >= 2.5

    def test_debilitated_lord_drops_bhavadhipati(self):
        """Mars debilitated in Cancer (sign 4)."""
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Mars": 4, "Sun": 1, "Moon": 1},
            planet_houses={"Mars": 4, "Sun": 1, "Moon": 1},
            planet_lons={"Mars": 110.0, "Sun": 10.0, "Moon": 10.0},
        )
        r = compute_bhava_bala_for(chart, 1)
        assert r.lord == "Mars"
        # 1.0 baseline - 1.0 debilitation + 0.5 kendra = 0.5
        assert r.bhavadhipati_bala < 1.0


class TestFormatting:
    def test_format_returns_string_with_all_bhavas(self):
        reports = compute_bhava_bala(_baseline_chart())
        text = format_bhava_bala(reports)
        assert "BHAVA BALA" in text
        # All 12 bhavas listed
        for b in range(1, 13):
            assert f" {b} " in text or f" {b}  " in text or f"  {b}" in text
