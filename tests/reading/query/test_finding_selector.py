"""Tests for ``app.reading.query.finding_selector``.

Coverage:
- Each per-intent selector returns relevant findings
- MAX_FINDINGS hard cap is respected
- Selection is deterministic
- Selection from the Bangalore baseline produces non-empty results
  for at least the GENERIC and DASHA intents (chart is fully populated)
- IDs returned by ``select_finding_ids`` are a subset of the IDs of the
  selected findings
"""
from __future__ import annotations

from typing import Any

import pytest

from app.reading.query.finding_selector import (
    MAX_FINDINGS,
    select_findings,
    select_finding_ids,
)
from app.reading.query.intent_classifier import IntentClassification, classify_intent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_classification(intent: str, entities: list[str] | None = None) -> IntentClassification:
    return IntentClassification(
        intent=intent,  # type: ignore[arg-type]
        confidence=1.0,
        extracted_entities=entities or [],
    )


# ---------------------------------------------------------------------------
# Bangalore baseline-driven smoke tests
# ---------------------------------------------------------------------------


def test_generic_selection_nonempty_on_baseline(bangalore_reading: dict) -> None:
    """GENERIC selection on the Bangalore baseline returns at least 1 finding."""
    cls = _make_classification("GENERIC")
    findings = select_findings(bangalore_reading, cls)
    assert len(findings) >= 1
    assert len(findings) <= MAX_FINDINGS


def test_dasha_selection_nonempty_on_baseline(bangalore_reading: dict) -> None:
    """DASHA selection returns MD overall verdicts from the baseline reading."""
    cls = _make_classification("DASHA")
    findings = select_findings(bangalore_reading, cls)
    assert len(findings) >= 1
    assert all(isinstance(f, dict) for f in findings)


def test_timing_selection_returns_md_overall_verdicts(bangalore_reading: dict) -> None:
    """TIMING selection includes MD/AD overall_verdicts when present."""
    cls = _make_classification("TIMING")
    findings = select_findings(bangalore_reading, cls)
    # The baseline has MD judgments so at least 1 timing finding should be returned.
    assert len(findings) >= 1
    assert len(findings) <= MAX_FINDINGS


def test_yoga_selection_only_returns_yogas(bangalore_reading: dict) -> None:
    """YOGA selection returns only findings classified as 'yoga'."""
    cls = _make_classification("YOGA")
    findings = select_findings(bangalore_reading, cls)
    for f in findings:
        assert f.get("classification") == "yoga"


def test_planet_selection_filters_by_entity_mention(bangalore_reading: dict) -> None:
    """PLANET selection includes findings mentioning the named planet.

    The selector scans id + rule + verdict + evidence (see ``_mention_blob``
    in finding_selector). Gulika findings, for example, mention Saturn in
    their evidence because Gulika is computed from Saturn — this test
    asserts the blob (including evidence) carries the entity.
    """
    cls = _make_classification("PLANET", entities=["saturn"])
    findings = select_findings(bangalore_reading, cls)
    for f in findings:
        parts = [
            str(f.get("id", "")),
            str(f.get("rule", "")),
            str(f.get("verdict", "")),
        ]
        evidence = f.get("evidence") or []
        if isinstance(evidence, list):
            parts.extend(str(e) for e in evidence)
        blob = " ".join(parts).lower()
        assert "saturn" in blob


def test_domain_selection_returns_domain_findings(bangalore_reading: dict) -> None:
    """DOMAIN selection with 'marriage' entity returns marriage block findings."""
    cls = _make_classification("DOMAIN", entities=["marriage"])
    findings = select_findings(bangalore_reading, cls)
    # Marriage block exists in baseline output — should return at least
    # promise + overall_verdict.
    assert len(findings) >= 1


# ---------------------------------------------------------------------------
# Hard cap + degenerate inputs
# ---------------------------------------------------------------------------


def test_max_findings_cap_enforced(bangalore_reading: dict) -> None:
    """Every per-intent selector caps at MAX_FINDINGS."""
    for intent in ("TIMING", "DOMAIN", "PLANET", "DASHA", "YOGA", "GENERIC"):
        cls = _make_classification(intent, entities=["saturn", "marriage"])
        findings = select_findings(bangalore_reading, cls)
        assert len(findings) <= MAX_FINDINGS


def test_empty_reading_returns_empty_list() -> None:
    """An empty reading dict returns no findings for any intent."""
    cls = _make_classification("DASHA")
    findings = select_findings({}, cls)
    assert findings == []


def test_non_dict_reading_returns_empty_list() -> None:
    """A non-dict reading returns an empty list (defensive)."""
    cls = _make_classification("GENERIC")
    assert select_findings(None, cls) == []  # type: ignore[arg-type]
    assert select_findings("not a dict", cls) == []  # type: ignore[arg-type]


def test_domain_selection_unknown_entity_returns_empty(bangalore_reading: dict) -> None:
    """DOMAIN selection with an entity that is not a real domain -> []."""
    cls = _make_classification("DOMAIN", entities=["fictional_domain"])
    findings = select_findings(bangalore_reading, cls)
    assert findings == []


def test_planet_selection_no_entities_returns_empty(bangalore_reading: dict) -> None:
    """PLANET selection without any extracted entities -> []."""
    cls = _make_classification("PLANET", entities=[])
    findings = select_findings(bangalore_reading, cls)
    assert findings == []


# ---------------------------------------------------------------------------
# Determinism + IDs
# ---------------------------------------------------------------------------


def test_selection_is_deterministic(bangalore_reading: dict) -> None:
    """Same inputs -> same selected findings (no random ordering)."""
    cls = _make_classification("DASHA")
    a = select_findings(bangalore_reading, cls)
    b = select_findings(bangalore_reading, cls)
    assert [_id(f) for f in a] == [_id(f) for f in b]


def test_select_finding_ids_matches_select_findings(bangalore_reading: dict) -> None:
    """``select_finding_ids`` IDs are a subset of ``select_findings`` IDs."""
    cls = _make_classification("DASHA")
    findings = select_findings(bangalore_reading, cls)
    ids = select_finding_ids(bangalore_reading, cls)
    finding_ids = {_id(f) for f in findings if _id(f)}
    assert set(ids).issubset(finding_ids)


def test_via_classifier_end_to_end(bangalore_reading: dict) -> None:
    """Classifier -> selector pipeline succeeds for a real question."""
    cls = classify_intent("Tell me about my current mahadasha")
    findings = select_findings(bangalore_reading, cls)
    assert cls.intent == "DASHA"
    assert len(findings) >= 1


# ---------------------------------------------------------------------------
# Local helper used in tests
# ---------------------------------------------------------------------------


def _id(f: dict[str, Any]) -> str | None:
    return f.get("id") if isinstance(f, dict) else None
