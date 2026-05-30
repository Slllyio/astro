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

    @given(
        st.lists(
            st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz_.",
                min_size=3,
                max_size=40,
            ),
            min_size=1,
            max_size=30,
            unique=True,
        )
    )
    def test_finding_ids_can_be_collected_uniquely(self, ids):
        """When findings carry distinct IDs the collection round-trips
        without conflict (spec Section 17 invariant)."""
        from app.reading.schema import ConfidenceScore, Finding

        findings = [
            Finding(
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
            for fid in ids
        ]
        collected = {f.id for f in findings}
        assert collected == set(ids)

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


# ---------------------------------------------------------------------------
# Enum tuples
# ---------------------------------------------------------------------------


class TestEnumTuples:
    """Verbatim check-key tuples from spec Section 6."""

    def test_md_check_keys_count_and_order(self):
        from app.reading.schema import MD_CHECK_KEYS

        assert isinstance(MD_CHECK_KEYS, tuple)
        assert len(MD_CHECK_KEYS) == 19
        # First and last entries are stable per spec
        assert MD_CHECK_KEYS[0] == "bhaav_from_lagna"
        assert MD_CHECK_KEYS[-1] == "repeat_from_karakamsha_lagna"

    def test_md_check_keys_unique(self):
        from app.reading.schema import MD_CHECK_KEYS

        assert len(MD_CHECK_KEYS) == len(set(MD_CHECK_KEYS))

    def test_ad_check_keys_count_and_order(self):
        from app.reading.schema import AD_CHECK_KEYS

        assert isinstance(AD_CHECK_KEYS, tuple)
        assert len(AD_CHECK_KEYS) == 7
        assert AD_CHECK_KEYS[0] == "rulership_of_ad_lord"
        assert AD_CHECK_KEYS[-1] == "mutual_position_md_ad"

    def test_amsha_bala_krama_keys_count_and_order(self):
        from app.reading.schema import AMSHA_BALA_KRAMA_KEYS

        assert isinstance(AMSHA_BALA_KRAMA_KEYS, tuple)
        assert len(AMSHA_BALA_KRAMA_KEYS) == 4
        assert AMSHA_BALA_KRAMA_KEYS == (
            "analyze_d1",
            "consult_d9",
            "specific_varga_refinement",
            "dasha_transit_activation",
        )

    def test_career_executive_keys_count_and_order(self):
        from app.reading.schema import CAREER_EXECUTIVE_KEYS

        assert isinstance(CAREER_EXECUTIVE_KEYS, tuple)
        assert len(CAREER_EXECUTIVE_KEYS) == 4
        assert CAREER_EXECUTIVE_KEYS == (
            "vargottama_amatya_karaka",
            "gandanta_knots",
            "vimsopaka_strength",
            "gulika_saturn_bottlenecks",
        )


# ---------------------------------------------------------------------------
# MDJudgment
# ---------------------------------------------------------------------------


class TestMDJudgment:
    """Mahadasha judgment dict must carry all 19 named keys."""

    def _make_full_checks(self):
        from app.reading.schema import MD_CHECK_KEYS

        return {k: _make_dummy_finding(k) for k in MD_CHECK_KEYS}

    def test_md_judgment_constructs_with_all_19_keys(self):
        from app.reading.schema import MDJudgment

        checks = self._make_full_checks()
        j = MDJudgment(
            md_lord="Saturn",
            start_jd=2447909.5,
            end_jd=2454850.0,
            start_date="1989-12-01",
            end_date="2009-01-15",
            age_at_start=0.0,
            age_at_end=19.1,
            is_current=False,
            is_past=True,
            is_future=False,
            checks=checks,
            overall_verdict=_make_dummy_finding("summary"),
        )
        assert set(j.checks.keys()) == set(self._make_full_checks().keys())

    def test_md_judgment_missing_key_rejected(self):
        from app.reading.schema import MDJudgment, MD_CHECK_KEYS

        partial = {k: _make_dummy_finding(k) for k in MD_CHECK_KEYS[:18]}
        with pytest.raises(ValidationError):
            MDJudgment(
                md_lord="Saturn",
                start_jd=2447909.5,
                end_jd=2454850.0,
                start_date="1989-12-01",
                end_date="2009-01-15",
                age_at_start=0.0,
                age_at_end=19.1,
                is_current=False,
                is_past=True,
                is_future=False,
                checks=partial,
                overall_verdict=_make_dummy_finding("summary"),
            )

    def test_md_judgment_extra_key_rejected(self):
        from app.reading.schema import MDJudgment

        bogus = self._make_full_checks()
        bogus["bonus_check_not_in_spec"] = _make_dummy_finding("bonus")
        with pytest.raises(ValidationError):
            MDJudgment(
                md_lord="Saturn",
                start_jd=2447909.5,
                end_jd=2454850.0,
                start_date="1989-12-01",
                end_date="2009-01-15",
                age_at_start=0.0,
                age_at_end=19.1,
                is_current=False,
                is_past=True,
                is_future=False,
                checks=bogus,
                overall_verdict=_make_dummy_finding("summary"),
            )


# ---------------------------------------------------------------------------
# ADJudgment
# ---------------------------------------------------------------------------


class TestADJudgment:
    """Antardasha judgment dict must carry all 7 named keys."""

    def _make_full_checks(self):
        from app.reading.schema import AD_CHECK_KEYS

        return {k: _make_dummy_finding(k) for k in AD_CHECK_KEYS}

    def test_ad_judgment_constructs_with_all_7_keys(self):
        from app.reading.schema import ADJudgment

        j = ADJudgment(
            ad_lord="Mercury",
            md_lord="Saturn",
            start_jd=2450000.0,
            end_jd=2450500.0,
            start_date="1995-10-01",
            end_date="1997-02-15",
            age_at_start=5.2,
            age_at_end=6.6,
            is_current=False,
            is_past=True,
            is_future=False,
            checks=self._make_full_checks(),
            overall_verdict=_make_dummy_finding("summary"),
        )
        assert len(j.checks) == 7

    def test_ad_judgment_missing_key_rejected(self):
        from app.reading.schema import ADJudgment, AD_CHECK_KEYS

        partial = {k: _make_dummy_finding(k) for k in AD_CHECK_KEYS[:6]}
        with pytest.raises(ValidationError):
            ADJudgment(
                ad_lord="Mercury",
                md_lord="Saturn",
                start_jd=2450000.0,
                end_jd=2450500.0,
                start_date="1995-10-01",
                end_date="1997-02-15",
                age_at_start=5.2,
                age_at_end=6.6,
                is_current=False,
                is_past=True,
                is_future=False,
                checks=partial,
                overall_verdict=_make_dummy_finding("summary"),
            )


# ---------------------------------------------------------------------------
# AmshaBalaKramaResult
# ---------------------------------------------------------------------------


class TestAmshaBalaKramaResult:
    def test_constructs_with_all_4_steps(self):
        from app.reading.schema import AMSHA_BALA_KRAMA_KEYS, AmshaBalaKramaResult

        steps = {k: _make_dummy_finding(k) for k in AMSHA_BALA_KRAMA_KEYS}
        r = AmshaBalaKramaResult(
            steps=steps, overall_verdict=_make_dummy_finding("summary")
        )
        assert len(r.steps) == 4

    def test_missing_step_rejected(self):
        from app.reading.schema import AMSHA_BALA_KRAMA_KEYS, AmshaBalaKramaResult

        partial = {k: _make_dummy_finding(k) for k in AMSHA_BALA_KRAMA_KEYS[:3]}
        with pytest.raises(ValidationError):
            AmshaBalaKramaResult(
                steps=partial, overall_verdict=_make_dummy_finding("summary")
            )


# ---------------------------------------------------------------------------
# CareerExecutiveResult
# ---------------------------------------------------------------------------


class TestCareerExecutiveResult:
    def test_constructs_with_all_4_steps(self):
        from app.reading.schema import CAREER_EXECUTIVE_KEYS, CareerExecutiveResult

        steps = {k: _make_dummy_finding(k) for k in CAREER_EXECUTIVE_KEYS}
        r = CareerExecutiveResult(
            steps=steps, overall_verdict=_make_dummy_finding("summary")
        )
        assert len(r.steps) == 4

    def test_missing_step_rejected(self):
        from app.reading.schema import CAREER_EXECUTIVE_KEYS, CareerExecutiveResult

        partial = {k: _make_dummy_finding(k) for k in CAREER_EXECUTIVE_KEYS[:3]}
        with pytest.raises(ValidationError):
            CareerExecutiveResult(
                steps=partial, overall_verdict=_make_dummy_finding("summary")
            )


# ---------------------------------------------------------------------------
# Contradiction
# ---------------------------------------------------------------------------


class TestContradiction:
    def test_constructs(self):
        from app.reading.schema import Contradiction

        c = Contradiction(
            finding_ids=["seq_5.md_3.step_5", "seq_6.ad_1.step_2"],
            domain="marriage",
            description="MD says trinal support; AD says 6/8 friction.",
            severity="soft",
            suggested_arbitration=None,
        )
        assert c.severity == "soft"

    def test_invalid_severity_rejected(self):
        from app.reading.schema import Contradiction

        with pytest.raises(ValidationError):
            Contradiction(
                finding_ids=["a", "b"],
                domain="marriage",
                description="x",
                severity="catastrophic",  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# TimingWindow
# ---------------------------------------------------------------------------


class TestTimingWindow:
    def test_constructs(self):
        from app.reading.schema import TimingWindow

        w = TimingWindow(
            start_date="2027-03-15",
            end_date="2028-09-20",
            driving_period="MD Saturn / AD Jupiter",
            event_type="marriage",
            confidence_band="medium",
            triggering_finding_ids=["domain.marriage.7l_dasha_window"],
        )
        assert w.event_type == "marriage"


# ---------------------------------------------------------------------------
# DoctrineConfig — echoes the 16 lockfile decisions
# ---------------------------------------------------------------------------


class TestDoctrineConfig:
    """DoctrineConfig defaults match docs/doctrine-decisions.md D-1..D-16."""

    def test_default_values_match_lockfile(self):
        """Every default matches the locked decision (D-1..D-13 + consensus)."""
        from app.reading.schema import DoctrineConfig

        dc = DoctrineConfig()
        # D-1 Karaka mode = 8 (PVR Narasimha Rao)
        assert dc.karaka_mode == 8
        # D-2 Arudha exception
        assert dc.arudha_exception == "1_7_to_10"
        # D-3 Vimsopaka scheme
        assert dc.vimsopaka_scheme == "shodashavarga"
        # D-4 Ishta formula
        assert dc.ishta_formula == "bphs_47_3"
        # D-8 Bhava Chalit
        assert dc.bhava_chalit_system == "sripati"
        # D-10 Karaka triangulation
        assert dc.karaka_triangulation_reading == "sanjay_rath"
        # D-11 Neech Bhanga primary rule
        assert dc.neech_bhanga_rule == "bphs_39_10"
        # D-12 Kala Sarpa definition
        assert dc.kala_sarpa_definition == "strict_180_rahu_leading"
        # D-13 Graha Yuddha winner
        assert dc.graha_yuddha_winner == "northern_latitude"
        # Consensus defaults (Section 12, open Q #5)
        assert dc.consensus_min_sources == 3
        assert dc.consensus_agreement_threshold == 0.66

    def test_invalid_karaka_mode_rejected(self):
        """Karaka mode is constrained to Literal[7, 8]."""
        from app.reading.schema import DoctrineConfig

        with pytest.raises(ValidationError):
            DoctrineConfig(karaka_mode=9)  # type: ignore[arg-type]

    def test_consensus_agreement_threshold_clamped(self):
        from app.reading.schema import DoctrineConfig

        with pytest.raises(ValidationError):
            DoctrineConfig(consensus_agreement_threshold=1.5)

    def test_consensus_min_sources_non_negative(self):
        from app.reading.schema import DoctrineConfig

        with pytest.raises(ValidationError):
            DoctrineConfig(consensus_min_sources=-1)

    def test_alternative_karaka_mode_accepted(self):
        from app.reading.schema import DoctrineConfig

        dc = DoctrineConfig(karaka_mode=7)
        assert dc.karaka_mode == 7


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------


class TestMeta:
    """Meta block: version locks + doctrine echo."""

    def _make_meta(self, **overrides):
        from app.reading.schema import ChartInput, DoctrineConfig, Meta

        defaults = dict(
            engine_version="abc1234",
            swiss_ephemeris_version="2.10.03",
            python_version="3.12.10",
            generated_at="2026-05-28T12:00:00+00:00",
            chart_input=ChartInput(
                dob="1990-07-15", time="12:00", tz="+05:30", lat=12.97, lon=77.59
            ),
            doctrines_used=["D-1", "D-2"],
            doctrine_config=DoctrineConfig(),
            enrichment_enabled=False,
            robustness_enabled=False,
            stage_timings_ms={"stage_1": 12, "stage_2": 240},
        )
        defaults.update(overrides)
        return Meta(**defaults)

    def test_schema_version_locked_at_1_1_0(self):
        """schema_version defaults to the V1.5 emitted value (1.1.0)."""
        m = self._make_meta()
        assert m.schema_version == "1.2.0"

    def test_schema_version_1_0_0_still_accepted(self):
        """Backward-compat: 1.0.0 remains a valid Literal value."""
        m = self._make_meta(schema_version="1.0.0")
        assert m.schema_version == "1.0.0"

    def test_stability_default_experimental(self):
        m = self._make_meta()
        assert m.stability == "experimental"

    def test_schema_changelog_url_default(self):
        m = self._make_meta()
        assert m.schema_changelog_url == "docs/reading/CHANGELOG.md"

    def test_invalid_stability_rejected(self):
        with pytest.raises(ValidationError):
            self._make_meta(stability="grandfather")

    def test_doctrine_config_required(self):
        """doctrine_config must be explicitly supplied -- it's the reproducibility lock."""
        from app.reading.schema import ChartInput, Meta

        with pytest.raises(ValidationError):
            Meta(  # type: ignore[call-arg]
                engine_version="x",
                swiss_ephemeris_version="x",
                python_version="x",
                generated_at="x",
                chart_input=ChartInput(
                    dob="1990-07-15", time="12:00", tz="+05:30", lat=12.97, lon=77.59
                ),
                doctrines_used=[],
                # doctrine_config omitted
                enrichment_enabled=False,
                robustness_enabled=False,
                stage_timings_ms={},
            )


# ---------------------------------------------------------------------------
# DomainReading
# ---------------------------------------------------------------------------


class TestDomainReading:
    def test_constructs(self):
        from app.reading.schema import (
            ConfidenceScore,
            DomainReading,
            RemedyRecommendation,
        )

        promise = _make_dummy_finding("promise")
        cs = ConfidenceScore(
            score=0.7,
            votes={"house": True, "lord": True, "karaka": False},
            band="medium",
        )
        remedy = RemedyRecommendation(
            kind="mantra",
            description="Recite the Mahamrityunjaya mantra 108x weekly.",
            source="Phaladeepika Ch.27",
        )
        dr = DomainReading(
            domain="marriage",
            promise=promise,
            triggers=[],
            timing_windows=[],
            afflictions=[],
            cross_checks=[],
            remedies=[remedy],
            overall_verdict=_make_dummy_finding("overall"),
            confidence=cs,
        )
        assert dr.domain == "marriage"
        assert len(dr.remedies) == 1


# ---------------------------------------------------------------------------
# Block models (ChartBlock, PrimitivesBlock, etc.)
# ---------------------------------------------------------------------------


class TestBlockModels:
    """Each pipeline-stage block model exists, is frozen, forbids extra fields."""

    def test_chart_block_constructs_empty(self):
        from app.reading.schema import ChartBlock

        c = ChartBlock()
        assert isinstance(c, ChartBlock)

    def test_primitives_block_constructs_empty(self):
        from app.reading.schema import PrimitivesBlock

        c = PrimitivesBlock()
        assert isinstance(c, PrimitivesBlock)

    def test_foundations_block_constructs_empty(self):
        from app.reading.schema import FoundationsBlock

        c = FoundationsBlock()
        assert isinstance(c, FoundationsBlock)

    def test_practitioner_block_constructs_empty(self):
        from app.reading.schema import PractitionerBlock

        c = PractitionerBlock()
        assert isinstance(c, PractitionerBlock)

    def test_sequences_block_constructs_empty(self):
        from app.reading.schema import SequencesBlock

        c = SequencesBlock()
        assert isinstance(c, SequencesBlock)

    def test_domains_block_constructs_empty(self):
        from app.reading.schema import DomainsBlock

        c = DomainsBlock()
        assert isinstance(c, DomainsBlock)

    def test_chart_block_rejects_extra_field(self):
        from app.reading.schema import ChartBlock

        with pytest.raises(ValidationError):
            ChartBlock(bogus="x")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ReadingOutput — root
# ---------------------------------------------------------------------------


class TestReadingOutput:
    """The root model holding all 9 top-level keys from spec Section 6."""

    def _make_output(self, **overrides):
        from app.reading.schema import (
            ChartBlock,
            ChartInput,
            DoctrineConfig,
            DomainsBlock,
            FoundationsBlock,
            Meta,
            PractitionerBlock,
            PrimitivesBlock,
            ReadingOutput,
            SequencesBlock,
        )

        meta = Meta(
            engine_version="abc1234",
            swiss_ephemeris_version="2.10.03",
            python_version="3.12.10",
            generated_at="2026-05-28T12:00:00+00:00",
            chart_input=ChartInput(
                dob="1990-07-15", time="12:00", tz="+05:30", lat=12.97, lon=77.59
            ),
            doctrines_used=[],
            doctrine_config=DoctrineConfig(),
            enrichment_enabled=False,
            robustness_enabled=False,
            stage_timings_ms={},
        )
        defaults = dict(
            meta=meta,
            chart=ChartBlock(),
            primitives=PrimitivesBlock(),
            foundations=FoundationsBlock(),
            practitioner=PractitionerBlock(),
            sequences=SequencesBlock(),
            domains=DomainsBlock(),
            contradictions=[],
            warnings=[],
        )
        defaults.update(overrides)
        return ReadingOutput(**defaults)

    def test_constructs_with_all_top_level_keys(self):
        o = self._make_output()
        # All 9 top-level keys must be present and accessible.
        assert o.meta is not None
        assert o.chart is not None
        assert o.primitives is not None
        assert o.foundations is not None
        assert o.practitioner is not None
        assert o.sequences is not None
        assert o.domains is not None
        assert o.contradictions == []
        assert o.warnings == []

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            self._make_output(extra_unspecified_block={"x": 1})

    def test_schema_version_round_trip_via_dump(self):
        """Round-tripping via model_dump preserves the schema_version lock."""
        o = self._make_output()
        d = o.model_dump()
        assert d["meta"]["schema_version"] == "1.2.0"

    def test_contradictions_carries_contradiction_objects(self):
        from app.reading.schema import Contradiction

        c = Contradiction(
            finding_ids=["a.b.c", "x.y.z"],
            domain="marriage",
            description="conflict",
            severity="soft",
        )
        o = self._make_output(contradictions=[c])
        assert len(o.contradictions) == 1
        assert o.contradictions[0].severity == "soft"
