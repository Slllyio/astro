"""Tests for ``app.reading.computations.yogas_extended.kala_sarpa``.

Doctrine source: D-12 lockfile (strict 180° / Rahu-leading definition).

Classical rule (D-12 STRICT)
============================

**Kala Sarpa Yoga (KSY)**:
    All seven non-nodal planets (Su, Mo, Ma, Me, Ju, Ve, Sa) fall within
    the 180° arc bounded by Rahu (leading) and Ketu (trailing) — i.e.
    moving from Rahu's longitude forward 180° in the zodiacal direction,
    all seven planets are inside that arc.

**Kala Amrita Yoga**:
    Same configuration but with Ketu leading (planets in the 180° arc
    from Ketu forward, Rahu trailing). Often considered the more
    benign mirror.

**Loose / partial variants**:
    NOT detected per D-12 strict commitment. (One stray planet outside
    the hemisphere = no Finding. Tier-3 dispute_surfacing handles loose
    cases.)

ID grammar
==========

``practitioner.yogas_extended.kala_sarpa.ksy``        (negative)
``practitioner.yogas_extended.kala_sarpa.amrita``     (positive)

At most one Finding emitted per chart.
"""
from __future__ import annotations

import pytest


def _planet_dict(longitude: float) -> dict:
    """Build a planet record at the given absolute longitude (0..360)."""
    sign = int(longitude // 30) + 1
    return {"sign": sign, "longitude": float(longitude % 360)}


def _kala_sarpa_chart(rahu_lon: float, planet_offsets: dict[str, float]) -> dict:
    """Build a chart with Rahu at rahu_lon, Ketu opposite, and the seven
    classical planets at rahu_lon + offset (modulo 360) per planet.
    All offsets must be in (0, 180) for KSY (Rahu-leading).
    """
    ketu_lon = (rahu_lon + 180.0) % 360.0
    chart: dict[str, dict] = {
        "Rahu": _planet_dict(rahu_lon),
        "Ketu": _planet_dict(ketu_lon),
    }
    for planet, offset in planet_offsets.items():
        chart[planet] = _planet_dict((rahu_lon + offset) % 360.0)
    return chart


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestDetectKalaSarpaShape:

    def test_returns_list(self):
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = {
            p: _planet_dict(0.0)
            for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                      "Venus", "Saturn", "Rahu", "Ketu")
        }
        result = detect_kala_sarpa(chart, asc_sign=1)
        assert isinstance(result, list)

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = {
            p: _planet_dict(0.0)
            for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                      "Venus", "Saturn", "Rahu", "Ketu")
        }
        with pytest.raises(ValueError):
            detect_kala_sarpa(chart, asc_sign=0)
        with pytest.raises(ValueError):
            detect_kala_sarpa(chart, asc_sign=13)


# ---------------------------------------------------------------------------
# Kala Sarpa Yoga — strict (all 7 in Rahu-leading 180° arc)
# ---------------------------------------------------------------------------


