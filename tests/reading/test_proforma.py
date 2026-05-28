"""Tests for `app.reading.proforma` orchestrator.

The two-function pattern (private `_run_core_pipeline`, public `compute`) is
the seam that prevents Tier-3 enrichment recursion (spec Section 5). These
tests lock that contract before any sequence module can violate it. Per the
TDD discipline in CLAUDE.md, each test asserts one structural fact:

- The pipeline emits a dict that round-trips through `ReadingOutput`.
- `Meta.schema_version` and `Meta.stability` carry the locked defaults.
- `DoctrineConfig` defaults match the 16 lockfile decisions (D-1..D-16) and
  the open-Q5 consensus thresholds.
- `compute(enrich=False)` returns the exact same dict as the bare core
  pipeline (no Tier-3 mutation).
- `compute(enrich=True)` is the reachable path through `_apply_tier3_enrichments`
  (Phase 1 stub: identity).
"""
from __future__ import annotations

from app.reading.proforma import (
    _apply_tier3_enrichments,
    _run_core_pipeline,
    compute,
)
from app.reading.schema import ChartInput, ReadingOutput


CANONICAL_INPUT = ChartInput(
    dob="1990-07-15",
    time="12:00",
    tz="+05:30",
    lat=12.97,
    lon=77.59,
)


class TestRunCorePipeline:
    """`_run_core_pipeline` is the private deterministic Stages-1..7 entry."""

    def test_returns_dict_matching_reading_output_shape(self):
        """Output dict must validate against ReadingOutput Pydantic model."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        # Round-trip through Pydantic asserts the full structural contract.
        validated = ReadingOutput.model_validate(output)
        assert validated.meta.schema_version == "1.0.0"
        assert validated.meta.stability == "experimental"

    def test_meta_chart_input_echoes_user_envelope(self):
        """Meta.chart_input must echo the user-supplied ChartInput verbatim."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        ci_dict = output["meta"]["chart_input"]
        assert ci_dict["dob"] == "1990-07-15"
        assert ci_dict["time"] == "12:00"
        assert ci_dict["tz"] == "+05:30"
        assert ci_dict["lat"] == 12.97
        assert ci_dict["lon"] == 77.59

    def test_meta_doctrine_config_has_locked_defaults(self):
        """DoctrineConfig in output must match the 16 lockfile decisions."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        dc = output["meta"]["doctrine_config"]
        # D-1: 8-karaka (PVR Narasimha Rao)
        assert dc["karaka_mode"] == 8
        # D-2: 1/7 -> 10 arudha exception
        assert dc["arudha_exception"] == "1_7_to_10"
        # D-3: Shodashavarga 16-varga vimsopaka
        assert dc["vimsopaka_scheme"] == "shodashavarga"
        # D-4: BPHS Ch.47 v.3 Ishta formula
        assert dc["ishta_formula"] == "bphs_47_3"
        # D-8: Sripati cusps
        assert dc["bhava_chalit_system"] == "sripati"
        # D-10: Sanjay-Rath karaka triangulation
        assert dc["karaka_triangulation_reading"] == "sanjay_rath"
        # D-11: BPHS 39.10 Neech Bhanga
        assert dc["neech_bhanga_rule"] == "bphs_39_10"
        # D-12: Strict 180-degree Rahu-leading Kala Sarpa
        assert dc["kala_sarpa_definition"] == "strict_180_rahu_leading"
        # D-13: Northern-latitude Graha Yuddha winner
        assert dc["graha_yuddha_winner"] == "northern_latitude"
        # Open-Q5 resolution: consensus thresholds
        assert dc["consensus_min_sources"] == 3
        assert dc["consensus_agreement_threshold"] == 0.66

    def test_enrichment_flags_default_to_false_in_core(self):
        """Core pipeline must report enrichment_enabled=False (no Tier-3 ran)."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        assert output["meta"]["enrichment_enabled"] is False
        assert output["meta"]["robustness_enabled"] is False

    def test_all_required_stage_blocks_present(self):
        """The 9 top-level keys per spec Section 6 must all be present."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        required = {
            "meta",
            "chart",
            "primitives",
            "foundations",
            "practitioner",
            "sequences",
            "domains",
            "contradictions",
            "warnings",
        }
        assert required <= set(output.keys())


class TestCompute:
    """`compute` is the public orchestrator with optional Tier-3 wrapping."""

    def test_compute_with_enrich_false_skips_tier3(self):
        """enrich=False MUST return the core pipeline output unmodified.

        This is the discipline-lock: birth-time-robustness and any other
        recursion-prone caller must be able to bypass Tier-3 cleanly.
        """
        bare = _run_core_pipeline(CANONICAL_INPUT)
        result = compute(CANONICAL_INPUT, enrich=False)
        assert result == bare

    def test_compute_default_enrich_true_is_reachable(self):
        """Default enrich=True path is reachable.

        Phase 1 stub: _apply_tier3_enrichments returns base unchanged, so the
        result still validates and equals the core output structurally. The
        purpose of this test is to lock the call-graph (compute -> core ->
        tier3 stub) before Tier-3 modules land.
        """
        result = compute(CANONICAL_INPUT)
        # Round-trip validation proves the enriched payload still conforms.
        validated = ReadingOutput.model_validate(result)
        assert validated.meta.schema_version == "1.0.0"

    def test_compute_explicit_enrich_true_matches_default(self):
        """Passing enrich=True explicitly is identical to the default."""
        default_result = compute(CANONICAL_INPUT)
        explicit_result = compute(CANONICAL_INPUT, enrich=True)
        assert default_result == explicit_result

    def test_apply_tier3_enrichments_stub_is_identity(self):
        """Phase 1 stub for Tier-3 returns base unchanged.

        When Task 6.x lands the real Tier-3 modules, this test is expected
        to be replaced with content-level assertions about citations,
        consensus, dispute, robustness, and contradiction enrichments.
        """
        bare = _run_core_pipeline(CANONICAL_INPUT)
        enriched = _apply_tier3_enrichments(bare, CANONICAL_INPUT)
        assert enriched == bare
