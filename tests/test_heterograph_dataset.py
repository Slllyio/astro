"""Tests for app/medini/ml/heterograph_dataset.py.

Pins the PyG HeteroData factory contract:
- Every chart yields a HeteroData with 4 node types and 5 edge types
- Node feature shapes match the documented node-type sizes
- ChartHeteroDataset's labeling logic is binary "did-have-event"
- Persons with no documented events at all are excluded
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import torch

# torch_geometric is an optional heavy GNN dependency (not in requirements.txt);
# skip this module cleanly when it isn't installed rather than erroring at
# collection. heterograph_dataset imports torch_geometric at module load time.
pytest.importorskip("torch_geometric")

from app.medini.ml.heterograph_dataset import (  # noqa: E402
    NUM_BHAVA, NUM_GRAHA, NUM_NAKSHATRA, NUM_RASI,
    ChartHeteroDataset, build_chart_hetero_data,
)


@pytest.fixture
def tiny_chart_edges() -> pd.DataFrame:
    """Edges for one person matching the format of build_chart_heterograph."""
    return pd.DataFrame({
        "person_id": ["P:1"] * 5,
        "edge_type": ["occupies", "drishti", "dispositor_of", "nakshatra_of", "occupies"],
        "src_type": ["Graha"] * 5,
        "src_idx": [0, 0, 0, 0, 1],
        "dst_type": ["Bhava", "Bhava", "Graha", "Nakshatra", "Bhava"],
        "dst_idx": [0, 6, 1, 5, 3],
        "attr_value": [0.0, 7.0, 0.0, 0.0, 0.0],
    })


@pytest.fixture
def tiny_static_edges() -> pd.DataFrame:
    """One static rules edge (Mars rules Aries)."""
    return pd.DataFrame({
        "edge_type": ["rules"],
        "src_type": ["Graha"],
        "src_idx": [2],
        "dst_type": ["Rasi"],
        "dst_idx": [0],
        "attr_value": [1.0],
        "attr_label": ["Mars"],
    })


class TestHeteroDataConstruction:
    """build_chart_hetero_data must produce a valid PyG HeteroData object."""

    def test_returns_four_node_types(self, tiny_chart_edges, tiny_static_edges):
        """4 node types: Graha, Rasi, Bhava, Nakshatra."""
        hd = build_chart_hetero_data("P:1", tiny_chart_edges, tiny_static_edges)
        assert set(hd.node_types) == {"Graha", "Rasi", "Bhava", "Nakshatra"}

    def test_node_feature_shapes(self, tiny_chart_edges, tiny_static_edges):
        """Each node type has identity-one-hot features of correct size."""
        hd = build_chart_hetero_data("P:1", tiny_chart_edges, tiny_static_edges)
        assert hd["Graha"].x.shape == (NUM_GRAHA, NUM_GRAHA)
        assert hd["Rasi"].x.shape == (NUM_RASI, NUM_RASI)
        assert hd["Bhava"].x.shape == (NUM_BHAVA, NUM_BHAVA)
        assert hd["Nakshatra"].x.shape == (NUM_NAKSHATRA, NUM_NAKSHATRA)

    def test_edge_types_include_chart_and_static(self, tiny_chart_edges, tiny_static_edges):
        """5 edge types: 4 chart-dependent + 1 static."""
        hd = build_chart_hetero_data("P:1", tiny_chart_edges, tiny_static_edges)
        assert len(hd.edge_types) == 5

    def test_occupies_edges_are_present(self, tiny_chart_edges, tiny_static_edges):
        """The two occupies rows in the fixture survive the build."""
        hd = build_chart_hetero_data("P:1", tiny_chart_edges, tiny_static_edges)
        ei = hd["Graha", "occupies", "Bhava"].edge_index
        assert ei.shape == (2, 2)

    def test_drishti_attribute_preserved(self, tiny_chart_edges, tiny_static_edges):
        """The drishti aspect-distance (7.0) is preserved as edge_attr."""
        hd = build_chart_hetero_data("P:1", tiny_chart_edges, tiny_static_edges)
        ea = hd["Graha", "drishti", "Bhava"].edge_attr
        assert ea.shape == (1, 1)
        assert torch.isclose(ea[0, 0], torch.tensor(7.0))

    def test_person_id_attached(self, tiny_chart_edges, tiny_static_edges):
        """The HeteroData carries person_id for traceability."""
        hd = build_chart_hetero_data("P:1", tiny_chart_edges, tiny_static_edges)
        assert hd.person_id == "P:1"


@pytest.fixture
def tmp_silver_for_dataset(tmp_path: Path) -> Path:
    """Build the minimal Silver files ChartHeteroDataset reads.

    Three persons: P:1 has a marriage event, P:2 has a career event, P:3 has none.
    Expected after filtering: only P:1 and P:2 (P:3 has no documented events).
    """
    pd.DataFrame({
        "person_id": ["P:1", "P:1", "P:1", "P:2", "P:2"],
        "edge_type": ["occupies"] * 5,
        "src_type": ["Graha"] * 5,
        "src_idx": [0, 1, 2, 0, 1],
        "dst_type": ["Bhava"] * 5,
        "dst_idx": [0, 1, 2, 0, 1],
        "attr_value": [0.0] * 5,
    }).to_parquet(tmp_path / "chart_edges.parquet", index=False)
    pd.DataFrame({
        "edge_type": ["rules"],
        "src_type": ["Graha"],
        "src_idx": [2],
        "dst_type": ["Rasi"],
        "dst_idx": [0],
        "attr_value": [1.0],
        "attr_label": ["Mars"],
    }).to_parquet(tmp_path / "static_graph_edges.parquet", index=False)
    pd.DataFrame({
        "event_id": [0, 1],
        "person_id": ["P:1", "P:2"],
        "event_class": ["marriage", "career"],
        "event_root": ["Marriage", "Work"],
        "event_subtype": [None, None],
        "event_date": ["1950-01-01", "1960-01-01"],
        "event_label": ["m1", "c1"],
        "source": ["x", "x"],
    }).to_parquet(tmp_path / "events.parquet", index=False)
    return tmp_path


class TestChartHeteroDataset:
    """End-to-end labeling + iteration."""

    def test_drops_persons_with_no_events(self, tmp_silver_for_dataset: Path):
        """P:3 had no events anywhere; must be excluded."""
        ds = ChartHeteroDataset(event_class="marriage", data_dir=tmp_silver_for_dataset)
        assert "P:3" not in ds.person_ids

    def test_binary_label_for_target_class(self, tmp_silver_for_dataset: Path):
        """P:1 has marriage event -> label 1; P:2 only has career -> label 0."""
        ds = ChartHeteroDataset(event_class="marriage", data_dir=tmp_silver_for_dataset)
        label_map = dict(zip(ds.person_ids, ds.labels))
        assert label_map["P:1"] == 1
        assert label_map["P:2"] == 0

    def test_iteration_yields_hetero_data(self, tmp_silver_for_dataset: Path):
        """The dataset iterator yields PyG HeteroData objects."""
        ds = ChartHeteroDataset(event_class="marriage", data_dir=tmp_silver_for_dataset)
        items = list(ds)
        assert len(items) == 2
        for hd, label, pid in items:
            assert hd["Graha"].x.shape == (NUM_GRAHA, NUM_GRAHA)
            assert label in {0, 1}
            assert pid.startswith("P:")
