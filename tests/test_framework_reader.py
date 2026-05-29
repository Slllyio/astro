"""Tests for app.medini.services.framework_reader — the bridge layer."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.reading_composer import Reading
from app.medini.services.framework_reader import (
    _to_framework_chart,
    read_chart_via_framework,
    reading_to_dict,
)


@pytest.fixture
def chart_dict() -> dict:
    """Minimal calculate_all_charts-shaped dict for tests."""
    return {
        "ascendant": {"longitude": 173.99, "sign": 6,
                      "sign_name": "Virgo", "degree_in_sign": 23.99},
        "d1": {
            "Sun": {"longitude": 88.6, "sign": 3, "house": 10,
                    "is_retrograde": False},
            "Moon": {"longitude": 351.0, "sign": 12, "house": 7,
                     "is_retrograde": False},
            "Mars": {"longitude": 120.5, "sign": 4, "house": 11,
                     "is_retrograde": False},
            "Mercury": {"longitude": 95.2, "sign": 3, "house": 10,
                        "is_retrograde": False},
            "Jupiter": {"longitude": 101.8, "sign": 4, "house": 11,
                        "is_retrograde": False},
            "Venus": {"longitude": 102.0, "sign": 4, "house": 11,
                      "is_retrograde": False},
            "Saturn": {"longitude": 268.4, "sign": 9, "house": 4,
                       "is_retrograde": False},
            "Rahu": {"longitude": 348.5, "sign": 12, "house": 7,
                     "is_retrograde": True},
            "Ketu": {"longitude": 168.5, "sign": 6, "house": 1,
                     "is_retrograde": True},
        },
        "birth_jd": 2448087.5,
        "current_mahadasha": {"lord": "Mercury", "elapsed_years": 5.0},
    }


class TestToFrameworkChart:
    """Conversion from ephemeris dict to framework Chart."""

    def test_extracts_lagna(self, chart_dict):
        """ascendant.sign + ascendant.longitude land in Chart."""
        ch = _to_framework_chart(chart_dict)
        assert ch.asc_sign == 6
        assert ch.asc_lon == pytest.approx(173.99)

    def test_extracts_all_9_planets(self, chart_dict):
        """All 9 grahas appear in planet_signs/houses/lons."""
        ch = _to_framework_chart(chart_dict)
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                    "Venus", "Saturn", "Rahu", "Ketu"}
        assert set(ch.planet_signs) == expected
        assert set(ch.planet_houses) == expected
        assert set(ch.planet_lons) == expected

    def test_preserves_retrograde_flags(self, chart_dict):
        """is_retrograde flows through; Rahu/Ketu True, visible False."""
        ch = _to_framework_chart(chart_dict)
        assert ch.planet_retrograde["Rahu"] is True
        assert ch.planet_retrograde["Sun"] is False

    def test_rejects_missing_required_keys(self):
        """Missing 'ascendant' or 'd1' → ValueError."""
        with pytest.raises(ValueError):
            _to_framework_chart({})


class TestReadChartViaFramework:
    """End-to-end bridge call."""

    def test_returns_framework_reading(self, chart_dict):
        """Output type matches app.core.reading_composer.Reading."""
        r = read_chart_via_framework(chart_dict)
        assert isinstance(r, Reading)

    def test_picks_md_lord_from_current_mahadasha(self, chart_dict):
        """vimshottari_md_at_target sourced from chart_dict.current_mahadasha."""
        r = read_chart_via_framework(chart_dict)
        assert r.vimshottari_md_at_target == "Mercury"

    def test_person_id_propagates(self, chart_dict):
        """Caller-supplied person_id appears on the Reading."""
        r = read_chart_via_framework(chart_dict, person_id="bangalore-baseline")
        assert r.person_id == "bangalore-baseline"


class TestReadingToDict:
    """Serialisation for HTTP response."""

    def test_returns_dict(self, chart_dict):
        """Public type: dict[str, Any] suitable for JSON."""
        r = read_chart_via_framework(chart_dict)
        d = reading_to_dict(r)
        assert isinstance(d, dict)

    def test_covers_all_12_bhavas(self, chart_dict):
        """bhava_claims is a dict keyed by '1'..'12' as strings."""
        r = read_chart_via_framework(chart_dict)
        d = reading_to_dict(r)
        assert set(d["bhava_claims"].keys()) == {str(b) for b in range(1, 13)}

    def test_each_claim_has_verdict_label(self, chart_dict):
        """Per-bhava entries carry the verdict label."""
        r = read_chart_via_framework(chart_dict)
        d = reading_to_dict(r)
        for b_str, claim in d["bhava_claims"].items():
            assert claim["verdict_label"] in {"strong", "medium",
                                              "weak", "afflicted"}

    def test_includes_rendered_text(self, chart_dict):
        """rendered_text gives a plain-text view for quick display."""
        r = read_chart_via_framework(chart_dict)
        d = reading_to_dict(r)
        assert "ASTROLOGER-LENS READING" in d["rendered_text"]

    def test_active_yogas_include_classical_ref(self, chart_dict):
        """Each active yoga entry has a `reference` (BPHS Ch. X)."""
        r = read_chart_via_framework(chart_dict)
        d = reading_to_dict(r)
        for y in d["active_yogas"]:
            assert "Ch" in y["reference"] or y["reference"]
