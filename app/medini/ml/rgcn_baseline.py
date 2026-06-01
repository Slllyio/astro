"""Phase 7b - R-GCN baseline for the chart heterograph.

Tests the SINGLE FALSIFIABLE QUESTION that the multi-agent audit raised:

  Does a relational graph representation extract per-chart predictive
  signal that flat-tabular ML (the Round-9 null baselines) destroys?

Architecture: 2-layer Heterogeneous SAGEConv over the chart heterograph
(60 nodes, ~58 edges per chart). Pool over Graha nodes (the subject
planets) -> linear classifier -> binary cross-entropy.

The R-GCN MVP is intentionally SMALL to keep the comparison clean:
  * No transit features (Phase 6 deferred)
  * No dasha-tree mutual-relation features (Phase 5 not yet wired in)
  * Identity-one-hot node features (no learned embeddings)

This is a CONSERVATIVE test of the representation hypothesis: if the
bare heterograph beats flat XGBoost by >0.01 AUC, the representation
hypothesis has support; if it matches or trails, the Round-9 null
verdict is reinforced and Phases 5/6 are not worth the investment.

Person-disjoint split matches Round-9's nonstructural_chart_predictor
protocol exactly so the comparison is apples-to-apples.

Usage:
    python -m app.medini.ml.rgcn_baseline --event-class marriage --epochs 30
    python -m app.medini.ml.rgcn_baseline --event-class marriage --limit-persons 5000
"""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import Final

import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from torch_geometric.data import HeteroData
from torch_geometric.loader import DataLoader
from torch_geometric.nn import HeteroConv, SAGEConv

from app.medini.ml.heterograph_dataset import (
    DEFAULT_DATA_DIR, NUM_BHAVA, NUM_GRAHA, NUM_NAKSHATRA, NUM_RASI,
    ChartHeteroDataset,
)

logger = logging.getLogger(__name__)

_DEFAULT_HIDDEN: Final = 32
_DEFAULT_EPOCHS: Final = 30
_DEFAULT_LR: Final = 1e-3
_DEFAULT_BATCH: Final = 64


class ChartHeteroGNN(nn.Module):
    """2-layer Heterogeneous SAGEConv with per-edge-type aggregation.

    The aggregation pooling step takes the mean over Graha nodes
    (representing the chart's 9 planetary subjects) and feeds it to a
    binary classifier. We deliberately pool Graha-only because the
    "what this chart predicts" question is fundamentally about the
    Grahas - the Bhavas, Rasis, and Nakshatras are spatial scaffolding.
    """

    def __init__(self, hidden_dim: int = _DEFAULT_HIDDEN):
        super().__init__()
        self.in_dims = {
            "Graha": NUM_GRAHA,
            "Rasi": NUM_RASI,
            "Bhava": NUM_BHAVA,
            "Nakshatra": NUM_NAKSHATRA,
        }
        # Project each node type's identity-feature to hidden_dim first
        # so HeteroConv can mix them safely.
        self.input_proj = nn.ModuleDict({
            t: nn.Linear(d, hidden_dim) for t, d in self.in_dims.items()
        })
        self.conv1 = HeteroConv({
            ("Graha", "occupies",      "Bhava"):     SAGEConv(hidden_dim, hidden_dim),
            ("Graha", "drishti",       "Bhava"):     SAGEConv(hidden_dim, hidden_dim),
            ("Graha", "dispositor_of", "Graha"):     SAGEConv(hidden_dim, hidden_dim),
            ("Graha", "nakshatra_of",  "Nakshatra"): SAGEConv(hidden_dim, hidden_dim),
            ("Graha", "rules",         "Rasi"):      SAGEConv(hidden_dim, hidden_dim),
        }, aggr="mean")
        self.conv2 = HeteroConv({
            ("Graha", "occupies",      "Bhava"):     SAGEConv(hidden_dim, hidden_dim),
            ("Graha", "drishti",       "Bhava"):     SAGEConv(hidden_dim, hidden_dim),
            ("Graha", "dispositor_of", "Graha"):     SAGEConv(hidden_dim, hidden_dim),
            ("Graha", "nakshatra_of",  "Nakshatra"): SAGEConv(hidden_dim, hidden_dim),
            ("Graha", "rules",         "Rasi"):      SAGEConv(hidden_dim, hidden_dim),
        }, aggr="mean")
        self.classifier = nn.Linear(hidden_dim, 1)

    def forward(self, data: HeteroData) -> torch.Tensor:
        """Forward pass. Returns logits of shape (batch_size,)."""
        # Input projection per node type.
        x_dict = {t: self.input_proj[t](data[t].x) for t in self.in_dims}

        # Two rounds of message passing.
        x_dict = self.conv1(x_dict, data.edge_index_dict)
        x_dict = {t: F.relu(x) for t, x in x_dict.items()}
        x_dict = self.conv2(x_dict, data.edge_index_dict)

        # Pool over Graha nodes per batch element. data['Graha'].batch
        # is the per-node batch index that DataLoader sets automatically.
        graha_x = x_dict["Graha"]
        batch = data["Graha"].batch
        if batch is None:
            pooled = graha_x.mean(dim=0, keepdim=True)
        else:
            pooled = torch.zeros(
                batch.max().item() + 1, graha_x.size(1), device=graha_x.device,
            )
            pooled.index_add_(0, batch, graha_x)
            counts = torch.bincount(batch).float().unsqueeze(-1).clamp(min=1)
            pooled = pooled / counts

        return self.classifier(pooled).squeeze(-1)


