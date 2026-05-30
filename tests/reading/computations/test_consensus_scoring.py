"""Tests for ``app.reading.computations.consensus_scoring`` (Tier-3).

Phase 6 Wave A — cross-source doctrine consensus scoring.

Discipline asserted by this test file (Spec Section 14):

1.  **Methodology docstring block** — auditable Section 14 block.
2.  **Scope of "agreement"** — agreement is over rule-applicability
    statements (e.g. "this configuration is *called* Gajakesari"),
    NEVER over outcome claims (e.g. "Gajakesari produces wealth"); the
    latter would be a fitted prediction claim, which v1 refuses to make.
3.  **Low-consensus flag** — when ``sources_agreeing / sources_total <
    0.5`` the finding is flagged for downstream UI surface.
4.  **No fabrication** — Findings with zero citations are returned with
    ``consensus = None`` and ``consensus_status = "no_agreement"`` (NOT
    a fabricated zero score); Findings with citations get a real
    ConsensusScore.
5.  **Lazy-import discipline** — same as rag_citations: no heavy ML
    stack at module top.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_finding_with_citations():
    """Factory for a Finding with a configurable citation list."""
    from app.reading.schema import Citation, ConfidenceScore, Finding

    def _make(
        *,
        rule: str = "Gajakesari Yoga",
        classification: str = "yoga",
        citations: list[dict] | None = None,
        band: str = "very_strong",
        id_suffix: str = "ok",
    ) -> Finding:
        citation_objs = [
            Citation(
                source=c["source"],
                passage=c["passage"],
                relevance=c.get("relevance", 0.8),
                knowledge_doc_id=c.get("knowledge_doc_id", "doc-001"),
            )
            for c in (citations or [])
        ]
        return Finding(
            id=f"yoga.{id_suffix}",
            rule=rule,
            source_sequence=None,
            classification=classification,  # type: ignore[arg-type]
            direction="positive",
            verdict="placeholder",
            evidence=[],
            confidence=ConfidenceScore(
                score=1.0,
                votes={"house": True, "lord": True, "karaka": True},
                band=band,  # type: ignore[arg-type]
            ),
            citations=citation_objs,
        )

    return _make


# ---------------------------------------------------------------------------
# Spec Section 14 — methodology block must be present
# ---------------------------------------------------------------------------


class TestMethodologyBlock:
    """Auditable docstring block required by Spec Section 14."""

    def test_module_has_methodology_block(self):
        from app.reading.computations import consensus_scoring

        doc = consensus_scoring.__doc__ or ""
        assert "Methodology:" in doc

    def test_module_publishes_prediction_trap_declaration(self):
        from app.reading.computations import consensus_scoring

        doc = consensus_scoring.__doc__ or ""
        assert "Prediction-trap declaration:" in doc

    def test_module_publishes_famous_chart_anti_contamination(self):
        from app.reading.computations import consensus_scoring

        doc = consensus_scoring.__doc__ or ""
        assert "Famous-chart anti-contamination:" in doc


# ---------------------------------------------------------------------------
# No-citation findings: no consensus computed
# ---------------------------------------------------------------------------


class TestNoCitationHandling:
    """A Finding with zero citations must NOT fabricate a consensus score."""

    def test_finding_without_citations_gets_no_consensus(
        self, make_finding_with_citations
    ):
        from app.reading.computations.consensus_scoring import score_consensus

        f = make_finding_with_citations(citations=None)
        out = score_consensus([f])
        assert len(out) == 1
        assert out[0].consensus is None
        assert out[0].consensus_status == "no_agreement"

    def test_non_eligible_classification_passed_through(
        self, make_finding_with_citations
    ):
        """Primitives still get consensus_status set, never silently fabricated."""
        from app.reading.computations.consensus_scoring import score_consensus

        f = make_finding_with_citations(
            classification="primitive",
            citations=[
                {"source": "BPHS", "passage": "Atmakaraka is called the soul karaka."}
            ],
        )
        out = score_consensus([f])
        assert len(out) == 1
        # primitives are skipped entirely — consensus_status remains the schema default
        assert out[0].consensus is None


# ---------------------------------------------------------------------------
# Agreement scope — rule-applicability statements only
# ---------------------------------------------------------------------------


class TestRuleApplicabilityAgreement:
    """Agreement counts ONLY rule-applicability passages, never outcome claims."""

    def test_is_called_statement_counts_as_agreeing(self):
        from app.reading.computations.consensus_scoring import (
            _is_rule_applicability_statement,
        )

        passage = "Gajakesari Yoga is called the elephant-lion yoga."
        assert _is_rule_applicability_statement(passage, rule_name="Gajakesari") is True

    def test_is_termed_statement_counts_as_agreeing(self):
        from app.reading.computations.consensus_scoring import (
            _is_rule_applicability_statement,
        )

        passage = "This configuration is termed Gajakesari Yoga."
        assert _is_rule_applicability_statement(passage, rule_name="Gajakesari") is True

    def test_is_known_as_statement_counts_as_agreeing(self):
        from app.reading.computations.consensus_scoring import (
            _is_rule_applicability_statement,
        )

        passage = "Jupiter in kendra from Moon is known as Gajakesari."
        assert _is_rule_applicability_statement(passage, rule_name="Gajakesari") is True

    def test_outcome_claim_does_not_count(self):
        """'Produces wealth / fame' is a fitted prediction claim — refuse."""
        from app.reading.computations.consensus_scoring import (
            _is_rule_applicability_statement,
        )

        passage = "Gajakesari Yoga produces wealth and fame to the native."
        assert (
            _is_rule_applicability_statement(passage, rule_name="Gajakesari")
            is False
        )

    def test_passage_missing_rule_name_does_not_count(self):
        from app.reading.computations.consensus_scoring import (
            _is_rule_applicability_statement,
        )

        passage = "This combination is called a Raja Yoga."
        assert (
            _is_rule_applicability_statement(passage, rule_name="Gajakesari")
            is False
        )


# ---------------------------------------------------------------------------
# Public API: score_consensus end-to-end
# ---------------------------------------------------------------------------


class TestScoreConsensusEndToEnd:
    """End-to-end behavior of score_consensus over a list of findings."""

    def test_two_of_two_sources_agree_yields_score_one(
        self, make_finding_with_citations
    ):
        from app.reading.computations.consensus_scoring import score_consensus

        f = make_finding_with_citations(
            rule="Gajakesari Yoga",
            citations=[
                {
                    "source": "BPHS Vol.I",
                    "passage": "Jupiter in kendra from Moon is called Gajakesari Yoga.",
                },
                {
                    "source": "Phaladeepika",
                    "passage": "This combination is termed Gajakesari.",
                },
            ],
        )
        out = score_consensus([f])
        assert out[0].consensus is not None
        assert out[0].consensus.sources_total == 2
        assert out[0].consensus.sources_agreeing == 2
        assert out[0].consensus.score == pytest.approx(1.0)
        assert out[0].consensus.low_consensus_flag is False
        assert out[0].consensus_status == "computed"

    def test_one_of_two_yields_low_consensus_flag(
        self, make_finding_with_citations
    ):
        from app.reading.computations.consensus_scoring import score_consensus

        f = make_finding_with_citations(
            rule="Gajakesari Yoga",
            citations=[
                {
                    "source": "BPHS Vol.I",
                    "passage": "Jupiter in kendra from Moon is called Gajakesari Yoga.",
                },
                {
                    "source": "modern blog",
                    "passage": "Gajakesari produces immense wealth — outcome claim.",
                },
            ],
        )
        out = score_consensus([f])
        assert out[0].consensus is not None
        assert out[0].consensus.sources_total == 2
        assert out[0].consensus.sources_agreeing == 1
        assert out[0].consensus.score == pytest.approx(0.5)
        # threshold is < 0.5 → flag; 0.5 itself is the boundary which is NOT flagged
        assert out[0].consensus.low_consensus_flag is False

    def test_zero_agree_of_two_yields_low_consensus_flag(
        self, make_finding_with_citations
    ):
        from app.reading.computations.consensus_scoring import score_consensus

        f = make_finding_with_citations(
            rule="Gajakesari Yoga",
            citations=[
                {
                    "source": "modern blog A",
                    "passage": "Gajakesari produces wealth.",
                },
                {
                    "source": "modern blog B",
                    "passage": "This yoga gives fame.",
                },
            ],
        )
        out = score_consensus([f])
        assert out[0].consensus is not None
        assert out[0].consensus.sources_agreeing == 0
        assert out[0].consensus.score == pytest.approx(0.0)
        assert out[0].consensus.low_consensus_flag is True


# ---------------------------------------------------------------------------
# Lazy-import regression
# ---------------------------------------------------------------------------


class TestLazyImportDiscipline:
    """No sentence_transformers / torch / knowledge_search at module top."""

    def test_sentence_transformers_not_imported_at_module_top(self):
        import inspect

        from app.reading.computations import consensus_scoring

        src = inspect.getsource(consensus_scoring)
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
