"""Tests for modern-career detector.

Doctrine note: every emitted Finding must use ``classification="primitive"``
(advisory, not predictive).
"""
from __future__ import annotations

from app.reading.modern_life.career import detect_modern_career
from app.reading.schema import Finding


class TestDetectModernCareer:
    """Structural and signal-specific checks for the career detector."""

    def test_returns_list(self, bangalore_chart, asc_sign):
        result = detect_modern_career(bangalore_chart, asc_sign)
        assert isinstance(result, list)

    def test_all_findings_are_primitive(self, bangalore_chart, asc_sign):
        for f in detect_modern_career(bangalore_chart, asc_sign):
            assert isinstance(f, Finding)
            assert f.classification == "primitive"

    def test_all_finding_ids_use_modern_career_prefix(
        self, bangalore_chart, asc_sign
    ):
        for f in detect_modern_career(bangalore_chart, asc_sign):
            assert f.id.startswith("modern_life.career."), f.id

    def test_rejects_invalid_asc_sign(self, bangalore_chart):
        import pytest

        with pytest.raises(ValueError):
            detect_modern_career(bangalore_chart, 0)
        with pytest.raises(ValueError):
            detect_modern_career(bangalore_chart, 13)

    def test_software_it_fires_on_synthetic_tech_triad(self, synthetic):
        """Rahu+Mercury+Saturn all in 10H of D1 should fire the IT signal."""
        # asc_sign=1 (Aries) -> 10H is Capricorn (sign=10)
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Rahu": 10, "Mercury": 10, "Saturn": 10},
        )
        findings = detect_modern_career(chart, 1)
        ids = {f.id for f in findings}
        assert "modern_life.career.software_it" in ids

    def test_social_media_fires_on_rahu_in_3h(self, synthetic):
        """Aries asc -> 3H = Gemini (sign 3)."""
        chart = synthetic(asc_sign=1, d1_overrides={"Rahu": 3})
        findings = detect_modern_career(chart, 1)
        ids = {f.id for f in findings}
        assert "modern_life.career.social_media" in ids

    def test_social_media_fires_on_rahu_in_11h(self, synthetic):
        """Aries asc -> 11H = Aquarius (sign 11)."""
        chart = synthetic(asc_sign=1, d1_overrides={"Rahu": 11})
        findings = detect_modern_career(chart, 1)
        ids = {f.id for f in findings}
        assert "modern_life.career.social_media" in ids

    def test_government_fires_on_sun_saturn_in_10h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Sun": 10, "Saturn": 10})
        findings = detect_modern_career(chart, 1)
        ids = {f.id for f in findings}
        assert "modern_life.career.government" in ids

    def test_consulting_fires_on_jupiter_mercury_in_9h(self, synthetic):
        """Aries asc -> 9H = Sagittarius (sign 9)."""
        chart = synthetic(asc_sign=1, d1_overrides={"Jupiter": 9, "Mercury": 9})
        findings = detect_modern_career(chart, 1)
        ids = {f.id for f in findings}
        assert "modern_life.career.consulting" in ids

    def test_entrepreneur_fires_on_mars_saturn_conjunction(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Mars": 5, "Saturn": 5})
        findings = detect_modern_career(chart, 1)
        ids = {f.id for f in findings}
        assert "modern_life.career.entrepreneur" in ids

    def test_no_outcome_prediction_language(self, bangalore_chart, asc_sign):
        """Career findings must not predict outcomes."""
        import re

        forbidden = re.compile(
            r"\b(will|guaranteed|certain|definitely|always)\b",
            re.IGNORECASE,
        )
        for f in detect_modern_career(bangalore_chart, asc_sign):
            assert not forbidden.search(f.verdict), (
                f"Forbidden prediction language in {f.id}: {f.verdict!r}"
            )
