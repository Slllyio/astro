"""Smoke tests for the narrative composer.

Uses a deterministic ScriptedLLM (extending StubClient) so tests are
fast + reproducible without real LLM calls.
"""

from __future__ import annotations

import json

import pytest

from app.integration.narrative.composer import (
    DomainNarrative,
    NarrativeOutput,
    compose_narrative,
)
from app.llm.client import StubClient


class CountingStubLLM:
    """LLM stub that returns a fixed paragraph and counts calls."""

    def __init__(self, response: str = "Stub narrative paragraph for testing.") -> None:
        self.response = response
        self.calls: list[str] = []

    def complete(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.response


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
        "triggers": [],
        "timing_windows": [],
        "afflictions": [],
        "cross_checks": [],
        "remedies": [],
        "overall_verdict": _finding(id=f"d.{domain}.overall", rule=f"overall.{domain}",
                                    direction=direction, verdict=f"{domain} overall"),
        "confidence": {"score": 0.7, "votes": {"house": True, "lord": True, "karaka": True}, "band": "high"},
    }


def _reading_with(domains_present: list[str]) -> dict:
    domains_block = {d: _domain_block(d) for d in domains_present}
    return {
        "meta": {"schema_version": "1.2.0"},
        "chart": {}, "primitives": {}, "foundations": {}, "practitioner": {},
        "sequences": {},
        "domains": domains_block,
        "contradictions": [], "warnings": [],
    }


class TestComposerMechanics:
    def test_returns_narrative_output(self):
        llm = CountingStubLLM("para")
        out = compose_narrative(_reading_with(["career"]), llm=llm)
        assert isinstance(out, NarrativeOutput)

    def test_one_paragraph_per_populated_domain(self):
        llm = CountingStubLLM("para")
        out = compose_narrative(_reading_with(["career", "marriage"]), llm=llm)
        assert len(out.per_domain) == 2

    def test_missing_domain_skipped(self):
        llm = CountingStubLLM("para")
        out = compose_narrative(_reading_with(["career"]), llm=llm)
        assert {n.domain for n in out.per_domain} == {"career"}

    def test_llm_provider_name_recorded(self):
        llm = CountingStubLLM("para")
        out = compose_narrative(_reading_with(["career"]), llm=llm)
        assert out.llm_provider == "CountingStubLLM"

    def test_llm_called_once_per_domain_plus_one_summary(self):
        llm = CountingStubLLM("para")
        out = compose_narrative(_reading_with(["career", "marriage", "wealth"]), llm=llm)
        # 3 domain prompts + 1 summary prompt
        assert len(llm.calls) == 4


class TestDomainNarrativeShape:
    def test_overall_direction_propagated(self):
        llm = CountingStubLLM("para")
        out = compose_narrative(_reading_with(["career"]), llm=llm)
        assert out.per_domain[0].overall_direction == "positive"

    def test_bhava_set_for_each_domain(self):
        llm = CountingStubLLM("para")
        out = compose_narrative(
            _reading_with(["career", "marriage", "children", "wealth", "health", "education"]),
            llm=llm,
        )
        bhavas = {n.domain: n.bhava for n in out.per_domain}
        assert bhavas == {"career": 10, "marriage": 7, "children": 5,
                          "wealth": 2, "health": 6, "education": 4}

    def test_cited_findings_includes_promise_and_overall(self):
        llm = CountingStubLLM("para")
        out = compose_narrative(_reading_with(["career"]), llm=llm)
        cited = set(out.per_domain[0].cited_findings)
        assert "promise.career" in cited
        assert "overall.career" in cited


class TestDefaultStubFallback:
    def test_no_llm_uses_stub(self):
        out = compose_narrative(_reading_with(["career"]))
        # StubClient is the fallback
        assert out.llm_provider == "StubClient"

    def test_stub_returns_canned_response(self):
        out = compose_narrative(_reading_with(["career"]))
        assert "stub" in out.per_domain[0].paragraph.lower()


class TestEmptyReading:
    def test_no_domains_yields_empty_per_domain_and_placeholder_summary(self):
        out = compose_narrative(_reading_with([]))
        assert out.per_domain == []
        assert "no domains" in out.overall_summary.lower()


class TestSerialization:
    def test_narrative_output_json_roundtrip(self):
        llm = CountingStubLLM("para")
        out = compose_narrative(_reading_with(["career"]), llm=llm)
        as_json = json.dumps(out.model_dump(mode="json"))
        revived = NarrativeOutput.model_validate(json.loads(as_json))
        assert len(revived.per_domain) == 1
        assert revived.per_domain[0].domain == "career"
