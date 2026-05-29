"""Tests for app.core.gochara_engine — Phase 7 transit engine."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.gochara_engine import (
    GocharaVerdict,
    TransitState,
    compute_gochara,
    is_triggered,
)


@pytest.fixture
def bangalore_chart() -> Chart:
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


class TestDoubleTransitDetection:
    """Saturn + Jupiter both touching a bhava."""

    def test_both_in_bhava_sign_fires_dt_bhava(self, bangalore_chart):
        """Saturn and Jupiter both transiting sign 6 (= bhava 1 for Virgo Lagna)."""
        transits = {"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
                    "Jupiter": 6, "Venus": 4, "Saturn": 6,
                    "Rahu": 12, "Ketu": 6}
        v = compute_gochara(bangalore_chart, transits)
        assert v.per_bhava[1].is_double_transit_bhava

    def test_neither_in_bhava_fails_dt(self, bangalore_chart):
        """Saturn and Jupiter scattered → no DT."""
        transits = {"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
                    "Jupiter": 11, "Venus": 4, "Saturn": 3,
                    "Rahu": 12, "Ketu": 6}
        v = compute_gochara(bangalore_chart, transits)
        # Bhava 5 (sign 10 for Virgo Lagna) — Saturn aspects (3rd), but Jupiter doesn't.
        assert not v.per_bhava[5].is_double_transit_bhava


class TestSaturnPresence:
    """Saturn presence = sitting in OR aspecting."""

    def test_saturn_in_bhava_marks_present(self, bangalore_chart):
        """Saturn transiting sign 9 = bhava 4 → saturn_present in 4."""
        transits = {"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
                    "Jupiter": 6, "Venus": 4, "Saturn": 9,
                    "Rahu": 12, "Ketu": 6}
        v = compute_gochara(bangalore_chart, transits)
        assert v.per_bhava[4].saturn_present

    def test_saturn_aspect_marks_present(self, bangalore_chart):
        """Saturn in bhava 1 aspects 3rd, 7th, 10th → present in those."""
        transits = {"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
                    "Jupiter": 11, "Venus": 4, "Saturn": 6,  # sign 6 = bhava 1
                    "Rahu": 12, "Ketu": 6}
        v = compute_gochara(bangalore_chart, transits)
        assert v.per_bhava[3].saturn_present
        assert v.per_bhava[7].saturn_present
        assert v.per_bhava[10].saturn_present


class TestSadeSati:
    """Saturn in 12th/1st/2nd from natal Moon."""

    def test_sade_sati_fires_with_saturn_on_moon(self, bangalore_chart):
        """Moon at sign 12. Saturn at sign 12 → 1st from Moon → Sade Sati."""
        transits = {"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
                    "Jupiter": 6, "Venus": 4, "Saturn": 12,
                    "Rahu": 12, "Ketu": 6}
        v = compute_gochara(bangalore_chart, transits)
        assert v.sade_sati_active

    def test_sade_sati_inactive_when_saturn_distant(self, bangalore_chart):
        """Saturn at sign 4 from Moon sign 12 = 5th house → not Sade Sati."""
        transits = {"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
                    "Jupiter": 6, "Venus": 4, "Saturn": 4,
                    "Rahu": 12, "Ketu": 6}
        v = compute_gochara(bangalore_chart, transits)
        assert not v.sade_sati_active


class TestSthiraVedha:
    """Chart-level Saturn vedha cancellation."""

    def test_vedha_fires_when_mars_blocks_saturn_3rd(self):
        """Saturn 3rd from Moon AND Mars in 12th from Moon → vedha cancels."""
        ch = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Sun": 1, "Moon": 1, "Mars": 1, "Mercury": 1,
                          "Jupiter": 1, "Venus": 1, "Saturn": 1,
                          "Rahu": 1, "Ketu": 7},
            planet_houses={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                          "Jupiter", "Venus", "Saturn"]},
            planet_lons={p: 0.0 for p in ["Sun", "Moon", "Mars", "Mercury",
                                          "Jupiter", "Venus", "Saturn",
                                          "Rahu", "Ketu"]},
        )
        # Moon at sign 1. Saturn at sign 3 (3rd from Moon). Mars at sign 12 (12th from Moon).
        transits = {"Sun": 2, "Moon": 4, "Mars": 12, "Mercury": 5,
                    "Jupiter": 7, "Venus": 6, "Saturn": 3,
                    "Rahu": 8, "Ketu": 2}
        v = compute_gochara(ch, transits)
        assert v.saturn_from_moon == 3
        assert v.saturn_vedha_cancelled

    def test_vedha_inactive_when_saturn_outside_3_6_11(self, bangalore_chart):
        """Saturn at 7H from Moon → not a vedha-eligible position."""
        transits = {"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
                    "Jupiter": 6, "Venus": 4, "Saturn": 6,
                    "Rahu": 12, "Ketu": 6}
        v = compute_gochara(bangalore_chart, transits)
        # Saturn at sign 6, Moon at sign 12 → distance 7.
        assert v.saturn_from_moon == 7
        assert not v.saturn_vedha_cancelled


class TestTrigger:
    """is_triggered convenience boolean."""

    def test_triggered_when_any_dt_flag_fires(self, bangalore_chart):
        """At least one of DT_bhava / DT_lord / DT_karaka → triggered."""
        transits = {"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
                    "Jupiter": 6, "Venus": 4, "Saturn": 6,
                    "Rahu": 12, "Ketu": 6}
        v = compute_gochara(bangalore_chart, transits)
        for b in v.active_double_transit_bhavas:
            assert is_triggered(v, b)


class TestStructure:
    """Verdict-object integrity."""

    def test_per_bhava_covers_all_12(self, bangalore_chart):
        """Verdict has TransitState for every bhava 1..12."""
        transits = {p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                    "Jupiter", "Venus", "Saturn",
                                    "Rahu", "Ketu"]}
        v = compute_gochara(bangalore_chart, transits)
        assert set(v.per_bhava.keys()) == set(range(1, 13))
        for ts in v.per_bhava.values():
            assert isinstance(ts, TransitState)

    def test_transit_state_is_frozen(self, bangalore_chart):
        """TransitState is frozen — prevents downstream mutation."""
        transits = {p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                    "Jupiter", "Venus", "Saturn"]}
        v = compute_gochara(bangalore_chart, transits)
        with pytest.raises(Exception):  # FrozenInstanceError
            v.per_bhava[1].saturn_present = True  # type: ignore[misc]
