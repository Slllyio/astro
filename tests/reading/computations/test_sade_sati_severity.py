"""Tests for ``app.reading.computations.sade_sati_severity``.

Doctrine source: Classical Parashari Sade Sati definition (Saturn in
12th/1st/2nd from natal Moon) layered with Sarvashtakavarga bindu
modulation per K.N. Rao (*Predicting Through Jaimini Chara Dasa* and
related works) and Sanjay Rath's *Vedic Remedies in Astrology* (Saturn
remedies section).

Algorithm
=========

1. Determine the current Sade Sati phase via ``app.core.sade_sati.is_in_sade_sati``.
2. If not in Sade Sati: emit a neutral "no Sade Sati" Finding.
3. If in Sade Sati: compute Sarvashtakavarga (SAV) for the rashi
   currently hosting transit Saturn, then apply the severity matrix:

   | Condition                                          | Severity |
   |----------------------------------------------------|----------|
   | SAV >= 30 AND natal Saturn is functional benefic   | mild     |
   | SAV >= 30 AND natal Saturn is NOT benefic          | moderate |
   | 25 <= SAV < 30                                     | moderate |
   | SAV < 25 AND phase == PEAK                         | severe   |
   | SAV < 25 AND phase != PEAK                         | moderate |
"""
from __future__ import annotations

import pytest


def _planet(sign: int, *, longitude: float | None = None) -> dict:
    lon = longitude if longitude is not None else (sign - 1) * 30.0 + 15.0
    return {
        "sign": sign,
        "longitude": lon,
        "degree_in_sign": lon % 30.0,
    }


def _build_chart(moon_sign: int, saturn_sign: int) -> dict:
    """Build a chart with the 7 BAV planets in distinct signs for SAV
    computation. Moon and Saturn at the requested signs; the other 5
    planets at varied signs to produce a plausible SAV vector."""
    placements = {
        "Sun":     1,
        "Mars":    3,
        "Mercury": 4,
        "Jupiter": 5,
        "Venus":   6,
    }
    placements["Moon"] = moon_sign
    placements["Saturn"] = saturn_sign
    chart = {}
    for name, sign in placements.items():
        chart[name] = _planet(sign)
    # Add Rahu/Ketu (not used by ashtakavarga but present in real charts).
    chart["Rahu"] = _planet(8)
    chart["Ketu"] = _planet(2)
    return chart


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestShape:

    def test_returns_finding(self):
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )
        from app.reading.schema import Finding

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=3,  # 12 from Moon = Rising
        )
        assert isinstance(finding, Finding)


# ---------------------------------------------------------------------------
# Not-in-Sade-Sati branch.
# ---------------------------------------------------------------------------


class TestNotInSadeSati:

    def test_neutral_finding_when_not_active(self):
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        # Saturn in sign 6 — that's 3rd from natal Moon (Cancer=4),
        # which is OUTSIDE the 12/1/2 from Moon window.
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=6,
        )
        assert finding.direction == "neutral"
        verdict_lower = finding.verdict.lower()
        # The verdict should reflect "not in Sade Sati".
        assert "no" in verdict_lower or "not" in verdict_lower or "inactive" in verdict_lower


# ---------------------------------------------------------------------------
# Active Sade Sati: direction is negative.
# ---------------------------------------------------------------------------


class TestActiveSadeSati:

    def test_direction_is_negative_when_active(self):
        """Moon Cancer (4), transit Saturn at Pisces (12) = 9th from Moon —
        NOT Sade Sati. We need the 12/1/2 from Moon.
        Moon = 4. 12th from 4 = sign 3. 1st = 4. 2nd = 5.
        So transit Saturn in sign 3 (Gemini) = Rising phase."""
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=3,  # 12 from Moon
        )
        assert finding.direction == "negative"

    def test_classification_is_trigger(self):
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=4,  # PEAK
        )
        assert finding.classification == "trigger"


# ---------------------------------------------------------------------------
# Finding contract.
# ---------------------------------------------------------------------------


class TestFindingContract:

    def test_id_pin(self):
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=4,
        )
        assert finding.id == "practitioner.sade_sati.current"

    def test_verdict_under_140(self):
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=4,
        )
        assert len(finding.verdict) <= 140

    def test_evidence_records_phase(self):
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=4,  # PEAK (1st from Moon)
        )
        evidence_blob = " ".join(finding.evidence).lower()
        assert "peak" in evidence_blob

    def test_evidence_records_sav(self):
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=3,
        )
        evidence_blob = " ".join(finding.evidence).lower()
        assert "sav" in evidence_blob


# ---------------------------------------------------------------------------
# Severity matrix
# ---------------------------------------------------------------------------


class TestSeverityMatrix:

    def test_verdict_mentions_severity(self):
        """The verdict must surface one of mild/moderate/severe."""
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=4,
        )
        verdict_lower = finding.verdict.lower()
        assert any(s in verdict_lower for s in ("mild", "moderate", "severe"))


# ---------------------------------------------------------------------------
# Property: works across all transit Saturn signs.
# ---------------------------------------------------------------------------


class TestPropertyAllSaturnSigns:

    @pytest.mark.parametrize("transit_saturn_sign", list(range(1, 13)))
    def test_runs_for_every_saturn_position(self, transit_saturn_sign):
        from app.reading.computations.sade_sati_severity import (
            compute_sade_sati_severity,
        )

        chart = _build_chart(moon_sign=4, saturn_sign=10)
        finding = compute_sade_sati_severity(
            chart, asc_sign=1, transit_saturn_sign=transit_saturn_sign,
        )
        # Single Finding returned regardless of phase.
        assert finding.id == "practitioner.sade_sati.current"
