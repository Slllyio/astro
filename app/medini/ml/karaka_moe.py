"""Round 6 Phase 8: Karaka-aware Mixture-of-Experts.

9 expert sub-networks (one per graha = karaka): each receives the
natal-feature subset specific to its planet. A gating network learns
to route different event types through the relevant karakas' experts.

Why this architecture: classical Vedic theory says each event domain
is "ruled by" specific karakas (Venus for marriage, Saturn for career,
Sun for father, Moon for mother, Jupiter for children, etc.). A MoE
with explicit karaka experts gives the model a structural prior that
matches the theory.

After training we inspect gating weights — does the Venus expert
dominate marriage prediction? Does Saturn dominate career? If yes,
the classical karaka theory is data-confirmed. If gating weights
diverge from classical mapping, that's a learnable refinement.

Implementation
==============
- Per-graha feature selection: planet expert sees only features
  whose name contains the graha keyword (e.g. Venus expert gets
  lon_venus, house_venus, dist_*_venus, d9_venus_sign, drishti_*_venus,
  cross_lon_venus, etc.). Lagna features go to all experts.
- Each expert: small MLP (feature_subset_dim → 64 → 64 → 27 classes).
- Gating: (event_label_embedding → 9-D softmax). At inference we
  read gating weights per class.
- Final logits = sum over experts (gating_weight_per_class * expert_logits).

Trained on the 14,166-event corpus (one row per event), event_root
as multi-class label.
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

logger = logging.getLogger(__name__)


GRAHAS: tuple[str, ...] = (
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
)


# ---------- Feature partitioning by karaka ----------

def _partition_features_by_karaka(
    feature_cols: list[str],
) -> dict[str, list[str]]:
    """Assign each feature to one or more karakas based on name match.

    Conservative: features named with one planet go to that planet's
    expert. Features without planet name (e.g. lagna_lon, sav_house_4,
    panchanga_tithi) go to ALL experts (treated as shared context).
    """
    per_karaka: dict[str, list[str]] = {p: [] for p in GRAHAS}
    shared: list[str] = []
    for col in feature_cols:
        c_lower = col.lower()
        owning = [p for p in GRAHAS if p in c_lower]
        if not owning:
            shared.append(col)
            continue
        # If multiple planets named (e.g. dist_sun_moon, drishti_sun_moon),
        # send to BOTH planets' experts so each can use the pairwise feature.
        for p in owning:
            per_karaka[p].append(col)
    # Append shared features to every expert
    for p in GRAHAS:
        per_karaka[p].extend(shared)
    logger.info("feature partition:")
    for p in GRAHAS:
        logger.info("  %-8s: %d cols", p, len(per_karaka[p]))
    logger.info("  (shared: %d cols added to each)", len(shared))
    return per_karaka


# ---------- MoE Model ----------

class KarakaExpert(nn.Module):
    """One per-graha expert. Input dim = features assigned to this graha."""

    def __init__(self, in_dim: int, hidden_dim: int, n_classes: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class KarakaMoE(nn.Module):
    """9 experts + per-class gating network.

    Gating receives a 1-hot encoding of the predicted class? No — gating
    needs to be PER-INPUT to be conditional. The setup here is:
    - Gating per-input: g(x) = softmax over 9 experts (input-dependent)
    - But we ALSO surface per-class average gating weights post-training
      to interpret which karakas dominate which classes.
    """

    def __init__(
        self,
        karaka_dims: dict[str, int],
        n_classes: int,
        hidden_dim: int = 64,
        gating_hidden: int = 32,
    ):
        super().__init__()
        self.karakas = list(GRAHAS)
        self.experts = nn.ModuleDict({
            p: KarakaExpert(karaka_dims[p], hidden_dim, n_classes)
            for p in self.karakas
        })
        # Gating: takes a concatenation of mean-per-karaka features as
        # input, outputs 9-D weight vector.
        gating_in = len(self.karakas) * 8  # 8-D summary per karaka
        self.gating = nn.Sequential(
            nn.Linear(gating_in, gating_hidden),
            nn.ReLU(),
            nn.Linear(gating_hidden, len(self.karakas)),
        )

    def forward(
        self,
        x_per_karaka: dict[str, torch.Tensor],
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Returns (logits, gating_weights).

        logits: (B, n_classes)
        gating_weights: (B, 9) — softmax over experts
        """
        expert_logits = []
        karaka_summaries = []
        for p in self.karakas:
            x_p = x_per_karaka[p]
            logits_p = self.experts[p](x_p)
            expert_logits.append(logits_p)
            # 8-D summary of this karaka's feature subset for gating
            summary = torch.stack([
                x_p.mean(dim=1), x_p.std(dim=1, unbiased=False),
                x_p.max(dim=1).values, x_p.min(dim=1).values,
                x_p.median(dim=1).values, x_p.abs().mean(dim=1),
                (x_p > 0).float().mean(dim=1), x_p.norm(dim=1),
            ], dim=-1)
            karaka_summaries.append(summary)
        gating_input = torch.cat(karaka_summaries, dim=-1)
        gating_logits = self.gating(gating_input)
        gating_weights = F.softmax(gating_logits, dim=-1)
        # Weighted combination of expert logits
        stacked_logits = torch.stack(expert_logits, dim=1)  # (B, 9, C)
        weighted = (gating_weights.unsqueeze(-1) * stacked_logits).sum(dim=1)
        return weighted, gating_weights


