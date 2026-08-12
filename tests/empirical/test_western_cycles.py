"""Progressions, returns, and transits — the time-varying layer.

These are pinned by structural properties that must hold by construction:
a progressed chart at age zero *is* the natal chart; a return chart's body *is*
on its natal degree. A violation of either is a bug no amount of plausible
output can hide.
"""

from __future__ import annotations

import pytest

from app.empirical.western.angles import separation
from app.empirical.western.aspects import PTOLEMAIC, AspectDef
from app.empirical.western.progressions import (
    JULIAN_YEAR_DAYS,
    TROPICAL_YEAR_DAYS,
    progressed_solar_arc,
    secondary_progressed_jd,
    solar_arc,
    solar_arc_directed,
)
from app.empirical.western.returns import (
    ReturnNotFoundError,
    find_return,
    lunar_return,
    solar_return,
)
from app.empirical.western.transits import aspect_targets, transit_hits
from app.empirical.western.tropical import julian_day_ut, tropical_position, tropical_positions

CANONICAL_JD = julian_day_ut(1990, 7, 15, 12.0 - 5.5)
_ARCSEC = 1.0 / 3600.0


class TestSecondaryProgressions:
    """Day-for-year, with the year length an explicit parameter."""

    def test_progressed_chart_at_age_zero_is_the_natal_chart(self):
        """The defining property: zero elapsed time, zero progression."""
        assert secondary_progressed_jd(CANONICAL_JD, CANONICAL_JD) == CANONICAL_JD

    def test_one_year_of_life_advances_one_day_of_ephemeris(self):
        """A year after birth, the progressed chart is one day after birth."""
        target = CANONICAL_JD + TROPICAL_YEAR_DAYS
        progressed = secondary_progressed_jd(CANONICAL_JD, target)
        assert progressed == pytest.approx(CANONICAL_JD + 1.0, abs=1e-9)

    def test_thirty_years_advances_thirty_days(self):
        """Linear in elapsed time; no accumulating drift."""
        target = CANONICAL_JD + 30 * TROPICAL_YEAR_DAYS
        progressed = secondary_progressed_jd(CANONICAL_JD, target)
        assert progressed == pytest.approx(CANONICAL_JD + 30.0, abs=1e-9)

    def test_converse_progression_runs_backwards(self):
        """Negative elapsed time needs no special case."""
        target = CANONICAL_JD - 10 * TROPICAL_YEAR_DAYS
        progressed = secondary_progressed_jd(CANONICAL_JD, target)
        assert progressed == pytest.approx(CANONICAL_JD - 10.0, abs=1e-9)

    def test_year_length_choice_is_material(self):
        """Tropical vs Julian year differ measurably over a lifetime.

        Documents why the constant is a parameter rather than a literal: over
        85 years the two conventions disagree by enough progressed motion to
        matter, so the choice belongs in a pre-registration row.
        """
        target = CANONICAL_JD + 85 * 365.25
        tropical = secondary_progressed_jd(CANONICAL_JD, target, year_days=TROPICAL_YEAR_DAYS)
        julian = secondary_progressed_jd(CANONICAL_JD, target, year_days=JULIAN_YEAR_DAYS)
        assert abs(tropical - julian) > 1e-3

    def test_does_not_reuse_the_vedic_year_constant(self):
        """365.2425 is locked to Vimshottari; the tropical default is distinct."""
        assert TROPICAL_YEAR_DAYS != 365.2425

    def test_nonpositive_year_length_rejected(self):
        """A zero or negative year is not a convention, it is a bug."""
        with pytest.raises(ValueError):
            secondary_progressed_jd(CANONICAL_JD, CANONICAL_JD + 1.0, year_days=0.0)


