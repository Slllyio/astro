"""Tests for app.medini.etl.rebuild DAG runner."""
from __future__ import annotations

import pytest

from app.medini.etl.rebuild import (
    _BY_NAME, _DAG, _transitive_deps,
)


class TestDAGStructure:
    """DAG topology contract."""

    def test_all_targets_unique_names(self):
        names = [t.name for t in _DAG]
        assert len(names) == len(set(names)), "duplicate target names"

    def test_all_outputs_unique(self):
        outputs = [t.output for t in _DAG]
        assert len(outputs) == len(set(outputs)), "two targets produce same output"

    def test_every_input_produced_or_external(self):
        """Each declared input is either produced by another target OR
        sourced from outside the DAG (bronze / silver-foundation).
        """
        produced = {t.output for t in _DAG}
        external = {
            "events.parquet",  # part of persons_events module's combined output
        }
        for t in _DAG:
            for inp in t.inputs:
                assert inp in produced or inp in external, (
                    f"Target '{t.name}' has unsourced input '{inp}' "
                    f"-- neither produced by another target nor declared external"
                )

    def test_topological_order_respected_in_definition(self):
        """The order of _DAG list IS the canonical topological order.

        For any target T with input file F, the producer of F must appear
        earlier in _DAG than T.
        """
        positions = {t.output: i for i, t in enumerate(_DAG)}
        for i, t in enumerate(_DAG):
            for inp in t.inputs:
                if inp in positions:
                    assert positions[inp] < i, (
                        f"Out-of-order: {t.name} (pos {i}) depends on "
                        f"{inp} (produced at pos {positions[inp]}) -- "
                        f"reorder _DAG"
                    )


class TestTransitiveDeps:
    """--target X expansion semantics."""

    def test_target_with_no_deps_returns_just_itself(self):
        result = _transitive_deps("persons_events")
        assert result == ["persons_events"]

    def test_target_with_chain_of_deps(self):
        """master_readings -> person_dossier -> persons + charts + jaimini_karakas."""
        result = _transitive_deps("master_readings")
        assert "master_readings" in result
        assert "person_dossier" in result
        assert "charts" in result
        assert "persons_events" in result
        assert result.index("master_readings") == len(result) - 1
        assert result.index("persons_events") < result.index("charts")
        assert result.index("charts") < result.index("person_dossier")

    def test_unknown_target_errors(self):
        with pytest.raises(SystemExit):
            _transitive_deps("not_a_target")

    def test_no_duplicates_in_chain(self):
        """Diamond deps (X needs A+B, both need C) -> C appears once."""
        result = _transitive_deps("event_dossier")
        assert len(result) == len(set(result)), "diamond dep duplicated"