def _materialise_dataset(
    ds: ChartHeteroDataset, limit: int | None = None,
) -> tuple[list[HeteroData], list[int], list[str]]:
    """Iterate the dataset once and collect HeteroData objects + labels."""
    data_list: list[HeteroData] = []
    labels: list[int] = []
    person_ids: list[str] = []
    for i, (hd, label, pid) in enumerate(ds):
        if limit is not None and i >= limit:
            break
        # Attach label to the HeteroData so DataLoader can batch it.
        hd.y = torch.tensor([label], dtype=torch.float32)
        data_list.append(hd)
        labels.append(label)
        person_ids.append(pid)
    return data_list, labels, person_ids


def train_rgcn(
    event_class: str,
    data_dir: Path = DEFAULT_DATA_DIR,
    epochs: int = _DEFAULT_EPOCHS,
    hidden_dim: int = _DEFAULT_HIDDEN,
    lr: float = _DEFAULT_LR,
    batch_size: int = _DEFAULT_BATCH,
    limit_persons: int | None = None,
    test_size: float = 0.2,
    seed: int = 42,
    device: str = "cpu",
) -> dict[str, float]:
    """Train + evaluate the R-GCN. Returns final-epoch metrics dict."""
    torch.manual_seed(seed)

    ds = ChartHeteroDataset(event_class=event_class, data_dir=data_dir)
    logger.info("Materialising %d HeteroData objects...", min(limit_persons or len(ds), len(ds)))
    t0 = time.time()
    data_list, labels, person_ids = _materialise_dataset(ds, limit_persons)
    logger.info("Materialised %d in %.1fs", len(data_list), time.time() - t0)

    # Person-disjoint train/test split.
    indices = list(range(len(data_list)))
    idx_train, idx_test = train_test_split(
        indices, test_size=test_size, stratify=labels, random_state=seed,
    )
    train_data = [data_list[i] for i in idx_train]
    test_data = [data_list[i] for i in idx_test]
    logger.info("Train=%d  Test=%d  Test positive rate=%.3f",
                len(train_data), len(test_data),
                sum(labels[i] for i in idx_test) / len(idx_test))

    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=batch_size, shuffle=False)

    model = ChartHeteroGNN(hidden_dim=hidden_dim).to(device)
    optim = torch.optim.Adam(model.parameters(), lr=lr)
    pos_weight = torch.tensor(
        [(len(labels) - sum(labels)) / max(1, sum(labels))], device=device,
    )
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    best_test_auc = 0.0
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            batch = batch.to(device)
            optim.zero_grad()
            logits = model(batch)
            loss = loss_fn(logits, batch.y)
            loss.backward()
            optim.step()
            train_loss += loss.item() * batch.num_graphs

        # Eval.
        model.eval()
        all_logits: list[torch.Tensor] = []
        all_y: list[torch.Tensor] = []
        with torch.no_grad():
            for batch in test_loader:
                batch = batch.to(device)
                logits = model(batch)
                all_logits.append(logits.cpu())
                all_y.append(batch.y.cpu())
        y_score = torch.cat(all_logits).numpy()
        y_true = torch.cat(all_y).numpy()
        test_auc = roc_auc_score(y_true, y_score)
        if test_auc > best_test_auc:
            best_test_auc = test_auc

        if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
            logger.info(
                "Epoch %02d  train_loss=%.4f  test_AUC=%.4f  (best=%.4f)",
                epoch, train_loss / len(train_data), test_auc, best_test_auc,
            )

    return {
        "final_test_auc": float(test_auc),
        "best_test_auc": float(best_test_auc),
        "n_train": len(train_data),
        "n_test": len(test_data),
        "positive_rate_test": sum(labels[i] for i in idx_test) / len(idx_test),
    }


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-class", type=str, default="marriage")
    parser.add_argument("--epochs", type=int, default=_DEFAULT_EPOCHS)
    parser.add_argument("--hidden-dim", type=int, default=_DEFAULT_HIDDEN)
    parser.add_argument("--lr", type=float, default=_DEFAULT_LR)
    parser.add_argument("--batch-size", type=int, default=_DEFAULT_BATCH)
    parser.add_argument("--limit-persons", type=int, default=None,
                        help="Limit dataset for smoke testing.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    metrics = train_rgcn(
        event_class=args.event_class,
        data_dir=args.data_dir,
        epochs=args.epochs,
        hidden_dim=args.hidden_dim,
        lr=args.lr,
        batch_size=args.batch_size,
        limit_persons=args.limit_persons,
        seed=args.seed,
    )
    print("\n=== Final metrics ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
