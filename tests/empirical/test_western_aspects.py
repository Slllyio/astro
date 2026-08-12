"""Aspect detection, orb-table fingerprinting, and applying/separating polarity.

Applying/separating is asserted against hand-constructed positions with known
speeds rather than against a real chart, because the point under test is the
sign of a derivative — a real chart would let a wrong sign hide behind a
plausible-looking output.
"""

from __future__ import annotations

import pytest

from app.empirical.western.aspects import (
    DEFAULT_ORBS,
    MINOR,
    PTOLEMAIC,
    AspectDef,
    OrbTable,
    find_aspects,
)
from app.empirical.western.tropical import Position


def _pos(name: str, lon: float, speed: float) -> Position:
    return Position(name, lon, 0.0, 1.0, speed, 0.0)


class TestOrbTable:
    """The orb table is pre-registration data, so its identity must be stable."""

    def test_fingerprint_is_stable_across_construction_order(self):
        """Two tables with the same content hash identically."""
        a = OrbTable(per_aspect={"square": 7.0, "trine": 7.0}, luminary_bonus=2.0)
        b = OrbTable(per_aspect={"trine": 7.0, "square": 7.0}, luminary_bonus=2.0)
        assert a.fingerprint() == b.fingerprint()

    def test_fingerprint_changes_when_an_orb_changes(self):
        """Widening an orb invalidates the registration."""
        a = OrbTable(per_aspect={"square": 7.0})
        b = OrbTable(per_aspect={"square": 8.0})
        assert a.fingerprint() != b.fingerprint()

    def test_fingerprint_changes_when_luminary_bonus_changes(self):
        """The luminary widening is part of the registered identity."""
        a = OrbTable(per_aspect={"square": 7.0}, luminary_bonus=0.0)
        b = OrbTable(per_aspect={"square": 7.0}, luminary_bonus=2.0)
        assert a.fingerprint() != b.fingerprint()

    def test_unlisted_aspect_is_not_tested(self):
        """An aspect absent from the table returns None — do not test it."""
        table = OrbTable(per_aspect={"square": 7.0})
        assert table.orb_for("trine", "Mars", "Venus") is None

    def test_luminary_bonus_widens_only_for_lights(self):
        """Sun/Moon get the wider orb; other pairs do not."""
        table = OrbTable(per_aspect={"square": 7.0}, luminary_bonus=2.0)
        assert table.orb_for("square", "Sun", "Mars") == 9.0
        assert table.orb_for("square", "Mars", "Venus") == 7.0


class TestAspectDetection:
    """Orb gating, cusp safety, and pair coverage."""

    def test_conjunction_across_zero_aries_is_detected(self):
        """358° and 3° are 5° apart, not 355° — the circular-distance trap."""
        positions = {"A": _pos("A", 358.0, 1.0), "B": _pos("B", 3.0, 0.5)}
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"conjunction": 8.0}))
        assert len(hits) == 1
        assert hits[0].aspect == "conjunction"
        assert hits[0].orb == pytest.approx(5.0)

    def test_aspect_outside_orb_is_rejected(self):
        """A 10° separation does not qualify under an 8° conjunction orb."""
        positions = {"A": _pos("A", 0.0, 1.0), "B": _pos("B", 10.0, 0.5)}
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"conjunction": 8.0}))
        assert hits == []

    def test_each_pair_reported_once_per_aspect(self):
        """Three bodies mutually in trine give three hits, not six."""
        positions = {
            "A": _pos("A", 0.0, 1.0),
            "B": _pos("B", 120.0, 1.0),
            "C": _pos("C", 240.0, 1.0),
        }
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"trine": 7.0}))
        assert len(hits) == 3

    def test_hits_sorted_tightest_first(self):
        """Ordering by orb makes the strongest aspect the first element."""
        positions = {
            "A": _pos("A", 0.0, 1.0),
            "B": _pos("B", 4.0, 1.0),
            "C": _pos("C", 1.0, 1.0),
        }
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"conjunction": 8.0}))
        assert [h.orb for h in hits] == sorted(h.orb for h in hits)

    def test_unknown_body_raises(self):
        """A missing body is an error, never a silent drop."""
        with pytest.raises(KeyError):
            find_aspects({"A": _pos("A", 0.0, 1.0)}, bodies=["A", "Nope"])

    def test_minor_aspects_are_opt_in(self):
        """MINOR is not part of PTOLEMAIC — each added aspect enlarges the family."""
        assert not set(a.name for a in MINOR) & set(a.name for a in PTOLEMAIC)


class TestApplyingSeparating:
    """The sign of d|separation|/dt, checked against constructed velocities."""

    def test_faster_body_behind_is_applying_to_conjunction(self):
        """A at 0° moving 2°/day closes on B at 5° moving 1°/day."""
        positions = {"A": _pos("A", 0.0, 2.0), "B": _pos("B", 5.0, 1.0)}
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"conjunction": 8.0}))
        assert hits[0].applying is True

    def test_faster_body_ahead_is_separating_from_conjunction(self):
        """A at 5° moving 2°/day pulls away from B at 0° moving 1°/day."""
        positions = {"A": _pos("A", 5.0, 2.0), "B": _pos("B", 0.0, 1.0)}
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"conjunction": 8.0}))
        assert hits[0].applying is False

    def test_retrograde_body_can_apply_backwards(self):
        """A retrograde body closing on a slower one is applying."""
        positions = {"A": _pos("A", 10.0, -0.5), "B": _pos("B", 5.0, 0.0)}
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"conjunction": 8.0}))
        assert hits[0].applying is True

    def test_wide_side_of_opposition_applies_when_closing(self):
        """Past-180 separation closes toward exactness when the gap narrows."""
        # Separation 175°, B gaining on A widens it toward 180°.
        positions = {"A": _pos("A", 0.0, 0.0), "B": _pos("B", 175.0, 1.0)}
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"opposition": 8.0}))
        assert hits[0].applying is True

    def test_equal_speeds_give_indeterminate_polarity(self):
        """Bodies locked at the same speed are neither applying nor separating."""
        positions = {"A": _pos("A", 0.0, 1.0), "B": _pos("B", 5.0, 1.0)}
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"conjunction": 8.0}))
        assert hits[0].applying is None

    def test_exact_aspect_has_no_polarity(self):
        """At exactness there is nothing to apply to."""
        positions = {"A": _pos("A", 0.0, 1.0), "B": _pos("B", 90.0, 0.5)}
        hits = find_aspects(positions, orbs=OrbTable(per_aspect={"square": 7.0}))
        assert hits[0].orb == pytest.approx(0.0)
        assert hits[0].applying is None


class TestDefaultOrbs:
    """The shipped default is conservative and complete over PTOLEMAIC."""

    def test_default_covers_every_ptolemaic_aspect(self):
        """No Ptolemaic aspect is silently untested under the default table."""
        for adef in PTOLEMAIC:
            assert DEFAULT_ORBS.orb_for(adef.name, "Mars", "Venus") is not None

    def test_custom_aspect_set_is_respected(self):
        """Callers may register their own aspect definitions."""
        positions = {"A": _pos("A", 0.0, 1.0), "B": _pos("B", 45.0, 0.5)}
        hits = find_aspects(
            positions,
            orbs=OrbTable(per_aspect={"semisquare": 2.0}),
            aspects=(AspectDef("semisquare", 45.0),),
        )
        assert len(hits) == 1
