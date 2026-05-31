"""Tests for app.core.bphs_pattern_library — L-3 classical-pattern lookup."""
from __future__ import annotations

import pytest

from app.core.bphs_pattern_library import (
    PatternVerdict, detect_all_patterns, patterns_for_domain,
    pattern_jupiter_in_2h_own_sign, pattern_jupiter_in_5h,
    pattern_jupiter_in_7h_benefic_aspect, pattern_jupiter_in_9h,
    pattern_marital_discord_mars_7h_sat_aspect, pattern_sun_in_10h_own_sign,
    registry_size,
)
from app.core.chart_model import Chart


class TestRegistry:
    def test_registry_size_is_15(self):
        """L-3 ships 15 BPHS-derived patterns across 6 domains."""
        assert registry_size() == 15

    def test_detect_all_returns_only_matches(self):
        """detect_all_patterns returns only fired patterns — never None entries."""
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Sun": 1, "Moon": 5, "Mars": 7, "Mercury": 10,
                          "Jupiter": 11, "Venus": 2, "Saturn": 4,
                          "Rahu": 6, "Ketu": 12},
            planet_houses={"Sun": 1, "Moon": 5, "Mars": 7, "Mercury": 10,
                           "Jupiter": 11, "Venus": 2, "Saturn": 4,
                           "Rahu": 6, "Ketu": 12},
            planet_lons={p: (h - 1) * 30.0 + 15.0 for p, h in (
                ("Sun", 1), ("Moon", 5), ("Mars", 7), ("Mercury", 10),
                ("Jupiter", 11), ("Venus", 2), ("Saturn", 4),
                ("Rahu", 6), ("Ketu", 12),
            )},
        )
        results = detect_all_patterns(chart)
        for v in results:
            assert isinstance(v, PatternVerdict)


class TestMarriagePatterns:
    def test_mars_7h_saturn_aspect_fires(self):
        """Mars in 7H + Saturn aspecting 7H (from 1H opposition) → afflicting."""
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Mars": 7, "Saturn": 1, "Sun": 5,
                          "Moon": 5, "Mercury": 5, "Jupiter": 5, "Venus": 5},
            planet_houses={"Mars": 7, "Saturn": 1, "Sun": 5,
                           "Moon": 5, "Mercury": 5, "Jupiter": 5, "Venus": 5},
            planet_lons={"Mars": 190.0, "Saturn": 10.0, "Sun": 130.0,
                         "Moon": 130.0, "Mercury": 130.0, "Jupiter": 130.0,
                         "Venus": 130.0},
        )
        v = pattern_marital_discord_mars_7h_sat_aspect(chart)
        assert v is not None
        assert v.domain == "marriage"
        assert v.polarity == "afflicting"

    def test_jupiter_7h_with_benefic_aspect_fires(self):
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Jupiter": 7, "Venus": 1, "Sun": 4, "Moon": 5,
                          "Mars": 8, "Mercury": 9, "Saturn": 11},
            planet_houses={"Jupiter": 7, "Venus": 1, "Sun": 4, "Moon": 5,
                           "Mars": 8, "Mercury": 9, "Saturn": 11},
            planet_lons={"Jupiter": 190.0, "Venus": 10.0, "Sun": 100.0,
                         "Moon": 130.0, "Mars": 220.0, "Mercury": 250.0,
                         "Saturn": 310.0},
        )
        v = pattern_jupiter_in_7h_benefic_aspect(chart)
        assert v is not None
        assert v.polarity == "supportive"


