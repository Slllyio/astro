"""Tests for ``app.reading.computations.eclipse_natal_activation``.

Doctrine source: Modern Jyotisha synthesis (no single BPHS verse). The
rule, established in K.N. Rao's predictive astrology and refined in
BV Raman's *Eclipses in Mundane Astrology*, holds that an eclipse
whose ecliptic degree falls within ±1° of a natal nakshatra-degree (a
planet's longitude or the lagna) activates that natal point for the
~6 months following the eclipse.

Algorithm
=========

1. For each supplied eclipse (date, type, degree, sign):
   a. Compute the eclipse longitude (sign_index − 1) × 30 + degree.
   b. For each natal point (9 planets + lagna):
      - Compute the natal longitude (with lagna at the supplied mid-sign
        offset).
      - Test |eclipse_lon − natal_lon| ≤ 1° in circular distance.
      - If hit, emit a Finding.

Direction
=========

* If natal point is a benefic (Jupiter, Venus, Mercury, Moon) → positive
  (the activation is constructive — career, finance, learning).
* If natal point is a malefic (Sun, Mars, Saturn, Rahu, Ketu) → negative
  (the activation foregrounds difficulty — health, friction).
* Lagna activation → neutral (signals general life-direction shift).
"""
from __future__ import annotations

import pytest


