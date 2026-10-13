"""Natal chart assembly: canonical pins, honest nulls, deterministic scoring.

The epistemic point: ``assemble_chart`` is pure plumbing over the already-
pinned ``western`` toolkit, so what needs testing here is the *assembly
honesty* — that missing houses are recorded with the right reason and never
substituted, that unknown-time births are cast at noon with the Moon's
ambiguity measured, and that the chart-level derivations (balance, ruler,
dominants) follow their documented arithmetic exactly.
"""

from __future__ import annotations

from app.empirical.natal.chart import (
    ASCENDANT_WEIGHT,
    BALANCE_WEIGHTS,
    BirthMoment,
    REASON_POLAR,
    REASON_TIME_UNKNOWN,
    TRAIT_PLANETS,
    assemble_chart,
)
from app.empirical.natal.lexicon import SIGN_RULERS, SIGNS
from app.empirical.western.tropical import DEFAULT_BODIES, julian_day_ut

#: The canonical baseline birth: Bangalore 1990-07-15 12:00 IST.
CANONICAL = BirthMoment(1990, 7, 15, 12, 0, 12.97, 77.59, 5.5)

#: High-arctic latitude where quadrant house systems are undefined.
SVALBARD = BirthMoment(1990, 7, 15, 12, 0, 78.0, 15.6, 1.0)


class TestCanonicalChart:
    """Pins against externally verifiable facts of the canonical birth."""

    def test_hour_ut_subtracts_the_offset(self):
        """12:00 IST is 06:30 UT — the same conversion the western tests pin."""
        assert CANONICAL.hour_ut == 6.5

    def test_sun_in_cancer(self):
        """Mid-July Sun is tropically in Cancer (it enters Leo ~July 22)."""
        chart = assemble_chart(CANONICAL)
        assert SIGNS[chart.positions["Sun"].sign_index] == "Cancer"

    def test_houses_present_with_no_missing_reason(self):
        """At tropical latitudes Placidus is defined, so houses must exist."""
        chart = assemble_chart(CANONICAL)
        assert chart.houses is not None
        assert chart.houses_missing_reason is None

    def test_chart_ruler_is_the_modern_ruler_of_the_rising_sign(self):
        """chart_ruler must equal SIGN_RULERS applied to the ascendant's sign."""
        chart = assemble_chart(CANONICAL)
        asc_sign = SIGNS[int(chart.houses.ascendant // 30.0)]
        assert chart.chart_ruler == SIGN_RULERS[asc_sign]

    def test_house_of_body_covers_every_default_body(self):
        """Every computed body gets a house assignment in 1..12."""
        chart = assemble_chart(CANONICAL)
        assert set(chart.house_of_body) == set(DEFAULT_BODIES)
        assert all(1 <= h <= 12 for h in chart.house_of_body.values())

    def test_all_positions_and_derived_points_present(self):
        """positions carries all DEFAULT_BODIES and the south node opposes the true node."""
        chart = assemble_chart(CANONICAL)
        assert set(chart.positions) == set(DEFAULT_BODIES)
        diff = abs(chart.south_node - chart.positions["TrueNode"].longitude) % 360.0
        assert abs(min(diff, 360.0 - diff) - 180.0) < 1e-9


class TestHonestNulls:
    """Missing houses carry a reason and are never silently substituted."""

    def test_polar_placidus_yields_none_with_polar_reason(self):
        """Placidus is undefined at 78°N: houses None, reason polar_latitude."""
        chart = assemble_chart(SVALBARD, house_system="placidus")
        assert chart.houses is None
        assert chart.houses_missing_reason == REASON_POLAR
        assert chart.house_of_body is None
        assert chart.chart_ruler is None

    def test_polar_whole_sign_stays_defined(self):
        """Whole-sign never references the horizon, so it works at any latitude."""
        chart = assemble_chart(SVALBARD, house_system="whole_sign")
        assert chart.houses is not None
        assert chart.houses_missing_reason is None

    def test_unknown_time_omits_houses_with_time_reason(self):
        """No birth time → houses never computed, reason birth_time_unknown."""
        moment = BirthMoment(1990, 7, 15, 0, 0, 12.97, 77.59, 5.5, time_known=False)
        chart = assemble_chart(moment)
        assert chart.houses is None
        assert chart.houses_missing_reason == REASON_TIME_UNKNOWN
        assert chart.house_of_body is None

    def test_unknown_time_casts_at_local_noon(self):
        """The stated hour is ignored for unknown-time births; noon is used."""
        moment = BirthMoment(1990, 7, 15, 3, 30, 12.97, 77.59, 5.5, time_known=False)
        chart = assemble_chart(moment)
        assert chart.jd_ut == julian_day_ut(1990, 7, 15, 12.0 - 5.5)

    def test_known_time_never_flags_moon_ambiguity(self):
        """A stated birth time pins the Moon; the flag is for unknown time only."""
        assert assemble_chart(CANONICAL).moon_sign_ambiguous is False

    def test_moon_ambiguity_varies_across_a_lunar_fortnight(self):
        """The Moon changes sign roughly every 2.5 days, so a 5-day scan of
        unknown-time births must contain both ambiguous and unambiguous days."""
        flags = []
        for day in range(14, 19):
            moment = BirthMoment(1990, 7, day, 0, 0, 12.97, 77.59, 5.5, time_known=False)
            flags.append(assemble_chart(moment).moon_sign_ambiguous)
        assert any(flags) and not all(flags)


class TestDerivations:
    """The documented balance and dominance arithmetic, re-derived independently."""

    def test_element_counts_follow_the_documented_weights(self):
        """Recompute the weighted tallies from positions; must match exactly."""
        chart = assemble_chart(CANONICAL)
        elements = {"fire": 0, "earth": 0, "air": 0, "water": 0}
        keys = ("fire", "earth", "air", "water")
        for body, weight in BALANCE_WEIGHTS.items():
            elements[keys[chart.positions[body].sign_index % 4]] += weight
        asc_idx = int(chart.houses.ascendant // 30.0)
        elements[keys[asc_idx % 4]] += ASCENDANT_WEIGHT
        assert dict(chart.element_counts) == elements

    def test_balance_total_is_weight_sum_plus_ascendant(self):
        """Tallies conserve mass: sum equals the fixed weight budget."""
        chart = assemble_chart(CANONICAL)
        budget = sum(BALANCE_WEIGHTS.values()) + ASCENDANT_WEIGHT
        assert sum(chart.element_counts.values()) == budget
        assert sum(chart.modality_counts.values()) == budget

    def test_houseless_balance_excludes_the_ascendant(self):
        """Without houses there is no ascendant to weigh — budget shrinks by it."""
        chart = assemble_chart(SVALBARD, house_system="placidus")
        assert sum(chart.element_counts.values()) == sum(BALANCE_WEIGHTS.values())

    def test_dominant_planets_deterministic_and_trait_only(self):
        """Two assemblies agree exactly; dominants come from the ten trait planets."""
        a = assemble_chart(CANONICAL)
        b = assemble_chart(CANONICAL)
        assert a.dominant_planets == b.dominant_planets
        assert len(a.dominant_planets) == 3
        assert set(a.dominant_planets) <= set(TRAIT_PLANETS)

    def test_aspects_are_ptolemaic_only(self):
        """The chart carries only the five classical aspect names."""
        chart = assemble_chart(CANONICAL)
        allowed = {"conjunction", "sextile", "square", "trine", "opposition"}
        assert {a.aspect for a in chart.aspects} <= allowed