class TestKalaSarpaYoga:

    def test_all_seven_in_rahu_leading_arc(self):
        """Rahu at 0° (Aries). All 7 planets within (0°, 180°) → KSY."""
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = _kala_sarpa_chart(
            rahu_lon=0.0,
            planet_offsets={
                "Sun":     30.0,
                "Moon":    45.0,
                "Mars":    60.0,
                "Mercury": 75.0,
                "Jupiter": 90.0,
                "Venus":  120.0,
                "Saturn": 150.0,
            },
        )
        result = detect_kala_sarpa(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.kala_sarpa.ksy"
        assert result[0].direction == "negative"
        assert result[0].classification == "yoga"

    def test_one_planet_outside_arc_no_yoga(self):
        """Saturn placed past Ketu (outside Rahu-to-Ketu forward arc) →
        breaks the strict KSY. Per D-12, no Finding (loose variant lives
        in dispute layer)."""
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = _kala_sarpa_chart(
            rahu_lon=0.0,
            planet_offsets={
                "Sun":     30.0,
                "Moon":    45.0,
                "Mars":    60.0,
                "Mercury": 75.0,
                "Jupiter": 90.0,
                "Venus":  120.0,
                "Saturn": 200.0,  # past Ketu (at 180°)
            },
        )
        result = detect_kala_sarpa(chart, asc_sign=1)
        assert result == []

    def test_rahu_in_different_sign(self):
        """Rahu at 90° (Cancer). All 7 in (90°, 270°) → KSY."""
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = _kala_sarpa_chart(
            rahu_lon=90.0,
            planet_offsets={
                "Sun":     20.0,
                "Moon":    40.0,
                "Mars":    60.0,
                "Mercury": 80.0,
                "Jupiter": 100.0,
                "Venus":  130.0,
                "Saturn": 170.0,
            },
        )
        result = detect_kala_sarpa(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.kala_sarpa.ksy"


# ---------------------------------------------------------------------------
# Kala Amrita Yoga — Ketu-leading 180° arc
# ---------------------------------------------------------------------------


class TestKalaAmritaYoga:

    def test_all_seven_in_ketu_leading_arc(self):
        """Rahu at 0° → Ketu at 180°. All 7 in (180°, 360°) arc going
        forward from Ketu → Kala Amrita."""
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        # Place planets at Rahu_lon + 200°..350° → all between Ketu and Rahu
        chart = _kala_sarpa_chart(
            rahu_lon=0.0,
            planet_offsets={
                "Sun":     200.0,
                "Moon":    220.0,
                "Mars":    240.0,
                "Mercury": 260.0,
                "Jupiter": 280.0,
                "Venus":   310.0,
                "Saturn":  340.0,
            },
        )
        result = detect_kala_sarpa(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.kala_sarpa.amrita"
        assert result[0].direction == "positive"


# ---------------------------------------------------------------------------
# Property: no findings when neither strict variant matches
# ---------------------------------------------------------------------------


class TestNoFinding:

    def test_planets_spread_across_both_hemispheres_no_finding(self):
        """4 planets in Rahu-leading half, 3 in Ketu-leading half →
        neither strict variant matches → no Finding."""
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = _kala_sarpa_chart(
            rahu_lon=0.0,
            planet_offsets={
                "Sun":     30.0,
                "Moon":    60.0,
                "Mars":    90.0,
                "Mercury": 120.0,
                # The next three sit past Ketu (in Ketu→Rahu arc):
                "Jupiter": 200.0,
                "Venus":   240.0,
                "Saturn":  300.0,
            },
        )
        result = detect_kala_sarpa(chart, asc_sign=1)
        assert result == []

    def test_no_rahu_no_finding(self):
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = {
            p: _planet_dict(30.0)
            for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                      "Venus", "Saturn", "Ketu")
        }
        # No Rahu — detector should silently skip.
        result = detect_kala_sarpa(chart, asc_sign=1)
        assert result == []


# ---------------------------------------------------------------------------
# Finding envelope
# ---------------------------------------------------------------------------


class TestFindingEnvelope:

    def test_verdict_under_140_chars(self):
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = _kala_sarpa_chart(
            rahu_lon=0.0,
            planet_offsets={
                "Sun":     30.0,  "Moon":    45.0, "Mars":    60.0,
                "Mercury": 75.0,  "Jupiter": 90.0, "Venus":  120.0,
                "Saturn":  150.0,
            },
        )
        result = detect_kala_sarpa(chart, asc_sign=1)
        for f in result:
            assert len(f.verdict) <= 140

    def test_evidence_contains_doctrine_sentinel(self):
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = _kala_sarpa_chart(
            rahu_lon=0.0,
            planet_offsets={
                "Sun":     30.0, "Moon": 45.0, "Mars": 60.0,
                "Mercury": 75.0, "Jupiter": 90.0, "Venus": 120.0,
                "Saturn":  150.0,
            },
        )
        result = detect_kala_sarpa(chart, asc_sign=1)
        for f in result:
            doctrine = next(
                (e for e in f.evidence if e.startswith("doctrine=")), None
            )
            assert doctrine is not None
            assert "D-12" in doctrine or "Kala Sarpa" in doctrine

    def test_confidence_is_indicative_only(self):
        from app.reading.computations.yogas_extended.kala_sarpa import (
            detect_kala_sarpa,
        )

        chart = _kala_sarpa_chart(
            rahu_lon=0.0,
            planet_offsets={
                "Sun":     30.0, "Moon": 45.0, "Mars": 60.0,
                "Mercury": 75.0, "Jupiter": 90.0, "Venus": 120.0,
                "Saturn":  150.0,
            },
        )
        [finding] = detect_kala_sarpa(chart, asc_sign=1)
        assert finding.confidence.band == "indicative_only"
        assert finding.confidence.score == 0.0
