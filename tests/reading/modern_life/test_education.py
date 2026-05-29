"""Tests for modern-education detector."""
from __future__ import annotations

from app.reading.modern_life.education import detect_modern_education
from app.reading.schema import Finding


class TestDetectModernEducation:

    def test_returns_list(self, bangalore_chart, asc_sign):
        assert isinstance(detect_modern_education(bangalore_chart, asc_sign), list)

    def test_all_findings_are_primitive(self, bangalore_chart, asc_sign):
        for f in detect_modern_education(bangalore_chart, asc_sign):
            assert isinstance(f, Finding)
            assert f.classification == "primitive"

    def test_all_ids_use_modern_education_prefix(self, bangalore_chart, asc_sign):
        for f in detect_modern_education(bangalore_chart, asc_sign):
            assert f.id.startswith("modern_life.education."), f.id

    def test_online_learning_on_rahu_mercury_in_4h(self, synthetic):
        """Aries asc -> 4H = Cancer (sign 4)."""
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Rahu": 4, "Mercury": 4},
        )
        findings = detect_modern_education(chart, 1)
        assert any(
            f.id == "modern_life.education.online_remote_learning" for f in findings
        )

    def test_self_directed_on_ketu_in_5h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Ketu": 5})
        findings = detect_modern_education(chart, 1)
        assert any(
            f.id == "modern_life.education.self_directed" for f in findings
        )

    def test_self_directed_on_mars_in_4h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Mars": 4})
        findings = detect_modern_education(chart, 1)
        assert any(
            f.id == "modern_life.education.self_directed" for f in findings
        )

    def test_stem_inclination_on_mercury_saturn_in_4h(self, synthetic):
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Mercury": 4, "Saturn": 4},
        )
        findings = detect_modern_education(chart, 1)
        assert any(
            f.id == "modern_life.education.stem_inclination" for f in findings
        )

    def test_humanities_on_jupiter_venus_in_4h(self, synthetic):
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Jupiter": 4, "Venus": 4},
        )
        findings = detect_modern_education(chart, 1)
        assert any(
            f.id == "modern_life.education.humanities_inclination" for f in findings
        )

    def test_higher_education_on_jupiter_in_9h(self, synthetic):
        """Aries asc -> 9H = Sagittarius (sign 9)."""
        chart = synthetic(asc_sign=1, d1_overrides={"Jupiter": 9})
        findings = detect_modern_education(chart, 1)
        assert any(
            f.id == "modern_life.education.higher_education" for f in findings
        )

    def test_non_traditional_on_rahu_in_9h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Rahu": 9})
        findings = detect_modern_education(chart, 1)
        assert any(
            f.id == "modern_life.education.non_traditional_path" for f in findings
        )

    def test_no_outcome_prediction_language(self, bangalore_chart, asc_sign):
        import re
        forbidden = re.compile(
            r"\b(will|guaranteed|certain|definitely|always)\b",
            re.IGNORECASE,
        )
        for f in detect_modern_education(bangalore_chart, asc_sign):
            assert not forbidden.search(f.verdict), (
                f"Forbidden prediction language in {f.id}: {f.verdict!r}"
            )
