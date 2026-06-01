"""Phase 7a - PyG HeteroData factory for chart heterograph + survival labels.

Builds the input tensors for the R-GCN baseline (Phase 7b) by joining:
  - chart_edges.parquet       (per-chart relational structure)
  - static_graph_edges.parquet (sign rulership + karaka assignments)
  - events_with_dasha.parquet  (the binary label + active dasha context)

The R-GCN MVP test is intentionally framed as a falsifiable comparison
against the prior null XGBoost baseline:

  Task: for each (person, event_class) pair, predict whether that person
        has a documented event of that class anywhere in life.
  Features: the typed heterograph (60 nodes, ~50 edges per chart).
  Cross-validation: person-disjoint folds (same protocol as Round 9
                    nonstructural_chart_predictor.py).
  Baseline: XGBoost on the 9-graha (lon, sign, house, nakshatra) flat
            features --- the EXISTING null baseline.

If R-GCN AUC > XGBoost AUC by >= 0.01 across folds, the relational
representation contributes signal that flat tabular destroys --- this
would falsify the strongest interpretation of the Round-9 null verdict
(that "chart structure carries no recoverable signal"). If R-GCN matches
or trails XGBoost, the representation hypothesis is unsupported and the
null verdict stands.

Node-type encoding (must match build_chart_heterograph.py):
  Graha     0..8
  Rasi      0..11
  Bhava     0..11
  Nakshatra 0..26

Output: an iterable yielding one (HeteroData, label, person_id) per
person, where HeteroData has node feature tensors and edge_index per
edge type. Labels are per-event-class binary masks materialised by the
caller, not stored on the HeteroData.

Usage:
    from app.medini.ml.heterograph_dataset import build_chart_hetero_data, ChartHeteroDataset

    ds = ChartHeteroDataset(event_class="marriage")
    for hd, label, person_id in ds:
        ...
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Final

import pandas as pd
import torch
from torch_geometric.data import HeteroData

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")

# Node-type sizes (matching build_chart_heterograph.py).
NUM_GRAHA: Final = 9
NUM_RASI: Final = 12
NUM_BHAVA: Final = 12
NUM_NAKSHATRA: Final = 27

# Edge types in the heterograph. Each value is (src_type, relation, dst_type)
# as PyG expects.
_CHART_EDGE_TYPES: Final[tuple[tuple[str, str, str], ...]] = (
    ("Graha", "occupies", "Bhava"),
    ("Graha", "drishti", "Bhava"),
    ("Graha", "dispositor_of", "Graha"),
    ("Graha", "nakshatra_of", "Nakshatra"),
)
_STATIC_EDGE_TYPES: Final[tuple[tuple[str, str, str], ...]] = (
    ("Graha", "rules", "Rasi"),
)


def _node_features() -> dict[str, torch.Tensor]:
    """Initial node features --- one-hot identity for each node type.

    This gives the GNN a per-type embedding to learn against without
    hand-crafted features. Future work: replace with learned embeddings
    trained jointly with the classifier.
    """
    return {
        "Graha":     torch.eye(NUM_GRAHA, dtype=torch.float32),
        "Rasi":      torch.eye(NUM_RASI, dtype=torch.float32),
        "Bhava":     torch.eye(NUM_BHAVA, dtype=torch.float32),
        "Nakshatra": torch.eye(NUM_NAKSHATRA, dtype=torch.float32),
    }


def build_chart_hetero_data(
    person_id: str,
    chart_edges_for_person: pd.DataFrame,
    static_edges: pd.DataFrame,
) -> HeteroData:
    """Build a PyG HeteroData object for one person's chart.

    chart_edges_for_person must already be filtered to ``person_id`` (the
    function does NOT filter for you to avoid repeated bool masks across
    thousands of persons).
    """
    data = HeteroData()

    # Identity-features per node type (shared across all charts; PyG
    # documents this is the canonical pattern for tied-embedding GNNs).
    for ntype, feat in _node_features().items():
        data[ntype].x = feat

    # Chart-dependent edges.
    for src_type, rel, dst_type in _CHART_EDGE_TYPES:
        mask = chart_edges_for_person["edge_type"] == rel
        sub = chart_edges_for_person[mask]
        if len(sub) == 0:
            edge_index = torch.zeros((2, 0), dtype=torch.long)
            edge_attr = torch.zeros((0, 1), dtype=torch.float32)
        else:
            src = torch.tensor(sub["src_idx"].to_numpy(), dtype=torch.long)
            dst = torch.tensor(sub["dst_idx"].to_numpy(), dtype=torch.long)
            edge_index = torch.stack([src, dst], dim=0)
            edge_attr = torch.tensor(
                sub["attr_value"].to_numpy(), dtype=torch.float32,
            ).unsqueeze(-1)
        data[src_type, rel, dst_type].edge_index = edge_index
        data[src_type, rel, dst_type].edge_attr = edge_attr

    # Static edges (rulership) - same for every chart but PyG needs them
    # present on each HeteroData instance.
    for src_type, rel, dst_type in _STATIC_EDGE_TYPES:
        mask = static_edges["edge_type"] == rel
        sub = static_edges[mask]
        src = torch.tensor(sub["src_idx"].to_numpy(), dtype=torch.long)
        dst = torch.tensor(sub["dst_idx"].to_numpy(), dtype=torch.long)
        data[src_type, rel, dst_type].edge_index = torch.stack([src, dst], dim=0)

    data.person_id = person_id
    return data


class ChartHeteroDataset:
    """Iterable dataset of (HeteroData, label, person_id) for one event class.

    Loads chart_edges + static_edges once into memory and groups them
    by person_id for fast per-chart construction. For 43k persons this
    is ~2 GB of pandas; we accept that cost for the simplicity of not
    needing a streaming materialisation layer at MVP scale.

    The label is binary: 1 if the person has at least one documented
    event of ``event_class``, else 0. Persons with NO events at all
    (in any class) are dropped --- they would otherwise dominate the
    negative class as documentation-missing rather than event-absent.
    """

    def __init__(
        self,
        event_class: str,
        data_dir: Path = DEFAULT_DATA_DIR,
    ):
        self.event_class = event_class
        self.data_dir = data_dir
        self._load()

    def _load(self) -> None:
        logger.info("Loading heterograph dataset for event_class=%r", self.event_class)
        self.chart_edges = pd.read_parquet(self.data_dir / "chart_edges.parquet")
        self.static_edges = pd.read_parquet(self.data_dir / "static_graph_edges.parquet")
        events = pd.read_parquet(self.data_dir / "events.parquet")

        # Drop persons with NO documented events --- they are documentation
        # holes, not negatives. Same convention as Round 9 protocol.
        persons_with_any_event = set(events["person_id"].unique())
        persons_with_target_event = set(
            events.loc[events["event_class"] == self.event_class, "person_id"]
        )

        person_ids = sorted(persons_with_any_event)
        labels = [
            1 if p in persons_with_target_event else 0
            for p in person_ids
        ]
        self.person_ids: list[str] = person_ids
        self.labels: list[int] = labels

        # Group chart_edges by person_id for fast retrieval.
        self._edges_by_person = {
            p: df for p, df in self.chart_edges.groupby("person_id", sort=False)
        }
        logger.info(
            "Loaded %d persons (%d positive, %d negative) for class=%s",
            len(person_ids), sum(labels), len(person_ids) - sum(labels),
            self.event_class,
        )

    def __len__(self) -> int:
        return len(self.person_ids)

    def __iter__(self) -> Iterator[tuple[HeteroData, int, str]]:
        for person_id, label in zip(self.person_ids, self.labels):
            edges = self._edges_by_person.get(person_id)
            if edges is None:
                continue
            hetero = build_chart_hetero_data(person_id, edges, self.static_edges)
            yield hetero, label, person_id

    def get_one(self, person_id: str) -> HeteroData:
        """Retrieve one person's HeteroData on demand."""
        edges = self._edges_by_person[person_id]
        return build_chart_hetero_data(person_id, edges, self.static_edges)