class TestSolarArc:
    """The arc is forward motion, not a shortest-signed delta."""

    def test_arc_is_zero_at_birth(self):
        """No elapsed time, no arc."""
        assert solar_arc(100.0, 100.0) == 0.0

    def test_arc_is_forward_and_wraps_correctly(self):
        """A Sun that has crossed 0° Aries still shows a positive forward arc."""
        assert solar_arc(350.0, 10.0) == pytest.approx(20.0)

    def test_directed_chart_at_zero_arc_equals_natal(self):
        """Rigid direction by a zero arc is the identity."""
        positions = tropical_positions(CANONICAL_JD)
        directed = solar_arc_directed(positions, 0.0)
        for name, pos in positions.items():
            assert directed[name] == pytest.approx(pos.longitude)

    def test_direction_moves_every_body_by_the_same_arc(self):
        """Solar arc is rigid: relative aspects are preserved exactly."""
        positions = tropical_positions(CANONICAL_JD)
        directed = solar_arc_directed(positions, 30.0)
        for name, pos in positions.items():
            assert separation(directed[name], pos.longitude) == pytest.approx(30.0)

    def test_progressed_solar_arc_grows_about_one_degree_per_year(self):
        """The Sun advances ~0.986°/day, so ~1° per progressed year of life."""
        natal_sun = tropical_position(CANONICAL_JD, "Sun").longitude
        arc = progressed_solar_arc(CANONICAL_JD, CANONICAL_JD + 30 * TROPICAL_YEAR_DAYS, natal_sun)
        assert 28.0 < arc < 31.0, f"30-year solar arc was {arc}°"


class TestReturns:
    """A return chart is only a return if the body is exactly on its degree."""

    def test_solar_return_puts_the_sun_on_its_natal_degree(self):
        """Sub-arcsecond, because the ascendant moves 15° per hour."""
        natal_sun = tropical_position(CANONICAL_JD, "Sun").longitude
        jd = solar_return(natal_sun, CANONICAL_JD + 300.0)
        actual = tropical_position(jd, "Sun").longitude
        assert separation(actual, natal_sun) < _ARCSEC

    def test_solar_return_lands_about_one_year_later(self):
        """The first return after a 300-day offset is within days of the anniversary."""
        natal_sun = tropical_position(CANONICAL_JD, "Sun").longitude
        jd = solar_return(natal_sun, CANONICAL_JD + 300.0)
        assert 360.0 < (jd - CANONICAL_JD) < 371.0

    def test_lunar_return_puts_the_moon_on_its_natal_degree(self):
        """Same contract for the fast body."""
        natal_moon = tropical_position(CANONICAL_JD, "Moon").longitude
        jd = lunar_return(natal_moon, CANONICAL_JD + 5.0)
        actual = tropical_position(jd, "Moon").longitude
        assert separation(actual, natal_moon) < _ARCSEC

    def test_lunar_return_lands_within_one_sidereal_month(self):
        """Searching from birth + 5 days finds the return ~27.3 days out."""
        natal_moon = tropical_position(CANONICAL_JD, "Moon").longitude
        jd = lunar_return(natal_moon, CANONICAL_JD + 5.0)
        assert 25.0 < (jd - CANONICAL_JD) < 30.0

    def test_successive_solar_returns_are_a_year_apart(self):
        """Chaining returns does not drift."""
        natal_sun = tropical_position(CANONICAL_JD, "Sun").longitude
        first = solar_return(natal_sun, CANONICAL_JD + 300.0)
        second = solar_return(natal_sun, first + 10.0)
        assert 364.0 < (second - first) < 367.0

    def test_retrograding_body_is_rejected(self):
        """Bracket-and-bisect is only sound for monotonic longitude."""
        with pytest.raises(KeyError, match="monotonic"):
            find_return(100.0, CANONICAL_JD, "Mars")

    def test_no_crossing_in_span_raises(self):
        """A search span too short to contain a return fails loudly."""
        natal_sun = tropical_position(CANONICAL_JD, "Sun").longitude
        with pytest.raises(ReturnNotFoundError):
            find_return(natal_sun, CANONICAL_JD + 10.0, "Sun", max_cycles=0.01)


