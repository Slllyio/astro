"""Schema model validation tests for `app.reading.schema`.

Each test class covers one major Pydantic model. Tests assert structural
contracts (field constraints, default values, frozen/extra=forbid behaviour,
enum-keyed dict validators) -- NOT astronomical correctness, which lives in
the dedicated computation test modules.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_dummy_finding(slug: str):
    """Construct a minimal valid Finding for use in *Judgment.checks dicts."""
    from app.reading.schema import ConfidenceScore, Finding

    return Finding(
        id=f"primitive.dummy.{slug}",
        rule=slug,
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=f"dummy verdict for {slug}",
        evidence=[],
        confidence=ConfidenceScore(
            score=0.5,
            votes={"house": False, "lord": False, "karaka": False},
            band="indicative_only",
        ),
    )


# ---------------------------------------------------------------------------
# ChartInput
# ---------------------------------------------------------------------------


class TestChartInput:
    """ChartInput is the user-supplied birth-data envelope."""

    def test_valid_chart_input_constructs(self):
        """A canonical Bangalore-baseline input constructs without error."""
        from app.reading.schema import ChartInput

        ci = ChartInput(
            dob="1990-07-15", time="12:00", tz="+05:30",
            lat=12.97, lon=77.59,
        )
        assert ci.dob == "1990-07-15"
        assert ci.lat == 12.97
        assert ci.lon == 77.59

    def test_invalid_latitude_rejected(self):
        """Latitude outside [-90, 90] is refused."""
        from app.reading.schema import ChartInput

        with pytest.raises(ValidationError):
            ChartInput(dob="1990-07-15", time="12:00", tz="+05:30", lat=100.0, lon=77.59)

    def test_invalid_longitude_rejected(self):
        """Longitude outside [-180, 180] is refused."""
        from app.reading.schema import ChartInput

        with pytest.raises(ValidationError):
            ChartInput(dob="1990-07-15", time="12:00", tz="+05:30", lat=12.97, lon=200.0)

    def test_extra_field_rejected(self):
        """extra='forbid' on the model rejects unknown kwargs (CLAUDE.md lock)."""
        from app.reading.schema import ChartInput

        with pytest.raises(ValidationError):
            ChartInput(
                dob="1990-07-15", time="12:00", tz="+05:30",
                lat=12.97, lon=77.59,
                bogus_field="ignored",  # type: ignore[call-arg]
            )

    def test_frozen_model_cannot_be_mutated(self):
        """frozen=True prevents accidental in-place mutation."""
        from app.reading.schema import ChartInput

        ci = ChartInput(dob="1990-07-15", time="12:00", tz="+05:30", lat=12.97, lon=77.59)
        with pytest.raises(ValidationError):
            ci.lat = 99.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ConfidenceScore
# ---------------------------------------------------------------------------


class TestConfidenceScore:
    """3-vote rule envelope with band classification."""

    def test_score_in_range(self):
        from app.reading.schema import ConfidenceScore

        cs = ConfidenceScore(
            score=0.66,
            votes={"house": True, "lord": True, "karaka": False},
            band="medium",
        )
        assert 0.0 <= cs.score <= 1.0

    def test_score_above_one_rejected(self):
        from app.reading.schema import ConfidenceScore

        with pytest.raises(ValidationError):
            ConfidenceScore(
                score=1.5,
                votes={"house": True, "lord": True, "karaka": True},
                band="very_strong",
            )

    def test_score_below_zero_rejected(self):
        from app.reading.schema import ConfidenceScore

        with pytest.raises(ValidationError):
            ConfidenceScore(
                score=-0.1,
                votes={"house": False, "lord": False, "karaka": False},
                band="indicative_only",
            )

    def test_invalid_band_rejected(self):
        from app.reading.schema import ConfidenceScore

        with pytest.raises(ValidationError):
            ConfidenceScore(
                score=0.5,
                votes={"house": False, "lord": False, "karaka": False},
                band="enormous",  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


class TestFinding:
    """Universal finding model used by every emitting module."""

    def test_finding_constructs_with_defaults(self):
        """Tier-3 enrichment fields default to neutral, non-populated values."""
        from app.reading.schema import ConfidenceScore, Finding

        f = Finding(
            id="primitive.karakas.atmakaraka",
            rule="Atmakaraka identification",
            source_sequence=None,
            classification="primitive",
            direction="neutral",
            verdict="Jupiter at 27.5° is Atmakaraka",
            evidence=["Jupiter degree: 27.5", "Highest among 7 planets"],
            confidence=ConfidenceScore(
                score=1.0,
                votes={"house": True, "lord": True, "karaka": True},
                band="very_strong",
            ),
        )
        assert f.enrichment_level == 0
        assert f.citations == []
        assert f.contradicts_finding_ids == []
        assert f.verdict_language == "en"
        assert f.consensus is None
        assert f.consensus_status == "not_computed"
        assert f.dispute is None
        assert f.robustness is None

    def test_verdict_max_length_enforced(self):
        """verdict must be ≤140 chars (spec Section 15)."""
        from app.reading.schema import ConfidenceScore, Finding

        with pytest.raises(ValidationError):
            Finding(
                id="x.y.z",
                rule="x",
                source_sequence=None,
                classification="primitive",
                direction="neutral",
                verdict="x" * 200,
                evidence=[],
                confidence=ConfidenceScore(
                    score=0.5,
                    votes={"house": False, "lord": False, "karaka": False},
                    band="indicative_only",
                ),
            )

    def test_verdict_at_max_length_accepted(self):
        """verdict exactly 140 chars is accepted."""
        from app.reading.schema import ConfidenceScore, Finding

        f = Finding(
            id="x.y.z",
            rule="x",
            source_sequence=None,
            classification="primitive",
            direction="neutral",
            verdict="x" * 140,
            evidence=[],
            confidence=ConfidenceScore(
                score=0.5,
                votes={"house": False, "lord": False, "karaka": False},
                band="indicative_only",
            ),
        )
        assert len(f.verdict) == 140

    def test_content_addressed_id_format_accepted(self):
        """ID grammar follows the dotted pattern from spec Section 6."""
        from app.reading.schema import ConfidenceScore, Finding

        # All spec-listed ID patterns construct fine -- the schema accepts the
        # string and does not enforce a specific prefix (validation lives in
        # the emitting modules' tests).
        for fid in (
            "seq_5.md_3.step_05_rashi_depositor",
            "primitive.karakas.atmakaraka",
            "foundation.argala.7th_house_argala",
            "practitioner.mks.saturn_in_1",
            "domain.marriage.7l_dasha_window",
        ):
            f = Finding(
                id=fid,
                rule="r",
                source_sequence=None,
                classification="primitive",
                direction="neutral",
                verdict="v",
                evidence=[],
                confidence=ConfidenceScore(
                    score=0.5,
                    votes={"house": False, "lord": False, "karaka": False},
                    band="indicative_only",
                ),
            )
            assert "." in f.id

    def test_invalid_classification_rejected(self):
        from app.reading.schema import ConfidenceScore, Finding

        with pytest.raises(ValidationError):
            Finding(
                id="x.y.z",
                rule="x",
                source_sequence=None,
                classification="badtype",  # type: ignore[arg-type]
                direction="neutral",
                verdict="v",
                evidence=[],
                confidence=ConfidenceScore(
                    score=0.5,
                    votes={"house": False, "lord": False, "karaka": False},
                    band="indicative_only",
                ),
            )

    def test_invalid_direction_rejected(self):
        from app.reading.schema import ConfidenceScore, Finding

        with pytest.raises(ValidationError):
            Finding(
                id="x.y.z",
                rule="x",
                source_sequence=None,
                classification="primitive",
                direction="cosmic",  # type: ignore[arg-type]
                verdict="v",
                evidence=[],
                confidence=ConfidenceScore(
                    score=0.5,
                    votes={"house": False, "lord": False, "karaka": False},
                    band="indicative_only",
                ),
            )


# ---------------------------------------------------------------------------
# Citation / Dispute / RobustnessScore / ConsensusScore
# ---------------------------------------------------------------------------


class TestCitation:
    def test_citation_constructs(self):
        from app.reading.schema import Citation

        c = Citation(
            source="BPHS Vol.I Ch.32 v.13",
            passage="The Atmakaraka is the planet of highest longitude.",
            relevance=0.92,
            knowledge_doc_id="bphs_v1_ch32",
        )
        assert c.relevance == 0.92

    def test_relevance_out_of_range_rejected(self):
        from app.reading.schema import Citation

        with pytest.raises(ValidationError):
            Citation(source="x", passage="y", relevance=1.5, knowledge_doc_id="z")


class TestConsensusScore:
    def test_constructs(self):
        from app.reading.schema import ConsensusScore

        cs = ConsensusScore(
            score=0.75,
            sources_agreeing=3,
            sources_total=4,
            low_consensus_flag=False,
        )
        assert cs.score == 0.75
        assert cs.low_consensus_flag is False

    def test_score_clamped(self):
        from app.reading.schema import ConsensusScore

        with pytest.raises(ValidationError):
            ConsensusScore(score=1.1, sources_agreeing=1, sources_total=1, low_consensus_flag=True)


class TestDispute:
    def test_constructs(self):
        from app.reading.schema import Dispute

        d = Dispute(
            rule="Ishta Phal formula",
            sources_for=["BPHS Ch.47 v.3"],
            sources_against=["Phaladeepika Ch.13"],
            canonical_example=None,
        )
        assert d.canonical_example is None


class TestRobustnessScore:
    def test_constructs(self):
        from app.reading.schema import RobustnessScore

        r = RobustnessScore(
            sensitive_to_birth_time=True,
            flip_rate_at_5min=0.10,
            flip_rate_at_10min=0.18,
            inputs_used=["T", "T-5min", "T+5min"],
        )
        assert r.sensitive_to_birth_time is True

    def test_flip_rate_clamp(self):
        from app.reading.schema import RobustnessScore

        with pytest.raises(ValidationError):
            RobustnessScore(
                sensitive_to_birth_time=False,
                flip_rate_at_5min=1.5,
                flip_rate_at_10min=0.0,
                inputs_used=[],
            )


# ---------------------------------------------------------------------------
# Property-based invariants
# ---------------------------------------------------------------------------


from hypothesis import given
from hypothesis import strategies as st


class TestPropertyInvariants:
    """Property-based tests for schema invariants (spec Section 17)."""

    @given(score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    def test_confidence_score_accepts_any_value_in_range(self, score):
        from app.reading.schema import ConfidenceScore

        cs = ConfidenceScore(
            score=score,
            votes={"house": False, "lord": False, "karaka": False},
            band="indicative_only",
        )
        assert 0.0 <= cs.score <= 1.0

    @given(score=st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x < 0 or x > 1))
    def test_confidence_score_rejects_out_of_range(self, score):
        from app.reading.schema import ConfidenceScore

        with pytest.raises(ValidationError):
            ConfidenceScore(
                score=score,
                votes={"house": False, "lord": False, "karaka": False},
                band="indicative_only",
            )

    @given(length=st.integers(min_value=0, max_value=140))
    def test_finding_verdict_at_or_below_max_length(self, length):
        from app.reading.schema import ConfidenceScore, Finding

        f = Finding(
            id="x.y.z",
            rule="x",
            source_sequence=None,
            classification="primitive",
            direction="neutral",
            verdict="v" * length,
            evidence=[],
            confidence=ConfidenceScore(
                score=0.5,
                votes={"house": False, "lord": False, "karaka": False},
                band="indicative_only",
            ),
        )
        assert len(f.verdict) <= 140

    @given(length=st.integers(min_value=141, max_value=2000))
    def test_finding_verdict_above_max_length_rejected(self, length):
        from app.reading.schema import ConfidenceScore, Finding

        with pytest.raises(ValidationError):
            Finding(
                id="x.y.z",
                rule="x",
                source_sequence=None,
                classification="primitive",
                direction="neutral",
                verdict="v" * length,
                evidence=[],
                confidence=ConfidenceScore(
                    score=0.5,
                    votes={"house": False, "lord": False, "karaka": False},
                    band="indicative_only",
                ),
            )