# ---------- Training ----------

def train(
    model: KarakaMoE,
    train_data: list[tuple[dict[str, np.ndarray], int]],
    val_data: list[tuple[dict[str, np.ndarray], int]],
    *,
    epochs: int = 15,
    batch_size: int = 128,
    lr: float = 1e-3,
    seed: int = 42,
) -> list[float]:
    rng = random.Random(seed)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    losses: list[float] = []
    for epoch in range(1, epochs + 1):
        rng.shuffle(train_data)
        epoch_loss = 0.0
        n_batches = 0
        for start in range(0, len(train_data), batch_size):
            batch = train_data[start:start + batch_size]
            if len(batch) < 8:
                continue
            x_per_karaka = {
                p: torch.from_numpy(np.stack([row[0][p] for row in batch])).float()
                for p in GRAHAS
            }
            y = torch.tensor([row[1] for row in batch], dtype=torch.long)
            logits, _ = model(x_per_karaka)
            loss = F.cross_entropy(logits, y)
            optim.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optim.step()
            epoch_loss += float(loss.item())
            n_batches += 1
        avg = epoch_loss / max(n_batches, 1)
        losses.append(avg)
        val_acc = evaluate(model, val_data, batch_size=batch_size)
        logger.info(
            "epoch %2d/%d  loss=%.4f  val_acc=%.4f",
            epoch, epochs, avg, val_acc,
        )
    return losses


def evaluate(
    model: KarakaMoE,
    data: list[tuple[dict[str, np.ndarray], int]],
    batch_size: int = 128,
) -> float:
    if not data:
        return 0.0
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for start in range(0, len(data), batch_size):
            batch = data[start:start + batch_size]
            x_per_karaka = {
                p: torch.from_numpy(np.stack([row[0][p] for row in batch])).float()
                for p in GRAHAS
            }
            y = np.array([row[1] for row in batch])
            logits, _ = model(x_per_karaka)
            pred = logits.argmax(dim=-1).cpu().numpy()
            correct += int((pred == y).sum())
            total += len(batch)
    model.train()
    return correct / max(total, 1)


def gating_weights_per_class(
    model: KarakaMoE,
    data: list[tuple[dict[str, np.ndarray], int]],
    n_classes: int,
    batch_size: int = 128,
) -> np.ndarray:
    """For each class, mean gating-weight vector across rows of that
    class. Returns (n_classes, 9) matrix."""
    model.eval()
    sums = np.zeros((n_classes, len(GRAHAS)))
    counts = np.zeros(n_classes)
    with torch.no_grad():
        for start in range(0, len(data), batch_size):
            batch = data[start:start + batch_size]
            x_per_karaka = {
                p: torch.from_numpy(np.stack([row[0][p] for row in batch])).float()
                for p in GRAHAS
            }
            y = [row[1] for row in batch]
            _, gw = model(x_per_karaka)
            gw_np = gw.cpu().numpy()
            for i, yi in enumerate(y):
                sums[yi] += gw_np[i]
                counts[yi] += 1
    model.train()
    counts = np.maximum(counts, 1)
    return sums / counts[:, None]


# ---------- Main ----------

