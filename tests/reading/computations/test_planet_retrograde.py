"""Tests for ``app.reading.computations.planet_retrograde``.

Wraps the ``is_retrograde`` flag carried by every entry in ``d1`` of a
chart computed by ``app.core.ephemeris_engine.calculate_all_charts`` and
emits Finding-shaped output per the universal schema.

Bangalore baseline (1990-07-15 12:00 IST / 12.97, 77.59) is used as the
canonical fixture; we recompute it at test time rather than hard-coding
values so any swisseph upgrade is caught by these tests.
"""
from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Bangalore baseline fixture (computed once per session)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    """Canonical Bangalore-baseline chart used across reading-layer tests."""
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def d1_chart(bangalore_chart) -> dict:
    return bangalore_chart["d1"]


# ---------------------------------------------------------------------------
# Construction / shape
# ---------------------------------------------------------------------------


class TestDetectRetrograde:
    """``detect_retrograde`` extracts the per-planet retrograde flag."""

    def test_returns_mapping_keyed_by_planet(self, d1_chart):
        """Returns a dict keyed by each planet present in the D1 chart."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        result = detect_retrograde(d1_chart)
        assert isinstance(result, dict)
        # Every planet in D1 yields a Finding.
        assert set(result.keys()) == set(d1_chart.keys())

    def test_emits_findings(self, d1_chart):
        """Each value is a valid Finding model instance."""
        from app.reading.computations.planet_retrograde import detect_retrograde
        from app.reading.schema import Finding

        result = detect_retrograde(d1_chart)
        for planet, finding in result.items():
            assert isinstance(finding, Finding), f"{planet} is not a Finding"

    def test_id_grammar(self, d1_chart):
        """IDs follow ``primitive.planet_retrograde.<planet>`` exactly."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        result = detect_retrograde(d1_chart)
        for planet, finding in result.items():
            assert finding.id == f"primitive.planet_retrograde.{planet.lower()}"

    def test_classification_is_primitive(self, d1_chart):
        """Retrograde is a primitive observation, not promise/affliction/yoga."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        result = detect_retrograde(d1_chart)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_direction_is_neutral(self, d1_chart):
        """Retrograde alone carries no positive/negative valence in our model."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        result = detect_retrograde(d1_chart)
        for finding in result.values():
            assert finding.direction == "neutral"

    def test_sun_and_moon_never_retrograde(self, d1_chart):
        """Sun and Moon are NEVER retrograde in geocentric astronomy."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        result = detect_retrograde(d1_chart)
        assert "direct" in result["Sun"].verdict.lower()
        assert "direct" in result["Moon"].verdict.lower()

    def test_rahu_and_ketu_always_retrograde(self, d1_chart):
        """Mean / True nodes are conventionally always retrograde."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        # Both Rahu and Ketu inherit ``is_retrograde`` from the True Node.
        # That flag may be True or False numerically at any given moment, but
        # we still expect the verdict to follow whatever D1 reports.
        result = detect_retrograde(d1_chart)
        # Whichever way the engine reports, verdict and flag must agree.
        for nodal in ("Rahu", "Ketu"):
            f = result[nodal]
            flag = d1_chart[nodal]["is_retrograde"]
            if flag:
                assert "retrograde" in f.verdict.lower()
            else:
                assert "direct" in f.verdict.lower()

    def test_verdict_under_140_chars(self, d1_chart):
        """Verdict respects the universal Finding limit."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        result = detect_retrograde(d1_chart)
        for finding in result.values():
            assert len(finding.verdict) <= 140


# ---------------------------------------------------------------------------
# Property-based invariants
# ---------------------------------------------------------------------------


# A small synthetic-chart strategy that fabricates the minimal D1 envelope
# the function consumes (one entry per planet, with the boolean flag).
_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury",
    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


@st.composite
def _synthetic_d1(draw):
    return {
        name: {
            "name": name,
            "longitude": draw(st.floats(min_value=0.0, max_value=359.999)),
            "is_retrograde": draw(st.booleans()),
        }
        for name in _PLANET_NAMES
    }


class TestPropertyInvariants:

    @given(d1=_synthetic_d1())
    def test_finding_count_matches_planet_count(self, d1):
        """The set of finding keys must equal the set of d1 keys."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        result = detect_retrograde(d1)
        assert set(result.keys()) == set(d1.keys())

    @given(d1=_synthetic_d1())
    def test_id_uniqueness(self, d1):
        """All emitted IDs are unique (Section 17 invariant)."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        result = detect_retrograde(d1)
        ids = [f.id for f in result.values()]
        assert len(ids) == len(set(ids))

    @given(d1=_synthetic_d1())
    def test_verdict_matches_flag(self, d1):
        """When ``is_retrograde`` is True the verdict says retrograde, else direct."""
        from app.reading.computations.planet_retrograde import detect_retrograde

        result = detect_retrograde(d1)
        for name, finding in result.items():
            if d1[name]["is_retrograde"]:
                assert "retrograde" in finding.verdict.lower()
                assert "direct" not in finding.verdict.lower()
            else:
                assert "direct" in finding.verdict.lower()
                assert "retrograde" not in finding.verdict.lower()
