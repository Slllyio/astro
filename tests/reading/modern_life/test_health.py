"""Tests for modern-health detector.

Critical safety tests
=====================

- Mental-health findings must be CONTEXT, never diagnosis. Forbidden
  verdict phrases: ``will``, ``guaranteed``, ``always``, ``diagnose``,
  ``cure``.
- All findings ``classification="primitive"``.
"""
from __future__ import annotations

from app.reading.modern_life.health import detect_modern_health
from app.reading.schema import Finding


class TestDetectModernHealth:

    def test_returns_list(self, bangalore_chart, asc_sign):
        assert isinstance(detect_modern_health(bangalore_chart, asc_sign), list)

    def test_all_findings_are_primitive(self, bangalore_chart, asc_sign):
        for f in detect_modern_health(bangalore_chart, asc_sign):
            assert isinstance(f, Finding)
            assert f.classification == "primitive"

    def test_all_ids_use_modern_health_prefix(self, bangalore_chart, asc_sign):
        for f in detect_modern_health(bangalore_chart, asc_sign):
            assert f.id.startswith("modern_life.health."), f.id

    # ---- Critical safety tests ------------------------------------------------

    def test_no_outcome_predictions(self, bangalore_chart, asc_sign):
        """Health verdicts must never predict outcomes."""
        import re

        forbidden = re.compile(
            r"\b(will|guaranteed|certain|definitely|always|"
            r"diagnose[ds]?|cure[ds]?|incurable)\b",
            re.IGNORECASE,
        )
        for f in detect_modern_health(bangalore_chart, asc_sign):
            assert not forbidden.search(f.verdict), (
                f"Forbidden outcome-prediction language in {f.id}: {f.verdict!r}"
            )

    def test_mental_health_findings_disclaim_clinical(self, synthetic):
        """Anxiety/depression/dissociation findings must NOT be clinical claims.

        Detector verdicts should reference "context" / "marker" / "classical"
        wording; evidence must include ``not_clinical_diagnosis`` note.
        """
        chart = synthetic(asc_sign=1, d1_overrides={"Moon": 1, "Mercury": 1})
        findings = detect_modern_health(chart, 1)
        anx = [f for f in findings if f.id == "modern_life.health.anxiety_context"]
        assert anx, "Moon-Mercury co-location should fire anxiety_context"
        ev_blob = " ".join(anx[0].evidence)
        assert "not_clinical_diagnosis" in ev_blob

    def test_emotional_foundation_always_emits(self, bangalore_chart, asc_sign):
        """The 4H + 4L context pillar should always be surfaced."""
        ids = {f.id for f in detect_modern_health(bangalore_chart, asc_sign)}
        assert "modern_life.health.emotional_foundation" in ids

    def test_moon_nakshatra_lord_emits(self, bangalore_chart, asc_sign):
        """Moon's nakshatra-lord should be surfaced as a context pillar."""
        ids = {f.id for f in detect_modern_health(bangalore_chart, asc_sign)}
        assert "modern_life.health.moon_nakshatra_lord" in ids

    # ---- Signal-specific tests ------------------------------------------------

    def test_depression_context_on_moon_saturn(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Moon": 1, "Saturn": 1})
        findings = detect_modern_health(chart, 1)
        assert any(
            f.id == "modern_life.health.depression_context" for f in findings
        )

    def test_dissociation_context_on_moon_rahu(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Moon": 4, "Rahu": 4})
        findings = detect_modern_health(chart, 1)
        assert any(
            f.id == "modern_life.health.dissociation_context" for f in findings
        )

    def test_digestive_focus_on_mars_in_6h(self, synthetic):
        """Aries asc -> 6H = Virgo (sign 6)."""
        chart = synthetic(asc_sign=1, d1_overrides={"Mars": 6})
        findings = detect_modern_health(chart, 1)
        assert any(f.id == "modern_life.health.digestive_focus" for f in findings)

    def test_chronic_focus_on_saturn_in_8h(self, synthetic):
        """Aries asc -> 8H = Scorpio (sign 8)."""
        chart = synthetic(asc_sign=1, d1_overrides={"Saturn": 8})
        findings = detect_modern_health(chart, 1)
        assert any(f.id == "modern_life.health.chronic_focus" for f in findings)

    def test_accident_prone_on_mars_in_8h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Mars": 8})
        findings = detect_modern_health(chart, 1)
        assert any(f.id == "modern_life.health.accident_prone" for f in findings)
