"""Tests for ``app.reading.computations.dispute_surfacing`` (Tier-3).

Phase 6 Wave A — surface lockfile-documented doctrine disagreements.

Discipline asserted by this test file (Spec Section 14):

1.  **Methodology docstring block** — Section 14 mandate.
2.  **Lockfile-driven dispute table** — disputes flagged by this module
    correspond to entries documented in ``docs/doctrine-decisions.md``
    (D-10 karaka triangulation alternative, D-11 Neech Bhanga alternative
    rules, D-3 Vimsopaka scheme alternative, ...). The module ships a
    static dispute table for v1; doctrine-version detection from RAG
    is out of scope.
3.  **No engine-preferred-side leakage** — the emitted Dispute object
    must NEVER carry an ``is_correct`` / ``engine_preferred`` field;
    this is already enforced by ``schema.py`` (Dispute has no such
    field), but a test here documents the intent.
4.  **Pass-through behaviour** — Findings whose rules are NOT in the
    known-dispute table are returned unchanged (``dispute = None``).
5.  **Lazy-import discipline** — no heavy ML stack at module top.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_finding():
    """Factory for Findings — overrides the rule per test."""
    from app.reading.schema import ConfidenceScore, Finding

    def _make(
        *,
        rule: str = "Karaka Triangulation (marriage)",
        rule_id_suffix: str = "marriage",
        classification: str = "trigger",
        band: str = "very_strong",
    ) -> Finding:
        return Finding(
            id=f"domain.marriage.karaka_triangulation_{rule_id_suffix}",
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
        )

    return _make


# ---------------------------------------------------------------------------
# Spec Section 14 — methodology block must be present
# ---------------------------------------------------------------------------


class TestMethodologyBlock:
    """Auditable docstring block required by Spec Section 14."""

    def test_module_has_methodology_block(self):
        from app.reading.computations import dispute_surfacing

        doc = dispute_surfacing.__doc__ or ""
        assert "Methodology:" in doc

    def test_module_publishes_prediction_trap_declaration(self):
        from app.reading.computations import dispute_surfacing

        doc = dispute_surfacing.__doc__ or ""
        assert "Prediction-trap declaration:" in doc

    def test_module_publishes_famous_chart_anti_contamination(self):
        from app.reading.computations import dispute_surfacing

        doc = dispute_surfacing.__doc__ or ""
        assert "Famous-chart anti-contamination:" in doc


# ---------------------------------------------------------------------------
# Lockfile-driven dispute table
# ---------------------------------------------------------------------------


class TestDisputeTable:
    """The dispute table must cover D-10 / D-11 / D-3 lockfile entries."""

    def test_dispute_table_has_karaka_triangulation_entry(self):
        """D-10 — Sanjay-Rath vs BPHS Vol.I Ch.11."""
        from app.reading.computations.dispute_surfacing import _DISPUTE_TABLE

        keys = " | ".join(_DISPUTE_TABLE.keys()).lower()
        assert "karaka triangulation" in keys

    def test_dispute_table_has_neech_bhanga_entry(self):
        """D-11 — BPHS Ch.39 v.10 primary vs 3 supplementary rules."""
        from app.reading.computations.dispute_surfacing import _DISPUTE_TABLE

        keys = " | ".join(_DISPUTE_TABLE.keys()).lower()
        assert "neech bhanga" in keys

    def test_dispute_table_has_vimsopaka_entry(self):
        """D-3 — Shodashavarga vs Saptavarga."""
        from app.reading.computations.dispute_surfacing import _DISPUTE_TABLE

        keys = " | ".join(_DISPUTE_TABLE.keys()).lower()
        assert "vimsopaka" in keys


# ---------------------------------------------------------------------------
# Dispute attachment
# ---------------------------------------------------------------------------


class TestDisputeAttachment:
    """surface_disputes attaches a Dispute when the finding's rule is disputed."""

    def test_karaka_triangulation_finding_gets_dispute(self, make_finding):
        from app.reading.computations.dispute_surfacing import surface_disputes

        f = make_finding(rule="Karaka Triangulation (marriage)")
        out = surface_disputes([f])
        assert len(out) == 1
        assert out[0].dispute is not None
        dispute = out[0].dispute
        # rule is captured
        assert "karaka triangulation" in dispute.rule.lower()
        # sources_for documents the engine's locked side
        assert any(
            "sanjay-rath" in s.lower() or "sanjay rath" in s.lower()
            for s in dispute.sources_for
        )
        # sources_against documents the BPHS alternative
        assert any("bphs" in s.lower() for s in dispute.sources_against)

    def test_neech_bhanga_finding_gets_dispute(self, make_finding):
        from app.reading.computations.dispute_surfacing import surface_disputes

        f = make_finding(
            rule="Neech Bhanga",
            rule_id_suffix="neech",
            classification="yoga",
        )
        out = surface_disputes([f])
        assert len(out) == 1
        assert out[0].dispute is not None
        assert "neech bhanga" in out[0].dispute.rule.lower()

    def test_undisputed_rule_passed_through_unchanged(self, make_finding):
        """Findings whose rule isn't in the dispute table get no Dispute."""
        from app.reading.computations.dispute_surfacing import surface_disputes

        f = make_finding(
            rule="Gajakesari Yoga",
            rule_id_suffix="gajakesari",
            classification="yoga",
        )
        out = surface_disputes([f])
        assert len(out) == 1
        assert out[0].dispute is None


# ---------------------------------------------------------------------------
# Engine-preferred-side leakage check
# ---------------------------------------------------------------------------


class TestNoEnginePreferredLeakage:
    """The Dispute schema deliberately omits engine-preferred-side fields.

    This test documents the intent — the actual constraint is enforced by
    the schema's ``extra="forbid"`` config + the absence of an
    ``is_correct`` / ``recommended_side`` / ``engine_preferred`` field.
    """

    def test_dispute_has_no_winner_field(self):
        """Adding a winner-side field would require a schema bump + lockfile."""
        from app.reading.schema import Dispute

        fields = set(Dispute.model_fields.keys())
        for forbidden in ("is_correct", "recommended_side", "engine_preferred"):
            assert forbidden not in fields, (
                f"Dispute schema must not carry {forbidden!r} — "
                "violates Tier-3 anti-preference design."
            )


# ---------------------------------------------------------------------------
# Lazy-import regression
# ---------------------------------------------------------------------------


class TestLazyImportDiscipline:
    """No sentence_transformers / torch / knowledge_search at module top."""

    def test_sentence_transformers_not_imported_at_module_top(self):
        import inspect

        from app.reading.computations import dispute_surfacing

        src = inspect.getsource(dispute_surfacing)
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
