"""Tests for ``app.reading.computations.contradiction_detector`` (Tier-3).

Phase 6 Wave B — detect cross-sequence verdict-direction conflicts.

Discipline asserted by this test file (Spec Section 14):

1.  **Methodology docstring block** — Section 14 mandate.
2.  **Compare `direction` enums ONLY** — the module must NEVER consult
    ``Finding.verdict`` free-text. Verdict is biographical / narrative
    and would re-introduce confirmation bias into a cross-source
    contradiction check.
3.  **Descriptive arbitration only** — the emitted
    ``Contradiction.suggested_arbitration`` is descriptive ("Sequence 5
    says positive, Sequence 6 says negative") and MUST NEVER pick a
    winner ("Sequence 5 wins"). Picking a side is left to the human
    reader / narrator.
4.  **Pass-through when no conflict** — Findings whose directions agree
    or whose ID prefixes share no domain context yield no Contradiction.
5.  **Severity enum** — `"soft"` (different verdicts about same
    question) is the default; `"hard"` is reserved for logical
    impossibilities (yoga detected AND prerequisite missing) and is
    only set when the detector explicitly classifies the conflict that
    way.
6.  **Lazy-import discipline** — no heavy ML stack at module top.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_finding():
    """Factory for Findings with configurable id / direction."""
    from app.reading.schema import ConfidenceScore, Finding

    def _make(
        *,
        id: str,
        rule: str = "PlaceholderRule",
        classification: str = "trigger",
        direction: str = "positive",
        band: str = "medium",
    ) -> Finding:
        return Finding(
            id=id,
            rule=rule,
            source_sequence=None,
            classification=classification,  # type: ignore[arg-type]
            direction=direction,  # type: ignore[arg-type]
            verdict="placeholder",
            evidence=[],
            confidence=ConfidenceScore(
                score=0.6,
                votes={"house": True, "lord": False, "karaka": True},
                band=band,  # type: ignore[arg-type]
            ),
        )

    return _make


@pytest.fixture
def make_reading_output():
    """Factory for a minimal ReadingOutput-shaped dict with a populated domains block."""

    def _make(
        *,
        domain_findings: dict[str, list] | None = None,
        sequence_findings: list | None = None,
    ) -> dict:
        # Flatten domain findings into top-level lists for the detector
        # to inspect. The detector consumes the `findings` accumulator
        # collected from blocks; we approximate with a flat list.
        out = {
            "_all_findings": [],
        }
        if domain_findings:
            for _domain, findings in domain_findings.items():
                out["_all_findings"].extend(findings)
        if sequence_findings:
            out["_all_findings"].extend(sequence_findings)
        return out

    return _make


# ---------------------------------------------------------------------------
# Spec Section 14 — methodology block must be present
# ---------------------------------------------------------------------------


class TestMethodologyBlock:
    """Auditable docstring block required by Spec Section 14."""

    def test_module_has_methodology_block(self):
        from app.reading.computations import contradiction_detector

        doc = contradiction_detector.__doc__ or ""
        assert "Methodology:" in doc

    def test_module_publishes_prediction_trap_declaration(self):
        from app.reading.computations import contradiction_detector

        doc = contradiction_detector.__doc__ or ""
        assert "Prediction-trap declaration:" in doc

    def test_module_publishes_famous_chart_anti_contamination(self):
        from app.reading.computations import contradiction_detector

        doc = contradiction_detector.__doc__ or ""
        assert "Famous-chart anti-contamination:" in doc

    def test_module_publishes_verdict_field_ban(self):
        """The module must explicitly declare it ignores ``Finding.verdict``."""
        from app.reading.computations import contradiction_detector

        doc = contradiction_detector.__doc__ or ""
        assert "verdict" in doc.lower()


# ---------------------------------------------------------------------------
# Detection: direction-mismatch within shared domain context
# ---------------------------------------------------------------------------


class TestDirectionMismatch:
    """Two findings in the same domain with conflicting directions."""

    def test_domain_career_positive_vs_sequence_negative_emits_contradiction(
        self, make_finding, make_reading_output
    ):
        from app.reading.computations.contradiction_detector import (
            detect_contradictions,
        )

        f_positive = make_finding(
            id="domain.career.10l_strong",
            direction="positive",
        )
        f_negative = make_finding(
            id="seq_5.md_3.career_check",
            rule="career check",
            direction="negative",
        )
        out = detect_contradictions(
            make_reading_output(sequence_findings=[f_positive, f_negative])
        )
        assert len(out) == 1
        c = out[0]
        assert set(c.finding_ids) == {f_positive.id, f_negative.id}
        # Severity defaults to "soft" — directional disagreement
        assert c.severity == "soft"
        # Descriptive arbitration only, never picks a winner
        assert c.suggested_arbitration is not None
        lower = c.suggested_arbitration.lower()
        assert "positive" in lower
        assert "negative" in lower

    def test_same_domain_agreeing_directions_no_contradiction(
        self, make_finding, make_reading_output
    ):
        from app.reading.computations.contradiction_detector import (
            detect_contradictions,
        )

        f1 = make_finding(id="domain.marriage.7l_strong", direction="positive")
        f2 = make_finding(
            id="seq_5.md_3.marriage_check",
            rule="marriage check",
            direction="positive",
        )
        out = detect_contradictions(
            make_reading_output(sequence_findings=[f1, f2])
        )
        assert out == []

    def test_neutral_vs_positive_does_not_contradict(
        self, make_finding, make_reading_output
    ):
        """Neutral is not a substantive disagreement."""
        from app.reading.computations.contradiction_detector import (
            detect_contradictions,
        )

        f1 = make_finding(id="domain.health.6l_strong", direction="neutral")
        f2 = make_finding(
            id="seq_5.md_3.health_check",
            rule="health check",
            direction="positive",
        )
        out = detect_contradictions(
            make_reading_output(sequence_findings=[f1, f2])
        )
        assert out == []

    def test_different_domain_contexts_no_contradiction(
        self, make_finding, make_reading_output
    ):
        """Career-positive and Marriage-negative are not contradictions."""
        from app.reading.computations.contradiction_detector import (
            detect_contradictions,
        )

        f1 = make_finding(id="domain.career.10l_strong", direction="positive")
        f2 = make_finding(
            id="domain.marriage.7l_weak",
            rule="marriage rule",
            direction="negative",
        )
        out = detect_contradictions(
            make_reading_output(sequence_findings=[f1, f2])
        )
        assert out == []


# ---------------------------------------------------------------------------
# Discipline: detector must not consult Finding.verdict free-text
# ---------------------------------------------------------------------------


class TestVerdictNotConsulted:
    """The detector compares ``direction`` enums ONLY, never ``verdict``."""

    def test_same_directions_but_opposite_verdict_text_does_NOT_contradict(
        self, make_finding, make_reading_output
    ):
        """Two findings whose direction agree must not contradict.

        Even if their verdict free-text reads contradictorily, the engine
        does NOT use verdict for cross-source diff (it would reintroduce
        biographical confirmation bias).
        """
        from app.reading.computations.contradiction_detector import (
            detect_contradictions,
        )
        from app.reading.schema import ConfidenceScore, Finding

        f1 = Finding(
            id="domain.career.10l_strong",
            rule="career strength",
            source_sequence=None,
            classification="trigger",
            direction="positive",
            verdict="GREAT for career",
            evidence=[],
            confidence=ConfidenceScore(
                score=0.6,
                votes={"house": True, "lord": True, "karaka": True},
                band="medium",
            ),
        )
        f2 = Finding(
            id="seq_5.md_3.career_check",
            rule="career check",
            source_sequence="seq_5",
            classification="trigger",
            direction="positive",
            verdict="DISASTER for career",
            evidence=[],
            confidence=ConfidenceScore(
                score=0.6,
                votes={"house": True, "lord": True, "karaka": True},
                band="medium",
            ),
        )
        out = detect_contradictions(
            make_reading_output(sequence_findings=[f1, f2])
        )
        # Same direction → no contradiction, even though verdict text disagrees.
        assert out == []


# ---------------------------------------------------------------------------
# Suggested arbitration discipline
# ---------------------------------------------------------------------------


class TestArbitrationDescriptiveOnly:
    """suggested_arbitration is descriptive — never picks a winner."""

    def test_arbitration_does_not_say_wins(
        self, make_finding, make_reading_output
    ):
        from app.reading.computations.contradiction_detector import (
            detect_contradictions,
        )

        f1 = make_finding(id="domain.wealth.2l_strong", direction="positive")
        f2 = make_finding(
            id="seq_5.md_3.wealth_check",
            rule="wealth check",
            direction="negative",
        )
        out = detect_contradictions(
            make_reading_output(sequence_findings=[f1, f2])
        )
        assert len(out) == 1
        arb = (out[0].suggested_arbitration or "").lower()
        for forbidden in (" wins", "winner", "correct side", "engine prefers"):
            assert forbidden not in arb, (
                f"arbitration text must not pick a winner — found {forbidden!r}"
            )


# ---------------------------------------------------------------------------
# Empty / pass-through behaviour
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Detector handles empty / minimal inputs gracefully."""

    def test_empty_findings_returns_empty_list(self, make_reading_output):
        from app.reading.computations.contradiction_detector import (
            detect_contradictions,
        )

        out = detect_contradictions(make_reading_output())
        assert out == []


# ---------------------------------------------------------------------------
# Lazy-import regression
# ---------------------------------------------------------------------------


class TestLazyImportDiscipline:
    """No sentence_transformers / torch / knowledge_search at module top."""

    def test_sentence_transformers_not_imported_at_module_top(self):
        import inspect

        from app.reading.computations import contradiction_detector

        src = inspect.getsource(contradiction_detector)
        lines = src.splitlines()
        top_lines: list[str] = []
        in_doc = False
        doc_closed = False
        for line in lines:
            stripped = line.strip()
            if not doc_closed:
                if stripped.startswith('"""') and not in_doc:
                    in_doc = True
                    if stripped.endswith('"""') and len(stripped) > 3:
                        in_doc = False
                        doc_closed = True
                    continue
                if in_doc and stripped.endswith('"""'):
                    in_doc = False
                    doc_closed = True
                    continue
                if in_doc:
                    continue
                doc_closed = True
            if stripped.startswith(("def ", "class ", "async def ")):
                break
            top_lines.append(line)
        top_src = "\n".join(top_lines)
        assert "sentence_transformers" not in top_src
        assert "from app.medini.services" not in top_src
