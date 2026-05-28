"""Tests for ``app.reading.computations.rookie_guards``.

Doctrine source: practitioner-craft invariants. These are not rules about
the chart; they are rules about *how a reading is constructed*. Each
guard catches a class of rookie mistake that the engine could otherwise
emit silently:

1. Marriage timing predicted without D9 dispositor agreement.
2. Yoga claimed "Raja" but participating planets weak/combust/in trika.
3. Health prediction without lagna-lord context evidence.
4. Career direction predicted with only 1 of 5 pillars confirming.

A guard fires by emitting a Finding (id pattern
``practitioner.rookie_guards.<rule_name>``, classification ``affliction``,
direction ``negative``). An empty list means no violations detected.

The shape of the input is the partially-built reading dict so this guard
can run *after* the other Tier-2 modules but *before* the reading is
sealed.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _empty_reading() -> dict:
    return {
        "marriage": {},
        "yogas": [],
        "health": {},
        "career": {},
    }


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestShape:

    def test_returns_list(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        result = check_rookie_invariants(_empty_reading())
        assert isinstance(result, list)

    def test_empty_reading_yields_no_findings(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        result = check_rookie_invariants(_empty_reading())
        assert result == []


# ---------------------------------------------------------------------------
# Guard 1: marriage timing without D9 dispositor agreement.
# ---------------------------------------------------------------------------


class TestMarriageGuard:

    def test_marriage_timing_without_d9_dispositor_fires(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["marriage"] = {
            "predicted_window": "2030-2032",
            # missing 'd9_dispositor_confirmation'
        }
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.marriage_no_d9_dispositor" in ids

    def test_marriage_timing_with_d9_dispositor_does_not_fire(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["marriage"] = {
            "predicted_window": "2030-2032",
            "d9_dispositor_confirmation": True,
        }
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.marriage_no_d9_dispositor" not in ids

    def test_marriage_without_prediction_does_not_fire(self):
        """If the engine declined to predict marriage timing at all, the
        guard should stay silent (the precondition is the prediction)."""
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["marriage"] = {}  # no predicted_window
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.marriage_no_d9_dispositor" not in ids


# ---------------------------------------------------------------------------
# Guard 2: weak Raja yoga.
# ---------------------------------------------------------------------------


class TestRajaYogaGuard:

    def test_raja_yoga_with_weak_planets_fires(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["yogas"] = [
            {
                "name": "Some Raja Yoga",
                "participating_planets": ["Jupiter", "Venus"],
                "participating_planet_states": {
                    "Jupiter": {"combust": True, "in_trika": False, "weak": True},
                    "Venus":   {"combust": False, "in_trika": True, "weak": False},
                },
            },
        ]
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.raja_yoga_weak_participants" in ids

    def test_raja_yoga_with_strong_participants_does_not_fire(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["yogas"] = [
            {
                "name": "Gajakesari Raja Yoga",
                "participating_planets": ["Jupiter", "Moon"],
                "participating_planet_states": {
                    "Jupiter": {"combust": False, "in_trika": False, "weak": False},
                    "Moon":    {"combust": False, "in_trika": False, "weak": False},
                },
            },
        ]
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.raja_yoga_weak_participants" not in ids

    def test_non_raja_yoga_ignored(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["yogas"] = [
            {
                "name": "Daridra Yoga",  # not a Raja yoga
                "participating_planets": ["Saturn"],
                "participating_planet_states": {
                    "Saturn": {"combust": True, "in_trika": True, "weak": True},
                },
            },
        ]
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.raja_yoga_weak_participants" not in ids


# ---------------------------------------------------------------------------
# Guard 3: health prediction without lagna-lord context.
# ---------------------------------------------------------------------------


class TestHealthGuard:

    def test_health_prediction_without_lagna_lord_fires(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["health"] = {
            "verdict": "good vitality",
            # missing lagna_lord_context
        }
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.health_no_lagna_lord_context" in ids

    def test_health_prediction_with_lagna_lord_does_not_fire(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["health"] = {
            "verdict": "good vitality",
            "lagna_lord_context": "Lagna lord Mercury in 11th, exalted, supports vitality",
        }
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.health_no_lagna_lord_context" not in ids


# ---------------------------------------------------------------------------
# Guard 4: career direction with only 1 of 5 pillars confirming.
# ---------------------------------------------------------------------------


class TestCareerGuard:

    def test_career_with_one_pillar_fires(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["career"] = {
            "direction": "engineering",
            "pillar_confirmations": {
                "D1_10H": True,
                "D10_lagna": False,
                "AmK": False,
                "Sun_placement": False,
                "Saturn_role": False,
            },
        }
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.career_thin_evidence" in ids

    def test_career_with_three_pillars_does_not_fire(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        reading["career"] = {
            "direction": "engineering",
            "pillar_confirmations": {
                "D1_10H": True,
                "D10_lagna": True,
                "AmK": True,
                "Sun_placement": False,
                "Saturn_role": False,
            },
        }
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.career_thin_evidence" not in ids

    def test_career_without_direction_ignored(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        reading = _empty_reading()
        # No 'direction' key -> nothing to guard.
        result = check_rookie_invariants(reading)
        ids = {f.id for f in result}
        assert "practitioner.rookie_guards.career_thin_evidence" not in ids


# ---------------------------------------------------------------------------
# Finding contract on emitted guards.
# ---------------------------------------------------------------------------


class TestFindingContract:

    def test_all_findings_are_affliction_negative(self):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        # Build a reading that violates every guard.
        reading = {
            "marriage": {"predicted_window": "2030"},
            "yogas": [
                {
                    "name": "Some Raja Yoga",
                    "participating_planets": ["Saturn"],
                    "participating_planet_states": {
                        "Saturn": {"combust": True, "in_trika": True, "weak": True},
                    },
                },
            ],
            "health": {"verdict": "robust"},
            "career": {
                "direction": "art",
                "pillar_confirmations": {
                    "D1_10H": True,
                    "D10_lagna": False,
                    "AmK": False,
                    "Sun_placement": False,
                    "Saturn_role": False,
                },
            },
        }
        findings = check_rookie_invariants(reading)
        assert len(findings) >= 4
        for f in findings:
            assert f.classification == "affliction"
            assert f.direction == "negative"
            assert f.id.startswith("practitioner.rookie_guards.")
            assert len(f.verdict) <= 140
            assert "warning" in f.verdict.lower()


# ---------------------------------------------------------------------------
# Property: never raises.
# ---------------------------------------------------------------------------


class TestPropertyRobust:

    @pytest.mark.parametrize("bad_input", [
        {},
        {"marriage": None},
        {"yogas": None},
        {"health": None},
        {"career": None},
    ])
    def test_robust_to_partial_inputs(self, bad_input):
        from app.reading.computations.rookie_guards import (
            check_rookie_invariants,
        )

        # Should not raise, regardless of partial / None values.
        result = check_rookie_invariants(bad_input)
        assert isinstance(result, list)
