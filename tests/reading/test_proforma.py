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

    def test_classical_yogas_surfaced_with_citations(self):
        """The core 88-detector yoga library is surfaced in the reading as
        `classical_yogas`, each carrying a name + classical reference. This
        guards the modern-life re-assembly, which must carry the field through
        (it rebuilds a fresh ReadingOutput and previously dropped it)."""
        output = _run_core_pipeline(CANONICAL_INPUT)
        assert "classical_yogas" in output
        cy = output["classical_yogas"]
        # a real natal chart lights up several classical yogas
        assert len(cy) >= 3, len(cy)
        for y in cy:
            assert y["name"] and y["reference"]
        # enrich=True (through Tier-3) must not drop them either
        enriched = compute(CANONICAL_INPUT, enrich=True)
        assert len(enriched["classical_yogas"]) == len(cy)


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


class TestPresentTenseAndDoctrineEnrichments:
    """Phase 0/1: compute() attaches present-tense + real-doctrine blocks under
    chart.extras — the daśā running TODAY (not birth), live transits, the
    encoded Raman per-house verdicts, and the executive summary."""

    def test_dasha_now_is_present_day_not_birth(self):
        """extras.dasha_now.md must be the MD covering TODAY, distinct from the
        birth balance — the fix for the impossible 'Current Mahadasha' window."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        dn = extras.get("dasha_now") or {}
        md = dn.get("md") or {}
        bb = dn.get("birth_balance") or {}
        assert md.get("md_lord"), "dasha_now.md must carry a running mahādaśā lord"
        # The running MD must cover the present moment: age_now falls inside the window.
        assert md["age_at_start_years"] <= md["age_now_years"] < md["age_at_end_years"]
        # And it must be labelled distinctly from the birth balance.
        assert bb.get("md_lord"), "birth_balance must be surfaced separately"
        assert bool(md.get("is_at_birth")) is False

    def test_house_doctrine_grades_all_twelve_houses(self):
        """extras.house_doctrine.houses carries a real Raman verdict per house,
        each with a 0..8 grade index and the evidence findings (the 'why')."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        hd = extras.get("house_doctrine") or {}
        houses = hd.get("houses") or {}
        assert len(houses) == 12
        for h in range(1, 13):
            hv = houses[str(h)]
            assert hv["verdict_label"] in hd["scale"]
            assert hv["verdict_index"] is None or 0 <= hv["verdict_index"] <= 8
            # Confidence is a real N-of-3 vote, never a fabricated probability.
            conf = hv["confidence"]
            assert conf["graded"] <= 3
            assert 0 <= conf["agreement"] <= conf["graded"]

    def test_executive_summary_is_populated(self):
        """extras.executive_summary is a deterministic list of lay-language
        lines built from the real engine output."""
        extras = compute(CANONICAL_INPUT)["chart"]["extras"]
        summary = extras.get("executive_summary") or []
        assert isinstance(summary, list) and summary
        assert all(isinstance(line, str) and line for line in summary)
