"""Tests for ``app.reading.computations.gandanta``.

Detects planets in the three water-to-fire nakshatra junctions
(Revati->Ashwini, Ashlesha->Magha, Jyeshtha->Mula). Classical zone is
+-3 deg 20 min (one pada) around each junction.

We exercise the public API on synthetic charts so the geometry is under
test independent of any specific birth-data fixture, then sanity-check
against the Bangalore baseline.
"""
from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st


# Pada (= 1 nakshatra / 4) = 360/27/4 = 3.3333... degrees. This is the
# classical Gandanta zone half-width per BPHS / Phaladeepika tradition.
_GANDANTA_ZONE_HALFWIDTH = 360.0 / 27.0 / 4.0  # ~ 3.333... degrees

# The three water-to-fire junction longitudes in sidereal absolute degrees.
# Revati ends at 360.0 (= 0.0 mod 360, start of Ashwini in Aries).
# Ashlesha ends at 120.0 (= start of Magha in Leo).
# Jyeshtha ends at 240.0 (= start of Mula in Sagittarius).
_JUNCTIONS = (0.0, 120.0, 240.0)


# ---------------------------------------------------------------------------
# Bangalore baseline (shared with other Tier-0 tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


# ---------------------------------------------------------------------------
# Synthetic chart helpers
# ---------------------------------------------------------------------------


def _make_chart(longitudes: dict[str, float]) -> dict:
    """Build the minimal d1 envelope ``detect_gandanta`` consumes."""
    return {
        name: {"name": name, "longitude": lon, "is_retrograde": False}
        for name, lon in longitudes.items()
    }


# ---------------------------------------------------------------------------
# Construction / shape
# ---------------------------------------------------------------------------


class TestDetectGandanta:

    def test_no_planets_in_gandanta_returns_empty_list(self):
        """When no planet is inside any junction zone, return [] (empty)."""
        from app.reading.computations.gandanta import detect_gandanta

        # 60 deg (mid-Taurus) is safely far from every junction.
        chart = _make_chart({"Sun": 60.0, "Moon": 60.0})
        result = detect_gandanta(chart)
        assert result == []

    def test_planet_in_pisces_gandanta_zone_detected(self):
        """A planet at 358 deg (Revati pada 4) sits inside Revati->Ashwini zone."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Mercury": 358.0})
        result = detect_gandanta(chart)
        assert len(result) == 1
        assert result[0].id == "primitive.gandanta.mercury"

    def test_planet_in_aries_gandanta_zone_detected(self):
        """A planet at 2 deg (Ashwini pada 1) sits inside Revati->Ashwini zone."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Saturn": 2.0})
        result = detect_gandanta(chart)
        assert len(result) == 1
        assert result[0].id == "primitive.gandanta.saturn"

    def test_planet_in_cancer_leo_gandanta_zone(self):
        """A planet near 120 deg (Ashlesha-Magha) is detected."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Jupiter": 118.5})  # ~1.5 deg before junction
        result = detect_gandanta(chart)
        assert len(result) == 1
        assert "Ashlesha" in result[0].verdict or "Magha" in result[0].verdict

    def test_planet_in_scorpio_sag_gandanta_zone(self):
        """A planet near 240 deg (Jyeshtha-Mula) is detected."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Mars": 241.0})
        result = detect_gandanta(chart)
        assert len(result) == 1
        assert "Jyeshtha" in result[0].verdict or "Mula" in result[0].verdict

    def test_emits_findings(self):
        """Each output is a valid Finding instance."""
        from app.reading.computations.gandanta import detect_gandanta
        from app.reading.schema import Finding

        chart = _make_chart({"Mars": 241.0, "Sun": 60.0, "Mercury": 358.5})
        result = detect_gandanta(chart)
        for finding in result:
            assert isinstance(finding, Finding)

    def test_id_grammar(self):
        """IDs follow ``primitive.gandanta.<planet>`` format."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Mars": 241.0})
        result = detect_gandanta(chart)
        for finding in result:
            assert finding.id.startswith("primitive.gandanta.")

    def test_classification_is_affliction(self):
        """Gandanta is an affliction per classical doctrine."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Jupiter": 119.5})
        result = detect_gandanta(chart)
        assert result[0].classification == "affliction"

    def test_direction_is_negative(self):
        """Gandanta carries a negative valence (knot, instability)."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Jupiter": 119.5})
        result = detect_gandanta(chart)
        assert result[0].direction == "negative"

    def test_verdict_under_140_chars(self):
        """Verdict respects the universal Finding limit."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Mars": 241.0, "Jupiter": 119.5, "Mercury": 358.5})
        result = detect_gandanta(chart)
        for finding in result:
            assert len(finding.verdict) <= 140

    def test_verdict_includes_planet_and_degree(self):
        """Verdict carries the planet name and degree, per spec phrasing."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Mars": 241.0})
        result = detect_gandanta(chart)
        verdict = result[0].verdict
        assert "Mars" in verdict
        # Some representation of the degree must appear.
        assert "241" in verdict or "1.00" in verdict or "1.0" in verdict

    def test_boundary_at_exact_junction(self):
        """A planet exactly at 0 / 120 / 240 deg lands inside Gandanta."""
        from app.reading.computations.gandanta import detect_gandanta

        chart = _make_chart({"Sun": 120.0})
        result = detect_gandanta(chart)
        assert len(result) == 1

    def test_just_outside_zone_not_detected(self):
        """A planet > 3 deg 20 min away from junction is NOT in Gandanta."""
        from app.reading.computations.gandanta import detect_gandanta

        # 5 deg past Ashlesha-Magha junction = 125.0, well outside.
        chart = _make_chart({"Mercury": 125.0})
        result = detect_gandanta(chart)
        assert result == []

    def test_bangalore_baseline_runs_without_error(self, bangalore_chart):
        """Sanity check: Bangalore baseline doesn't crash detect_gandanta."""
        from app.reading.computations.gandanta import detect_gandanta
        from app.reading.schema import Finding

        result = detect_gandanta(bangalore_chart["d1"])
        # Result may be empty or not; just verify it's a list of Findings.
        assert isinstance(result, list)
        for f in result:
            assert isinstance(f, Finding)