class TestTransits:
    """Exact hits, both aspect targets, and orb windows."""

    def test_non_symmetric_aspects_have_two_targets(self):
        """A square perfects at natal+90 and natal-90 — both must be searched."""
        assert len(aspect_targets(100.0, 90.0)) == 2
        assert set(aspect_targets(100.0, 90.0)) == {190.0, 10.0}

    def test_conjunction_and_opposition_have_one_target(self):
        """0° and 180° are self-symmetric on the circle."""
        assert aspect_targets(100.0, 0.0) == (100.0,)
        assert aspect_targets(100.0, 180.0) == (280.0,)

    def test_sun_conjunction_occurs_once_a_year(self):
        """The Sun conjoins a fixed degree exactly once per orbit."""
        hits = transit_hits(
            100.0, "Sun", CANONICAL_JD, CANONICAL_JD + 365.0,
            aspects=(AspectDef("conjunction", 0.0),), orb=1.0,
        )
        assert len(hits) == 1

    def test_exact_hit_places_body_on_target(self):
        """At exact_jd the transiting body is on the target degree."""
        hits = transit_hits(
            100.0, "Sun", CANONICAL_JD, CANONICAL_JD + 365.0,
            aspects=(AspectDef("conjunction", 0.0),), orb=1.0,
        )
        actual = tropical_position(hits[0].exact_jd, "Sun").longitude
        assert separation(actual, 100.0) < 1e-4

    def test_orb_window_brackets_the_exact_hit(self):
        """Entry precedes perfection precedes exit."""
        hits = transit_hits(
            100.0, "Sun", CANONICAL_JD, CANONICAL_JD + 365.0,
            aspects=(AspectDef("conjunction", 0.0),), orb=1.0,
        )
        hit = hits[0]
        assert hit.enter_jd is not None and hit.exit_jd is not None
        assert hit.enter_jd < hit.exact_jd < hit.exit_jd

    def test_orb_window_edges_sit_at_the_orb(self):
        """Entry and exit are where separation equals the orb, not near it."""
        hits = transit_hits(
            100.0, "Sun", CANONICAL_JD, CANONICAL_JD + 365.0,
            aspects=(AspectDef("conjunction", 0.0),), orb=1.0,
        )
        hit = hits[0]
        for edge in (hit.enter_jd, hit.exit_jd):
            lon = tropical_position(edge, "Sun").longitude
            assert separation(lon, hit.target_longitude) == pytest.approx(1.0, abs=1e-4)

    def test_moon_conjoins_a_degree_about_thirteen_times_a_year(self):
        """The fast body's default step must not skip crossings."""
        hits = transit_hits(
            100.0, "Moon", CANONICAL_JD, CANONICAL_JD + 365.0,
            aspects=(AspectDef("conjunction", 0.0),), orb=1.0,
        )
        assert 12 <= len(hits) <= 14, f"got {len(hits)} lunar conjunctions"

    def test_squares_return_hits_on_both_sides(self):
        """Over a full solar year both square targets are perfected."""
        hits = transit_hits(
            100.0, "Sun", CANONICAL_JD, CANONICAL_JD + 365.0,
            aspects=(AspectDef("square", 90.0),), orb=1.0,
        )
        assert len({h.target_longitude for h in hits}) == 2

    def test_hits_are_sorted_by_time(self):
        """Callers consume these as a timeline."""
        hits = transit_hits(
            100.0, "Sun", CANONICAL_JD, CANONICAL_JD + 365.0,
            aspects=PTOLEMAIC, orb=1.0,
        )
        assert [h.exact_jd for h in hits] == sorted(h.exact_jd for h in hits)

    def test_invalid_window_rejected(self):
        """An end before the start is a caller bug."""
        with pytest.raises(ValueError):
            transit_hits(100.0, "Sun", CANONICAL_JD, CANONICAL_JD - 1.0)

    def test_nonpositive_orb_rejected(self):
        """A zero orb has no window to measure."""
        with pytest.raises(ValueError):
            transit_hits(100.0, "Sun", CANONICAL_JD, CANONICAL_JD + 10.0, orb=0.0)
