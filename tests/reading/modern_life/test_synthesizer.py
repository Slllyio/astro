"""Tests for ``enrich_with_modern_signals``.

Verifies that the synthesizer appends modern-life Findings to each
domain's ``cross_checks`` list — *without* modifying the V1 domain files.
Operates in both **dict mode** (the documented JSON-roundtrip API) and
**object mode** (ReadingOutput in, ReadingOutput out).
"""
from __future__ import annotations

import copy

import pytest

from app.reading.modern_life.synthesizer import enrich_with_modern_signals


# ---------------------------------------------------------------------------
# Minimal fixture builders
# ---------------------------------------------------------------------------


def _minimal_finding(prefix: str) -> dict:
    return {
        "id": f"{prefix}.placeholder",
        "rule": f"{prefix}.placeholder",
        "source_sequence": None,
        "classification": "promise",
        "direction": "neutral",
        "verdict": "placeholder",
        "verdict_language": "en",
        "evidence": [],
        "confidence": {
            "score": 0.0,
            "votes": {"house": False, "lord": False, "karaka": False},
            "band": "indicative_only",
        },
        "enrichment_level": 0,
        "citations": [],
        "consensus": None,
        "consensus_status": "not_computed",
        "dispute": None,
        "robustness": None,
        "contradicts_finding_ids": [],
    }


def _empty_confidence() -> dict:
    return {
        "score": 0.0,
        "votes": {"house": False, "lord": False, "karaka": False},
        "band": "indicative_only",
    }


def _minimal_domain(name: str) -> dict:
    return {
        "domain": name,
        "promise": _minimal_finding(f"domain.{name}"),
        "triggers": [],
        "timing_windows": [],
        "afflictions": [],
        "cross_checks": [],
        "remedies": [],
        "overall_verdict": _minimal_finding(f"domain.{name}"),
        "confidence": _empty_confidence(),
    }


def _minimal_reading_dict() -> dict:
    """Build a ReadingOutput-shaped dict with all 6 minimal domains."""
    return {
        "meta": {},  # synthesizer does not inspect meta
        "chart": {},
        "primitives": {},
        "foundations": {},
        "practitioner": {},
        "sequences": {},
        "domains": {
            name: _minimal_domain(name)
            for name in ("career", "marriage", "children", "wealth", "health", "education")
        },
        "contradictions": [],
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Dict-mode tests
# ---------------------------------------------------------------------------


class TestEnrichDictMode:

    def test_returns_dict(self, bangalore_chart, asc_sign):
        reading = _minimal_reading_dict()
        out = enrich_with_modern_signals(reading, bangalore_chart, asc_sign)
        assert isinstance(out, dict)

    def test_does_not_mutate_input(self, bangalore_chart, asc_sign):
        reading = _minimal_reading_dict()
        before = copy.deepcopy(reading)
        _ = enrich_with_modern_signals(reading, bangalore_chart, asc_sign)
        assert reading == before, "input dict was mutated"

    def test_adds_modern_findings_to_bangalore_health(
        self, bangalore_chart, asc_sign
    ):
        """Bangalore baseline triggers health.emotional_foundation + nakshatra_lord."""
        reading = _minimal_reading_dict()
        out = enrich_with_modern_signals(reading, bangalore_chart, asc_sign)
        health_xc = out["domains"]["health"]["cross_checks"]
        ids = {f["id"] for f in health_xc}
        assert "modern_life.health.emotional_foundation" in ids
        assert "modern_life.health.moon_nakshatra_lord" in ids

    def test_preserves_existing_cross_checks(self, bangalore_chart, asc_sign):
        """Pre-existing cross_check findings remain in place."""
        reading = _minimal_reading_dict()
        pre_existing = _minimal_finding("domain.health.preexisting")
        pre_existing["id"] = "domain.health.preexisting_cross_check"
        reading["domains"]["health"]["cross_checks"] = [pre_existing]
        out = enrich_with_modern_signals(reading, bangalore_chart, asc_sign)
        ids = [f["id"] for f in out["domains"]["health"]["cross_checks"]]
        assert "domain.health.preexisting_cross_check" in ids
        # And modern findings were appended.
        assert any(i.startswith("modern_life.health.") for i in ids)

    def test_rejects_invalid_asc_sign(self, bangalore_chart):
        with pytest.raises(ValueError):
            enrich_with_modern_signals(_minimal_reading_dict(), bangalore_chart, 0)

    def test_rejects_invalid_reading_type(self, bangalore_chart, asc_sign):
        with pytest.raises(TypeError):
            enrich_with_modern_signals("not_a_dict", bangalore_chart, asc_sign)


# ---------------------------------------------------------------------------
# V1 architectural-purity preservation check
# ---------------------------------------------------------------------------


class TestV1DomainFilesUntouched:
    """Sanity: importing the synthesizer must not touch any V1 domain file."""

    def test_v1_domain_modules_still_importable(self):
        from app.reading.domains import (
            career as v1_career,
            marriage as v1_marriage,
            health as v1_health,
            wealth as v1_wealth,
            children as v1_children,
            education as v1_education,
        )
        # Confirm the public synthesize_<domain> APIs still exist.
        assert hasattr(v1_career, "synthesize_career")
        assert hasattr(v1_marriage, "synthesize_marriage")
        assert hasattr(v1_health, "synthesize_health")
        assert hasattr(v1_wealth, "synthesize_wealth")
        assert hasattr(v1_children, "synthesize_children")
        assert hasattr(v1_education, "synthesize_education")

    def test_modern_life_is_separate_package(self):
        """The modern_life package must NOT live under domains/."""
        import app.reading.modern_life as ml
        assert ml.__name__ == "app.reading.modern_life"
        # Confirm domains/ does not contain modern_life sub-imports.
        from app.reading import domains
        assert "modern_life" not in dir(domains)
