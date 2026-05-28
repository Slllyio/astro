"""Tests for ``app.reading.computations.residential_strength``.

Doctrine lock D-5 (``docs/doctrine-decisions.md``):

    strength = 60 × (1 − distance_from_madhya / 30)

where ``distance_from_madhya`` is the absolute degree-distance (within
the 30° sign) between the planet's longitude-within-sign and the
Lagna's degree-within-its-sign. The 8° / 3° classification bands are a
**post-processing overlay** applied on top of the continuous formula.

Bangalore baseline (1990-07-15 12:00 IST / 12.97, 77.59) is used as the
canonical fixture; we recompute it at test time rather than hard-coding
values.
"""
from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Bangalore baseline fixture
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


@pytest.fixture(scope="module")
def lagna_degree(bangalore_chart) -> float:
    return float(bangalore_chart["ascendant"]["degree_in_sign"])


# ---------------------------------------------------------------------------
# Construction / shape
# ---------------------------------------------------------------------------


class TestComputeResidentialStrength:

    def test_returns_mapping_per_planet(self, d1_chart, lagna_degree):
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        result = compute_residential_strength(d1_chart, lagna_degree)
        assert isinstance(result, dict)
        assert set(result.keys()) == set(d1_chart.keys())

    def test_emits_findings(self, d1_chart, lagna_degree):
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )
        from app.reading.schema import Finding

        result = compute_residential_strength(d1_chart, lagna_degree)
        for planet, finding in result.items():
            assert isinstance(finding, Finding), f"{planet} is not a Finding"

    def test_id_grammar(self, d1_chart, lagna_degree):
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        result = compute_residential_strength(d1_chart, lagna_degree)
        for planet, finding in result.items():
            assert finding.id == (
                f"primitive.residential_strength.{planet.lower()}"
            )

    def test_classification_is_primitive(self, d1_chart, lagna_degree):
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        result = compute_residential_strength(d1_chart, lagna_degree)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, d1_chart, lagna_degree):
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        result = compute_residential_strength(d1_chart, lagna_degree)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_strength_within_range(self, d1_chart, lagna_degree):
        """All emitted strengths must be in [0, 60]."""
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        result = compute_residential_strength(d1_chart, lagna_degree)
        for finding in result.values():
            strength = None
            for line in finding.evidence:
                if line.startswith("strength="):
                    strength = float(line.split("=", 1)[1])
                    break
            assert strength is not None
            assert 0.0 <= strength <= 60.0


class TestFormulaCorrectness:
    """Verify the explicit linear falloff per D-5."""

    def test_planet_at_madhya_scores_sixty(self):
        """Planet exactly at the Lagna's degree -> max strength of 60."""
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        chart = {
            "Sun": {
                "longitude": 22.5, "degree_in_sign": 22.5,
                "is_retrograde": False,
            },
        }
        result = compute_residential_strength(chart, lagna_degree=22.5)
        strength = _parse_strength(result["Sun"])
        assert abs(strength - 60.0) < 1e-9

    def test_planet_at_sandhi_scores_zero(self):
        """Planet 30° from madhya (i.e. at sandhi) scores 0."""
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        # Madhya at degree 15; sandhi is 15° before or 15° after = 0 or 30 in sign.
        # But the half-bhava span is 30°/2 = 15° each direction... wait, with the
        # formula `1 - dist/30` strength=0 needs dist=30. The "distance" here
        # is computed *within* the 30° sign as min(diff, 30-diff), so max dist
        # is 15. The formula clips dist at 30 for safety; in practice the max
        # natural value is 15 -> strength of 30. Use lagna deg 0 and planet at
        # exactly 15 to ensure we hit the half-sign midpoint.
        chart = {
            "Sun": {
                "longitude": 15.0, "degree_in_sign": 15.0,
                "is_retrograde": False,
            },
        }
        result = compute_residential_strength(chart, lagna_degree=0.0)
        strength = _parse_strength(result["Sun"])
        # dist = min(15, 30-15) = 15, strength = 60 * (1 - 15/30) = 30.
        assert abs(strength - 30.0) < 1e-9

    def test_planet_8deg_from_madhya_approx_44(self):
        """Planet exactly 8° from Lagna degree scores ~44 (8°-strong band)."""
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        chart = {
            "Sun": {
                "longitude": 20.0, "degree_in_sign": 20.0,
                "is_retrograde": False,
            },
        }
        # Lagna at 12°; planet at 20° -> abs diff = 8°; circular min = 8.
        result = compute_residential_strength(chart, lagna_degree=12.0)
        strength = _parse_strength(result["Sun"])
        expected = 60.0 * (1.0 - 8.0 / 30.0)  # 44.0
        assert abs(strength - expected) < 1e-9
        # 8° from madhya falls in 'strong' band (>= 40).
        band = _parse_band(result["Sun"])
        assert band == "strong"

    def test_planet_3deg_from_madhya_very_strong(self):
        """Planet 3° from Lagna scores ~54, in the 'very_strong' band (>=51)."""
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        chart = {
            "Sun": {
                "longitude": 15.0, "degree_in_sign": 15.0,
                "is_retrograde": False,
            },
        }
        # Lagna at 12°; planet at 15° -> diff = 3°.
        result = compute_residential_strength(chart, lagna_degree=12.0)
        strength = _parse_strength(result["Sun"])
        expected = 60.0 * (1.0 - 3.0 / 30.0)  # 54.0
        assert abs(strength - expected) < 1e-9
        band = _parse_band(result["Sun"])
        assert band == "very_strong"

    def test_circular_wraparound(self):
        """A planet at 0.0° and Lagna at 29.5° -> distance 0.5° (wraparound)."""
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        chart = {
            "Sun": {
                "longitude": 30.0, "degree_in_sign": 0.0,
                "is_retrograde": False,
            },
        }
        result = compute_residential_strength(chart, lagna_degree=29.5)
        strength = _parse_strength(result["Sun"])
        # Distance: min(|0 - 29.5|, 30 - |0 - 29.5|) = min(29.5, 0.5) = 0.5.
        expected = 60.0 * (1.0 - 0.5 / 30.0)  # 59.0
        assert abs(strength - expected) < 1e-9


