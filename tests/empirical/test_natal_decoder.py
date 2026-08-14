"""Decoder invariants: determinism, completeness, honest degradation, audit trail.

The epistemic point: the decoder is the layer where a computed chart becomes
prose, which is exactly where an astrology product usually starts cheating —
inventing statements without sources, padding empty sections, or quietly
guessing houses it does not have. Each test here closes one of those doors.
"""

from __future__ import annotations

from app.empirical.natal.chart import BirthMoment, assemble_chart
from app.empirical.natal.decoder import decode
from app.empirical.natal.lexicon import FACETS, TRADITION_BANNER, WESTERN_TRADITION

CANONICAL = BirthMoment(1990, 7, 15, 12, 0, 12.97, 77.59, 5.5)
SVALBARD = BirthMoment(1990, 7, 15, 12, 0, 78.0, 15.6, 1.0)
TIMELESS = BirthMoment(1990, 7, 15, 0, 0, 12.97, 77.59, 5.5, time_known=False)


class TestInvariants:
    """Determinism and the seven-facet completeness guarantee."""

    def test_decode_is_deterministic(self):
        """Two decodes of the same chart are equal, field for field."""
        chart = assemble_chart(CANONICAL)
        assert decode(chart) == decode(chart)

    def test_all_seven_facets_present_in_order_and_nonempty(self):
        """The facet tuple is exactly FACETS, ordered, each with statements."""
        reading = decode(assemble_chart(CANONICAL))
        assert tuple(s.facet for s in reading.facets) == FACETS
        assert all(s.statements for s in reading.facets)

    def test_every_statement_carries_source_provenance_and_basis(self):
        """No statement escapes the audit trail or the provenance tag."""
        reading = decode(assemble_chart(CANONICAL))
        for section in reading.facets:
            for stmt in section.statements:
                assert stmt.text and stmt.source and stmt.basis
                assert stmt.provenance == WESTERN_TRADITION

    def test_disclosures_lead_with_the_tradition_banner(self):
        """The banner is the first disclosure on every decode."""
        reading = decode(assemble_chart(CANONICAL))
        assert reading.disclosures[0] == TRADITION_BANNER

    def test_nodes_never_produce_statements(self):
        """TrueNode is computed but excluded from trait decoding by design."""
        reading = decode(assemble_chart(CANONICAL))
        for section in reading.facets:
            for stmt in section.statements:
                assert "TrueNode" not in stmt.source
                assert all("TrueNode" not in b for b in stmt.basis)


class TestDegradation:
    """Missing houses degrade honestly: omitted, marked, explained — never guessed."""

    def test_houseless_chart_has_no_house_basis_keys(self):
        """No statement may rest on a house the chart does not have."""
        reading = decode(assemble_chart(SVALBARD, house_system="placidus"))
        for section in reading.facets:
            for stmt in section.statements:
                assert not any(b.startswith("planet_house:") for b in stmt.basis)
                assert not any(b.startswith("ascendant:") for b in stmt.basis)

    def test_houseless_facets_are_degraded_with_a_reason_note(self):
        """Every facet is marked degraded and carries the polar explanation."""
        reading = decode(assemble_chart(SVALBARD, house_system="placidus"))
        for section in reading.facets:
            assert section.degraded
            assert any("polar" in n for n in section.notes)

    def test_houseless_facets_are_still_nonempty(self):
        """Sign-level vocabulary is total, so degradation never empties a facet."""
        reading = decode(assemble_chart(SVALBARD, house_system="placidus"))
        assert all(s.statements for s in reading.facets)

    def test_unknown_time_work_area_names_the_missing_houses(self):
        """work_area must say explicitly that the vocational houses are gone."""
        reading = decode(assemble_chart(TIMELESS))
        work = next(s for s in reading.facets if s.facet == "work_area")
        assert work.degraded
        assert any("2nd, 6th, 10th" in n for n in work.notes)

    def test_known_time_chart_is_not_degraded(self):
        """A full chart carries no degradation flags."""
        reading = decode(assemble_chart(CANONICAL))
        assert not any(s.degraded for s in reading.facets)


class TestWording:
    """Pinned wording rules."""

    def test_intelligence_never_claims_iq(self):
        """The intelligence facet describes cognitive style, never a quotient."""
        for moment in (CANONICAL, TIMELESS):
            reading = decode(assemble_chart(moment))
            section = next(s for s in reading.facets if s.facet == "intelligence")
            for stmt in section.statements:
                assert "IQ" not in stmt.text

    def test_sourced_placements_name_the_house_system(self):
        """House-based sources disclose which system produced the house."""
        reading = decode(assemble_chart(CANONICAL))
        house_sourced = [
            stmt
            for section in reading.facets
            for stmt in section.statements
            if any(b.startswith("planet_house:") for b in stmt.basis)
        ]
        assert house_sourced
        assert all("placidus" in stmt.source for stmt in house_sourced)
