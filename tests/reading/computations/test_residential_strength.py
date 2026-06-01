"""Tests for ``app.reading.computations.residential_strength``.

Doctrine lock D-5 (``docs/doctrine-decisions.md`` — amended 2026-05-27
post-checkpoint-#1):

    strength = 60 × (1 − distance_from_madhya / 15)

The divisor is **15°**, the half-bhava distance from Bhaav-Madhya to
bhava sandhi under whole-sign Vedic doctrine. The circular distance
``min(diff, 30 - diff)`` naturally maxes at 15°, so the formula reaches
exactly zero at sandhi (D-5 "zero at sandhi" invariant).

Classification bands are **degree-distance based**:

| band         | dist from madhya |
|--------------|------------------|
| very_strong  | ≤ 3°             |
| strong       | ≤ 8°             |
| moderate     | ≤ 12°            |
| weak         | > 12°            |

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
    """Verify the explicit linear falloff per D-5 (divisor 15°)."""

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
        """Planet 15° from madhya (i.e. at sandhi) scores exactly 0.

        D-5 "zero at sandhi" invariant: under whole-sign doctrine the
        bhava sandhi sits 15° from Bhaav-Madhya. The circular distance
        ``min(diff, 30-diff)`` maxes at 15°, and with divisor 15 the
        linear falloff ``60 × (1 - 15/15) = 0`` is the floor.
        """
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        # Lagna at 0°, planet at 15° -> circular dist = min(15, 15) = 15.
        # Per amended D-5: strength = 60 * (1 - 15/15) = 0 (zero at sandhi).
        chart = {
            "Sun": {
                "longitude": 15.0, "degree_in_sign": 15.0,
                "is_retrograde": False,
            },
        }
        result = compute_residential_strength(chart, lagna_degree=0.0)
        strength = _parse_strength(result["Sun"])
        assert strength == 0.0

    def test_planet_8deg_from_madhya_scores_28(self):
        """Planet exactly 8° from Lagna degree scores 28 (= 60 × (1 − 8/15)).

        8° is the BPHS effective-zone boundary, so this planet falls in
        the 'strong' band by the degree-distance cutoff.
        """
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
        expected = 60.0 * (1.0 - 8.0 / 15.0)  # 28.0
        assert abs(strength - expected) < 1e-9
        # 8° from madhya falls exactly on the 'strong' boundary
        # (distance ≤ 8°).
        band = _parse_band(result["Sun"])
        assert band == "strong"

    def test_planet_3deg_from_madhya_scores_48(self):
        """Planet 3° from Lagna scores 48 (= 60 × (1 − 3/15)) in 'very_strong'.

        3° is the Phaladeepika intense-zone boundary; planets at this
        distance from madhya fall in the 'very_strong' degree-based band.
        """
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
        expected = 60.0 * (1.0 - 3.0 / 15.0)  # 48.0
        assert abs(strength - expected) < 1e-9
        band = _parse_band(result["Sun"])
        assert band == "very_strong"

    def test_planet_05deg_from_madhya_scores_58(self):
        """Planet 0.5° from Lagna scores 58 (= 60 × (1 − 0.5/15)) in 'very_strong'."""
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        chart = {
            "Sun": {
                "longitude": 15.0, "degree_in_sign": 15.0,
                "is_retrograde": False,
            },
        }
        # Lagna at 14.5°; planet at 15° -> diff = 0.5°.
        result = compute_residential_strength(chart, lagna_degree=14.5)
        strength = _parse_strength(result["Sun"])
        expected = 60.0 * (1.0 - 0.5 / 15.0)  # 58.0
        assert abs(strength - expected) < 1e-9
        band = _parse_band(result["Sun"])
        assert band == "very_strong"

    def test_planet_at_15deg_distance_is_weak_band(self):
        """Planet at sandhi (15° distance) -> 'weak' band per amended D-5.

        Under the amended degree-distance bands, anything > 12° from
        madhya is classified 'weak' (approaching / at sandhi). 15° is
        the max natural distance, so this is the sandhi case explicitly.
        """
        from app.reading.computations.residential_strength import (
            compute_residential_strength,
        )

        chart = {
            "Sun": {
                "longitude": 15.0, "degree_in_sign": 15.0,
                "is_retrograde": False,
            },
        }
        # Lagna at 0°, planet at 15° -> circular dist = 15° (sandhi).
        result = compute_residential_strength(chart, lagna_degree=0.0)
        strength = _parse_strength(result["Sun"])
        band = _parse_band(result["Sun"])
        assert strength == 0.0
        assert band == "weak"

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
        expected = 60.0 * (1.0 - 0.5 / 15.0)  # 58.0
        assert abs(strength - expected) < 1e-9


class TestBands:
    """The four classification bands: very_strong / strong / moderate / weak.

    Bands are now degree-distance based (amended D-5):
    - very_strong: ≤ 3°
    - strong: ≤ 8°
    - moderate: ≤ 12°
    - weak: > 12°
    """

    @pytest.mark.parametrize(
        "lagna_deg,planet_deg,expected_band",
        [
            # dist=0   -> very_strong (≤ 3°)
            (10.0, 10.0, "very_strong"),
            # dist=3   -> very_strong (boundary; ≤ 3°)
            (10.0, 13.0, "very_strong"),
            # dist=3.001 -> strong (just past the very_strong cutoff)
            (10.0, 13.001, "strong"),
            # dist=5   -> strong (≤ 8°)
            (10.0, 15.0, "strong"),
            # dist=8   -> strong (boundary; ≤ 8°)
            (10.0, 18.0, "strong"),
            # dist=8.001 -> moderate (just past the strong cutoff)
            (10.0, 18.001, "moderate"),
            # dist=10  -> moderate (≤ 12°)
            (10.0, 20.0, "moderate"),
            # dist=12  -> moderate (boundary; ≤ 12°)
            (10.0, 22.0, "moderate"),
            # dist=12.001 -> weak (just past the moderate cutoff)
            (10.0, 22.001, "weak"),
            # dist=15  -> weak (sandhi)
            (10.0, 25.0, "weak"),
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
