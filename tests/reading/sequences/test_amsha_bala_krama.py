"""Tests for ``app.reading.sequences.amsha_bala_krama``.

Doctrine source: notebook NotebookLM proforma — "The Architecture of Fate:
Shodasha Varga System" (BPHS-derived). The sequence runs 4 named checks
in fixed order and emits an :class:`AmshaBalaKramaResult` whose ``steps``
dict must match :data:`AMSHA_BALA_KRAMA_KEYS` exactly.

Bangalore baseline (1990-07-15 12:00 IST / 12.97 N, 77.59 E) is the
canonical fixture (CLAUDE.md test-pinning policy).
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Bangalore baseline fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def baseline_inputs(bangalore_chart) -> dict:
    """Inputs the ``run_sequence`` API needs for the Bangalore baseline."""
    md = bangalore_chart["current_mahadasha"]
    antardashas = bangalore_chart["antardashas"]
    # Pick the first AD lord under the current MD as a representative.
    ad_lord = md["mahadasha_lord"]
    for ad in antardashas:
        if ad.get("maha_lord") == md["mahadasha_lord"] and ad.get("antar_lord"):
            ad_lord = ad["antar_lord"]
            break

    return {
        "chart": bangalore_chart,
        "asc_sign": bangalore_chart["ascendant"]["sign"],
        "moon_sign": bangalore_chart["d1"]["Moon"]["sign"],
        "current_md_lord": md["mahadasha_lord"],
        "current_ad_lord": ad_lord,
        "target_varga": "d10",
    }


# ---------------------------------------------------------------------------
# Public-API + structural conformance
# ---------------------------------------------------------------------------


class TestRunSequence:

    def test_returns_amsha_bala_krama_result(self, baseline_inputs):
        from app.reading.schema import AmshaBalaKramaResult
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        assert isinstance(result, AmshaBalaKramaResult)

    def test_steps_dict_keys_match_enum(self, baseline_inputs):
        from app.reading.schema import AMSHA_BALA_KRAMA_KEYS
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        assert set(result.steps.keys()) == set(AMSHA_BALA_KRAMA_KEYS)

    def test_all_steps_are_findings(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        for key, finding in result.steps.items():
            assert isinstance(finding, Finding), f"step {key} not a Finding"

    def test_overall_verdict_is_finding(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        assert isinstance(result.overall_verdict, Finding)

    def test_finding_ids_use_sequence_grammar(self, baseline_inputs):
        """Per spec Section 6, sequence findings use ``seq_<N>.<scope>...``."""
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        for key, finding in result.steps.items():
            assert finding.id.startswith("seq_1."), (
                f"step {key} id {finding.id!r} must start with 'seq_1.'"
            )
        assert result.overall_verdict.id.startswith("seq_1.")

    def test_source_sequence_tagged(self, baseline_inputs):
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        for finding in result.steps.values():
            assert finding.source_sequence == "amsha_bala_krama"


class TestPerStepDelegation:
    """Each check should pull data from existing Tier-0/1/2 computations."""

    def test_analyze_d1_evidence_mentions_d1(self, baseline_inputs):
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        evidence = " ".join(result.steps["analyze_d1"].evidence)
        assert "D1" in evidence or "d1" in evidence

    def test_consult_d9_evidence_mentions_d9(self, baseline_inputs):
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        evidence = " ".join(result.steps["consult_d9"].evidence)
        assert "D9" in evidence or "d9" in evidence

    def test_specific_varga_refinement_mentions_target(self, baseline_inputs):
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        evidence = " ".join(result.steps["specific_varga_refinement"].evidence)
        # Bangalore default target_varga is "d10" -> verdict references D10.
        assert "D10" in evidence or "d10" in evidence

    def test_dasha_transit_activation_mentions_md_and_ad(self, baseline_inputs):
        from app.reading.sequences.amsha_bala_krama import run_sequence

        result = run_sequence(**baseline_inputs)
        evidence = " ".join(result.steps["dasha_transit_activation"].evidence)
        assert baseline_inputs["current_md_lord"] in evidence
        assert baseline_inputs["current_ad_lord"] in evidence


class TestTargetVargaParameterization:

    @pytest.mark.parametrize("varga", ["d2", "d7", "d9", "d10", "d24", "d60"])
    def test_varga_parameter_accepted(self, baseline_inputs, varga):
        from app.reading.sequences.amsha_bala_krama import run_sequence

        inputs = {**baseline_inputs, "target_varga": varga}
        result = run_sequence(**inputs)
        # Result still validates, no matter which varga.
        assert result is not None

    def test_invalid_varga_raises(self, baseline_inputs):
        from app.reading.sequences.amsha_bala_krama import run_sequence

        inputs = {**baseline_inputs, "target_varga": "d99"}
        with pytest.raises((ValueError, TypeError)):
            run_sequence(**inputs)