def _planet(longitude: float, sign: int | None = None) -> dict:
    record = {"longitude": longitude % 360.0}
    record["sign"] = sign if sign is not None else int(longitude // 30.0) + 1
    record["degree_in_sign"] = longitude % 30.0
    record["nakshatra"] = {
        "index": int((longitude % 360.0) // (360.0 / 27.0)),
        "name": "Ashwini",
    }
    return record


def _build_chart(planets: dict[str, dict]) -> dict:
    chart: dict[str, dict] = {}
    benign = _planet(0.5, 1)
    for name in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ):
        chart[name] = planets.get(name, benign)
    return chart


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestShape:

    def test_returns_list(self):
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        result = detect_eclipse_activation(
            _build_chart({}), asc_sign=1, eclipses=[],
        )
        assert isinstance(result, list)

    def test_no_eclipses_no_findings(self):
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        result = detect_eclipse_activation(
            _build_chart({}), asc_sign=1, eclipses=[],
        )
        assert result == []


# ---------------------------------------------------------------------------
# Direct hit cases.
# ---------------------------------------------------------------------------


class TestDirectHit:

    def test_solar_eclipse_at_moon_position_emits(self):
        """Solar eclipse at 23° Cancer (= sign 4) — moon at 23° Cancer
        (longitude 113°). Hit within 0° — must fire."""
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart = _build_chart({
            "Moon": _planet(longitude=113.0, sign=4),  # 23° Cancer
        })
        eclipses = [{
            "date": "2026-07-12",
            "type": "solar",
            "degree": 23.0,
            "sign": 4,  # Cancer
        }]
        result = detect_eclipse_activation(chart, asc_sign=4, eclipses=eclipses)
        assert len(result) >= 1
        # Moon-finding present.
        ids = {f.id for f in result}
        assert any("moon" in i for i in ids), f"Moon activation missing: {ids}"

    def test_hit_within_1_degree_orb(self):
        """Eclipse 0.5° from Moon — within orb."""
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart = _build_chart({
            "Moon": _planet(longitude=113.0, sign=4),
        })
        eclipses = [{
            "date": "2026-07-12",
            "type": "solar",
            "degree": 23.5,  # 0.5° away from Moon's 23°
            "sign": 4,
        }]
        result = detect_eclipse_activation(chart, asc_sign=4, eclipses=eclipses)
        assert any("moon" in f.id for f in result)

    def test_miss_beyond_1_degree(self):
        """Eclipse 2° from Moon — outside orb."""
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart = _build_chart({
            "Moon": _planet(longitude=113.0, sign=4),
        })
        eclipses = [{
            "date": "2026-07-12",
            "type": "solar",
            "degree": 25.0,  # 2° away
            "sign": 4,
        }]
        result = detect_eclipse_activation(chart, asc_sign=4, eclipses=eclipses)
        for f in result:
            assert "moon" not in f.id, "Moon falsely activated outside orb"


# ---------------------------------------------------------------------------
# Direction depends on benefic/malefic.
# ---------------------------------------------------------------------------


class TestDirection:

    def test_benefic_activation_positive(self):
        """Jupiter activated → positive."""
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart = _build_chart({
            "Jupiter": _planet(longitude=113.0, sign=4),
        })
        eclipses = [{
            "date": "2026-07-12",
            "type": "solar",
            "degree": 23.0,
            "sign": 4,
        }]
        result = detect_eclipse_activation(chart, asc_sign=4, eclipses=eclipses)
        jupiter_findings = [f for f in result if "jupiter" in f.id]
        assert jupiter_findings
        assert jupiter_findings[0].direction == "positive"

    def test_malefic_activation_negative(self):
        """Saturn activated → negative."""
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart = _build_chart({
            "Saturn": _planet(longitude=113.0, sign=4),
        })
        eclipses = [{
            "date": "2026-07-12",
            "type": "solar",
            "degree": 23.0,
            "sign": 4,
        }]
        result = detect_eclipse_activation(chart, asc_sign=4, eclipses=eclipses)
        saturn_findings = [f for f in result if "saturn" in f.id]
        assert saturn_findings
        assert saturn_findings[0].direction == "negative"


# ---------------------------------------------------------------------------
# Finding contract.
# ---------------------------------------------------------------------------


class TestFindingContract:

    def _moon_hit_chart_and_eclipses(self) -> tuple[dict, list[dict]]:
        chart = _build_chart({
            "Moon": _planet(longitude=113.0, sign=4),
        })
        eclipses = [{
            "date": "2026-07-12",
            "type": "solar",
            "degree": 23.0,
            "sign": 4,
        }]
        return chart, eclipses

    def test_id_grammar(self):
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart, eclipses = self._moon_hit_chart_and_eclipses()
        result = detect_eclipse_activation(chart, asc_sign=4, eclipses=eclipses)
        moon_f = next(f for f in result if "moon" in f.id)
        # id pattern: practitioner.eclipse_activation.<date>_<natal_point>
        assert moon_f.id.startswith("practitioner.eclipse_activation.")
        assert "2026-07-12" in moon_f.id
        assert "moon" in moon_f.id

    def test_classification_is_trigger(self):
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart, eclipses = self._moon_hit_chart_and_eclipses()
        result = detect_eclipse_activation(chart, asc_sign=4, eclipses=eclipses)
        for f in result:
            assert f.classification == "trigger"

    def test_verdict_under_140(self):
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart, eclipses = self._moon_hit_chart_and_eclipses()
        result = detect_eclipse_activation(chart, asc_sign=4, eclipses=eclipses)
        for f in result:
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Multi-eclipse + multi-natal-hit coverage.
# ---------------------------------------------------------------------------


class TestMultipleHits:

    def test_two_eclipses_each_hitting(self):
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart = _build_chart({
            "Moon":   _planet(longitude=113.0, sign=4),
            "Saturn": _planet(longitude=215.0, sign=8),  # 5° Scorpio
        })
        eclipses = [
            {"date": "2026-07-12", "type": "solar", "degree": 23.0, "sign": 4},
            {"date": "2026-12-21", "type": "lunar", "degree": 5.0, "sign": 8},
        ]
        result = detect_eclipse_activation(chart, asc_sign=4, eclipses=eclipses)
        assert len(result) >= 2
        ids = {f.id for f in result}
        assert any("moon" in i for i in ids)
        assert any("saturn" in i for i in ids)


# ---------------------------------------------------------------------------
# Lagna activation.
# ---------------------------------------------------------------------------


class TestLagnaActivation:

    def test_eclipse_at_lagna_emits_lagna_finding(self):
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        # Lagna = Aries (asc_sign=1). v1 simplification uses mid-sign (15°).
        chart = _build_chart({})
        eclipses = [{
            "date": "2026-04-01",
            "type": "solar",
            "degree": 15.0,  # mid-Aries
            "sign": 1,
        }]
        result = detect_eclipse_activation(chart, asc_sign=1, eclipses=eclipses)
        ids = {f.id for f in result}
        assert any("lagna" in i for i in ids), (
            f"Lagna activation missing for eclipse at mid-Aries: {ids}"
        )

    def test_lagna_direction_is_neutral(self):
        from app.reading.computations.eclipse_natal_activation import (
            detect_eclipse_activation,
        )

        chart = _build_chart({})
        eclipses = [{
            "date": "2026-04-01",
            "type": "solar",
            "degree": 15.0,
            "sign": 1,
        }]
        result = detect_eclipse_activation(chart, asc_sign=1, eclipses=eclipses)
        lagna_findings = [f for f in result if "lagna" in f.id]
        assert lagna_findings
        assert lagna_findings[0].direction == "neutral"