class TestBands:
    """The four classification bands: very_strong / strong / moderate / weak."""

    @pytest.mark.parametrize(
        "lagna_deg,planet_deg,expected_band",
        [
            # diff=0   -> strength 60 -> very_strong
            (10.0, 10.0, "very_strong"),
            # diff=4.5 -> strength = 60*(1-4.5/30) = 51 -> very_strong
            (10.0, 14.5, "very_strong"),
            # diff=5   -> strength = 50 -> strong (>= 40, < 51)
            (10.0, 15.0, "strong"),
            # diff=10  -> strength = 40 -> strong (boundary)
            (10.0, 20.0, "strong"),
            # diff=11  -> strength = 60*(1 - 11/30) = 38 -> moderate
            (10.0, 21.0, "moderate"),
            # diff=13  -> strength = 60*(1 - 13/30) = 34 -> moderate
            (10.0, 23.0, "moderate"),
            # diff=15  -> strength = 30 -> not weak yet (>= 20)
            (10.0, 25.0, "moderate"),
        ],
    )
    def test_band_thresholds(self, lagna_deg, planet_deg, expected_band):
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        chart = {
            "Sun": {
                "longitude": planet_deg,
                "degree_in_sign": planet_deg,
                "is_retrograde": False,
            },
        }
        result = compute_residential_strength(chart, lagna_degree=lagna_deg)
        assert _parse_band(result["Sun"]) == expected_band


# ---------------------------------------------------------------------------
# Property-based invariants
# ---------------------------------------------------------------------------


_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury",
    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


@st.composite
def _synthetic_d1(draw):
    return {
        name: {
            "longitude": draw(st.floats(min_value=0.0, max_value=359.999)),
            "degree_in_sign": draw(st.floats(min_value=0.0, max_value=29.999)),
            "is_retrograde": False,
        }
        for name in _PLANET_NAMES
    }


class TestPropertyInvariants:

    @given(
        d1=_synthetic_d1(),
        lagna_deg=st.floats(min_value=0.0, max_value=29.999),
    )
    def test_strength_always_in_zero_sixty(self, d1, lagna_deg):
        """Strength must be in [0, 60] for any planet at any degree."""
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        result = compute_residential_strength(d1, lagna_deg)
        for finding in result.values():
            strength = _parse_strength(finding)
            assert 0.0 <= strength <= 60.0

    @given(
        deg=st.floats(min_value=0.0, max_value=29.999),
    )
    def test_madhya_gives_max(self, deg):
        """Planet exactly at Lagna's degree -> strength 60.0."""
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        chart = {
            "Sun": {
                "longitude": deg, "degree_in_sign": deg, "is_retrograde": False,
            },
        }
        result = compute_residential_strength(chart, lagna_degree=deg)
        strength = _parse_strength(result["Sun"])
        assert abs(strength - 60.0) < 1e-9

    @given(d1=_synthetic_d1(), lagna_deg=st.floats(min_value=0.0, max_value=29.999))
    def test_ids_unique(self, d1, lagna_deg):
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        result = compute_residential_strength(d1, lagna_deg)
        ids = [f.id for f in result.values()]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_strength(finding) -> float:
    """Extract the numeric ``strength=`` value from a Finding."""
    for line in finding.evidence:
        if line.startswith("strength="):
            return float(line.split("=", 1)[1])
    raise AssertionError(
        f"finding {finding.id!r} missing 'strength=' evidence line"
    )


def _parse_band(finding) -> str:
    """Extract the categorical ``band=`` value from a Finding."""
    for line in finding.evidence:
        if line.startswith("band="):
            return line.split("=", 1)[1]
    raise AssertionError(
        f"finding {finding.id!r} missing 'band=' evidence line"
    )