def run_phase8(
    *,
    corpus_parquet: Path,
    output_dir: Path,
    epochs: int = 15,
    batch_size: int = 128,
    min_class_count: int = 100,
    seed: int = 42,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    logger.info("loading event corpus ...")
    df = pd.read_parquet(corpus_parquet)
    df["_label"] = df["event_root"].astype(str).str.lower().str.strip()
    # Collapse rare classes
    counts = df["_label"].value_counts()
    rare = set(counts[counts < min_class_count].index)
    if rare:
        df.loc[df["_label"].isin(rare), "_label"] = "other"
    class_names = sorted(df["_label"].unique().tolist())
    class_to_idx = {n: i for i, n in enumerate(class_names)}
    df["y"] = df["_label"].map(class_to_idx)
    logger.info("classes: %s", class_names)

    # Identify numeric feature columns (exclude metadata)
    NON_FEATURE = {
        "name", "rodden_rating", "categories_raw", "categories_lower",
        "categories_tokens", "source_url", "_label", "y",
        "event_date", "event_jd", "birth_jd", "event_root",
        "event_subtype", "is_event",
    }
    feature_cols = []
    for c in df.columns:
        if c in NON_FEATURE:
            continue
        s = df[c]
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            if s.nunique() > 1:
                feature_cols.append(c)
    logger.info("numeric feature cols: %d", len(feature_cols))

    # Partition by karaka
    per_karaka_cols = _partition_features_by_karaka(feature_cols)
    karaka_dims = {p: len(per_karaka_cols[p]) for p in GRAHAS}

    # Build (per_karaka_features, label) tuples
    from sklearn.preprocessing import StandardScaler
    scalers = {}
    feature_arrs = {}
    for p in GRAHAS:
        cols = per_karaka_cols[p]
        arr = df[cols].fillna(0.0).to_numpy().astype(np.float32)
        scaler = StandardScaler()
        feature_arrs[p] = scaler.fit_transform(arr).astype(np.float32)
        scalers[p] = scaler

    labels = df["y"].astype(int).to_numpy()
    all_data = []
    for i in range(len(df)):
        per_kar = {p: feature_arrs[p][i] for p in GRAHAS}
        all_data.append((per_kar, int(labels[i])))

    rng = random.Random(seed)
    rng.shuffle(all_data)
    n_val = max(int(len(all_data) * 0.2), 100)
    val_data = all_data[:n_val]
    train_data = all_data[n_val:]
    logger.info("train=%d  val=%d", len(train_data), len(val_data))

    n_classes = len(class_names)
    model = KarakaMoE(karaka_dims, n_classes=n_classes, hidden_dim=64)
    n_params = sum(p.numel() for p in model.parameters())
    logger.info("model params: %d (%.2f M)", n_params, n_params / 1e6)

    losses = train(
        model, train_data, val_data,
        epochs=epochs, batch_size=batch_size, seed=seed,
    )
    val_acc = evaluate(model, val_data)
    logger.info("final val accuracy: %.4f", val_acc)

    # Gating weights per class
    gw_per_class = gating_weights_per_class(model, val_data, n_classes)

    # Persist
    np.save(output_dir / "gating_weights_per_class.npy", gw_per_class)
    pd.DataFrame(
        gw_per_class, index=class_names, columns=list(GRAHAS),
    ).to_csv(output_dir / "gating_weights_per_class.csv")
    torch.save(model.state_dict(), output_dir / "moe_model.pt")
    with (output_dir / "config.json").open("w", encoding="utf-8") as f:
        json.dump({
            "class_names": class_names,
            "karakas": list(GRAHAS),
            "karaka_dims": karaka_dims,
            "val_accuracy": val_acc,
        }, f, indent=2)

    # Report — for each class, the top karaka
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = output_dir / "report.md"
    lines = [
        "# Phase 8 — Karaka-aware Mixture of Experts",
        "",
        f"_Generated {now}_",
        "",
        f"- Classes: {n_classes}",
        f"- Experts: 9 (one per graha)",
        f"- Total params: {n_params:,}",
        f"- Validation accuracy: **{val_acc:.4f}**",
        f"- Random baseline: {1 / n_classes:.4f}",
        f"- Phase 4 multi-class baseline (Round 5): 0.363",
        "",
        "## Loss curve",
        "",
        "| Epoch | Loss |",
        "|---|---|",
    ]
    for i, l in enumerate(losses, start=1):
        lines.append(f"| {i} | {l:.4f} |")

    lines.extend([
        "",
        "## Gating weights — which karaka dominates each event class?",
        "",
        "After training, for each event class we compute the **mean**",
        "gating weight across all validation rows of that class. The",
        "karaka with the highest gating weight is the model's choice of",
        "which expert to listen to most for that event type.",
        "",
        "**The classical-Vedic karaka theory predicts**:",
        "- marriage → Venus",
        "- career → Saturn / Sun",
        "- death → Saturn",
        "- fame → Sun / Jupiter",
        "- children → Jupiter",
        "- crime → Mars / Saturn",
        "- health → Sun / Mars",
        "- education → Mercury / Jupiter",
        "",
        "| Event class | Top karaka | 2nd | 3rd | Weights (Su Mo Ma Me Ju Ve Sa Ra Ke) |",
        "|---|---|---|---|---|",
    ])
    for class_name, weights in zip(class_names, gw_per_class, strict=True):
        order = np.argsort(-weights)
        top_3 = [GRAHAS[i] for i in order[:3]]
        w_str = " ".join(f"{w:.2f}" for w in weights)
        lines.append(
            f"| `{class_name}` | **{top_3[0]}** | {top_3[1]} | {top_3[2]} | {w_str} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "If gating weights match classical-karaka predictions, the model",
        "has empirically reproduced 2000-year-old astrological theory.",
        "Discrepancies are interesting: features the model relies on may",
        "have come into the era of recorded events through routes the",
        "classical texts didn't describe.",
    ])

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report to %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.karaka_moe",
    )
    parser.add_argument(
        "--corpus", type=Path,
        default=Path("app/medini/data/event_corpus_round5_all.parquet"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/moe_round6_phase8/"),
    )
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--min-class-count", type=int, default=100)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_phase8(
        corpus_parquet=args.corpus,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        min_class_count=args.min_class_count,
    )
    print(f"Phase 8 artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
