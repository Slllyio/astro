"""Round 6 Phase 5: Graph Neural Network on chart graphs.

Each natal chart is naturally a heterogeneous graph: 9 planets + 12
houses + 1 ascendant node, with edges encoding drishti, conjunction,
occupancy, and rulership. A Graph Neural Network respects this
structure and can discover yoga-like motifs WITHOUT enumerating
classical named yogas.

This phase distills the Phase-3 chart embeddings into a GNN, then
evaluates whether the GNN matches or exceeds the MLP on the K-NN
Jaccard manifold-preservation metric. If the GNN matches Phase 3,
it confirms the structural representation is information-equivalent.
If it exceeds, the graph structure adds value beyond raw features.

Graph construction
==================
Nodes (22 per chart):
  - 9 planet nodes: features = (longitude_sin, longitude_cos, sign,
    nakshatra_index, retrograde, ecliptic_lat, declination, velocity)
  - 12 house nodes: features = (sign, occupancy_count)
  - 1 ascendant node: features = (longitude_sin, longitude_cos, sign,
    nakshatra_index, 0, 0, 0, 0)

Edges (heterogeneous):
  - drishti: planet → planet  (Vedic aspect, per app.core.avastha rules)
  - conjunction: planet ↔ planet (orb < 8°)
  - occupancy: planet → house (planet's whole-sign house)
  - rulership: planet → house (whose sign rules that house)

We use a homogeneous GraphSAGE / GCN for simplicity (heterogeneous
GNNs are more powerful but PyG's HeteroData adds complexity). All
nodes share the same feature dim via projection layers, and edge
types are encoded as edge attributes.

CLI
===
    python -m app.medini.ml.gnn_chart_encoder \\
        --natal app/medini/data/ml_astro_round5.parquet \\
        --embeddings data/ml_runs/embeddings_round6_phase3/chart_embeddings.npy \\
        --names data/ml_runs/embeddings_round6_phase3/chart_names.parquet \\
        --output data/ml_runs/gnn_round6_phase5/
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Batch, Data
from torch_geometric.nn import GATv2Conv, global_mean_pool

from app.core.avastha import _DRISHTI_HOUSES
from app.medini.etl.feature_engineering import SIGN_RULERS

logger = logging.getLogger(__name__)


# ---------- Chart → Graph ----------

GRAHAS: tuple[str, ...] = (
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
)

# Edge type ids (single-int categorical packed into edge_attr column 0)
EDGE_TYPE_DRISHTI = 0
EDGE_TYPE_CONJUNCTION = 1
EDGE_TYPE_OCCUPANCY = 2
EDGE_TYPE_RULERSHIP = 3

NODE_FEATURE_DIM = 8
EDGE_FEATURE_DIM = 2  # (edge_type_id, edge_orb_or_zero)


def _node_features_for_planet(row: pd.Series, planet: str) -> np.ndarray:
    """Build the 8-D feature vector for one planet node."""
    lon = float(row[f"lon_{planet}"])
    return np.array([
        np.sin(np.deg2rad(lon)),
        np.cos(np.deg2rad(lon)),
        float(row[f"nak_{planet}"]),       # nakshatra index 0..26
        float(row[f"house_{planet}"]),     # 1..12
        float(row[f"rx_{planet}"]),
        float(row[f"lat_{planet}"]),
        float(row[f"dec_{planet}"]),
        float(row[f"vel_{planet}"]),
    ], dtype=np.float32)


def _node_features_for_house(
    sign: int, occupancy: int,
) -> np.ndarray:
    """House node: signed by ascending house, occupancy as a count."""
    return np.array([
        0.0, 0.0,                 # no longitude
        0.0,                       # no nakshatra
        float(sign),              # the house's sign
        0.0,
        0.0,
        0.0,
        float(occupancy),
    ], dtype=np.float32)


def _node_features_for_ascendant(row: pd.Series) -> np.ndarray:
    asc_lon = float(row["lagna_lon"])
    asc_sign = float(row["lagna_sign"])
    nak_idx = int(asc_lon // (360.0 / 27))
    return np.array([
        np.sin(np.deg2rad(asc_lon)),
        np.cos(np.deg2rad(asc_lon)),
        float(nak_idx),
        asc_sign,
        0.0, 0.0, 0.0, 0.0,
    ], dtype=np.float32)


def chart_to_graph(row: pd.Series) -> Data:
    """Build a PyG Data object from one natal-feature row."""
    # 9 planets + 12 houses + 1 ascendant = 22 nodes
    nodes: list[np.ndarray] = []
    # Planet nodes (0..8)
    for planet in GRAHAS:
        nodes.append(_node_features_for_planet(row, planet))
    # House nodes (9..20) — sign of each house = (lagna_sign + i - 1) % 12 + 1
    asc_sign = int(row["lagna_sign"])
    planet_signs = {
        planet: int(row[f"lon_{planet}"]) // 30 + 1 for planet in GRAHAS
    }
    occupancy_per_house: dict[int, int] = {}
    for planet in GRAHAS:
        h = int(row[f"house_{planet}"])
        occupancy_per_house[h] = occupancy_per_house.get(h, 0) + 1
    for house_idx in range(1, 13):
        sign = (asc_sign + house_idx - 2) % 12 + 1
        nodes.append(_node_features_for_house(
            sign=sign, occupancy=occupancy_per_house.get(house_idx, 0),
        ))
    # Ascendant node (21)
    nodes.append(_node_features_for_ascendant(row))

    x = torch.from_numpy(np.stack(nodes)).float()

    # Edges
    src_list, dst_list, attr_list = [], [], []

    # 1) Drishti edges: planet→planet per classical rules
    planet_to_sign = {
        planet: planet_signs[planet] for planet in GRAHAS
    }
    drishti_table = {p.title(): houses for p, houses in _DRISHTI_HOUSES.items()}
    for i, p_from in enumerate(GRAHAS):
        sign_from = planet_to_sign[p_from]
        houses = drishti_table.get(p_from.title(), frozenset())
        for j, p_to in enumerate(GRAHAS):
            if i == j:
                continue
            sign_to = planet_to_sign[p_to]
            distance = ((sign_to - sign_from) % 12) + 1
            if distance in houses:
                src_list.append(i)
                dst_list.append(j)
                attr_list.append([EDGE_TYPE_DRISHTI, 0.0])

    # 2) Conjunction edges: planet ↔ planet within 8° (both directions)
    lons = {p: float(row[f"lon_{p}"]) for p in GRAHAS}
    for i, p1 in enumerate(GRAHAS):
        for j, p2 in enumerate(GRAHAS):
            if i >= j:
                continue
            d = abs(lons[p1] - lons[p2]) % 360.0
            orb = min(d, 360 - d)
            if orb < 8.0:
                src_list.extend([i, j])
                dst_list.extend([j, i])
                attr_list.extend([
                    [EDGE_TYPE_CONJUNCTION, orb],
                    [EDGE_TYPE_CONJUNCTION, orb],
                ])

    # 3) Occupancy edges: planet (i) → house node (9 + house_idx - 1)
    for i, planet in enumerate(GRAHAS):
        h = int(row[f"house_{planet}"])
        if 1 <= h <= 12:
            src_list.append(i)
            dst_list.append(9 + h - 1)
            attr_list.append([EDGE_TYPE_OCCUPANCY, 0.0])

    # 4) Rulership: each house's sign → the planet ruling it
    sign_to_planet_idx = {
        s: GRAHAS.index(ruler.lower()) if ruler.lower() in GRAHAS else 0
        for s, ruler in SIGN_RULERS.items()
    }
    for house_idx in range(1, 13):
        sign = (asc_sign + house_idx - 2) % 12 + 1
        ruler_idx = sign_to_planet_idx.get(sign)
        if ruler_idx is not None:
            src_list.append(ruler_idx)
            dst_list.append(9 + house_idx - 1)
            attr_list.append([EDGE_TYPE_RULERSHIP, 0.0])

    if not src_list:
        # Defensive: every chart should produce some edges
        src_list = [0]
        dst_list = [0]
        attr_list = [[0, 0.0]]

    edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)
    edge_attr = torch.tensor(attr_list, dtype=torch.float32)
    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)


# ---------- GNN model ----------

class ChartGNN(nn.Module):
    """3-layer GATv2 + global mean pool → 128-D chart embedding."""

    def __init__(
        self,
        in_dim: int = NODE_FEATURE_DIM,
        edge_dim: int = EDGE_FEATURE_DIM,
        hidden_dim: int = 64,
        embed_dim: int = 128,
        n_heads: int = 4,
        n_layers: int = 3,
    ):
        super().__init__()
        self.input_proj = nn.Linear(in_dim, hidden_dim)
        self.convs = nn.ModuleList()
        for _ in range(n_layers):
            self.convs.append(
                GATv2Conv(
                    hidden_dim, hidden_dim // n_heads,
                    heads=n_heads, edge_dim=edge_dim,
                    add_self_loops=True,
                )
            )
        self.norm = nn.LayerNorm(hidden_dim)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, embed_dim),
            nn.ReLU(),
            nn.Linear(embed_dim, embed_dim),
        )
        self.embed_dim = embed_dim

    def forward(self, data: Data | Batch) -> torch.Tensor:
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        h = self.input_proj(x)
        for conv in self.convs:
            h_new = conv(h, edge_index, edge_attr=edge_attr)
            h = h + F.relu(h_new)  # residual
            h = self.norm(h)
        batch = getattr(data, "batch", None)
        if batch is None:
            batch = torch.zeros(h.size(0), dtype=torch.long, device=h.device)
        graph_emb = global_mean_pool(h, batch)
        out = self.head(graph_emb)
        return F.normalize(out, dim=-1)


# ---------- Distillation training ----------

def distill_train(
    model: ChartGNN,
    graphs: list[Data],
    target_embeddings: torch.Tensor,           # (N, 128)
    *,
    epochs: int = 15,
    batch_size: int = 128,
    lr: float = 1e-3,
    seed: int = 42,
) -> list[float]:
    """Train the GNN to match the Phase-3 MLP embeddings (knowledge distill).

    Loss = 1 - cosine_similarity(predicted, target). Standard distillation
    objective when target is L2-normalised.
    """
    rng = random.Random(seed)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    losses: list[float] = []
    indices = list(range(len(graphs)))
    for epoch in range(1, epochs + 1):
        rng.shuffle(indices)
        epoch_loss = 0.0
        n_batches = 0
        for start in range(0, len(indices), batch_size):
            batch_idx = indices[start:start + batch_size]
            batch_graphs = [graphs[i] for i in batch_idx]
            batch_targets = target_embeddings[batch_idx]
            batch = Batch.from_data_list(batch_graphs)
            pred = model(batch)
            cos = F.cosine_similarity(pred, batch_targets, dim=-1)
            loss = (1.0 - cos).mean()
            optim.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optim.step()
            epoch_loss += float(loss.item())
            n_batches += 1
        avg = epoch_loss / max(n_batches, 1)
        losses.append(avg)
        logger.info("epoch %2d/%d  loss=%.4f", epoch, epochs, avg)
    return losses


# ---------- Inference ----------

@torch.no_grad()
def encode_all(
    model: ChartGNN, graphs: list[Data], batch_size: int = 256,
) -> np.ndarray:
    model.eval()
    out_chunks: list[np.ndarray] = []
    for start in range(0, len(graphs), batch_size):
        batch = Batch.from_data_list(graphs[start:start + batch_size])
        z = model(batch).cpu().numpy()
        out_chunks.append(z)
    return np.concatenate(out_chunks, axis=0)


# ---------- Main ----------

def run_phase5(
    *,
    natal_parquet: Path,
    embeddings_path: Path,
    names_parquet: Path,
    output_dir: Path,
    epochs: int = 15,
    batch_size: int = 128,
    max_charts: int | None = None,
    seed: int = 42,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    logger.info("loading Phase-3 MLP embeddings + names ...")
    target_arr = np.load(embeddings_path)
    names_df = pd.read_parquet(names_parquet)
    names = names_df["name_lower"].tolist()
    logger.info("Phase-3 targets: %d × %d", *target_arr.shape)

    logger.info("loading natal parquet ...")
    natal_df = pd.read_parquet(natal_parquet)
    natal_df["_n"] = natal_df["name"].astype(str).str.strip().str.lower()
    natal_df = natal_df.drop_duplicates(subset="_n").set_index("_n")

    # Align natal rows with embedding ordering (names list)
    aligned_names = [n for n in names if n in natal_df.index]
    aligned_idx = [names.index(n) for n in aligned_names]
    if max_charts:
        aligned_names = aligned_names[:max_charts]
        aligned_idx = aligned_idx[:max_charts]
    logger.info("aligned charts: %d", len(aligned_names))

    target_emb = torch.from_numpy(target_arr[aligned_idx]).float()

    logger.info("building graphs from natal rows ...")
    graphs: list[Data] = []
    for name in aligned_names:
        try:
            graphs.append(chart_to_graph(natal_df.loc[name]))
        except Exception as exc:
            logger.warning("chart_to_graph failed for %s: %s", name, exc)
    logger.info("built %d chart graphs", len(graphs))

    # Quick sanity: graph stats
    sample_g = graphs[0]
    logger.info(
        "sample graph: %d nodes, %d edges, %d edge-attrs",
        sample_g.x.size(0), sample_g.edge_index.size(1),
        sample_g.edge_attr.size(0),
    )

    model = ChartGNN(
        in_dim=NODE_FEATURE_DIM, edge_dim=EDGE_FEATURE_DIM,
        hidden_dim=64, embed_dim=target_emb.size(1), n_heads=4, n_layers=3,
    )
    n_params = sum(p.numel() for p in model.parameters())
    logger.info("ChartGNN parameters: %d (%.2f M)", n_params, n_params / 1e6)

    losses = distill_train(
        model, graphs, target_emb,
        epochs=epochs, batch_size=batch_size, seed=seed,
    )

    logger.info("encoding all charts via GNN ...")
    gnn_embeddings = encode_all(model, graphs)
    np.save(output_dir / "gnn_chart_embeddings.npy", gnn_embeddings)
    pd.DataFrame({"name_lower": aligned_names}).to_parquet(
        output_dir / "chart_names.parquet", index=False,
    )
    torch.save(model.state_dict(), output_dir / "gnn_encoder.pt")

    # Compare MLP vs GNN embeddings on outcome-Jaccard preservation
    # (cheap re-use of the Phase-3 fingerprint logic — load events)
    from app.medini.ml.contrastive_embeddings import (  # noqa: E402
        build_outcome_fingerprints,
        nearest_neighbor_event_jaccard,
        random_baseline_jaccard,
    )
    fingerprints = build_outcome_fingerprints(
        Path("data/astro_databank/events_all.csv"), set(aligned_names),
    )
    gnn_jaccard = nearest_neighbor_event_jaccard(
        gnn_embeddings, aligned_names, fingerprints, k=5,
    )
    mlp_jaccard = nearest_neighbor_event_jaccard(
        target_arr[aligned_idx], aligned_names, fingerprints, k=5,
    )
    baseline = random_baseline_jaccard(fingerprints)
    logger.info(
        "K=5 NN Jaccard:  GNN=%.4f  MLP=%.4f  random=%.4f",
        gnn_jaccard, mlp_jaccard, baseline,
    )

    # Report
    report = output_dir / "report.md"
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Phase 5 — GNN on chart graphs",
        "",
        f"_Generated {now}_",
        "",
        "## Graph construction",
        "",
        f"- Nodes per chart: 22 (9 planets + 12 houses + 1 ascendant)",
        f"- Node features: {NODE_FEATURE_DIM}-D",
        f"- Edge types: drishti, conjunction, occupancy, rulership",
        f"- Edge features: {EDGE_FEATURE_DIM}-D (type id + orb)",
        "",
        "## Training",
        "",
        f"- Distillation target: Phase-3 MLP embeddings ({target_emb.size(1)}-D)",
        f"- Loss: 1 - cosine_similarity(GNN(graph), MLP(features))",
        f"- Charts trained: {len(graphs):,}",
        f"- Epochs: {epochs}",
        f"- Model: 3-layer GATv2, 4 heads, hidden 64, ~{n_params/1e6:.2f}M params",
        "",
        "### Loss curve",
        "",
        "| Epoch | Loss |",
        "|---|---|",
    ]
    for i, l in enumerate(losses, start=1):
        lines.append(f"| {i} | {l:.4f} |")
    lines.extend([
        "",
        "## Manifold evaluation (K=5 NN outcome-Jaccard)",
        "",
        "| Encoder | K=5 NN Jaccard |",
        "|---|---|",
        f"| **GNN** (structural) | {gnn_jaccard:.4f} |",
        f"| **MLP** (tabular features, Phase 3) | {mlp_jaccard:.4f} |",
        f"| Random baseline | {baseline:.4f} |",
        "",
        "## Interpretation",
        "",
    ])
    delta = gnn_jaccard - mlp_jaccard
    if abs(delta) < 0.02:
        lines.append(
            "GNN matches the MLP within noise. The structural representation",
            )
        lines.append(
            "is information-equivalent to the tabular features for outcome",
        )
        lines.append("preservation.")
    elif delta > 0:
        lines.append(
            f"GNN beats the MLP by {delta:+.4f}. Graph structure adds value "
            f"beyond raw features — chart-as-graph is a richer representation."
        )
    else:
        lines.append(
            f"GNN underperforms the MLP by {delta:.4f}. The tabular features "
            f"already encode most of what the graph structure offers. "
            f"GNN provides a different (not necessarily better) lens."
        )
    lines.append("")
    lines.append(
        "Note: GNN was trained by DISTILLATION on the MLP targets. An "
        "independent contrastive-objective training of the GNN may "
        "produce a different result (potentially higher than distillation)."
    )

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report to %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.gnn_chart_encoder",
    )
    parser.add_argument(
        "--natal", type=Path,
        default=Path("app/medini/data/ml_astro_round5.parquet"),
    )
    parser.add_argument(
        "--embeddings", type=Path,
        default=Path("data/ml_runs/embeddings_round6_phase3/chart_embeddings.npy"),
    )
    parser.add_argument(
        "--names", type=Path,
        default=Path("data/ml_runs/embeddings_round6_phase3/chart_names.parquet"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/gnn_round6_phase5/"),
    )
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--max-charts", type=int, default=None,
                        help="Cap for fast smoke tests")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_phase5(
        natal_parquet=args.natal,
        embeddings_path=args.embeddings,
        names_parquet=args.names,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        max_charts=args.max_charts,
    )
    print(f"Phase 5 artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
