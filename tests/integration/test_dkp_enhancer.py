"""Smoke tests for the DKP-translation enhancer.

These tests exercise ``app.integration.dkp_enhancer.enhance()`` against
synthetic Finding dicts so they run fast (no Track-A pipeline invocation,
no swisseph imports). The enhancer reads from Track-B's static
TranslationRecord registry only.
"""

from __future__ import annotations

import json

import pytest

from app.integration.dkp_enhancer import (
    IntegratedReadingOutput,
    _extract_bhava_planet_pairs,
    _name_variants,
    enhance,
    registry_size,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _minimal_reading(findings: list[dict]) -> dict:
    """Build a minimal ReadingOutput-shaped dict with one career-domain
    finding list. All other top-level keys are present but empty so the
    walker only finds these findings."""
    return {
        "meta": {"schema_version": "1.2.0"},
        "chart": {},
        "primitives": {},
        "foundations": {},
        "practitioner": {},
        "sequences": {},
        "domains": {
            "career": {
                "verdict": "test",
                "findings": findings,
                "cross_checks": [],
            }
        },
        "contradictions": [],
        "warnings": [],
    }


def _finding(*, id: str, rule: str, classification: str = "yoga",
             evidence: list[str] | None = None) -> dict:
    """Build a Finding-shaped dict matching the schema's required fields."""
    return {
        "id": id,
        "rule": rule,
        "source_sequence": None,
        "classification": classification,
        "direction": "positive",
        "verdict": "test verdict",
        "verdict_language": "en",
        "evidence": evidence or [],
        "confidence": {"score": 0.7, "tier": "medium"},
        "enrichment_level": 0,
        "citations": [],
        "consensus": None,
        "consensus_status": "not_computed",
        "dispute": None,
        "robustness": None,
        "contradicts_finding_ids": [],
    }


# ---------------------------------------------------------------------------
# Registry / sanity
# ---------------------------------------------------------------------------

class TestRegistry:
    """Translation registry is populated and reachable."""

    def test_registry_size_matches_documented_count(self):
        """27 records were documented in memory entry as of 2026-05-29."""
        assert registry_size() == 27


# ---------------------------------------------------------------------------
# Name variant generator
# ---------------------------------------------------------------------------

class TestNameVariants:
    """Variant generation handles the underscore/space/case normalization
    needed to bridge Track-A's lowercase namespaced rule IDs to Track-B's
    TitleCase keys."""

    def test_simple_lowercase_yields_titlecase_variant(self):
        variants = _name_variants("lakshmi")
        assert "Lakshmi" in variants

    def test_underscore_word_yields_spaced_titlecase(self):
        """``vipareeta_raja`` must yield ``Vipareeta Raja`` to match the
        registry's space-separated key."""
        variants = _name_variants("vipareeta_raja")
        assert "Vipareeta Raja" in variants
        assert "Vipareeta_Raja" in variants

    def test_empty_string_yields_no_variants(self):
        assert _name_variants("") == []

    def test_variants_are_deduplicated(self):
        """A single-word lowercase segment shouldn't repeat itself across
        the as-is/title-underscored/title-spaced/lowercase-spaced paths."""
        variants = _name_variants("lakshmi")
        assert len(variants) == len(set(variants))


# ---------------------------------------------------------------------------
# Bhava+planet extractor
# ---------------------------------------------------------------------------

class TestBhavaPlanetExtraction:
    """Regex-driven extraction of (bhava, planet) pairs from evidence text."""

    def test_saturn_in_8h_extracted(self):
        pairs = _extract_bhava_planet_pairs("Saturn occupies 8H bhava")
        assert (8, "Saturn") in pairs

    def test_planet_without_bhava_yields_nothing(self):
        """If no bhava number appears, no pairs are emitted."""
        assert _extract_bhava_planet_pairs("Jupiter is exalted") == []

    def test_multiple_planets_single_bhava_pair_correctly(self):
        """When two planets co-occur with one bhava, both pairs surface."""
        pairs = _extract_bhava_planet_pairs("Mars and Saturn in 10H")
        assert (10, "Mars") in pairs
        assert (10, "Saturn") in pairs

    def test_bhava_out_of_1_12_range_ignored(self):
        """Bhava regex is bounded 1..12 — '13H' must not pair."""
        pairs = _extract_bhava_planet_pairs("Saturn in 13H")
        assert pairs == []


# ---------------------------------------------------------------------------
# End-to-end enhance() behavior
# ---------------------------------------------------------------------------

class TestEnhance:
    """End-to-end coverage of enhance() over a minimal reading."""

    def test_lakshmi_yoga_finding_gets_one_translation(self):
        """Lakshmi is in the registry under ``career_wealth``. Yoga lookup
        with name-variant ``Lakshmi`` must surface exactly one record."""
        reading = _minimal_reading([
            _finding(id="t.1", rule="yogas_extended.lakshmi", classification="yoga"),
        ])
        result = enhance(reading)
        sidecar = result.reading["domains"]["career"]["findings"][0]["dkp_translations"]
        assert len(sidecar) == 1
        assert sidecar[0]["key"] == "Lakshmi"
        assert sidecar[0]["domain"] == "career_wealth"

    def test_vipareeta_yoga_returns_multiple_domain_records(self):
        """Vipareeta Raja exists in BOTH career_wealth and health domains
        with distinct shlokas. Both must be attached — our dedup key is
        (key, domain), not key alone."""
        reading = _minimal_reading([
            _finding(id="t.2", rule="yogas_extended.vipareeta_raja", classification="yoga"),
        ])
        result = enhance(reading)
        sidecar = result.reading["domains"]["career"]["findings"][0]["dkp_translations"]
        assert len(sidecar) == 2
        domains = {t["domain"] for t in sidecar}
        assert domains == {"career_wealth", "health"}

    def test_bhava_planet_extraction_from_evidence(self):
        """Evidence text 'Saturn occupies 8H' must trigger
        translate_bhava_planet(8, 'Saturn') → bhava_8_planet_Saturn record."""
        reading = _minimal_reading([
            _finding(
                id="t.3",
                rule="karaka.health",
                classification="affliction",
                evidence=["Saturn occupies 8H bhava"],
            ),
        ])
        result = enhance(reading)
        sidecar = result.reading["domains"]["career"]["findings"][0]["dkp_translations"]
        assert any(t["key"] == "bhava_8_planet_Saturn" for t in sidecar)

    def test_unknown_finding_attaches_empty_sidecar(self):
        """A finding with no matchable rule/yoga/bhava+planet still gets the
        ``dkp_translations`` key — just an empty list."""
        reading = _minimal_reading([
            _finding(id="t.4", rule="nonexistent.rule.id", classification="primitive"),
        ])
        result = enhance(reading)
        sidecar = result.reading["domains"]["career"]["findings"][0]["dkp_translations"]
        assert sidecar == []

    def test_summary_dedup_across_findings(self):
        """Same Lakshmi key referenced by two findings appears once in the
        summary records (deduped by key) but twice in total_records_attached."""
        reading = _minimal_reading([
            _finding(id="t.5a", rule="yogas_extended.lakshmi", classification="yoga"),
            _finding(id="t.5b", rule="yogas_extended.lakshmi", classification="yoga"),
        ])
        result = enhance(reading)
        # Summary dedupes by key
        assert "Lakshmi" in result.dkp_translations_summary.records
        # But cross_references has both finding IDs
        assert result.dkp_translations_summary.cross_references["Lakshmi"] == ["t.5a", "t.5b"]
        # total_records_attached counts BOTH attachments
        assert result.dkp_translations_summary.total_records_attached == 2

    def test_envelope_is_pydantic_serializable(self):
        """IntegratedReadingOutput round-trips through JSON — that's the
        public contract for downstream consumers."""
        reading = _minimal_reading([
            _finding(id="t.6", rule="yogas_extended.lakshmi", classification="yoga"),
        ])
        result = enhance(reading)
        as_json = json.dumps(result.model_dump(mode="json"))
        revived = IntegratedReadingOutput.model_validate(json.loads(as_json))
        assert revived.dkp_translations_summary.total_records_attached == 1

    def test_integration_version_pinned(self):
        """``integration_version`` is the public contract version for this
        envelope; bumping it is intentional."""
        reading = _minimal_reading([])
        result = enhance(reading)
        assert result.integration_version == "0.1.0"

    def test_walker_skips_meta_dicts_with_id_key(self):
        """The walker identifies Findings structurally by requiring ALL of
        id/rule/classification/verdict — not just ``id``. Meta blocks
        carrying just an 'id' field must not be treated as findings."""
        reading = _minimal_reading([])
        # Contaminate sequences with a non-Finding dict that happens to have 'id'
        reading["sequences"]["fake"] = {"id": "not-a-finding", "value": 42}
        result = enhance(reading)
        # The fake dict survived untouched (no dkp_translations key added)
        assert "dkp_translations" not in reading["sequences"]["fake"]


# ---------------------------------------------------------------------------
# Pydantic input acceptance
# ---------------------------------------------------------------------------

class TestLordshipVsPlacement:
    """The DKP enhancer must NOT attach bhava_N_planet_P records on
    lordship references like 'NH lord P' — only on actual placements.

    Surfaced 2026-05-31 by user review of Mainpuri chart: Saturn was the
    4H lord but placed in 2H; the enhancer wrongly attached
    bhava_4_planet_Saturn (which describes Saturn IN 4H, a totally
    different astrological signature).
    """

    def test_lordship_phrase_does_not_attach_placement_record(self):
        """Finding text 'D24 4H lord Saturn in Cancer' must NOT trigger
        bhava_4_planet_Saturn attachment."""
        reading = _minimal_reading([
            _finding(
                id="t.4h.lord",
                rule="d24_chaturvimsamsa",
                classification="primitive",
                evidence=[
                    "house=4",
                    "house_sign=11",
                    "house_lord=Saturn",
                    "d24_sign=4",
                    "d24_sign_name=Cancer",
                ],
            ),
        ])
        result = enhance(reading)
        sidecar = result.reading["domains"]["career"]["findings"][0]["dkp_translations"]
        keys = [t["key"] for t in sidecar]
        assert "bhava_4_planet_Saturn" not in keys

    def test_placement_phrase_still_attaches_when_chart_confirms(self):
        """Finding 'Saturn in 4H' WITH planet_houses[Saturn]==4 should attach."""
        reading = _minimal_reading([
            _finding(
                id="t.4h.place",
                rule="karaka.health",
                classification="affliction",
                evidence=["Saturn occupies 4H bhava in this chart"],
            ),
        ])
        # Inject a chart so the enhancer can verify placement.
        reading["chart"] = {
            "planets": {
                "Saturn": {"house": 4, "sign": 4, "longitude": 100.0},
            },
        }
        result = enhance(reading)
        sidecar = result.reading["domains"]["career"]["findings"][0]["dkp_translations"]
        keys = [t["key"] for t in sidecar]
        assert "bhava_4_planet_Saturn" in keys

    def test_placement_phrase_blocked_when_chart_disagrees(self):
        """Even if text says 'Saturn in 4H', if the chart says Saturn is in
        2H, we must NOT attach the bhava_4_planet_Saturn record."""
        reading = _minimal_reading([
            _finding(
                id="t.4h.wrong",
                rule="some.rule",
                classification="affliction",
                evidence=["Saturn in 4H or wherever"],
            ),
        ])
        reading["chart"] = {
            "planets": {
                "Saturn": {"house": 2, "sign": 9, "longitude": 254.0},
            },
        }
        result = enhance(reading)
        sidecar = result.reading["domains"]["career"]["findings"][0]["dkp_translations"]
        keys = [t["key"] for t in sidecar]
        assert "bhava_4_planet_Saturn" not in keys

    def test_house_lord_equals_pattern_recognised(self):
        """Structured evidence form 'house_lord=Saturn' must be detected."""
        from app.integration.dkp_enhancer import _looks_like_lordship_reference
        assert _looks_like_lordship_reference("house_lord=Saturn", "Saturn") is True
        assert _looks_like_lordship_reference("bhava_lord=Jupiter", "Jupiter") is True

    def test_lord_word_near_planet_recognised(self):
        from app.integration.dkp_enhancer import _looks_like_lordship_reference
        assert _looks_like_lordship_reference("4H lord Saturn in Cancer", "Saturn") is True
        assert _looks_like_lordship_reference("Saturn rules the 4H", "Saturn") is True
        assert _looks_like_lordship_reference("Saturn owns 4H", "Saturn") is True

    def test_placement_phrase_NOT_flagged_as_lordship(self):
        from app.integration.dkp_enhancer import _looks_like_lordship_reference
        assert _looks_like_lordship_reference("Saturn in 4H", "Saturn") is False
        assert _looks_like_lordship_reference("Saturn occupies 4H bhava", "Saturn") is False


class TestPydanticInput:
    """enhance() accepts both Pydantic models and dicts — important because
    Track-A's compute() returns a Pydantic model in the in-process path."""

    def test_dict_input_works(self):
        result = enhance(_minimal_reading([]))
        assert isinstance(result, IntegratedReadingOutput)

    def test_basemodel_input_is_dumped_correctly(self):
        from pydantic import BaseModel, ConfigDict

        class FakeReading(BaseModel):
            model_config = ConfigDict(extra="allow")
            domains: dict
            meta: dict

        model = FakeReading(
            domains={"career": {"findings": [], "cross_checks": []}},
            meta={"schema_version": "1.2.0"},
        )
        result = enhance(model)
        assert result.dkp_translations_summary.total_records_attached == 0
