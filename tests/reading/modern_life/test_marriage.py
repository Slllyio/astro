"""Tests for modern-marriage detector.

Critical safety tests
=====================

- Mental-health and identity-fluidity findings must use
  ``classification="primitive"`` (advisory, not predictive).
- Queer / non-binary findings must carry the
  ``mainstream_practice_reads_partnership_gender_agnostically``
  disclaimer in their ``evidence`` list.
- No verdict text may contain predictive outcome language ("will",
  "guaranteed", etc.).
"""
from __future__ import annotations

from app.reading.modern_life.marriage import detect_modern_marriage
from app.reading.schema import Finding


class TestDetectModernMarriage:

    def test_returns_list(self, bangalore_chart, asc_sign):
        assert isinstance(detect_modern_marriage(bangalore_chart, asc_sign), list)

    def test_all_findings_are_primitive(self, bangalore_chart, asc_sign):
        for f in detect_modern_marriage(bangalore_chart, asc_sign):
            assert isinstance(f, Finding)
            assert f.classification == "primitive"

    def test_all_ids_use_modern_marriage_prefix(self, bangalore_chart, asc_sign):
        for f in detect_modern_marriage(bangalore_chart, asc_sign):
            assert f.id.startswith("modern_life.marriage."), f.id

    def test_rejects_invalid_asc_sign(self, bangalore_chart):
        import pytest
        with pytest.raises(ValueError):
            detect_modern_marriage(bangalore_chart, 13)

    # ---- Critical safety tests ------------------------------------------------

    def test_mental_health_findings_marked_advisory(
        self, bangalore_chart, asc_sign
    ):
        """All findings must be primitive (advisory), never trigger/promise."""
        for f in detect_modern_marriage(bangalore_chart, asc_sign):
            assert f.classification == "primitive", (
                f"{f.id} must be classification=primitive, "
                f"got {f.classification!r} (advisory not predictive)"
            )

    def test_queer_finding_carries_gender_agnostic_disclaimer(self, synthetic):
        """Identity-fluidity findings MUST surface mainstream disclaimer.

        Synthesise Mercury in Libra (sign 7) + Venus in Gemini (sign 3)
        -> Mercury-Venus mutual reception.
        """
        chart = synthetic(
            asc_sign=1,
            d1_overrides={"Mercury": 7, "Venus": 3},
        )
        findings = detect_modern_marriage(chart, 1)
        flu = [f for f in findings if f.id == "modern_life.marriage.identity_fluidity"]
        assert flu, "identity_fluidity finding did not fire on Mercury-Venus exchange"
        evidence_blob = " ".join(flu[0].evidence)
        assert (
            "mainstream_practice_reads_partnership_gender_agnostically"
            in evidence_blob
        ), (
            "identity_fluidity finding MUST carry the gender-agnostic "
            "disclaimer in evidence — got: " + evidence_blob
        )

    def test_no_outcome_prediction_language(self, bangalore_chart, asc_sign):
        import re
        forbidden = re.compile(
            r"\b(will|guaranteed|certain|definitely|always|never)\b",
            re.IGNORECASE,
        )
        for f in detect_modern_marriage(bangalore_chart, asc_sign):
            assert not forbidden.search(f.verdict), (
                f"Forbidden prediction language in {f.id}: {f.verdict!r}"
            )

    # ---- Signal-specific tests ------------------------------------------------

    def test_late_marriage_fires_on_saturn_in_7h(self, synthetic):
        """Aries asc -> 7H = Libra (sign 7). Saturn in Libra is exalted +
        in 7H -> late_marriage."""
        chart = synthetic(asc_sign=1, d1_overrides={"Saturn": 7})
        findings = detect_modern_marriage(chart, 1)
        assert any(
            f.id == "modern_life.marriage.late_marriage" for f in findings
        )

    def test_love_marriage_fires_on_venus_mars_conjunction(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Venus": 5, "Mars": 5})
        findings = detect_modern_marriage(chart, 1)
        assert any(f.id == "modern_life.marriage.love_marriage" for f in findings)

    def test_divorce_risk_fires_on_mars_in_7h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Mars": 7})
        findings = detect_modern_marriage(chart, 1)
        assert any(f.id == "modern_life.marriage.divorce_risk" for f in findings)

    def test_long_distance_fires_on_rahu_in_7h(self, synthetic):
        chart = synthetic(asc_sign=1, d1_overrides={"Rahu": 7})
        findings = detect_modern_marriage(chart, 1)
        assert any(
            f.id == "modern_life.marriage.long_distance_partner" for f in findings
        )
