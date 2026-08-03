"""S1 judgment graph — completeness, closed vocabulary, endpoint resolution, determinism."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.judgment_graph import (RELATION_VOCABULARY, build_judgment_graph)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def graph(report):
    return build_judgment_graph(report)


class TestJudgmentGraph:
    def test_all_houses_and_grahas_are_noded(self, graph):
        ids = graph.node_ids()
        for h in range(1, 13):
            assert f"house:{h}" in ids
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                  "Rahu", "Ketu"):
            assert f"planet:{p}" in ids

    def test_every_edge_endpoint_resolves(self, graph):
        ids = graph.node_ids()
        for e in graph.edges:
            assert e.src in ids and e.dst in ids, (e.src, e.dst)

    def test_relation_vocabulary_is_closed(self, graph):
        for e in graph.edges:
            assert e.relation in RELATION_VOCABULARY, e.relation

    def test_structural_edges_exist_for_the_canonical_chart(self, graph):
        rels = {e.relation for e in graph.edges}
        for expected in ("lord_of", "occupies", "aspects", "karaka_of", "timer_of",
                         "rules_period", "maraka_tier"):
            assert expected in rels, expected

    def test_every_edge_carries_provenance(self, graph):
        assert all(e.provenance for e in graph.edges)

    def test_the_graph_is_deterministic(self, report, graph):
        again = build_judgment_graph(report)
        assert again.nodes == graph.nodes
        assert again.edges == graph.edges

    def test_guide_relations_land_as_section_edges(self, graph):
        """The v18 records become section->section edges (e.g. timeline governs
        av_dasha_seat per PREC-4)."""
        assert any(e.src == "section:timeline" and e.dst == "section:av_dasha_seat"
                   and e.relation == "governs" for e in graph.edges)

    def test_json_ships_the_graph(self, report):
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)["judgment_graph"]
        assert d["nodes"] and d["edges"]
        assert {"id", "kind", "label"} <= set(d["nodes"][0])

    def test_non_raman_groupings_are_always_bannered(self, graph):
        """S4: every modern cross-house edge and matter node carries the banner —
        never bare doctrine (user decision 2026-08-03)."""
        from app.raman_saab.judgment_graph import MODERN_PROVENANCE, NON_RAMAN_GROUPINGS
        matter_ids = {f"matter:{name}" for name in NON_RAMAN_GROUPINGS}
        assert matter_ids <= graph.node_ids()
        for e in graph.edges:
            if e.dst in matter_ids:
                assert e.provenance == MODERN_PROVENANCE
        for n in graph.nodes:
            if n.id in matter_ids:
                assert ("provenance", MODERN_PROVENANCE) in n.data

    def test_verdict_path_never_imports_the_synthesis_layer(self):
        """The VERDICT-AUTHORITY wall extends to S1-S3: the judges/proforma/synthesis
        never import the graph, biographies, or narrator."""
        import inspect

        from app.raman_saab import proforma, synthesis
        from app.raman_saab.judges import house_judge, house_template
        for mod in (house_template, house_judge, proforma, synthesis):
            src = inspect.getsource(mod)
            for banned in ("judgment_graph", "planet_biographies", "tension_narrator"):
                assert banned not in src, (mod.__name__, banned)
