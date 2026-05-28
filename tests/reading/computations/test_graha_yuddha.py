"""Tests for ``app.reading.computations.graha_yuddha``.

Doctrine lock D-13 (``docs/doctrine-decisions.md``):

    When two non-luminary planets are within 1° of longitude of each
    other (in the same sign), they engage in Graha Yuddha (planetary
    war). The winner is determined by celestial latitude: the more
    NORTHERN-latitude planet wins (BPHS Vol.I Ch.27 v.13). The loser's
    effects spoil lifelong (treated as if combust).

    Sun and Moon are EXCLUDED — luminaries do not engage in graha yuddha
    in classical doctrine.

Inputs
======

The detector reads planet records carrying:
  - ``longitude`` (sidereal Lahiri, degrees [0, 360))
  - ``sign`` (1..12)
  - ``latitude`` (celestial latitude in degrees; ECLIPTIC north positive)

Latitude must be supplied per planet — when absent the planet is treated
as never participating in a war (silent skip — defensive).
"""
from __future__ import annotations

import pytest


def _planet(longitude: float, sign: int | None = None,
            latitude: float | None = None) -> dict:
    """Build a minimal planet record."""
    record = {"longitude": longitude % 360.0}
    record["sign"] = sign if sign is not None else int(longitude // 30.0) + 1
    record["degree_in_sign"] = longitude % 30.0
    if latitude is not None:
        record["latitude"] = latitude
    return record


def _build_chart(planets: dict[str, dict]) -> dict:
    """Build a d1 chart, filling missing planets with safe 1H placements."""
    chart: dict[str, dict] = {}
    for name in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ):
        chart[name] = planets.get(name, _planet(0.5, 1, 0.0))
    return chart


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestDetectShape:

    def test_returns_list(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        result = detect_graha_yuddha(_build_chart({}))
        assert isinstance(result, list)

    def test_no_war_no_findings(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        # All planets at sign 1, 0.5° — but a uniform deg means many are
        # within 1°. We move them apart explicitly.
        chart = _build_chart({
            "Mars":    _planet(15.0, sign=1, latitude=1.0),
            "Mercury": _planet(45.0, sign=2, latitude=0.5),
            "Jupiter": _planet(75.0, sign=3, latitude=0.5),
            "Venus":   _planet(105.0, sign=4, latitude=0.5),
            "Saturn":  _planet(135.0, sign=5, latitude=0.5),
        })
        result = detect_graha_yuddha(chart)
        assert result == []


# ---------------------------------------------------------------------------
# D-13 northern-latitude winner pin.
# ---------------------------------------------------------------------------


class TestDirectWar:

    def test_mars_vs_saturn_mars_wins_when_more_northern(self):
        """Mars at +2.1°N latitude beats Saturn at +1.4°N latitude.
        Both within 1° longitude in same sign."""
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        chart = _build_chart({
            "Mars":   _planet(15.0, sign=1, latitude=2.1),
            "Saturn": _planet(15.5, sign=1, latitude=1.4),
        })
        result = detect_graha_yuddha(chart)
        assert len(result) == 1
        verdict = result[0].verdict
        # Mars wins.
        assert "Mars" in verdict
        assert "Saturn" in verdict
        # Winner mentioned first in verdict ("Mars wins over Saturn").
        assert verdict.index("Mars") < verdict.index("Saturn")

    def test_saturn_wins_when_more_northern(self):
        """Reverse: Saturn at +3.0°N beats Mars at +0.2°N."""
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        chart = _build_chart({
            "Mars":   _planet(15.0, sign=1, latitude=0.2),
            "Saturn": _planet(15.5, sign=1, latitude=3.0),
        })
        result = detect_graha_yuddha(chart)
        assert len(result) == 1
        verdict = result[0].verdict
        # Saturn wins.
        assert verdict.index("Saturn") < verdict.index("Mars")

    def test_negative_latitudes_southern_loses(self):
        """Mars +0.5°N vs Saturn -1.0° (south of ecliptic). Mars wins."""
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        chart = _build_chart({
            "Mars":   _planet(15.0, sign=1, latitude=0.5),
            "Saturn": _planet(15.5, sign=1, latitude=-1.0),
        })
        result = detect_graha_yuddha(chart)
        assert len(result) == 1
        verdict = result[0].verdict
        assert verdict.index("Mars") < verdict.index("Saturn")


# ---------------------------------------------------------------------------
# Finding contract.
# ---------------------------------------------------------------------------


class TestFindingContract:

    def _war_chart(self) -> dict:
        return _build_chart({
            "Mars":   _planet(15.0, sign=1, latitude=2.1),
            "Saturn": _planet(15.5, sign=1, latitude=1.4),
        })

    def test_id_grammar(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        [f] = detect_graha_yuddha(self._war_chart())
        # id pattern: practitioner.graha_yuddha.<winner>_vs_<loser>
        assert f.id == "practitioner.graha_yuddha.mars_vs_saturn"

    def test_classification_is_affliction(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        [f] = detect_graha_yuddha(self._war_chart())
        assert f.classification == "affliction"

    def test_direction_is_negative(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        [f] = detect_graha_yuddha(self._war_chart())
        assert f.direction == "negative"

    def test_verdict_under_140(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        [f] = detect_graha_yuddha(self._war_chart())
        assert len(f.verdict) <= 140

    def test_evidence_cites_d13(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        [f] = detect_graha_yuddha(self._war_chart())
        assert any("D-13" in e for e in f.evidence)


# ---------------------------------------------------------------------------
# Luminary exclusion (D-13 invariant).
# ---------------------------------------------------------------------------


class TestLuminaryExclusion:

    def test_sun_never_wars(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        chart = _build_chart({
            "Sun":  _planet(15.0, sign=1, latitude=0.0),
            "Mars": _planet(15.5, sign=1, latitude=1.0),
        })
        # Even though within 1° longitude, Sun's involvement disqualifies.
        result = detect_graha_yuddha(chart)
        assert result == []

    def test_moon_never_wars(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        chart = _build_chart({
            "Moon":   _planet(15.0, sign=1, latitude=2.0),
            "Saturn": _planet(15.5, sign=1, latitude=1.4),
        })
        result = detect_graha_yuddha(chart)
        assert result == []


# ---------------------------------------------------------------------------
# Out-of-orb and out-of-sign cases.
# ---------------------------------------------------------------------------


class TestOrbBoundary:

    def test_more_than_1_degree_apart_no_war(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        chart = _build_chart({
            "Mars":   _planet(15.0, sign=1, latitude=2.1),
            "Saturn": _planet(16.5, sign=1, latitude=1.4),  # 1.5° apart
        })
        result = detect_graha_yuddha(chart)
        assert result == []

    def test_different_signs_no_war(self):
        """Even if longitudes are within 1° across the 30° cusp, the war
        only fires when both planets are in the SAME sign (classical
        doctrine — different-sign-near-cusp is technically a conjunction
        not a war)."""
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        chart = _build_chart({
            "Mars":   _planet(29.8, sign=1, latitude=2.1),
            "Saturn": _planet(30.5, sign=2, latitude=1.4),
        })
        result = detect_graha_yuddha(chart)
        assert result == []


# ---------------------------------------------------------------------------
# Property: only non-luminary planets participate.
# ---------------------------------------------------------------------------


class TestPropertyParticipants:

    def test_only_non_luminaries_appear_in_finding_ids(self):
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        # Crowd many planets into a 0.5° band; verify Sun/Moon never
        # surface in the resulting Finding IDs.
        chart = _build_chart({
            "Sun":     _planet(15.0, sign=1, latitude=0.0),
            "Moon":    _planet(15.1, sign=1, latitude=4.0),
            "Mars":    _planet(15.2, sign=1, latitude=2.1),
            "Mercury": _planet(15.3, sign=1, latitude=1.8),
            "Jupiter": _planet(15.4, sign=1, latitude=1.5),
            "Venus":   _planet(15.5, sign=1, latitude=1.2),
            "Saturn":  _planet(15.6, sign=1, latitude=0.9),
        })
        findings = detect_graha_yuddha(chart)
        for f in findings:
            assert "sun_vs" not in f.id and "_vs_sun" not in f.id, (
                f"Sun appears in finding id {f.id} — luminary should be excluded"
            )
            assert "moon_vs" not in f.id and "_vs_moon" not in f.id, (
                f"Moon appears in finding id {f.id} — luminary should be excluded"
            )


# ---------------------------------------------------------------------------
# Missing-latitude defensive branch.
# ---------------------------------------------------------------------------


class TestMissingLatitude:

    def test_silently_skips_when_latitude_unavailable(self):
        """If latitude is absent for one of the close planets, we cannot
        determine the winner — skip silently."""
        from app.reading.computations.graha_yuddha import detect_graha_yuddha

        chart = _build_chart({
            "Mars":   _planet(15.0, sign=1, latitude=None),  # no latitude
            "Saturn": _planet(15.5, sign=1, latitude=1.4),
        })
        result = detect_graha_yuddha(chart)
        assert result == []