# ---------------------------------------------------------------------------
# Property-based invariants
# ---------------------------------------------------------------------------


_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


@st.composite
def _synthetic_d1(draw, lon_strategy=st.floats(min_value=0.0, max_value=359.999)):
    return {name: {"name": name, "longitude": draw(lon_strategy), "is_retrograde": False} for name in _PLANETS}


def _is_in_gandanta(lon: float) -> bool:
    """Reference predicate: True iff lon lies within +-3.333... of a junction."""
    lon = lon % 360.0
    for jct in _JUNCTIONS:
        diff = abs(lon - jct)
        diff = min(diff, 360.0 - diff)  # circular distance
        if diff <= _GANDANTA_ZONE_HALFWIDTH + 1e-9:
            return True
    return False


class TestPropertyInvariants:

    @given(d1=_synthetic_d1())
    def test_detected_count_matches_reference_predicate(self, d1):
        """The set of Gandanta planets matches the independent predicate.

        We use the schema-only reference ``_is_in_gandanta`` to validate
        the module's geometry; if the two disagree on any chart, either
        the implementation or the test predicate is wrong (whichever is
        cheaper to fix).
        """
        from app.reading.computations.gandanta import detect_gandanta

        expected = {n for n, p in d1.items() if _is_in_gandanta(p["longitude"])}
        result = detect_gandanta(d1)
        got = {f.id.rsplit(".", 1)[1] for f in result}
        # Normalize: implementation slugs are lowercase.
        expected_slugs = {name.lower() for name in expected}
        assert got == expected_slugs

    @given(d1=_synthetic_d1())
    def test_id_uniqueness(self, d1):
        from app.reading.computations.gandanta import detect_gandanta

        result = detect_gandanta(d1)
        ids = [f.id for f in result]
        assert len(ids) == len(set(ids))

    @given(d1=_synthetic_d1())
    def test_all_findings_have_negative_direction(self, d1):
        from app.reading.computations.gandanta import detect_gandanta

        result = detect_gandanta(d1)
        for f in result:
            assert f.direction == "negative"
            assert f.classification == "affliction"
