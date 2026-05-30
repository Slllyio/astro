"""Tests for ``app.reading.computations.confidence_voting``.

Doctrine source: the practitioner 3-vote rule (house + lord + karaka).

The 3-vote rule is the cross-cutting confidence-calibration mechanism
used throughout the practitioner / domain layers. Three pillars of
evidence are checked for any signification:

  1. House -- does the relevant bhava itself bear favourable
     indicators (occupant, aspects, ashtakavarga score)?
  2. Lord  -- does the lord of that bhava exhibit favourable placement
     (dignity, strength, conjunctions)?
  3. Karaka -- does the natural karaka for the signification's theme
     exhibit favourable state (dignity, freedom from affliction)?

Each vote is a boolean. The aggregate score = votes_for / 3.0.

Schema-aware band mapping
=========================

The schema ``ConfidenceScore.band`` literal set is
{indicative_only, low, medium, high, very_strong}; "moderate" and
"absent" are not members. The spec's nominal 4-band scheme is mapped:

  - 3/3  ->  score=1.0    -> band="very_strong"
  - 2/3  ->  score=0.667  -> band="medium"   (== "moderate" in spec)
  - 1/3  ->  score=0.333  -> band="indicative_only"
  - 0/3  ->  score=0.0    -> band="indicative_only" (closest to "absent")

The collapse of 0/3 and 1/3 into a single band is acceptable; the
``score`` field distinguishes them precisely.
"""
from __future__ import annotations

import math

import pytest

from app.reading.schema import ConfidenceScore


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestCastConfidenceVote:

    def test_returns_confidence_score(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(True, True, True)
        assert isinstance(result, ConfidenceScore)

    def test_votes_dict_has_three_keys(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(True, False, True)
        assert set(result.votes.keys()) == {"house", "lord", "karaka"}

    def test_votes_are_booleans(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(True, False, True)
        for value in result.votes.values():
            assert isinstance(value, bool)


# ---------------------------------------------------------------------------
# Score arithmetic -- exact fractions
# ---------------------------------------------------------------------------


class TestScoreArithmetic:
    """The score is an exact n/3 fraction; we verify all 4 buckets."""

    def test_score_3_of_3_is_one(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(True, True, True)
        assert math.isclose(result.score, 1.0, abs_tol=1e-12)

    def test_score_2_of_3_is_two_thirds(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(True, True, False)
        assert math.isclose(result.score, 2.0 / 3.0, abs_tol=1e-12)

    def test_score_1_of_3_is_one_third(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(True, False, False)
        assert math.isclose(result.score, 1.0 / 3.0, abs_tol=1e-12)

    def test_score_0_of_3_is_zero(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(False, False, False)
        assert math.isclose(result.score, 0.0, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# Band mapping per the schema-aware scheme
# ---------------------------------------------------------------------------


class TestBandMapping:

    def test_three_of_three_band_very_strong(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(True, True, True)
        assert result.band == "very_strong"

    def test_two_of_three_band_medium(self):
        """The spec says 'moderate' for 2/3; schema lacks 'moderate',
        we use the closest equivalent 'medium'."""
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(True, True, False)
        assert result.band == "medium"

    def test_one_of_three_band_indicative_only(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(True, False, False)
        assert result.band == "indicative_only"

    def test_zero_of_three_band_indicative_only(self):
        """0/3 maps to indicative_only (closest to spec's 'absent';
        schema lacks an 'absent' literal)."""
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(False, False, False)
        assert result.band == "indicative_only"


# ---------------------------------------------------------------------------
# Exhaustive: all 8 combinations of (house, lord, karaka)
# ---------------------------------------------------------------------------


class TestAllEightCombinations:
    """The wave-B plan asks for all 8 combinations to be exercised."""

    @pytest.mark.parametrize("house,lord,karaka", [
        (False, False, False),
        (False, False, True),
        (False, True,  False),
        (False, True,  True),
        (True,  False, False),
        (True,  False, True),
        (True,  True,  False),
        (True,  True,  True),
    ])
    def test_score_equals_count_over_three(self, house, lord, karaka):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(house, lord, karaka)
        count = int(house) + int(lord) + int(karaka)
        assert math.isclose(result.score, count / 3.0, abs_tol=1e-12)

    @pytest.mark.parametrize("house,lord,karaka", [
        (False, False, False),
        (False, False, True),
        (False, True,  False),
        (False, True,  True),
        (True,  False, False),
        (True,  False, True),
        (True,  True,  False),
        (True,  True,  True),
    ])
    def test_votes_dict_round_trips_inputs(self, house, lord, karaka):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        result = cast_confidence_vote(house, lord, karaka)
        assert result.votes["house"] == house
        assert result.votes["lord"] == lord
        assert result.votes["karaka"] == karaka


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestPropertyScoreDomain:
    """Score is always exactly in {0.0, 1/3, 2/3, 1.0}."""

    def test_score_always_in_quartic_set(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        allowed = {0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0}
        for house in (False, True):
            for lord in (False, True):
                for karaka in (False, True):
                    score = cast_confidence_vote(house, lord, karaka).score
                    assert any(
                        math.isclose(score, v, abs_tol=1e-12) for v in allowed
                    ), f"unexpected score {score!r}"


class TestPropertyBandDomain:
    """Band is always one of the four output values we use."""

    def test_band_always_in_expected_set(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        # We only emit 3 of the 5 schema literals from this helper.
        allowed = {"very_strong", "medium", "indicative_only"}
        for house in (False, True):
            for lord in (False, True):
                for karaka in (False, True):
                    band = cast_confidence_vote(house, lord, karaka).band
                    assert band in allowed, (
                        f"unexpected band {band!r}"
                    )


class TestPropertyMonotonicity:
    """Adding a True vote can never decrease the score."""

    def test_more_votes_means_higher_score(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        base = cast_confidence_vote(False, False, False).score
        assert base <= cast_confidence_vote(True, False, False).score
        assert (
            cast_confidence_vote(True, False, False).score
            <= cast_confidence_vote(True, True, False).score
        )
        assert (
            cast_confidence_vote(True, True, False).score
            <= cast_confidence_vote(True, True, True).score
        )


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestArgumentValidation:
    """Non-bool inputs are rejected loudly to prevent truthy-int slippage."""

    def test_non_bool_house_raises(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        with pytest.raises(TypeError):
            cast_confidence_vote(1, True, True)  # type: ignore[arg-type]

    def test_non_bool_lord_raises(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        with pytest.raises(TypeError):
            cast_confidence_vote(True, "yes", True)  # type: ignore[arg-type]

    def test_non_bool_karaka_raises(self):
        from app.reading.computations.confidence_voting import (
            cast_confidence_vote,
        )

        with pytest.raises(TypeError):
            cast_confidence_vote(True, True, None)  # type: ignore[arg-type]
