"""Tests for modern-children detector.

Includes IVF/ART and adoption signals — important: classification must
remain ``primitive`` so the medical/lifestyle implications are advisory.
"""
from __future__ import annotations

from app.reading.modern_life.children import detect_modern_children
from app.reading.schema import Finding


class TestDetectModernChildren:

    def test_returns_list(self, bangalore_chart, asc_sign):
        assert isinstance(detect_modern_children(bangalore_chart, asc_sign), list)

    def test_all_findings_are_primitive(self, bangalore_chart, asc_sign):
        for f in detect_modern_children(bangalore_chart, asc_sign):
            assert isinstance(f, Finding)
            assert f.classification == "primitive"

    def test_all_ids_use_modern_children_prefix(self, bangalore_chart, asc_sign):
        for f in detect_modern_children(bangalore_chart, asc_sign):
            assert f.id.startswith("modern_life.children."), f.id

    def test_no_outcome_prediction_language(self, bangalore_chart, asc_sign):
        import re
        forbidden = re.compile(
            r"\b(will|guaranteed|certain|definitely|always|impossible)\b",
            re.IGNORECASE,
        )
        for f in detect_modern_children(bangalore_chart, asc_sign):
            assert not forbidden.search(f.verdict), (
                f"Forbidden prediction language in {f.id}: {f.verdict!r}"
            )

    def test_ivf_art_context_fires_on_rahu_in_5h(self, synthetic):
        """Aries asc -> 5H = Leo (sign 5)."""
        chart = synthetic(asc_sign=1, d1_overrides={"Rahu": 5})
        findings = detect_modern_children(chart, 1)
        assert any(f.id == "modern_life.children.ivf_art_context" for f in findings)

    def test_adoption_context_fires_on_ketu_in_5h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Ketu": 5})
        findings = detect_modern_children(chart, 1)
        assert any(f.id == "modern_life.children.adoption_context" for f in findings)

    def test_delay_context_fires_on_saturn_in_5h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Saturn": 5})
        findings = detect_modern_children(chart, 1)
        assert any(f.id == "modern_life.children.delay_context" for f in findings)

    def test_conception_difficulty_on_mars_saturn_on_5h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Mars": 5, "Saturn": 5})
        findings = detect_modern_children(chart, 1)
        assert any(
            f.id == "modern_life.children.conception_difficulty" for f in findings
        )

    def test_ivf_evidence_has_advisory_note(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Rahu": 5})
        findings = detect_modern_children(chart, 1)
        ivf = [f for f in findings if f.id == "modern_life.children.ivf_art_context"]
        ev = " ".join(ivf[0].evidence)
        assert "medical_intervention_path_advisory" in ev
