"""Smoke tests for the 4-critic adversarial verifier + synthesizer.

Uses scripted LLM responses so the threshold logic is verifiable.
"""

from __future__ import annotations

import json

import pytest

from app.integration.narrative.composer import compose_narrative
from app.integration.narrative.critics import (
    CriticReview,
    CriticVerdict,
    _parse_verdict_json,
    run_critics,
)
from app.integration.narrative.synthesizer import (
    VerifiedClaim,
    VerifiedNarrative,
    narrate_and_verify,
)


class ScriptedLLM:
    """LLM stub that returns responses based on prompt content."""

    def __init__(self, scripts: dict[str, str], default: str = '{"verdict": "uncertain", "reason": "default"}'):
        self.scripts = scripts
        self.default = default
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        # Match the LATEST matching key (specific overrides generic).
        for key, response in self.scripts.items():
            if key in prompt:
                return response
        return self.default


def _finding(*, id: str, rule: str, direction: str = "positive",
             classification: str = "primitive", verdict: str = "test") -> dict:
    return {
        "id": id, "rule": rule, "source_sequence": None,
        "classification": classification, "direction": direction,
        "verdict": verdict, "verdict_language": "en", "evidence": [],
        "confidence": {"score": 0.7, "votes": {}, "band": "medium"},
        "enrichment_level": 0, "citations": [],
        "consensus": None, "consensus_status": "not_computed",
        "dispute": None, "robustness": None, "contradicts_finding_ids": [],
    }


def _domain_block(domain: str, direction: str = "positive") -> dict:
    return {
        "domain": domain,
        "promise": _finding(id=f"d.{domain}.promise", rule=f"promise.{domain}",
                            direction=direction, verdict=f"{domain} promise"),
        "triggers": [], "timing_windows": [], "afflictions": [],
        "cross_checks": [], "remedies": [],
        "overall_verdict": _finding(id=f"d.{domain}.overall", rule=f"overall.{domain}",
                                    direction=direction, verdict=f"{domain} overall"),
        "confidence": {"score": 0.7, "votes": {"house": True, "lord": True, "karaka": True}, "band": "high"},
    }


def _reading(domains: list[str]) -> dict:
    return {
        "meta": {"schema_version": "1.2.0"},
        "chart": {}, "primitives": {}, "foundations": {}, "practitioner": {},
        "sequences": {},
        "domains": {d: _domain_block(d) for d in domains},
        "contradictions": [], "warnings": [],
    }


# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------

class TestVerdictJSONParser:
    def test_clean_json_parses(self):
        verdict, reason = _parse_verdict_json('{"verdict": "confirm", "reason": "looks good"}')
        assert verdict == "confirm"
        assert reason == "looks good"

    def test_json_with_surrounding_text_parses(self):
        text = 'Here is my verdict:\n{"verdict": "refute", "reason": "off"}\nThanks!'
        verdict, reason = _parse_verdict_json(text)
        assert verdict == "refute"
        assert reason == "off"

    def test_invalid_verdict_falls_to_uncertain(self):
        verdict, _ = _parse_verdict_json('{"verdict": "yes", "reason": "x"}')
        assert verdict == "uncertain"

    def test_malformed_json_falls_to_uncertain(self):
        verdict, _ = _parse_verdict_json("not json at all")
        assert verdict == "uncertain"

    def test_empty_response_falls_to_uncertain(self):
        verdict, _ = _parse_verdict_json("")
        assert verdict == "uncertain"


# ---------------------------------------------------------------------------
# Critics
# ---------------------------------------------------------------------------

class TestCriticReview:
    def test_four_verdicts_per_domain_with_one_domain(self):
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "confirm", "reason": "ok"}'})
        narrative = compose_narrative(_reading(["career"]), llm=llm)
        review = run_critics(narrative, _reading(["career"]), llm=llm)
        assert review.total_verdicts == 4

    def test_review_covers_all_domains(self):
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "confirm", "reason": "ok"}'})
        narrative = compose_narrative(_reading(["career", "marriage"]), llm=llm)
        review = run_critics(narrative, _reading(["career", "marriage"]), llm=llm)
        assert set(review.domains_reviewed) == {"career", "marriage"}
        assert review.total_verdicts == 8

    def test_each_verdict_has_required_fields(self):
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "confirm", "reason": "ok"}'})
        narrative = compose_narrative(_reading(["career"]), llm=llm)
        review = run_critics(narrative, _reading(["career"]), llm=llm)
        for v in review.per_claim:
            assert v.critic_angle in (
                "bphs_purist", "skeptic", "modern_translator", "contradiction_hunter",
            )
            assert v.verdict in ("confirm", "refute", "uncertain")
            assert v.domain == "career"


# ---------------------------------------------------------------------------
# Synthesizer
# ---------------------------------------------------------------------------

class TestSurvival:
    def test_all_confirm_ships_the_domain(self):
        """When all 4 critics confirm, status = shipped."""
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "confirm", "reason": "ok"}'})
        result = narrate_and_verify(_reading(["career"]), llm=llm)
        assert result.per_domain[0].status == "shipped"
        assert result.per_domain[0].survives is True
        assert "career" in result.domains_shipped

    def test_all_refute_rejects_the_domain(self):
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "refute", "reason": "bad"}'})
        result = narrate_and_verify(_reading(["career"]), llm=llm)
        assert result.per_domain[0].status == "rejected"
        assert result.per_domain[0].survives is False
        assert "career" in result.domains_rejected

    def test_mixed_verdicts_flag_the_domain(self):
        """Without 3 confirms and without 3 refutes — flagged."""
        # Use a stub that always says uncertain.
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "uncertain", "reason": "?"}'})
        result = narrate_and_verify(_reading(["career"]), llm=llm)
        assert result.per_domain[0].status == "flagged"

    def test_survival_threshold_configurable(self):
        """Lowering threshold to 2 makes the same review ship more domains."""
        # Confirm response means 4 confirms always.
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "confirm", "reason": "ok"}'})
        result_strict = narrate_and_verify(_reading(["career"]), llm=llm, survival_threshold=4)
        result_loose = narrate_and_verify(_reading(["career"]), llm=llm, survival_threshold=2)
        # Both should ship since all 4 confirm; the loose one would also ship
        # with fewer confirms but here we just check the threshold is propagated.
        assert result_strict.survival_threshold == 4
        assert result_loose.survival_threshold == 2


class TestVerifiedNarrativeShape:
    def test_per_domain_partitions_consistently(self):
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "confirm", "reason": "ok"}'})
        result = narrate_and_verify(_reading(["career", "marriage"]), llm=llm)
        partition_sizes = (
            len(result.domains_shipped) + len(result.domains_flagged) + len(result.domains_rejected)
        )
        assert partition_sizes == len(result.per_domain)

    def test_confirm_refute_uncertain_counts_sum_to_four_per_claim(self):
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "confirm", "reason": "ok"}'})
        result = narrate_and_verify(_reading(["career"]), llm=llm)
        for claim in result.per_domain:
            assert claim.confirm_count + claim.refute_count + claim.uncertain_count == 4


class TestSerialization:
    def test_verified_narrative_json_roundtrip(self):
        llm = ScriptedLLM({"NARRATIVE": '{"verdict": "confirm", "reason": "ok"}'})
        result = narrate_and_verify(_reading(["career"]), llm=llm)
        as_json = json.dumps(result.model_dump(mode="json"))
        revived = VerifiedNarrative.model_validate(json.loads(as_json))
        assert revived.per_domain[0].status == "shipped"
        assert revived.survival_threshold == 3
