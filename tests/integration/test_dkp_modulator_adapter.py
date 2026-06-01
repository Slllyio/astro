"""Smoke tests for the DKP modulator adapter.

The adapter wraps Track-A domain verdicts as Track-B BhavaVerdicts and
runs them through ``apply_dkp_modulation``. Tests cover:

- Static domain→bhava mapping correctness
- DKPContext extraction from a Track-A reading
- Single-domain modulation with empty + populated context
- Reading-level (all-domains) modulation
- Round-trip JSON serialisation
- Lossiness audit notes are present
"""

from __future__ import annotations

import json

import pytest

from app.core.dkp_modulation import DKPContext
from app.integration.dkp_modulator_adapter import (
    DkpModulatedReading,
    ModulatedDomainReading,
    _DOMAIN_TO_BHAVA,
    build_dkp_context_from_reading,
    modulate_all_domains,
    modulate_domain,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _finding_dict(*, id: str, rule: str, direction: str = "positive",
                  classification: str = "primitive", verdict: str = "test") -> dict:
    return {
        "id": id,
        "rule": rule,
        "source_sequence": None,
        "classification": classification,
        "direction": direction,
        "verdict": verdict,
        "verdict_language": "en",
        "evidence": [],
        "confidence": {"score": 0.7, "votes": {}, "band": "medium"},
        "enrichment_level": 0,
        "citations": [],
        "consensus": None,
        "consensus_status": "not_computed",
        "dispute": None,
        "robustness": None,
        "contradicts_finding_ids": [],
    }


def _domain_reading(*, domain: str, overall_direction: str = "positive",
                    score: float = 0.7) -> dict:
    return {
        "domain": domain,
        "promise": _finding_dict(
            id=f"d.{domain}.promise", rule=f"promise.{domain}",
            direction=overall_direction, verdict=f"{domain} promise text",
        ),
        "triggers": [],
        "timing_windows": [],
        "afflictions": [],
        "cross_checks": [],
        "remedies": [],
        "overall_verdict": _finding_dict(
            id=f"d.{domain}.overall", rule=f"overall.{domain}",
            direction=overall_direction, verdict=f"{domain} overall",
        ),
        "confidence": {
            "score": score,
            "votes": {"house": True, "lord": True, "karaka": True},
            "band": "high" if score >= 0.7 else "medium",
        },
    }


def _minimal_reading_with(domains: dict) -> dict:
    return {
        "meta": {"schema_version": "1.2.0"},
        "chart": {"latitude": 12.97, "longitude": 77.59, "dob": "1990-07-15"},
        "primitives": {},
        "foundations": {},
        "practitioner": {},
        "sequences": {"vimshottari": {"current_md_lord": "Mercury"}},
        "domains": domains,
        "contradictions": [],
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Domain→bhava mapping
# ---------------------------------------------------------------------------

class TestDomainBhavaMapping:
    """The domain→bhava map is a doctrinal pick; pin it explicitly."""

    @pytest.mark.parametrize(
        "domain,expected_bhava",
        [
            ("career", 10), ("marriage", 7), ("children", 5),
            ("wealth", 2), ("health", 6), ("education", 4),
        ],
    )
    def test_each_domain_maps_to_expected_bhava(self, domain, expected_bhava):
        assert _DOMAIN_TO_BHAVA[domain] == expected_bhava

    def test_modulate_domain_uses_the_static_map(self):
        result = modulate_domain(_domain_reading(domain="career"))
        assert result.bhava == 10

    def test_unknown_domain_raises(self):
        with pytest.raises(ValueError, match="Unknown domain"):
            modulate_domain(_domain_reading(domain="not_a_real_domain"))


# ---------------------------------------------------------------------------
# DKPContext construction from reading
# ---------------------------------------------------------------------------

class TestBuildDKPContext:
    """Extracted context populates lat/lon/dob/md_lord from the reading."""

    def test_extracts_lat_lon_dob(self):
        reading = _minimal_reading_with({})
        ctx = build_dkp_context_from_reading(reading)
        assert ctx.birth_latitude == 12.97
        assert ctx.birth_longitude == 77.59
        assert ctx.birth_date_iso == "1990-07-15"

    def test_extracts_md_lord_from_sequences(self):
        reading = _minimal_reading_with({})
        ctx = build_dkp_context_from_reading(reading)
        assert ctx.active_dasha_lord == "Mercury"

    def test_overrides_take_precedence(self):
        """User-supplied overrides win over extracted fields."""
        reading = _minimal_reading_with({})
        ctx = build_dkp_context_from_reading(
            reading,
            ashrama="grihastha",
            marital_status="married",
            profession="software_engineer",
        )
        assert ctx.ashrama == "grihastha"
        assert ctx.marital_status == "married"
        assert ctx.profession == "software_engineer"
        # Extracted fields still present
        assert ctx.birth_latitude == 12.97


# ---------------------------------------------------------------------------
# Single-domain modulation
# ---------------------------------------------------------------------------

class TestSingleDomainModulation:
    """``modulate_domain()`` always returns a ``ModulatedDomainReading``
    and preserves the original."""

    def test_returns_modulated_domain_reading(self):
        result = modulate_domain(_domain_reading(domain="career"))
        assert isinstance(result, ModulatedDomainReading)
        assert result.domain == "career"
        assert result.bhava == 10

    def test_original_preserved(self):
        """Original DomainReading dict survives in result.original."""
        domain_dict = _domain_reading(domain="career")
        result = modulate_domain(domain_dict)
        assert result.original == domain_dict

    def test_empty_context_yields_low_confidence(self):
        """With DKPContext() (all None), context_completeness=0 and
        Track B forces confidence to LOW."""
        result = modulate_domain(_domain_reading(domain="career"))
        assert result.modulated.context_completeness == 0
        assert result.modulated.confidence == "LOW"

    def test_mapping_notes_include_provenance(self):
        result = modulate_domain(
            _domain_reading(domain="career", overall_direction="positive")
        )
        notes_joined = " ".join(result.mapping_notes)
        assert "adapted_from=domain.career" in notes_joined
        assert "direction_source=positive" in notes_joined

    def test_mixed_direction_collapse_is_noted(self):
        result = modulate_domain(
            _domain_reading(domain="career", overall_direction="mixed")
        )
        notes_joined = " ".join(result.mapping_notes)
        assert "mixed_direction_collapsed_to_label_weak" in notes_joined


# ---------------------------------------------------------------------------
# Reading-level modulation
# ---------------------------------------------------------------------------

class TestModulateAllDomains:
    """``modulate_all_domains()`` walks the 6 Track-A domains and emits
    one ModulatedDomainReading per non-None domain."""

    def test_two_populated_domains_yield_two_entries(self):
        reading = _minimal_reading_with({
            "career": _domain_reading(domain="career"),
            "marriage": _domain_reading(domain="marriage"),
        })
        result = modulate_all_domains(reading)
        assert isinstance(result, DkpModulatedReading)
        assert len(result.per_domain) == 2
        bhavas = {pd.bhava for pd in result.per_domain}
        assert bhavas == {7, 10}

    def test_missing_domains_skipped_silently(self):
        reading = _minimal_reading_with({
            "career": _domain_reading(domain="career"),
        })
        result = modulate_all_domains(reading)
        assert len(result.per_domain) == 1
        assert result.per_domain[0].domain == "career"

    def test_dkp_context_used_is_serialised(self):
        reading = _minimal_reading_with({
            "career": _domain_reading(domain="career"),
        })
        result = modulate_all_domains(reading)
        # All 12 DKPContext fields should be in the dict
        assert "birth_latitude" in result.dkp_context_used
        assert "active_dasha_lord" in result.dkp_context_used
        assert result.dkp_context_used["birth_latitude"] == 12.97
        assert result.dkp_context_used["active_dasha_lord"] == "Mercury"

    def test_user_context_propagates_to_completeness(self):
        """When user supplies extra DKPContext fields, completeness
        increases and confidence ladder steps up."""
        reading = _minimal_reading_with({
            "career": _domain_reading(domain="career"),
        })
        rich_ctx = DKPContext(
            birth_latitude=12.97, birth_longitude=77.59,
            current_residence_country="India",
            climate_mahabhuta="vata",
            birth_date_iso="1990-07-15",
            age_years=36.0,
            active_mundane_event="post_pandemic",
            active_dasha_lord="Mercury",
            ashrama="grihastha", marital_status="single",
            profession="software_engineer",
            prashna="career_change",
        )
        result = modulate_all_domains(reading, dkp_context=rich_ctx)
        # 12 of 12 fields filled → completeness 12
        assert result.context_completeness == 12
        # With max completeness, confidence rises above LOW
        assert result.per_domain[0].modulated.confidence in ("MEDIUM", "HIGH")


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_modulated_domain_roundtrip(self):
        result = modulate_domain(_domain_reading(domain="career"))
        as_json = json.dumps(result.model_dump(mode="json"))
        revived = ModulatedDomainReading.model_validate(json.loads(as_json))
        assert revived.bhava == 10
        assert revived.domain == "career"

    def test_full_modulated_reading_roundtrip(self):
        reading = _minimal_reading_with({
            "career": _domain_reading(domain="career"),
            "marriage": _domain_reading(domain="marriage"),
        })
        result = modulate_all_domains(reading)
        as_json = json.dumps(result.model_dump(mode="json"))
        revived = DkpModulatedReading.model_validate(json.loads(as_json))
        assert len(revived.per_domain) == 2
        assert revived.integration_version == "0.2.0"
