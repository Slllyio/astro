"""Midpoints and harmonics — the pure-arithmetic layer.

No ephemeris calls, so these are pinned entirely by algebraic properties:
symmetry, idempotence, and the identity transforms (``midpoint(a, a) == a``,
``harmonic(x, 1) == x``).
"""

from __future__ import annotations

import pytest

from app.empirical.western.angles import separation
from app.empirical.western.harmonics import harmonic, harmonic_chart, harmonic_conjunctions
from app.empirical.western.midpoints import (
    midpoint,
    midpoint_tree,
    midpoints_near,
    opposite_midpoint,
)
from app.empirical.western.tropical import Position, julian_day_ut, tropical_positions

CANONICAL_JD = julian_day_ut(1990, 7, 15, 12.0 - 5.5)


def _pos(name: str, lon: float) -> Position:
    return Position(name, lon, 0.0, 1.0, 1.0, 0.0)


class TestMidpointArithmetic:
    """Circular midpoints, including across the Aries point."""

    def test_midpoint_of_a_point_with_itself_is_itself(self):
        """Idempotence — the degenerate case must not drift."""
        assert midpoint(123.456, 123.456) == pytest.approx(123.456)

    def test_midpoint_is_symmetric(self):
        """Order of arguments cannot matter on a circle."""
        assert midpoint(10.0, 50.0) == pytest.approx(midpoint(50.0, 10.0))

    def test_midpoint_takes_the_short_arc(self):
        """350° and 10° meet at 0°, not at 180°."""
        assert midpoint(350.0, 10.0) == pytest.approx(0.0)

    def test_simple_midpoint_is_the_average(self):
        """Away from the seam it reduces to the arithmetic mean."""
        assert midpoint(10.0, 50.0) == pytest.approx(30.0)

    def test_opposite_midpoint_is_180_from_the_near_one(self):
        """The far end of the axis, by definition."""
        near, far = midpoint(10.0, 50.0), opposite_midpoint(10.0, 50.0)
        assert separation(near, far) == pytest.approx(180.0)


class TestMidpointTree:
    """Pairwise coverage and activation."""

    def test_tree_has_one_entry_per_unordered_pair(self):
        """n bodies give n(n-1)/2 midpoints — 55 for the default eleven."""
        positions = tropical_positions(CANONICAL_JD)
        tree = midpoint_tree(positions)
        n = len(positions)
        assert len(tree) == n * (n - 1) // 2

    def test_unknown_body_raises(self):
        """A missing body is an error, never a silently smaller tree."""
        with pytest.raises(KeyError):
            midpoint_tree({"A": _pos("A", 0.0)}, bodies=["A", "Nope"])

    def test_point_on_the_midpoint_is_a_hit(self):
        """The obvious case: a point sitting exactly on the axis."""
        tree = {("A", "B"): 30.0}
        hits = midpoints_near(tree, 30.0, orb=1.0)
        assert len(hits) == 1
        assert hits[0].orb == pytest.approx(0.0)
        assert hits[0].on_far_side is False

    def test_point_on_the_far_end_is_still_on_the_axis(self):
        """Ebertin counts both ends; the hit is flagged, not discarded."""
        tree = {("A", "B"): 30.0}
        hits = midpoints_near(tree, 210.0, orb=1.0)
        assert len(hits) == 1
        assert hits[0].on_far_side is True

    def test_point_outside_orb_is_not_a_hit(self):
        """Orb gating is real."""
        assert midpoints_near({("A", "B"): 30.0}, 45.0, orb=1.0) == []

    def test_nonpositive_orb_rejected(self):
        """A zero-width orb admits nothing and is surely a caller bug."""
        with pytest.raises(ValueError):
            midpoints_near({("A", "B"): 30.0}, 30.0, orb=0.0)


class TestHarmonics:
    """Addey's longitude × n."""

    def test_first_harmonic_is_the_radix(self):
        """The defining identity."""
        positions = tropical_positions(CANONICAL_JD)
        chart = harmonic_chart(positions, 1)
        for name, pos in positions.items():
            assert chart[name] == pytest.approx(pos.longitude)

    def test_harmonic_multiplies_and_wraps(self):
        """100° in the fourth harmonic is 400° mod 360 = 40°."""
        assert harmonic(100.0, 4) == pytest.approx(40.0)

    def test_trine_becomes_conjunction_in_the_third_harmonic(self):
        """A 120° radix aspect maps to 0° in H3 — the point of harmonics."""
        chart = harmonic_chart({"A": _pos("A", 10.0), "B": _pos("B", 130.0)}, 3)
        assert separation(chart["A"], chart["B"]) < 1e-9

    def test_quintile_becomes_conjunction_in_the_fifth_harmonic(self):
        """72° maps to 0° in H5."""
        chart = harmonic_chart({"A": _pos("A", 10.0), "B": _pos("B", 82.0)}, 5)
        assert separation(chart["A"], chart["B"]) < 1e-9

    def test_harmonic_zero_or_negative_rejected(self):
        """There is no zeroth harmonic."""
        with pytest.raises(ValueError):
            harmonic(100.0, 0)
        with pytest.raises(ValueError):
            harmonic(100.0, -3)

    def test_unknown_body_raises(self):
        """Consistent with the rest of the toolkit: no silent drops."""
        with pytest.raises(KeyError):
            harmonic_chart({"A": _pos("A", 0.0)}, 5, bodies=["A", "Nope"])

    def test_harmonic_conjunctions_finds_the_pair(self):
        """The H3 conjunction of a radix trine is reported."""
        chart = harmonic_chart({"A": _pos("A", 10.0), "B": _pos("B", 130.0)}, 3)
        pairs = harmonic_conjunctions(chart, orb=1.0)
        assert len(pairs) == 1
        assert pairs[0][:2] == ("A", "B")

    def test_harmonic_conjunctions_sorted_tightest_first(self):
        """Consumers read the strongest pairing first."""
        chart = {"A": 0.0, "B": 4.0, "C": 1.0}
        pairs = harmonic_conjunctions(chart, orb=6.0)
        assert [p[2] for p in pairs] == sorted(p[2] for p in pairs)
