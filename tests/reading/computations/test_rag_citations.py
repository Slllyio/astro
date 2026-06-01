"""Tests for ``app.reading.computations.rag_citations`` (Tier-3 RAG).

Phase 6 Wave A — Tier-3 doctrine citation enrichment.

Discipline asserted by this test file (Spec Section 14):

1.  **Methodology docstring block** — the module MUST publish the
    canonical methodology block so an auditor can read the anti-
    prediction-trap commitments without diving into code.
2.  **Anti-confirmation-bias query construction** — the retrieval query
    MUST be built from ``finding.rule + finding.classification``
    (structural slots) and MUST NOT incorporate ``finding.verdict``.
    Surfacing passages by free-text verdict would let the engine ratify
    itself ("Einstein had X, so X must be true") — the exact failure
    mode the design is built to avoid.
3.  **Famous-chart anti-contamination** — biographical passages naming
    famous-chart figures (Einstein, Gandhi, Steve Jobs, Ramana, APJ
    Kalam, Obama, Nehru) must be filtered out of the citation pool
    because those passages were used in famous-chart fixture pinning.
4.  **Lazy import discipline** — ``sentence_transformers`` must NOT
    appear at module top (would break the Phase 6 Task 6.0 lazy-import
    regression test).
5.  **Eligibility filter** — only Findings with
    ``classification ∈ {promise, yoga, trigger}`` and
    ``confidence.band ∈ {very_strong, medium, high}`` should be enriched.
    All other Findings pass through unchanged.

The retrieval backend is mocked so these tests run without the heavy
sentence-transformers model and without the on-disk knowledge_library
embeddings index.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_finding():
    """Factory returning a Finding with sensible defaults; override per test."""
    from app.reading.schema import ConfidenceScore, Finding

    def _make(
        *,
        id: str = "primitive.karakas.atmakaraka",
        rule: str = "Atmakaraka identification",
        classification: str = "primitive",
        direction: str = "neutral",
        verdict: str = "Atmakaraka is Mercury",
        band: str = "very_strong",
    ) -> Finding:
        return Finding(
            id=id,
            rule=rule,
            source_sequence=None,
            classification=classification,
            direction=direction,
            verdict=verdict,
            evidence=[],
            confidence=ConfidenceScore(
                score=1.0,
                votes={"house": True, "lord": True, "karaka": True},
                band=band,
            ),
        )

    return _make


@pytest.fixture
def fake_search_service(monkeypatch):
    """Patch ``get_default_service`` to return a controllable mock.

    The mock exposes an ``encode``-bearing ``_model`` plus a ``retrieve``
    method that returns a configurable list of ``SearchResult``-shaped
    namespaces. Returning a single mock from this fixture lets each test
    set up its own return values.
    """
    from app.medini.services import knowledge_search as ks_module

    svc = MagicMock()
    svc.ensure_loaded = MagicMock(return_value=None)
    svc._model = MagicMock()
    # Default: encode returns a 2D numpy array of zero vectors, one per query.
    svc._model.encode = MagicMock(
        side_effect=lambda queries, **kw: np.zeros((len(queries), 4), dtype=np.float32)
    )
    svc.retrieve = MagicMock(return_value=())

    monkeypatch.setattr(
        ks_module, "get_default_service", lambda *a, **kw: svc, raising=True,
    )
    return svc


# ---------------------------------------------------------------------------
# Spec Section 14 — methodology block must be present
# ---------------------------------------------------------------------------


class TestMethodologyBlock:
    """Auditable docstring block required by Spec Section 14."""

    def test_module_has_methodology_block(self):
        """The module docstring must publish the Section 14 methodology block."""
        from app.reading.computations import rag_citations

        doc = rag_citations.__doc__ or ""
        assert "Methodology:" in doc, (
            "Spec Section 14 mandates a 'Methodology:' block in every Tier-3 module"
        )

    def test_module_publishes_prediction_trap_declaration(self):
        """The methodology block MUST explicitly declare no prediction fitting."""
        from app.reading.computations import rag_citations

        doc = rag_citations.__doc__ or ""
        assert "Prediction-trap declaration:" in doc

    def test_module_publishes_famous_chart_anti_contamination(self):
        """The methodology block MUST declare famous-chart contamination policy."""
        from app.reading.computations import rag_citations

        doc = rag_citations.__doc__ or ""
        assert "Famous-chart anti-contamination:" in doc


# ---------------------------------------------------------------------------
# Anti-confirmation-bias query construction
# ---------------------------------------------------------------------------


class TestQueryConstruction:
    """Queries MUST be built from rule+slots, NEVER from verdict text."""

    def test_query_does_not_include_verdict(self, make_finding):
        """If the verdict appeared in the retrieval query the engine would
        surface passages that ratify whatever it already said — the exact
        confirmation-bias failure mode the design is built to avoid.
        """
        from app.reading.computations.rag_citations import (
            _build_query_from_rule_slot,
        )

        f = make_finding(
            verdict="VERDICT_TEXT_THAT_MUST_NOT_LEAK_INTO_QUERY",
            rule="Atmakaraka identification",
            classification="primitive",
        )
        query = _build_query_from_rule_slot(f)
        assert "VERDICT_TEXT_THAT_MUST_NOT_LEAK_INTO_QUERY" not in query

    def test_query_includes_rule_name(self, make_finding):
        """The query MUST include the rule name so the index matches doctrine."""
        from app.reading.computations.rag_citations import (
            _build_query_from_rule_slot,
        )

        f = make_finding(rule="Atmakaraka identification")
        query = _build_query_from_rule_slot(f)
        assert "Atmakaraka" in query

    def test_query_includes_classification_slot(self, make_finding):
        """Classification is a structural slot and is fair game in the query."""
        from app.reading.computations.rag_citations import (
            _build_query_from_rule_slot,
        )

        f = make_finding(classification="yoga", rule="Gajakesari Yoga")
        query = _build_query_from_rule_slot(f)
        assert "yoga" in query.lower()


# ---------------------------------------------------------------------------
# Famous-chart anti-contamination filter
# ---------------------------------------------------------------------------


class TestFamousChartContaminationFilter:
    """Biographical passages naming famous-chart figures must be filtered out."""

    @pytest.mark.parametrize(
        "passage",
        [
            "Einstein was born under a powerful Atmakaraka configuration.",
            "Mahatma Gandhi's chart shows the same yoga.",
            "Steve Jobs had a remarkable Atmakaraka.",
            "Ramana Maharshi's spiritual depth came from his AK.",
            "APJ Kalam's chart shows ...",
            "President Obama was born with ...",
            "Nehru's chart was studied by ...",
        ],
    )
    def test_biographical_famous_chart_passages_are_filtered(self, passage):
        from app.reading.computations.rag_citations import (
            _is_biographical_about_famous_chart,
        )

        assert _is_biographical_about_famous_chart(passage) is True

    def test_doctrine_passages_without_famous_names_pass_through(self):
        from app.reading.computations.rag_citations import (
            _is_biographical_about_famous_chart,
        )

        passage = (
            "The Atmakaraka is the planet with the highest degree-within-sign. "
            "It signifies the soul's intent."
        )
        assert _is_biographical_about_famous_chart(passage) is False


# ---------------------------------------------------------------------------
# Eligibility filter
# ---------------------------------------------------------------------------


class TestEligibilityFilter:
    """Only high-confidence promise/yoga/trigger findings should be enriched."""

    def test_primitives_are_passed_through_unchanged(
        self, make_finding, fake_search_service
    ):
        """Primitives are bookkeeping; they don't need doctrine citations.

        They must be returned unchanged (citations stay empty).
        """
        from app.reading.computations.rag_citations import attach_citations

        f = make_finding(classification="primitive", band="very_strong")
        out = attach_citations([f])
        assert len(out) == 1
        assert out[0].citations == []

    def test_low_confidence_findings_are_passed_through_unchanged(
        self, make_finding, fake_search_service
    ):
        """Findings whose band is 'low' or 'indicative_only' get no citations."""
        from app.reading.computations.rag_citations import attach_citations

        f = make_finding(classification="yoga", band="low")
        out = attach_citations([f])
        assert len(out) == 1
        assert out[0].citations == []

    def test_high_confidence_yoga_is_eligible_for_enrichment(
        self, make_finding, fake_search_service
    ):
        """Yoga + very_strong band MUST be passed to the retrieval service."""
        from app.reading.computations.rag_citations import attach_citations

        f = make_finding(
            id="yoga.gajakesari",
            classification="yoga",
            rule="Gajakesari Yoga",
            band="very_strong",
        )
        attach_citations([f])
        # encode must be called with at least one query (the eligible one)
        assert fake_search_service._model.encode.called
        queries_passed = fake_search_service._model.encode.call_args[0][0]
        assert any("Gajakesari" in q for q in queries_passed)


# ---------------------------------------------------------------------------
# End-to-end Citation attachment behaviour
# ---------------------------------------------------------------------------


class TestCitationAttachment:
    """Public API ``attach_citations`` populates Citation lists correctly."""

    def test_attach_citations_returns_new_finding_with_citations(
        self, make_finding, fake_search_service
    ):
        from types import SimpleNamespace

        from app.reading.computations.rag_citations import attach_citations

        # The mock retrieval returns one doctrine-clean passage.
        fake_search_service.retrieve.return_value = (
            SimpleNamespace(
                source="BPHS Vol.I Ch.27",
                text="The Atmakaraka is the planet of highest degree.",
                score=0.92,
                artefact_id="bphs-vol1-ch27-001",
            ),
        )
        f = make_finding(
            id="yoga.gajakesari",
            classification="yoga",
            rule="Gajakesari Yoga",
            band="very_strong",
        )
        out = attach_citations([f])
        assert len(out) == 1
        assert len(out[0].citations) == 1
        c = out[0].citations[0]
        assert c.source == "BPHS Vol.I Ch.27"
        assert c.relevance == pytest.approx(0.92)
        assert c.knowledge_doc_id == "bphs-vol1-ch27-001"
        assert len(c.passage) <= 500

    def test_attach_citations_filters_contaminated_passages(
        self, make_finding, fake_search_service
    ):
        from types import SimpleNamespace

        from app.reading.computations.rag_citations import attach_citations

        fake_search_service.retrieve.return_value = (
            SimpleNamespace(
                source="biography",
                text="Einstein had a powerful Gajakesari Yoga in his chart.",
                score=0.95,
                artefact_id="contam-001",
            ),
            SimpleNamespace(
                source="BPHS Vol.I Ch.27",
                text="Gajakesari Yoga forms when Jupiter is in a kendra from Moon.",
                score=0.85,
                artefact_id="bphs-vol1-ch27-002",
            ),
        )
        f = make_finding(
            id="yoga.gajakesari",
            classification="yoga",
            rule="Gajakesari Yoga",
            band="very_strong",
        )
        out = attach_citations([f])
        # The Einstein passage must be filtered; only the BPHS passage survives.
        citations = out[0].citations
        assert len(citations) == 1
        assert citations[0].knowledge_doc_id == "bphs-vol1-ch27-002"

    def test_attach_citations_preserves_non_eligible_findings(
        self, make_finding, fake_search_service
    ):
        """A mixed list (eligible + non-eligible) must come back complete."""
        from app.reading.computations.rag_citations import attach_citations

        primitive_f = make_finding(
            id="primitive.karakas.atmakaraka",
            classification="primitive",
            band="very_strong",
        )
        yoga_f = make_finding(
            id="yoga.gajakesari",
            classification="yoga",
            rule="Gajakesari Yoga",
            band="very_strong",
        )
        out = attach_citations([primitive_f, yoga_f])
        # Both must be present
        out_ids = {f.id for f in out}
        assert out_ids == {"primitive.karakas.atmakaraka", "yoga.gajakesari"}


# ---------------------------------------------------------------------------
# Lazy-import regression (Phase 6 Task 6.0)
# ---------------------------------------------------------------------------


class TestLazyImportDiscipline:
    """sentence_transformers / torch / knowledge_search must not be at module top."""

    def test_sentence_transformers_not_imported_at_module_top(self):
        """Inspect the module source AST-free: scan for top-level imports."""
        import inspect

        from app.reading.computations import rag_citations

        src = inspect.getsource(rag_citations)
        # Find the docstring-end marker (close of triple-quote) to scope only the
        # top-of-module imports, not internal lazy ones.
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
            # Stop at first function or class definition — everything before it is module-top.
            if stripped.startswith(("def ", "class ", "async def ")):
                break
            top_lines.append(line)
        top_src = "\n".join(top_lines)
        assert "sentence_transformers" not in top_src, (
            "sentence_transformers MUST be imported lazily inside attach_citations"
        )
        # KnowledgeSearchService import is also a heavy chain (pandas already loaded
        # elsewhere; but explicit policy is no get_default_service at module top).
        assert "from app.medini.services" not in top_src
