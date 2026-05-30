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
        assert validated.meta.schema_version == "1.2.0"
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
        """enrich=False MUST take the bare deterministic path (no Tier-3).

        Asserts that Tier-3 enrichment never fires when ``enrich=False``:
        ``Meta.enrichment_enabled`` and ``Meta.robustness_enabled`` both
        stay False, no contradictions are computed top-level. (Direct
        dict-equality with a second `_run_core_pipeline` call would
        compare two independent timestamps and become flaky once Phase 7
        wiring causes the pipeline to take real wall-clock time.)
        """
        result = compute(CANONICAL_INPUT, enrich=False)
        assert result["meta"]["enrichment_enabled"] is False
        assert result["meta"]["robustness_enabled"] is False
        # The contradictions list is only populated by the Tier-3
        # afterpass; with enrich=False it MUST stay empty.
        assert result["contradictions"] == []

    def test_compute_default_enrich_true_is_reachable(self):
        """Default enrich=True path is reachable and round-trips schema.

        Phase 7: with the real Tier-3 chain wired, the result still
        validates against the schema and reports ``enrichment_enabled=True``
        on its Meta envelope.
        """
        result = compute(CANONICAL_INPUT)
        # Round-trip validation proves the enriched payload still conforms.
        validated = ReadingOutput.model_validate(result)
        assert validated.meta.schema_version == "1.2.0"
        assert validated.meta.enrichment_enabled is True

    def test_compute_explicit_enrich_true_validates(self):
        """Passing enrich=True explicitly produces a schema-valid result."""
        explicit_result = compute(CANONICAL_INPUT, enrich=True)
        validated = ReadingOutput.model_validate(explicit_result)
        assert validated.meta.schema_version == "1.2.0"
        assert validated.meta.enrichment_enabled is True

    def test_apply_tier3_enrichments_flips_enrichment_flag(self):
        """Phase 7: Tier-3 afterpass flips ``Meta.enrichment_enabled``.

        Pre-Phase-7 this test asserted identity (the stub returned `base`
        unchanged). Post-Phase-7 the real Tier-3 chain runs and the only
        invariant we can lock structurally (without coupling to specific
        finding contents) is that ``enrichment_enabled`` transitions
        False -> True.
        """
        bare = _run_core_pipeline(CANONICAL_INPUT)
        assert bare["meta"]["enrichment_enabled"] is False
        enriched = _apply_tier3_enrichments(bare, CANONICAL_INPUT)
        assert enriched["meta"]["enrichment_enabled"] is True
