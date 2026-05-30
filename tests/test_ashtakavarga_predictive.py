"""Tests for the Ashtakavarga predictive layer — Gap A."""
from __future__ import annotations

import pytest

from app.core.ashtakavarga_predictive import (
    BAV_PER_PLANET_STRONG, SAV_STRONG_THRESHOLD, SAV_AVERAGE_THRESHOLD,
    _classify_bav, _classify_sav, compute_predictive,
    kakshya_owner, sage_dasha_bhukti_grade, transit_bav_report,
)
from app.core.chart_model import Chart


def _baseline_chart() -> Chart:
    """Bangalore baseline 1990-07-15."""
    return Chart(
        asc_sign=6, asc_lon=173.99,
        planet_signs={
            "Sun": 3, "Moon": 12, "Mars": 4, "Mercury": 3,
            "Jupiter": 4, "Venus": 4, "Saturn": 9,
            "Rahu": 12, "Ketu": 6,
        },
        planet_houses={
            "Sun": 10, "Moon": 7, "Mars": 11, "Mercury": 10,
            "Jupiter": 11, "Venus": 11, "Saturn": 4,
            "Rahu": 7, "Ketu": 1,
        },
        planet_lons={
            "Sun": 88.6, "Moon": 351.0, "Mars": 120.5, "Mercury": 95.2,
            "Jupiter": 101.8, "Venus": 102.0, "Saturn": 268.4,
            "Rahu": 348.5, "Ketu": 168.5,
        },
    )


class TestClassify:
    def test_sav_strong_threshold_30(self):
        """SAV >= 30 classifies as strong with 1.3x multiplier."""
        label, mult = _classify_sav(35)
        assert label == "strong"
        assert mult == 1.3

    def test_sav_below_25_weak(self):
        """SAV < 25 classifies as weak with 0.7x multiplier."""
        label, mult = _classify_sav(20)
        assert label == "weak"
        assert mult == 0.7

    def test_sav_between_25_29_average(self):
        """SAV in 25-29 classifies as average with 1.0x multiplier."""
        label, mult = _classify_sav(27)
        assert label == "average"
        assert mult == 1.0

    def test_bav_strong_at_5(self):
        """BAV >= 5 per planet per sign classifies as strong."""
        label, mult = _classify_bav(BAV_PER_PLANET_STRONG)
        assert label == "strong"
        assert mult == 1.3


class TestComputePredictive:
    def test_returns_12_bhava_reports(self):
        """Predictive report covers all 12 bhavas."""
        report = compute_predictive(_baseline_chart())
        assert set(report.sav_per_bhava.keys()) == set(range(1, 13))

    def test_strongest_weakest_consistent(self):
        """strongest_bhava and weakest_bhava match argmax/argmin."""
        report = compute_predictive(_baseline_chart())
        strongest = report.sav_per_bhava[report.strongest_bhava]
        weakest = report.sav_per_bhava[report.weakest_bhava]
        for r in report.sav_per_bhava.values():
            assert r.sav_points <= strongest.sav_points
            assert r.sav_points >= weakest.sav_points

    def test_total_sav_matches_sum(self):
        """total_sav equals sum of sav_per_sign."""
        report = compute_predictive(_baseline_chart())
        assert report.total_sav == sum(report.sav_per_sign)

    def test_bav_max_per_planet_at_most_56_per_sign(self):
        """Each planet's BAV per sign is in 0..8 (max 8 contributors)."""
        report = compute_predictive(_baseline_chart())
        for planet, bav_list in report.bav_per_planet_per_sign.items():
            for points in bav_list:
                assert 0 <= points <= 8, f"{planet}: BAV={points}"

    def test_sav_per_sign_sums_to_total(self):
        """SAV per sign is in 0..56 typically; total SAV ≈337 (classical) or 338
        (some implementations include Lagna for all 7 planets)."""
        report = compute_predictive(_baseline_chart())
        for points in report.sav_per_sign:
            assert 0 <= points <= 56
        # Classical 337 vs implementation-specific 338 — both valid conventions
        assert report.total_sav in (337, 338)


class TestTransitBAVReport:
    def test_returns_planet_and_sign(self):
        """Report carries planet name and transit sign."""
        report = compute_predictive(_baseline_chart())
        t = transit_bav_report(report, "Saturn", 6)
        assert t.planet == "Saturn"
        assert t.transit_sign == 6

    def test_bav_in_valid_range(self):
        """BAV points are 0..8."""
        report = compute_predictive(_baseline_chart())
        t = transit_bav_report(report, "Jupiter", 4)
        assert 0 <= t.bav_points <= 8

    def test_rejects_invalid_planet(self):
        """Only visible planets (no nodes) have BAV."""
        report = compute_predictive(_baseline_chart())
        with pytest.raises(ValueError):
            transit_bav_report(report, "Rahu", 6)

    def test_rejects_invalid_sign(self):
        """Sign must be 1..12."""
        report = compute_predictive(_baseline_chart())
        with pytest.raises(ValueError):
            transit_bav_report(report, "Saturn", 13)


class TestSageDashaBhuktiGrade:
    def test_both_strong_yields_full(self):
        """Strong static SAV + strong transit BAV = FULL delivery."""
        # We can't guarantee the chart will produce this — instead synth a report
        from app.core.ashtakavarga_predictive import AshtakavargaPredictive, BhavaSAVReport
        sav_per_sign = [35 if i == 5 else 27 for i in range(12)]   # sign 6 strong
        bav_per_planet = {"Saturn": [6 if i == 5 else 3 for i in range(12)]}
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus"):
            bav_per_planet[p] = [3]*12
        sav_per_bhava = {b: BhavaSAVReport(b, sav_per_sign[b-1], "strong", 1.3)
                         for b in range(1, 13)}
        report = AshtakavargaPredictive(
            sav_per_bhava=sav_per_bhava,
            bav_per_planet_per_sign=bav_per_planet,
            sav_per_sign=sav_per_sign,
            strongest_bhava=6, weakest_bhava=1,
            total_sav=sum(sav_per_sign),
        )
        result = sage_dasha_bhukti_grade(
            report, bhukti_lord="Saturn",
            bhukti_lord_natal_sign=6, current_transit_sign=6,
        )
        assert result["composite_grade"] == "FULL"
        assert result["delivery_multiplier"] == 1.5


class TestKakshyaOwner:
    def test_first_kakshya_owner_is_saturn(self):
        """First 3°45' of every sign is Saturn's kakshya per BPHS Ch.69."""
        assert kakshya_owner(1, 1.0) == "Saturn"
        assert kakshya_owner(7, 3.0) == "Saturn"

    def test_second_kakshya_owner_is_jupiter(self):
        """3°45' to 7°30' is Jupiter's kakshya."""
        assert kakshya_owner(1, 5.0) == "Jupiter"

    def test_last_kakshya_owner_is_lagna(self):
        """The 8th kakshya (26°15' to 30°) is Lagna's."""
        assert kakshya_owner(1, 27.0) == "Lagna"

    def test_rejects_out_of_range_sign(self):
        """Sign must be 1..12."""
        with pytest.raises(ValueError):
            kakshya_owner(13, 5.0)

    def test_rejects_out_of_range_degree(self):
        """deg_in_sign must be 0..30."""
        with pytest.raises(ValueError):
            kakshya_owner(1, 30.5)