class TestWealthPatterns:
    def test_jupiter_2h_own_sign_fires(self):
        """Jupiter in 2H in own sign — needs Aquarius Lagna so 2H = Pisces."""
        chart = Chart(
            asc_sign=11, asc_lon=310.0,
            planet_signs={"Jupiter": 12, "Sun": 1, "Moon": 2, "Mars": 3,
                          "Mercury": 4, "Venus": 5, "Saturn": 8},
            planet_houses={"Jupiter": 2, "Sun": 3, "Moon": 4, "Mars": 5,
                           "Mercury": 6, "Venus": 7, "Saturn": 10},
            planet_lons={"Jupiter": 340.0, "Sun": 10.0, "Moon": 40.0,
                         "Mars": 70.0, "Mercury": 100.0, "Venus": 130.0,
                         "Saturn": 220.0},
        )
        v = pattern_jupiter_in_2h_own_sign(chart)
        assert v is not None
        assert v.domain == "wealth"
        assert v.polarity == "supportive"


class TestCareerPatterns:
    def test_sun_10h_leo_fires(self):
        """Sun in 10H in Leo from Scorpio Lagna."""
        chart = Chart(
            asc_sign=8, asc_lon=220.0,
            planet_signs={"Sun": 5, "Moon": 1, "Mars": 2, "Mercury": 4,
                          "Jupiter": 6, "Venus": 7, "Saturn": 11},
            planet_houses={"Sun": 10, "Moon": 6, "Mars": 7, "Mercury": 9,
                           "Jupiter": 11, "Venus": 12, "Saturn": 4},
            planet_lons={"Sun": 130.0, "Moon": 10.0, "Mars": 40.0,
                         "Mercury": 100.0, "Jupiter": 160.0, "Venus": 190.0,
                         "Saturn": 310.0},
        )
        v = pattern_sun_in_10h_own_sign(chart)
        assert v is not None
        assert v.severity >= 0.85


class TestDharmaPatterns:
    def test_jupiter_9h_supports_dharma(self):
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Jupiter": 9, "Sun": 1, "Moon": 2, "Mars": 3,
                          "Mercury": 4, "Venus": 5, "Saturn": 7},
            planet_houses={"Jupiter": 9, "Sun": 1, "Moon": 2, "Mars": 3,
                           "Mercury": 4, "Venus": 5, "Saturn": 7},
            planet_lons={"Jupiter": 250.0, "Sun": 10.0, "Moon": 40.0,
                         "Mars": 70.0, "Mercury": 100.0, "Venus": 130.0,
                         "Saturn": 190.0},
        )
        v = pattern_jupiter_in_9h(chart)
        assert v is not None
        assert v.domain == "dharma"
        assert v.polarity == "supportive"


class TestChildrenPatterns:
    def test_jupiter_5h_fires_for_progeny(self):
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Jupiter": 5, "Sun": 1, "Moon": 2, "Mars": 3,
                          "Mercury": 4, "Venus": 6, "Saturn": 8},
            planet_houses={"Jupiter": 5, "Sun": 1, "Moon": 2, "Mars": 3,
                           "Mercury": 4, "Venus": 6, "Saturn": 8},
            planet_lons={"Jupiter": 130.0, "Sun": 10.0, "Moon": 40.0,
                         "Mars": 70.0, "Mercury": 100.0, "Venus": 160.0,
                         "Saturn": 220.0},
        )
        v = pattern_jupiter_in_5h(chart)
        assert v is not None
        assert v.domain == "children"


class TestPerDomainQuery:
    def test_marriage_filter(self):
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Jupiter": 7, "Venus": 1, "Sun": 4, "Moon": 5,
                          "Mars": 8, "Mercury": 9, "Saturn": 11},
            planet_houses={"Jupiter": 7, "Venus": 1, "Sun": 4, "Moon": 5,
                           "Mars": 8, "Mercury": 9, "Saturn": 11},
            planet_lons={"Jupiter": 190.0, "Venus": 10.0, "Sun": 100.0,
                         "Moon": 130.0, "Mars": 220.0, "Mercury": 250.0,
                         "Saturn": 310.0},
        )
        marriage_patterns = patterns_for_domain(chart, "marriage")
        for v in marriage_patterns:
            assert v.domain == "marriage"
